import requests
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta


def fetch_federal_register(days_back=7):
    since = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    resp = requests.get(
        "https://www.federalregister.gov/api/v1/documents.json",
        params={
            "conditions[term]": "tariff",
            "conditions[publication_date][gte]": since,
            "per_page": 20,
            "order": "newest",
        },
        timeout=15,
    )
    resp.raise_for_status()

    events = []
    for r in resp.json().get("results", []):
        events.append({
            "title": r.get("title", ""),
            "event_date": r.get("publication_date", ""),
            "source_url": r.get("html_url", ""),
            "source_type": "federal_register",
            "raw_content": r.get("abstract") or r.get("title", ""),
        })
    return events


def fetch_google_news(days_back=7):
    queries = [
        "Trump tariff",
        "US tariff impact consumers",
        "US trade war 2025",
        "import tariff prices",
    ]

    seen_urls = set()
    events = []
    cutoff = datetime.now() - timedelta(days=days_back)

    for query in queries:
        try:
            resp = requests.get(
                "https://news.google.com/rss/search",
                params={"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"},
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()

            root = ET.fromstring(resp.content)
            items = root.findall(".//item")

            for item in items:
                url   = (item.findtext("link") or "").strip()
                title = (item.findtext("title") or "").strip()
                pub   = (item.findtext("pubDate") or "").strip()
                desc  = (item.findtext("description") or "").strip()

                if not url or url in seen_urls:
                    continue

                # Parse date
                try:
                    pub_dt = datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %Z")
                except ValueError:
                    pub_dt = datetime.now()

                if pub_dt < cutoff:
                    continue

                seen_urls.add(url)
                events.append({
                    "title": title,
                    "event_date": pub_dt.strftime("%Y-%m-%d"),
                    "source_url": url,
                    "source_type": "news",
                    "raw_content": desc or title,
                })

        except Exception as e:
            print(f"  Google News fetch failed for '{query}': {e}")

    return events


def fetch_news(days_back=7):
    api_key = os.environ.get("NEWS_API_KEY")
    if not api_key:
        return []

    since = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%S")
    resp = requests.get(
        "https://newsapi.org/v2/everything",
        params={
            "q": '"US tariff" OR "trade tariff" OR "import tariff"',
            "language": "en",
            "sortBy": "publishedAt",
            "from": since,
            "pageSize": 20,
            "apiKey": api_key,
        },
        timeout=15,
    )
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"  NewsAPI unavailable: {e}")
        return []

    events = []
    for a in resp.json().get("articles", []):
        events.append({
            "title": a.get("title", ""),
            "event_date": (a.get("publishedAt") or "")[:10],
            "source_url": a.get("url", ""),
            "source_type": "news",
            "raw_content": " ".join(filter(None, [a.get("description"), a.get("content")])),
        })
    return events
