---
name: freshness-corroboration
description: Check whether a brand's key facts are dated/verifiable and whether they are corroborated by independent sources elsewhere on the web, and whether the brand name is disambiguated from other entities sharing it. Use when a brand's own site looks fine but an AI assistant states outdated facts, hedges heavily, cites a different (wrong) entity of the same name, or won't commit to a claim about the brand at all.
license: MIT
allowed-tools: ["bash", "web_fetch", "web_search"]
---

# Freshness & Cross-Web Corroboration Audit

## When to use
Use after the on-site checks (`crawl-render-audit`, `structured-data-audit`) confirm the page itself is fine. This skill covers Round-2 appendix section D: assistants weight facts by how dated they look and by how many independent sources agree, and they can conflate entities that share a name unless something disambiguates them.

## Inputs
- `url` / `brand_name` (required).
- `key_facts` (optional): specific facts to spot-check (price, leadership, certification, location) surfaced by the other skills; if absent, derive 3-5 from the homepage/about page.

## Procedure
1. **Date every key fact.** For each fact identified, look for an explicit date (JSON-LD `dateModified`, a visible "Last updated" string, a press-release date). No date anywhere → **medium** finding (can't be judged fresh, so a freshness-sensitive assistant will hedge or skip it); a date that is clearly stale relative to the fact's nature (e.g. a "current pricing" page last touched 2+ years ago, or leadership/team page listing a person no longer in that role per the brand's own newer press releases) → **high** finding.
2. **Corroborate 2-3 of the most important facts via independent web search** (search for the fact plus brand name, excluding the brand's own domain from the read). Classify each as:
   - Repeated consistently across ≥2 independent, unaffiliated sources → pass.
   - Found on the brand's own site only, with zero independent mentions → **medium** finding (fragile claim; an assistant is less likely to state it confidently or at all).
   - Contradicted by an independent source (e.g. a review site or news article states a different price/fact) → **high** finding — this is actively harmful, since an assistant may repeat the more corroborated (wrong, outdated, or competitor) version instead of the brand's current truth.
3. **Check entity disambiguation.** Search the brand name alone.
   - If multiple unrelated entities plausibly share the exact name (common word, common company name, or a well-known unrelated entity), and the brand's own pages/markup don't clearly disambiguate (no `sameAs` to an authoritative profile, no distinguishing qualifier like industry/location/domain paired with the name, no Wikidata/Wikipedia entry linked) → **high** finding — an assistant has a concrete, common failure mode of answering about the wrong entity.
   - If the name is distinctive/unique, this check passes trivially — say so rather than manufacturing a finding.
4. **Check "About"/trust-page basics** that assistants use as corroborating signals for legitimacy: physical address or registration info, third-party press mentions, verifiable social profiles linked consistently (same handle/URL) across the site. Absence isn't automatically a finding on its own — only flag if combined with a genuinely ambiguous or unverifiable brand identity from step 3.

## Output
Same finding shape, `id` prefix `FC-`. Return `[]` where a step passes. As a proactive (non-defect) suggestion, consider recommending the brand actively seed accurate, dated facts on a small number of high-authority independent surfaces (industry directories, its own well-linked press page, Wikidata) where that's realistic — flag as `low`/`medium` priority.

See `references/checklist.md` for how to phrase corroboration searches and avoid false positives, and `scripts/corroboration_check.py` for a reference implementation of the date-extraction half (step 1); steps 2-3 require live web search and are best driven by the calling agent's search tool using the query patterns in the checklist.
