#!/usr/bin/env python3
"""
corroboration_check.py -- reference implementation of freshness-corroboration
step 1 (date extraction / staleness). Steps 2-3 (independent corroboration,
entity disambiguation) require a live web-search tool and are driven by the
calling agent using the query patterns in references/checklist.md -- this
script only handles the on-page freshness signal, read-only plain GET.

Usage: python corroboration_check.py <url>
Prints a JSON array of findings to stdout.
"""
import sys
import json
import re
import datetime

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Requires: pip install requests beautifulsoup4")

UA = "Mozilla/5.0 (compatible; brand-ai-readiness-audit/1.0)"
STALE_DAYS = 400  # ~13 months; tune per fact type in real use

DATE_META_KEYS = ["article:modified_time", "article:published_time", "og:updated_time"]
DATE_TEXT_PATTERN = re.compile(
    r"(last updated|updated on|last modified)[:\s]*([A-Za-z0-9,\s\-/]{6,25})", re.IGNORECASE
)


def fetch(url):
    return requests.get(url, headers={"User-Agent": UA}, timeout=10)


def find_jsonld_dates(soup):
    dates = []
    for b in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(b.string or "{}")
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            for key in ("dateModified", "datePublished"):
                if key in item:
                    dates.append((key, item[key]))
    return dates


def find_meta_dates(soup):
    dates = []
    for key in DATE_META_KEYS:
        tag = soup.find("meta", attrs={"property": key})
        if tag and tag.get("content"):
            dates.append((key, tag["content"]))
    return dates


def find_text_dates(soup):
    text = soup.get_text(" ", strip=True)
    m = DATE_TEXT_PATTERN.search(text)
    if m:
        return [("visible_text", m.group(2).strip())]
    return []


def parse_date(s):
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d", "%B %d, %Y", "%b %d, %Y", "%m/%d/%Y"):
        try:
            return datetime.datetime.strptime(s[:len(datetime.datetime.now().strftime(fmt))], fmt)
        except (ValueError, IndexError):
            continue
    return None


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: corroboration_check.py <url>")
    url = sys.argv[1]
    r = fetch(url)
    soup = BeautifulSoup(r.text, "html.parser")

    all_dates = find_jsonld_dates(soup) + find_meta_dates(soup) + find_text_dates(soup)
    findings = []

    if not all_dates:
        findings.append({
            "id": "FC-001",
            "title": "No freshness/date signal found on page",
            "severity": "medium",
            "evidence": f"No dateModified/datePublished JSON-LD, date meta tags, or visible 'last updated' text found on {url}.",
            "suggested_action": {
                "summary": "Add a dateModified field to JSON-LD and/or a visible 'Last updated' line for time-sensitive content.",
                "priority": "medium"
            }
        })
    else:
        now = datetime.datetime.now(datetime.timezone.utc)
        stale = []
        for source, raw in all_dates:
            dt = parse_date(raw)
            if dt:
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                age_days = (now - dt).days
                if age_days > STALE_DAYS:
                    stale.append((source, raw, age_days))
        if stale:
            findings.append({
                "id": "FC-002",
                "title": "Freshness date is stale",
                "severity": "high",
                "evidence": "; ".join(f"{s}={r} ({d} days old)" for s, r, d in stale),
                "suggested_action": {
                    "summary": "Review and refresh time-sensitive content; update dateModified once verified current, don't just bump the timestamp.",
                    "priority": "high"
                }
            })

    print(json.dumps(findings, indent=2))


if __name__ == "__main__":
    main()
