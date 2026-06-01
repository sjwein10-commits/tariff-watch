"""
Backfill consumer_impact, retaliation_risk, and historical_context
for all existing events that are missing the new fields.
"""
from dotenv import load_dotenv
load_dotenv()

from db import supabase
from analyze import analyze_event


def run():
    result = supabase.table("tariff_events") \
        .select("id, title, raw_content, claude_summary") \
        .is_("consumer_impact", "null") \
        .execute()

    events = result.data
    print(f"{len(events)} events need enrichment")

    for i, event in enumerate(events, 1):
        title = event["title"]
        print(f"[{i}/{len(events)}] {title[:70]}...")

        analysis = analyze_event(
            title,
            event.get("raw_content") or event.get("claude_summary") or title
        )

        if not analysis:
            print("  Skipped — analysis returned nothing")
            continue

        supabase.table("tariff_events").update({
            "consumer_impact":   analysis.get("consumer_impact"),
            "retaliation_risk":  analysis.get("retaliation_risk"),
            "historical_context": analysis.get("historical_context"),
            # Also refresh the summary with the improved prompt
            "claude_summary":    analysis.get("claude_summary"),
        }).eq("id", event["id"]).execute()

        print(f"  Done")

    print(f"\nFinished. {len(events)} events enriched.")


if __name__ == "__main__":
    run()
