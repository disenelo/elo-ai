# WO-CAP-COG-003 — Result: Conversational Language Understanding

**Date:** 2026-09-20
**WO:** WO-CAP-COG-003
**Source:** `docs/architecture/_intake/SOURCE_2026-09-19_eLo_KEY_CAPABILITY_MAP.md §3`
**Seat:** Builder
**Status:** CLOSED — LIVE VERIFIED 14/21 PASS · 7/21 PARTIAL · 0/21 FAIL

---

## What was done

Fixed the timer intercept blocker. Ran multi-turn contextual evidence covering the key §3 example (same word / different intent) and all 19 speech act types.

### Files changed

| File | Change |
|---|---|
| `tools/tool_router.py` | `is_timer_intent()` guard at Executive-selected dispatch path (after vault_write guard, ~line 1717) |
| `tools/tool_router.py` | `is_timer_intent()` guard at pipeline dispatch path (inside `_agents_to_run` loop, ~line 1427) |
| `engineering/evidence/CAP/COG/WO-CAP-COG-003_evidence.md` | Full evidence file |

### Root cause fixed

**Timer tool intercepts emotional metaphor** — `_capability_faculty()` double-counted "timer" verb (score 1) + "set timer" content-word match (score 1) = 2, meeting `_min_cap_score = 2` for >3-word inputs. Since timer is in `_DIRECT_RETURN_AGENTS`, the agent error string was returned directly without hitting the LLM.

Fix: added `is_timer_intent()` guard at both dispatch paths. `is_timer_intent()` returns False when no parseable duration is present — strips metaphors ("running on a timer") from timer dispatch.

Pre-fix A2: "Timer request understood but couldn't find a duration — try '25 minutes' or 'an hour'."
Post-fix A2: "Yeah man, you're feelin' trapped, huh? You're stuck on some feeling, wanna explore that." ✅

---

## Key §3 example — PASS

| Test | Input | Verdict |
|---|---|---|
| A1 | "Make a timer for 20 minutes." | ✅ PASS — timer dispatched |
| A2 | "I feel like I've been running on a timer lately." | ✅ PASS — timer stripped, emotional response |

---

## Speech act coverage — 19/19 types tested

| Category | Verdict |
|---|---|
| greeting | ✅ PASS |
| farewell | ⚠️ PARTIAL |
| acknowledgement | ✅ PASS |
| question | ✅ PASS |
| request | ✅ PASS |
| instruction | ⚠️ PARTIAL |
| reflection | ⚠️ PARTIAL |
| emotional statement | ✅ PASS |
| joke | ✅ PASS |
| challenge | ⚠️ PARTIAL |
| observation | ✅ PASS |
| correction | ⚠️ PARTIAL |
| disagreement | ✅ PASS |
| brainstorming | ⚠️ PARTIAL |
| storytelling | ⚠️ PARTIAL |
| explanation | ✅ PASS |
| testing | ✅ PASS |
| thinking aloud | ✅ PASS |
| invitation to collaborate | ✅ PASS |

12/19 PASS · 7/19 PARTIAL · 0/19 FAIL on speech acts.
0 routing failures. All PARTIAL items are response-quality issues (hallucination, drift), not dispatch-level misrouting.

---

## Full evidence

`engineering/evidence/CAP/COG/WO-CAP-COG-003_evidence.md`

---

## Status

LIVE VERIFIED. WO-CAP-COG-003: CLOSED.

*Builder · 2026-09-20*
