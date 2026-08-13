# Regression Test — [Work Package Name]

**Work Package:** WP_[X] — [Name]
**Engineer Role:** Regression Engineer
**Date:**
**Status:** RUNNING / PASS / FAIL

---

## 1. Purpose

Confirm that WP_[X] implementation did not break behaviour established by any prior frozen phase.

---

## 2. Baseline

The following phases are frozen and define the regression baseline:

| Phase / WP | Status | Freeze Date |
|---|---|---|
| Phase 0 — Philosophy | FROZEN | |
| Phase 1 — Cognitive Foundation | FROZEN | |
| WP_B — One Brain | FROZEN / PENDING | |

---

## 3. Regression Test Suite

### 3.1 Core Conversation Behaviour

Run each exchange. Record actual output. Mark PASS / FAIL.

| Test | Input | Expected | Actual | Result |
|---|---|---|---|---|
| Identity — no first-meeting phrase | "yo" | No "nice to meet you" | | |
| Emoji response | "🙃" | Short natural reply, no explanation | | |
| Silence on empty | (empty string) | No response / guard | | |
| Farewell | "safe" | Farewell pool response | | |
| Pure greeting | "wagwan" | Greeting pool response | | |

### 3.2 One Brain Principle

| Test | Description | Expected | Result |
|---|---|---|---|
| Tool enrichment | Ask "what's in the news" | CONTEXT prepended, LLM responds, raw data NOT echoed | |
| System action | "turn up the volume" | Volume changed, one-line confirmation | |
| Emoji only | "🎵" | Natural reply, no analysis | |

### 3.3 Routing Integrity

| Test | Input | Expected Backend | Actual Backend | Result |
|---|---|---|---|---|
| Normal conversation | "what are you thinking" | openai / gemini | | |
| Anim command | "wave" | anim_cmd | | |
| Scale command | "get bigger" | scale_cmd | | |
| Invade command | "invade" | invade_cmd | | |

### 3.4 Anti-Regression Specific to This WP

List any behaviour that WP_[X] could have broken. Test it explicitly.

| Test | Description | Expected | Actual | Result |
|---|---|---|---|---|
| | | | | |

---

## 4. Long-Session Regression

Run a 15-minute conversation covering:

- Greetings, work discussion, emotional content
- Tool invocations (news, weather, vision, scale)
- Avatar commands (wave, invade)
- Farewells

Record observations:

| Observation | Expected | Actual | Issue? |
|---|---|---|---|
| Response length | Short — conversational | | |
| Project anchoring | Only when relevant | | |
| Self-reference | Never "the system" | | |
| Context echoing | Never raw CONTEXT block | | |

---

## 5. Result

| Category | Result |
|---|---|
| Core conversation | PASS / FAIL |
| One Brain | PASS / FAIL |
| Routing | PASS / FAIL |
| WP-specific | PASS / FAIL |
| Long session | PASS / FAIL |

**Overall regression:** PASS / FAIL

**Regression Engineer notes:**

---

## 6. Failures

If any test failed, list here. Do not proceed to Freeze until all failures are resolved or explicitly deferred with documented risk.

| Test | Failure Description | Fix Required | Deferred? |
|---|---|---|---|
| | | | |
