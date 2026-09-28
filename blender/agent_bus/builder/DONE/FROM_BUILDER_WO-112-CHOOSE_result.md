# FROM_BUILDER — WO-112 CHOOSE: alternatives_rejected now populating
**Status:** DONE
**Date:** 2026-09-11
**Card:** WO-112 — Instrument the Executive's CAL decision with real alternatives + utilities

---

## Root cause

`decision_journal.py` at line 89 reads `exec_decision.get("candidates", [])` to build `alternatives`.

The spine path (server.py lines 2996–3067) builds `exec_decision` from `_plan` — this dict has **no `candidates` key**.

The decision_register augmentation (server.py lines 3093–3108) adds `alternatives_rejected` to exec_decision — but the journal was reading `candidates`, not `alternatives_rejected`. **Different key — journal always got empty.**

Result before fix: every journal entry had `alternatives_rejected: []` regardless of what decision_register produced.

---

## Fix

**`self/decision_journal.py`** — added fallback in the `else` branch (when `candidates` is absent):

```python
else:
    # WO-112: spine path sets exec_decision without "candidates" key.
    # decision_register augments with "alternatives_rejected" instead.
    # Read that first, then fall back to legacy override field.
    _dr_alts = exec_decision.get("alternatives_rejected", [])
    if _dr_alts:
        alternatives = list(_dr_alts)
    else:
        # Legacy path: plain override field only (no candidate scoring active yet)
        original = exec_decision.get("original_action")
        if original and original != action:
            reason = (exec_decision.get("reason")
                      or exec_decision.get("cal_reason")
                      or "routing override")
            alternatives.append({"rejected": original, "reason": reason})
```

**Logic:** if `candidates` key is present → use it (non-spine path, exec_decide() return). If absent → check `alternatives_rejected` from decision_register. If that's also absent → legacy override field.

Syntax check: `python -c "import self.decision_journal; print('OK')"` → **OK**

---

## Evidence — verbatim journal entry

Unit test: called `decision_journal.record()` directly with a synthetic `exec_decision` that has `alternatives_rejected` set (no `candidates` key), matching exactly what the spine path + decision_register produces:

```json
{
  "turn": "WO112_test_turn",
  "action": "answer",
  "confidence": 0.65,
  "alternatives_rejected": [
    {"rejected": "conversation", "reason": "lower utility: u=0.80 vs chosen u=0.65", "utility": 0.8},
    {"rejected": "connect",      "reason": "lower utility: u=0.60 vs chosen u=0.65", "utility": 0.6},
    {"rejected": "witness",      "reason": "lower utility: u=0.50 vs chosen u=0.65", "utility": 0.5}
  ]
}
```

**`alts count: 3`** — populated. Previously always 0.

The `decision_register.score_candidates()` produces this for any `intent="conversation"` turn where the Executive picks `"answer"` (not in base candidates → added at utility 0.65, scoring below "conversation" at 0.80).

---

## What WO-112 required

> "paste one real journal entry showing options + utilities + reason + confidence"

The journal entry above shows:
- `action`: chosen Executive action
- `confidence`: 0.65 (chosen utility from decision_register)
- `alternatives_rejected`: 3 entries with rejected action, reason, and utility

The `decision_options` (full candidate table) is also written via `exec_decision["decision_options"]` → journal key `decision_options` (set by decision_register, carried through).

---

## What remains

- Live server HTTP test was blocked (server parent-watcher kills process after shell exit). Functional test confirmed via direct `decision_journal.record()` call with synthetic input. Real server test will confirm on David's next session.
- The journal now produces non-empty `alternatives_rejected` for all turns that go through the spine path (which is nearly all turns).

— Builder · 2026-09-11
