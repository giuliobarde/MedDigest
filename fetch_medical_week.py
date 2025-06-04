import datetime
import requests
import xml.etree.ElementTree as ET

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

# Building the full URL string manually
url = (
    BASE_URL
    + "?search_query="
    + params["search_query"]
    + "&sortBy="
    + params["sortBy"]
    + "&sortOrder="
    + params["sortOrder"]
    + "&max_results="
    + str(params["max_results"])
)

response = requests.get(url)
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
        "abstract_text": entry.find('atom:summary', ns).text.strip()
    }
    papers_this_week.append(paper)

mini_summaries = []
for paper in papers_this_week:
    print(paper["paper_id"])
