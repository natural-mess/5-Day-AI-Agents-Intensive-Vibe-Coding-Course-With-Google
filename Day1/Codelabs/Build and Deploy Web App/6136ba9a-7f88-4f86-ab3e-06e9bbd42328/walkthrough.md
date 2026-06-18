# Walkthrough: Serverless Event-Driven Document Processing Pipeline

We have successfully created all the components and utility scripts for the event-driven document processing pipeline on GCP.

## Summary of Codebase

The following files have been created in your workspace:

1. **[requirements.txt](file:///d:/EmbeddedSystem/OnlineCourses/5-Day%20AI%20Agents%20Intensive%20Vibe%20Coding%20Course%20With%20Google/Day1/Codelabs/Build%20a%20Web%20Application%20in%20AI%20Studio%20and%20Deploy%20to%20Cloud%20Run/google-cloud-serverless-app/requirements.txt)**: Python package requirements (Flask, Google Cloud Storage, Google Cloud BigQuery, and Gunicorn).
2. **[Dockerfile](file:///d:/EmbeddedSystem/OnlineCourses/5-Day%20AI%20Agents%20Intensive%20Vibe%20Coding%20Course%20With%20Google/Day1/Codelabs/Build%20a%20Web%20Application%20in%20AI%20Studio%20and%20Deploy%20to%20Cloud%20Run/google-cloud-serverless-app/Dockerfile)**: Docker instructions to build the Cloud Run container.
3. **[main.py](file:///d:/EmbeddedSystem/OnlineCourses/5-Day%20AI%20Agents%20Intensive%20Vibe%20Coding%20Course%20With%20Google/Day1/Codelabs/Build%20a%20Web%20Application%20in%20AI%20Studio%20and%20Deploy%20to%20Cloud%20Run/google-cloud-serverless-app/main.py)**: The core Flask microservice. Handles incoming Pub/Sub push messages, checks GCS event properties, runs simulated OCR (downloads text files from GCS to parse contents; generates mock data for binary files), and streams metadata into BigQuery.
4. **[deploy.sh](file:///d:/EmbeddedSystem/OnlineCourses/5-Day%20AI%20Agents%20Intensive%20Vibe%20Coding%20Course%20With%20Google/Day1/Codelabs/Build%20a%20Web%20Application%20in%20AI%20Studio%20and%20Deploy%20to%20Cloud%20Run/google-cloud-serverless-app/deploy.sh)**: Automation bash script that configures GCP, creates the bucket, topic, dataset, table, service account, deploys the Cloud Run service, and sets up GCS Pub/Sub triggers.
5. **[test_local.py](file:///d:/EmbeddedSystem/OnlineCourses/5-Day%20AI%20Agents%20Intensive%20Vibe%20Coding%20Course%20With%20Google/Day1/Codelabs/Build%20a%20Web%20Application%20in%20AI%20Studio%20and%20Deploy%20to%20Cloud%20Run/google-cloud-serverless-app/test_local.py)**: Local tester script that sends simulated GCS Pub/Sub envelopes to the local Flask application.
6. **[verify_pipeline.py](file:///d:/EmbeddedSystem/OnlineCourses/5-Day%20AI%20Agents%20Intensive%20Vibe%20Coding%20Course%20With%20Google/Day1/Codelabs/Build%20a%20Web%20Application%20in%20AI%20Studio%20and%20Deploy%20to%20Cloud%20Run/google-cloud-serverless-app/verify_pipeline.py)**: E2E cloud-integrated test that uploads a `.txt` file, waits for the processing pipeline to insert details in BigQuery, verifies the content, and cleans up the uploaded file.

---

## Instructions for Testing & Deployment

### 1. Local Testing
To test the Flask application locally:

1. Install local dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the local server:
   ```bash
   python main.py
   ```
3. Run the local mock test tool in a separate terminal:
   ```bash
   python test_local.py
   ```
   > [!NOTE]
   > The test case with the PDF file will succeed and mock the OCR payload. The text file test case will try to access the GCS API to download the file and will fail locally unless Google Cloud authentication is set up in your local terminal.

### 2. Deploying to Google Cloud
Ensure your `gcloud` CLI is logged in and pointed to your target project:
```bash
gcloud auth login
gcloud config set project [YOUR_PROJECT_ID]
```

Run the deployment script:
```bash
bash deploy.sh
```

### 3. End-to-End Pipeline Verification
Once deployed, verify the cloud integration using the verification script:
```bash
python verify_pipeline.py
```
This script will upload a text file, query BigQuery, and display the ingested metadata table row.
