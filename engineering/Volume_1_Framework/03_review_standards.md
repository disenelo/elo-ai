# Volume 1 — Review Standards

Every review in the Engineering Programme — Architecture Review, Current State Audit, Conversation Tests, Stress Tests — follows these standards.

---

## The Six Architecture Constants (Check Every Review)

Every review document must explicitly check all six. Not "assumed compliant." Explicitly stated.

1. **One Brain** — does this phase add any decision-making path that bypasses the Executive?
2. **One Executive** — does this phase modify `runtime/executive.py`? (It must not.)
3. **Faculties Observe** — does every new faculty component produce observations, not decisions?
4. **FREEZE_V1_LOCK** — does this phase touch `runtime/executive.py` or `prompts/`? (It must not.)
5. **Silence is Valid** — can every new component produce nothing? Is nothing handled gracefully?
6. **Evidence Gates Expansion** — has the prior phase passed validation before this one begins implementation?

If any constant is violated, the review fails. No exceptions.

---

## Honesty Markers

Use these consistently. Ambiguity is not allowed in review documents.

| Marker | Meaning |
|---|---|
| ✅ | Verified working. I ran it. I saw the output. |
| ⚠️ | Exists but not tested. Works in theory, unverified in practice. |
| 🔴 | Not implemented, broken, or known to fail. |
| 🔒 | Frozen. This component must not be modified. |
| 📐 | In design phase. Architecture defined, implementation not started. |
| ⏳ | Awaiting external dependency (runtime test, user session, hardware). |

**Rule:** If you didn't run it, it's ⚠️ at best. Don't mark ✅ for something you only read.

---

## What a Good Architecture Review Looks Like

A good architecture review:
- Cites specific files and line numbers
- States what the component does and what it does not do
- Identifies the boundaries of the component (what it touches, what it doesn't)
- Asks "what happens when this fails?" for every new component
- Asks "does this duplicate anything that already exists?"
- Recommends accept / revise / reject with reasoning

A poor architecture review:
- Uses phrases like "should work" or "probably handles it"
- Describes what the code is supposed to do without verifying it
- Doesn't check the Architecture Constants
- Approves something because it looks right, not because it was tested

---

## What a Good Conversation Test Looks Like

A conversation test has:
- A specific scenario (what David says, what context exists)
- An expected eLo response (specific behaviour, not "something reasonable")
- An actual eLo response (what actually happened)
- A pass/fail judgment with reasoning

A poor conversation test:
- "Asked eLo about the robot. It answered well." (No scenario, no expectation, no evidence.)
- "eLo seemed to understand." (Seeming is not evidence.)

---

## Regression Rule

When a new phase introduces a regression against a prior phase's documented behaviour:

1. The regression is documented immediately (what broke, what was expected)
2. The new phase's freeze is blocked until the regression is resolved
3. The fix is tested against both the prior and current phase test suites
4. The fix is committed before freeze is re-attempted

**A regression that slips through freeze becomes an architectural debt. It compounds.**

---

## Gap Analysis Rule

Every gap in the analysis must resolve to one of:

- **A deliverable in this phase** — "this will be built in Step 05"
- **A dependency in a later phase** — "this is Phase 3.5 scope, not Phase 3"
- **A known limitation** — "this is out of scope for eLo OS; documented here"
- **A risk** — "this may cause problems; mitigation is X"

A gap described as "probably fine" or "should be OK" is not resolved. It's hidden.

---

## The Presence Test (Phase 2.5 Onward)

Starting from Phase 2.5, every phase that touches presence, avatar, or embodiment adds:

> **Does this feel like someone sharing the space?**

This is not a technical question. It is observed during a real work session with Desktop Buddy visible. The answer is one of:

- Yes, distinctly
- Kind of, sometimes
- Not yet
- No

Anything below "Kind of, sometimes" is a finding that the phase must address before freeze.
