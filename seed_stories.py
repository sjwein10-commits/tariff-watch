"""
Seeds the stories table and tags all existing events with story slugs.
Run once after adding the stories table to Supabase.
"""
from dotenv import load_dotenv
load_dotenv()

import anthropic
from db import supabase

client = anthropic.Anthropic()

STORIES = [
    {
        "slug": "us-china-trade-war",
        "title": "US-China Trade War",
        "description": "From the first Section 301 tariffs in 2018 through escalation, the Phase One deal, and the 2025 trade truce — the defining trade conflict of the era.",
    },
    {
        "slug": "canada-mexico-tensions",
        "title": "Canada & Mexico Tensions",
        "description": "Trump's 2025 IEEPA tariffs on America's two largest trading partners, the 30-day pause, and the ongoing uncertainty for North American supply chains.",
    },
    {
        "slug": "steel-aluminum",
        "title": "Steel & Aluminum (Section 232)",
        "description": "The 2018 national security tariffs on steel and aluminum that reshaped global metals trade and triggered retaliatory tariffs from allies and rivals alike.",
    },
    {
        "slug": "liberation-day",
        "title": "Liberation Day & Global Tariffs",
        "description": "Trump's April 2025 announcement of sweeping reciprocal tariffs on 185+ countries — the most aggressive US trade action since Smoot-Hawley — and the 90-day pause that followed.",
    },
    {
        "slug": "phase-one-deal",
        "title": "Phase One Trade Deal",
        "description": "The January 2020 US-China partial truce that paused the trade war without resolving it, and its legacy through subsequent administrations.",
    },
]

TAGGING_TOOL = {
    "name": "assign_story_tags",
    "description": "Assign story thread slugs to a tariff event",
    "input_schema": {
        "type": "object",
        "properties": {
            "story_tags": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "us-china-trade-war",
                        "canada-mexico-tensions",
                        "steel-aluminum",
                        "liberation-day",
                        "phase-one-deal",
                    ],
                },
                "description": "Which story threads this event belongs to. Can be empty if none apply.",
            }
        },
        "required": ["story_tags"],
    },
}


def tag_event(title, summary, countries, products):
    context = f"Title: {title}\nSummary: {summary or ''}\nCountries: {', '.join(countries or [])}\nProducts: {', '.join(products or [])}"
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        tools=[TAGGING_TOOL],
        tool_choice={"type": "tool", "name": "assign_story_tags"},
        messages=[{
            "role": "user",
            "content": f"Which of the predefined story threads does this tariff event belong to? It can belong to multiple or none.\n\n{context}",
        }],
    )
    for block in response.content:
        if block.type == "tool_use":
            return block.input.get("story_tags", [])
    return []


def run():
    # Seed stories
    print("Seeding stories...")
    for story in STORIES:
        existing = supabase.table("stories").select("id").eq("slug", story["slug"]).execute()
        if existing.data:
            print(f"  Already exists: {story['slug']}")
        else:
            supabase.table("stories").insert(story).execute()
            print(f"  Inserted: {story['slug']}")

    # Tag existing events
    events = supabase.table("tariff_events") \
        .select("id, title, claude_summary, countries, products") \
        .is_("story_tags", "null") \
        .execute().data

    print(f"\nTagging {len(events)} events...")
    tag_counts = {s["slug"]: 0 for s in STORIES}

    for i, event in enumerate(events, 1):
        print(f"  [{i}/{len(events)}] {event['title'][:65]}...")
        tags = tag_event(
            event["title"],
            event.get("claude_summary"),
            event.get("countries"),
            event.get("products"),
        )
        supabase.table("tariff_events").update({"story_tags": tags}).eq("id", event["id"]).execute()
        for t in tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1
        if tags:
            print(f"    → {', '.join(tags)}")

    # Update event counts on stories
    print("\nUpdating story event counts...")
    for slug, count in tag_counts.items():
        supabase.table("stories").update({"event_count": count}).eq("slug", slug).execute()

    print("\nDone.")


if __name__ == "__main__":
    run()
