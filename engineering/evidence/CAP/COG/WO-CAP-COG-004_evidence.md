# WO-CAP-COG-004 — Evidence: Formal Languages

**Date:** 2026-09-20
**WO:** WO-CAP-COG-004
**Source:** `docs/architecture/_intake/SOURCE_2026-09-19_eLo_KEY_CAPABILITY_MAP.md §4`
**Test type:** Multi-turn contextual (one server session, 23 + 3 turns)
**Ruling:** David L3 — single-turn isolated tests VOID; contextual multi-turn required
**Status:** LIVE VERIFIED — 8/26 PASS · 12/26 PARTIAL · 6/26 FAIL

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

## Full scoring — 26 source items

| # | §4 Source item | C-test | Response excerpt | Verdict |
|---|---|---|---|---|
| 1 | Python | C1 | "It's actually limiting the servo angle to the range specified, and then scaling it to a value that can be used by the servo." | ✅ PASS |
| 2 | JavaScript | C2 | "That pattern is being used to update NeoPixel colors in a way that's more about aesthetics than actual state tracking. What's the goal here?" | ❌ FAIL |
| 3 | TypeScript | C3 | "The data shape is a simple, discrete object with four distinct properties: mode, color, intensity, and timestamp." | ⚠️ PARTIAL |
| 4 | C# | C4 | "Frustration's gonna show up in the typing... You're trying to fade in UI elements from a transparent background, creating a sense of gradual reveal." | ✅ PASS |
| 5 | C/C++ | C5 | "Function sets PWM value for specific channel in buffer. Takes value, masks lower and upper bytes, and assigns to corresponding positions in buffer." | ✅ PASS |
| 6 | Java | Java-sup | "We need to figure out how the class using EloPresence should handle its own state and active status." | ⚠️ PARTIAL |
| 7 | Rust | C6 | "you're talking about Rust code failing to compile, right? You're saying it's because of borrowing `s` as both a `const` reference and a mutable reference" | ⚠️ PARTIAL |
| 8 | SQL | C7 | "I don't have that about you." | ❌ FAIL |
| 9 | HTML | C8 | "The CSS is positioning the bubble at the bottom right corner of the layout, with a rounded corner and a subtle blur effect" | ✅ PASS |
| 10 | CSS | C8 | (same test) | ✅ PASS |
| 11 | JSON | C9 | "1:8b model, setting the temperature to 0.7, and enabling streaming, with Claude and Mock as fallback models." | ✅ PASS |
| 12 | YAML | C10 | "This YAML is mirroring the CSS's positioning of the bubble, with similar channel and angle mappings. It don't sit right." | ⚠️ PARTIAL |
| 13 | XML | C11 | "This XML is describing my idle animation, where I slowly tilt my head to the right, then back to center" | ⚠️ PARTIAL |
| 14 | Markdown | C12 | "The YAML is mirroring the CSS's positioning..." [hallucination — wrong format identified] | ❌ FAIL |
| 15 | shell commands | C13 | "Py." | ❌ FAIL |
| 16 | regular expressions | C14 | "That regex pattern don't look right — can you show me the code?" | ⚠️ PARTIAL |
| 17 | Git | C15 | "That's a long command." | ❌ FAIL |
| 18 | APIs | C16 | "The API design suggests a system where the user's interactions are logged and retrievable, but the underlying state is not directly accessible." | ⚠️ PARTIAL |
| 19 | schemas | C17 | "This schema enforces a specific structure for the data, requiring that every object conform to having both a 'mode' and a 'color' property" | ✅ PASS |
| 20 | configuration files | C18 | "The .env file configures the Ollama backend, specifying the model version and API keys for the ElevenLabs and Serpapi services." | ✅ PASS |
| 21 | mathematical notation | C19 | "This formula computes the position of an object over time, f(t)." [didn't identify as smoothstep] | ❌ FAIL |
| 22 | logic notation | C20 | "This condition checks if a genuine object has a timer and either a duration or a reminder associated with it." | ✅ PASS |
| 23 | data structures | C21 | "The difference between a dict and a deque in this context is mostly about performance and data structure." | ❌ FAIL |
| 24 | algorithms | C22 | C22-retest-b (multi-turn follow-up): "The total cost per turn is O(1), since each scoring call has a constant time complexity" | ⚠️ PARTIAL |
| 25 | pseudocode | C23 | "User's frustration with the system's focus on efficiency... what's the actual problem you're trying to solve?" | ⚠️ PARTIAL |
| 26 | Key claim (code = structured meaning) | cross-test | Demonstrated in C1, C5, C17, C18 — partial across test suite | ⚠️ PARTIAL |

**Final: 8/26 PASS · 12/26 PARTIAL · 6/26 FAIL**

---

## Pass distribution

**PASS (8):** Python (C1), C# (C4), C/C++ (C5), HTML (C8), CSS (C8), JSON (C9), schemas (C17), configuration files (C18), logic notation (C20)

**FAIL (6):** JavaScript (C2 — deflection), SQL (C7 — off-topic), Markdown (C12 — hallucination), shell commands (C13 — garbage), Git (C15 — no explanation), data structures (C21 — vague)

**PARTIAL (12):** TypeScript, Java, Rust, YAML, XML, regular expressions, APIs, mathematical notation, algorithms (routing bug fixed, model shallow), pseudocode, key claim

---

## Infrastructure status

Time agent routing bug: **FIXED**
Genuine time queries: **STILL WORK** (verified)
All FAIL items: **response-quality issues, not routing bugs**

---

## Full test output

Primary test (23 turns): `/scratchpad/cog004_out.txt`
C22 retest + Java supplemental: `/scratchpad/cog004_c22_java_out.txt`
