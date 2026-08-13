# WP_G — Executive Faculty Audit

**Status:** PENDING
**Priority:** CRITICAL
**Depends On:** WP_C, WP_D, WP_E, WP_F (all faculty inputs audited)
**Architecture Reference:** `docs/architecture/09_executive_faculty.md`, `docs/architecture/06_conversation_context_matrix.md`, `docs/architecture/08_capability_faculty.md`

---

## Purpose

Audit the Executive Faculty — the sole decision-maker in eLo OS. This is the most sensitive audit. The Executive Faculty is frozen (FREEZE_V1_LOCK). The audit reviews its inputs, outputs, and the validity of its decisions — not its implementation.

**CRITICAL: `runtime/executive.py` and `prompts/` are never modified. The audit observes and documents. It does not change.**

---

## Objective

At the end of WP_G:
- Every input path into the Executive is documented and validated
- Every output field of the Executive's decision is validated
- The Executive's decisions are confirmed to be consistent with eLo's personality
- Gaps in Executive input (things it should know but doesn't) are documented for future work
- The audit is frozen

---

## Existing Architecture Review Required

**Files to audit (read-only):**

| File | Role |
|---|---|
| `runtime/executive.py` | FROZEN — read only. The decision engine. |
| `prompts/` | FROZEN — read only. Personality specification. |
| `runtime/router/context_matrix.py` | Conversation Context Matrix |
| `runtime/router/agent_router.py` | Agent selection from Executive decision |
| `docs/architecture/09_executive_faculty.md` | Architecture specification |
| `docs/architecture/06_conversation_context_matrix.md` | CCM specification |
| `docs/architecture/08_capability_faculty.md` | Capability registry |

---

## What the Executive Receives

Trace every input into `exec_decide()`:

| Input | Source | Status |
|---|---|---|
| attention_model | Attention Faculty | Active |
| user_input | Raw user message | Active |
| loop_detected | Loop guard | Active |
| _exec_decision (g_ctx) | All faculty outputs assembled | Active |

---

## What the Executive Produces

The Executive produces one `exec_decision` dict per turn:

| Output Field | Purpose | Used By |
|---|---|---|
| action | CAL action (reflect, answer, celebrate, etc.) | Spine → prompt_builder |
| tone | DIRECT, EMPATHETIC, etc. | prompt_builder |
| max_sentences | Response length cap | backend_router normalise() |
| response_goal | answer, stabilise, connect, etc. | prompt_builder |
| valence | neutral, positive, negative | Spine |
| momentum | stable, building, declining | Spine |
| mode | CONVERSATIONAL, BUILD, etc. | prompt_builder |
| register | SOUTH_LDN_MODE etc. | Spine |
| cal_reason | Why this action was chosen | Debug |

---

## Audit Focus

Since the Executive is frozen, the audit focuses on:

1. **Input completeness** — Is the Executive receiving everything it needs? Are any faculty outputs missing?
2. **Output correctness** — Are the Executive's decisions appropriate for the test inputs?
3. **max_sentences** — Is the Executive's sentence cap being respected downstream?
4. **Action accuracy** — Does "reflect" produce reflection? Does "celebrate" produce celebration?
5. **g_ctx contamination** — Is anything in g_ctx that should not be there?

---

## Known Issues

1. **max_sentences not holding** — Debug transcript showed eLo giving paragraph-length responses. The Executive may be setting max_sentences correctly but the normalise() function or the LLM may not be respecting it. Investigate the path from max_sentences → normalise().

2. **"OS/book/robot" anchoring** — Executive may be getting studio brief context that over-anchors responses to the project triplet. Mitigated with [ANTI-ANCHOR] injection. Validate effectiveness.

---

## Freeze Criteria

- [ ] All inputs to Executive traced and documented
- [ ] All outputs validated against expected behaviour
- [ ] max_sentences path traced and validated
- [ ] Action accuracy validated (10 inputs per CAL action)
- [ ] One Brain compliance confirmed (Executive decides, nothing else does)
- [ ] Audit document frozen (no code changes — audit only)
