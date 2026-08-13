---
id: INT7-C1
title: "One Brain visualiser — C1 Data Packet Routing (single change)"
status: READY → DISPATCHED (Design)
target_agent: UI/Avatar (Design)
priority: P2
owner: ""
depends_on: [INT7-M3 (DONE ✅ David)]
spec_refs:
  - docs/architecture/20_one_brain_visualiser.md §6.6 (C1) + §6.7 (synapse beads ride the web)
lane: Presence/Unity (EloBrainCluster) — NOT eLo OS (D-I)
created: 2026-07-27
---

# INT7-C1 — Data Packet Routing (One Brain visualiser, v-next change #4)

First **computational** motion in the queue (M1–M3 = neural/homeostatic are done). Where the
neural behaviours are organic and analog, C1 reads as **machine**: discrete, quantized, precise.
This is the beads/packets David described — *"data links that shoot along the spider-web lines."*

## 1. Objective (one change only)
When a system transitions active / spikes in `energy`, emit **discrete data beads** that route
along the web filaments from that system → Intent core → peripheral, by dependency
(e.g. Vision → Attention → Intent). The firing you can *see* travelling the connectome.

## 2. Exactly what to build
- **Trigger:** a system activity transition or an `energy` spike (per-system, from `brain_state.json`).
- **Bead:** a **bright, step-quantized packet** — *no organic tail*. Motion profile is machine-like:
  **sharp acceleration → uniform glide → instant arrival** (not eased/organic like the M-series).
- **Route:** travels **on the web filaments** (the spider-web links are the routing substrate — the
  bead rides the line, never crosses empty space), following dependency order toward the Intent core
  and out to peripheral.
- **Pooling:** beads **pool alongside `beadsPerLink`** (reuse, don't allocate per-fire) — many can be
  in flight at once without GC churn.
- **Distraction control:** **high speed = low distraction** — fast enough that density reads as
  "traffic," not a light show.

## 3. Signal contract
Reads per-system `energy` / `active` + the existing link/dependency topology from `brain_state.json`
and the current web geometry. Pure render + pooling. **No new state, no eLo OS change.**

## 4. Constraints (MUST)
- **One change only** — data-packet routing, nothing else. M1 respiration, M2 dormant noise,
  M3 afterglow, colours (full MoodPalette), clustering, click-pin, labels/`_tip`, node size, anchors
  all **untouched**.
- Beads **ride the web filaments** — do not draw them through empty space (that breaks the "links are
  the substrate" canon, §6.7).
- **Machine, not organic:** quantized/step motion, no soft tail — it must read as *computation*, visibly
  distinct from the M-series' organic easing.
- **Background-safe:** at idle/low energy, no or minimal beads; density scales with activity.
- Lane: `EloBrainCluster` (Presence/Unity). Do **NOT** touch eLo OS (`~/elo-ai/`) — D-I.

## 5. Acceptance (visual review + build gate)
- [ ] A system going active / spiking emits discrete bright beads that travel **along the web lines**
      toward Intent, in dependency order.
- [ ] Bead motion is **quantized/machine** (sharp accel → uniform glide → instant arrival), no organic tail.
- [ ] Reads as *computation* — clearly distinct from M1/M2/M3 organic motion; not distracting at speed.
- [ ] Beads are **pooled** (`beadsPerLink`); many concurrent fires don't hitch/allocate.
- [ ] M1 + M2 + M3 still work unchanged (all coexist); colours from the full MoodPalette untouched.
- [ ] Builds 0 compile errors; relaunch shows it live; diff is data-packet-only.

## 6. Build discipline
One change · exactly to spec · build (0 errors) · relaunch · **then WAIT** for review.
Baseline = the M3 commit (`8aacb2a`).

## 7. Handback
Commit hash + one-line note → `COMPLETION_LOG.md`. David visual-reviews; Architect verifies against
§2/§5 → DONE → next in the queue is **M4 Synaptic Cascade** (the bead's *arrival* ripples onward).
