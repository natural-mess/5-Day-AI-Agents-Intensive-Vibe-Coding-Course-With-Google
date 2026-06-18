# Google Drive File Uploader in Python

This repository contains a robust, command-line Python utility to upload files to Google Drive using the **Google Drive API v3**. 

It handles OAuth 2.0 user authorization, credentials/token caching, MIME-type auto-detection, and resumable chunked uploads.

## Features
- **Resumable Uploads**: Automatically uploads files using chunked requests (highly recommended for large files or unstable connections).
- **MIME-Type Detection**: Automatically guesses the file's MIME type based on extension (e.g. `.png` as `image/png`) or falls back to binary octet-stream.
- **Parent Folders**: Allows uploading files directly to a specific Google Drive folder.
- **Custom Naming**: Option to name the file differently on Google Drive than its local filename.
- **Secure Scopes**: Uses the minimal and secure `https://www.googleapis.com/auth/drive.file` scope, meaning it can only view and modify files that *this* specific app created.

---

## 🛠️ Step 1: Install Dependencies

Make sure Python 3 is installed. Then, install the required Google client libraries:

```bash
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

---

## 🔑 Step 2: Set Up Google Cloud & Credentials

To access Google Drive, you must configure a Google Cloud project and download your OAuth 2.0 client configuration.

1. **Create/Select a Google Cloud Project**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project or select an existing one.

2. **Enable the Google Drive API**:
   - Navigate to the **API Library** (Search for "Google Drive API" in the search bar or go to APIs & Services > Library).
   - Click **Enable**.

3. **Configure the OAuth Consent Screen**:
   - Go to **APIs & Services** > **OAuth consent screen** (or **Google Auth platform** > **Branding**).
   - Set the User Type to **External** (or **Internal** if using a Google Workspace organization account).
   - Enter your **App name**, **User support email**, and **Developer contact information**. Click **Save and Continue**.
   - Under **Scopes**, you do not need to add scopes manually for quickstart testing. Under **Test Users**, add your own Google email address (the one you intend to log in with and upload to).

4. **Create Desktop Application Credentials**:
   - Go to **APIs & Services** > **Credentials** (or **Google Auth platform** > **Clients**).
   - Click **Create Credentials** > **OAuth client ID**.
   - Set the **Application type** to **Desktop app**.
   - Name the credential (e.g., `Drive Uploader`) and click **Create**.
   - Download the client secrets JSON file.
   - Rename this file to **`credentials.json`** and place it in the same directory as `upload_to_drive.py`.

---

## 🚀 Step 3: Run the Script

### Basic Usage
To upload a file (e.g., `my_photo.jpg`) to your Google Drive root directory:

```bash
python upload_to_drive.py my_photo.jpg
```

*Note: The first time you run this, a browser window will automatically open asking you to log in to your Google Account. Once authorized, it will save your token as `token.json` so you won't need to log in again.*

### Uploading to a Specific Folder
To upload a file inside a specific Google Drive folder, get the **Folder ID** (found at the end of the folder URL in the Drive web interface, e.g., `https://drive.google.com/drive/folders/1A2B3C...`):

```bash
python upload_to_drive.py my_photo.jpg --folder-id "1A2B3C..."
```

### Specifying a Custom Name on Drive
To name the file differently on Google Drive:

```bash
python upload_to_drive.py my_photo.jpg --name "vacation_photo_2026.jpg"
```

### Specifying MIME-Type Manually
If you want to bypass auto-detection and specify a MIME-type (e.g. `text/plain`):

```bash
python upload_to_drive.py my_notes.txt --mime-type "text/plain"
```

---

## 📄 File Overview
- [upload_to_drive.py](file:///D:/EmbeddedSystem/OnlineCourses/5-Day-AI-Agents-Intensive-Vibe-Coding-Course-With-Google/Day2/Codelabs/Google%20Developer%20Knowledge%20MCP/google-developer-knowledge/upload_to_drive.py): The main script handling credentials and file upload logic.
- `credentials.json` *(User Provided)*: OAuth client secrets file from the Google Cloud Console.
- `token.json` *(Auto-generated)*: Cached user credentials stored locally after first login.
