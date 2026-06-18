# Walkthrough - Google News CLI Tool

We have built a command-line application that allows you to easily fetch the latest news from Google News.

## Changes Made

1. **[package.json](file:///d:/EmbeddedSystem/OnlineCourses/5-Day%20AI%20Agents%20Intensive%20Vibe%20Coding%20Course%20With%20Google/Day1/Codelabs/Getting%20Started%20with%20Google%20Antigravity/my-first-project/package.json)**: Initialized project metadata, added `"type": "module"`, and installed dependencies: `rss-parser`, `chalk`, and `commander`.
2. **[index.js](file:///d:/EmbeddedSystem/OnlineCourses/5-Day%20AI%20Agents%20Intensive%20Vibe%20Coding%20Course%20With%20Google/Day1/Codelabs/Getting%20Started%20with%20Google%20Antigravity/my-first-project/index.js)**: Created the CLI application script which:
   - Sets up command line flags for limiting results (`--limit` or `-l`) and searching queries (`--search` or `-s`).
   - Fetches the RSS feed dynamically from Google News.
   - Cleans up article titles to separate the headline from the publishing source.
   - Displays the formatted news beautifully in the terminal with colored headers, sources, publication dates, and underlines for links.

---

## Verification Results

### Top Stories Run
Command:
```bash
node index.js --limit 3
```
Output:
```
🔄 Fetching latest news from Google News...
✔ Successfully loaded feed!

 TOP STORIES 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. US officials say Iran deal calls for diluting uranium at minimum, waiving sanctions, opening strait
   Source: AP News   Published: 6/17/2026, 10:50:00 PM
   https://news.google.com/rss/articles/...

2. Senate delays Jay Clayton’s nomination for intel director after Trump post
   Source: NBC News   Published: 6/17/2026, 6:23:31 PM
   https://news.google.com/rss/articles/...

3. Subcontractors say they’re owed millions, face financial ruin, after helping build Obama Presidential Center
   Source: Fox News   Published: 6/17/2026, 9:32:06 PM
   https://news.google.com/rss/articles/...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Showing 3 of 38 items.
```

### Search Run
Command:
```bash
node index.js --search "Google" --limit 3
```
Output:
```
🔄 Fetching latest news from Google News...
✔ Successfully loaded feed!

 SEARCH RESULTS FOR: "GOOGLE" 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Android 17 launches with new multitasking tools as Google expands Gemini features
   Source: TechCrunch   Published: 6/16/2026, 8:00:00 PM
   https://news.google.com/rss/articles/...

2. Check out what's new in Android 17
   Source: blog.google   Published: 6/16/2026, 8:01:19 PM
   https://news.google.com/rss/articles/...

3. Google Phone app on Wear OS gets Material 3 Expressive redesign
   Source: 9to5Google   Published: 6/17/2026, 12:05:00 AM
   https://news.google.com/rss/articles/...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Showing 3 of 102 items.
```

---

## How to Run the App

1. Ensure dependencies are installed:
   ```bash
   npm install
   ```
2. Run the script:
   - For top stories:
     ```bash
     node index.js
     ```
   - For top 5 stories:
     ```bash
     node index.js --limit 5
     ```
   - To search for stories about "Google":
     ```bash
     node index.js --search "Google"
     ```
