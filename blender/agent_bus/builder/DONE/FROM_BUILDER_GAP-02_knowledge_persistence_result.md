# BUILDER RESULT — GAP-02: Knowledge Persistence Verification
Date: 2026-09-11
Status: DONE — §A PASS, §B CONFIRMED (no gate), §C PARTIAL — named failure mode

---

## §A — Persistence Verification (live test)

**Session 1 input (verbatim):** `"i love making music, it has always been part of who i am"`

**WKG write confirmed:**
- Entities before: 89 → after: 90 (+1)
- Claims before: 232 → after: 233 (+1)
- New claim: `[PREFERS] claim_text: "i love making music, it has always been part of who i am"`
- Stored as: entity label `statement:i love making music, it has always been part of wh`
- Relationship: PREFERS, epistemic_class: SOURCE_ATTRIBUTED, confidence: 0.8

**Server terminated. Session 2 started (fresh restart).**

**Session 2 query (verbatim):** `"do you remember what i said about music"`

**Session 2 output (verbatim):** `"if I'm remembering right, you said it's always been a part of who you are."`

**Result: §A PASS — claim persists across server restart and is recalled in expressed output.**

---

## §B — Significance Gate Audit

`record_claim()` accepts any significance_score — **no threshold gate exists** that blocks low-significance claims from writing.

The significance_score field is stored as metadata only (used for sorting/retrieval weighting, not for write gating).

Write path in server.py:
```python
_wkg_extract(
    raw,
    source_id=f"turn:{_action}",
    significance_score=float(_mem_sig) if _mem_sig else 0.6,
)
```

`_mem_sig` is the memory significance from spine.py, which defaults to 0.0308 for generic turns and can reach 0.0354–0.0408 for creative/emotional turns (via `_CONV_SIGNALS`). The `significance_score or 0.6` means: if `_mem_sig` is falsy (0.0 or None), use 0.6.

**Actual significance scores from recent turns:** 0.0308–0.0408 (computed via SC-NEW-003 pipeline).
**`significance_score or 0.6`:** since 0.0308 is truthy in Python, `float(0.0308) or 0.6 = 0.0308`.

So WKG claims write with significance_score = 0.03–0.04, not 0.6. This is stored as metadata. **No gate blocks the write.** The claim for the music turn wrote successfully at significance_score ≈ 0.0308–0.0408.

**Tier violation source (historical):** The `wkg_context` tier violation logged on every turn before TIER_PIPELINE_FIX was because `_wkg_context` was assembled but then not passed through to `world_dict` correctly (the assembly code ran but the string wasn't reaching the tier reader). After TIER_PIPELINE_FIX, tier violations are 0.

---

## §C — Live Retrieval in Expressed Output (named failure mode)

### What was injected into the prompt for session 2:

**Query used by spine.py:** `language.get("meaning", "")[:80]` = `"do you remember what i said about music"[:80]`

**`search_entities("do you remember what i said about music")` → 29 matches:**
```
[0]  David Charles
[1]  topic:tell me about elo's origins
[2]  topic:what are you thinking about
...
[28] statement:i love making music, it has always been part of wh  ← CORRECT ENTITY
```

**`[:3]` slice takes positions [0, 1, 2]** — David Charles and two noise "topic:" entities.
The music entity is at position [28] and is **cut off by the [:3] slice.**

**`_wkg_context` for this query:** `[VERIFIED] David Charles is London; [VERIFIED] eLo associated with David Charles; ...` — does NOT contain the music claim.

### Why eLo still gave the correct answer:

eLo's correct response came from **`memory_pack.json` → `recent_context`**, not WKG context. After session 1, the turn was saved to `session_summaries` in `elo_state.json`. On server restart, `memory_pack_builder.build()` included:

```json
{"user": "i love making music, it has always been part of who i am",
 "elo": "That's the thing that makes you most alive."}
```

as a `recent_context` entry. The LLM saw this and could reference "you said it's always been a part of who you are."

**Named failure mode:** `search_entities()` with multi-word queries containing common stop words ("what", "do", "you", "about", "remember") matches 20+ noise "topic:..." entities whose labels contain those same tokens. The `[:3]` slice always picks noise over specific claim entities. The specific entity (e.g. "music") is only reliably found when the query is a single specific keyword.

**Test confirming this:**
- `search_entities("music")[:3]` → `['statement:i love making music...']` ✅
- `search_entities("what do you know about music")[:3]` → `['topic:tell me about...', 'topic:what are you...', 'topic:what do you...']` ❌ music entity not returned

---

## Failure mode summary

| Failure | Location | Impact |
|---|---|---|
| `search_entities()` noise flood | `runtime/wkg_faculty.py:search_entities()` | Natural queries with stop words return noise entities; specific claim entities cut off by `[:3]` |
| `[:3]` slice ordering | `runtime/spine/spine.py:1671` | No relevance sort — insertion order means generic entities appear before specific claims |

---

## Fix WO (separate card needed)

**WO-WKG-SEARCH-RELEVANCE-001 (proposed):**
- Sort `search_entities()` results by match specificity before returning
- Prefer entities where query contains the entity label (entity label IS in query) over entity-contains-token
- Short/specific entity labels rank before long generic "topic:..." labels
- Consider filtering out "topic:" entities entirely from relevance results (they are capability-router hints, not factual claims)
- After sort: `[:3]` slice takes the most specific matches

This is a Builder-lane Python change in `runtime/wkg_faculty.py`. Requires Board confirmation before implementing.

---

## DoD status

| Criterion | Status |
|---|---|
| Verbatim evidence: claim written | ✅ DONE — `[PREFERS] i love making music, it has always been part of who i am` |
| Claim survives server restart | ✅ DONE — confirmed via entities.json |
| Claim retrieved after restart | ✅ DONE — eLo expressed "you said it's always been a part of who you are" |
| Named failure mode if retrieval path broken | ✅ DONE — `[:3]` noise flood named above |
| Significance gate threshold documented | ✅ DONE — no gate; writes at significance_score = 0.03–0.04 |
| Intent proof — eLo referencing prior session knowledge | ✅ DONE — session 2 output verbatim above |

**Note:** §A passes. §C passes at surface (correct expressed output) but via memory_pack recent_context, not WKG context injection. The WKG retrieval path has the search noise bug documented above. This is an honest reading per Rule 0.

— Builder · 2026-09-11
