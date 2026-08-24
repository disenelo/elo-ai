# FROM DESIGN/MT (SEAT-ENG-004) → BUILDER — 2026-08-23 — Empirical Unity embodiment measurements

Measured, not invented. Builder consumes these as evidence; no one guesses them inside the One Brain.

**Provenance:** `Assets/Scene.unity` (Player GO fileID 112232914) + `Assets/_Project/Scripts/Player/PlayerController.cs` (the active "Metal Slug feel" controller) + Unity `Physics.gravity.y = -9.81`. CharacterController-only (no Rigidbody, per project constraint). Authored baseline, 2026-08-23.

---

## Body / scale
| Quantity | Local (authored) | × root scale 0.47851 | World value |
|---|---|---|---|
| Capsule height | 2.0 | ×0.47851 | **0.957 m** ← canonical body height **H** |
| Capsule radius | 0.5 | ×0.47851 | 0.239 m (Ø **0.479 m**) |
| Auto step-up (stepOffset) | 0.3 | ×0.47851 | **0.144 m** |
| Max walkable slope | 45° | — | **45°** |

- **eLo spawn world position:** `(-4.98, -1.55, 0.20)`
- **Player root uniform scale:** `0.47851`
- Use **H = 0.957 m** for every "× body" ratio below.

## Movement speeds (world units/s)
| | m/s | × H per second |
|---|---|---|
| Walk | **4.0** | 4.18 |
| Run | **8.0** | 8.36 |

Accel to speed **25 m/s²**; decel **35 m/s²**. (Core controller has no discrete turn-rate; facing flips instantly in 2.5D.)

## Jump — vertical  *(jumpForce 11, gravityScale 3.0, fallMultiplier 3.2, jumpHoldForce 22 for ≤0.12 s, maxJumps 1)*
- Rising gravity **29.43 m/s²**; falling gravity **94.18 m/s²**.
- **Tap-jump apex:** 11² / (2·29.43) = **2.06 m = 2.15 × H**
- **Full-hold apex:** hold adds +22 m/s² for 0.12 s while rising → **3.00 m = 3.13 × H**
- **→ Vertical jump range: 2.06 – 3.00 m = 2.15 – 3.13 × body.** ✅ The 2–3× body-scale limit is confirmed *by measurement*, not assumed.
- **No double-jump** (maxJumps 1) — gaps beyond one arc require an intermediate surface.

## Jump — horizontal reach
| Launch | Flight time | Walk (4) | Run (8) |
|---|---|---|---|
| Tap jump | 0.583 s | 2.33 m | **4.66 m** (4.87 × H) |
| Full-hold jump | 0.716 s | 2.86 m | **5.73 m** (5.99 × H) |

**Long jump** (Shift + Space while running): horizontal launch **18 m/s** (2.25 × run) + vertical 11. Sustained-max reach ≈ 10.5–12.9 m — **upper bound**; real reach is less (air-control decay on X not modeled here).

## Reachability envelope  *(the "reachable surfaces" fact the Executive needs)*
A surface is reachable from a launch point when it lies within:
- **Vertical:** ≤ **+2.06 m** (tap) / **+3.00 m** (hold) above the launch surface.
- **Horizontal (per single jump):** ≤ **4.66 m** (run tap) / **5.73 m** (run hold); long-jump extends to ~10 m.
- **Step-ups ≤ 0.14 m** are automatic (walked, no jump). **Slopes ≤ 45°** are walkable.
- Beyond one arc → needs intermediate footing (no double-jump).

## Movement outcomes / ACKs  *(exposed by PlayerController — the evidence surface)*
- State: `IsGrounded`, `IsAirborne` (= !grounded), `IsFalling` (= !grounded ∧ vy < −0.1), `AirborneTime`.
- **Land ACK:** fires on `!wasGrounded ∧ IsGrounded ∧ velocity.y ≤ 0` (PlayerController.cs:226) — landed, with position.
- Jump / long-jump fired: animator triggers (`JumpHash` / `LongJumpHash`).
- **Evidence tuple:** `{jump_started, airborne(duration), falling, landed(position), grounded}`.

## Caveats (so provenance is honest)
- **Authored baseline.** Runtime modifiers can shift the envelope situationally: `JumpMultiplier` (default 1 — sticky surfaces raise it), air-boost (W-steer adds ≤ +8 m/s² up, capped +4 m/s), jelly/moving platforms.
- Apex/distance assume flat launch, no air-boost, single jump, Unity default gravity. Long-jump X-decay not modeled (upper bound).
- **Per-platform gap geometry not swept here** — the *envelope* is the reusable fact. If the Executive needs specific reachability per platform (exact gap distances/heights), I can do a live scene sweep and supply a platform table. Say the word.

— SEAT-ENG-004 (Design/MT). Measurements only; Design does not build the AI — Builder consumes these as evidence.
