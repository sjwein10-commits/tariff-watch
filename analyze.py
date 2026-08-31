import anthropic

client = anthropic.Anthropic()

SYSTEM_PROMPT = "You are an international trade economist and investment analyst who specializes in US tariff policy and its effects on prices, supply chains, equities, and global trade relationships. When analyzing events, be specific — name real companies, tickers, ETFs, and commodities. Quantify where possible."

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
                "description": "1-2 sentences explaining the real-world effect on everyday consumers — mention specific products and estimated price changes where possible.",
            },
            "retaliation_risk": {
                "type": "string",
                "description": "1-2 sentences on whether affected countries are likely to retaliate, what form it might take, and what US exports are most at risk.",
            },
            "historical_context": {
                "type": "string",
                "description": "1-2 sentences placing this in the context of US trade history — compare to prior tariff actions, trade wars, or relevant precedents.",
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
            "winners": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["category", "description"],
                },
                "description": "Industries, sectors, or company types that benefit from this tariff action. Name specific domestic producers, substitutes, or geographies that gain competitive advantage. Include 2-4 winners.",
            },
            "losers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["category", "description"],
                },
                "description": "Industries, sectors, or company types hurt by this tariff action. Include importers, manufacturers with foreign inputs, and affected end consumers. Include 2-4 losers.",
            },
            "affected_companies": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "ticker": {"type": "string"},
                        "impact": {"type": "string", "enum": ["positive", "negative", "mixed"]},
                        "reason": {"type": "string"},
                    },
                    "required": ["name", "ticker", "impact", "reason"],
                },
                "description": "Specific publicly traded companies most affected. Include 4-8 companies with real ticker symbols. Only include companies with material impact.",
            },
            "inflation_implications": {
                "type": "string",
                "description": "2-3 sentences on the inflationary effect. Mention specific price categories, CPI components, and estimated magnitude (e.g. 'could add 0.2-0.4% to core CPI').",
            },
            "supply_chain_implications": {
                "type": "string",
                "description": "2-3 sentences on supply chain disruption. Which supply chains are at risk? What sourcing shifts might occur? Which regions absorb the shock?",
            },
            "stocks_to_watch": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string"},
                        "name": {"type": "string"},
                        "direction": {"type": "string", "enum": ["up", "down"]},
                        "reason": {"type": "string"},
                    },
                    "required": ["ticker", "name", "direction", "reason"],
                },
                "description": "4-6 individual stocks most directly impacted. Mix of winners and losers. Use real ticker symbols.",
            },
            "etfs_affected": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string"},
                        "name": {"type": "string"},
                        "direction": {"type": "string", "enum": ["up", "down"]},
                        "reason": {"type": "string"},
                    },
                    "required": ["ticker", "name", "direction", "reason"],
                },
                "description": "2-4 sector or thematic ETFs affected. E.g. XME (metals), KWEB (Chinese internet), XBI (biotech), SOXX (semiconductors).",
            },
            "commodities_affected": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "direction": {"type": "string", "enum": ["up", "down"]},
                        "reason": {"type": "string"},
                    },
                    "required": ["name", "direction", "reason"],
                },
                "description": "Commodities impacted — steel, soybeans, oil, lithium, copper, etc. Include 1-4 relevant commodities.",
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
            "winners",
            "losers",
            "affected_companies",
            "inflation_implications",
            "supply_chain_implications",
            "stocks_to_watch",
            "etfs_affected",
            "commodities_affected",
        ],
    },
}


def analyze_event(title, raw_content):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        tools=[ANALYSIS_TOOL],
        tool_choice={"type": "tool", "name": "store_tariff_analysis"},
        messages=[
            {
                "role": "user",
                "content": f"Analyze this US tariff event and fill out the full analysis tool.\n\nTitle: {title}\n\nContent: {raw_content[:2000]}",
            }
        ],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "store_tariff_analysis":
            return block.input

    return None
