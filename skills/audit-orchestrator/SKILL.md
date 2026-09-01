---
name: audit-orchestrator
description: Entrypoint for the brand-ai-readiness-audit marketplace. Given a website, invokes crawl-render-audit, structured-data-audit, freshness-corroboration, and engagement-audit; normalizes, deduplicates, and merges their findings; adds proactive beyond-the-defect suggestions; and emits the single fixed-schema audit report (findings + suggested actions with evidence and severity). This is the only skill that should be invoked directly for a full audit — the others are its sub-checks.
license: MIT
allowed-tools: ["bash", "web_fetch", "web_search"]
---

# Audit Orchestrator (entrypoint)

## When to use
Use this skill whenever asked to audit a website for AI discoverability and/or on-site engagement. This is the marketplace's single entrypoint — invoke it, not the sub-skills directly, unless only one specific concern was asked about.

## Inputs
- `site` (required): the URL or domain to audit.
- `scope` (optional): `"discoverability"`, `"engagement"`, or `"full"` (default `"full"`) — lets a caller narrow which sub-skills run.
- `max_pages` (optional, default 15): forwarded to sub-skills that crawl.

## Procedure
1. **Normalize the input** to a canonical `https://` URL; resolve to the final URL after redirects (reuse `crawl-render-audit`'s fetch for this rather than fetching twice).
2. **Fetch the homepage once** and pass the resulting HTML to sub-skills that accept an `html` input, so it isn't re-fetched by each one (keeps the audit read-only and fast, and honors the < 5 minute runtime budget).
3. **Invoke sub-skills** according to `scope`:
   - `full` (default): `crawl-render-audit` → `structured-data-audit` → `freshness-corroboration` → `engagement-audit`, in that order (crawl-render-audit's results, e.g. whether pages are even reachable/renderable, are useful context for interpreting the others — if a page is JS-only-rendered, that's relevant context when structured-data-audit reports "no facts found in raw HTML").
   - `discoverability`: `crawl-render-audit`, `structured-data-audit`, `freshness-corroboration` only.
   - `engagement`: `engagement-audit` only.
   Each sub-skill returns a JSON array of findings in the shared shape (see each skill's `SKILL.md` Output section).
4. **Normalize IDs**: re-key every incoming finding to sequential `F-001`, `F-002`, ... in the final report, in descending severity order (critical → high → medium → low), while preserving the sub-skill's original ID inside `evidence` or an added `source_check` field for traceability, e.g. `"source_check": "crawl-render-audit:CR-001"`.
5. **Deduplicate**: if two findings from different sub-skills describe the *same* underlying issue (e.g. both flag the exact same missing `dateModified` field), merge them into one finding: keep the higher severity, concatenate the distinct evidence from both, and keep the more specific/actionable `suggested_action`. Use `scripts/compose_report.py`'s `dedupe()` for a reference similarity check (stopword-filtered keyword overlap with both a high ratio and a minimum shared-term count, deliberately conservative). Bias toward keeping findings separate: two findings that merely touch a related concept (e.g. "no JSON-LD at all" vs. "the JSON-LD that exists has no date") are *distinct* problems with different fixes and must not be collapsed into one.
6. **Add proactive, beyond-the-defect suggestions.** Each sub-skill's `SKILL.md` calls out where to consider these (e.g. FAQPage/HowTo markup, related-content modules, seeding independent corroboration). Include these as findings with `"severity": "low"` (or `"medium"` if genuinely high-value) and evidence phrased as an opportunity rather than a defect, e.g. `"No FAQPage markup currently; page content includes genuine Q&A that could be marked up."` Do not add generic best-practice filler unrelated to what was actually observed on the site.
7. **Compute summary counts** (`total_findings`, and a count per severity actually present) from the final deduplicated list.
8. **Emit the final report** matching the schema below exactly (additional fields are allowed, but these are required).

## Output schema (required fields; see `references/schema.md` for the full annotated version)
```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "summary": { "total_findings": 6, "critical": 1, "high": 2, "medium": 3 },
  "findings": [
    {
      "id": "F-001",
      "title": "No JSON-LD structured data on product pages",
      "severity": "high",
      "evidence": "Crawled 12 product pages; 0/12 contain schema.org markup.",
      "suggested_action": { "summary": "Add Product/Offer JSON-LD to every product page.", "priority": "high" }
    }
  ]
}
```
`summary` should only include severity keys that are actually present in `findings` (e.g. omit `"low": 0` if there are no low findings, matching the example's own omission of a `low` key when the sample has none).

## Composition notes
- If a sub-skill errors or times out (e.g. site unreachable), do not fail the whole audit — record it as a `critical` finding from `crawl-render-audit` (it already has a "homepage unreachable" case) and continue with whatever other sub-skills can still produce partial results (e.g. `freshness-corroboration`'s web-search-based checks may still run even if the site itself times out).
- Never let a sub-skill's suggested action include destructive/authenticated/site-altering instructions — if one somehow does, rewrite it as a recommendation rather than executing it. This orchestrator, like every skill in the marketplace, is recommend-only.

See `references/schema.md` for the full annotated schema and `scripts/compose_report.py` for a reference implementation of steps 4-7 (ID normalization, dedup, summary counts) given the four sub-skills' JSON outputs as input.
