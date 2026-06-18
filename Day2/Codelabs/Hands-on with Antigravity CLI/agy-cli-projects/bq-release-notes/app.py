import os
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

FEED_URL = "https://docs.cloud.google.com/feeds/bigquery-release-notes.xml"
CACHE_DURATION = 600  # 10 minutes cache
cache = {
    "data": None,
    "last_updated": 0
}

def fix_relative_links(soup):
    """Convert relative links to absolute Google Cloud links."""
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('/'):
            a['href'] = 'https://cloud.google.com' + href
        # Ensure all links open in a new tab
        a['target'] = '_blank'
        a['rel'] = 'noopener noreferrer'

def parse_release_notes(xml_content):
    """Parse the Atom feed XML and extract individual release note updates."""
    # Using 'lxml-xml' or just 'xml' for Atom feed parsing
    soup = BeautifulSoup(xml_content, 'xml')
    entries = soup.find_all('entry')
    
    parsed_updates = []
    
    for entry in entries:
        # Title is typically the date, e.g. "June 17, 2026"
        date_str = entry.find('title').text.strip() if entry.find('title') else ''
        updated_str = entry.find('updated').text.strip() if entry.find('updated') else ''
        
        link_tag = entry.find('link', rel='alternate')
        link_href = link_tag['href'] if link_tag and 'href' in link_tag.attrs else ''
        
        content_tag = entry.find('content')
        content_html = content_tag.text if content_tag else ''
        
        # Parse the HTML content inside the entry
        content_soup = BeautifulSoup(content_html, 'html.parser')
        fix_relative_links(content_soup)
        
        # The content usually contains h3 elements marking category starts (e.g. Feature, Issue, Deprecation)
        # and then p/ul elements for the actual update details.
        headers = content_soup.find_all(['h3', 'h4'])
        
        entry_id = entry.find('id').text.strip() if entry.find('id') else ''
        
        if not headers:
            # If no subheadings, treat the whole content as one update
            parsed_updates.append({
                'id': entry_id,
                'parent_id': entry_id,
                'date': date_str,
                'updated_iso': updated_str,
                'link': link_href,
                'category': 'General',
                'content_html': str(content_soup),
                'content_text': content_soup.get_text().strip()
            })
        else:
            # We split the entry content by headers
            for idx, header in enumerate(headers):
                category = header.text.strip()
                
                # Gather all siblings until the next h3 or h4
                siblings = []
                curr = header.next_sibling
                while curr and curr.name not in ['h3', 'h4']:
                    siblings.append(curr)
                    curr = curr.next_sibling
                
                # Construct HTML and text representation of this specific sub-update
                sub_soup = BeautifulSoup('', 'html.parser')
                for sibling in siblings:
                    # Append a copy of the sibling node
                    sub_soup.append(BeautifulSoup(str(sibling), 'html.parser'))
                
                content_html_clean = str(sub_soup).strip()
                content_text_clean = sub_soup.get_text().strip()
                
                # Use a specific anchor link for this date category if possible
                anchor_link = f"{link_href}#{category.lower()}_{idx}" if link_href else ""
                
                parsed_updates.append({
                    'id': f"{entry_id}_{idx}",
                    'parent_id': entry_id,
                    'date': date_str,
                    'updated_iso': updated_str,
                    'link': link_href,
                    'category': category,
                    'content_html': content_html_clean,
                    'content_text': content_text_clean
                })
                
    return parsed_updates

def get_feed_data(force_refresh=False):
    """Fetch from GCP feed URL and cache results."""
    current_time = time.time()
    
    if force_refresh or not cache["data"] or (current_time - cache["last_updated"]) > CACHE_DURATION:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(FEED_URL, headers=headers, timeout=15)
            response.raise_for_status()
            
            updates = parse_release_notes(response.content)
            cache["data"] = updates
            cache["last_updated"] = current_time
        except Exception as e:
            # If fetch fails but we have cached data, fall back to it
            if cache["data"]:
                return cache["data"], True, str(e)
            raise e
            
    return cache["data"], False, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/release-notes')
def release_notes_api():
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'
    try:
        data, fell_back, error_msg = get_feed_data(force_refresh)
        return jsonify({
            "status": "success",
            "fell_back": fell_back,
            "error": error_msg,
            "last_updated": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cache["last_updated"])),
            "data": data
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
