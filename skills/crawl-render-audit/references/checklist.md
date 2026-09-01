# Crawl & Render — Detailed Checklist

| Check | Pass condition | Fail severity | Notes |
|---|---|---|---|
| robots.txt allows key AI/search agents | No `Disallow: /` for `*`, `GPTBot`, `Google-Extended`, `ChatGPT-User`, `CCBot`, `anthropic-ai`, `PerplexityBot` on core content paths | critical | Distinguish "blocks everything" from "blocks one low-value path (e.g. `/admin`)" — only the former/latter-on-core-content counts |
| sitemap.xml present & valid XML | 200 status, well-formed, contains real URLs | medium | Only applies to sites with >~10 pages |
| No linked page returns 4xx/5xx | All same-site links from nav/footer/sitemap resolve | high | Check a sample, not exhaustively, to stay non-abusive |
| Redirect chains ≤ 2 hops, consistent canonical host/scheme | Fetch chain length and final URL | medium | Inconsistent www/non-www or http/https across pages is the common real-world case |
| Raw-HTML text ≈ rendered text | Ratio ≥ ~70% | critical (< 30%) / high (30-70%) | `<noscript>` fallback with real content downgrades one level |
| No stray noindex / bad canonical | meta robots + canonical link match intent | high | Especially check pages that clearly should be indexable (product, blog, docs) |
| No bot-challenge/interstitial on public pages | Plain GET with a generic UA returns real content, not a challenge page | high | Distinguish legitimate abuse protection on checkout/auth flows (fine) from blocking marketing pages (not fine) |

## Common false positives to avoid
- A `Disallow` rule scoped to `/cart`, `/checkout`, `/account` etc. is normal and not a finding.
- A single slow page (one 5xx) during a transient deploy isn't a systemic finding — only report if reproducible.
- Sites intentionally built as pure SPA dashboards behind login (not public marketing/content) don't need SSR — only flag JS-only rendering on pages meant to be publicly discoverable.
