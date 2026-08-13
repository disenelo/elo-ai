---
id: INT7-M4
title: "One Brain visualiser — M4 Synaptic Cascade (single change)"
status: READY → DISPATCHED (Design)
target_agent: UI/Avatar (Design)
priority: P2
owner: ""
depends_on: [INT7-C1 (DONE ✅ David)]
spec_refs:
  - docs/architecture/20_one_brain_visualiser.md §6.6 (M4) + §6.7 (beads ride the web)
lane: Presence/Unity (EloBrainCluster) — NOT eLo OS (D-I)
created: 2026-07-28
---

# INT7-M4 — Synaptic Cascade (One Brain visualiser, v-next change #5)

Builds directly on C1. Where C1 is a single bead firing to the core, **M4 is the chain reaction** —
activity *propagates* hop-to-hop across the connectome, weakening as it spreads. This is the brain
"thinking through" a signal, not just routing one packet.

## 1. Objective (one change only)
When a system is `active` with **energy rising**, its activity **propagates hop-to-hop** along the
web — `Vision → Intent → Attention → Memory → Emotion → Voice` — **losing energy each hop**, so the
cascade visibly fades as it travels outward from the origin.

## 2. Exactly what to build
- **Trigger:** a system is `active` **and** its `energy` is **rising** (not merely nonzero — a rising
  edge). Distinct from C1's discrete single-spike bead.
- **Propagation:** the activity hands off **hop-to-hop** along the dependency chain
  (`Vision→Intent→Attention→Memory→Emotion→Voice`), each downstream node lighting/firing in turn,
  riding the web filaments (same substrate as C1).
- **Energy loss per hop:** each hop is **dimmer/weaker** than the last — the cascade **attenuates**
  and dies out; it does not travel forever at full strength.
- **Depth cap (MUST):** **cap propagation depth** — the chain stops after N hops (or when energy
  falls below a floor), so a cascade can't run away across the whole graph or loop.

## 3. Signal contract
Reads per-system `energy` / `active` (+ rising edge) and the dependency/link topology from
`brain_state.json` + existing web geometry. Reuses C1's bead/pool substrate where possible. Pure
render. **No new state, no eLo OS change.**

## 4. Constraints (MUST)
- **One change only** — synaptic cascade, nothing else. M1 respiration, M2 dormant noise, M3 afterglow,
  **C1 single-bead routing**, colours (full MoodPalette), clustering, click-pin, labels/`_tip`, node
  size, anchors all **untouched**. M4 layers on top and coexists.
- **Beads ride the web filaments** — propagation travels on the links, not through empty space (§6.7).
- **Cap propagation depth** — hard limit on hops + an energy floor; no runaway, no infinite loop, no
  full-graph flood. Background-safe.
- Distinct from C1: C1 = one discrete packet to core; **M4 = a fading multi-hop chain**. They must read
  as related but different (routing vs cascade).
- Lane: `EloBrainCluster` (Presence/Unity). Do **NOT** touch eLo OS (`~/elo-ai/`) — D-I.

## 5. Acceptance (visual review + build gate)
- [ ] A rising-energy active system triggers a **hop-to-hop cascade** along the dependency chain.
- [ ] Each hop is visibly **weaker than the last**; the cascade **fades out** (energy loss per hop).
- [ ] Propagation **depth is capped** — it stops (N hops / energy floor), never floods the graph or loops.
- [ ] Rides the web filaments; reads as distinct from C1's single bead.
- [ ] C1 + M1 + M2 + M3 still work unchanged (all coexist); MoodPalette colours untouched.
- [ ] Builds 0 compile errors; relaunch shows it live; diff is cascade-only.

## 6. Build discipline
One change · exactly to spec · build (0 errors) · relaunch · **then WAIT** for review.
Baseline = the C1 commit (`df5e552`).

## 7. Handback
Commit hash + one-line note → `COMPLETION_LOG.md`. David visual-reviews; Architect verifies against
§2/§5 → DONE → next in the queue is **M5 Memory Echo** (retrieval sends 3 diminishing, slowing ripples).
