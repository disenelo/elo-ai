---
id: EA2-2B
title: "Company Brain — author the Figma frames (reuse EloBrainCluster look) → David review → Unity assemble"
owner_seat: SEAT-ENG-004 (UI/Avatar, Design) — Figma + Unity
occupant: Design (Unity/Figma)
priority: P1
reason: "EA2-2's Design half was implicit. David 2026-08-01: the Company Brain must LOOK and be built like the One Brain (EloBrainCluster), authored in Figma FIRST, then assembled in Unity. This is that discrete deliverable."
review_required: L1 → L3 (David reviews the Figma before any Unity build)
risk: low (design authoring; no runtime/kernel change)
status: READY — queues after INT7-WEB (same One-Brain family; Design's sole lane focus)
created: 2026-08-01
depends_on: EA2-2 (Builder data lane ✅) · reuses EloBrainCluster
figma_file: UdpnVgHT7qWOiyzk0MIgLU
---

# EA2-2B — Company Brain: Figma frames (One Brain look), then Unity

**Mandate (David):** the Company Brain is **not a new renderer** — it reuses `EloBrainCluster` (the One
Brain engine: quantum-vortex motes, MoodPalette glow, motion M1–M6/C1, spider-web) in **company-data
mode**. **No orange founder core.** Author in **Figma first** → David reviews → assemble in Unity.

## Data is ready (already emitted by `company_runtime` in `company_state/v1`)
- `graph` — divisions/seats/links (the nodes + connections)
- `agents[]` — live heartbeat (agent_bus): `fresh · pending · active · in_review · blocked · needs_david`
  → drives each node's **energy + valence** (active = brighter/faster; blocked/stale = negative → M6
  contracts inward + cooler; fresh = alive glow)
- `wo_tests` + `board[].importance/badge` — test health + approval tier per seat
- `coordination` — what's flowing to David → C1/M4 beads route between seats

## Deliverable (Figma → David → Unity)
1. **Figma frames** in `UdpnVgHT7qWOiyzk0MIgLU` (MoodPalette variables already there):
   - the **Company Brain** itself — divisions = vortex systems, seats = motes, agents = the heartbeat
     driving energy/valence, links = graph + spider-web (INT7-WEB), lightning-liquid (INT7-LL) on high
     cross-seat activity. **Company-mode, no founder core.**
   - the surrounding **HUD panels** — briefing · board · approvals · **agents heartbeat** · test-health
     (the interim `DISENELO_Presence_Dashboard.html` mirrors this data 1:1 as the build reference).
2. **David reviews the Figma** (L3) — the look, before any Unity work.
3. On approval: **assemble in Unity on `EloBrainCluster`** (company-data mode), reading `company_state`.

## Acceptance
1. Figma frames present the Company Brain in the One-Brain visual language + the HUD panels, MoodPalette
   only, no founder core.
2. David signs off the Figma look (L3).
3. Unity assembly reuses `EloBrainCluster` (not a new renderer) and reads live `company_state`.
4. Handback: Figma frame links + a short recording of the company-mode brain reacting to live data.

## Notes
- Same One-Brain family as INT7-WEB/LL — sequence **after** INT7-WEB so the web/mesh language is settled,
  then reuse it here. Design's sole lane focus stays One Brain; this is part of it.
- 🟠 DAVID importance — the Figma look is your call; nothing assembles in Unity before you approve it.
