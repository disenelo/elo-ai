# 05a_HEADLOOK_AUDIT_findings.md — Architect audit of HeadLook.cs (read-only, done 2026-08-10)

David asked: *"Audit how the HeadLook works, and can we add the rotations to it with a follow system or
constraint stack follow if possible?"* — Architect read the file (474 lines). Findings below are FACTS from
the code, so the Designer doesn't re-diagnose.

## FINDING 1 — why the idle animation beats HeadLook (THE bug David sees)
The head write is **additive on top of the animated pose**:
```csharp
headBone.localRotation = headBone.localRotation * Quaternion.Euler(curPitch + …, curYaw, …);
```
`headBone.localRotation * …` means HeadLook **offsets whatever the idle clip already did** — it never
*overrides* it. So if the idle animation swings the head, that swing stays and HeadLook's look is a small
wobble riding on it. **This is exactly David's "the head rotates during idle and I never see the headlook
move as I want."** Not a tuning problem — a compositing problem.

## FINDING 2 — the look is tiny, and the random wander masks it
- `maxYawDegrees = 30`, `maxPitchDegrees = 15` (David wants **±100**).
- `lookStrength = 0.44`, `cursorLookDuty = 0.30` → he tracks only ~30% of the time, at 44% strength →
  **effective yaw ≈ 13°**.
- Meanwhile `explore` wander adds **±8 yaw / ±12 pitch** ALWAYS, additively.
→ The deliberate cursor-look (~13°) and the random wander (~8–12°) are **nearly the same magnitude**, so the
looking reads as drift. Even fixed, the ceiling is 30° — nowhere near what David asked for.

## FINDING 3 — HeadLook is a god-object (474 lines, mostly NOT head aim)
It also owns: cursor-reactive smile/worried, the whole **micro-expression system** (Ekman flashes, bored
holds, mood baseline, WO-062 `FlashMicro` from the brain), drag tilt, peek tilt, belly-glow look-down,
observe pitch/roll, sit tilt, agreement **nod**. **Only ~1/4 of the file is head rotation.**
→ Do NOT delete HeadLook. The expression half is good, working, and brain-wired.

## FINDING 4 — brain gating already exists (reuse it, don't rebuild)
`receiver.HeadCueActive` / `HeadYawCue` / `HeadPitchCue` already let eLo OS drive the head in DEGREES, and
autonomy yields to it. **The new aim must consume the same cue** — that's the One-Brain path, already built.
Also present and must be preserved: `PeekPitch` (the WO-049 peek-before-jump beat), `ObservePitch/Roll`
(watching you work), `SitTilt`, `Nod()`, drag tilt, `Calm` rest.

## ANSWER to David's question
**Yes — and the constraint stack is the RIGHT fix, precisely because of Finding 1.** An Animation Rigging
constraint evaluates in the animation graph and produces an **absolute aim**, so it beats the idle clip
cleanly. Bolting bigger numbers onto the current additive line would still be riding on top of the idle swing.

## THE PLAN (Designer: build in this order)
1. **SPLIT the file.** `HeadLook.cs` → keep everything EXCEPT the rotation as **`HeadExpression.cs`**
   (expressions · micro-expressions · mood baseline · nod · tilts). Zero behaviour change to that half.
2. **`HeadAim` (rig constraint) takes over rotation** — Multi Aim Constraint, constrained object = **head
   bone (`c_head.x`)**, mouse target, **±100** per David, smooth. It must consume `HeadCueActive` /
   `HeadYawCue` / `HeadPitchCue` so the brain still owns the head when it speaks.
3. **Re-home the additive beats** (peek · drag · observe · sit · nod · belly) as offsets ON TOP of the
   constraint result — they're small and deliberate, and must survive.
4. **Then ChestAim + ArmAim (Two Bone IK)** per the main card — the natural stack.
5. **Retire the rotation half of HeadLook only.** Never two drivers on `c_head.x`.

## Test
Idle running → head aims where HeadAim says (NOT where the idle clip says) — that's the acceptance David
cares about. Cursor look is clearly visible, not masked by wander. Brain cue still wins. Peek/drag/observe/
sit/nod still fire. No regressions.
