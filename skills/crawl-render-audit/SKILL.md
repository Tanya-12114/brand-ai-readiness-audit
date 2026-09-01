---
name: crawl-render-audit
description: Check whether crawlers and AI-assistant fetchers can actually reach and read a website's pages — robots/sitemap access, HTTP health, redirect hygiene, and whether the meaningful content exists in the raw HTML or only appears after client-side JavaScript runs. Use when diagnosing why a brand's pages are missing from AI-assistant answers or search results even though a human sees the content fine in a browser.
license: MIT
allowed-tools: ["bash", "web_fetch"]
---

# Crawl & Render Audit

## When to use
Use this skill as step 1 of a discoverability audit, or standalone when a brand reports "we're invisible to AI assistants / search" despite the site looking normal in a browser. This skill answers the first of the three gates in the Round-2 appendix (crawler let in → content readable → fact extractable): it covers the first two gates.

## Inputs
- `url` (required): the site's homepage or a representative page.
- `max_pages` (optional, default 15): cap on how many URLs this skill will fetch, to stay read-only and non-abusive.

## Procedure
Follow these steps in order; each step's evidence feeds directly into a finding if it fails.

1. **Fetch `robots.txt`** at the root. Parse it (`urllib.robotparser` or equivalent).
   - If disallowed rules block major crawlers (`*`, `GPTBot`, `Google-Extended`, `ChatGPT-User`, `CCBot`, `anthropic-ai`, `PerplexityBot`) from the whole site or from key sections (product/docs/blog paths), that is a **critical** finding — the brand is opting itself out of AI-assistant fetching by construction, no matter how good the content is.
   - If `robots.txt` 404s or is empty, that's not itself a problem (no explicit block), but note it — it means nothing here explains an absence, so look downstream.
2. **Fetch `sitemap.xml`** (from `robots.txt`'s `Sitemap:` line, or `/sitemap.xml` directly). Missing/broken sitemap on a multi-page site is a **medium** finding — it doesn't block crawling but slows discovery of new/updated pages.
3. **Fetch the target URL and up to `max_pages` internally-linked pages** with a plain `GET` (no auth, no forms), respecting robots rules found in step 1 and a short delay between requests. For each:
   - Record the HTTP status. Any 4xx/5xx on a page that's linked from navigation is a **high** finding (a linked-but-broken page wastes crawl budget and signals low maintenance).
   - Record redirect chains. A chain of 3+ hops, or redirects that change scheme/host inconsistently (e.g. only some pages canonicalize to `https://www.`), is a **medium** finding — extra hops make a page more likely to be skipped or de-prioritized by a fetcher with a hop budget.
4. **Compare raw HTML vs. rendered content** for the target page and 1-2 representative deep pages (e.g. a product/article page):
   - Fetch raw HTML via a plain HTTP GET.
   - Separately obtain the DOM after JavaScript execution (headless-render tool if the calling agent has one available; otherwise approximate by checking for empty root containers like `<div id="root"></div>` / `<div id="app"></div>` with a large paired JS bundle and near-empty `<body>` text).
   - Compute the ratio of visible text length in raw HTML vs. rendered DOM. If the raw-HTML text is under ~30% of rendered text (i.e. most content only exists after JS runs), that's a **critical** finding for any fetcher that doesn't execute JavaScript, and **high** even for ones that do (rendering is slower/costlier so JS-only content is fetched/used less reliably).
   - Check for a server-rendered `<noscript>` fallback with real content — if present, downgrade the above finding by one severity level, since a non-JS fetcher still gets something.
5. **Check canonical/meta robots tags** on each fetched page: a stray `<meta name="robots" content="noindex">` or a canonical URL pointing to a different page than the one serving unique content is a **high** finding (self-inflicted invisibility that's easy to miss because the page renders fine).
6. **Check response headers** for anything that would block a simple fetcher: required cookies before content loads, aggressive bot-challenge pages (CAPTCHA/JS-challenge) served to non-browser user agents, or content gated behind an interstitial. Any of these on public marketing/informational pages is a **high** finding.

## Output
Emit a JSON array of findings, each shaped as:
```json
{
  "id": "CR-001",
  "title": "short description",
  "severity": "critical|high|medium|low",
  "evidence": "what was observed, with concrete numbers/URLs",
  "suggested_action": { "summary": "what to change and how", "priority": "critical|high|medium|low" }
}
```
Return `[]` if a step finds nothing wrong — do not manufacture findings to pad the report. Pass this array to `audit-orchestrator` for merging into the final report.

See `references/checklist.md` for the full pass/fail table and `scripts/crawl_check.py` for a runnable reference implementation of steps 1-3 and 5-6 (step 4's headless render depends on tools available to the calling agent).
