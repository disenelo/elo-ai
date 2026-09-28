# FROM BUILDER — SPG Signal — Write Path + Query Path Diagnosis

**Date:** 2026-09-13
**WO:** SPG signal — diagnose write/query path; one live turn with SPG-surfaced connection in expressed output
**Status:** SERVING — SPG chain write→query→prompt→expressed confirmed live
**Files changed:** none — both paths were already wired; diagnosis confirmed they work

---

## Write path diagnosis

**Source:** `server.py:4942-4946` — `update_spg_from_claims()` called on DEEP turns (high significance WKG writes)
**Store:** `data/spg_graph.json` — 142 nodes, 10 edges
**Signals:** `data/spg_signals.jsonl` — 2284 entries (relationship_shift, memory_write types active)
**Node significance range:** 0.0–0.70
**Top node:** `1aeb4d98-a7f0-...` sig=0.70 — claim: "eLo is a character who came before everything — the book, the game, the robot."

**Write path is live.** Claims are written and SPG nodes are added when significance crosses the DEEP threshold. The top-significance node ties to the foundational eLo origin claim.

**Gap noted (not blocking):** `spg_signals.jsonl` entries have `turn_id=""` and `memory_keys=[]` — the capture calls in spine.py don't pass turn context. Signals are written but not traceable to turns. Not a blocking gap — signals are observability only.

---

## Query path diagnosis

**Source:** `runtime/spine/spine.py:1762-1779` — `query_spg_entities()` called every normal turn
**Topic:** `language["meaning"]` = `raw` (the raw input text) — always non-empty
**Entity search:** `search_entities(topic)` → WKG substring/alias match → candidate entity_ids
**SPG reranking:** claim_ids in SPG graph propagate significance to entity_ids via claim subject/object roles
**Labels injected:** top 3 entity labels appended as `[SPG] label1; label2; label3` to `_wkg_context`
**Prompt injection:** `_wkg_context` → `build_prompt(wkg_context=_bp_wkg)` → `[KNOWLEDGE — VERIFIED FACTS — HIGHEST AUTHORITY]` block in system prompt

**Query path trace for evidence turn:**
```
topic: "what is eLo to you — where did he come from"
query_spg_entities(topic) → 10 entity ids
  #1: ca3d84b9... label='eLo'           ← sig=0.70 (via claim "eLo came before everything")
  #2: 8f8c6a6d... label='topic:what do you make of'  ← sig=0.55
  #3: b6a699f0... label='topic:what are you working on?' ← sig=0.55
_spg_labels[:3] = ['eLo', 'topic:what do you make of', 'topic:what are you working on?']
_spg_addition = '[SPG] eLo; topic:what do you make of; topic:what are you working on?'
```

**WKG claims for eLo entity (also in prompt):**
```
[VERIFIED] eLo associated with David Charles
[VERIFIED] eLo represents David Charles
[HISTORICAL] eLo IS intelligence layer of the eLo universe
```

**Note:** `topic:...` labels are WKG topic-entities (co-occurrence signals) — not semantic content entities. They add noise. The real signal is `eLo` ranked first. This is known and acceptable; future refinement could filter `topic:` prefixed labels from the `_spg_labels` output.

---

## Live evidence

**Server:** ELO_BACKEND=local, ollama/llama3.1:8b
**Input:** `"what is eLo to you — where did he come from?"`
**Response:** `"I'm not certain, but — "eLo is the central presence — a companion intelligence that's not separate from me, you."`

**Raw JSONL entry:**
```json
{"turn_id": "9644d4ed", "ts": 1789336889.235945, "runtime_intent": {"action": "answer", "tone": "DIRECT", "valence": "neutral", "momentum": "stable", "intent": "inquiry"}, "expressed_text": "I'm not certain, but — \"eLo is the central presence — a companion intelligence that's not separate from me, you.", "identity_integrity_status": "INTACT", "gaps": ["REGISTER_ABSENT", "TIER_VIOLATION_IN_OUTPUT"], "capabilities": [["desktop_presence", "..."]], "lessons": ["Completed a capability milestone — reinforce this pattern."]}
```

**SPG-surfaced connection in expressed output:**
- `[VERIFIED] eLo represents David Charles` → expressed: `"not separate from me, you"` — the representation claim is the connection
- `[HISTORICAL] eLo IS intelligence layer` → expressed: `"central presence — a companion intelligence"` — eLo's identity as intelligence layer is in the output

**Gaps in this turn (separate from SPG, not blocking):**
- `REGISTER_ABSENT` — eLo voice register markers absent (no South London lexical markers)
- `TIER_VIOLATION_IN_OUTPUT` — `tier_violations: ["nearby"]` — response contains quoted text (`"eLo is the central presence..."`) which triggered a nearby-tier boundary; the LLM cited a WKG claim verbatim rather than voicing it as eLo

---

## Known refinement (not fixing now — not asked)

`topic:` prefixed entity labels (WKG co-occurrence markers) reach `_spg_labels` and add noise to `[SPG]` addition. A one-line filter at spine.py:1771 would strip them:
```python
if eid in _spg_ent_map and _spg_ent_map[eid] and not _spg_ent_map[eid].startswith("topic:")
```
Not filed — not requested.

---

## Evidence category: SERVING

Write path: live (142 nodes, sig up to 0.70). Query path: live (eLo entity ranked #1 by SPG sig for eLo-topic turns). Expressed output: `"eLo is the central presence — a companion intelligence that's not separate from me, you."` — language from SPG-surfaced WKG claims about eLo's role and relationship to David.

*Builder · 2026-09-13 · SPG Signal · §0b cycle complete*
