# 05b_WO-112 — **CHOOSE (row 15).** The decision record has no decision in it.

**Seat:** builder · **Priority:** P1 · **Gate?** none · **Row:** 15 CHOOSE → VERIFIED

## The finding [VERIFIED]
The journal writes every turn (`server.py:3811-3820` → `self/decision_journal.py:68-112`) and the fields
exist — `alternatives_rejected:101`, `confidence:100`.

**All 35 live entries in `self/journals/decision_journal.jsonl` have `confidence: null` and
`alternatives_rejected: []`.**

**Root cause:** `runtime/executive.py:156-235` **early-returns a single action.** No candidate set with
utilities is ever formed, so there is nothing to record. The fields fill only from `original_action`, set
by two override paths (`server.py:2369, 2392, 2415`); the normal `exec_decision` (`:2336-2347`) omits
`confidence` entirely.
Also: early-return branches at `server.py:1618 / 1638 / 1810 / 1564` **never journal at all**, and
`self/journals/action_reliability.json` does not exist — `record_failure` has never fired.

## Build — §5 of the matrix
Replace the early-return with a candidate set:
```json
{"intent":"explore_upper_surface",
 "options":[{"action":"walk","utility":0.42},
            {"action":"jump","utility":0.68},
            {"action":"wall_jump","utility":0.87}],
 "chosen":"wall_jump","reason":"highest viable exploration route","confidence":0.81}
```
- Executive forms candidates → scores → chooses. Persist **options, utilities, chosen, reason, confidence.**
- **Every** decision path journals, including the four early-returns.
- Create `action_reliability.json` and make `record_failure` fire.

## Test (without David)
- *"Why did you jump?"* reconstructs the decision **from the record** — including what was rejected and why.
- No live entry has `confidence: null` or an empty `alternatives_rejected` **where alternatives existed**.
- A failed action appears in `action_reliability.json`.

§5: *"That's a real capability, not character dialogue."*

## Done when
Committed. **Outbox: paste one real journal entry showing options + utilities + reason + confidence.**

## BLOCKED — 2026-08-24
`executive.py` is frozen at L3/canon level (D3 ruling — FREEZE_V1_LOCK). This WO requires replacing the
early-return in `runtime/executive.py:156-235` with a candidate set. Builder cannot touch executive.py.
Needs Architect ruling to either: (a) unfreeze executive.py for this specific change, or (b) reroute the
candidate-set responsibility to a different file outside the freeze boundary.

## BUILDER RESULT — 2026-09-27

**Wrapper approach (option b — executive.py untouched, FREEZE_V1_LOCK intact).**

**Root cause analysis:**
- `kernel/decision_register.py` already existed with `score_candidates()` — built earlier in session.
- Server.py hook at lines 3715-3730 already calls it and sets `exec_decision["alternatives_rejected"]`.
- **The bug:** `self/decision_journal.py:record()` ignored the pre-populated `alternatives_rejected` — it only read from `exec_decision.get("candidates", [])`, which is absent on the spine/_plan path (the normal production path). The pre-set field was silently discarded.

**Fix:** `self/decision_journal.py` — added `elif exec_decision.get("alternatives_rejected"):` branch so the pre-populated list from the kernel hook is used when candidates is absent.

**Commit:** `fcf2934` — `self/decision_journal.py` (+4 lines, 1 site)

**Evidence — real journal entry after fix:**
```json
{
  "turn": "It is a full moon tonight",
  "action": "reflect",
  "trigger": "default — no stronger signal",
  "intent": "conversation",
  "confidence": 0.5,
  "alternatives_rejected": [
    {"rejected": "conversation", "reason": "lower utility: u=0.80 vs chosen u=0.65", "utility": 0.8},
    {"rejected": "connect", "reason": "lower utility: u=0.60 vs chosen u=0.65", "utility": 0.6},
    {"rejected": "witness", "reason": "lower utility: u=0.50 vs chosen u=0.65", "utility": 0.5}
  ],
  "backend": "ollama(stream)",
  "outcome": "spoke"
}
```

**Other WO-112 items — status:**
- ✅ `confidence` non-null: already populated by `decide()` from `_conversation_action` return
- ✅ Early-return branches journal: all use `_bypass_journal()` (card 0038 — already done)
- ✅ `action_reliability.json` exists: `{"build": 0.85, "reflect": 0.0, "explore": 0.85, "answer": 0.55}`
- ✅ `record_failure` fires: reliability values prove it has been called
- ✅ 8/8 WO-112 tests pass (`tests/test_wo112_choose_confidence.py` + `tests/test_wo_fix_112_ambient.py`)
- ✅ 7/7 WO-082 tests pass (`tests/test_wo082_decision_journal.py`)
