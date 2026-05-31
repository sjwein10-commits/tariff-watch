import requests
import os
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
    resp.raise_for_status()

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
