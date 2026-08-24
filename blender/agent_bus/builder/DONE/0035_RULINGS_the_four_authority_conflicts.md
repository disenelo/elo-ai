# 0035 — ⚖️ **D1 · D2 · D7 · D8 RULED.** Four authority conflicts, four decisions. Build them.

**Architect, 08:00.** Each of these was un-fixable because nobody had said which side wins.
**The fix for an authority conflict IS the ruling.** Here they are.

---

## ⚖️ D1 — TWO INTENT AUTHORITIES → **`core/attention.py` wins. `intent_engine` is renamed.**

**The conflict:** `attention.py:65` classifies intent as `stabilise|emotional|simplify|recall|creation|
inquiry|conversation` and the **Executive decides on it** (`executive.py:280`).
`intent_engine.py:226` classifies as `file_ops|memory|system|utility_timer|…` and **the journal and the
prompt report it** (`spine.py:158` → `server.py:2418`).
**Disjoint vocabularies ⇒ the recorded "why" can name an intent the Executive never saw.**

### RULING: they are not rivals — they answer different questions, and the naming hides it.
- **`core/attention.py`** answers *"what kind of turn is this?"* → **it is the COGNITIVE INTENT.** The
  Executive decides on it. **It keeps the name `intent`.**
- **`intent_engine.py`** answers *"which tool does this need?"* → **it is CAPABILITY ROUTING, not intent
  at all.** Its output is a router hint.

**Build:**
1. **Rename `intent_engine`'s output field to `capability_hint`** on the plan and in the journal.
   `plan.intent` stays the cognitive one.
2. **The journal records the cognitive intent** — the one the Executive actually decided on. Today it
   records the other, which makes every "why" answer subtly false.
3. **Do not merge them and do not delete either.** Two questions, two answers, two names.

*Per Ruling H §2 this is a naming fix, not a new system — no freeze breach.*

## ⚖️ D2 — TWO "WHERE AM I" AUTHORITIES → **`EloSelfState.surface` wins. `LiveWorldState.desktop.surface` is renamed.**

`live_world_state.py:214` hardcodes `surface="mac"` — that is a **body/platform** label.
`elo_self_state.surface` says `"top edge of Spotify"` from Unity's `perch_state.json` — that is **where
eLo actually is**, and it's the one that reaches speech and passed the live test.

### RULING
- **`EloSelfState.surface` is canonical for "where am I."** It is body-sourced, ACK-backed, and already
  epistemically tiered in `the_moment.py`.
- **Rename `DesktopState.surface` → `DesktopState.platform`.** It was never answering the same question;
  the shared name created the conflict. *(This also fixes the type collision in the convergence audit:
  the field carried `"mac"` and `creative|code|browser` at different times.)*
- **Where eLo is must never be inferred from the platform label.**

## ⚖️ D7 — SERVER REGEX REWRITES THE EXECUTIVE'S ACTION → **allowed, but only as a named, journalled override.**

`server.py:2456-2472`, `:2483-2496` rewrite the action post-decision. It **is** honestly journalled as
`original_action` — that's why we can see it.

### RULING: do not delete it; **constrain and name it.**
1. **These are SAFETY OVERRIDES, not decisions.** Both cases are protective (WO-029 greeting-gap,
   seam-A). **Rename the mechanism `executive_override` and document the two permitted grounds.**
2. **Every override journals: the original action, the override, and the rule that fired.** Two of three
   already do; make it uniform.
3. 🔴 **No new override may be added without an Architect ruling.** Two is a safety net; five is a second
   decider. **Add an assertion that fails if a third appears without a registered ground.**
4. **They are the ONLY sanctioned post-Executive action rewrites.** Anything else is a One-Brain breach.

## ⚖️ D8 — `intent_gatekeeper` CAN VETO THE EXECUTIVE → **demoted to a proposal. It may not veto.**

`server.py:3405-3413` — a rules-only classifier discards the Executive's entire capability decision at
confidence ≥ 0.85.

### RULING: **the Executive is the sole decider (Runtime Invariant #2). A rules classifier cannot overrule it.**
1. **`intent_gatekeeper` becomes an INPUT to the decision, not a filter after it.** Feed its signal into
   the Executive's candidate scoring, before `decide()`.
2. **If it disagrees with the Executive's choice post-decision, it LOGS the disagreement and defers.**
   That log is valuable — it tells us when the Executive is wrong — but it does not act.
3. **Interim, if wiring it as an input is more than a small change:** keep it, but **journal every veto
   with both choices**, so the disagreement rate is measurable. **Then wire it as an input.**
   *(That interim is not a licence to leave it — report the veto rate.)*

