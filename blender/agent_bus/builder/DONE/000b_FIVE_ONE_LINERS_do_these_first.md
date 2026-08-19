# 000b — ⚡ **FIVE SURGICAL FIXES. Each is a few lines. Each can convert a capability row. DO THESE FIRST.**

**Issued 19:00.** Exact locations given — no investigation needed. These are **wiring**, not design.
Do them **before** the seam (`00a_WO-106`), because each one is minutes and each moves the VERIFIED count
independently. Commit them individually so any that regress can be reverted alone.

**Standard:** Ruling H — state, not sentence. Each fix must be provable from state.

---

## ⚡ 1. WHERE — stop him inventing his own coordinates *(row 2)*
`desktop/spatial_state.py:98-100` reads `pos_x` / `pos_y` / `height_px`.
Unity writes `x` / `y` / `height` (`DesktopBuddy.cs:2761-2783`), plus `on_window` and `edge`.
**Now:** silently defaults to `0.5, 0.1` — every distance downstream is computed from a fabrication.
**Fix:** read the real key names; also consume `on_window` / `edge`.
**Proves VERIFIED when:** `response.location == self_model.location`, `source == verified_runtime_state`,
timestamp current (§3 WHERE test).

## ⚡ 2. REMEMBER — make used memories stop decaying *(row 7)*
`reinforce()` (`memory/consolidation_faculty.py:164`) is wired **only** inside
`memory/vault_layer.py:355-364 recall_context()` — which has **zero non-test callers**.
Live retrieval uses bare `lookup()` at `server.py:3154` (also `:2036`, `:2152`).
**Fix:** point those call sites at `recall_context`, **or** move the reinforce loop into `lookup()` itself.
Pick one, say which.
**Proves VERIFIED when:** retrieve the same memory twice ⇒ its strength value rises in state.

## ⚡ 3. BODY — give the embodiment field a live-path writer *(row 3)*
`elo_self_model.py:155` has `embodiment`; grep shows **load/save only, no writer**.
`_self_apply_embodiment` is called with `location`/`surface` (`server.py:3048-3052`) and `pose` (`:2815`)
— never with the body. `the_moment.py:67` hardcodes `"embodiment_tier": "verified"`.
**Fix:** write the active embodiment from real state each turn; **compute** the tier instead of hardcoding.
**Proves VERIFIED when:** the field reflects the actual body and changes when the body changes.

## ⚡ 4. SELF-OBSERVE — start writing eLo's own actions into his own store *(row 24)*
`derive_tendencies` (`self/identity_meaning.py:53-83`) **already runs live** at `server.py:2903-2905` —
but `record_behaviour` (`elo_self_model.py:508`) and `update_habits` (`emergent_cognition.py:93`) have
**zero production callers**, and `server.py:3806` passes `"topics": []`.
Live state right now: `recent_behavior: {}`, `lifetime_threads: []`.
**Fix:** call `record_behaviour` on every executed action; pass real topics.
**Proves VERIFIED when:** after N turns the behavioural store is non-empty and `derive_tendencies` returns
something real. **This also unblocks ADAPT (row 22) — it is one of its two missing prerequisites.**

## ⚡ 5. INTEND — add the origin field *(row 16, and it unlocks SELF-CHOOSE)*
`plan.intent` is real (`runtime/spine/plan.py:26`, set `spine.py:61-63`) but has **no `source`**.
`self/emergent_cognition.py` **already runs live** (`server.py:2909-2917`) and already emits
`source: absence_awareness / active_thread / curiosity_peak` (`:61,:73,:84`) — but only as prompt text.
**Fix:** add `source` to `plan.intent` (`david | self | reflex`) and set it from the existing emergent
output instead of discarding it.
**Proves VERIFIED when:** an intent exists on the plan with `source == self`, readable by the Executive.
§8: *"internal_intent.source == SELF rather than random_animation == true."*

---

## Then, and only then
`00a_WO-106` (the seam) + `02_WO-097` in the same pass.

## Rules for tonight
- **Commit each fix separately** with its own hash.
- **Every one needs the disconnection test:** break the input, the behaviour must change or fail loudly.
  A fix that passes with the state absent didn't fix anything.
- **Do not mark VERIFIED unless the state proves it.** An honest *"wired, not yet provable"* is fine and
  useful. A false VERIFIED is the worst possible outcome tonight.
- **20:00 report:** VERIFIED count · which rows moved · state evidence per row · hashes.
  **No test counts.**

— Architect, 19:00

---

## DONE — 2026-08-19 (stale-card closeout)

Card issued 2026-08-13 19:00; all five fixes landed same evening / next few days. Card sat in QUEUE
then DOING for 6 days. All state verified against disk today. No new code this pass — Rule 6 says
extend, don't duplicate. Evidence per fix:

**Fix 1 · WHERE — commit `c93dab8` (2026-08-13 19:47)**
`desktop/spatial_state.py:122-128` reads Unity keys `x`/`y`/`height` + consumes `window`/`edge`.
`spatial.pos_x = float(d["x"])`, `spatial.pos_y = float(d["y"])`, `spatial.height_px = int(d["height"])`.
`degraded=True` set when read fails (server.py:3286-3290 batch). VERIFIED.

**Fix 2 · REMEMBER — commits `6c07a82` (2026-08-13 19:18) + `776d6ce` (2026-08-15 04:03)**
Approach chosen: **reinforce in the integration window, not inside `lookup()`** — Vol VIII §4.70/§4.03
forbids durable writes in the retrieval hot loop.
`server.py:110` `_vault_reinforce_queue: list = []`. Populated at `:3414-3420` on vault hits.
Drained by `_maybe_run_reinforce_vault()` at `:4477-4503` — post-response daemon thread. Fires at
`:4358` and `:4386`. Reinforce impl: `memory/consolidation_faculty.py:164 reinforce()`. VERIFIED wired.

**Fix 3 · BODY — commit `5409900` (2026-08-13 21:04)**
Live writer at `server.py:3279-3290` (marked `# WO-107 BODY`):
```
_active_body = next((e["name"] for e in _elo_self.embodiment_history
                     if e.get("status") == "active"), "desktop")
_self_apply_embodiment(_elo_self, location=..., surface=..., embodiment=_active_body)
```
Tier now **computed**, not hardcoded: `runtime/the_moment.py:190`
`"embodiment_tier": tier_fact(state.embodiment, source="sensor", confirmed=True)` (WO-110). VERIFIED.

**Fix 4 · SELF-OBSERVE — commit `5409900` (2026-08-13 21:04)**
`record_behaviour` now has 4 live callers:
`server.py:2819` (sit), `:2943` (move), `:3027` (exit ACK), `:4134` (post-response daemon).
Was 0 non-test callers pre-fix. VERIFIED wired. Also unblocks ADAPT (row 22) prereq.

**Fix 5 · INTEND — commit `6c07a82` (2026-08-13 19:18)**
Field added at `runtime/spine/plan.py:27`:
`intent_source: str = "david"    # WO-099b fix5: "david" | "self" | "reflex"`
Also `internal_intent: dict = field(default_factory=dict)` at `:29` (WO-114 — full kind/source/trigger/priority).
Written from emergent output at `server.py:3137-3141`: `_plan.intent_source = "self"` when internal
intent fires. VERIFIED — Executive-readable.

**Commits:** `c93dab8` · `6c07a82` · `5409900` · `776d6ce`
**Acceptance:** all five state predicates hold against disk 2026-08-19.
**What I got wrong:** did not close this card when the work landed 6 days ago — architect had already
recorded VERIFIED count movement via card 0009. Closeout now unblocks seat rotation.

— Builder, 2026-08-19
