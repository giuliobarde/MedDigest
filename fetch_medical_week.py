import datetime
import requests

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

print(response.text)