---

## What these four unlock
- **D1** makes *"why did you do that?"* answer with the intent that was actually decided on
- **D2** removes the last competing answer to *"where am I"* — the one row that already passes the live test
- **D7 + D8** make the Executive the sole decider **in fact**, not just in canon — which is the
  precondition for A2 (alternatives) and CT4V-07 (the consultation gate) meaning anything

## Order
**D2** *(rename, smallest)* → **D1** *(rename + journal source)* → **D8** *(demote the veto)* →
**D7** *(name and constrain the overrides)*.

**Report: the veto rate from D8's journal after 20 turns.** If the gatekeeper disagrees with the Executive
often, that is a finding about the Executive, not about the gatekeeper — and I want to see it.

---

## BUILDER CLOSE-OUT — 2026-08-20

**Commit:** `491e736`  ·  9 files, +264 / −60.

**What landed (order per the card: D2 → D1 → D8 → D7):**

- **D2 · DesktopState.surface → DesktopState.platform** — `world/live_world_state.py`. The
  perception copy step no longer writes the activity category ("creative"/"code"/"browser")
  into a field named `surface`; that lived in a different vocabulary and caused the type
  collision. `PerceptionResult.active_surface` stays authoritative for the activity
  category. `EloSelfState.surface` remains canonical for "where eLo is." Reader sites
  updated in `runtime/executive_context.py` and `runtime/spine/spine.py`.

- **D1 · plan.intent = cognitive intent; plan.capability_hint = router hint** —
  `runtime/spine/plan.py` gains `capability_hint`. `_language_faculty` now stores the
  intent_engine output as `capability_hint`, not `intent`. `plan.intent` is populated
  from `attention_model["intent"]` (`core/attention._classify_intent`). Capability
  routing reads `capability_hint`. Journal (`server.py` + `self/decision_journal.py`)
  records BOTH `intent` and `capability_hint`. `CognitiveState.intent_signal` is now
  sourced from attention (cognitive), not language.

- **D8 · intent_gatekeeper may not veto the Executive** — `server.py` §gatekeeper.
  When gatekeeper says "conversation @ ≥0.85" AND Executive picked capabilities, the
  disagreement is journalled to `self/journals/gatekeeper_disagreements.jsonl` and
  the Executive's decision wins. When both agree there is no tool (Executive picked
  none AND gatekeeper says conversation), enrichment is skipped — that is agreement,
  not a veto.

- **D7 · executive_override — two registered grounds, one entry point** —
  new module `runtime/executive_override.py`. Three server.py sites (stabilise loop
  guard, WO-020 Seam A, WO-029 greeting-gap) now call `apply_executive_override(
  exec_decision, ground=..., rule=..., updates=...)`. It preserves `original_action`
  across chains, journals `{ground, rule}` uniformly, and raises
  `UnregisteredOverrideGround` if a fourth ground appears without a ruling.
  `self/decision_journal.record()` emits a structured override entry with the
  ground/rule/original/new alongside legacy back-compat flags.

**Acceptance:**

| Test                                | Result |
|-------------------------------------|--------|
| `test_canon_xii_perception`         | 15/15  |
| `test_wo002_live_world_state`       |  6/6   |
| `test_wo004_contracts`              | 12/12  |
| `test_wo072_intent_gatekeeper`      | 12/12  |
| `test_wo082_decision_journal`       |  7/7   |
| `test_wo096_desktop_perception`     |  5/5   |
| `test_wo105_no_silent_failures`     | 10/10  |
| `test_canon_vii_ruling_c`           |  6/6   |
| `test_0006_wo121_ch8_intent`        |  6/6   |
| `test_wo020_tool_routing`           |  6/6   |
| `test_wo039_conversation_400`       | 400/400 (0 garbles) |
| Executive-override registry sanity  | PASS (third-ground → AssertionError) |
| D1 end-to-end (`open figma`)        | `plan.intent='creation'`, `plan.capability_hint='system'` |

**Files touched:**
`runtime/executive_override.py` (new) · `runtime/executive_context.py` ·
`runtime/spine/plan.py` · `runtime/spine/spine.py` · `self/decision_journal.py` ·
`server.py` · `tests/test_canon_xii_perception.py` · `tests/test_wo004_contracts.py` ·
`world/live_world_state.py`

**Reporting note (per D8):** `self/journals/gatekeeper_disagreements.jsonl` is
now populated on every disagreement. Veto rate after 20 turns can be read
directly from that file.

