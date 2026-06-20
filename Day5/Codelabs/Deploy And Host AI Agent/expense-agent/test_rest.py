import os
import requests
import google.auth
import google.auth.transport.requests

def get_access_token():
    credentials, _ = google.auth.default()
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    return credentials.token

def test_rest():
    token = get_access_token()
    project_id = "162241375902"
    location = "us-east1"
    re_id = "8225719166275944448"
    url = f"https://{location}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{location}/reasoningEngines/{re_id}:streamQuery"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print("\n--- Test 1: $50 Meal Expense ---")
    data1 = {
        "input": {
            "message": "Here is my $50 meal expense",
            "user_id": "test_user_1",
        }
    }
    try:
        response = requests.post(url, headers=headers, json=data1)
        print("Status:", response.status_code)
        for line in response.iter_lines():
            if line:
                print(line.decode('utf-8'))
    except Exception as e:
        print("Error:", e)

    print("\n--- Test 2: $150 Client Dinner Expense ---")
    data2 = {
        "input": {
            "message": "Here is my $150 client dinner expense",
            "user_id": "test_user_2",
        }
    }
    try:
        response = requests.post(url, headers=headers, json=data2)
        print("Status:", response.status_code)
        for line in response.iter_lines():
            if line:
                print(line.decode('utf-8'))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_rest()
