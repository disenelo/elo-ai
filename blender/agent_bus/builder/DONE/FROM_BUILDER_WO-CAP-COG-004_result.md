# WO-CAP-COG-004 — Result: Formal Languages

**Date:** 2026-09-20
**WO:** WO-CAP-COG-004
**Source:** `docs/architecture/_intake/SOURCE_2026-09-19_eLo_KEY_CAPABILITY_MAP.md §4`
**Seat:** Builder
**Status:** IN PROGRESS — Best confirmed score: RE-RUN 5 17/26 PASS (unconfirmed — RE-RUN 7 with same code scored 10/26). RE-RUN 6 10/26 (regression — reverted). RE-RUN 7 10/26 (baseline not reproduced — high variance). Active failure: shell truncation + context contamination.
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

RE-RUN 5 (best score): 17/26 PASS. FAIL items: C3 TypeScript, C4 question-back, C10 contamination, C18 poetic, C19 wrong math, C22 contamination, C25 deflect, C26 deflect, C6 Rust (partial).

RE-RUN 6: 10/26 PASS — REGRESSION. `_technical_anchor` replaced `_anchor` in technical path; caused model to write "does the following: 1. ..." list format which truncated at preamble. C13, C15, C17, C22 all complete in RE-RUN 5, all truncated in RE-RUN 6. Context contamination (C20) also worsened. Change reverted.

---

## Full evidence

`engineering/evidence/CAP/COG/WO-CAP-COG-004_evidence.md`

---

## Run history

| Run | Score | Notes |
|---|---|---|
| Original | 5/26 PASS | PARTIAL = FAIL applied; routing bugs present |
| RE-RUN 2 | 13/26 PASS | FRUSTRATION fix + anchor + SQL/SHELL signals |
| RE-RUN 5 | 17/26 PASS | _LOGIC_SIGNAL_RE added; claimed best score |
| RE-RUN 6 | 10/26 PASS | REGRESSION — _technical_anchor truncation; reverted |
| RE-RUN 7 | 10/26 PASS | Reverted code (RE-RUN 5 baseline); 17/26 NOT reproduced — high variance confirmed |
| RE-RUN 8 | 10/26 PASS | Anti-list-preamble instruction + per-turn focus anchor applied; baseline unchanged |
| RE-RUN 9 | 10/26 PASS | C3/C14/C16 routing fixes applied; C19-Math PASS (new); baseline unchanged |

## RE-RUN 9 routing fix verdicts

| Fix | Intended effect | Actual result |
|---|---|---|
| C3 CC_TECH_BLOCK_RE | Prevent TypeScript from routing to computer_control | ✅ Block confirmed, ❌ server timeout = still FAIL in run |
| C14 _vld_skip_tech | Prevent GT-R5 retry on regex/state-name inputs | ✅ No gt-r5-retry in backend tag, ❌ contamination from C13 = same wrong answer |
| C16 HTTP patterns in _CODE_SIGNAL_RE | Route HTTP request blocks to ollama technical path | ❌ OVERRIDE fires but model still single-clause ("This is an HTTP request to a chat server.") |

## RE-RUN 9 PASS items

C1-Python · C5-C/C++ · C7-SQL · C10-YAML · C15-Git · C17-Schemas · C18-Config · C19-Math · C21-DataStructures · C26-KeyClaim

## RE-RUN 9 failure breakdown

| Category | Items |
|---|---|
| Contamination cascade (2-turn offset) | C4←C2, C8←C6, C9←C7, C14←C13 |
| Timeouts (no response) | C2, C22, C23, C24 |
| eLo identity drift | C12, C25 |
| Single clause (PARTIAL = FAIL) | C6, C13, C16 |
| Complete non-answer | C20 (AND/NOT boolean logic) |
| Metaphorical only | C11 (XML attributes unexplained) |
| Routing fix — timed out | C3 |
| Routing fix — contamination wins | C14 |

## Status

IN PROGRESS. Score stuck at 10/26 for RE-RUN 6, 7, 8, AND 9 (four consecutive runs). All applied routing fixes (C3, C14, C16) either confirmed bypassed by other failure modes (contamination, timeout) or insufficient alone (C16 single-clause response). Structural failures that no code change has addressed:

1. **Contamination cascade** — when prior turns produce no response (C2, C3 timeout), the grounding context retains the previous subject. Next turn answers that prior subject. Per-turn focus anchor is insufficient when there are dropped turns.
2. **Persistent timeouts** — C22, C23, C24 time out consistently on every run. C2 timed out in RE-RUN 9. Model capacity or server quota state during multi-turn run.
3. **Identity drift** — C12 (Markdown), C25 (StructuredMeaning) both contain eLo-related vocabulary; model self-references instead of explaining the input.
4. **Logic/boolean non-answer** — C20 `grounded AND NOT swimming AND velocity < 0.1` produces "I don't understand." No OVERRIDE trigger pattern matches boolean logic notation.

Outstanding: 5-turn identity audit on mistral-nemo:12b (per Architect direction). P0-A through P0-E from FROM_ARCHITECT_2026-09-20_CAP-REBUILD-REDIRECT.md not started.

*Builder · 2026-09-22*
