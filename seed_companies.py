"""
Seed the companies table with major public companies and AI-generated trade exposure scores.
Run once: cd ~/tariff-watch && venv/bin/python seed_companies.py
"""
from dotenv import load_dotenv
load_dotenv()

import anthropic
from db import supabase

client = anthropic.Anthropic()

COMPANIES = [
    # Technology
    {"ticker": "AAPL", "name": "Apple", "sector": "Technology", "description": "Consumer electronics giant; assembles ~90% of products in China via Foxconn and Pegatron"},
    {"ticker": "NVDA", "name": "Nvidia", "sector": "Technology", "description": "GPU/AI chip designer; subject to US export controls on advanced chips to China; ~20% of revenue from China"},
    {"ticker": "QCOM", "name": "Qualcomm", "sector": "Technology", "description": "Mobile chip designer; ~60% of revenue from China; heavily exposed to US-China tech restrictions"},
    {"ticker": "INTC", "name": "Intel", "sector": "Technology", "description": "Semiconductor manufacturer; building US fabs; subject to export controls on advanced chips"},
    {"ticker": "AMAT", "name": "Applied Materials", "sector": "Technology", "description": "Semiconductor equipment maker; subject to export controls restricting sales to Chinese chipmakers"},
    {"ticker": "LRCX", "name": "Lam Research", "sector": "Technology", "description": "Semiconductor etch equipment; subject to US export controls; ~30% China revenue"},
    {"ticker": "MU", "name": "Micron Technology", "sector": "Technology", "description": "Memory chip maker; banned from selling to Chinese critical infrastructure; China is ~10% of revenue"},
    {"ticker": "DELL", "name": "Dell Technologies", "sector": "Technology", "description": "PC and server maker; sourcing shifting out of China; significant import dependency"},
    {"ticker": "HPQ", "name": "HP Inc", "sector": "Technology", "description": "PC and printing hardware; majority of products manufactured in Asia; exposed to tariffs on electronics"},
    # Auto
    {"ticker": "F", "name": "Ford Motor", "sector": "Automotive", "description": "Major US automaker; produces in Mexico (F-150, Mustang Mach-E); exposed to steel/aluminum tariffs and USMCA rules"},
    {"ticker": "GM", "name": "General Motors", "sector": "Automotive", "description": "Large automaker with major Mexico production; exposed to USMCA rules, steel tariffs, and EV battery supply chain"},
    {"ticker": "TSLA", "name": "Tesla", "sector": "Automotive", "description": "EV maker with Shanghai gigafactory (sells into China); sources lithium and battery materials globally"},
    {"ticker": "STLA", "name": "Stellantis", "sector": "Automotive", "description": "Chrysler/Jeep/RAM parent; heavy Mexico/Canada production; exposed to USMCA tariff changes"},
    # Retail
    {"ticker": "WMT", "name": "Walmart", "sector": "Retail", "description": "Largest US retailer; historically ~70% of goods sourced from China; has been diversifying to Vietnam, India"},
    {"ticker": "TGT", "name": "Target", "sector": "Retail", "description": "Mass retailer with significant China-sourced private label goods; directly exposed to consumer goods tariffs"},
    {"ticker": "AMZN", "name": "Amazon", "sector": "Retail/Tech", "description": "E-commerce and cloud giant; marketplace sellers heavily import from China; AWS unaffected"},
    {"ticker": "COST", "name": "Costco", "sector": "Retail", "description": "Warehouse retailer; significant private-label sourcing from Asia; passing costs through to members"},
    {"ticker": "HD", "name": "Home Depot", "sector": "Retail", "description": "Home improvement retailer; ~40% of products sourced from China (tools, hardware, appliances)"},
    {"ticker": "LOW", "name": "Lowe's", "sector": "Retail", "description": "Home improvement retailer; similar China import exposure to Home Depot across tools and building materials"},
    # Apparel
    {"ticker": "NKE", "name": "Nike", "sector": "Apparel", "description": "Athletic apparel leader; shifted manufacturing to Vietnam (~50%) and Indonesia after China tariffs; still exposed"},
    {"ticker": "PVH", "name": "PVH Corp", "sector": "Apparel", "description": "Calvin Klein/Tommy Hilfiger parent; significant Asia sourcing; directly impacted by apparel tariffs"},
    {"ticker": "LULU", "name": "Lululemon", "sector": "Apparel", "description": "Premium athletic wear; manufactures primarily in Vietnam, Cambodia, and China; exposed to apparel tariffs"},
    {"ticker": "VFC", "name": "VF Corporation", "sector": "Apparel", "description": "North Face/Timberland parent; heavy Asia sourcing; exposed to broad apparel and footwear tariffs"},
    {"ticker": "HBI", "name": "Hanesbrands", "sector": "Apparel", "description": "Basics apparel maker; sources from Central America and Asia; exposed to cotton and finished goods tariffs"},
    # Industrial
    {"ticker": "CAT", "name": "Caterpillar", "sector": "Industrials", "description": "Heavy equipment maker; sells into China (~5% revenue); uses steel/aluminum inputs; exposed to retaliatory tariffs"},
    {"ticker": "DE", "name": "Deere & Company", "sector": "Industrials", "description": "Farm and construction equipment; sells into China; exposed to agricultural retaliatory tariffs on US soybeans"},
    {"ticker": "HON", "name": "Honeywell", "sector": "Industrials", "description": "Diversified industrial conglomerate; global supply chain; China revenue ~10%; aerospace components exposed"},
    {"ticker": "MMM", "name": "3M", "sector": "Industrials", "description": "Diversified manufacturer; significant China manufacturing and revenue; exposed to electronics and industrial tariffs"},
    {"ticker": "EMR", "name": "Emerson Electric", "sector": "Industrials", "description": "Industrial automation maker; China revenue ~15%; supply chain exposed to tariffs on industrial components"},
    {"ticker": "ETN", "name": "Eaton Corporation", "sector": "Industrials", "description": "Power management company; global supply chain for electrical components; Mexico manufacturing exposed"},
    {"ticker": "ROK", "name": "Rockwell Automation", "sector": "Industrials", "description": "Factory automation; exposed to US-China tech decoupling; industrial equipment tariffs"},
    {"ticker": "GE", "name": "GE Aerospace", "sector": "Industrials", "description": "Jet engine maker; global supply chain; China is a key aviation market; engine components crossing borders"},
    # Steel & Metals
    {"ticker": "NUE", "name": "Nucor", "sector": "Steel & Metals", "description": "Largest US steel producer; direct beneficiary of Section 232 steel tariffs and protectionist trade policy"},
    {"ticker": "X", "name": "US Steel", "sector": "Steel & Metals", "description": "Major integrated steel producer; benefits from import tariffs on foreign steel; domestic pricing power"},
    {"ticker": "CLF", "name": "Cleveland-Cliffs", "sector": "Steel & Metals", "description": "Flat-rolled steel producer; strong tariff beneficiary; domestic auto OEM supplier"},
    {"ticker": "AA", "name": "Alcoa", "sector": "Steel & Metals", "description": "Aluminum producer; benefits from Section 232 aluminum tariffs; global bauxite supply chain"},
    # Agriculture
    {"ticker": "ADM", "name": "Archer-Daniels-Midland", "sector": "Agriculture", "description": "Ag commodities giant; soybean exports to China directly impacted by retaliatory tariffs; major trade exposure"},
    {"ticker": "BG", "name": "Bunge", "sector": "Agriculture", "description": "Global agribusiness; soybean/grain trading exposed to US-China ag retaliatory tariffs"},
    {"ticker": "MOS", "name": "Mosaic", "sector": "Agriculture", "description": "Fertilizer maker; potash and phosphate trade exposed to tariffs on Canadian and Moroccan imports"},
    {"ticker": "TSN", "name": "Tyson Foods", "sector": "Agriculture", "description": "Largest US meat company; pork and poultry exports to China at risk from retaliatory tariffs"},
    {"ticker": "HRL", "name": "Hormel Foods", "sector": "Agriculture", "description": "SPAM/Jennie-O maker; exports pork to China; exposed to agricultural retaliatory tariffs"},
    # Energy
    {"ticker": "XOM", "name": "ExxonMobil", "sector": "Energy", "description": "Oil major; LNG exports to China; global refining supply chains; less direct tariff exposure than goods"},
    {"ticker": "CVX", "name": "Chevron", "sector": "Energy", "description": "Oil major; global operations; LNG and crude export volumes sensitive to trade relationship with China"},
    # Pharma
    {"ticker": "LLY", "name": "Eli Lilly", "sector": "Pharmaceuticals", "description": "Pharma leader; ~80% of active pharmaceutical ingredients (APIs) imported from China/India; supply chain risk"},
    {"ticker": "PFE", "name": "Pfizer", "sector": "Pharmaceuticals", "description": "Major pharma; significant API and finished goods imports from China and India; exposed to pharma tariff proposals"},
    {"ticker": "MRK", "name": "Merck", "sector": "Pharmaceuticals", "description": "Pharma giant; API import dependency from China; manufacturing in Ireland and Singapore with US sales"},
    {"ticker": "ABBV", "name": "AbbVie", "sector": "Pharmaceuticals", "description": "Biotech/pharma; Humira and oncology portfolio; some API exposure but less China-dependent than generic makers"},
    # Logistics
    {"ticker": "FDX", "name": "FedEx", "sector": "Logistics", "description": "Global logistics; trade volume directly tied to cross-border goods flows; tariffs reduce e-commerce shipments"},
    {"ticker": "UPS", "name": "UPS", "sector": "Logistics", "description": "Package delivery; global trade volumes drive revenue; e-commerce shipments from China directly exposed"},
    # Solar/Clean Energy
    {"ticker": "FSLR", "name": "First Solar", "sector": "Clean Energy", "description": "US domestic thin-film solar panel maker; direct beneficiary of tariffs on Chinese solar panels"},
    {"ticker": "ENPH", "name": "Enphase Energy", "sector": "Clean Energy", "description": "Solar microinverter maker; manufactures in US and Mexico; benefits from solar tariffs but exposed to component costs"},
    # Semiconductors (Foundry)
    {"ticker": "TSM", "name": "TSMC", "sector": "Technology", "description": "World's largest chip foundry; Taiwan geopolitical risk; building Arizona fabs; subject to export controls"},
    {"ticker": "AMD", "name": "Advanced Micro Devices", "sector": "Technology", "description": "CPU/GPU designer; ~20% China revenue; subject to export controls on advanced AI chips to China"},
    # Chemicals
    {"ticker": "DOW", "name": "Dow", "sector": "Chemicals", "description": "Chemical maker; global supply chain for plastics and chemicals; ethylene exports exposed to trade tensions"},
    {"ticker": "LYB", "name": "LyondellBasell", "sector": "Chemicals", "description": "Plastics/chemicals maker; exposed to tariffs on chemical imports and retaliatory actions on US exports"},
    # Consumer goods
    {"ticker": "PG", "name": "Procter & Gamble", "sector": "Consumer Goods", "description": "Consumer goods giant; global supply chain; some China manufacturing; commodity input costs affected by tariffs"},
    {"ticker": "CL", "name": "Colgate-Palmolive", "sector": "Consumer Goods", "description": "Oral care and personal products; EM-heavy revenue; Latin America and China exposure; input cost tariff risk"},
    {"ticker": "KMB", "name": "Kimberly-Clark", "sector": "Consumer Goods", "description": "Tissue/diaper maker; global manufacturing; pulp and fiber input costs exposed to tariff-driven commodity shifts"},
    # Tech Hardware
    {"ticker": "CSCO", "name": "Cisco Systems", "sector": "Technology", "description": "Network equipment maker; banned from Chinese government contracts; significant China revenue loss from restrictions"},
    {"ticker": "KEYS", "name": "Keysight Technologies", "sector": "Technology", "description": "Test and measurement equipment; subject to export controls; significant China revenue (~20%)"},
]

