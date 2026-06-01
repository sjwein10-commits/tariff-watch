import anthropic

client = anthropic.Anthropic()

SYSTEM_PROMPT = "You are an international trade economist who specializes in US tariff policy and its effects on prices, supply chains, and global trade relationships."

ANALYSIS_TOOL = {
    "name": "store_tariff_analysis",
    "description": "Store structured analysis of a US tariff event",
    "input_schema": {
        "type": "object",
        "properties": {
            "products": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Affected product categories, e.g. ['Steel', 'Aluminum']",
            },
            "countries": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Affected countries, e.g. ['China', 'Canada']",
            },
            "tariff_rate_change": {
                "type": "string",
                "description": "Rate change description, e.g. '0% → 25%' or 'New 10% baseline'",
            },
            "trade_value_billions": {
                "type": "number",
                "description": "Estimated annual trade value affected in billions USD. Omit if unknown.",
            },
            "claude_summary": {
                "type": "string",
                "description": "3 sentences: what happened, who is directly affected, and the immediate economic consequence.",
            },
            "claude_impact_score": {
                "type": "integer",
                "description": "Impact score 1 (minor procedural change) to 10 (historic, economy-wide effect)",
            },
            "claude_impact_label": {
                "type": "string",
                "enum": ["Low", "Medium", "High", "Critical"],
            },
            "affected_sectors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Economic sectors affected, e.g. ['Automotive', 'Agriculture', 'Technology']",
            },
            "consumer_impact": {
                "type": "string",
                "description": "1-2 sentences explaining the real-world effect on everyday consumers — mention specific products and estimated price changes where possible. E.g. 'Expect washing machine prices to rise ~$100. Cars could cost $800-1,500 more within a year.'",
            },
            "retaliation_risk": {
                "type": "string",
                "description": "1-2 sentences on whether affected countries are likely to retaliate, what form it might take, and what US exports are most at risk. E.g. 'China is likely to target US agricultural exports, particularly soybeans and pork, which would hurt Midwestern farmers.'",
            },
            "historical_context": {
                "type": "string",
                "description": "1-2 sentences placing this in the context of US trade history — compare to prior tariff actions, trade wars, or relevant precedents. E.g. 'The last time the US imposed steel tariffs of this scale was under Bush in 2002, which the WTO ruled illegal 18 months later.'",
            },
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
                "description": "Story thread slugs this event belongs to. Can be empty array if none apply.",
            },
        },
        "required": [
            "products",
            "countries",
            "tariff_rate_change",
            "claude_summary",
            "claude_impact_score",
            "claude_impact_label",
            "affected_sectors",
            "consumer_impact",
            "retaliation_risk",
            "historical_context",
            "story_tags",
        ],
    },
}


def analyze_event(title, raw_content):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        tools=[ANALYSIS_TOOL],
        tool_choice={"type": "tool", "name": "store_tariff_analysis"},
        messages=[
            {
                "role": "user",
                "content": f"Analyze this US tariff event and fill out the analysis tool.\n\nTitle: {title}\n\nContent: {raw_content[:2000]}",
            }
        ],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "store_tariff_analysis":
            return block.input

    return None
