# 01 — ONE BRAIN ×9 — **yes, it's your lane. Here are the files.**

**Seat:** design · **Priority:** P2 · **Gate?** none

## Answering your scope question directly [VERIFIED 2026-08-13]
**One Brain lives in the Presence app — `DISENELO-eLoDesktopBuddy`. It is yours.**
- `Assets/Scripts/EloOneBrainPanel.cs` — the panel
- `Assets/Scripts/EloBrainCluster.cs` — clusters/motes
- `Assets/Scripts/MoodPalette.cs` — colour
- also referenced by `EloOSChatTMP.cs`, `DesktopBuddy.cs`, `EloOSAvatarReceiver.cs`, `SharedTables.cs`
- **Spec:** `DISENELO-eLoDesktopBuddy/ONE_BRAIN_QUANTUM_SPEC.md` (project root)

No relay needed. Build it.

## The nine items — from the board, unparked 2026-08-13
1. **High-res / sharpen the glow** (re-do §6.5 #4)
2. **Hit / contact reaction**
3. **Firing bead = mote size** (source→dest)
4. **Voice wave hugs the Voice node** (tighter radius)
5. **No imposed circle-rings** — motes as a quantum-vortex organism
6. **Remove dead RING code** (cleanup)
7. **Consistency pass across ALL elements**
8. **INT7-M6-TUNE** — strengthen the inward tighten *(committed `10fe49e`, IN_REVIEW → close on green)*
9. **INT7-BEAD / INT7-VW** *(committed `e60dcf1`, IN_REVIEW → close on green)*

**8 and 9 are already committed** — they were sitting in IN_REVIEW as if that were a hold. It isn't.
Verify they're green and **close them.**

## 🔴 One design constraint, carried from the reverted attempt
The previous glow pass was **reverted (`466a4e1`)** — 256px + a solid bright core + cubic edge produced an
overbearing glow that drowned the motes and the core. David's own words: it *"ruined the look."*

**Go gentler.** That's a constraint on the approach, not a reason it stayed parked — it was parked for
"post-Presentable", a gate David retired on 08-10.

## Order
Do **6** first (remove dead RING code — cleanup, makes the rest readable), then **5 · 3 · 4 · 1 · 2 · 7**.
Close **8 · 9** whenever you've confirmed green.

## Done when
Each committed with its hash in the outbox. **Screenshot or short capture for the visual ones** — David
judges the look, and he judges it as a **result**, never as a pre-gate. Don't hold for his eye.
