# WO-MOBILE-PHASE2 — Brain publishes Phase 2 mobile signals

**Authority:** David L3 (D3 ruling, 2026-08-30) + Mobile Presence Plan
**Source:** `docs/architecture/_intake/SOURCE_2026-08-29_D1_mobile_embodiment_ruling.md`
**Priority:** P2 (after Phase 1A MT returns)
**Owner:** Builder (spine-side write)

---

## Why this exists

D3 RULED: `travelling` disposition requires explicit brain intent — NOT inference from snapshot. Until the brain publishes `travel_intent`, the travelling disposition does not exist for MT. This WO delivers the three missing signals that unlock Phase 2 dispositions.

---

## Three signals to publish into the state file

All three are additive writes to `blender_state.json` (or companion file the probe serves). No new endpoints. Ruling 006 untouched. `executive.py` NOT touched.

### 1. `embodiment` — unlocks `dormant`

```json
{ "embodiment": "desktop" }   // eLo's current body location
```

- Write when eLo is embodied on desktop (the normal running state)
- Absent / null = embodiment unknown
- Phone reads this → if `embodiment == "desktop"` and phone has a snapshot → **dormant** disposition (he knows he's somewhere, staying there)

### 2. `travel_intent` — unlocks `travelling`

```json
{ "travel_intent": true }   // eLo has autonomously chosen to travel with David
```

**David (2026-08-30):** *"I want that to be a thing the brain can think, like the way he can choose an intent to go somewhere and do something himself."*

This is NOT a developer-set flag. It is a cognitive decision eLo makes autonomously — the same way he can choose to navigate to a spot or sit somewhere. The mechanism:

- Significance faculty + relationship faculty detect that David is mobile / away from the desktop
- If significance threshold is crossed → Executive produces a plan that includes `travel` as the chosen intent
- The consequence of that plan is `travel_intent: true` written to the state file
- This is eLo expressing a choice through his cognitive loop, not a hardcoded trigger

`travel_intent` is therefore an OUTPUT of the executive capability-action chain, not a static API field. It must flow through:
`PERCEIVE (David away) → UNDERSTAND → PLAN (travel intent) → EXECUTE (write to state) → CONSEQUENCE (phone reads it)`

Wiring: the `travel` intent/capability must be registered in the capability registry and the executive must be able to plan it. The state file write is the action consequence.

### 3. `asleep` — completes `absent`

```json
{ "asleep": true }   // eLo has deliberately gone to sleep
```

- Write on sleep/rest event (complement to Take Five exit event which already exists)
- Phone reads this → `asleep == true` → absent disposition (gone to sleep path)

---

## Acceptance Tests

- **AT-1:** Brain running, desktop embodied → `embodiment: "desktop"` in state file. Phone reads it.
- **AT-2:** `travel_intent: true` written to state file → phone can read and parse it.
- **AT-3:** Sleep event fires → `asleep: true` in state file. Clear on wake.
- **AT-4:** All three fields present → probe serves them unchanged (read-only to phone).
- **AT-5:** `executive.py` not modified. `executive.py` FREEZE_V1_LOCK (restored after WO-SEAM-A) clean.

---

## Return

`DONE/FROM_BUILDER_WO-MOBILE-PHASE2_brain_signals_result.md` · AT pass count · commit hash

*Board / Lead Architect · 2026-08-30*
