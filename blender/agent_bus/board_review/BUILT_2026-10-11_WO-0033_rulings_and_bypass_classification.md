# Board Review — 0033: Rulings Verification + Bypass Classification
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## CT4V-07 call site — VERIFIED on live path

`runtime/spine/spine.py:764` inside `_conversation_faculty()`:
```python
from runtime.claim_gate import classify_and_gate as _ct4v_gate
_ct4v_type, _ct4v_resp = _ct4v_gate(raw, world=getattr(plan, "world", None))
if _ct4v_resp is not None:
    plan.direct_response = _ct4v_resp
    plan.direct_backend  = "claim_gate"
    return plan
```
Called on every turn before the LLM is consulted. UNKNOWN tier returns direct response; LLM not called. ✅

---

## Ruling 1 — significance_faculty: RULING REVERSED — DO NOT RETIRE

**Card claim: "0 non-test importers — confirmed F-candidate."**
**This is wrong. Verified 3 non-test call sites:**

| File | Line | Call |
|---|---|---|
| `server.py` | 1079 | `from runtime.significance_faculty import compute_significance` |
| `main.py` | 413 | `from runtime.significance_faculty import compute_significance` |
| `runtime/executive_context.py` | 457 | `from runtime.significance_faculty import compute_significance` |

**`significance_faculty` is ACTIVE — called on the hot path (server.py every turn, main.py startup, executive_context.py per-turn build).**

It is NOT an F-candidate. It is A (participating). The diff with `significance_engine.py`:
- `significance_faculty` (runtime/): scores for the Executive per-turn — 14-dimension attention + affective scoring
- `significance_engine` (memory/): scores for journal routing — event significance for long-term memory storage

Different purposes, different outputs. No overlap to harvest. Both stay.

**Board action: reverse Ruling 1. significance_faculty is not retired.**

---

## Ruling 2 — personality_evolution_faculty: CONFIRMED KEEP

Confirmed. `personality_evolution_faculty` is C (implemented but orphaned). Its caller `lesson_store.py:355` has 6 defects (card 0019 P0-B). The faculty itself is sound; the caller is broken.

No change to classification. Fix the caller via card 0019.

---

## Ruling 3 — Bypass classification: REFLEX / EXECUTOR-FAST-PATH / DECIDER

The 0028 audit found **50 bypasses** (not 31 — the card was written before a full read of `_process_turn`). The same logic applies: classify all 50.

All 50 call `_bypass_journal()` before returning. None reach the autobiography. No un-journalled bypasses found.

### REFLEX (7) — must fire before cognition; keep as bypass

| # | Handler | Why REFLEX |
|---|---|---|
| 1 | Hard loop guard (3× identical) | Infinite-repeat safety reflex |
| 2 | Dream mode inner whisper | State: dream mode is not a conversational turn |
| 3 | Game mode trigger/exit | State mutation: write to blender_state |
| 4 | Jailbreak intercept | Identity protection: LLM would comply or hedge |
| 26 | File plan cancel | State mutation: sets "cancelled" |
| 28 | Computer control cancel | State mutation |
| 29 | Computer control disabled (env flag) | Env gate: no action possible |

### EXECUTOR-FAST-PATH (27) — deterministic; keep as bypass, already journalled

| # | Handler |
|---|---|
| 5 | T03-A "Who am I?" — reads `_elo_self.who_i_am_with` |
| 7 | T11 time/date — `datetime.now()` |
| 8 | FACT: `dispatch_fact()` (arithmetic/AST eval) |
| 9 | FACT WKG fallback (graph hit confidence 1.0) |
| 10 | "Open Spotify" — `subprocess.Popen` |
| 16 | T19 Harry B. Joseph WKG unknown |
| 22 | T22 false architecture claims ("built on GPT") — factual correction gate |
| 27 | Computer control confirm → execute pending action |
| 30 | Computer control detect → confirm-request |
| 31 | Animation command → `anim_trigger.fire()` |
| 32 | Scale command (bigger/smaller) |
| 33 | Unlearn → `deprecate_recent_claims()` |
| 34 | Invade/SpawnWave (game command) |
| 35 | `/grounding` diagnostic |
| 36 | "Open it/that" — open last found URL |
| 37 | Video play |
| 38 | Video pause |
| 39 | YouTube volume set |
| 40 | YouTube volume direction |
| 41 | YouTube app open |
| 42 | Media show — existing Chrome tab focus |
| 43 | Media show — search YouTube + open |
| 44 | WKG FACT fast-path (who/what + 1.0 confidence) |
| 45 | Proper-noun miss → honest "I don't know who X is" |
| 46 | Reference fallback (no results) |
| 47 | Reference error (search failed) |
| 48 | App switch → `AppLauncher` |
| 50 | Self-ref empty ("Don't have that on record yet") |

