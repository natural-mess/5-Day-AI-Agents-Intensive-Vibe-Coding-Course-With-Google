# =====================================================================
# Configuration Variables
# Change these values or override them
# =====================================================================
$env:CLOUDSDK_PYTHON = "python"

$PROJECT_ID = gcloud config get-value project
if (-not $PROJECT_ID) {
    Write-Error "Error: No active gcloud project found. Please run 'gcloud config set project [PROJECT_ID]' first."
    exit 1
}

$PROJECT_NUMBER = gcloud projects list --filter="projectId:$PROJECT_ID" --format="value(projectNumber)"
$REGION = "us-central1"
$BUCKET_NAME = "${PROJECT_ID}-document-ingest"
$TOPIC_NAME = "gcs-document-uploads"
$DATASET_NAME = "document_pipeline"
$TABLE_NAME = "metadata"
$SERVICE_NAME = "document-processor"
$SERVICE_ACCOUNT_NAME = "doc-pipeline-runner"
$SERVICE_ACCOUNT_EMAIL = "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
$COMPUTE_SA_EMAIL = "${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

Write-Host "=== Pipeline Configuration ==="
Write-Host "Project ID:        $PROJECT_ID"
Write-Host "Project Number:    $PROJECT_NUMBER"
Write-Host "Region:            $REGION"
Write-Host "Storage Bucket:    gs://$BUCKET_NAME"
Write-Host "Pub/Sub Topic:     $TOPIC_NAME"
Write-Host "BigQuery Dataset:  $DATASET_NAME"
Write-Host "BigQuery Table:    $TABLE_NAME"
Write-Host "Cloud Run Service: $SERVICE_NAME"
Write-Host "Service Account:   $SERVICE_ACCOUNT_EMAIL"
Write-Host "=============================="
Write-Host ""

# 1. Enable GCP Services
Write-Host "Step 1: Enabling Google Cloud APIs..."
gcloud services enable `
  storage.googleapis.com `
  pubsub.googleapis.com `
  bigquery.googleapis.com `
  run.googleapis.com `
  artifactregistry.googleapis.com `
  cloudbuild.googleapis.com

# 2. Create the Service Account for Cloud Run
Write-Host "Step 2: Creating Cloud Run Service Account..."
gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" 2>$null
if ($LASTEXITCODE -ne 0) {
    gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" `
      --description="Service account for serverless document processing Cloud Run service" `
      --display-name="Document Processing Pipeline Service Account"
} else {
    Write-Host "Service account already exists."
}

# 3. Create GCS Bucket
Write-Host "Step 3: Creating Cloud Storage Bucket..."
gcloud storage buckets describe "gs://$BUCKET_NAME" 2>$null
if ($LASTEXITCODE -ne 0) {
    gcloud storage buckets create "gs://$BUCKET_NAME" --location="$REGION"
} else {
    Write-Host "Bucket gs://$BUCKET_NAME already exists."
}

Write-Host "Granting read access to GCS bucket for the service account..."
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET_NAME" `
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" `
  --role="roles/storage.objectViewer"

# 4. Create BigQuery Dataset and Table
Write-Host "Step 4: Creating BigQuery Dataset..."
bq show "$DATASET_NAME" 2>$null
if ($LASTEXITCODE -ne 0) {
    bq mk --dataset --location="$REGION" --quiet "$DATASET_NAME"
} else {
    Write-Host "Dataset $DATASET_NAME already exists."
}

Write-Host "Granting BigQuery Data Editor role to the service account..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" `
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" `
  --role="roles/bigquery.dataEditor"

Write-Host "Creating BigQuery Metadata Table..."
$SCHEMA = @'
[
  {"name": "filename", "type": "STRING", "mode": "REQUIRED"},
  {"name": "bucket", "type": "STRING", "mode": "REQUIRED"},
  {"name": "size", "type": "INTEGER", "mode": "NULLABLE"},
  {"name": "content_type", "type": "STRING", "mode": "NULLABLE"},
  {"name": "word_count", "type": "INTEGER", "mode": "NULLABLE"},
  {"name": "tags", "type": "STRING", "mode": "REPEATED"},
  {"name": "ocr_text_preview", "type": "STRING", "mode": "NULLABLE"},
  {"name": "process_timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"}
]
'@

bq show "${DATASET_NAME}.${TABLE_NAME}" 2>$null
if ($LASTEXITCODE -ne 0) {
    $tempSchemaFile = [System.IO.Path]::GetTempFileName()
    # Write file using .NET to prevent UTF-8 BOM encoding which breaks BigQuery's schema parser
    [System.IO.File]::WriteAllText($tempSchemaFile, $SCHEMA)
    bq mk --table --quiet "${DATASET_NAME}.${TABLE_NAME}" $tempSchemaFile
    Remove-Item -Path $tempSchemaFile
} else {
    Write-Host "Table ${DATASET_NAME}.${TABLE_NAME} already exists."
}

# 5. Build and Deploy Cloud Run Service
Write-Host "Step 5: Granting Storage Admin role to the default Compute SA for Cloud Build..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" `
  --member="serviceAccount:$COMPUTE_SA_EMAIL" `
  --role="roles/storage.admin"

Write-Host "Deploying Cloud Run Service..."
gcloud run deploy "$SERVICE_NAME" `
  --source . `
  --region "$REGION" `
  --service-account "$SERVICE_ACCOUNT_EMAIL" `
  --allow-unauthenticated `
  --set-env-vars BQ_DATASET="$DATASET_NAME",BQ_TABLE="$TABLE_NAME" `
  --quiet

$SERVICE_URL = gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)"
Write-Host "Service URL is: $SERVICE_URL"

