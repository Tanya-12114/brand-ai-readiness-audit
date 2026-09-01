#!/usr/bin/env python3
"""
structured_data_check.py -- reference implementation of structured-data-audit
steps 1-3 and 5. Read-only plain GET.

Usage: python structured_data_check.py <url>
Prints a JSON array of findings to stdout.
"""
import sys
import json

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Requires: pip install requests beautifulsoup4")

UA = "Mozilla/5.0 (compatible; brand-ai-readiness-audit/1.0)"
REQUIRED_PROPS = {
    "Organization": ["name", "url", "logo", "sameAs"],
    "Product": ["name", "image", "description", "offers"],
    "Article": ["headline", "datePublished", "dateModified", "author"],
    "BlogPosting": ["headline", "datePublished", "dateModified", "author"],
    "LocalBusiness": ["name", "address", "telephone"],
}


def fetch(url):
    return requests.get(url, headers={"User-Agent": UA}, timeout=10)


def check_jsonld(soup):
    findings = []
    blocks = soup.find_all("script", type="application/ld+json")
    if not blocks:
        findings.append({
            "id": "SD-001",
            "title": "No JSON-LD structured data on page",
            "severity": "high",
            "evidence": "0 <script type=\"application/ld+json\"> blocks found.",
            "suggested_action": {
                "summary": "Add JSON-LD (Organization/Product/Article as appropriate) with the page's core facts so assistants can extract them unambiguously.",
                "priority": "high"
            }
        })
        return findings, []

    parsed_blocks = []
    for i, b in enumerate(blocks):
        try:
            data = json.loads(b.string or "{}")
            parsed_blocks.append(data)
        except json.JSONDecodeError:
            findings.append({
                "id": f"SD-002-{i}",
                "title": "Malformed JSON-LD block",
                "severity": "medium",
                "evidence": f"Block #{i} is not valid JSON and will be silently ignored by parsers.",
                "suggested_action": {"summary": "Fix JSON syntax in the ld+json block; validate with a JSON-LD validator before deploy.", "priority": "medium"}
            })

    for i, data in enumerate(parsed_blocks):
        items = data if isinstance(data, list) else [data]
        for item in items:
            t = item.get("@type")
            types = t if isinstance(t, list) else [t]
            for typ in types:
                req = REQUIRED_PROPS.get(typ)
                if not req:
                    continue
                missing = [p for p in req if p not in item]
                if missing:
                    findings.append({
                        "id": f"SD-003-{typ}-{i}",
                        "title": f"{typ} JSON-LD missing required properties",
                        "severity": "medium",
                        "evidence": f"Block declares @type={typ} but is missing: {', '.join(missing)}",
                        "suggested_action": {"summary": f"Add {', '.join(missing)} to the {typ} block.", "priority": "medium"}
                    })
    return findings, parsed_blocks


def check_meta(soup):
    findings = []
    title = soup.find("title")
    desc = soup.find("meta", attrs={"name": "description"})
    if not title or not title.text.strip():
        findings.append({
            "id": "SD-004", "title": "Missing <title>", "severity": "medium",
            "evidence": "No non-empty <title> tag found.",
            "suggested_action": {"summary": "Add a unique, descriptive <title> to every page.", "priority": "medium"}
        })
    if not desc or not desc.get("content", "").strip():
        findings.append({
            "id": "SD-005", "title": "Missing meta description", "severity": "medium",
            "evidence": "No non-empty meta[name=description] found.",
            "suggested_action": {"summary": "Add a unique meta description summarizing the page's key facts in plain text.", "priority": "medium"}
        })
    return findings


def check_headings(soup):
    findings = []
    h1s = soup.find_all("h1")
    if len(h1s) == 0:
        findings.append({
            "id": "SD-006", "title": "No <h1> on page", "severity": "medium",
            "evidence": "0 <h1> tags found.",
            "suggested_action": {"summary": "Add a single clear <h1> stating what the page is about.", "priority": "medium"}
        })
    elif len(h1s) > 1:
        findings.append({
            "id": "SD-007", "title": "Multiple <h1> tags", "severity": "low",
            "evidence": f"{len(h1s)} <h1> tags found; ambiguous which states the page topic.",
            "suggested_action": {"summary": "Use exactly one <h1> per page; demote others to <h2>/<h3>.", "priority": "low"}
        })
    return findings


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: structured_data_check.py <url>")
    url = sys.argv[1]
    r = fetch(url)
    soup = BeautifulSoup(r.text, "html.parser")

    findings = []
    jsonld_findings, _ = check_jsonld(soup)
    findings += jsonld_findings
    findings += check_meta(soup)
    findings += check_headings(soup)

    print(json.dumps(findings, indent=2))


if __name__ == "__main__":
    main()
