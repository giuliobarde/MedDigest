import datetime
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
import time

now_utc = datetime.datetime.now(datetime.timezone.utc)

one_week_ago = now_utc - datetime.timedelta(days=7)

#print(one_week_ago)





BASE_URL = "http://export.arxiv.org/api/query"
search_query = "all:medical"
params = {
    "search_query": search_query,
    "sortBy": "submittedDate",
    "sortOrder": "descending",
    "max_results": 100,
    "startDate": one_week_ago.strftime("%Y-%m-%d"),
}

# Proper URL encoding
url = f"{BASE_URL}?{urlencode(params)}"

# Add headers to make request more browser-like
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8',
}


try:
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()  # Raise an exception for bad status codes
except (requests.exceptions.RequestException, requests.exceptions.ConnectionError) as e:
    print(f"Attempt failed: {str(e)}")

root = ET.fromstring(response.content)

# Define the namespace
ns = {'atom': 'http://www.w3.org/2005/Atom'}

# Initialize the list to store papers
papers_this_week = []

# Parse each entry in the response
for entry in root.findall('.//atom:entry', ns):
    paper = {
        "paper_id": entry.find('atom:id', ns).text.split('/')[-1],
        "title": entry.find('atom:title', ns).text,
        "link": entry.find('atom:link', ns).get('href'),
        "published_date": datetime.datetime.strptime(
            entry.find('atom:published', ns).text,
            '%Y-%m-%dT%H:%M:%SZ'
        ).replace(tzinfo=datetime.timezone.utc),
        "abstract_text": entry.find('atom:summary', ns).text.strip(),
        "authors": [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)],
        "conclusion": entry.find('atom:summary', ns).text.strip()
    }
    papers_this_week.append(paper)

mini_summaries = []
for paper in papers_this_week:
    mini_summaries.append({"abstract_text": paper["abstract_text"], "conclusion": paper["conclusion"]})

if mini_summaries:
    print(mini_summaries[0])
else:
    print("No papers found in the specified time range.")