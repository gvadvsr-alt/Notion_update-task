import os
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()
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
}

def get_today():
    return datetime.now(ZoneInfo("Australia/Sydney")).date()

def shift_to_today(original_str, today_str):
    """Replace the date part keeping the time and timezone if present."""
    if not original_str:
        return today_str
    if "T" in original_str:
        # e.g. "2026-06-02T22:30:00.000+10:00" -> "2026-06-10T22:30:00.000+10:00"
        return today_str + original_str[10:]
    return today_str

def query_overdue_tasks(database_id):
    today = get_today().isoformat()
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    payload = {
        "filter": {
            "and": [
                {"property": "DoDate", "date": {"before": today}},
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

def update_task(page_id, new_dodate_str, new_dodate_end=None, new_start_str=None):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    dodate_date = {"start": new_dodate_str}
    if new_dodate_end:
        dodate_date["end"] = new_dodate_end
    properties = {"DoDate": {"date": dodate_date}}
    if new_start_str:
        properties["Start"] = {"date": {"start": new_start_str}}
    resp = requests.patch(url, headers=HEADERS, json={"properties": properties})
    resp.raise_for_status()

def main():
    today = get_today()
    today_str = today.isoformat()
    print(f"\nNotion DoDate Updater -- {today}")
    print("=" * 50)
    total_updated = 0
    for db_name, db_id in DATABASES.items():
        print(f"\n[{db_name}]")
        try:
            tasks = query_overdue_tasks(db_id)
            print(f"   Task scaduti: {len(tasks)}")
            for task in tasks:
                page_id = task["id"]
                title_prop = task["properties"].get("\U0001f94a", {})
                title = title_prop["title"][0]["plain_text"] if title_prop.get("title") else "Senza titolo"

                dodate = task["properties"].get("DoDate", {}).get("date")
                if not dodate or not dodate.get("start"):
                    continue
                old_dodate = dodate["start"]
                new_dodate = shift_to_today(old_dodate, today_str)

                # Shift DoDate.end if present (preserves time, changes only date)
                old_dodate_end = dodate.get("end")
                new_dodate_end = shift_to_today(old_dodate_end, today_str) if old_dodate_end else None

                # Also shift Start if set
                start_prop = task["properties"].get("Start", {}).get("date")
                new_start = None
                if start_prop and start_prop.get("start"):
                    new_start = shift_to_today(start_prop["start"], today_str)

                update_task(page_id, new_dodate, new_dodate_end, new_start)

                end_label = f"→{new_dodate_end[11:16]}" if new_dodate_end and "T" in new_dodate else ""
                start_label = f" | Start {start_prop['start'][:10]} -> {today_str}" if new_start else ""
                print(f"   OK '{title}' {old_dodate[:10]} -> {today_str}{end_label}{start_label}")
                total_updated += 1
        except Exception as ex:
            print(f"   ERRORE: {ex}")
    print(f"\nTotale aggiornati: {total_updated}\n")

if __name__ == "__main__":
    main()
