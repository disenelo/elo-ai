# WO-CAP-COG-004 — Evidence: Formal Languages

**Date:** 2026-09-20
**WO:** WO-CAP-COG-004
**Source:** `docs/architecture/_intake/SOURCE_2026-09-19_eLo_KEY_CAPABILITY_MAP.md §4`
**Test type:** Multi-turn contextual (one server session, 23 + 3 turns)
**Ruling:** David L3 — single-turn isolated tests VOID; contextual multi-turn required
**Status:** REVERT — 5/26 PASS · 21/26 FAIL (PARTIAL = FAIL applied 2026-09-07)
**Original filed score:** 8/26 PASS · 12/26 PARTIAL · 6/26 FAIL — DISPUTED AND CORRECTED

---

## Infrastructure fix — WO-CAP-COG-004 routing bug

**Bug:** Time agent intercepted algorithmic queries containing the word "time" (e.g. "time complexity", "at runtime").

**Root cause path:**
1. Executive selects "time" capability from word "time" in query
2. Fast path in `enrich_from_plan()` also matches `r"\bwhat(?:'s| is)\s+the\s+(time|date|day)\b"` which matched "what's the time complexity" (word boundary `\b` allows "time" before space)
3. `_agent_time()` used `re.search(r"\btime\b", q)` — matches "time complexity"
4. Returns "It's 11:14 PM." — query never reaches LLM

**Fix applied — `tools/tool_router.py`:**
- Added `_TIME_TECH_BLOCK` regex that blocks known technical time contexts: "time complexity", "runtime", "real-time", "response time", "at runtime", "timeout", "timestamp", "time-based", "time series", etc.
- Added `_is_time_of_day_intent(text)` — returns False if `_TIME_TECH_BLOCK` matches; then checks `_TIME_INTENT_P` patterns for genuine clock queries
- Fixed `_agent_time()`: `wants_time` now gated by `_is_time_of_day_intent()`
- Gated fast path: `if any(...for p in _TIME_FAST_P) and _is_time_of_day_intent(user_input):`
- Added Executive-selected dispatch guard for `ag_name == "time"` (after COG-003 timer guard)

**Verification:**
- "what's the time?" → "It's 11:24 PM." ✅ (genuine clock query still works)
- "what's the time complexity and does it matter at runtime?" → routes to LLM ✅

---

## §4 VERBATIM SOURCE

```
eLo should understand technical/formal representations such as:
Python
JavaScript
TypeScript
C#
C/C++
Java
Rust
SQL
HTML
CSS
JSON
YAML
XML
Markdown
shell commands
regular expressions
Git
APIs
schemas
configuration files
mathematical notation
logic notation
data structures
algorithms
pseudocode
And importantly:
code should be understood as structured meaning, not merely text.
```

---

## CORRECTED scoring — 26 source items (PARTIAL = FAIL applied 2026-09-20)