# 6. Create Pub/Sub Topic
Write-Host "Step 6: Creating Pub/Sub Topic..."
gcloud pubsub topics describe "$TOPIC_NAME" 2>$null
if ($LASTEXITCODE -ne 0) {
    gcloud pubsub topics create "$TOPIC_NAME"
} else {
    Write-Host "Topic $TOPIC_NAME already exists."
}

# 7. Configure GCS notifications
Write-Host "Step 7: Granting GCS permissions to publish to Pub/Sub..."
# Fetch the GCS service agent (creates it dynamically if missing)
$GCS_SA_EMAIL = ((gcloud storage service-agent --project="$PROJECT_ID") -match "@").Trim()

gcloud pubsub topics add-iam-policy-binding "$TOPIC_NAME" `
  --member="serviceAccount:$GCS_SA_EMAIL" `
  --role="roles/pubsub.publisher"

Write-Host "Creating GCS Bucket Notification Trigger..."
$notifications = gcloud storage buckets notifications list "gs://$BUCKET_NAME"
if ($notifications -like "*$TOPIC_NAME*") {
    Write-Host "Notification trigger already configured."
} else {
    gcloud storage buckets notifications create "gs://$BUCKET_NAME" --topic="$TOPIC_NAME"
}

# 8. Create Pub/Sub Subscription for Cloud Run Push
Write-Host "Step 8: Creating Pub/Sub Push Subscription..."
$SUBSCRIPTION_NAME = "${TOPIC_NAME}-sub"
gcloud pubsub subscriptions describe "$SUBSCRIPTION_NAME" 2>$null
if ($LASTEXITCODE -ne 0) {
    gcloud pubsub subscriptions create "$SUBSCRIPTION_NAME" `
      --topic="$TOPIC_NAME" `
      --push-endpoint="$SERVICE_URL"
} else {
    gcloud pubsub subscriptions update "$SUBSCRIPTION_NAME" `
      --push-endpoint="$SERVICE_URL"
}

Write-Host ""
Write-Host "=== Deployment Completed Successfully! ==="
Write-Host "Upload files to: gs://$BUCKET_NAME"
Write-Host "Monitor logs:    gcloud run services logs tail $SERVICE_NAME --region=$REGION"
Write-Host "BigQuery Table:  $DATASET_NAME.$TABLE_NAME"
Write-Host "=========================================="
