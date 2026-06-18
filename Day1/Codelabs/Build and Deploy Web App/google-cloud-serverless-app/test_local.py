import base64
import json
import urllib.request
import urllib.error
import sys

def send_mock_event(filename, size, content_type, bucket="my-mock-bucket"):
    url = "http://localhost:8080/"
    
    # Construct the GCS notification payload
    gcs_notification = {
        "kind": "storage#object",
        "name": filename,
        "bucket": bucket,
        "size": str(size),
        "contentType": content_type,
        "timeCreated": "2026-06-18T12:00:00Z"
    }
    
    # Base64 encode the GCS notification for the Pub/Sub envelope
    gcs_notification_json = json.dumps(gcs_notification)
    encoded_data = base64.b64encode(gcs_notification_json.encode("utf-8")).decode("utf-8")
    
    pubsub_envelope = {
        "message": {
            "data": encoded_data,
            "messageId": "1234567890"
        }
    }
    
    headers = {"Content-Type": "application/json"}
    req_data = json.dumps(pubsub_envelope).encode("utf-8")
    
    req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
    
    print(f"Sending mock Pub/Sub event for: gs://{bucket}/{filename} ({content_type})")
    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            response_text = response.read().decode("utf-8")
            print(f"Response Status: {status_code}")
            print(f"Response Body: {response_text}")
            if status_code == 200:
                print("SUCCESS: Mock event processed correctly.")
            else:
                print(f"FAILED: Status code {status_code}")
    except urllib.error.HTTPError as e:
        status_code = e.code
        response_text = e.read().decode("utf-8")
        print(f"FAILED (HTTPError): Status code {status_code}")
        print(f"Response Body: {response_text}")
    except urllib.error.URLError as e:
        print(f"CONNECTION ERROR: Could not connect to {url}. Is the Flask server running?")
        print(f"Reason: {e.reason}")

if __name__ == "__main__":
    print("--- Running Local Mock Tests ---")
    print("Make sure your Flask server is running locally (e.g. via python main.py) before running this script.\n")
    
    # Test 1: Simulated non-text file (e.g., PDF)
    # This should succeed and use mock OCR values, bypass downloading from actual GCS.
    print("Test Case 1: Mock PDF file (should bypass GCS download and write mocked OCR metadata)")
    send_mock_event(filename="report.pdf", size=1048576, content_type="application/pdf")
    print("-" * 50)
    
    # Test 2: Simulated text file (e.g., text/plain)
    # Note: If GCS credentials are not configured locally, this test will trigger a 500 error in Flask
    # because it will attempt to download the file from the non-existent bucket "my-mock-bucket".
    print("Test Case 2: Mock TXT file (will attempt to download from GCS and count words)")
    send_mock_event(filename="sample.txt", size=512, content_type="text/plain")
    print("-" * 50)
