"""
Backfill intelligence fields for all existing events missing the new analysis.
Run: cd ~/tariff-watch && venv/bin/python reenrich.py
"""
from dotenv import load_dotenv
load_dotenv()

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from db import supabase
from analyze import analyze_event

CONCURRENCY = 8

NEW_FIELDS = [
    "winners", "losers", "affected_companies",
    "inflation_implications", "supply_chain_implications",
    "stocks_to_watch", "etfs_affected", "commodities_affected",
]

print_lock = threading.Lock()


def enrich(event, index, total):
    title = event["title"]
    content = event.get("raw_content") or event.get("claude_summary") or title
    analysis = analyze_event(title, content)

    if not analysis:
        with print_lock:
            print(f"[{index}/{total}] SKIP — {title[:60]}")
        return False

    update = {field: analysis.get(field) for field in NEW_FIELDS}
    update["consumer_impact"] = analysis.get("consumer_impact")
    update["retaliation_risk"] = analysis.get("retaliation_risk")
    update["historical_context"] = analysis.get("historical_context")
    update["claude_summary"] = analysis.get("claude_summary")

    supabase.table("tariff_events").update(update).eq("id", event["id"]).execute()

    companies = len(analysis.get("affected_companies") or [])
    stocks = len(analysis.get("stocks_to_watch") or [])
    with print_lock:
        print(f"[{index}/{total}] Done — {companies} cos, {stocks} stocks — {title[:55]}")
    return True


def run():
    result = supabase.table("tariff_events") \
        .select("id, title, raw_content, claude_summary") \
        .is_("winners", "null") \
        .order("created_at", desc=True) \
        .execute()

    events = result.data
    total = len(events)
    print(f"{total} events need enrichment — running {CONCURRENCY} parallel workers\n")

    succeeded = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = {
            pool.submit(enrich, event, i + 1, total): event
            for i, event in enumerate(events)
        }
        for future in as_completed(futures):
            if future.result():
                succeeded += 1
            else:
                failed += 1

    print(f"\nFinished. {succeeded} enriched, {failed} failed.")


if __name__ == "__main__":
    run()
