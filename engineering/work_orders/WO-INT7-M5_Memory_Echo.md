---
id: INT7-M5
title: "One Brain visualiser — M5 Memory Echo (single change)"
status: READY → DISPATCHED (Design)
target_agent: UI/Avatar (Design)
priority: P2
owner: ""
depends_on: [INT7-M4 (DONE ✅ David)]
spec_refs:
  - docs/architecture/20_one_brain_visualiser.md §6.6 (M5)
lane: Presence/Unity (EloBrainCluster) — NOT eLo OS (D-I)
created: 2026-07-29
---

# INT7-M5 — Memory Echo (One Brain visualiser, v-next change #6)

The "it came from somewhere" motion. Where M4 propagates *outward* from a strong activation, **M5 fires
when the Memory system is read** — a retrieval sends **diminishing, slowing ripples** back through the
field, as if the thought surfaced from depth.

## 1. Objective (one change only)
On a **memory retrieval**, emit **3 concentric echo ripples** from the Memory system — each **weaker and
slower** than the last — then fade. Reads as recall, not activity.

## 2. Exactly what to build
- **Trigger:** the **Memory** system performs a retrieval (from `brain_state.json` — memory active /
  retrieval event / Memory energy pulse). Distinct from M4's strong-activation cascade.
- **Motion:** **3 ripples** emanate (from the Memory node / its region), **diminishing** (each dimmer)
  **and slowing** (each expands slower than the last) — a settling echo, not a steady pulse.
- **Character:** gentle, low-amplitude — "came from somewhere," a surfacing memory. Not a firing.
- **Fade:** the 3rd ripple dissolves; nothing persists.

## 3. Signal contract
Reads the Memory system's retrieval/energy signal from `brain_state.json` (already emitted). Pure render,
no new state. Reuse the ripple/pooling substrate where it helps.

## 4. Constraints (MUST)
- **One change only** — memory echo, nothing else. M1 respiration · M2 dormant noise · M3 afterglow ·
  C1 routing · M4 cascade · colours (MoodPalette) · clustering · click-pin · labels · node size · anchors
  all **untouched**. M5 layers on top and coexists.
- **Low amplitude** — must read as *recall*, clearly gentler than M4's cascade and below "activity"; it is
  an echo, not a firing.
- **Exactly 3 ripples**, diminishing **and** slowing — not an indefinite pulse train.
- Only on a **Memory retrieval** — not on general Memory activity.
- Lane: `EloBrainCluster` (Presence/Unity). Do **NOT** touch eLo OS (`~/elo-ai/`) — D-I.

## 5. Acceptance (visual review + build gate)
- [ ] A memory retrieval emits **3 concentric ripples** from the Memory region.
- [ ] Each ripple is **weaker and slower** than the previous; the set settles and fades.
- [ ] Reads as gentle recall — clearly distinct from M4's cascade and from C1's bead.
- [ ] M1 · M2 · M3 · C1 · M4 still work unchanged (all coexist); MoodPalette colours untouched.
- [ ] Builds 0 compile errors; relaunch shows it live; diff is memory-echo-only.

## 6. Build discipline
One change · exactly to spec · build (0 errors) · relaunch · **then WAIT** for review.
Baseline = the M4 commit (`5e834f3`).

## 7. Handback
Commit hash + one-line note → `COMPLETION_LOG.md`. David visual-reviews; Architect verifies against
§2/§5 → DONE → next in the queue is **M6 Emotional Diffusion** (valence change diffuses like dye).
