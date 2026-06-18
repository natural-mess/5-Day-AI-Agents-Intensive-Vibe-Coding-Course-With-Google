#!/usr/bin/env python3
"""
Google Drive File Uploader
==========================
This script uploads a local file to Google Drive using the Google Drive API v3.
It handles OAuth 2.0 user authentication, tokens caching (token.json),
automatic mime-type detection, and uploading files to specific folders.

Prerequisites:
--------------
1. Install dependencies:
   pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

2. Obtain `credentials.json` from the Google Cloud Console:
   - Create a Google Cloud Project
   - Enable the Google Drive API
   - Configure the OAuth Consent Screen (User Type: External/Internal)
   - Create credentials for a "Desktop Application"
   - Download the JSON credentials file and rename it to `credentials.json` in the same directory as this script.
"""

import os
import sys
import argparse
import mimetypes
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.json.
# 'https://www.googleapis.com/auth/drive.file' allows uploading and managing
# files/folders created or opened by this app. For full access, use 'https://www.googleapis.com/auth/drive'.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def get_credentials(credentials_path="credentials.json", token_path="token.json"):
    """
    Authenticates the user and retrieves Google Drive API credentials.
    Loads cached token.json if it exists and is valid, otherwise prompts
    the user to log in via browser and saves the new credentials.
    """
    creds = None
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print(f"Warning: Could not load token from {token_path}: {e}")
            creds = None

    # If there are no valid credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired access token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}. Re-authenticating...")
                creds = None

        if not creds:
            if not os.path.exists(credentials_path):
                print(
                    f"Error: Credentials file '{credentials_path}' not found.\n"
                    f"Please follow the instructions in the README to download your OAuth 2.0 client secrets file "
                    f"from the Google Cloud Console, save it as '{credentials_path}' in this directory, and try again.",
                    file=sys.stderr
                )
                sys.exit(1)
            
            print("No valid credentials found. Initiating browser authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())
            print(f"Credentials cached successfully to '{token_path}'.")

    return creds


def upload_file(file_path, name=None, folder_id=None, mime_type=None):
    """
    Uploads a file to Google Drive.

    Parameters:
    -----------
    file_path : str
        The path to the local file to upload.
    name : str, optional
        The name the uploaded file should have on Google Drive. Defaults to the local filename.
    folder_id : str, optional
        The ID of the parent folder in Google Drive. If omitted, the file is uploaded to the root.
    mime_type : str, optional
        The MIME type of the file. Automatically guessed if omitted.

    Returns:
    --------
    dict or None
        The metadata of the created file, containing 'id' and 'webViewLink' if successful, else None.
    """
    if not os.path.exists(file_path):
        print(f"Error: Local file '{file_path}' does not exist.", file=sys.stderr)
        return None

    # Guess MIME type if not specified
    if not mime_type:
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"
            print(f"Could not determine MIME type. Defaulting to '{mime_type}'.")
        else:
            print(f"Detected MIME type: '{mime_type}'")
    else:
        print(f"Using specified MIME type: '{mime_type}'")

    # Determine file name for Google Drive
    drive_filename = name if name else os.path.basename(file_path)

    # Load credentials and build the drive service
    creds = get_credentials()
    try:
        service = build("drive", "v3", credentials=creds)

        # Prepare metadata
        file_metadata = {
            "name": drive_filename
        }
        if folder_id:
            file_metadata["parents"] = [folder_id]

        # Use resumable=True which is recommended for robustness and large files
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

        print(f"Uploading '{file_path}' to Google Drive as '{drive_filename}'...")
        
        # Execute the request
        request = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name, webViewLink"
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Upload Progress: {int(status.progress() * 100)}%")

        print("\nUpload complete!")
        print(f"File Name: {response.get('name')}")
        print(f"File ID  : {response.get('id')}")
        print(f"View Link: {response.get('webViewLink')}")
        return response

    except HttpError as error:
        print(f"Google Drive API error occurred: {error}", file=sys.stderr)
        return None
    except Exception as error:
        print(f"An unexpected error occurred: {error}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Upload a local file to Google Drive using the Google Drive API v3."
    )
    parser.add_argument(
        "file_path",
        help="Path to the local file to upload"
    )
    parser.add_argument(
        "-n", "--name",
        help="Name to give the file in Google Drive (defaults to the local filename)"
    )
    parser.add_argument(
        "-f", "--folder-id",
        help="Google Drive Folder ID where the file should be uploaded (optional)"
    )
    parser.add_argument(
        "-t", "--mime-type",
        help="Explicit MIME type of the file (optional, guessed automatically if not provided)"
    )
    
    args = parser.parse_args()
    
    upload_file(
        file_path=args.file_path,
        name=args.name,
        folder_id=args.folder_id,
        mime_type=args.mime_type
    )


if __name__ == "__main__":
    main()
