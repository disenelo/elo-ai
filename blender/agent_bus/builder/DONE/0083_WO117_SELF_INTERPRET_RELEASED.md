# 0083 — WO-117 SELF-INTERPRET · 🟢 RELEASED. Its dependencies were already real.

**WO:** WO-117 · **Seat:** builder · **Priority:** 🔴 P0
**Reserved?** no
**LAYER:** `[VERIFIED]` — grepped 2026-08-21, not read from the board.

---

## 0 · Why this card exists

`WO-117` sat `⛓ BLOCKED on 21·23·24` for weeks. **All three dependencies are wired and exercised.**
The board text was stale and the Architect reported the stale text back to David twice.

🔴 **David, 2026-08-21:** *"I saw this was the case (8 hours ago)"* · *"built-never-wired"* ×9.
**He was correcting a status I never verified. That is the fault this card closes.**

| dep | board said | 🟢 truth on disk, 2026-08-21 |
|---|---|---|
| **21** REFLECT | never writes back | `last_reflection_lesson` is a real `EloSelfState` field (`elo_self_model.py:174`), loaded at `:218`, written every turn (`:317`) |
| **23** HISTORY | `append_autobiography` **zero callers**, file **doesn't exist** | **3 production callers** — `server.py:2942 · 3077 · 3168`. All pass the provenance gate: `verified=True`, `source="body_ack"`, `episode_ref` set. **`self/journals/autobiography.jsonl` exists with 5 verified entries.** |
| **24** SELF-OBSERVE | `record_behaviour`+`update_habits` **zero callers**, inputs permanently empty | **4 production callers** — `server.py:2930 · 3071 · 3159 · 4456`. Live `elo_self_state.json`: `recent_behavior = {reflect:105, answer:54, celebrate:38, build:12, sit:5, ground:5, witness:1}`; `lifetime_threads` populated. |

**Nothing is blocking WO-117. Build it.**

---

## 1 · What SELF-INTERPRET is

Row 25. eLo reads **his own accumulated record** and says something true about himself that
nobody wrote into him. From the card: *"they don't get built, they become true when the layers
beneath them work."* The layers now work — so this is assembly, not invention.

**Inputs, all live and all verified:**
- `state.recent_behavior` — what he actually does, by CAL verb
- `state.lifetime_threads` — what he keeps returning to
- `self/journals/autobiography.jsonl` — body-ACK'd lived events, provenance-gated
- `state.last_reflection_lesson` — the lesson from the last reflection cycle
- `identity_meaning.derive_tendencies(state)` — already exists (`identity_meaning.py:53`)

---

## 2 · The rule that governs the output — 🔴 read before writing a line

**`ADR-Exec-005 D1`: language alone is never evidence.** A self-interpretation is a **claim about
eLo**, so it is subject to the same gate as any other capability claim.

- An interpretation may only cite counts that exist in the store. **No rounding up, no "often" without a number behind it.**
- 🔴 **It must be falsifiable.** `reflect:105` vs `answer:54` supports *"I reflect about twice as
  often as I answer."* It does not support *"I am a reflective person."*
- **Never create identity facts** — `CT4V-03`, CA ruling: *"Narrative must never create identity facts."*
  SELF-INTERPRET reads the record. It does not write to `EloSelfState`.
- David, 2026-08-21: *"learns and **asses** not adopts … and there is a reason to why."*
  **Every interpretation carries the numbers it came from.** An interpretation with no traceable
  source is a personality trait someone invented.

---

## 3 · Wiring (required — a card without this block is rejected)

- **caller:** `runtime/spine/spine.py`, after the self-model refresh, alongside the Learning Faculty consult
- **trigger:** a real turn where `recent_behavior` is non-empty
- **observable:** `plan.self_interpretation` — non-empty, with a `derived_from` list naming the exact counts

---

## 4 · Test — `tests/test_wo117_self_interpret.py`, RED when disconnected

1. Empty `recent_behavior` + empty autobiography ⇒ **no interpretation.** Silence, not a guess.
2. Real live state ⇒ interpretation is non-empty and **every number in it appears in the store.**
3. 🔴 **Disconnection check:** stub the store to zeros ⇒ the interpretation **disappears.** If it
   survives, it was hardcoded and the test is worthless.
4. An interpretation citing a count that is not in the store ⇒ **rejected, not emitted.**
5. `EloSelfState` is **byte-identical** before and after interpretation (`CT4V-03` — reads only).

## 5 · Done when
built · **wired** (spine calls it) · **exercised** (ran on a real turn with the live store) ·
**falsifiable** (test 3 goes RED when the wire is cut). Nothing short of all four.

## 6 · Result (seat fills this in)
- commit:
- test:
- the interpretation eLo produced on a real turn, verbatim:
- the counts it cited:
