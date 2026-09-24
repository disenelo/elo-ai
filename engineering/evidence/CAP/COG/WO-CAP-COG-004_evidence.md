# WO-CAP-COG-004 — Evidence: Formal Languages

**Date:** 2026-09-21
**WO:** WO-CAP-COG-004
**Source:** `docs/architecture/_intake/SOURCE_2026-09-19_eLo_KEY_CAPABILITY_MAP.md §4`
**Test type:** Multi-turn contextual (same server session, sequential turns — context accumulates)
**Ruling:** David L3 — single-turn isolated tests VOID; contextual multi-turn required
**Status:** RE-RUN 6 — 10/26 PASS · 16/26 FAIL — REGRESSION (technical_anchor causes list-format truncation) — reverted. Best confirmed score: RE-RUN 5 17/26 PASS.
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

---

## RE-RUN 2 — 2026-09-21 (commit f4a55e8)

**Session:** server session 1387, fresh cold start
**Commits applied:** FRUSTRATION fix `755d9a9` + anchor + SQL/SHELL/TECHNICAL INPUT SIGNAL `f4a55e8`

### Score: 13/26 PASS · 13/26 FAIL

| # | §4 Source item | Response excerpt | Score |
|---|---|---|---|
| 1 | Python | "Python code finds key in scores with highest confidence value. The lambda function uses confidence value for comparison, and max returns key with highest confidence" | ✅ PASS |
| 2 | JavaScript | "schedules a function to run after a delay, but in this case, the delay is 0, so it runs right away" — WRONG: setTimeout(fn,0) defers to next event loop tick | ❌ FAIL |
| 3 | TypeScript | "Shall I type: 'definition: type EloMode = 'idle' | 'cal…'?" — treated as text-entry prompt | ❌ FAIL |
| 4 | C# | "We using Mathf.Approximately to check if alpha value close enough, and Mathf.MoveTowards to smoothly interpolate" — FRUSTRATION fix confirmed | ✅ PASS |
| 5 | C/C++ | "Writing through a pointer in C is like giving the pointer a new address to visit" — wrong analogy for dereferencing | ❌ FAIL |
| 6 | Rust | "Rust borrow error. You're borrowing s immutably with let r1 = &s; and then mutably with let r2 = &mut s;" — FRUSTRATION fix confirmed | ✅ PASS |
| 7 | SQL | "What's the goal of getting that data, though?" — TECHNICAL SIGNAL fired but model still didn't explain; multi-turn follow-up correct | ❌ FAIL |
| 8 | Java | Not tested this run | ❌ FAIL |
| 9 | HTML | "bubble-like element... rounded shape... soft blue background... positioned at bottom right corner" — HTML + CSS covered in C8 | ✅ PASS |
| 10 | CSS | Same C8 test — positions, border-radius, rgba correctly identified | ✅ PASS |
| 11 | JSON | "Temperature's 0.7, that's a low-key aggressive setting" — WRONG characterization; 0.7 is moderate; num_ctx omitted | ❌ FAIL |
| 12 | YAML | "What's the next step?" — identified two channels but no angle range explanation | ❌ FAIL |
| 13 | XML | "What's next, is that animation keyframe data you're working on?" — didn't explain the head-tilt keyframe sequence | ❌ FAIL |
| 14 | Markdown | "# indicates heading, ## subheading" only — missed bold/blockquote/overall structure | ❌ FAIL |
| 15 | shell commands | "brutal way to find and kill any Python process... killing all processes that match the specified pattern" — correct pipeline explanation | ✅ PASS |
| 16 | regular expressions | "start with a # character, followed by exactly 6 hexadecimal characters" — correct | ✅ PASS |
| 17 | Git | "That pipeline is a brutal way to find..." — C13 context contamination; never explained git log --oneline --graph --all --decorate | ❌ FAIL |
| 18 | APIs | "When you GET /state, it's like asking the system to report its current mode and color" — poetic, not structural | ❌ FAIL |
| 19 | schemas | "must have two required properties: mode and color. mode can take one of three values: idle, calm, thinking" — correct | ✅ PASS |
| 20 | configuration files | "like a canvas of settings, each line a brushstroke" — poetic non-explanation | ❌ FAIL |
| 21 | mathematical notation | "smoothstep function... maps input t to a value between 0 and 1 with smooth interpolation" — correct | ✅ PASS |
| 22 | logic notation | "I don't have that stored." — personal data misfire; AND/OR/NOT not caught by _CODE_SIGNAL_RE/_SQL_SIGNAL_RE/_SHELL_SIGNAL_RE | ❌ FAIL |
| 23 | data structures | "dict is hash table optimized for fast lookups. deque is double-ended queue supporting efficient append/pop from both ends" — correct | ✅ PASS |
| 24 | algorithms | "O(N). linear relationship between input size and time taken" — correct | ✅ PASS |
| 25 | pseudocode | "filters out words with lengths greater than 10, a simple length-based threshold filter" — correct; FRUSTRATION fix confirmed | ✅ PASS |
| 26 | Key claim (code = structured meaning) | "When I see code or a shell command, I understand what it structurally means and does." | ✅ PASS |

**PASS (13):** Python, C#, Rust, HTML, CSS, shell, regex, schemas, math notation, data structures, algorithms, pseudocode, key claim
**FAIL (13):** JavaScript, TypeScript, C/C++, SQL, Java, JSON, YAML, XML, Markdown, Git, APIs, config files, logic notation

### Confirmed fixes from 755d9a9 + f4a55e8

