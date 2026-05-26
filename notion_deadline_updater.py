import os
import requests
from datetime import datetime, timedelta, timezone

NOTION_TOKEN = os.environ["NOTION_TOKEN"]

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

DATABASES = {
    "La Dea":        "081cdaad43d446038f8afb58aee18174",
    "Noize Agency":  "02465e52a75143b08f039f81c8466392",
    "Vita Personale":"94725e54dd9542a58450c80c8d47298f",
    "Sport":         "1a8a084f44004132bffb196dd7b497b9",
}

def get_today():
    return datetime.now(timezone.utc).date()

def query_overdue_tasks(database_id):
    today = get_today().isoformat()
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    payload = {
        "filter": {
            "and": [
                {"property": "Deadline", "date": {"before": today}},
                {"property": "Status", "status": {"does_not_equal": "Done"}}
            ]
        }
    }
    results = []
    has_more = True
    start_cursor = None
    while has_more:
        if start_cursor:
            payload["start_cursor"] = start_cursor
        resp = requests.post(url, headers=HEADERS, json=payload)
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
    return results

def shift_date_by_one(date_str):
    if not date_str:
        return None
    if "T" in date_str:
        dt = datetime.fromisoformat(date_str)
        return (dt + timedelta(days=1)).isoformat()
    d = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
    return (d + timedelta(days=1)).isoformat()

def update_deadline(page_id, new_start, new_end):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    date_value = {"start": new_start}
    if new_end:
        date_value["end"] = new_end
    payload = {"properties": {"Deadline": {"date": date_value}}}
    resp = requests.patch(url, headers=HEADERS, json=payload)
    resp.raise_for_status()

def main():
    today = get_today()
    print(f"\n🥊 Notion Deadline Updater — {today}")
    print("=" * 50)
    total_updated = 0
    for db_name, db_id in DATABASES.items():
        print(f"\n📂 {db_name}")
        try:
            tasks = query_overdue_tasks(db_id)
            print(f"   Task scaduti: {len(tasks)}")
            for task in tasks:
                page_id = task["id"]
                title_prop = task["properties"].get("🥊", {})
                title = title_prop["title"][0]["plain_text"] if title_prop.get("title") else "Senza titolo"
                start = task["properties"].get("Deadline", {}).get("date", {})
                if not start:
                    continue
                s = start.get("start")
                e = start.get("end")
                new_start = shift_date_by_one(s)
                new_end = shift_date_by_one(e) if e else None
                update_deadline(page_id, new_start, new_end)
                print(f"   ✅ '{title}' → {s} ➜ {new_start}")
                total_updated += 1
        except Exception as ex:
            print(f"   ❌ Errore: {ex}")
    print(f"\n✅ Totale aggiornati: {total_updated}\n")

if __name__ == "__main__":
    main()
