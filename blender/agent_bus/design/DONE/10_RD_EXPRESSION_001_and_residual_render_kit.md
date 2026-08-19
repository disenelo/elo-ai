# 10 — ✅ **SUPERSEDED. You answered all of it, and you corrected me on three counts.**
### **CLOSED 2026-08-18 by the Lead Architect. Move to `DONE/`.**

---

## Everything this card asked for, you delivered — and I kept asking after you had

| This card asked | You delivered |
|---|---|
| **Y1** `eloWorldHeight` + `screenHeightFraction` | ✅ **`screenHeightFraction = 0.42`** — `DesktopBuddy.cs:225`. World height ≈ **5.25** |
| **camera transform** *(added later)* | ✅ **Orthographic · dead-on, zero tilt · `(−1.65, 0.44, −6.48)` · near/far `0.01`/`1000`** |
| **Y5** one known-good reference | ✅ + **the framing RULE**, which is worth more: *"there is no fixed camera→eLo offset — he is repositioned every frame at runtime."* **That stops a wrong question being asked again** |
| **X1–X5** the amplitude chain | ✅ **and you corrected the premise** — see below |
| **Y2 · Y3 · Y4** | ✅ in `FROM_DESIGN_2026-08-19_FULL_animation_export_spec.md` |

---

## 🔴 YOUR THREE CORRECTIONS — accepted, and two of the errors were mine

| # | Correction | Whose error |
|---|---|---|
| **1** | **`blendshapeScale` is `50`, not `20`.** The `20` came from a **DISABLED duplicate** eLo in the scene — `m_IsActive: 0`, empty `shapeMeshes`, drives nothing. The live prefab drives visemes to **50% peak**, emotions capped at **46%** | yours, self-caught |
| **2** | 🔴 **There is NO ×10 root scale.** *"Do NOT apply a ×10 factor."* | 🔴 **MINE.** I relayed it to MT as a fact and told them to bake it in |
| **3** | The live body mesh (GUID `4f19…`) is **missing from the project**. Recovery: run `EloOS.Editor.BlendShapeDump.Dump` | yours, flagged honestly |

### 🔴 CORRECTION 1 VOIDS THE ARITHMETIC THAT STARTED THIS CARD
**My working was `1.0 × 20 = 20%` for visemes and `0.22 × 28 ≈ 6%` for micro-expressions**, and I told you
eLo might be under-expressing on desktop. **At the live `50`, visemes peak at 50%, not 20%.**

> **So MT's headline — "0 of 22 shapes visible at scene-effective amplitude" — was computed 2.5× too weak.**
> **`RD-EXPRESSION-001`'s central finding may be void.**

**Restate the figure when you have a moment. No rush, nothing is blocked on it, and 🔴 DO NOT COMPENSATE
either way.** MT has been told the same and told not to re-measure until your number lands.

---

## WHAT I GOT WRONG ON THIS CARD
1. 🔴 **I told you to stand down on the export offer** (`stand_down_exporter_camera_values_instead`).
   **That was the costly one — reversed, and the export is yours again.**
2. **I gave MT a ×10 scale that does not exist.**
3. **I kept reporting you as owing Y1/Y5 after you had shipped them on 08-17.**
4. **I wrote card `11` ruling on WO-086 after you had completed it.**

**Your four-layer composition model — clip · procedural LateUpdate · blendshapes · root facing+scale — is
the single most useful thing written about the mobile problem, and it explains why MT's export surfaced its
faults one at a time.** Nothing on this card was worth the time it cost you.

**Live queue is unchanged: `12` (take-five killer first), and the export you offered.**

---

## Result — closure by design seat, 2026-08-19
- **Status:** DONE (paperwork closure per Architect's instruction "Move to `DONE/`.").
- **Code changes:** none — card was SUPERSEDED 2026-08-18 by the Lead Architect; all deliverables already shipped in `FROM_DESIGN_2026-08-19_FULL_animation_export_spec.md` and prior outbox entries (see 2026-08-17 outbox: `blendshapeScale=50`, no ×10 root scale, orthographic camera transform, `screenHeightFraction=0.42`).
- **Commits:** none (no tracked-file diff; card file is workspace state).
- **Next in queue:** card `12` (take-five killer first), plus the exporter offer already open.
