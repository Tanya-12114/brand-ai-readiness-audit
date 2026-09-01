---
name: structured-data-audit
description: Check whether a page states its key facts explicitly and unambiguously in machine-readable form — valid schema.org/JSON-LD, sane meta tags, and facts given as plain readable text rather than only inside images, canvas, video, or PDFs. Use when a page is reachable and rendered but an AI assistant still gets facts about it wrong, omits it, or can't produce a clean citation-worthy snippet.
license: MIT
allowed-tools: ["bash", "web_fetch"]
---

# Structured Data & Explicit-Fact Audit

## When to use
Use once a page is confirmed reachable and readable (after `crawl-render-audit`). This skill covers the third gate in the Round-2 appendix: even a fully readable page can hide its *specific facts* from an extractor if they're implied, buried, or non-textual, and it covers what makes a page an easy, quotable source in the first place.

## Inputs
- `url` (required): a representative page for each key page type on the site (homepage, one product/service page, one article/blog page if applicable).
- `html` (optional): already-fetched HTML from `crawl-render-audit`, to avoid re-fetching.

## Procedure
1. **Extract all JSON-LD blocks** (`<script type="application/ld+json">`). Parse each as JSON.
   - No JSON-LD anywhere on a commercial/informational page → **high** finding. Structured data is the clearest, lowest-ambiguity channel for an assistant to pull a fact from; its absence forces the extractor to guess from prose.
   - JSON-LD present but malformed JSON, or missing required properties for its declared `@type` (e.g. a `Product` with no `offers`/`price`, an `Article` with no `datePublished`, an `Organization` with no `sameAs`/`url`) → **medium** finding per broken/incomplete block.
   - JSON-LD present but contradicts the visible page text (e.g. a different price or name) → **high** finding — this is worse than having none, since it risks a confidently wrong citation.
2. **Check core meta tags**: `<title>`, `meta[name=description]`, `og:title`, `og:description`, `og:image`, canonical link. Missing or generic/boilerplate (e.g. identical title across all pages) → **medium** finding — these are the fallback summary an assistant uses when structured data doesn't cover a field.
3. **Check for microdata/RDFa as a fallback** if JSON-LD is absent — if present, downgrade the "no structured data" finding by one severity level, but still recommend migrating to JSON-LD (more reliably parsed, decoupled from layout).
4. **Locate the page's 3-5 most commercially/informationally important facts** (price, availability, hours, address, phone, key spec, publish/update date, author, credentials/certifications — whatever is central to that page's purpose) and, for each, determine whether it is:
   - stated as plain text in the DOM (pass),
   - present only inside an `<img>`/`<canvas>`/embedded video/PDF with no adjacent text equivalent (fail — **critical** if it's the *only* place the fact appears anywhere on the domain, **high** otherwise),
   - implied rather than stated (e.g. price only visible after selecting options via JS interaction with no default/plain-text value) (fail — **high**).
5. **Check heading structure** (`h1`-`h3`) for a sane hierarchy with one clear `h1` stating what the page is about. A missing/duplicated `h1` or a heading-free wall of text is a **low**-to-**medium** finding — it doesn't block extraction outright but makes it harder for an assistant to segment the page into a quotable chunk.

## Output
Same finding shape as `crawl-render-audit` (`id` prefix `SD-`). Return `[]` where nothing is wrong. Beyond fixing defects, always consider whether adding `FAQPage`, `HowTo`, or `Review`/`AggregateRating` JSON-LD (where genuinely applicable to the content) would be a proactive, non-obvious suggestion even if no failure was found there — flag as a `low`/`medium` priority suggestion, not a "finding."

See `references/checklist.md` for required properties per common `@type`, and `scripts/structured_data_check.py` for a runnable reference implementation of steps 1-3 and 5.
