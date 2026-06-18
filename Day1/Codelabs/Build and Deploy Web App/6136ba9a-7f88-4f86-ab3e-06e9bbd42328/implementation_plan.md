# Serverless Event-Driven Document Processing Pipeline on GCP

Build a serverless pipeline that triggers on file uploads to a Cloud Storage bucket, sends notifications via Pub/Sub, processes the message in a Python Flask-based Cloud Run service (with GCS read and simulated OCR), and stores metadata in BigQuery using the streaming API.

## User Selections & Decisions

- **Infrastructure Provisioning**: Shell scripts running `gcloud` CLI commands step-by-step.
- **Event Route**: Native Cloud Storage Pub/Sub Notifications + Pub/Sub Push subscription to Cloud Run (unauthenticated endpoint).
- **Web Framework**: Flask with Gunicorn.
- **Processing Logic**: Full local simulation:
  - If it is a `.txt` file, download it from Cloud Storage, read the contents, count words, and extract tags.
  - For other files, generate mock OCR metadata and simulated word count.
  - No external API calls.
- **BigQuery Insertion**: Legacy Streaming API (`table.insert_rows()`).
- **Security**: Unauthenticated Cloud Run.
- **BigQuery Schema**:
  - `filename`: STRING
  - `bucket`: STRING
  - `size`: INTEGER
  - `content_type`: STRING
  - `word_count`: INTEGER
  - `tags`: STRING (REPEATED)
  - `ocr_text_preview`: STRING
  - `process_timestamp`: TIMESTAMP
- **Error Handling**: Fail-Fast with Retry (log to stdout, return HTTP 500 for Pub/Sub retries).
- **Testing**:
  - A local test script (`test_local.py`) to send mock Pub/Sub POST requests to the local Flask server.
  - A Cloud-integrated verification script (`verify_pipeline.py`) to upload a real file to GCS and verify the BigQuery record.

## Proposed Changes

We will create the following files in the project workspace:

### Cloud Run Python Application

#### [NEW] [main.py](file:///d:/EmbeddedSystem/OnlineCourses/5-Day%20AI%20Agents%20Intensive%20Vibe%20Coding%20Course%20With%20Google/Day1/Codelabs/Build%20a%20Web%20Application%20in%20AI%20Studio%20and%20Deploy%20to%20Cloud%20Run/google-cloud-serverless-app/main.py)
- Flask web server.
- Exposes `/` (POST) to receive Pub/Sub messages.
- Decodes Pub/Sub payload containing Cloud Storage event metadata (bucket, object, size, content_type).
- If `content_type` is text/plain or filename ends with `.txt`:
  - Downloads the file from Google Cloud Storage.
  - Counts words and extracts simple mock tags (e.g. capitalized words).
- If other file type:
  - Simulates word count and generates mock tags and OCR preview.
- Streams the metadata into the BigQuery table using `table.insert_rows()`.
- Implements error handling returning HTTP 500 on failures to trigger Pub/Sub retries.

#### [NEW] [requirements.txt](file:///d:/EmbeddedSystem/OnlineCourses/5-Day%20AI%20Agents%20Intensive%20Vibe%20Coding%20Course%20With%20Google/Day1/Codelabs/Build%20a%20Web%20Application%20in%20AI%20Studio%20and%20Deploy%20to%20Cloud%20Run/google-cloud-serverless-app/requirements.txt)
- `Flask==3.0.3`
- `google-cloud-storage==2.17.0`
- `google-cloud-bigquery==3.24.0`
- `gunicorn==22.0.0`

#### [NEW] [Dockerfile](file:///d:/EmbeddedSystem/OnlineCourses/5-Day%20AI%20Agents%20Intensive%20Vibe%20Coding%20Course%20With%20Google/Day1/Codelabs/Build%20a%20Web%20Application%20in%20AI%20Studio%20and%20Deploy%20to%20Cloud%20Run/google-cloud-serverless-app/Dockerfile)
- Python base image.
- Installs dependencies.
- Runs `gunicorn` binding to `PORT`.

### Scripts

#### [NEW] [deploy.sh](file:///d:/EmbeddedSystem/OnlineCourses/5-Day%20AI%20Agents%20Intensive%20Vibe%20Coding%20Course%20With%20Google/Day1/Codelabs/Build%20a%20Web%20Application%20in%20AI%20Studio%20and%20Deploy%20to%20Cloud%20Run/google-cloud-serverless-app/deploy.sh)
- Configures environment variables.
- Creates Cloud Storage bucket.
- Creates BigQuery dataset and table (defining schema).
- Builds and deploys the Cloud Run service (unauthenticated).
- Creates the Pub/Sub topic and configures GCS Notifications to publish to it.
- Creates a Pub/Sub Push Subscription pointing to the deployed Cloud Run service endpoint.

#### [NEW] [test_local.py](file:///d:/EmbeddedSystem/OnlineCourses/5-Day%20AI%20Agents%20Intensive%20Vibe%20Coding%20Course%20With%20Google/Day1/Codelabs/Build%20a%20Web%20Application%20in%20AI%20Studio%20and%20Deploy%20to%20Cloud%20Run/google-cloud-serverless-app/test_local.py)
- Locally sends mock Pub/Sub payloads to the Flask service running on `localhost:8080`.

#### [NEW] [verify_pipeline.py](file:///d:/EmbeddedSystem/OnlineCourses/5-Day%20AI%20Agents%20Intensive%20Vibe%20Coding%20Course%20With%20Google/Day1/Codelabs/Build%20a%20Web%20Application%20in%20AI%20Studio%20and%20Deploy%20to%20Cloud%20Run/google-cloud-serverless-app/verify_pipeline.py)
- Uploads a real sample file to the GCS bucket.
- Polls BigQuery to verify that the metadata is correctly ingested within a certain timeout.

## Verification Plan

### Automated/Local Tests
- Run `test_local.py` while the Flask app is running locally.

### Manual Verification
- Run `deploy.sh` to provision Google Cloud resources and deploy the Cloud Run service.
- Run `verify_pipeline.py` to test the end-to-end cloud integration.
