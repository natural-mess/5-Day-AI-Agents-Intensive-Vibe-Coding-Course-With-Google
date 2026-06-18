import os
import time
import uuid
import datetime
from google.cloud import storage
from google.cloud import bigquery

def main():
    # Detect Project ID
    # Use gcloud CLI active config or GCP default client resolver
    bq_client = bigquery.Client()
    project_id = bq_client.project
    
    region = "us-central1"
    bucket_name = os.environ.get("BUCKET_NAME", f"{project_id}-document-ingest")
    dataset_name = os.environ.get("BQ_DATASET", "document_pipeline")
    table_name = os.environ.get("BQ_TABLE", "metadata")
    
    test_id = str(uuid.uuid4())[:8]
    test_filename = f"verification_test_{test_id}.txt"
    test_content = (
        "Google Cloud Platform is awesome. "
        "Serverless architectures make development faster. "
        "Python and Flask are great for microservices. "
        "BigQuery handles structured logs perfectly."
    )
    
    print("=== End-to-End Pipeline Verification ===")
    print(f"Project ID:      {project_id}")
    print(f"Bucket:          gs://{bucket_name}")
    echo_table = f"{project_id}.{dataset_name}.{table_name}"
    print(f"BigQuery Table:  {echo_table}")
    print(f"Test File:       {test_filename}")
    print("========================================")
    
    # 1. Create a local temporary file and upload it to GCS
    storage_client = storage.Client()
    try:
        bucket = storage_client.get_bucket(bucket_name)
    except Exception as e:
        print(f"\nERROR: Could not fetch GCS bucket '{bucket_name}'. Has deploy.sh been run?")
        print(f"Details: {e}")
        return
        
    print(f"\nUploading test file to gs://{bucket_name}/{test_filename}...")
    blob = bucket.blob(test_filename)
    blob.upload_from_string(test_content, content_type="text/plain")
    print("Upload complete.")
    
    # 2. Poll BigQuery for the metadata record
    query = f"""
        SELECT filename, bucket, size, content_type, word_count, tags, ocr_text_preview, process_timestamp
        FROM `{project_id}.{dataset_name}.{table_name}`
        WHERE filename = @filename
        LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("filename", "STRING", test_filename)
        ]
    )
    
    max_attempts = 36
    delay_seconds = 5
    found = False
    
    print("\nPolling BigQuery for pipeline results...")
    for attempt in range(1, max_attempts + 1):
        print(f"Attempt {attempt}/{max_attempts}: Querying BigQuery...")
        try:
            query_job = bq_client.query(query, job_config=job_config)
            results = query_job.result()
            
            if results.total_rows > 0:
                found = True
                row = next(results)
                print("\nSUCCESS: Metadata record found in BigQuery!")
                print("-" * 50)
                print(f"Filename:          {row.filename}")
                print(f"Bucket:            {row.bucket}")
                print(f"Size (Bytes):      {row.size}")
                print(f"Content Type:      {row.content_type}")
                print(f"Word Count:        {row.word_count}")
                print(f"Tags:              {row.tags}")
                print(f"OCR Preview:       {row.ocr_text_preview}")
                print(f"Process Timestamp: {row.process_timestamp}")
                print("-" * 50)
                break
        except Exception as e:
            print(f"Query attempt failed with error: {e}")
            
        time.sleep(delay_seconds)
        
    if not found:
        print(f"\nTIMEOUT: Did not find metadata for {test_filename} in BigQuery after {max_attempts * delay_seconds} seconds.")
        print("Please check the Cloud Run logs for errors:")
        print(f"  gcloud run services logs tail document-processor --region={region}")
        
    # 3. Clean up the file from GCS
    print(f"\nCleaning up: Deleting gs://{bucket_name}/{test_filename}...")
    try:
        # If we didn't find the file, let's wait an extra 5 seconds to ensure any late request has a chance to download it
        if not found:
            time.sleep(180) # Keep it in GCS for subsequent retries if we haven't processed it yet
        blob.delete()
        print("Cleanup complete.")
    except Exception as e:
        print(f"Failed to delete test file from GCS: {e}")

if __name__ == "__main__":
    main()
