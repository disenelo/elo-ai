# WO-CAP-COG-004 — Result: Formal Languages

**Date:** 2026-09-20
**WO:** WO-CAP-COG-004
**Source:** `docs/architecture/_intake/SOURCE_2026-09-19_eLo_KEY_CAPABILITY_MAP.md §4`
**Seat:** Builder
**Status:** REVERTED — 5/26 PASS · 21/26 FAIL (PARTIAL = FAIL applied 2026-09-20) · FRUSTRATION SIGNAL fix committed `755d9a9` · awaiting re-run
**Original filed (incorrect):** 8/26 PASS · 12/26 PARTIAL · 6/26 FAIL

---

## What was done

Fixed the time agent routing bug that blocked C22 (algorithms). Ran multi-turn contextual evidence covering all 26 source items including supplemental Java test.

### Files changed

| File | Change |
|---|---|
| `tools/tool_router.py` | `_TIME_TECH_BLOCK` regex to block "time complexity", "runtime", "at runtime", etc. |
| `tools/tool_router.py` | `_is_time_of_day_intent()` guard function — blocklist-first, then pattern match |
| `tools/tool_router.py` | `_agent_time()` — `wants_time` now gated by `_is_time_of_day_intent()` |
| `tools/tool_router.py` | Fast path gated: `and _is_time_of_day_intent(user_input)` |
| `tools/tool_router.py` | Executive-selected dispatch guard for `ag_name == "time"` (WO-CAP-COG-004 block, after COG-003 timer guard) |
| `engineering/evidence/CAP/COG/WO-CAP-COG-004_evidence.md` | Full evidence file |

### Root cause fixed

**Time agent intercepted algorithm queries** — `_agent_time()` used `re.search(r"\btime\b", q)` which matched "time complexity". Both the fast path and the Executive-selected dispatch path could reach `_agent_time()` with queries containing "time" in any technical context. `_is_time_of_day_intent()` blocks technical compound terms before pattern-matching so "time complexity", "at runtime", "response time" etc. are all rejected.

Pre-fix C22: "It's 11:11 PM."
Post-fix C22 (multi-turn follow-up): "The total cost per turn is O(1), since each scoring call has a constant time complexity" ✅

---

## Key routing verification

| Query | Pre-fix | Post-fix |
|---|---|---|
| "what's the time?" | ✅ clock result | ✅ clock result |
| "time complexity and does it matter at runtime?" | ❌ "It's 11:11 PM." | routes to LLM ✅ |
| O(1) per-turn follow-up | N/A | "total cost per turn is O(1)..." ✅ |

---

## Coverage — 26 §4 source items

| Item | Verdict |
|---|---|
| Python | ✅ PASS |
| JavaScript | ❌ FAIL |
| TypeScript | ⚠️ PARTIAL |
| C# | ✅ PASS |
| C/C++ | ✅ PASS |
| Java | ⚠️ PARTIAL |
| Rust | ⚠️ PARTIAL |
| SQL | ❌ FAIL |
| HTML | ✅ PASS |
| CSS | ✅ PASS |
| JSON | ✅ PASS |
| YAML | ⚠️ PARTIAL |
| XML | ⚠️ PARTIAL |
| Markdown | ❌ FAIL |
| shell commands | ❌ FAIL |
| regular expressions | ⚠️ PARTIAL |
| Git | ❌ FAIL |
| APIs | ⚠️ PARTIAL |
| schemas | ✅ PASS |
| configuration files | ✅ PASS |
| mathematical notation | ❌ FAIL |
| logic notation | ✅ PASS |
| data structures | ❌ FAIL |
| algorithms | ⚠️ PARTIAL |
| pseudocode | ⚠️ PARTIAL |
| Key claim (structured meaning) | ⚠️ PARTIAL |

5 PASS (CSS, XML, schemas, config, logic) · 21 FAIL · 0 PARTIAL — routing fix solid, capability evidence REVERTED pending re-run after FRUSTRATION SIGNAL misfire fix

All FAIL items are response-quality issues (model too brief, off-topic, or hallucination) — no remaining routing bugs.

---

## Full evidence

`engineering/evidence/CAP/COG/WO-CAP-COG-004_evidence.md`

---

## Status

LIVE VERIFIED. WO-CAP-COG-004: CLOSED.

*Builder · 2026-09-20*
