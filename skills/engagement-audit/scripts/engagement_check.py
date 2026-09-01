#!/usr/bin/env python3
"""
engagement_check.py -- reference implementation of engagement-audit checks
inferable from static HTML (orientation, CTA, reachability, mobile viewport,
trust signals). Checks involving client-side/JS behavior (context retention,
interstitials, autoplay, layout shift) are noted as unverifiable here and
should be confirmed by the calling agent with a browser-rendering tool.
Read-only plain GET.

Usage: python engagement_check.py <url>
Prints a JSON array of findings to stdout.
"""
import sys
import json
import re

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Requires: pip install requests beautifulsoup4")

UA = "Mozilla/5.0 (compatible; brand-ai-readiness-audit/1.0)"
CTA_WORDS = re.compile(r"\b(buy|sign up|get started|contact|book|subscribe|add to cart|learn more|request|download|try)\b", re.I)
CONTACT_WORDS = re.compile(r"\b(contact|support|help|email us|call us)\b", re.I)
TRUST_WORDS = re.compile(r"\b(review|testimonial|case study|certified|accredited|as seen in|trusted by)\b", re.I)


def fetch(url):
    return requests.get(url, headers={"User-Agent": UA}, timeout=10)


def check_orientation(soup):
    findings = []
    breadcrumb = soup.find(attrs={"class": re.compile("breadcrumb", re.I)}) or soup.find(attrs={"aria-label": re.compile("breadcrumb", re.I)})
    nav = soup.find("nav")
    if not breadcrumb and not (nav and nav.find(attrs={"aria-current": True})):
        findings.append({
            "id": "EN-001",
            "title": "No breadcrumb or active-section indicator found",
            "severity": "high",
            "evidence": "No breadcrumb element and no nav item with aria-current found in the page HTML.",
            "suggested_action": {
                "summary": "Add a breadcrumb trail or highlight the active section in navigation so visitors landing deep can orient immediately.",
                "priority": "high"
            }
        })
    return findings


def check_cta(soup):
    findings = []
    text = soup.get_text(" ", strip=True)
    ctas = CTA_WORDS.findall(text)
    buttons = soup.find_all(["button", "a"], string=CTA_WORDS)
    if len(buttons) == 0:
        findings.append({
            "id": "EN-002",
            "title": "No clear call-to-action button/link found",
            "severity": "medium",
            "evidence": "No <button> or <a> element with common CTA wording (buy, sign up, contact, etc.) found.",
            "suggested_action": {"summary": "Add one visually prominent CTA matching the page's primary purpose.", "priority": "medium"}
        })
    elif len(buttons) > 8:
        findings.append({
            "id": "EN-003",
            "title": "Many competing calls-to-action, no evident hierarchy",
            "severity": "low",
            "evidence": f"{len(buttons)} CTA-worded buttons/links found on one page.",
            "suggested_action": {"summary": "Establish one primary CTA and demote the rest visually (secondary/tertiary styling).", "priority": "low"}
        })
    return findings


def check_viewport(soup):
    findings = []
    vp = soup.find("meta", attrs={"name": "viewport"})
    if not vp or "width=device-width" not in vp.get("content", ""):
        findings.append({
            "id": "EN-004",
            "title": "Missing or misconfigured mobile viewport meta tag",
            "severity": "high",
            "evidence": "No <meta name=\"viewport\" content=\"width=device-width...\"> found.",
            "suggested_action": {"summary": "Add a standard responsive viewport meta tag.", "priority": "high"}
        })
    return findings


def check_trust(soup):
    findings = []
    text = soup.get_text(" ", strip=True)
    has_contact = bool(CONTACT_WORDS.search(text))
    has_trust = bool(TRUST_WORDS.search(text))
    if not has_contact and not has_trust:
        findings.append({
            "id": "EN-005",
            "title": "No visible contact path or trust/legitimacy signal",
            "severity": "medium",
            "evidence": "No contact/support wording and no review/testimonial/certification wording found on page.",
            "suggested_action": {"summary": "Add a visible contact/support link and at least one legitimacy signal (reviews, case studies, credentials) appropriate to the page.", "priority": "medium"}
        })
    return findings


def unverifiable_notes():
    return [
        {
            "id": "EN-NOTE-1",
            "title": "Context retention across client-side navigation not verified",
            "severity": "low",
            "evidence": "This check requires executing JavaScript / simulating navigation and was not run in static-HTML mode.",
            "suggested_action": {"summary": "Re-run with a browser-rendering tool to confirm selections/filters survive back-navigation.", "priority": "low"}
        },
        {
            "id": "EN-NOTE-2",
            "title": "Interstitials / autoplay / layout shift not verified",
            "severity": "low",
            "evidence": "These are runtime behaviors and were not confirmed in static-HTML mode.",
            "suggested_action": {"summary": "Re-run with a browser-rendering tool to observe first-paint behavior directly.", "priority": "low"}
        }
    ]


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: engagement_check.py <url>")
    url = sys.argv[1]
    r = fetch(url)
    soup = BeautifulSoup(r.text, "html.parser")

    findings = []
    findings += check_orientation(soup)
    findings += check_cta(soup)
    findings += check_viewport(soup)
    findings += check_trust(soup)
    findings += unverifiable_notes()

    print(json.dumps(findings, indent=2))


if __name__ == "__main__":
    main()