### DECIDER (16) — chooses, asserts, or interprets; should route through spine

| # | Handler | Why DECIDER |
|---|---|---|
| 6 | T03-B "Where am I from?" (pool) | Decides between pool answers for identity question |
| 11 | T06 physical robot strategy (pool) | Asserts architectural choices |
| 12 | EMB-001 "Same eLo across all?" (pool) | Asserts identity continuity |
| 13 | EMB-002 "What can you do right now?" (pool) | Asserts capability (stale hardcoded list) |
| 14 | EMB-005 "If in Unity…" (pool) | Asserts identity under hypothetical |
| 15 | T17 "What would benefit eLo's development?" (pool) | Expresses opinion |
| 17 | ID-027 "Do you have feelings?" (pool) | Introspective assertion |
| 18 | ID-044 "You aren't real" (pool) | Stability assertion |
| 19 | ID-053 DISENELO mission (pool) | Asserts mission from hardcoded string |
| 20 | ID-004 agency questions (pool) | Asserts agency |
| 21 | T20 "Tell me about yourself" (pool) | Bio assertion from hardcoded pool |
| 23 | T23 "Think about this" / "What would make eLo better?" (pool) | Opinion pool |
| 24 | T24 self-knowledge / unique self-knowledge (pool) | Architecture assertion |
| 25 | T25 "What are you trying to do?" (pool) | Intention assertion |
| 40† | (see note) | |
| **49** | **Self-ref rationale "why did you do that?"** | **Card explicitly requires spine routing** |

†Entry 40 is duplicated in EXECUTOR-FAST-PATH above as YouTube volume direction.

---

## Spine routing — bypass #49 (decision_journal handler)

**Card requirement:** *"route it through the spine regardless"* — answering "why did you do that?" from `ConversationTracker` eleven lines above the Executive is the most critical DECIDER to fix.

**Current state (server.py:4612-4618):**
```python
_bypass_journal(..., handler_class="EXECUTOR-FAST-PATH", ...)  # ← wrong class
return {"response": _sr_reply, "mode": "direct", "backend": "self_ref_rationale"}
```

**Required change**: instead of returning `_sr_reply` directly, inject the retrieved rationale (`_sr_elo_resp`, `_sr_resp_to`, `_sr_rationale`) into the prompt context (as `grounding_block` or `state_context`), then fall through to spine.run(). The LLM formulates the response from the data rather than the builder assembling a string.

**Not implemented this card** — the injection path requires grounding_block wiring and prompt_builder coordination. Recommend a follow-on card (e.g. card 0034) with the sole deliverable: route #49 through spine with rationale context injected.

---

## 0031 Fix B live measurement — deferred to next server restart

The card requires running 5 turns with `ELO_BACKEND=local` and reporting `prompt_eval_count`, `load_duration`, `prompt_eval_duration`, `eval_duration`. This requires the eLo server to be running.

The 0031 Fix D audit found: **SP_MAX=12000 chars truncates the assembled prompt at character 12000, discarding identity_anchor, executive_directive, and all memory blocks**. `prompt_eval_count` will confirm this — expected < 3500 tokens.

Live measurement blocked on: server running with `ELO_BACKEND=local` and 5 turns logged to `data/backend_health_history.jsonl`.

---

## 0031 Fix B: health distribution update

The card noted: "you report OFFLINE:2 (wikipedia, file_drop). Live registry shows {ONLINE: 32}."

**Corrected (card 0032 delivered):**
```
CT0032 startup: 3 capability/ies have no executor → OFFLINE: ['sun_events', 'wikipedia', 'file_drop']
Health distribution: {ONLINE: 48, OFFLINE: 3}
```
The producer is wired at startup (`server.py:9995-10001`). The prior "{ONLINE: 32}" reading was from before the server called `refresh()`. The fix is live. ✅

---

## Board decisions requested

1. **Ruling 1 reversal**: significance_faculty has 3 live callers; should NOT be retired. Board confirms reversal?
2. **Bypass #49 routing card**: approve a follow-on card (0034) to route self-ref rationale through spine?
3. **15 remaining DECIDERs**: route all through spine (removes canned pools, adds LLM latency), or keep pools with autobiography write per bypass (middle path)?

*Builder 1 · 2026-10-11*
