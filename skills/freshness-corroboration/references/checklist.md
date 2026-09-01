# Freshness & Corroboration — Search Patterns and Pitfalls

## Corroboration search patterns
For a fact F about brand B, run searches like:
- `"B" F -site:B-domain.com` (force independent sources)
- `"B" reviews F` for consumer-facing claims (pricing, quality, service)
- `"B" news` for recent independent coverage that would mention/refresh key facts

Classify results by domain diversity, not just result count — five results all reposting the same wire article are effectively one source.

## Disambiguation search pattern
- Search the bare brand name with no other qualifier. Look at the result mix: are the top results all the target brand, or a blend of unrelated entities (a person, a place, a different company, a common-noun meaning)?
- If blended, check whether the brand's own site pairs its name with a consistent qualifier (industry + location, or a distinctive tagline) in its title tags and structured data `sameAs`/`alternateName` fields.

## False-positive guardrails
- A brand new company (<1 year old) will legitimately have thin independent corroboration — treat as `low`, not `medium`/`high`, and say so in evidence.
- Niche B2B brands may have few public reviews by nature — don't penalize absence of consumer review corroboration where it isn't a relevant channel; corroborate via industry press/directories instead.
- Don't flag disambiguation issues for names that are unique/coined (most startups) — only for real-word or common-name collisions.
