#!/usr/bin/env python3
"""
crawl_check.py -- reference implementation of crawl-render-audit steps 1-3, 5-6.

Read-only: issues plain GET requests only, respects robots.txt, caps page count,
adds a short delay between requests. Does not execute JavaScript (step 4's
render-diff should be done by the calling agent using a headless-browser tool
if one is available; this script approximates it via a heuristic).

Usage: python crawl_check.py <url> [max_pages]
Prints a JSON array of findings to stdout.
"""
import sys
import time
import json
import re
from urllib.parse import urljoin, urlparse
from urllib import robotparser

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Requires: pip install requests beautifulsoup4")

UA = "Mozilla/5.0 (compatible; brand-ai-readiness-audit/1.0; +https://agentskills.io)"
KEY_BOTS = ["*", "GPTBot", "Google-Extended", "ChatGPT-User", "CCBot", "anthropic-ai", "PerplexityBot"]
TIMEOUT = 10
DELAY = 0.5


def fetch(url):
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, allow_redirects=True)
        return r
    except requests.RequestException as e:
        return None


def check_robots(base):
    findings = []
    robots_url = urljoin(base, "/robots.txt")
    r = fetch(robots_url)
    blocked_core = []
    if r and r.status_code == 200:
        rp = robotparser.RobotFileParser()
        rp.parse(r.text.splitlines())
        for bot in KEY_BOTS:
            if not rp.can_fetch(bot, base):
                blocked_core.append(bot)
    if blocked_core:
        findings.append({
            "id": "CR-001",
            "title": "robots.txt blocks AI-assistant / search crawlers from core content",
            "severity": "critical",
            "evidence": f"robots.txt disallows: {', '.join(blocked_core)} at {robots_url}",
            "suggested_action": {
                "summary": "Remove or narrow the Disallow rules for AI/search agents so core content paths (product, blog, docs, marketing) are fetchable; keep auth/cart paths blocked.",
                "priority": "critical"
            }
        })
    return findings, r.text if r and r.status_code == 200 else ""


def check_sitemap(base):
    findings = []
    r = fetch(urljoin(base, "/sitemap.xml"))
    if not r or r.status_code != 200 or "<urlset" not in r.text and "<sitemapindex" not in r.text:
        findings.append({
            "id": "CR-002",
            "title": "No valid sitemap.xml found",
            "severity": "medium",
            "evidence": f"GET /sitemap.xml returned status {r.status_code if r else 'no response'}",
            "suggested_action": {
                "summary": "Publish a sitemap.xml listing all indexable URLs and reference it in robots.txt so new/updated pages are discovered faster.",
                "priority": "medium"
            }
        })
    return findings


def extract_links(base, html):
    soup = BeautifulSoup(html, "html.parser")
    domain = urlparse(base).netloc
    links = set()
    for a in soup.find_all("a", href=True):
        full = urljoin(base, a["href"])
        if urlparse(full).netloc == domain:
            links.add(full.split("#")[0])
    return links


def check_pages(base, homepage_html, max_pages):
    findings = []
    links = list(extract_links(base, homepage_html))[:max_pages]
    broken = []
    long_chains = []
    text_ratios = []
    for url in links:
        time.sleep(DELAY)
        r = fetch(url)
        if r is None or r.status_code >= 400:
            broken.append((url, r.status_code if r else "no response"))
            continue
        if len(r.history) >= 3:
            long_chains.append((url, len(r.history)))
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        visible_text = soup.get_text(strip=True)
        text_ratios.append((url, len(visible_text)))

    if broken:
        findings.append({
            "id": "CR-003",
            "title": "Linked pages return errors",
            "severity": "high",
            "evidence": f"{len(broken)} of {len(links)} linked pages failed: " + "; ".join(f"{u} -> {s}" for u, s in broken[:5]),
            "suggested_action": {
                "summary": "Fix or remove links to dead pages; add redirects for moved content.",
                "priority": "high"
            }
        })
    if long_chains:
        findings.append({
            "id": "CR-004",
            "title": "Long or inconsistent redirect chains",
            "severity": "medium",
            "evidence": "; ".join(f"{u}: {n} hops" for u, n in long_chains[:5]),
            "suggested_action": {
                "summary": "Canonicalize internal links to the final destination URL directly; collapse redirect chains to a single hop.",
                "priority": "medium"
            }
        })
    thin = [u for u, n in text_ratios if n < 200]
    if len(thin) > max(1, len(text_ratios) * 0.3):
        findings.append({
            "id": "CR-005",
            "title": "Many pages have very little extractable text (possible JS-only rendering)",
            "severity": "critical",
            "evidence": f"{len(thin)} of {len(text_ratios)} sampled pages had under 200 characters of visible text in raw HTML.",
            "suggested_action": {
                "summary": "Server-render (SSR/SSG) core content, or add a <noscript> fallback with the essential facts in plain text, so non-JS fetchers can read the page.",
                "priority": "critical"
            }
        })
    return findings


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: crawl_check.py <url> [max_pages]")
    base = sys.argv[1]
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 15

    findings = []
    robots_findings, _ = check_robots(base)
    findings += robots_findings
    findings += check_sitemap(base)

    home = fetch(base)
    if home and home.status_code == 200:
        findings += check_pages(base, home.text, max_pages)
    else:
        findings.append({
            "id": "CR-000",
            "title": "Homepage unreachable",
            "severity": "critical",
            "evidence": f"GET {base} returned {home.status_code if home else 'no response'}",
            "suggested_action": {"summary": "Investigate hosting/DNS/TLS issues preventing basic access.", "priority": "critical"}
        })

    print(json.dumps(findings, indent=2))


if __name__ == "__main__":
    main()
