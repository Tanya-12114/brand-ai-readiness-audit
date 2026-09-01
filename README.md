# brand-ai-readiness-audit

An Agent Skill Marketplace that audits a website for the two Round‑2 failure modes:

1. **Off-site discoverability** — why an AI assistant would fail to find, fetch, extract, trust, or cite the brand.
2. **On-site engagement** — why a visitor who does arrive doesn't stay or convert.

It is **read-only / recommend-only**: no skill fetches authenticated areas, submits forms, ignores `robots.txt`, or writes anything back to the target site. Every skill only reads and reports.

## Why four skills instead of one

Each skill owns one *mechanism* from the Round‑2 appendix, so a failure can be diagnosed and fixed independently, and each skill can be tested/improved in isolation:

| Skill | Appendix mechanism it covers | What it catches |
|---|---|---|
| `crawl-render-audit` | A (crawler access), C (machine-readability of the page) | robots/sitemap blocks, redirect/status problems, JS-only content, text buried in non-text assets |
| `structured-data-audit` | B (what makes a page an easy source to quote), C (explicit vs. implied facts) | missing/invalid JSON-LD, facts stated only in images/canvas/PDF, weak metadata |
| `freshness-corroboration` | D (cross-web agreement, entity disambiguation) | stale/undated facts, single-source claims, no disambiguating markup for an ambiguous brand name |
| `engagement-audit` | F-adjacent + general UX mechanics (on-site half of the brief) | weak orientation, no clear next step, context loss across pages, bounce-inducing patterns |

`audit-orchestrator` is the **entrypoint**. It is the only skill invoked directly by the calling agent. It:

1. Takes the target URL/domain as input.
2. Fans out to the four audit skills above (each independently read-only), passing along the URL and any already-fetched page content so pages aren't re-crawled unnecessarily.
3. Normalizes each skill's findings into the shared finding shape (`id`, `title`, `severity`, `evidence`, `suggested_action`).
4. Deduplicates overlapping findings (e.g. a missing-date issue raised by both `structured-data-audit` and `freshness-corroboration`), keeping the higher severity and merging evidence.
5. Adds its own **beyond-the-defect** proactive suggestions (opportunities that aren't failures but would still raise citation odds or engagement).
6. Computes the `summary` counts and emits the final audit report against the fixed schema (see `skills/audit-orchestrator/references/schema.md`).

A single well-built skill would have satisfied the floor requirement; this marketplace decomposes further because the four concerns above have genuinely different evidence sources (server/robots response vs. HTML markup vs. cross-site search vs. UX/DOM structure) and genuinely different fix owners on a real team (infra/SEO vs. dev vs. content/PR vs. design) — so keeping them as separable skills mirrors how a site would actually assign the resulting tickets.

## Layout

```
brand-ai-readiness-audit/
  marketplace.json
  README.md
  skills/
    audit-orchestrator/        <- entrypoint: composes the others, emits final report
      SKILL.md
      scripts/compose_report.py
      references/schema.md
    crawl-render-audit/
      SKILL.md
      scripts/crawl_check.py
      references/checklist.md
    structured-data-audit/
      SKILL.md
      scripts/structured_data_check.py
      references/checklist.md
    freshness-corroboration/
      SKILL.md
      scripts/corroboration_check.py
      references/checklist.md
    engagement-audit/
      SKILL.md
      scripts/engagement_check.py
      references/checklist.md
```

## Running it

Point a general agent with `audit-orchestrator` loaded (and the other four skills available in its skill set) at a URL. The orchestrator's `SKILL.md` procedure tells it exactly which sub-skill to invoke for which check, in what order, and how to merge results. Each sub-skill's script can be run standalone too (`python scripts/crawl_check.py <url>`, etc.) — they print JSON findings arrays to stdout that already match the shared finding shape, so the orchestrator (or a human) can merge them directly.

## Guardrails honored

- Every network call is a plain `GET`; no login, no POST/PUT/DELETE, no form submission.
- `robots.txt` is fetched and honored before any other page is crawled (`crawl-render-audit` step 1).
- No rate-abusive crawling: scripts cap page fetches (configurable, default ≤ 20 URLs) and add a short delay between requests.
- Nothing in the marketplace ever edits the target site — output is a JSON report plus prioritized recommendations only.
- Each skill declares `allowed-tools` in its frontmatter and needs no external service to resolve (only outbound HTTP).
