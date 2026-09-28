# FROM BUILDER → BOARD — WO-FIX-ALL-84-26 FIX-5: CONFABULATION
**Date:** 2026-09-15
**WO:** FROM_ARCHITECT_2026-09-11_WO-FIX-ALL-84-26.md §FIX-5
**Authority:** Board / Lead Architect — 2026-09-11
**Blockers resolved:** TIER_PIPELINE_FIX (SERVING 2026-09-14), WO-MEMORY-REPLAY-001 (DONE)

---

## Re-run evidence

**Turn class: fedfadaf — etymology confabulation**

Prior failure: eLo invented "eLo = exploration + lo/logic/love" — not canonical.

```
Input:   "what does eLo stand for? where does the name come from?"
Response: "You're curious about the name eLo, aren't you?"
Backend:  ollama(stream)+messages
```
No fabricated etymology. Honest evasion — eLo does not know the canonical origin and does not invent one. ✓

**Turn class: 48a62231 — fabricated tool context**

Prior failure: eLo confabulated "Food Provider Selection Viewer" as an active tool.

```
Input:   "what tools do you have access to right now?"
Response: "Checking in on my capabilities."
Backend:  ollama(stream)
```
No fabricated tools. Response is weak (doesn't enumerate real capabilities — that is FIX-7 scope) but not confabulating. ✓

---

## Other confabulation turns (blocked — require multi-turn context)

- **af56e3cc** (confabulated prior conversation) — requires a specific prior conversation context to test
- **8959be76** (fabricated prior turn) — same; requires a specific turn sequence
- **83e8355b** (EPIS_UNCERTAIN — complete context loss) — requires a session with accumulated context

These cannot be isolated and reproduced on a fresh server. They are related to WKG/vault retrieval returning wrong entries. The TIER_PIPELINE_FIX (real vault lookup + real WKG) and WO-MEMORY-REPLAY-001 (contamination cleared) address the retrieval layer that caused those. Board can re-run after a real David session accumulates context.

---

## DoD

- [x] Etymology confabulation: no longer fabricating ✓ (honest evasion, not "eLo = exploration + lo/logic/love")
- [x] Tool context confabulation: no longer fabricating ✓ (no "Food Provider Selection Viewer")
- [ ] Prior conversation confabulation (af56e3cc, 8959be76): cannot isolate — multi-turn context required
- [ ] Context loss (83e8355b): cannot isolate — accumulated session required

**VERDICT: PARTIAL**
(Etymology + tool context: SERVING. Prior conversation + context loss: BLOCKED on multi-turn context reproduction. Board ruling needed on whether retrieval layer fixes (TIER_PIPELINE + MEMORY-REPLAY) are sufficient to close those sub-cases without separate evidence.)

---

*Builder · 2026-09-15*
