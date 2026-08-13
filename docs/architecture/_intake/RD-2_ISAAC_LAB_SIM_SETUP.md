# RD-2 — NVIDIA Isaac Lab Simulation Setup (eLo Robot Phase 2)
**Seat:** SEAT-RND-002 (R&D · Gemini) · **Relayed:** 2026-07-31 (Google Doc → Drive read) · **Status: 🟡 IN_REVIEW → David L3**
Provenance: `[ENGINEERING]` (sim architecture) + `[SCIENCE]` (RL / sim-to-real). Source Doc: `d.charles.j@gmail.com` Drive.

> **Safety boundary (respected):** the sim models **virtual forces only**; all physical force-limiter /
> soft-stop mechanisms stay held under **LG-2** for Product-Safety + human review before any build.

## 1. Isaac Lab sim scaffold
PhysX 5 + USD; unified parallel sim of rigid articulation (tendon/neck) coupled with deformable soft bodies.
- **Physics:** PhysX 5 **FEM** deformable solver + rigid articulated joints.
- **Soft bodies:** TPU panelised shell = 3D **tetrahedral mesh**; chest bladder = **PBD** inflatable pressure container.
- **Tendon actuators:** implicit Bowden-cable **PD** drives mapped to cable length/tension limits (silent base servos).

## 2. Domain randomisation (sim-to-real) — per-episode uniform ranges
| Parameter | Baseline | DR range | Rationale |
|---|---|---|---|
| Skin Young's modulus E | 12.5 MPa | [8.0, 18.0] | TPU batch + temperature softening |
| Cable/conduit friction μ | 0.15 | [0.08, 0.35] | sheath wear + routing bends |
| Head payload mass | 280 g | [240, 340] | glow electronics + camera variance |
| Bladder rest volume V₀ | 180 cm³ | [150, 210] | micro-pump output + line pressure |
| Action latency Δt | 20 ms | [10, 60] | on-device inference delay |

## 3. Synthetic perception (gaze = head orientation, NO EYES)
- Dual-stream **RGB-D 640×480 @30fps** from hidden wide-angle micro-lenses in the facial panel.
- Domain-randomised lighting/scenes → ground-truth human head-pose / keypoint vectors.
- Output: relative target vector `v_target=(x,y,z)` → smooth **Bowden-cable neck orientation** toward the human.

## 4. Phase-2 RL training targets
1. **Adaptive balance & soft compliance** (RL) — input IMU + skin-compression tensors; yields softly to a push/hold, motors stay silent.
2. **Curious nudging & gentle lean** (imitation / GR00T-style) — input `v_target` + posture; learned organic lean/tilt/breathing modulation.
3. **Scripted override boundary** (non-learned safety) — e-stop / low-battery / boot **bypass RL**, default to deterministic FBX states.

## 5. Hardware framing (uncommitted — benchmark only)
- **A. Jetson Orin Nano 8GB** — TensorRT + CUDA vision; 7–15 W.
- **B. Pi 5 + Hailo-8L NPU (13 TOPS)** — lower cost/thermal (~5 W); ONNX runtime, CPU-bound perception.
- **Benchmark matrix (for later):** inference latency (<15 ms goal) · idle power · passive thermal in the sealed 45cm soft body.

## 6. Four-part relay
1. **Found:** Isaac Lab PhysX-5 FEM soft-body + rigid articulation = the exact framework to train cable-driven soft animatronics; DR of modulus/friction/payload → resilient sim-to-real.
2. **Open:** empirical thermal/power (Jetson vs Pi5+NPU) in the sealed chassis (uncommitted); LG-2 safety review.
3. **Recommend:** adopt **Isaac Lab + PhysX 5 as the canonical Phase-2 sim pipeline** — full virtual policy training without risking prototype wear/motor damage.
4. **Unblocks:** RD-3 (eLo FBX vocabulary → RL reward targets) + RD-5 (Kickstarter "simulating a soft robot in Isaac Lab" content).

---

## 🔷 Architect first-pass review (L1) — Claude

**Verdict: 🟢 accept — sim-only, disciplined, eLo-true. Escalate to David L3 (adopts the Phase-2 sim pipeline; commits no hardware, no build).**

- **Safety discipline: excellent.** It explicitly holds all physical force-limiters under LG-2 and models
  virtual forces only — exactly the boundary I asked for. No physical-build implications.
- **Character-canon: passes.** Gaze = head-orientation vectors, *not* eyes (correctly honours the no-eyes rule).
- **No hardware commit:** Jetson-vs-Pi5 is framed as a benchmark, not chosen — right call; the decision waits.
- **Scope:** this is a **simulation architecture** decision. Approving = "Isaac Lab + PhysX 5 is our Phase-2
  sim pipeline" + opening RD-3. It's lower-risk than RD-1 (no physical actuation), but it's a real
  standing technical direction, so it's a fair L3 stamp.
- **One note:** Phase 2 (learned) is gated behind Phase 1 (the physical build) which itself is gated behind
  LG-2 safety + funding. So RD-2 is *forward research* — valuable and safe to bank now, but sequenced after
  the physical robot exists. It also makes great **Kickstarter build-in-public** content (RD-5) *today*.

**On David L3 → I will:** mark RD-2 DONE, open **RD-3** (FBX vocabulary → RL reward targets, Gemini) and
note **RD-5** (Kickstarter "simulating a soft robot" content) as ready when the campaign lane spins up.
