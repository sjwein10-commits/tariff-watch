from dotenv import load_dotenv
load_dotenv()

from db import supabase
from fetch import fetch_federal_register, fetch_news, fetch_google_news
from analyze import analyze_event

MAX_NEW_EVENTS_PER_RUN = 10
TARIFF_KEYWORDS = {"tariff", "tariffs", "duty", "duties", "trade war", "import tax", "customs", "section 301", "section 232", "trade deal", "trade agreement"}


def get_existing_urls():
    result = supabase.table("tariff_events").select("source_url").execute()
    return {row["source_url"] for row in result.data if row["source_url"]}


def is_relevant(event):
    text = (event["title"] + " " + event.get("raw_content", "")).lower()
    return any(kw in text for kw in TARIFF_KEYWORDS)


def run():
    print("Fetching tariff events...")
    existing_urls = get_existing_urls()

    candidates = fetch_federal_register(days_back=7) + fetch_google_news(days_back=7) + fetch_news(days_back=7)
    new_events = [e for e in candidates if e["source_url"] not in existing_urls and is_relevant(e)]

    if len(new_events) > MAX_NEW_EVENTS_PER_RUN:
        print(f"Capping at {MAX_NEW_EVENTS_PER_RUN} events (found {len(new_events)})")
        new_events = new_events[:MAX_NEW_EVENTS_PER_RUN]

    print(f"Found {len(new_events)} new events (skipped {len(candidates) - len(new_events)} already in DB or irrelevant)")

    saved = 0
    for event in new_events:
        print(f"  Analyzing: {event['title'][:70]}...")
        analysis = analyze_event(event["title"], event.get("raw_content", ""))

        if not analysis:
            print("    Skipped — analysis returned nothing")
            continue

        supabase.table("tariff_events").insert({**event, **analysis}).execute()
        print(f"    Saved (impact {analysis['claude_impact_score']}/10 — {analysis['claude_impact_label']})")
        saved += 1

    print(f"\nDone. {saved} new events saved.")


if __name__ == "__main__":
    run()