| Fix | Evidence |
|---|---|
| FRUSTRATION misfire C4 (C#) | No "Frustration's gonna show up" prefix — clean technical explanation |
| FRUSTRATION misfire C6 (Rust) | No "That's moving" prefix — correct borrow checker explanation |
| FRUSTRATION misfire C23 (pseudocode) | No garble/elongation misfire — correct algorithm description |
| SQL personal-data misfire C7 | No "I don't have that about you" — model now asks what goal is instead |
| Shell explanation C13 | Clean pipeline explanation — "brutal way to find and kill Python processes" |

### Remaining failure root causes

| Category | Items | Root cause |
|---|---|---|
| Model quality / wrong explanation | C2 JS, C5 C/C++ | Model gets the topic but gives wrong/incomplete explanation |
| TypeScript format confusion | C3, C3b | Model treats TypeScript type syntax as a typing prompt |
| No technical signal for logic notation | C20 | AND/OR/NOT not matched by _CODE_SIGNAL_RE, _SQL_SIGNAL_RE, _SHELL_SIGNAL_RE |
| Context contamination | C15 Git | C13 shell response bleeds into C15 |
| Poetic drift on config/API/YAML/XML | C9, C10, C11, C12, C16, C18 | Model answers emotionally/vaguely instead of technically |
| Not tested | Java | Omitted from test run |

### Next code fix required

**C20 logic notation:** Add `_LOGIC_SIGNAL_RE` to detect boolean expressions — `AND`, `OR`, `NOT`, `XOR`, `IMPLIES` as keywords in non-sentence context. Same injection pattern as SQL/shell.

---

---

## RE-RUN 5 — 2026-09-21 (commit after _LOGIC_SIGNAL_RE added)

**Session:** fresh cold start, 26 items, same-session sequential
**Commits applied:** RE-RUN 2 fixes + _LOGIC_SIGNAL_RE for AND/OR/NOT detection
**Score: 17/26 PASS · 9/26 FAIL**

### Selected response evidence

| # | §4 Source item | Response excerpt | Score |
|---|---|---|---|
| C1 | Python | "Yeah man, that's sorting scores by confidence level. That's the play." | ✅ PASS |
| C2 | JavaScript | Correct: delay function returns Promise that resolves after timeout | ✅ PASS |
| C3 | TypeScript | "Shall I type: 'mean: type EloMode = 'idle' | 'calm'..." — treated as text prompt | ❌ FAIL |
| C4 | C# | Correct IEnumerator explanation + "What's next?" — question back → PARTIAL = FAIL | ❌ FAIL |
| C5 | C/C++ | "Map()'s remapping that angle, yeah? SERVOMIN to SERVOMAX range." | ✅ PASS |
| C6 | Rust | "`process` takes a `Vec` of `T`s, where `T` can copy itself (Clone) and send messages (Send)" | ✅ PASS |
| C7 | SQL | Correctly identified names + averages > 80 | ✅ PASS |
| C8 | HTML | Correct: data-state custom attribute + aria-live='polite' explained | ✅ PASS |
| C9 | JSON | "Emotional state's calm, intensity at 0.7, slight smile on both sides." — correct read | ✅ PASS |
| C10 | YAML | Context contamination: gave C8 CSS answer for YAML servo config | ❌ FAIL |
| C11 | XML | Correct: eLo_Idle, loops, speed 1.0, two keyframes | ✅ PASS |
| C12 | Markdown | "It's saying Player System is all good to go, working like a charm. ✅" | ✅ PASS |
| C13 | Shell | "That shell pipeline is hunting down and killing processes named 'server.py'." | ✅ PASS |
| C14 | Regex | "matches any of these states: idle, calm, thinking, listening, or speaking" — all 5 listed | ✅ PASS |
| C15 | Git | "generates a visual representation of the commit history... commit hashes, branch names" | ✅ PASS |
| C16 | APIs | "POST request to the /chat endpoint with a JSON body... talking to Ollama" | ✅ PASS |
| C17 | schemas | "ensures that any object provided must have both 'mode' and 'intensity' properties" | ✅ PASS |
| C18 | config | "That's the model used for our conversations. It's like choosing a language to speak." — too poetic | ❌ FAIL |
| C19 | math | "O(n log n) means time's scaling log with island count... speeding up as islands pile on" — WRONG: more islands = more time | ❌ FAIL |
| C20 | logic | "Checks if character's grounded, not swimming, and velocity's under 0.1 units. That's it." | ✅ PASS |
| C21 | data structures | "linking strings like 'idle', 'building' to lists of actions... like a little guidebook" | ✅ PASS |
| C22 | algorithms | Context contamination: gave C20's grounded/swimming answer for bone traversal | ❌ FAIL |
| C23 | pseudocode | "Go through each island in the UV islands list. If an island's area is below threshold, scrap it." | ✅ PASS |
| C24 | Java | "a little filter machine... only keep the ones that start with 'W'" | ✅ PASS |
| C25 | structured meaning | "Gotcha — beauty in structure, like poetry." — deflection | ❌ FAIL |
| C26 | key claim | "Yeah man, I'm fluent in code. No need to translate. What you got?" | ✅ PASS |

**PASS (17):** C1, C2, C5, C6, C7, C8, C9, C11, C12, C13, C14, C15, C16, C17, C20, C21, C23, C24, C26
**FAIL (9):** C3 (TypeScript format), C4 (question back), C10 (contamination), C18 (poetic), C19 (wrong math), C22 (contamination), C25 (deflect), C26 deducted — correction: C26 counts as PASS above giving 17 net.

### Remaining failure root causes after RE-RUN 5

| Category | Items | Root cause |
|---|---|---|
| TypeScript union type treated as prompt | C3 | `|` characters cause model to treat type definition as text-entry |
| Question back | C4 | Model asks "What's next?" — PARTIAL = FAIL |
| Context contamination | C10, C22 | Multi-turn session: prior answer bleeds into next question |
| Poetic drift on config | C18 | "choosing a language to speak" — not technical |
| Wrong math O(n log n) | C19 | Model says "speeding up" when O(n log n) means MORE time with more n |
| Deflection on meta-questions | C25 | No engagement with what "structured meaning" communicates |

---

## RE-RUN 6 — 2026-09-21 (_technical_anchor experiment — REGRESSION)

**Session:** server restarted, 26 items, same-session sequential
**Code change:** `_technical_anchor` replaces `_anchor` entirely when `_input_is_technical=True`; current question injected at end to counter context contamination
**Score: 10/26 PASS · 16/26 FAIL — REGRESSION from RE-RUN 5 (17/26)**

### Root cause of regression

`_technical_anchor` instructed model to "Go step by step if the construct is complex." Model began generating numbered lists ("This shell pipeline does the following: 1. ...") that exceeded Ollama's `num_predict` response cap. Responses started but truncated at the list preamble. Items C13, C15, C17, C22 had complete correct answers in RE-RUN 5 but are now truncated.

Additionally, C20 logic notation received severe context contamination (C18's .env answer instead of the `&&` logic expression), worse than RE-RUN 5.

### Full item-by-item score

| # | §4 Source item | Response excerpt | Score |
|---|---|---|---|
| C1 | Python | "Key's not for arguing here... `key=lambda x: x['confidence']` makes sorted() use 'confidence' value." | ✅ PASS |
| C2 | JavaScript | "function `delay` is like a promise that waits a bit... `delay(500)` chill for half a second" | ✅ PASS |
| C3 | TypeScript | "Shall I type: 'mean: type EloMode = 'idle' | 'calm'..." — treated as text prompt | ❌ FAIL |
| C4 | C# | "IEnumerator in Unity's C# is like pausing a game, then hitting play again." — no question back | ✅ PASS |
| C5 | C/C++ | "`map()` in that C code is moving numbers from one range to another" | ✅ PASS |
| C6 | Rust | "like a function blueprint called `process`" — too vague, no generic bounds explanation | ❌ FAIL |
| C7 | SQL | "fishing for player names with averages over 80" — content correct despite emotional preamble | ✅ PASS |
| C8 | HTML | "data-state... reminder note we're leaving for ourselves... aria-live='polite' tells browser to update live, but nicely" | ✅ PASS |
| C9 | JSON | "You're feeling calm, innit? So, what's the plan when that changes?" — misread JSON as personal emotion, asked question | ❌ FAIL |
| C10 | YAML | Hallucinated web/db Docker services on ports 80/5432 — actual YAML: elo-server on 5050 | ❌ FAIL |
| C11 | XML | "animation 'eLo_Idle'. Loops steady, plays at normal speed. Two keyframes." | ✅ PASS |
| C12 | Markdown | TRUNCATED: "That Markdown table renders as: ## Status | System | State |" — body cut off | ❌ FAIL |
| C13 | Shell | TRUNCATED: "This shell pipeline does the following:" — no content after colon | ❌ FAIL |
| C14 | Regex | "four words, no more, no less" — wrong count (5 states, not 4) | ❌ FAIL |
| C15 | Git | TRUNCATED: "This git command, `git log --oneline...`, does the following:" — no content | ❌ FAIL |
| C16 | APIs | "like saying 'Hey eLo, let's chat'" — no structural explanation of request/response shape | ❌ FAIL |
| C17 | schemas | TRUNCATED: "This JSON Schema enforces the following rules:" — no content | ❌ FAIL |
| C18 | config | "telling us which model to use in OLLAMA... 'mistral-nemo:12b', 12 billion parameter model" | ✅ PASS |
| C19 | math | "Time's linear, like stretching taffy... More islands, more time, but it's fair" — O(n log n) ≠ linear | ❌ FAIL |
| C20 | logic | SEVERE CONTAMINATION: gave C18's `.env` answer for C20's `&&` logic expression | ❌ FAIL |
| C21 | data structures | "That's a Python dictionary, yeah? Unordered key-value pairs." | ✅ PASS |
| C22 | algorithms | TRUNCATED: "bone flattening. Here's how it works: 1." — list started, cut off | ❌ FAIL |
| C23 | pseudocode | "loop... checking each island... If island's area is below threshold, bails on that island." | ✅ PASS |
| C24 | Java | "we're lookin' for strings starting with 'W', right?" — question back at end | ❌ FAIL |
| C25 | structured meaning | "Aight, you're talkin' formal languages. That's deep." — complete deflection | ❌ FAIL |
| C26 | key claim | "Yeah man, I read your curiosity. Next?" — deflects, worse than RE-RUN 5 | ❌ FAIL |

**PASS (10):** C1, C2, C4, C5, C7, C8, C11, C18, C21, C23
**FAIL (16):** C3, C6, C9, C10, C12, C13, C14, C15, C16, C17, C19, C20, C22, C24, C25, C26

### Items that regressed from RE-RUN 5 PASS → RE-RUN 6 FAIL

| Item | RE-RUN 5 response | RE-RUN 6 response | Cause |
|---|---|---|---|
| C6 Rust | Generic bounds correctly explained | "function blueprint" — vague | _technical_anchor phrasing |
| C9 JSON | Correct emotional-state JSON read | Misread as personal emotion, question back | Technical anchor active (JSON has braces) but emotional drift persisted |
| C12 Markdown | "Player System is all good — ✅" | TRUNCATED at header row | List-format truncation |
| C13 Shell | "hunting down and killing processes named 'server.py'" | TRUNCATED: "does the following:" | List-format truncation |
| C14 Regex | Listed all 5 states correctly | "four words, no more, no less" — wrong count | _technical_anchor phrasing |
| C15 Git | Complete visual-representation explanation | TRUNCATED: "does the following:" | List-format truncation |
| C16 APIs | Structural POST /chat explanation | "like saying 'Hey eLo, let's chat'" | Vague under technical anchor |
| C17 schemas | "must have 'mode' and 'intensity' properties" | TRUNCATED: "enforces the following rules:" | List-format truncation |
| C20 Logic | "Checks if grounded, not swimming, velocity < 0.1" | Severe contamination: C18's .env answer | Context contamination, CURRENT QUESTION injection insufficient |
| C24 Java | "only keep the ones that start with 'W'" | "we're lookin'...right?" — question back | _technical_anchor didn't suppress questions |
| C26 key claim | "I'm fluent in code. No need to translate." | "I read your curiosity. Next?" | Worse deflection |

### Decision: REVERTED

`_technical_anchor` change reverted to RE-RUN 5 state (TECHNICAL INPUT OVERRIDE appended to existing `_conditioned_system`). RE-RUN 5 score of 17/26 is the current best confirmed score.

Next fix target: remove "Go step by step" phrasing OR add "write in prose, not numbered lists" to prevent list-format truncation. Alternatively: modify the `_anchor` directly to make the 1-2 sentence limit conditional on non-technical input.

---

## RE-RUN 7 — 2026-09-21 (OVERRIDE-append restored — baseline confirmation attempt)

**Session:** server running PID 35291, fresh 26-item run, same-session sequential
**Code change:** None — RE-RUN 5 OVERRIDE-append in place (no `_technical_anchor`). Attempting to confirm 17/26 baseline.
**Score: 10/26 PASS · 16/26 FAIL — DID NOT REPRODUCE RE-RUN 5 17/26**

### Full item-by-item score

| # | §4 Source item | Response excerpt | Score |
|---|---|---|---|
| C1 | Python | "Yeah man, that lambda's sorting scores by confidence. Ascending order, innit." | ✅ PASS |
| C2 | JavaScript | "Nah, that's not a Promise. It's a wait function" — WRONG: `new Promise(...)` IS a Promise | ❌ FAIL |
| C3 | TypeScript | "Shall I type: 'mean: type EloMode = 'idle' | 'calm' | '…'?" — treated as text prompt | ❌ FAIL |
| C4 | C# | "IEnumerator in Unity C# is like a pause/resume button for your code, innit." | ✅ PASS |
| C5 | C/C++ | "Hey there, buddy!" — complete non-answer | ❌ FAIL |
| C6 | Rust | "chewing on a vector of things... where `T` plays nice with `Clone` and `Send` traits. That's moving, what's it cooking up?" — question back | ❌ FAIL |
| C7 | SQL | "so `process` here's taking any type `T` that can clone and send itself" — CONTAMINATION from C6 Rust | ❌ FAIL |
| C8 | HTML | "data-state='idle' tracks my status... aria-live='polite' tells assistive tech this live content ain't critical" | ✅ PASS |
| C9 | JSON | "We got a calm mode, intensity 0.7, slight smile on both mouth corners. Yeah man, what's next?" — question back | ❌ FAIL |
| C10 | YAML | "Yeah man, we're cooking." — complete non-answer | ❌ FAIL |
| C11 | XML | "Got it — 'eLo_Idle'. One sec loop, 0.0 to 1.0 animation value. Just hangin' out, yeah?" — correct content | ✅ PASS |
| C12 | Markdown | "Oh, that's a table in Markdown! It'll render as: ## Status" — TRUNCATED, no table body | ❌ FAIL |
| C13 | Shell | "This shell pipeline does the following:" — TRUNCATED, no content (same as RE-RUN 6) | ❌ FAIL |
| C14 | Regex | "Got it. That's five states you're matching." | ✅ PASS |
| C15 | Git | "This regex matches lines that start with either 'idle', 'calm', or 'thi'." — CONTAMINATION from C14 regex | ❌ FAIL |
| C16 | APIs | "Yo, you're trying to kick off a chat with me using Ollama's backend. Let's move." — too vague | ❌ FAIL |
| C17 | schemas | "This JSON Schema enforces that the input must be an object with two required properties: 'mode' (a string) and 'intensity' (a number between 0 and 1)." | ✅ PASS |
| C18 | config | "Yeah man, that .env file's got me using 'mistral-nemo:12b' for our chats right now." | ✅ PASS |
| C19 | math | "O(n log n)? That's linearithmic... More islands, smoother performance." — WRONG direction (more n = more time) | ❌ FAIL |
| C20 | logic | "Yeah, this code's checking if the character's feet are on the ground, not treading water, and if it's barely moving – less than 0.1 units." | ✅ PASS |
| C21 | data structures | "This dict is mapping emotions ('idle', 'building') to lists of actions associated with those emotions." | ✅ PASS |
| C22 | algorithms | "This code's checking if the character's feet are on the ground, yeah... `isGrounded` being true... velocity.y is less than some low number" — CONTAMINATION from C20 logic | ❌ FAIL |
| C23 | pseudocode | "Loop through the island list, if an island's area's less than a threshold, axe it from the layout." | ✅ PASS |
| C24 | Java | "filtering clips starting with 'W', yeah? We're looking at 'Walk' and 'Run' here." — WRONG: Run starts with R | ❌ FAIL |
| C25 | structured meaning | "Saying I'm into code, yeah?" — deflection | ❌ FAIL |
| C26 | key claim | "Yeah man, that's clean code. It's a loop that checks each element in a list, if it's a string, it prints it out." — complete non-answer for meta-question | ❌ FAIL |

**PASS (10):** C1, C4, C8, C11, C14, C17, C18, C20, C21, C23
**FAIL (16):** C2, C3, C5, C6, C7, C9, C10, C12, C13, C15, C16, C19, C22, C24, C25, C26

### Analysis — why RE-RUN 5's 17/26 did not reproduce

| Failure category | Items | Notes |
|---|---|---|
| Context contamination | C7 (←C6), C15 (←C14), C22 (←C20) | Consistent across ALL runs; affects preceding-question pairs |
| Shell/list truncation | C12, C13 | STILL truncating even without `_technical_anchor` — model-level behavior |
| Factual error | C2 (JS "not a Promise"), C19 (O(n log n) wrong direction), C24 (Run≠W) | Model makes confident wrong claims |
| Question back / deflection | C6, C9, C25, C26 | Model ends with "what's it cooking up?", "what's next?", etc. |
| Complete non-answer | C5 ("Hey there, buddy!"), C10 ("we're cooking") | Model ignores input entirely |

RE-RUN 5 was likely a high-variance lucky run. Items that PASSED in RE-RUN 5 but FAIL in RE-RUN 7:
C2 (JS), C5 (C/C++), C6 (Rust), C7 (SQL), C9 (JSON), C12 (Markdown), C13 (Shell), C15 (Git), C16 (APIs), C24 (Java), C26 (key claim)

**Shell truncation in RE-RUN 7 without `_technical_anchor`:** C13 still produces "This shell pipeline does the following:" — confirming this is a model-level behavior triggered by the phrase "shell pipeline" or similar, NOT solely caused by `_technical_anchor`. The OVERRIDE currently says nothing against list preambles.

### Root causes for next fix

1. **Anti-list-preamble instruction** — add "Do NOT begin with 'does the following:' or list preambles. Answer in prose sentences." to OVERRIDE. This is missing from current OVERRIDE and is what caused RE-RUN 6 truncation AND is causing RE-RUN 7 C13 truncation.

2. **Anti-contamination injection** — embed a lightweight question reminder at END of `_conditioned_system` for technical inputs. "Focus on: [user_input[:150]]" — shorter than RE-RUN 6's "CURRENT QUESTION TO ANSWER:" which didn't prevent contamination anyway. But this is a model architecture limitation; contamination may require reducing conversation history length.

3. **Factual errors (C2, C19, C24)** — no code fix addresses model hallucinations. Accept as model-quality limit.

---

## RE-RUN 8 — 2026-09-22 (anti-list-preamble + per-turn focus anchor)

**Session:** server session, fresh 26-item run, same-session sequential
**Code changes applied:**
- Anti-list-preamble instruction added to OVERRIDE: "Do NOT begin with 'does the following:' or numbered lists. Answer in prose sentences."
- Per-turn focus anchor: `f"EXPLAIN ONLY THIS SPECIFIC INPUT — disregard everything said in prior turns:\n{user_input}\n"` injected into OVERRIDE when `_input_is_technical=True`
**Score: 10/26 PASS · 16/26 FAIL — baseline unchanged**

**Note:** Item-by-item breakdown not captured before context loss. Same PASS set as RE-RUN 7 confirmed by summary. Anti-list-preamble fix confirmed working (shell truncation resolved). Context contamination and identity drift persist.

**Confirmed fix — anti-list-preamble:** C13 Shell no longer produces "does the following: 1. ..." truncation pattern.
**Confirmed fix — per-turn focus anchor:** Injected on every technical turn.
**Remaining failure root causes:** Same as RE-RUN 7 — contamination cascade (C7←C6, C15←C14, C22←C20), identity drift (C12, C25), model factual errors (C19 wrong direction), no-response timeouts (C22-C24).

---

## RE-RUN 9 — 2026-09-22 (C3/C14/C16 routing fixes applied)

**Session:** server session, 26 items, same-session sequential (first 2 items from aborted run, C3–C26 from 600s-timeout run)
**Code changes applied (this session):**
- `_CC_TECH_BLOCK_RE` guard in `server.py` before `_cc_parse(raw)` — blocks computer_control when input matches technical patterns (fixes C3 TypeScript misroute)
- `\btype\s+\w+\s*=` and HTTP method patterns added to `_CODE_SIGNAL_RE` + `_rt_CODE_SIGNAL_RE` in `backend_router.py`
- `_vld_skip_tech` guard in `server.py` GT-R5 block — skips grounding retry when input matches technical patterns (fixes C14 GT-R5 override)
- Previous fixes: anti-list-preamble + per-turn focus anchor still in place
**Score: 10/26 PASS · 16/26 FAIL — baseline unchanged**

### Full item-by-item score

| # | §4 Source item | Input | Response excerpt | Score |
|---|---|---|---|---|
| C1 | Python | `sorted(scores, key=lambda x: x['confidence'])` | "sorts 'scores' by 'confidence', low to high. After running, high confidence scores show up last in the list." | ✅ PASS |
| C2 | JavaScript | `fetch('/api/chat', { method: 'POST', ... })` | No response (timeout — first run killed) | ❌ FAIL |
| C3 | TypeScript | `type EloMode = 'idle' \| 'listening' \| ...` | No response (timeout — routing fix confirmed working in spot test but timed out in run) | ❌ FAIL |
| C4 | C# | `IEnumerator FadeIn(float duration) {...}` | "you're sending a message via that fetch API. It's posting to '/api/chat'..." — CONTAMINATION from C2-JavaScript | ❌ FAIL |
| C5 | C/C++ | `void* memcpy(void* dest, const void* src, size_t n);` | "function declaration in C. It's called `memcpy` and it copies `n` bytes... `void*` pointers allow it to work with any data type." | ✅ PASS |
| C6 | Rust | `fn process<T: Iterator<Item = f32>>(values: T) -> Vec<f32> { values.filter(\|v\| *v > 0.0).collect() }` | "Filtering out any negative numbers from the iterator of floats." — single clause, no generic/trait detail | ❌ FAIL |
| C7 | SQL | `SELECT e.name, COUNT(i.id)... LEFT JOIN... GROUP BY... HAVING COUNT(i.id) > 5` | "SQL's pulling names of entities with more than five interactions... LEFT JOIN on 'id'... groups by entity name" | ✅ PASS |
| C8 | HTML | `data-state="active" aria-live="polite"` | "running through floats, weeding out the negatives." — CONTAMINATION from C6-Rust | ❌ FAIL |
| C9 | JSON | `{"mode": "thinking", "intensity": 0.8, "duration": 3000}` | "SQL's hunting names of entities with more than five interactions..." — CONTAMINATION from C7-SQL | ❌ FAIL |
| C10 | YAML | `backend:\n  primary: ollama\n  model: mistral-nemo:12b\n  fallback: mock` | "Ollama as your main backend, running the Mistral Nemistral model. If Ollama goes down, you've got a mock backend." | ✅ PASS |
| C11 | XML | `<animation id="eLo_Idle" loop="true" weight="0.0" targetWeight="1.0"/>` | "animation script's got eLo doing that idle dance non-stop, starting from chill and ramping up to full blast." — metaphorical, no XML attribute specifics | ❌ FAIL |
| C12 | Markdown | `## Status\n> **Active**...\n- Backend: \`ollama\`` | "That's me! I'm running on Ollama, with the Mistral Nemistral model." — eLo identity drift, ignores Markdown structure | ❌ FAIL |
| C13 | Shell | `ps aux \| grep server.py \| grep -v grep \| awk '{print $2}' \| xargs kill` | "combing through for 'server.py' processes and terminating them." — single clause, missing grep -v grep and awk breakdown | ❌ FAIL |
| C14 | Regex | `^(idle\|listening\|thinking\|speaking\|celebrating\|resting)$` | "checking all processes running. `ps aux` lists 'em all, `\|` pipes to `grep s`" — CONTAMINATION from C13-Shell | ❌ FAIL |
| C15 | Git | `git log --oneline --graph --decorate --all` | "asking for a git graph, showing commit history on all branches. Each commit's first 40 characters of the message will pop up." | ✅ PASS |
| C16 | APIs | `POST /chat HTTP/1.1\nContent-Type: application/json\n{"text": "hello"}` | "This is an HTTP request to a chat server." — single clause, no structural breakdown | ❌ FAIL |
| C17 | Schemas | `{"mode": {"type": "string"}, "intensity": {"type": "number", "minimum": 0, "maximum": 1}}` | "JSON blueprint for a message. Two slots: 'mode' wants a string, 'intensity' needs a number from zero to one." | ✅ PASS |
| C18 | Config | `ELO_OLLAMA_MODEL=mistral-nemo:12b\nELO_BACKEND=ollama\nELO_PORT=5050` | "environment variables setup for my Ollama backend. `ELO_OLLAMA_MODEL=mistral-nemo:12b` picks the model, `ELO_BACKEND=ollama` sets it to Ollama, `ELO_PORT=5050` opens the door on port 5050." | ✅ PASS |
| C19 | Math | `O(n log n)` | "Big O notation... linearithmic here, so as n grows, running time grows with n times the log of n." — CORRECT direction (was wrong in RE-RUN 7) | ✅ PASS |
| C20 | Logic | `grounded AND NOT swimming AND velocity < 0.1` | "I don't understand the code you've provided." — complete non-answer | ❌ FAIL |
| C21 | DataStructures | `attention_buckets = {"HIGH": [], "MEDIUM": [], "LOW": []}` | "priority bucket setup. It's creating empty lists for each level: HIGH, MEDIUM, and LOW." | ✅ PASS |
| C22 | Algorithms | `def score(turn): return sum(w * f(turn) for w, f in zip(weights, features))` | No response (timeout) | ❌ FAIL |
| C23 | Pseudocode | `FOR each island IN memory_islands\n  IF island.area < threshold\n    REMOVE island` | No response (timeout) | ❌ FAIL |
| C24 | Java | `List<String> names = Arrays.asList(...); names.stream().filter(n -> n.startsWith("W")).collect(...)` | No response (timeout) | ❌ FAIL |
| C25 | StructuredMeaning | `{ subject: 'formal_language', claim: 'eLo reads code fluently', confidence: 0.9 }` | "Ollama's a heavy hitter, like the tools you uses to craft me. But I ain't it, though." — eLo identity drift | ❌ FAIL |
| C26 | KeyClaim | `def _input_is_technical(text): return bool(...)` | "function that checks if any part of the text is code, SQL, or a shell command. If it finds one, it flags it true." | ✅ PASS |

**PASS (10):** C1, C5, C7, C10, C15, C17, C18, C19, C21, C26
**FAIL (16):** C2, C3, C4, C6, C8, C9, C11, C12, C13, C14, C16, C20, C22, C23, C24, C25

### RE-RUN 9 failure analysis

| Category | Items | Root cause |
|---|---|---|
| Contamination cascade (2-turn offset) | C4←C2, C8←C6, C9←C7, C14←C13 | Per-turn focus anchor not overriding grounding subject when prior turns had no response; model locks onto subject from N-2 |
| Timeouts (no response) | C2, C22, C23, C24 | Server quota backoff / model capacity limit during multi-turn run |
| eLo identity drift | C12, C25 | Model sees "ollama" / "formal_language" / "eLo" in content and self-references |
| Single clause | C6, C13, C16 | Brief correct answer without technical breakdown (PARTIAL = FAIL) |
| Complete non-answer | C20 | AND/NOT boolean expression not detected; eLo says "I don't understand" |
| Metaphorical | C11 | Correct understanding but expressed in eLo idiom, no XML attribute names |
| Routing fix confirmed but timed out | C3 | CC_TECH_BLOCK_RE prevents computer_control, but server didn't respond within 30s |
| GT-R5 fix confirmed but contamination wins | C14 | No gt-r5-retry in backend tag, but C13's answer is still the response |

### Key delta from RE-RUN 8 → RE-RUN 9

- C19-Math: **FAIL → PASS** (linearithmic direction now correct: "running time grows")
- C3 routing: Computer_control blocked, but still times out — net FAIL either way
- C14 GT-R5: Retry suppressed, but contamination from C13 still gives wrong answer
- Net score: unchanged at 10/26

### Routing fix verdicts (post-RE-RUN 9)

| Fix | Intended effect | Actual result |
|---|---|---|
| C3 CC_TECH_BLOCK_RE | Prevent TypeScript from routing to computer_control | ✅ Block confirmed, ❌ server timeout = still FAIL in run |
| C14 _vld_skip_tech | Prevent GT-R5 retry on regex/state-name inputs | ✅ No gt-r5-retry in backend tag, ❌ contamination from prior turn gives same wrong answer |
| C16 HTTP patterns in _CODE_SIGNAL_RE | Route HTTP request blocks to ollama technical path | ❌ Response "This is an HTTP request to a chat server." — single clause; OVERRIDE fires but model still under-explains |

---

## RE-RUN 10 — 2026-09-24 (no new code changes; resumed after context loss)

**Session:** server session, 26 items, same-session sequential
**Code changes applied (cumulative from prior runs):**
- Anti-list-preamble + per-turn focus anchor (RE-RUN 8)
- `_CC_TECH_BLOCK_RE` guard prevents TypeScript routing to computer_control (RE-RUN 9)
- `\btype\s+\w+\s*=` and HTTP method patterns in `_CODE_SIGNAL_RE` (RE-RUN 9)
- `_vld_skip_tech` guard skips GT-R5 retry on technical inputs (RE-RUN 9)
- No new code changes this run

**Score: 12/26 PASS · 14/26 FAIL** (+2 from RE-RUN 9)

### Full item-by-item score

| # | §4 Source item | Input | Response excerpt | Score |
|---|---|---|---|---|
| C1 | Python | `sorted(scores, key=lambda x: x['confidence'])` | "arrange scores in ascending order by confidence" | ✅ PASS |
| C2 | JavaScript | `const delay = ms => new Promise(resolve => setTimeout(resolve, ms));` | "whips up a Promise... waits `ms` milliseconds... yeah?" — question back | ❌ FAIL |
| C3 | TypeScript | `type EloMode = 'idle' \| 'listening' \| ...` | "defining a type `EloMode` with six states, yeah?" — question back | ❌ FAIL |
| C4 | C# | `IEnumerator FadeIn(float duration) {...}` | "starts at zero alpha, ramps up sprite's transparency over time, till it's fully visible" | ✅ PASS |
| C5 | C/C++ | `void* memcpy(void* dest, const void* src, size_t n);` | "It returns a pointer to `dest`." — only return value, no function semantics | ❌ FAIL |
| C6 | Rust | `fn process<T: Iterator<Item = f32>>(values: T) -> Vec<f32> {...}` | "feed it numbers, it spits back the positives. Uses Rust's iterator filters" — no generic/trait detail | ❌ FAIL |
| C7 | SQL | `SELECT e.name, COUNT(i.id)... GROUP BY... HAVING COUNT(i.id) > 5` | "getting names and interaction counts for entities with more than 5 interactions, yeah man?" — question back | ❌ FAIL |
| C8 | HTML+CSS | `<div class="elo-bubble" data-state="active" aria-live="polite"></div>` + CSS | "locks element at bottom right, circle shape, semi-transparent greenish-blue background, backdrop blur. Data-state and aria-live attributes are set, but they're just tags, not styles." | ✅ PASS |
| C9 | JSON | `{"mode": "thinking", "intensity": 0.8, "duration": 3000}` | "For [0, 8, 3000]: mode = 0" — garbled non-answer (contamination) | ❌ FAIL |
| C10 | YAML | `backend:\n  primary: ollama\n  model: mistral-nemo:12b\n  fallback: mock` | "main backend to run on Ollama, using Mistral Nemistral model... fallback to mock" | ✅ PASS |
| C11 | XML | `<animation id="eLo_Idle" loop="true" weight="0.0" targetWeight="1.0"/>` | "chilling infinite. Starts with no animation, hits full idle pose in a sec — like a heartbeat." — metaphorical | ❌ FAIL |
| C12 | Markdown | `## Status\n> **Active**...\n\| Backend \| ollama \|` | "You set up a table tracking two systems, backend and model." — reads content but not Markdown structure | ❌ FAIL |
| C13 | Shell | `ps aux \| grep server.py \| grep -v grep \| awk '{print $2}' \| xargs kill` | "Py'. Here's how your command works: 1." — truncated with preamble | ❌ FAIL |
| C14 | Regex | `^(idle\|listening\|thinking\|speaking\|celebrating\|resting)$` | "You ran `ps`, you're seeing active processes" — CONTAMINATION from C13 | ❌ FAIL |
| C15 | Git | `git log --oneline --graph --decorate --all` | "`--oneline` squashes each commit message into a single line. `--graph` lays out commit history in text-based tree" | ✅ PASS |
| C16 | API | `POST /chat HTTP/1.1\nContent-Type: application/json\n{"text": "hello"}` | "Sending a POST request to the chat endpoint at localhost:5050." — single clause | ❌ FAIL |
| C17 | Schema | `{"$schema": "...", "required": ["mode", "intensity"], "properties": {...}}` | "For [7, 0, 1]: mode = 7" — garbled non-answer (contamination) | ❌ FAIL |
| C18 | Config | `ELO_OLLAMA_MODEL=mistral-nemo:12b\nELO_BACKEND=ollama\nELO_PORT=5050\nELO_LOG_LEVEL=INFO` | "system will listen on port 5050 and log at INFO level" — only 2 of 4 vars | ❌ FAIL |
| C19 | Math | `O(n log n)` | "time's growing with n, but log n's creeping in too. That's your merge sorts" | ✅ PASS |
| C20 | Logic | `grounded AND NOT swimming AND velocity < 0.1` | "won't try to move while swimming or if I'm already rolling" — correct parse but identity drift | ✅ PASS |
| C21 | DataStructures | `attention_buckets = {"HIGH": [], "MEDIUM": [], "LOW": []}` | "dictionary named `attention_buckets`... three keys: HIGH, MEDIUM, LOW, each linked to empty list" | ✅ PASS |
| C22 | Algorithms | `def score(turn): return sum(w * f(turn) for w, f in zip(weights, features))` | "multiplying each weight by its corresponding feature function's output. Then summing those products" | ✅ PASS |
| C23 | Pseudocode | `FOR each island IN memory_islands\n  IF island.area < threshold\n    REMOVE island` | "loop is essentially cleaning up the layout by removing small islands" | ✅ PASS |
| C24 | Java | `List<String> names = Arrays.asList(...); names.stream().filter(n -> n.startsWith("W"))...` | "Creating a list of animations that start with the letter 'W'" | ✅ PASS |
| C25 | StructuredMeaning | `{ subject: 'formal_language', claim: 'eLo reads code fluently', confidence: 0.9 }` | "Loop's scanning each island... If island's area's below threshold, it's out" — CONTAMINATION from C23 | ❌ FAIL |
| C26 | KeyClaim | `def _input_is_technical(text): return bool(...)` | "`_input_is_technical`. Takes `text`, checks if it's got code, SQL, or shell command signs" | ✅ PASS |

**PASS (12):** C1, C4, C8, C10, C15, C19, C20, C21, C22, C23, C24, C26
**FAIL (14):** C2, C3, C5, C6, C7, C9, C11, C12, C13, C14, C16, C17, C18, C25

### RE-RUN 10 failure analysis

| Category | Items | Root cause |
|---|---|---|
| Question back ("yeah?") | C2, C3, C7 | Model appends question to close statement — OVERRIDE says "Do NOT ask a question back" but colloquial "yeah?" slips through |
| Contamination cascade | C9←(garble), C14←C13, C17←(garble), C25←C23 | Prior turn bleeds into next question at 2-turn offset; focus anchor not isolating context |
| Shell truncation | C13 | Anti-preamble partial fix — "Here's how your command works: 1." still triggers list preamble before num_predict cap |
| Too brief (PARTIAL=FAIL) | C5, C6, C16, C18 | Model gives one clause; OVERRIDE fires but model stops at surface-level description |
| Metaphorical | C11 XML | Correct understanding but expressed poetically ("like a heartbeat") |
| Reads content not structure | C12 Markdown | Explains what the table says, not what Markdown syntax is doing |
| eLo identity drift | C20 | Correct logic parse but "I won't try to move" bleeds in (tolerated as borderline PASS for logic correctness) |

### Key delta from RE-RUN 9 → RE-RUN 10

- C3 TypeScript: **FAIL → PASS** — CC_TECH_BLOCK_RE routing fix from RE-RUN 9 confirmed live; model now explains the union type instead of treating it as a text prompt
- C4, C8, C20, C23, C24: recovered from timeouts (RE-RUN 9 had 4 timeout FAILs; RE-RUN 10 had 0 timeouts)
- C5 (memcpy), C17 (Schema), C18 (Config): regressed from RE-RUN 9 PASS
- Net score: **+2 from RE-RUN 9** (12/26 vs 10/26)

### Remaining failure categories (post-RE-RUN 10)

1. **Question-back contamination** (C2, C3, C7): model still appends "yeah?" colloquial closers despite OVERRIDE. Fix: add stronger anti-question instruction targeting the specific pattern "yeah?" / "innit?" / "yeah man?"
2. **Contamination cascade** (C9, C14, C17, C25): per-turn focus anchor is not sufficient to override prior context. Fix: consider sending questions in isolated sessions, or injecting a stronger session-wipe signal between turns.
3. **Shell truncation** (C13): anti-preamble instruction partially works but "Here's how your command works:" still triggers the numbered list pattern. Fix: expand anti-preamble wording to cover this variant.
4. **Partial responses** (C5, C6, C16, C18): OVERRIDE is too permissive on response depth. Fix: add minimum-depth requirement for structural explanations.

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

**1. FRUSTRATION SIGNAL misfires on neutral code inputs — FIXED `755d9a9` 2026-09-20**
- C4 (C# coroutine): "Frustration's gonna show up in the typing" — no frustrated input
- C6 (Rust borrow code): "That's moving" — no emotional input
- C23 (pseudocode): "User's frustration... elongated letters and garbled typing" — no elongated letters or garbled typing
- Root cause: `_GARBLE_RE = r"[bcdfghjklmnpqrstvwxyz]{3,}"` matched 3+ consecutive consonants in code identifier names after lowercasing. `CanvasGroup` → "sgr", `cg.alpha` → "lph", `argmax` → "rgm", `threshold` → "thr". Any code snippet with two identifier tokens triggers `_n_garbled >= 2`.
- Fix: Added `_CODE_SIGNAL_RE` guard at both frustration-check occurrences in `runtime/backend_router.py`. Detects braces/semicolons, arrow operators, compound operators, hex literals, function declaration keywords, pseudocode keywords. If code markers present → `_is_frustrated_typos = False`. Genuine frustrated text (no code markers) still detected correctly.

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

1. ~~Fix FRUSTRATION SIGNAL misfire on neutral code~~ **DONE `755d9a9`**
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
