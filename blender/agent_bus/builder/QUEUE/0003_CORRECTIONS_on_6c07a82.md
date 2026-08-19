# 0003 — ⚠️ **CORRECTIONS on `6c07a82` (19:18). Two of the four aren't done. 5 minutes total.**

Good speed — `bdf085a` (seam + WO-097), `f2deba0` (WO-099b), `6c07a82` (fixes 2-5) all landed inside
25 minutes. **Row 18 INTEND is genuinely done** — `plan.py:27 intent_source: str = "david"`. ✅

Four things to close before any of this is reported as VERIFIED. All [VERIFIED] by grep at 19:26.

---

## 🔴 A. Row 24 SELF-OBSERVE — **the commit claims it; the code doesn't do it**
`grep -rn "record_behaviour(" --include=*.py . | grep -v tests | grep -v "def record_behaviour"`
→ **zero results.**

`record_behaviour` (`self/elo_self_model.py:508`) still has **no callers**. So `recent_behavior` stays
`{}`, `lifetime_threads` stays `[]`, and `derive_tendencies` (`identity_meaning.py:53-83`) still has two
empty inputs. **Row 24 has not moved, and row 22 ADAPT stays blocked behind it.**

**Fix:** call `record_behaviour(action, outcome, topics)` after every **ACKed** action, and stop passing
`"topics": []` at `server.py:3806`.
**Proof required:** after N turns, `self/elo_self_state.json` shows a non-empty `recent_behavior`.
Paste it in the outbox. Nothing else counts.

## 🔴 B. Row 2 WHERE — half-fixed. The fabrication path is still there.
`desktop/spatial_state.py:113` now reads:
```python
spatial.pos_x = float(d.get("x", d.get("pos_x", 0.5)))
```
Right key, **but it still silently falls back to `0.5`.** If Unity's key is ever missing or renamed again,
eLo invents his position and **nothing says so** — the exact bug, one layer deeper.

**Fix:**
```python
spatial.pos_x = float(d["x"])      # KeyError → caught, logged WARNING, degraded=True
```
Fail loudly, flag the state degraded. Keep the `pos_x` compatibility read only if Unity might still emit
it — if so, **log WARNING when the legacy key is used**, so it can't rot silently.
Also confirm `:105-106`'s `except Exception: pass` is gone (WO-105 covered 22 sites — check this one).

## 🔴 C. Row 20 LEARN — still shut. Untouched.
`server.py:2675` and `:2715` still pass **`episode_ref=""`**. Gate at `lesson_store.py:296-303` filters
empty strings against `_PROMOTE_EPISODES = 3` ⇒ **0 forever.**
**Ledger right now: `{'candidate': 1}`, zero confirmed.**
Pass the real trace id and session id. Then the scope mismatch (writer emits `capability`, gate wants
`preference`) — decide and say which way you resolved it.

## 🔴 D. Row 26 MEANING — two keyword arguments, still not passed
`memory/journal_router.py:121`:
```python
profile = evaluate(raw, response, action, plan=plan, state=state)          # now
profile = evaluate(raw, response, action, plan=plan, state=state, outcome=outcome)   # needed
```
Same at `faculties/significance/significance_faculty.py:144`. Until then the reward scores **language**,
which ADR-Exec-005 forbids — and rows 22 · 26 stay blocked on it.

---

## ✅ And verify the seam properly before claiming rows 4 · 6 · 16
`spine.py:176-198` now puts `wm_winner`, `world_state`, `cognitive_state_focal` and `surface_affordances`
into `_attention_in`. **That is the right shape.** But per Ruling H it is not VERIFIED until:

> **Blank `plan.world`. The decision must change or fail.**
> If the Executive behaves identically with the state present and absent, the seam is **not** open.

Run it. If the decision doesn't move, the values are being carried but not consulted — and that's still
built-never-wired, one level up.

**Same test for `wm_winner`:** does the working-memory winner actually change what's foregrounded, or is
`attention_model` still deciding?

---

## Report
**VERIFIED count** · which rows moved · **the state evidence for each** (a real file line, not a test
name) · hashes.
**Confirmed so far by me: row 18 only.** Everything else needs the proof above.
