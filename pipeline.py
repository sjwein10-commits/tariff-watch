from dotenv import load_dotenv
load_dotenv()

import re
from concurrent.futures import ThreadPoolExecutor
from itertools import chain, zip_longest

from db import supabase
from fetch import fetch_federal_register, fetch_news, fetch_google_news
from analyze import analyze_event

MAX_NEW_EVENTS_PER_RUN = 12
CONCURRENCY = 4
TARIFF_KEYWORDS = {"tariff", "tariffs", "duty", "duties", "trade war", "import tax", "customs", "section 301", "section 232", "trade deal", "trade agreement"}
STORY_SLUGS = ["us-china-trade-war", "canada-mexico-tensions", "steel-aluminum", "liberation-day", "phase-one-deal"]


def fetch_all(column):
    # Supabase caps each response at 1000 rows, so page through the whole table
    rows, start, page_size = [], 0, 1000
    while True:
        page = supabase.table("tariff_events").select(column).range(start, start + page_size - 1).execute().data
        rows.extend(page)
        if len(page) < page_size:
            return rows
        start += page_size


def normalize_title(title):
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()[:80]


def is_relevant(event):
    text = (event["title"] + " " + event.get("raw_content", "")).lower()
    return any(kw in text for kw in TARIFF_KEYWORDS)


def interleave(*sources):
    # Alternate between sources so one noisy feed can't fill the whole per-run cap
    return [e for e in chain.from_iterable(zip_longest(*sources)) if e]


def analyze(event):
    try:
        return event, analyze_event(event["title"], event.get("raw_content", ""))
    except Exception as e:
        print(f"    Analysis failed for '{event['title'][:60]}': {e}")
        return event, None


def refresh_story_counts():
    for slug in STORY_SLUGS:
        count = supabase.table("tariff_events").select("id", count="exact").contains("story_tags", [slug]).limit(1).execute().count
        supabase.table("stories").update({"event_count": count}).eq("slug", slug).execute()


def run():
    print("Fetching tariff events...")
    existing = fetch_all("source_url, title")
    existing_urls = {r["source_url"] for r in existing if r["source_url"]}
    existing_titles = {normalize_title(r["title"]) for r in existing if r["title"]}

    candidates = interleave(fetch_federal_register(days_back=7), fetch_google_news(days_back=7), fetch_news(days_back=7))

    new_events, seen_titles = [], set(existing_titles)
    for e in candidates:
        key = normalize_title(e["title"])
        if e["source_url"] in existing_urls or key in seen_titles or not is_relevant(e):
            continue
        seen_titles.add(key)
        new_events.append(e)

    print(f"Found {len(new_events)} new events (skipped {len(candidates) - len(new_events)} duplicates or irrelevant)")
    if len(new_events) > MAX_NEW_EVENTS_PER_RUN:
        print(f"Capping at {MAX_NEW_EVENTS_PER_RUN}")
        new_events = new_events[:MAX_NEW_EVENTS_PER_RUN]

    saved = 0
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        for event, analysis in pool.map(analyze, new_events):
            if not analysis:
                print(f"  Skipped: {event['title'][:70]}")
                continue
            supabase.table("tariff_events").insert({**event, **analysis}).execute()
            print(f"  Saved ({analysis['claude_impact_score']}/10 {analysis['claude_impact_label']}): {event['title'][:70]}")
            saved += 1

    refresh_story_counts()
    print(f"\nDone. {saved} new events saved.")


if __name__ == "__main__":
    run()
