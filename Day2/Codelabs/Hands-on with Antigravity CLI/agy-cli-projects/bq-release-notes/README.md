# BigQuery Release Notes Explorer 🚀

A highly-polished, premium dark-mode web application built with a Python Flask backend and a plain vanilla HTML, JS, and CSS frontend. The application pulls the live Google Cloud BigQuery Release Notes XML feed, parses the contents, splits multi-part logs into separate granular updates, and allows you to customize and draft Twitter/X posts for any selected update with standard character limits.

---

## ✨ Features

- **Granular Updates**: Splits complex daily logs containing multiple updates (e.g. Features and Issues on the same day) into individual cards, enabling clean filtering and single-update sharing.
- **Dynamic Live Search & Category Filtering**: Instant text search through release note bodies, titles, and dates. Category pills dynamically recount active updates (Features, Announcements, Issues, Deprecations).
- **Interactive Twitter/X Draft Composer**: Styled composer card mirroring the X interface. Includes three predefined styling templates (Standard, Short, and Punchy) with an SVG circle progress bar matching X's 280-character limit.
- **Copy-to-Clipboard & Open Intent**: Seamlessly copy drafted text in the modal with verification feedback, or click "Post on X" to open a pre-populated Twitter Web Intent URL.
- **Direct Card Copying**: A dedicated "Copy" button is embedded directly on each release note card to instantly copy raw description text to your clipboard with visual confirmation.
- **Export to CSV**: An "Export CSV" utility triggers browser downloads of your currently filtered/searched list, including ID, Date, ISO Timestamp, Category, Link, and Content.
- **10-minute In-Memory Cache**: Prevents rate-limiting by caching RSS payloads. Forces live updates only when clicking the "Refresh" button.
- **Light/Dark Mode Theme Switcher**: Toggle between light and dark themes using the header control, which overrides CSS root variables and persists using HTML5 LocalStorage.
- **Responsive Glassmorphism Styling**: Fluid grids, customizable filters, absolute-to-relative date format mapping, and glowing border indicators.

---

## 🛠️ Technology Stack

* **Backend**: Python 3.14+, Flask 3.1+, Requests, BeautifulSoup4 (lxml)
* **Frontend**: Plain Vanilla HTML5, Vanilla CSS3 (Custom Variables & Animations), ES6 JavaScript

---

## 📂 Project Directory Structure

```text
bq-release-notes/
├── templates/
│   └── index.html         # Base dashboard HTML layout & Tweet Composer modal
├── static/
│   ├── css/
│   │   └── style.css      # Custom dark-mode, variables, and animation rules
│   └── js/
│       └── app.js         # AJAX request handling, searching, sorting, and Twitter drafting
├── app.py                 # Flask server, feed parsing, caching, and API endpoint
├── requirements.txt       # Python package dependencies
├── .gitignore             # Configured ignored items (virtualenv, pycache, logs)
└── README.md              # Project documentation
```

---

## 🚀 Setup & Local Execution

Follow these steps to run the application on your local machine:

### 1. Prerequisites
Ensure you have Python 3.9+ installed.

### 2. Create and Activate a Virtual Environment
In your terminal, navigate to the project root directory and run:

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Package Dependencies
Install the required libraries:
```bash
pip install -r requirements.txt
```

### 4. Run the Flask Server
Start the development server:
```bash
python app.py
```

### 5. Access the Web Dashboard
Open your browser and navigate to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 📝 Usage Guide

1. **Refresh Feed**: Click the **Refresh** button in the header to sync the latest release notes from Google Cloud. The spinner animation will active and fetch the live XML feed.
2. **Search and Filter**: Type key phrases (like `Gemini` or `embeddings`) into the search bar, or click category pills in the sidebar to filter cards.
3. **Select and Share**:
   - Hover over a release card and click **Draft Tweet**.
   - This opens the X Composer Modal.
   - Choose between **Standard**, **Short**, or **Punchy** styles using the styling toggles.
   - Click **Copy Text** to copy the text to your clipboard, or click **Post on X** to open a new tab containing the pre-filled post.
