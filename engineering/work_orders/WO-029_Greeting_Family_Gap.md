---
id: WO-029
title: "eLo greeting gap — 'you all good / you're all good / all good' route to CONNECT/REFLECT instead of a warm reply"
owner_seat: SEAT-ENG-001 (Builder)
occupant: Builder (Python)
priority: P1
reason: "Live debug (David 2026-08-02): 'you all good?' got associative replies ('One feeds the other', 'I'd hold onto that'). Routing classifies it 'conversation' correctly, but the greeting set _HOW_ARE_YOU has 'you good' NOT 'you all good' — so this phrasing falls through to CAL → CONNECT/REFLECT. Uncovered gap, NOT a WO-020 regression (Seam A intact)."
review_required: L1 → L3 (David feels it in real use)
risk: low (greeting-phrase coverage; no logic change)
status: READY
created: 2026-08-02
relates: WO-020 (routing drift — same class, this is the greeting-family gap it didn't cover)
---

# WO-029 — greeting family gap ("you all good?")

## Diagnosis (grounded)
- `runtime/executive.py` `_HOW_ARE_YOU` set matches `you good`, `you alright`, `you ok`, `you calm` — but
  **NOT** `you all good`, `you're all good`, `are you all good`, or a bare `all good` used as a check-in.
- "Are you all good?" → routing = conversation (correct) → greeting-detector misses → CAL fires
  CONNECT/REFLECT/WITNESS → associative one-liner. Same for "you're all good?".
- `executive.py` is FROZEN (kernel) — WO-020 used a **server.py Seam A override** for this exact reason.

## Fix (respect the frozen kernel — mirror WO-020's approach)
Add the missing greeting family so it routes to a **warm conversational ANSWER** ("Yeah, I'm good — you?"),
NOT CONNECT/REFLECT. Do it via the seam that doesn't touch the frozen kernel:
- Preferred: extend the **server.py greeting/Seam-A override** to catch the `all good` family →
  force a warm greeting reply (same mechanism that overrides plain imperatives).
- If a scoped `executive.py` data-only unlock is cleaner (adding strings to `_HOW_ARE_YOU`), request it
  from David (like D-K) — one list, revert-safe.

Phrases to cover (+ no-apostrophe + typo variants): `you all good`, `youre all good`, `you're all good`,
`are you all good`, `is everything good`, `all good?` (as a whole-input check-in), `you all g`,
`we all good`, `everything all good`.

## Guard against false positives
- Only treat as a greeting when it's a **short whole-input social check-in** — do NOT swallow "are you all
  good with the plan?" or "is the build all good?" (those carry a real object → answer normally).

## Acceptance
1. "you all good?", "you're all good?", "are you all good?" → warm conversational reply, not associative.
2. "is the build all good?" / "you all good with X?" still route to a real answer (no over-match).
3. `tests/test_wo029_greeting_gap.py` (≥4 cases incl. the false-positive guards); frozen kernel green.
4. **py_compile clean before commit** (completion protocol step 0). David feels it live → DONE.

## Notes
- Fold these cases into the **WO-027 behaviour golden-set** so greetings can't regress again.