SCORING_TOOL = {
    "name": "score_company",
    "description": "Score a public company's exposure to US tariff and trade policy on four dimensions",
    "input_schema": {
        "type": "object",
        "properties": {
            "tariff_exposure_score": {
                "type": "integer",
                "description": "0-100. How directly exposed is this company to US tariff actions? 0=no exposure (pure domestic services), 100=existential threat (single-source importer).",
            },
            "china_exposure_score": {
                "type": "integer",
                "description": "0-100. How exposed is this company to US-China trade tensions? Consider both manufacturing in China and revenue from China sales.",
            },
            "supply_chain_risk_score": {
                "type": "integer",
                "description": "0-100. How vulnerable is this company's supply chain to tariff-driven disruption? Consider geographic concentration, switching costs, and lead times.",
            },
            "import_dependency_score": {
                "type": "integer",
                "description": "0-100. How dependent is this company on imported goods or components? 0=fully domestic, 100=entirely import-dependent.",
            },
            "score_rationale": {
                "type": "string",
                "description": "2-3 sentences explaining the scores. Be specific about manufacturing locations, revenue geography, and key trade dependencies.",
            },
            "key_risks": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3-5 specific trade-related risks for this company. Be concrete — name tariff rates, product categories, retaliatory actions.",
            },
            "key_opportunities": {
                "type": "array",
                "items": {"type": "string"},
                "description": "2-3 trade-related opportunities. E.g. reshoring beneficiary, domestic substitute, supply chain winner.",
            },
        },
        "required": [
            "tariff_exposure_score",
            "china_exposure_score",
            "supply_chain_risk_score",
            "import_dependency_score",
            "score_rationale",
            "key_risks",
            "key_opportunities",
        ],
    },
}

