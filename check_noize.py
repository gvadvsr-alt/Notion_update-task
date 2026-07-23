import os, requests
from dotenv import load_dotenv
load_dotenv()
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
HEADERS = {"Authorization": f"Bearer {NOTION_TOKEN}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}

url = "https://api.notion.com/v1/databases/02465e52a75143b08f039f81c8466392/query"
payload = {"filter": {"property": "DoDate", "date": {"before": "2026-06-03"}}, "page_size": 20}
resp = requests.post(url, headers=HEADERS, json=payload)
data = resp.json()
results = data.get("results", [])
print(f"Task con deadline passata (incluse Done): {len(results)} (has_more: {data.get('has_more')})")
for t in results:
    title_prop = t["properties"].get("\U0001f94a", {})
    title = title_prop["title"][0]["plain_text"] if title_prop.get("title") else "N/A"
    status = t["properties"].get("Status", {}).get("status", {})
    status_name = status.get("name", "N/A") if status else "N/A"
    dodate = t["properties"].get("DoDate", {}).get("date", {})
    dl = dodate.get("start", "N/A") if dodate else "N/A"
    print(f"  [{status_name}] {dl} -- {title[:60]}")
