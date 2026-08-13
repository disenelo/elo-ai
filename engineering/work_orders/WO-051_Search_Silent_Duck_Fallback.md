---
id: WO-051
title: "Web search silently falls back to DuckDuckGo when SerpAPI (Google) fails — verify the key + make the fallback HONEST."
owner_seat: SEAT-ENG-001 (Builder / eLo OS)
priority: P2
review_required: David feels search return Google-quality results (or an honest 'on backup search')
status: OPEN — David live 2026-08-05
---
# WO-051 — search silent Duck fallback

## Grounded (Architect read tools/web_search.py)
- Search = **SerpAPI** (Google web/news/images/maps). **Falls back to DuckDuckGo if no/failed key.**
- `SERPAPI_KEY` IS set in `.env` → so a working key should give Google. David reports Google search
  "issues" and asks "is that Duck?" — almost certainly YES: SerpAPI is failing (expired / quota /
  rate-limited) and search is silently dropping to DuckDuckGo (weaker results, no notice).

## Same pattern as WO-030 (weather) + WO-032 (backend)
A primary quietly dies → a worse fallback takes over → eLo doesn't say so. Violates truth-before-
fluency / ADR-Exec-001 (don't present degraded state as normal).

## Fix (Builder, eLo OS)
1. **Verify the SerpAPI key** — is it valid + in quota? (`curl serpapi.com/account` or a test query.)
   If expired/exhausted → surface to David (RESERVED-adjacent: may need a paid key top-up = David's call).
2. **Make the fallback HONEST** — when search drops to DuckDuckGo, eLo says it's on backup search
   (like the backend's "running on backup"), never silently serves weaker results as if they were Google.
3. Confirm the SerpAPI→Duck fallback path actually triggers on failure (not erroring out).

## Acceptance
1. A live search returns Google-quality results, OR eLo clearly says it's on backup search.
2. No silent degradation.