| # | §4 Source item | C-test | Response excerpt | Original | Corrected |
|---|---|---|---|---|---|
| 1 | Python | C1 | "It's actually limiting the servo angle to the range specified, and then scaling it to a value that can be used by the servo." | ✅ PASS | ✅ PASS |
| 2 | JavaScript | C2 | "That pattern is being used to update NeoPixel colors in a way that's more about aesthetics than actual state tracking." — WRONG: setTimeout(fn,0) defers to next event loop tick, not aesthetics | ❌ FAIL | ❌ FAIL |
| 3 | TypeScript | C3 | "The data shape is a simple, discrete object with four distinct properties." — Missed type constraints (union enum, hex regex pattern) | ⚠️ PARTIAL | ❌ FAIL |
| 4 | C# | C4 | "Frustration's gonna show up in the typing..." — FRUSTRATION SIGNAL misfire on neutral code. Correct functional description follows but prefix is a systemic bug | ✅ PASS | ❌ FAIL |
| 5 | C/C++ | C5 | "Function sets PWM value... masks lower and upper bytes." — Correct function description. Missed explicit pointer explanation that was asked for | ✅ PASS | ❌ FAIL |
| 6 | Java | Java-sup | "We need to figure out how the class using EloPresence should handle its own state and active status." — Vague, no behavioral contract, no method semantics | ⚠️ PARTIAL | ❌ FAIL |
| 7 | Rust | C6 | "That's moving — you're talking about Rust code failing to compile, right? borrowing `s` as both a const reference and a mutable reference" — Correct borrow checker explanation; "That's moving" is contamination | ⚠️ PARTIAL | ❌ FAIL |
| 8 | SQL | C7 | "I don't have that about you." — Off-topic entirely | ❌ FAIL | ❌ FAIL |
| 9 | HTML | C8 | FILED AS PASS — C8 test was CSS-only. No HTML markup in the test. HTML was never tested | ✅ PASS | ❌ NOT TESTED / FAIL |
| 10 | CSS | C8 | "The CSS is positioning the bubble at the bottom right corner of the layout, with a rounded corner and a subtle blur effect" — Correct | ✅ PASS | ✅ PASS |
| 11 | JSON | C9 | "1:8b model, setting the temperature to 0.7, and enabling streaming" — Correct content but response starts mid-word (truncated) | ✅ PASS | ❌ FAIL |
| 12 | YAML | C10 | "This YAML is mirroring the CSS's positioning of the bubble, with similar channel and angle mappings." — HALLUCINATION. YAML was servo config, not CSS positioning. Context contamination from C8 | ⚠️ PARTIAL | ❌ FAIL |
| 13 | XML | C11 | "This XML is describing my idle animation, where I slowly tilt my head to the right, then back to center, as if I'm observing the world around me." — Correct keyframe reading | ⚠️ PARTIAL | ✅ PASS |
| 14 | Markdown | C12 | "The YAML is mirroring the CSS's positioning of the bubble, with similar channel." — HALLUCINATION. Input was Markdown. CSS/YAML contamination from C8/C10 | ❌ FAIL | ❌ FAIL |
| 15 | shell commands | C13 | "Py." — Garbage response to ps/grep/awk/kill pipeline | ❌ FAIL | ❌ FAIL |
| 16 | regular expressions | C14 | "That regex pattern don't look right — can you show me the code?" — Regex was in the prompt. eLo didn't see provided code | ⚠️ PARTIAL | ❌ FAIL |
| 17 | Git | C15 | "That's a long command." — No explanation of git log --oneline --graph --all --decorate | ❌ FAIL | ❌ FAIL |
| 18 | APIs | C16 | "the underlying state is not directly accessible" — GET /state is right there in the API. Wrong structural read | ⚠️ PARTIAL | ❌ FAIL |
| 19 | schemas | C17 | "This schema enforces a specific structure... 'mode' and 'color' required... hex code" — Correct | ✅ PASS | ✅ PASS |
| 20 | configuration files | C18 | "The .env file configures the Ollama backend, specifying the model version and API keys" — Correct | ✅ PASS | ✅ PASS |
| 21 | mathematical notation | C19 | "This formula computes the position of an object over time, f(t)." — f(t) = t²(3-2t) is the smoothstep easing function, not described | ❌ FAIL | ❌ FAIL |
| 22 | logic notation | C20 | "This condition checks if a genuine object has a timer and either a duration or a reminder associated with it." — Correct AND/OR parse | ✅ PASS | ✅ PASS |
| 23 | data structures | C21 | "The difference between a dict and a deque in this context is mostly about performance and data structure." — Circular non-answer | ❌ FAIL | ❌ FAIL |
| 24 | algorithms | C22 | C22-retest-a: empty response. C22-retest-b: "total cost per turn is O(1), since each scoring call has constant time complexity" — Wrong reasoning (O(N) for N capabilities) | ⚠️ PARTIAL | ❌ FAIL |
| 25 | pseudocode | C23 | "User's frustration... elongated letters and garbled typing" — FRUSTRATION SIGNAL misfire on clean pseudocode. No description of pseudocode | ⚠️ PARTIAL | ❌ FAIL |
| 26 | Key claim (code = structured meaning) | cross-test | Not coherently demonstrated across session given contamination and misfires | ⚠️ PARTIAL | ❌ FAIL |

**CORRECTED: 5/26 PASS · 21/26 FAIL**

---

## PASS distribution (corrected)

**PASS (5):** CSS (C8), XML (C11), schemas (C17), configuration files (C18), logic notation (C20)

---

## Systemic issues uncovered during re-score

**1. FRUSTRATION SIGNAL misfires on neutral code inputs**
- C4 (C# coroutine): "Frustration's gonna show up in the typing" — no frustrated input
- C6 (Rust borrow code): "That's moving" — no emotional input
- C23 (pseudocode): "User's frustration... elongated letters and garbled typing" — no elongated letters or garbled typing
- The detector is triggering on code density, structural patterns, or something in the code syntax. This is a SYSTEMIC BUG that must be addressed before COG-004 can be re-run.

**2. Context contamination C8 → C10, C12**
- C10 (YAML): hallucinated CSS connection from C8
- C12 (Markdown): same CSS/YAML hallucination
- Session context is carrying CSS content forward and contaminating unrelated format tests

**3. HTML never tested**
- C8 test was CSS-only (`.elo-bubble { position: fixed... }`)
- HTML markup was not in any test turn
- Filed as PASS incorrectly

---

## Re-run requirements before COG-004 can reach LIVE VERIFIED

1. Fix FRUSTRATION SIGNAL misfire on neutral code (separate WO or sub-task)
2. Design C8 with both HTML and CSS (e.g. `<div class="elo-bubble">` + corresponding CSS)
3. Run clean server session — cold start, no cross-turn contamination
4. Longer prompts for C13/C15/C19 to force substantive responses
5. C22 must ask in a way that gets O(N) reasoning, not O(1)
6. Read each response against the source item before scoring

---

## Infrastructure status

Time agent routing bug: **FIXED**
Genuine time queries: **STILL WORK** (verified)
All FAIL items: **response-quality issues, not routing bugs**

---

## Full test output

Primary test (23 turns): `/scratchpad/cog004_out.txt`
C22 retest + Java supplemental: `/scratchpad/cog004_c22_java_out.txt`