SYSTEM_PROMPT = "You are a trade policy analyst scoring major public companies on their exposure to US tariff and trade policy. Use your knowledge of each company's supply chain, manufacturing locations, revenue by geography, and import dependencies to produce precise, well-calibrated scores."


def score_company(company):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        tools=[SCORING_TOOL],
        tool_choice={"type": "tool", "name": "score_company"},
        messages=[{
            "role": "user",
            "content": f"Score {company['name']} ({company['ticker']}, sector: {company['sector']}) on trade/tariff exposure.\n\nContext: {company['description']}",
        }],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "score_company":
            return block.input
    return None


def run():
    existing = supabase.table("companies").select("ticker").execute()
    existing_tickers = {row["ticker"] for row in existing.data}
    to_seed = [c for c in COMPANIES if c["ticker"] not in existing_tickers]

    print(f"{len(to_seed)} companies to score ({len(existing_tickers)} already in DB)")

    succeeded = 0
    for i, company in enumerate(to_seed, 1):
        print(f"[{i}/{len(to_seed)}] {company['name']} ({company['ticker']})...")
        scores = score_company(company)

        if not scores:
            print(f"  Failed to score")
            continue

        record = {**company, **scores}
        supabase.table("companies").insert(record).execute()
        print(f"  Tariff: {scores['tariff_exposure_score']} | China: {scores['china_exposure_score']} | Supply Chain: {scores['supply_chain_risk_score']} | Import: {scores['import_dependency_score']}")
        succeeded += 1

    print(f"\nDone. {succeeded} companies seeded.")


if __name__ == "__main__":
    run()
