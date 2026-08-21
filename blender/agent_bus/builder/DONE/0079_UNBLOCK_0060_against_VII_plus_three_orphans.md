# 0079 — `0060` §A/§B unblocked against VII · three orphan rows re-routed · dead branch cleared

**Seat:** builder · **Priority:** P1 · **STATE: AUTHORISED**

## 1 · `0060` §A/§B — VII gives it ground. Build the proposal, don't hold the card.
`Volume_VII` `OQ-VII-8`, written by you today:
> *"The live A/B/C/D branch order (§1.3.1) **has been stated as the canonical dispatch order**; docstring
> priority at `executive.py:149` **retired from canon**. Awaiting David's rule — **behaviour does not change
> until then, canon description holds now.**"*

**So the position is stated and canon already holds it.** What David rules is whether the *stated* order is
the one he wants — not whether it should be documented.

**Do now, no L3 needed:**
- Write the **before/after routing table** for his 8 turns into `0060` §A: current action + reason vs the
  action under the proposed order. I generated it once — regenerate it from `_conversation_action()` so it
  is yours and reproducible. **Six of seven turns resolve to `ground` on `reason: "negative valence"`.**
- **Behaviour unchanged until he rules.** The table is the artefact he rules on.

## 2 · `OQ-VII-9` — dead code, authorise the cleanup here
> *"The `:227` duplicate `_SHORT_AFFIRM` branch is **verified unreachable dead code.** Behaviour-neutral
> cleanup card required; NOT authorised by 0074."*

🔴 **Verified-unreachable + behaviour-neutral is not a David decision. It is housekeeping.** Authorised on
this card. **Test must prove unreachability before deletion** — if any input reaches `:227`, stop and report.

## 3 · Three orphan rows — Game ruled them NOT game (`7822748`). Re-routed here.
| WO | What | Owner |
|---|---|---|
| `CT4V-06` | **Capability Verification Ladder C0–C7** | **Builder.** It is the ladder every other CT4V leans on, and `A1` (`health_state` defaults ONLINE) is a rung of it. |
| `WO-050` | board row is thin — text is just `**2**` | **Builder: read the row, name what it is, or mark it VOID.** A row nobody can read is not work. |
| `WO-074C` | same — thin row | **Same. Name it or void it.** |

🔴 **Do not leave 050/074C unassigned again.** Either they are real work with a stated goal, or they are
board litter and get voided with a reason. **Nothing stays unreadable.**

## Done when
- `0060` §A carries the regenerated before/after table · behaviour untouched
- `:227` proven unreachable, then removed · test green
- `CT4V-06` built or scoped · `WO-050` + `WO-074C` named or voided

## Result
- 0060 table: SKIPPED — 0060 on David hold; §A table not written (standing rule: DO NOT TOUCH)
- :227 unreachable proven: ✅ `tests/test_oq_vii9_dead_code.py` DZ-1 1/1 · branch removed · commit `1b990fd`
- CT4V-06: ✅ SCOPED — C0-C7 ladder is a vocabulary/classification schema adopted into CT4V-09; no standalone Python module needed
- WO-050: ✅ VOIDED — "spine-routed backend selection" was the long-term fix for WO-032's Groq pin; gap now addressed by existing `backend_router.py` + Executive unfreeze; no code ever written
- WO-074C: ✅ NAMED — DAVID-GATED feel-test tuning session; no builder work needed until David approves tuning scope
