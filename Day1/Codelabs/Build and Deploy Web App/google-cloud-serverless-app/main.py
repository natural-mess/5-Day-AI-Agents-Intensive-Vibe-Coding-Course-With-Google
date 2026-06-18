import os
import base64
import json
import random
import datetime
from flask import Flask, request
from google.cloud import storage
from google.cloud import bigquery

app = Flask(__name__)

# Initialize GCP clients
# Note: Clients will use the default service account credentials in the Cloud Run environment.
storage_client = storage.Client()
bq_client = bigquery.Client()

@app.route("/", methods=["POST"])
def process_message():
    envelope = request.get_json()
    if not envelope:
        print("Error: No JSON envelope received")
        return "Bad Request: No JSON envelope", 400

    if not isinstance(envelope, dict) or "message" not in envelope:
        print("Error: Invalid Pub/Sub message format")
        return "Bad Request: Invalid Pub/Sub message format", 400

    pubsub_message = envelope["message"]
    if "data" not in pubsub_message:
        print("Error: No data field in Pub/Sub message")
        return "Bad Request: No data field in Pub/Sub message", 400

    try:
        data_str = base64.b64decode(pubsub_message["data"]).decode("utf-8")
        gcs_event = json.loads(data_str)
    except Exception as e:
        print(f"Error decoding Pub/Sub data: {e}")
        return "Bad Request: Invalid base64 or JSON in message data", 400

    # Log the received event metadata
    print(f"Received event notification: {json.dumps(gcs_event)}")

    # GCS sends test notifications (e.g. on notification config creation) without object names.
    # Handle these gracefully by returning HTTP 200.
    bucket = gcs_event.get("bucket")
    filename = gcs_event.get("name")
    
    if not bucket or not filename:
        print("Notification is not a file upload event (likely a test notification or bucket creation check). Skipping processing.")
        return "Skipped: Missing bucket or filename", 200

    size = int(gcs_event.get("size", 0))
    content_type = gcs_event.get("contentType", "application/octet-stream")

    try:
        # Check if the file is a text file to simulate text processing / word count
        is_text_file = content_type.startswith("text/") or filename.endswith(".txt")

        if is_text_file:
            print(f"Processing text file: gs://{bucket}/{filename}")
            # Download file content from GCS
            bucket_obj = storage_client.bucket(bucket)
            blob = bucket_obj.blob(filename)
            file_content = blob.download_as_text()

            # Word count and tags extraction
            words = file_content.split()
            word_count = len(words)
            # Find unique words with length > 4 that start with an uppercase letter to use as tags
            tags = list(set([
                w.strip(".,!?;:()\"'") 
                for w in words 
                if len(w) > 4 and w[0].isupper()
            ]))[:5]
            
            if not tags:
                tags = ["text_file", "txt"]

            # Store the preview of text
            ocr_text_preview = file_content[:1000]
        else:
            print(f"Processing binary/other file: gs://{bucket}/{filename}")
            # Mock OCR results for non-text files
            word_count = random.randint(50, 500)
            tags = ["mocked_ocr", content_type.split("/")[-1], "processed"]
            ocr_text_preview = f"Simulated OCR text for non-text file '{filename}' of type '{content_type}'."

        # Insert metadata into BigQuery
        dataset_id = os.environ.get("BQ_DATASET", "document_pipeline")
        table_id = os.environ.get("BQ_TABLE", "metadata")
        
        # Get table reference
        table_ref = bq_client.dataset(dataset_id).table(table_id)
        
        row_to_insert = {
            "filename": filename,
            "bucket": bucket,
            "size": size,
            "content_type": content_type,
            "word_count": word_count,
            "tags": tags,
            "ocr_text_preview": ocr_text_preview,
            "process_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        print(f"Streaming metadata to BigQuery {dataset_id}.{table_id}: {json.dumps(row_to_insert)}")
        
        # insert_rows_json streams rows to BQ table directly
        errors = bq_client.insert_rows_json(table_ref, [row_to_insert])
        if errors:
            print(f"BigQuery insertion failed: {errors}")
            raise Exception(f"BigQuery insertion failed: {errors}")

        print(f"Successfully processed gs://{bucket}/{filename}")
        return f"Successfully processed {filename}", 200

    except Exception as e:
        print(f"Fail-Fast Triggered: Error processing message: {str(e)}")
        # Returning HTTP 500 triggers Pub/Sub message redelivery/retry
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    # Serve locally on port 8080 (default Cloud Run port)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
