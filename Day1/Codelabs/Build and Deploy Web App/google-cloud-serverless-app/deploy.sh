#!/bin/bash
set -e

# =====================================================================
# Configuration Variables
# Change these values or override them with environment variables
# =====================================================================
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
  echo "Error: No active gcloud project found. Please run 'gcloud config set project [PROJECT_ID]' first."
  exit 1
fi

REGION="us-central1"
BUCKET_NAME="${PROJECT_ID}-document-ingest"
TOPIC_NAME="gcs-document-uploads"
DATASET_NAME="document_pipeline"
TABLE_NAME="metadata"
SERVICE_NAME="document-processor"
SERVICE_ACCOUNT_NAME="doc-pipeline-runner"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=== Pipeline Configuration ==="
echo "Project ID:        $PROJECT_ID"
echo "Region:            $REGION"
echo "Storage Bucket:    gs://$BUCKET_NAME"
echo "Pub/Sub Topic:     $TOPIC_NAME"
echo "BigQuery Dataset:  $DATASET_NAME"
echo "BigQuery Table:    $TABLE_NAME"
echo "Cloud Run Service: $SERVICE_NAME"
echo "Service Account:   $SERVICE_ACCOUNT_EMAIL"
echo "=============================="
echo ""

# 1. Enable GCP Services
echo "Step 1: Enabling Google Cloud APIs..."
gcloud services enable \
  storage.googleapis.com \
  pubsub.googleapis.com \
  bigquery.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

# 2. Create the Service Account for Cloud Run
echo "Step 2: Creating Cloud Run Service Account..."
if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
    --description="Service account for serverless document processing Cloud Run service" \
    --display-name="Document Processing Pipeline Service Account"
else
  echo "Service account already exists."
fi

# 3. Create GCS Bucket
echo "Step 3: Creating Cloud Storage Bucket..."
if ! gcloud storage buckets describe "gs://$BUCKET_NAME" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://$BUCKET_NAME" --location="$REGION"
else
  echo "Bucket gs://$BUCKET_NAME already exists."
fi

# Grant Cloud Run service account permission to read objects from GCS
echo "Granting read access to GCS bucket for the service account..."
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET_NAME" \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/storage.objectViewer"

# 4. Create BigQuery Dataset and Table
echo "Step 4: Creating BigQuery Dataset..."
# Check if dataset exists
if ! bq show "$DATASET_NAME" >/dev/null 2>&1; then
  bq mk --dataset --location="$REGION" --quiet "$DATASET_NAME"
else
  echo "Dataset $DATASET_NAME already exists."
fi

# Grant BigQuery permissions to the service account
echo "Granting BigQuery Data Editor role to the service account..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/bigquery.dataEditor"

echo "Creating BigQuery Metadata Table..."
# Create temporary schema file
SCHEMA_FILE=$(mktemp)
cat <<EOF > "$SCHEMA_FILE"
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
EOF

if ! bq show "${DATASET_NAME}.${TABLE_NAME}" >/dev/null 2>&1; then
  bq mk --table --quiet "${DATASET_NAME}.${TABLE_NAME}" "$SCHEMA_FILE"
else
  echo "Table ${DATASET_NAME}.${TABLE_NAME} already exists."
fi
rm -f "$SCHEMA_FILE"

# 5. Build and Deploy Cloud Run Service
echo "Step 5: Deploying Cloud Run Service..."
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region "$REGION" \
  --service-account "$SERVICE_ACCOUNT_EMAIL" \
  --allow-unauthenticated \
  --set-env-vars BQ_DATASET="$DATASET_NAME",BQ_TABLE="$TABLE_NAME" \
  --quiet

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")
echo "Service URL is: $SERVICE_URL"

# 6. Create Pub/Sub Topic
echo "Step 6: Creating Pub/Sub Topic..."
if ! gcloud pubsub topics describe "$TOPIC_NAME" >/dev/null 2>&1; then
  gcloud pubsub topics create "$TOPIC_NAME"
else
  echo "Topic $TOPIC_NAME already exists."
fi

# 7. Configure GCS notifications
echo "Step 7: Granting GCS permissions to publish to Pub/Sub..."
PROJECT_NUMBER=$(gcloud projects list --filter="projectId:$PROJECT_ID" --format="value(projectNumber)")
GCS_SA_EMAIL="service-${PROJECT_NUMBER}@gs-project-accounts.iam.gserviceaccount.com"

gcloud pubsub topics add-iam-policy-binding "$TOPIC_NAME" \
  --member="serviceAccount:$GCS_SA_EMAIL" \
  --role="roles/pubsub.publisher"

echo "Creating GCS Bucket Notification Trigger..."
# Create notification only if it doesn't already exist
if ! gcloud storage buckets notifications list "gs://$BUCKET_NAME" | grep -q "$TOPIC_NAME"; then
  gcloud storage buckets notifications create "gs://$BUCKET_NAME" --topic="$TOPIC_NAME"
else
  echo "Notification trigger already configured."
fi

# 8. Create Pub/Sub Subscription for Cloud Run Push
echo "Step 8: Creating Pub/Sub Push Subscription..."
SUBSCRIPTION_NAME="${TOPIC_NAME}-sub"
if ! gcloud pubsub subscriptions describe "$SUBSCRIPTION_NAME" >/dev/null 2>&1; then
  gcloud pubsub subscriptions create "$SUBSCRIPTION_NAME" \
    --topic="$TOPIC_NAME" \
    --push-endpoint="$SERVICE_URL"
else
  # Update push endpoint in case service URL changed
  gcloud pubsub subscriptions update "$SUBSCRIPTION_NAME" \
    --push-endpoint="$SERVICE_URL"
fi

echo ""
echo "=== Deployment Completed Successfully! ==="
echo "Upload files to: gs://$BUCKET_NAME"
echo "Monitor logs:    gcloud run services logs tail $SERVICE_NAME --region=$REGION"
echo "BigQuery Table:  $DATASET_NAME.$TABLE_NAME"
echo "=========================================="
