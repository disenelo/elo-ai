# FROM DESIGN (SEAT-ENG-004) → MOBILE TEST — WO-124 FULL MOVEMENT & EXPRESSION AUDIT (manifest)

**Card:** `design/DOING/09_WO-124_FULL_MOVEMENT_EXPRESSION_AUDIT_for_MT.md` (Lead Architect, 2026-08-17).
**Closed:** 2026-08-24 (consolidation — nothing rebaked; every row indexed to a verified prior deliverable, filled to spec, or marked `UNKNOWN`/`NONE`).

**Standing rule for this file** (Architect §0): every enumerated row has a value. `NONE` if not applicable, `UNKNOWN` if I don't know (with the measurement that would settle it). No blanks. No prose substituted for a list.

**Provenance — the deliverables this manifest indexes (all in `mobile_test/`, all verified against source):**
- **R** — `FROM_DESIGN_2026-08-16_rig_answers.md` (Q1–Q5 rig)
- **P** — `FROM_DESIGN_2026-08-17_eLo_full_presentation_reference.md` (movement + camera + envt)
- **C1** — `FROM_DESIGN_2026-08-17_camera_transform_Y1_Y5.md`
- **F** — `FROM_DESIGN_2026-08-19_FULL_animation_export_spec.md` (**the master spec — 355 lines, authoritative**)
- **X** — `FROM_DESIGN_2026-08-19_frame_exporter_DELIVERED.md`
- **U** — `FROM_DESIGN_2026-08-20_FULL_mobile_app_UI_parity_spec.md`
- **I1** — `FROM_DESIGN_2026-08-20_idle_loop_answer.md`
- **B1** — `FROM_DESIGN_2026-08-21_P1_baked_idle_x_visemes_DELIVERED.md`
- **C2** — `FROM_DESIGN_2026-08-21_camera_reference_frame_head_pose.md`
- **I2** — `FROM_DESIGN_2026-08-21_idle_one_period_73_frames.md`
- **M** — `FROM_DESIGN_2026-08-22_FULL_MATRIX_deterministic_camera_DELIVERED.md` (final camera fix)
- **L** — `FROM_DESIGN_2026-08-22_P1_idle_lipsync_CORRECTED.md`
- **W** — `FROM_DESIGN_2026-08-23_PORTED_webp_neutral_calm.md`
- **LP** — `FROM_DESIGN_2026-08-23_lipsync_frame_pointer.md`
- **[F§n]** = section n of the F spec (the deep reference).

**Amplitude ruling (David override, 2026-08-22, per M):** viseme weight = **100** (not 50). David's expressions, David's strength. That supersedes the spec-7 correction chain in F§0. Where a table cites 50, read it as the code default; the LIVE authored value is 100.

---

# §A — BLENDSHAPES / FACE (46 shapes, `eLo-BodyxHead w/Mouth`)

## A1 — All 46 blendshapes, exact names, in index order
Source: F§7.1 (verified against MT's `BlendShapeDump` on `eLo-ProductonReady 1.prefab`, position-for-position).

| # | Name |
|---|---|
| 0 | MouthOpen.Slightly |
| 1 | MouthOpen.Wide |
| 2 | Smile.L |
| 3 | Smile.R |
| 4 | JawOpening |
| 5 | MouthWidth.L |
| 6 | MouthWidth.R |
| 7 | Upper-Lip.R |
| 8 | Lower-Lip.R |
| 9 | Lower-Jaw-U/D |
| 10 | Template |
| 11 | Mouth-Open-Shock |
| 12 | Sad-Lower-Lip-Dimples |
| 13 | Inflate-Cheeks-L |
| 14 | Smile-Cheeks |
| 15 | Puff-Cheeks |
| 16 | Smile/Sad-Open-Mouth |
| 17 | Mouth-OpenDisgust |
| 18 | Angry/Expressive |
| 19 | Huh |
| 20 | Curl-Lips |
| 21 | Stick-Out-Lip |
| 22 | Ah |
| 23 | Mbp |
| 24 | Mmmm |
| 25 | Eh |
| 26 | Ai |
| 27 | Oooh |
| 28 | Shock-Oooo |
| 29 | Fv |
| 30 | FvS |
| 31 | S |
| 32 | Ee |
| 33 | Puff-EyebrowsRaise |
| 34 | Confident |
| 35 | Worried |
| 36 | Disgusted |
| 37 | Angry |
| 38 | Satisfied/LittleJoy |
| 39 | Tongue Out |
| 40 | Tongue Move |
| 41 | Poke-Out |
| 42 | F/B |
| 43 | Twist |
| 44 | Key 6 |
| 45 | Key 7 |

**Sibling meshes** (same names, driven by the same weight write):
- `LowerJaw` (7): MouthOpen.Slightly, MouthOpen.Wide, Smile.L, Smile.R, JawOpening, MouthWidth.L, MouthWidth.R.
- `UpperJaw` (7): same 7 as LowerJaw.
- `Tongue` (7): Tongue Out, Tongue Move, Poke-Out, F/B, Twist, Key 6, Swirl. (Body's "Key 6/Key 7" ≠ Tongue's "Key 6/Swirl" — same-index positions on separate meshes.)

## A2 — Wired vs not wired (per shape)
Wired = live code writes it OR the FBX rig ships it linked to a driver. All 46 are drivable by name (`SetBlendShapeWeight` by string lookup, so brain can address any of them). **Wired-and-firing today** = the paths in A3 actually send them.

| # | Name | Wired |
|---|---|---|
| 0 | MouthOpen.Slightly | ✅ (viseme) |
| 1 | MouthOpen.Wide | ✅ (viseme) |
| 2 | Smile.L | ✅ (emotion + greeting) |
| 3 | Smile.R | ✅ (emotion + greeting) |
| 4 | JawOpening | ✅ (lip-sync jaw spring) |
| 5 | MouthWidth.L | ✅ (viseme shaper) |
| 6 | MouthWidth.R | ✅ (viseme shaper) |
| 7 | Upper-Lip.R | NOT WIRED (dormant, drivable) |
| 8 | Lower-Lip.R | NOT WIRED (dormant, drivable) |
| 9 | Lower-Jaw-U/D | NOT WIRED (dormant, drivable) |
| 10 | Template | NOT WIRED (author scaffold — do not render) |
| 11 | Mouth-Open-Shock | ✅ (emotion `shook` + viseme-adjacent) |
| 12 | Sad-Lower-Lip-Dimples | ✅ (emotion `sad`) |
| 13 | Inflate-Cheeks-L | ✅ (bored palette) |
| 14 | Smile-Cheeks | ✅ (emotion `joy`) |
| 15 | Puff-Cheeks | ✅ (emotion `cheek_puff`, bored) |
| 16 | Smile/Sad-Open-Mouth | NOT WIRED (dormant, drivable) |
| 17 | Mouth-OpenDisgust | ✅ (emotion `disgust`) |
| 18 | Angry/Expressive | NOT WIRED (dormant, drivable) |
| 19 | Huh | ✅ (viseme) |
| 20 | Curl-Lips | ✅ (emotion `lip_curl`) |
| 21 | Stick-Out-Lip | ✅ (bored palette) |
| 22 | Ah | ✅ (viseme) |
| 23 | Mbp | ✅ (viseme) |
| 24 | Mmmm | ✅ (viseme) |
| 25 | Eh | ✅ (viseme) |
| 26 | Ai | ✅ (viseme) |
| 27 | Oooh | ✅ (viseme) |
| 28 | Shock-Oooo | ✅ (viseme) |
| 29 | Fv | ✅ (viseme) |
| 30 | FvS | ✅ (viseme) |
| 31 | S | ✅ (viseme) |
| 32 | Ee | ✅ (viseme) |
| 33 | Puff-EyebrowsRaise | ✅ (emotion `worried` + bored) |
| 34 | Confident | ✅ (emotion `confident` — HeadLook palette) |
| 35 | Worried | ✅ (emotion `worried`) |
| 36 | Disgusted | NOT WIRED as its own key (disgust rides Mouth-OpenDisgust) |
| 37 | Angry | NOT WIRED (dormant, drivable) |
| 38 | Satisfied/LittleJoy | ✅ (micro-expression) |
| 39 | Tongue Out | ✅ (`shook` overlay, tongue-out gestures) |
| 40 | Tongue Move | NOT WIRED (dormant, drivable — on Tongue mesh × `tongueScale 100`) |
| 41 | Poke-Out | NOT WIRED (dormant) |
| 42 | F/B | NOT WIRED (dormant) |
| 43 | Twist | NOT WIRED (dormant) |
| 44 | Key 6 | NOT WIRED (dormant) |
| 45 | Key 7 | NOT WIRED (dormant — the body's "Key 7"; the Tongue's "Swirl" is at the same index) |

## A3 — Path per shape (viseme / emotion / other)
| # | Name | Path |
|---|---|---|
| 0 | MouthOpen.Slightly | VISEME |
| 1 | MouthOpen.Wide | VISEME |
| 2 | Smile.L | EMOTION (joy) + hard-coded greeting @ 23% |
| 3 | Smile.R | EMOTION (joy) + hard-coded greeting @ 23% |
| 4 | JawOpening | LIP-SYNC JAW SPRING (driven by viseme open amounts, not a viseme itself) |
| 5 | MouthWidth.L | VISEME SHAPER (jaw-family) |
| 6 | MouthWidth.R | VISEME SHAPER (jaw-family) |
| 7 | Upper-Lip.R | OTHER (dormant — drivable by name) |
| 8 | Lower-Lip.R | OTHER (dormant — drivable by name) |
| 9 | Lower-Jaw-U/D | OTHER (dormant — drivable by name) |
| 10 | Template | OTHER (scaffold — never render) |
| 11 | Mouth-Open-Shock | EMOTION (`shook` — code exists, currently unwired path; F§7.3) + can also read as viseme |
| 12 | Sad-Lower-Lip-Dimples | EMOTION (sad) |
| 13 | Inflate-Cheeks-L | EMOTION (bored palette) |
| 14 | Smile-Cheeks | EMOTION (joy) |
| 15 | Puff-Cheeks | EMOTION (cheek_puff + bored) |
| 16 | Smile/Sad-Open-Mouth | OTHER (dormant) |
| 17 | Mouth-OpenDisgust | EMOTION (disgust) |
| 18 | Angry/Expressive | OTHER (dormant) |
| 19 | Huh | VISEME |
| 20 | Curl-Lips | EMOTION (lip_curl + micro) |
| 21 | Stick-Out-Lip | EMOTION (bored) |
| 22 | Ah | VISEME |
| 23 | Mbp | VISEME |
| 24 | Mmmm | VISEME |
| 25 | Eh | VISEME |
| 26 | Ai | VISEME |
| 27 | Oooh | VISEME |
| 28 | Shock-Oooo | VISEME (shock — also readable as expression) |
| 29 | Fv | VISEME |
| 30 | FvS | VISEME |
| 31 | S | VISEME |
| 32 | Ee | VISEME |
| 33 | Puff-EyebrowsRaise | EMOTION (worried, bored) |
| 34 | Confident | EMOTION (HeadLook autonomous face) |
| 35 | Worried | EMOTION |
| 36 | Disgusted | OTHER (dormant — disgust rides #17) |
| 37 | Angry | OTHER (dormant) |
| 38 | Satisfied/LittleJoy | EMOTION (micro + HeadLook palette) |
| 39 | Tongue Out | EMOTION (`shook`) + gesture overlay |
| 40 | Tongue Move | OTHER (dormant) |
| 41 | Poke-Out | OTHER (dormant) |
| 42 | F/B | OTHER (dormant) |
| 43 | Twist | OTHER (dormant) |
| 44 | Key 6 | OTHER (dormant) |
| 45 | Key 7 | OTHER (dormant) |

## A4 — Driver per shape (eLo OS via DOWN channel vs Unity local)
- **All VISEMES (A3)**: DOWN — brain writes `expression.shape_keys{name:0..1}` in `blender_state.json`; Unity applies. Source of truth for the vocabulary is Python (F§7.2).
- **All EMOTION (A3) via `emotion_event`/`expression.micro`**: DOWN — brain emits, Unity applies via receiver B1 (event) or HeadLook.FlashMicro B3.
- **HeadLook autonomous face palette (B4)**: LOCAL — Unity picks a shape from a mood-conditioned palette when no brain drive is active (`BrainExprActive` gate = 2.5s). Explicitly Unity-side "aliveness" only.
- **Greeting smile @ 23%**: LOCAL — hard-coded 1.5s smile on arrival sequence.
- **JawOpening (#4)**: LOCAL — computed from active viseme weights × `_jawViseme[shape]` × `jawOpenScale 0.7`, through a spring — brain never writes it directly.
- **`shook`/Tongue Out (#39)**: LOCAL (currently unwired — code exists in EloExpression.Shook).
- **Dormant shapes (#7–10, 16, 18, 36, 37, 40–45)**: NO driver — brain COULD address them by name; no path does today.

## A5 — Effective amplitude (final multiplier chain per path, live-scene value)
Live receiver on `eLo-ProductonReady 1.prefab` (F§0/§7 corrections; David override M).

| Channel | Chain | Live effective peak |
|---|---|---|
| Visemes on mouth/jaw meshes | `value(0..1) × blendshapeScale` | **David override = 100** (spec default 50; the 20 originally reported was the disabled duplicate) |
| Viseme on Tongue mesh | `value × tongueScale 100` | **100** |
| Emotion (event / micro) | `value × emotionScale 28`, then `min(_, emotionMaxPct 46)` | **≤ 46** (~20–28 typical) |
| HeadLook autonomous face | palette weight (0.18–0.30) capped at 46 | **≤ 46** |
| JawOpening spring | `sum(viseme × _jawViseme) × jawOpenScale 0.7 × blendshapeScale`, spring clamp 0..1.15 | peak ~**77–115** (spring can overshoot 1.0) |
| Greeting smile | hard 23 | **23** |
| Smoothing | `Lerp(cur, tgt, blendshapeSmooth 10 · dt)` ≈ **0.1s time-constant** | — |

**Real 0–1 range a shape actually reaches in the live scene:** with David's override (viseme weight = 100), the brain's 0..1 input maps ~1:1 to visible weight — a viseme value of 1.0 hits 100% mouth weight. Emotions stay capped ≤ 46. Do NOT assume 20% desktop tuning any more.

## A6 — Neutral / rest pose (per shape)
- **Neutral value of EVERY shape = 0.** eLo's authored rest has no shape driven. Rest pose = closed mouth, relaxed cheeks, no eyebrow raise. Confirmed by baked `neutral` frame on Idle_loop (M/W — one per clip, "silence" pose).
- **JawOpening rest = 0** (spring settles to 0 when no viseme is active).
- Confirming reference frame on disk: `M`'s bake references `Idle_loop/neutral` (238×410 +130+188).

## A7 — Mutually exclusive / never-valid combinations
| Constraint | Detail |
|---|---|
| Visemes vs each other | Only ONE viseme is peak at a time (`_jawViseme` chooses the max across active visemes — F§7.4); crossfaded via `blendshapeSmooth 10 · dt`. It IS legal to co-articulate two low-weight visemes during a transition (~0.1s window). |
| Smile.L/R × Sad-Lower-Lip-Dimples | Contradictory expressions, mouth geometry conflicts — never co-drive at peak. Priority: emotion event overrides HeadLook palette. |
| Smile-Cheeks × Puff-Cheeks | Same cheek anatomy — never both above 0.3. |
| Worried × Confident | Contradictory brow. Never co-drive. |
| Mouth-Open-Shock × any wide viseme (Ah/Ai/Oooh/Wide) | Both open the mouth — driving both compounds jaw. `Shook` sets Mouth-Open-Shock @1.3 + Tongue Out @1.3; must NOT be composed with a viseme in the same frame (`shook` gates lipsync as a one-shot). |
| Tongue Out × any tongue-inside viseme | Tongue Out extends the tongue past the teeth — never during F/V/S/Ee visemes. |
| Emotion cap | Emotion channel cap = **46**, hard ceiling — never composite above it (receiver enforces). |
| Priority order on shared shapes | Per F§7.5: (1) receiver visemes → (2) emotion events override if > 0.001 → (3) lip-sync jaw is authoritative on JawOpening. Then HeadLook: `SetExpr` overrides > 0.01, `SetExprFloor` = max-never-lower. `BrainExprActive` (2.5s) suppresses HeadLook autonomous flashes when the brain is driving. |
| `Template` (#10) | 🔴 **NEVER render.** Author scaffold shape — treated as null. |

---

# §B — LIPSYNC / VISEMES

## B1 — Full viseme set, phoneme mapping
The **phoneme/word → viseme mapping lives in eLo OS Python (spine), not Unity** (F§7.2 + LP). Unity receives resolved shape names.

Viseme shapes on the mesh:
| # | Shape | Sound family (spine intent) | Open amount (`_jawViseme`) |
|---|---|---|---|
| 1 | Ah | open A (father, hot) | 1.0 |
| 2 | Ai | open front (my, price) | 0.9 |
| 3 | Ee | closed high front (bee, tree) | 0.25 |
| 4 | Eh | mid open (bed, red) | 0.6 |
| 5 | Fv | labiodental (f, v — teeth on lip) | 0 (closed) |
| 6 | FvS | labiodental + hissed | 0 (closed) |
| 7 | Huh | mid open unstressed | 0.8 |
| 8 | Mbp | bilabial (m, b, p) | 0 (closed) |
| 9 | Mmmm | held m/hum | 0 (closed) |
| 10 | MouthOpen.Slightly | filler small opening | 0.5 |
| 11 | MouthOpen.Wide | filler wide opening | 1.0 |
| 12 | MouthWidth.L | side shaper (smile-like L) | 0 |
| 13 | MouthWidth.R | side shaper (smile-like R) | 0 |
| 14 | Oooh | rounded (boot, blue) | 0.7 |
| 15 | S | sibilant (s, z) | 0 (closed teeth) |
| 16 | Shock-Oooo | wide rounded surprise | 1.0 |
| 17 | Mouth-Open-Shock | shock-adjacent widened | 1.0 |

Notes: (a) The 17 originally reported in R Q1 was the `expression.shape_keys` live set (verified). (b) MouthOpen.Slightly + MouthOpen.Wide are used as "opening fillers" between phonemes. (c) The mapping table lives in the spine — request from Builder if needed on-device.

## B2 — Driver + rate
- **Driver:** eLo OS TTS pipeline → writes `lipsync_state.json` (`{active, text, _ts}`) + `expression.shape_keys{name:0..1}` fields inside `blender_state.json`. **Written ~every 50ms while speaking** (UI parity spec §9, per receiver `ReadSpeaking()` in `EloOSAvatarReceiver.cs:518-550`).
- **TTS base rate:** **175 wpm ≈ 17 chars/s** (comment in `EloOSChatTMP.cs:58`).
- **Reveal (text on bubble):** `revealCharsPerSec = 16`, matched to TTS.
- **`speechOnsetDelay = 0.18s`** — audible speech visibly starts 0.18s after `lipsync_state.json.active=true` (aligns mouth + audio + text). Enforced in `EloOSAvatarReceiver.cs:275` (`_pendingSpeakAt = realtime + 0.18`).

## B3 — Frame rate / update cadence of viseme changes
- **File cadence:** `blender_state.json` rewritten ~every 50–100ms (spine tick). Visemes update at that cadence.
- **Applied at:** Unity `LateUpdate` — every frame (60 fps or device rate).
- **Effective mouth cadence:** limited by (a) spine emit rate (~10–20 Hz), (b) blendshape smoothing (`Lerp` at `blendshapeSmooth 10 · dt` ≈ 100ms time-constant → shapes reach ~63% target in 100ms).
- **Baked reference:** M's bake set is 21 clips × faces at **24 fps** (`m_SampleRate: 24` on every clip); the head grids are baked one frame per face pose.

## B4 — Blend / interpolation between visemes
- **Model:** exponential smoothing `Lerp(now, target, blendshapeSmooth 10 · dt)`. NOT a hard cross-fade; NOT eased.
- **Time-constant:** ~0.1s. In practical terms, if two visemes swap, the transition looks ~linear over 100–150ms.
- **A viseme PERSISTS its last value** until eLo OS sends a lower value — **no auto-decay in Unity.** The spine is authoritative for the falling edge.

## B5 — Silence behaviour
- `lipsync_state.json.active=false` → `IsSpeaking=false` → jaw spring settles to 0 (JawOpening → 0).
- **`neutral` frame is authored per-clip in the bake** (M, W): each of the 21 clips has a `neutral` face — that's what you render when silent.
- Watchdog forces `IsSpeaking=false` after **20s max** (`maxSpeechSecs`) or **1.5s stale** (`lipsyncStaleSecs`, receiver:527-531).
- HeadLook autonomous face palette (bored/mood floor) may still write low-weight shapes during silence (mood floor `0.06 × max(0.4, intensity)` on the current mood shape).

## B6 — Co-articulation
- **YES — visemes CAN combine at low weights during the ~0.1s smoothing window.** Because the receiver applies each shape independently by name, two shapes with values > 0 will both write.
- **In practice**: the spine emits one dominant viseme with a smoothed decay of the previous — pure "one-at-a-time" is the intent, but the render is continuous.
- Jaw uses `max` across all active viseme open amounts (F§7.4) — so co-articulating "Ah" + "Ee" gives you jaw = max(1.0, 0.25) = 1.0 (Ah wins the jaw), while both cheek/lip shapes render additively.

---

# §C — HEAD

## C1 — Every head movement channel
Source: F§5.2 (HeadLook is the primary head author, at execution order 10, ABSOLUTE write on `c_head.x` that beats the Animator clip).

| Channel | Bone | Author | Notes |
|---|---|---|---|
| yaw (turn L/R) | `c_head.x` | HeadLook | absolute rotation |
| pitch (nod up/down) | `c_head.x` | HeadLook | absolute rotation |
| roll (tilt L/R) | `c_head.x` | HeadLook `aimRoll 0.18` fold-in | small |
| head_lean (Y-axis lean) | `c_head.x` | receiver `expression.head_lean` | `headLeanDegrees 12` per 1.0, multiplied on top |
| observe roll | `c_head.x` | DesktopBuddy observe mode | ±30°, periodic |
| nod (agreement) | `c_head.x` | HeadLook additive tilt | `nodAmp 12°`, `nodCycles 2.5`, decaying sin over ~1.4s |
| head-shake | `c_head.x` | GestureCo one-shot | procedural |
| tilt (curious) | `c_head.x` | GestureCo one-shot | procedural |
| think | `c_head.x` | GestureCo one-shot | procedural, ~0.875–1.5s |
| lookup | `c_head.x` | GestureCo one-shot | procedural |
| idle sway | `c_head.x` | EloIdleBehaviour | multiplied ON TOP of HeadLook, ONLY while moving && !speaking |
| chest trail | `c_spine_03.x`/`c_spine_02.x` | HeadLook chest follow | trails head; `chestFollow 0.32`, `chestYawLimit 20`, `chestSmooth 1.5` (always lags) |
| peek pitch | `c_head.x` | DesktopBuddy peek | fold-in |
| belly-glow micro-tilt | `c_head.x` | EloBodyGlow drop-flash | tiny fold-in |
| sit tilt | `c_head.x` | HeadLook sit fold-in | 8° when sitting |

## C2 — Ranges in degrees (per axis, min/max)
Source: F§5.2 (live code defaults on `HeadLook.cs`). HeadLook is runtime-added — the code defaults ARE what runs.

| Axis | Min | Max | Field |
|---|---|---|---|
| Yaw (head) | −92° | +92° | `aimMaxYaw 92`; hard cap `headYawLimit 92` |
| Pitch (head) | −40° | +40° (soft) / hard cap ±55° | `aimMaxPitch 40`, `headPitchLimit 55` |
| Roll | small — folded via `aimRoll 0.18` | — | max ~±10° effective |
| Brain-cue clamps (viewer-only feed) | −30° yaw / +30° yaw | ±15° pitch | `maxYawDegrees 30`, `maxPitchDegrees 15` |
| Chest yaw | −20° | +20° | `chestYawLimit 20` |
| Head lean (Y axis) | 0 | ±12° per 1.0 | `headLeanDegrees 12`, brain `expression.head_lean` 0..1 |
| Observe roll | −30° | +30° | periodic |
| Sit tilt | 0 | 8° | one-shot on sit |
| Nod (peak amplitude) | −12° | +12° | `nodAmp 12°`, decaying sin |

David live-tuned to `aimMaxYaw ≈ 80` mid-session — **NOT persisted** (in-editor Play mode edit). Use **92/40** unless the spine seat says otherwise.

## C3 — Driver per channel (brain vs local)
| Channel | Driver |
|---|---|
| Yaw target | HeadLook local, TARGET is a priority stack: (1) brain gaze cue → (2) cursor NOTICE → (3) typing (turn to chat) → (4) idle glances → (5) explore wander → (6) Calm zero. |
| Pitch target | same stack |
| head_lean | BRAIN — `blender_state.json.expression.head_lean` (0..1) |
| Nod | LOCAL one-shot triggered by receiver / agreement |
| Head-shake / tilt / think / lookup gestures | LOCAL one-shot triggered by receiver on brain commands |
| Idle sway | LOCAL only — cosmetic |
| Chest trail | LOCAL derived from head yaw |
| Observe roll | LOCAL — DesktopBuddy observe mode |

## C4 — HeadAim / mouse-follow (active? driver? limits?)
- **Active:** YES on desktop. Cursor NOTICE fires when cursor is moving; hold time `noticeHold 1.6s`.
- **Driver:** local (cursor position → screen ray → world-space aim target). Suppressed while brain gaze cue is active.
- **Limits:** same ±92 yaw / ±40 pitch as C2. `lookSmooth 2.25` (slow), `aimResponse 0.18` (eagerness), `moveAimScale 0.2` (residual track while moving so he can glance at cursor while body walks).
- **On mobile:** there is no cursor. Substitute the equivalent input (touch position, or none). The gaze channel from the spine (§D2) is the shared cross-body input.

## C5 — Head position offset relative to body origin
🔴 **The head is a RIG BONE (`c_head.x`)**, not a script-positioned object. Its POSITION comes from the skeleton hierarchy / Animator (authored). Only its ROTATION is runtime (HeadLook). **Nothing sets a head `localPosition` offset in code.**

- **To reproduce**: read `c_head.x` local position from the prefab hierarchy — that IS the head-offset-from-body, and it is Animator-modulated (via the base clip's spine curves), not scripted.
- **The desktop rig's authored head/body proportions** are what you see in the baked frames (X delivered `Idle/Walk/Run/Calm/Jump` at 24 fps from the running app — the head-to-body position IS the rig's real proportions).
- **A batch render at the authored pose gets the head POSITION right for free**; the only runtime override to reproduce is the rotation (±92 / ±40 within the priority stack).
- **Head bone transform for camera anchoring**: `headT` = `c_head.x`; `hp = Camera.main.WorldToScreenPoint(headT.position)` is what the bubble uses.

## C6 — Idle head motion
- **Amplitude:** `swayDegrees 1.2` on X + Z, `1.2 × 0.6 = 0.72°` on Y (EloIdleBehaviour).
- **Period:** `swayEvery 0.7–1.6s` random per-interval.
- **Smoothing:** `swaySmooth 2.25`.
- **Procedural** (not a clip). Multiplied on top of HeadLook. Only fires while moving && !speaking.
- **Additional resting drift**: Idle_bones clip animates the head slightly (108 bones incl. head — the resting animation itself has a subtle motion, so "still" isn't frozen; see I2 — Idle loop is 73 frames ≈ 3.04s at 24 fps for the seamless in-app loop).

---

# §D — GAZE / EYES

## D1 — Gaze channels + ranges
🔴 **eLo has NO EYES.** The Identity Kernel rule: no eye geometry / no eye textures / no eye-look. "Gaze" is expressed by **head direction alone** (yaw + pitch).

- **Gaze channels on the DOWN stream** (`blender_state.json.gaze`): `{mode, point, win_id, weight, yaw, pitch, active}`.
- **Ranges:** yaw ±92°, pitch ±40° — see C2. Same limits as the head.

## D2 — What gaze targets
- **`gaze.mode`:** `"follow_cursor"` / `"look_at"` (point in screen or world) / `"look_at_window"` (a specific window / surface) / `"look_at_camera"` / `"free"`.
- **`gaze.point`:** target coords (screen normalized or world).
- **`gaze.win_id`:** target window / surface id (for embodied nav — SP-1/2 chain).
- **`gaze.weight`:** blend weight 0..1 for how strongly to follow the target.
- **`gaze.active`:** master enable.
- **On mobile:** targets that transfer = cursor→touch/none (drop), look-at-camera (front-on), look-at-window (irrelevant — no windows), look-at-user (front-on). Free = idle glances.

## D3 — Blink
🔴 **NO BLINK.** No eyes → no blink. Do NOT synthesize one on mobile. NONE.
- The rig ships `eye.L` / `eye.R` BONES (not blendshapes) — legacy from an earlier design. HeadLook has a residual "eye-pop" in `EloExpression.Shook` **that predates the NO-EYES rule** — treat as legacy, do not render eyes.

## D4 — Eye movement independent of head
NONE. See D3. Any perceived "eye" motion is head rotation.

## D5 — Reconciliation: eLo has no eyes vs the D1–D4 "gaze" channel
Reconciled cleanly in F§0.5 Tier 2: **eLo's gaze IS his head direction.** The `gaze.*` fields in the DOWN stream drive HeadLook (yaw/pitch/aim target). There is no eye channel. Whenever the brain says "look at X," Unity turns the head toward X — that is the visible gaze.

For mobile: implement gaze by rotating the head bone (or, if only rendering static frames, pre-render the head-yaw grid). MT already has `Idle_head` and `Sit_hold_head` grids baked exactly for this (M).

---

# §E — BODY / POSE

## E1 — Every body animation state (by state name in the live Animator controller)
Source: F§3.2 + F§4.3. **Live controller = `Assets/eLo/eLo.controller`.**

Base layer (Layer 0):
| # | State | Clip | Length | Loops? |
|---|---|---|---|---|
| 1 | Idle | Idle_bones | 1.792s (43f @24) | no (Idle→Idle_blend→Idle micro-loop) |
| 2 | Idle_blend | Idle_bones | 1.792s | no |
| 3 | Walk | Walk_bones | 0.833s (20f) | YES |
| 4 | Run | Run_bones | 0.750s (18f) | YES |
| 5 | Gun-Check | Gun-Check_bones | 1.208s (29f) | no |
| 6 | CalmEnter | CalmEnter_bones | 0.500s (12f) | no |
| 7 | CalmLoop | CalmLoop_bones | 0.375s (9f) | YES |
| 8 | CalmExit | CalmExit_bones | 0.542s (13f) | no |
| 9 | GunFire-Run | GunFire-Run_bones | 0.875s (21f) | no |
| 10 | Gun-Jump-Fire | Gun-Jump-Fire_bones | 1.708s (41f) | no |
| 11 | eLo_LongJ | eLo_LongJ_bones | 0.833s (20f) | no (has hold-loop band 0.5–0.8) |
| 12 | LongJ_Land | LongJ_Land (FBX) | 0.375s (9f) | no |
| 13 | Parkour | Parkour (FBX) | 0.958s (23f) | no |

Masked layers:
| # | Layer | State | Clip @ speed | Purpose |
|---|---|---|---|---|
| 14 | LegsWalk (LegsMask) | Walk | Walk_bones @ 2.5× | legs walk while body holds another pose (e.g. dragged) |
| 15 | GunArm (GunArmMask) | GunFire-Arm | GunFire-Run_bones @ 1× | arm fires over base Idle. **Out of mobile scope.** |
| 16 | SitLegs (LegsMask) | Sit | CalmLoop_bones @ 0.45× | sit legs over base Idle |
| 17 | SitLegs | SitExit | CalmExit_bones @ 1× | get-up |
| 18 | WaveArm (WaveArmMask) | Wave | eLo_LongJ_bones @ 1× | wave (used as clip-source; live wave is bone-driven, F§5.3) |

Special (code-driven, not a controller state):
| # | State | Trigger | Notes |
|---|---|---|---|
| 19 | Sit-hold (commanded) | `EnterSit` → SitInPlace | base Idle 0.5s + SitLegs `Sit` 0.25s, `animator.speed 0.4` |
| 20 | Reflex sit | roam gate | SitLegs `Sit` 0.25s |
| 21 | Get-up | `BeginSitExit` | SitLegs `SitExit` 0.2s, weight→0 over 0.7s |
| 22 | Drop-off / warp-out | biStepOut | WarpOut ~0.4s then hide, OR step-to-bottom + PlayJump off edge |
| 23 | Return-from-top | WakeFromExit | drop in from top (1.22y) + PlayJump + step ledge-to-ledge |
| 24 | Return-from-runoff | WakeFromExit | spawn off-screen + RUN in, then Idle |
| 25 | Drag/carry | grab | `SetDragPose(true)`: eLo_LongJ mid-loop 0.5→0.8, `dragSideYaw 35°`, masked LegsWalk wiggle |
| 26 | Drop (release) | ungrab | CrossFade Idle 0.15s |
| 27 | Grabbed limb (limp) | GrabbedLimb "l"/"r" | that leg FK blends limp (EloGrabLimb §5.6) |
| 28 | Wave (greeting) | `Wave()` | bone-driven ArmWave (§F5.3) + head-roll — NOT a clip |
| 29 | Arrival/spawn | ArrivalSequence | Idle + greeting wave/smile |
| 30 | Idle-fire | combat close-range | base Idle + GunArm weight→1. **Out of mobile scope.** |
| 31 | Fire-jump (lateral) | `_fireJumpNext` hop | SuppressGun + PlayGunJumpFire |

**Mobile scope** (per David / MT bake): **Idle · Walk · Run · Calm(Enter/Loop/Exit) · Jump (eLo_LongJ) · Wave · Sit(hold) · Idle_head grid · Sit_hold_head grid**. **OUT of mobile scope:** all Gun states, Parkour, LongJ_Land, drag/carry, grabbed-limb, warp-out/return.

## E2 — Idle / breathing
- **Amplitude / period source:** procedural, not clip-baked. `animator.speed` breathes via `Lerp(0.35, 0.6, sin·BreathRate)`.
- **BreathRate per mood:** joy 0.30 · worried 0.45 · anger 0.38 · **neutral 0.22** (Hz-ish — the `sin` argument multiplier).
- **Which bones/shapes:** breathing modulates the whole Idle clip's playback speed (so the spine/chest oscillation in Idle_bones expands/contracts with it). No specific bone is written.
- **Bake for mobile:** MT's baked **Idle_loop 73 frames** (I2) = one full period at 24 fps (≈ 3.04s) — that IS the seamless idle in-app loop with the breathing baked in.

## E3 — Sit · stand · perch · lean (the full pose set)
| Pose | Trigger | Rendering |
|---|---|---|
| **Stand** (default) | none — Idle | Idle_bones clip |
| **Sit-hold** | brain sit / rest / ground command | base Idle + SitLegs `Sit` weight 1 (masked); `animator.speed 0.4`; tilt 8° |
| **Reflex sit** | roam gate (autonomous) | SitLegs `Sit` 0.25s crossfade; same masked pose |
| **Sit-on-window** | `intent = sit_on_window` | travel to app window + Sit |
| **Get-up** | `BeginSitExit` | SitLegs `SitExit` 0.2s crossfade, weight→0 over 0.7s |
| **Perch** | `intent = climb_height` | travel + perch at nearest height (Idle at perch position) |
| **Lean** | expression.head_lean | HeadLean channel (see C1) — head only, no body pose change |
| **Calm/meditation** | `motion.mode = calm_enter/loop/exit` | CalmEnter → CalmLoop → CalmExit clips + `animator.speed 0.3` + envt VFX (§I) |
| **Dragged (side-on)** | grab | eLo_LongJ mid-loop 0.5→0.8, `dragSideYaw 35°` |

## E4 — Arm channels
| Channel | Bones | Author | Range/Params |
|---|---|---|---|
| Wave (right arm) | arm_stretch.r, arm_twist.r, c_arm_twist_offset.r, forearm.r (+stretch/twist), hand.r | ArmWave (order 15, absolute) | raise 95° axis (-1,-1,1), + `raiseForwardDeg 18°`, elbow `elbowBend 62°` @ frac 0.6, rock 10° @ 1.4Hz, hand counter-flick, envelope rise 0.4 / hold 1.9 / fall 0.4 = **2.7s total** |
| Reach (right, +left if two-handed) | R arm chain + fingers index1/pinky1/thumb1 (rotation curl) | ArmReach (order 15, absolute) | `reachAngle 55°`, `leanAngle 22°`, `fingerCurl 45°`; envelope reach 0.35 / hold 0.5 / return 0.45 = **1.3s** |
| Gun-arm fire (right) | R arm chain | GunArm masked layer | out of mobile scope |
| Idle arm sway | shoulders, arms | Idle_bones clip | authored subtle motion |
| Walk/run arm swing | shoulders, arms | Walk_bones / Run_bones clips | authored |
| Drag / limp | forearms | contact/pose-driven | dragged pose = eLo_LongJ mid |

## E5 — Leg channels
| Channel | Bones | Author | Range/Params |
|---|---|---|---|
| Walk cycle | c_thigh_ik.l/r, c_leg_ik.l/r, foot.l/r, toes | Walk_bones clip | 20f @ 24fps, loop; also masked at 2.5× via LegsWalk |
| Run cycle | same | Run_bones clip | 18f @ 24fps, loop |
| Jump (whole) | full leg IK chain | eLo_LongJ_bones (327-bone superset) | 20f + hold-loop band 0.5–0.8 |
| Parkour | same | Parkour FBX | out of mobile scope |
| Sit legs | c_thigh_fk, c_leg_fk, foot | SitLegs masked layer `Sit` (CalmLoop_bones @ 0.45×) | crossed / seated pose |
| Limp (grabbed) | grabbed side FK | EloGrabLimb (order 0) | `Slerp(current, restAtLoad, relaxWeight 0.85)`, `relaxSpeed 5` |
| Foot IK | native Unity | Animator IK pass | OFF (all layers `IKPass=off`) |

## E6 — Torso / spine
| Channel | Bones | Author | Range |
|---|---|---|---|
| Chest bend (breathing) | c_spine_01, _02, _03 | Idle_bones clip | subtle authored motion |
| Chest yaw trail | c_spine_03.x/_02.x | HeadLook chest follow | `chestFollow 0.32`, `chestYawLimit 20°`, `chestSmooth 1.5` — always lags head |
| Chest OFF (states) | — | HeadLook | chest follow disabled while moving / calm / sitting |
| Torso twist | authored per clip | Animator | out-of-band |
| Peek pitch | full body implicit | DesktopBuddy peek | fold-in |

## E7 — Scale / squash-stretch (`scale_cmd`)
- **Yes**, this is a real channel — `EloSquashStretch` (order 0, Update — writes ROOT localScale, not a bone).
- **Volume-preserving, pivoted at feet:** `Factor = (1/√y, y, 1/√y)` — X == Z so a yaw can't shear.
- **Range:** `y` clamped `1 ± maxAmount 0.3` → up to **1.3× tall / 0.77× short**.
- **Spring:** stiffness 90, damping 12.
- **Impulses:** anticipate 0.10 (crouch before launch) · jumpLaunch 0.12 (stretch up) · jumpLand 0.10 (squash) · hopAmount 0.09 · speechAccent 0.05 (tiny stretch while speaking).
- **Mood-modulated:** impulses × mood `bounceAmp` (0.3–2).
- **On mobile:** implement as a root scale on top of the baked frames — critical for jump/land reads and for the tiny speech accent.

---

# §F — LOCOMOTION / MOVEMENT

## F1 — Every movement type (with in/out of mobile scope)
| # | Type | Trigger | Scope |
|---|---|---|---|
| 1 | Walk | brain locomotion + travel distance ≤ walk threshold | **IN mobile** |
| 2 | Run | brain locomotion + travel distance > walk threshold OR run intent | **IN mobile** |
| 3 | Jump (`eLo_LongJ`) | `PlayJump()` — jump/celebrate/drop-fall/steps | **IN mobile** (small jumps only per David) |
| 4 | Wall-jump | Parkour + ~40% hops | OUT (parkour) |
| 5 | Fire-jump | `_fireJumpNext` lateral hop | OUT (combat) |
| 6 | Roam | brain intent = `explore/roam/wander/patrol` | **IN mobile** (Walk/Run + Jump — no window-hop physics needed for mobile) |
| 7 | Traverse (window-to-window) | brain intent = `jump_to_app/go_to_app` | OUT (desktop only — no windows on mobile) |
| 8 | Exit (leave for privacy) | intent = `step_out/leave/hide/give_space` | OUT (desktop only) |
| 9 | Return (from top / runoff) | WakeFromExit | OUT (desktop only) |
| 10 | Climb / perch | intent = `go_top/climb/climb_height` | OUT (desktop only) |
| 11 | Drag/carry follow | grab | OUT (mobile has no drag pointer) |
| 12 | Sit-travel (sit_on_window) | intent | OUT (window-specific) |
| 13 | Static Idle | default | **IN mobile** |
| 14 | Calm loop | `motion.mode = calm_loop` | **IN mobile** |

## F2 — Per type: speed, duration, easing
| Type | Speed | Duration | Easing |
|---|---|---|---|
| Walk | `walkSpeedPx = 90 px/s` (desktop reference) → `animator.speed = ±Clamp(walkSpeedPx / walkAnimRefPx, 0.3, 2)` | continuous (state) | crossfade in `locoFade 0.12s` |
| Run | `runSpeedPx` (2–3× walk range; controller `animator.speed 1.0`) | continuous | 0.12s crossfade |
| Jump | 1s ballistic (approx); clip 0.833s + optional hold-loop between norm 0.5–0.8 | until land | 0.08s crossfade in |
| Wall-jump / Parkour | controller default | 0.958s (Parkour) → 0.375s (LongJ_Land) | 0.08–0.12s |
| Fire-jump | controller default | 1.708s (Gun-Jump-Fire) | 0.12s |
| Roam | inherits Walk/Run speeds | until arrive | Walk/Run cadence |
| Traverse | ballistic hop between windows | per-hop | 0.08s crossfade |
| Exit | WarpOut ~0.4s OR step-off-edge PlayJump | 0.4s to hidden | linear (WarpOut) |
| Return | drop 1.22y from top + PlayJump ledge-to-ledge OR run-in from off-screen | until Idle | 0.08s per step / 0.12s run |
| Climb / perch | step by step, PlayJump | until at perch | 0.08s crossfade |
| Sit-travel | Walk/Run then Sit | until sit | 0.25s sit crossfade |
| Idle | `Lerp(0.35, 0.6, sin·BreathRate)` (breathing oscillation on animator.speed) | continuous | continuous |
| Calm | `animator.speed 0.3` | phase-driven (enter → loop → exit) | 0.5s crossfade per phase |

## F3 — Brain-driven vs local
| Type | Driver |
|---|---|
| Walk / Run | LOCAL (DesktopBuddy) — brain provides intent + target, Unity picks Walk vs Run and drives translation |
| Jump | LOCAL (DesktopBuddy `PlayJump`) — brain requests via intent, local computes arc |
| Roam | LOCAL — brain intent (`explore/roam/wander`) triggers autonomous window-hop |
| Idle | LOCAL — default state; brain sets mood/mode which modulates breathing |
| Calm | BRAIN — `motion.mode = calm_enter/loop/exit` |
| Sit | BRAIN — sit intent commanded |
| Reflex sit | LOCAL — roam gate autonomous |
| Wave | BRAIN — `wave` trigger |
| Exit / Return | BRAIN — `step_out/return` intents |
| Facing yaw | LOCAL — DesktopBuddy `DirectionalYaw`/`FacingYaw` from travel delta |
| Head aim | mixed — priority stack (brain gaze → cursor → typing → idle) |

## F4 — Transitions between movement states
| Transition | Duration | Blend |
|---|---|---|
| Idle → Walk | 0.12s | CrossFadeInFixedTime |
| Walk → Run | 0.12s | crossfade (no blend tree) |
| Walk/Run → Idle | 0.12s | crossfade |
| Idle → Jump | 0.08s | crossfade |
| Jump → Idle (on land) | 0.15s | crossfade (via LongJ_Land where used) |
| Idle → Sit (masked) | 0.5s base + 0.25s SitLegs weight | additive |
| Sit → Get-up | 0.2s SitExit + 0.7s weight fade | additive |
| Anything → CalmEnter | 0.5s | trigger `Calm` |
| CalmEnter → CalmLoop | 0.3s (exit 0.9) | fixed |
| CalmLoop → CalmExit | 0.5s | script CrossFade |
| CalmExit → Idle | 0.3s (exit 0.9) | fixed |
| Idle → Wave (bone-driven, not a clip) | envelope 0.4s rise | procedural |
| Idle → Drag pose | 0.12s | eLo_LongJ mid-loop |
| Drag → Idle (release) | 0.15s | crossfade |
| Parkour → LongJ_Land | 0.12s | fixed |
| Gun-* → Idle | 0.30s | fixed |
| **Facing yaw at any moment** | `LerpAngle(cur, tgt, faceSmooth 6 · dt)` ≈ 0.17s time-constant | root RotateAround-feet |
| **Squash spring** | stiffness 90, damping 12 | spring |

## F5 — What movement looks like from a fixed camera (does he leave frame?)
- **On desktop:** the camera moves with eLo (`DesktopBuddy` reframes each measure — `cam.orthographicSize = eloWorldHeight / (2 × screenHeightFraction 0.42)`) — so he does NOT leave frame during Walk/Run. Jump can leave frame briefly (vertical peak > frame height).
- **On mobile widget (fixed camera):** he WILL leave frame on any translation — the widget is a stationary viewport onto a single-cell composition. **Recommended:** render Walk/Run/Jump as **in-place clips with facing yaw** — no root translation, no camera move. That is exactly what X's frame exporter produces (facing yaw applied but position centered).
- **Jump vertical:** the tallest baked frame (`Jump`) leaves **137px top headroom** at MT's on-device framing (238×410 subject in 512-tall render); no clipping across the 240 checked frames (M).
- **Facing changes DO NOT translate:** `RotateAround(feetAnchor, worldUp, delta)` pivots on feet — a turn keeps him centered.

---

# §G — EMOTION → VISUAL MAPPING

## G1 — Every emotion value the DOWN channel can carry
Sources: F§7.3 (four sub-mechanisms), R Q1 (emotion vocab), P§6 (mood palette).

**Two carrier fields:**
1. **`expression.micro`** — a single word, edge-triggered by `expression.micro_ts`. Vocabulary:
   - `joy`
   - `smile` (alias of joy)
   - `Satisfied` / `LittleJoy`
   - `Confident`
   - `worry` / `Worried`
   - `Curl-Lips` (`lip_curl`)
   - `Mouth-OpenDisgust` (`disgust`)
   - `Sad-Lower-Lip-Dimples` (`sad`)
   - `bored` (a palette, not a single word)
   - `shook` / `shocked` (code exists, unwired path)
   - `greeting` (auto — hard-coded)
2. **`emotion_event`** — edge-triggered event `{type, ts}`. Vocabulary:
   - `cheek_puff` / `puff` → Puff-Cheeks
   - `disgust` → Mouth-OpenDisgust
   - `sad` → Sad-Lower-Lip-Dimples
   - `lip_curl` → Curl-Lips

**Plus mood as a state field** (`state.emotion` / `state.emotional_state` — see G5). Full mood vocab in P§6 (~30 named moods across 8 valence bands).

## G2 — Exactly which shapes / animations / colours each drives, at what weight
Source: F§7.3 (weights from HeadLook code + receiver).

| Emotion input | Shapes (weight per shape) | Animation | Colour (via MoodPalette when applied to belly-glow / material) |
|---|---|---|---|
| joy / smile | Smile.L 0.24 · Smile.R 0.24 · Smile-Cheeks 0.24 | (none — face only) | 330°/0.62/0.98 bright pink (or +10 magenta) |
| Satisfied / LittleJoy | Satisfied/LittleJoy 0.22 | — | +7 confident band 288°/0.58/0.92 purple |
| Confident | Confident 0.22 | — | 288° purple |
| worry / Worried | Worried 0.22 · Puff-EyebrowsRaise 0.22 | — | −4 contracting 42°/0.82/0.92 yellow-orange |
| Curl-Lips / lip_curl | Curl-Lips 0.22 | — | (band-dependent) |
| disgust | Mouth-OpenDisgust 0.20 (event: attack 0.25 / hold 1.0 / decay 1.5s) · Curl-Lips (co-driven in emoji React) | — | −4 band |
| sad | Sad-Lower-Lip-Dimples 0.20 (event curve) | slower breathing | −10 collapsed 20°/0.14/0.40 grey-brown |
| cheek_puff / puff | Puff-Cheeks 0.30 | — | (mood-dependent) |
| shook / shocked | Mouth-Open-Shock 1.3 + Tongue Out 1.3 (currently unwired — code in `EloExpression.Shook`) | — | — |
| greeting (auto) | Smile.L 23% · Smile.R 23% (hard 1.5s) | wave | +10 pink |
| bored | Puff-Cheeks 0.30 · Inflate-Cheeks-L 0.25 · Stick-Out-Lip 0.24 · Curl-Lips 0.22 · Puff-EyebrowsRaise 0.30 · Satisfied 0.22 | — | 32°/0.84/0.90 orange |
| speaking (mood) | (none — the face is viseme-driven while speaking) | animator speech accent | 330°/0.55/0.98 warm pink |
| thinking (mood) | (none — HeadLook can flash Satisfied/Confident) | orbit dot | 205°/0.58/0.93 light blue |
| calm / serene / peace / grounded / quiet | (none unique — HeadLook mood floor) | Calm state | 180°/0.48/0.90 cyan-teal |
| neutral / relaxed / idle / waiting | (none) | Idle | **140°/0.52/0.86 green (the baseline)** |
| tired / resting / sleeping | (none) | Idle slower | 155°/0.36/0.70 muted teal-green |
| frustrated / irritated | (none unique) | — | 52°/0.78/0.92 yellow |
| anxious / overwhelmed | Worried 0.22 · Puff-EyebrowsRaise 0.22 | — | 42° yellow-orange |
| doubt / bored | bored palette | — | 32° orange |
| anger / angry | (Angry #37 dormant) | — | 2°/0.86/0.80 red |
| hate / rage / jealousy | — | — | 358°/0.85/0.58 dark red |
| guilt / depressed / lost | — | — | 300°/0.12/0.48 grey-mauve |
| fear / grief / sad / heavy | Sad shapes when sad | — | 20°/0.14/0.40 grey-brown |
| shame / powerlessness | — | — | 0°/0.04/0.22 near-black |

**Emotion-event envelope (event path):** attack 0.25s → hold 1.0s → decay 1.5s.
**PlayFace envelope (emoji path):** attack 0.18s → hold (arg) → decay 0.5s.
**Micro-flash envelope (HeadLook.FlashMicro):** 40–500ms flashes.
**Emotion cap on ALL paths:** 46 (`emotionMaxPct`).

## G3 — `intensity` — how it scales the above
- `state.intensity` (0..1) modulates the mood-floor magnitude on the face: `mood_floor = 0.06 × max(0.4, intensity)` → typical floor 0.024–0.06 on the current mood's canonical shape.
- **Does NOT scale the event/micro peaks** — those are fixed by the palette.
- **Also feeds `animator.speed` breathing amplitude** via `BreathRate`.
- **Feeds squash-stretch impulse magnitude** (`bounceAmp` mood-dependent 0.3–2 range).

## G4 — `pacing` (what it changes)
- `motion.speed` (0.1–2.0, default 0.6) → animator playback speed for the current non-run reaction clip.
- `voice_pacing` (from `presence_plan`) → TTS rate (spine side) → indirectly changes reveal rate and mouth cadence.
- **Does NOT change animation clip choice** — pacing modulates the playing clip.

## G5 — `mood` (live value = `"open"`) — full value set + visual effect
🔴 **Two "mood" fields — do not conflate:**

1. **`state.emotional_state` / `state.emotion`** — the VALENCE mood, drives colour + face floor. Full palette in P§6 (~30 moods across 8 bands from +10 expansive to −10 collapsed). Example current live: `"joy"`.
2. **`presence_plan.expression_profile`** = `"open"` — a HIGH-LEVEL BEHAVIOURAL PROFILE, not a mood word. Vocab (from spine): `open` / `focused` / `guarded` / `withdrawn` / (extensible). Effect: gates HeadLook autonomous palettes and expressiveness. `open` = full palette enabled, higher amplitude autonomous face + more idle glances.

**MoodPalette explicit-word table** (verbatim, MoodPalette.cs HSV values — the visual effect column is the belly-glow / material colour applied to eLo's body-inside glow, phone orb, and Dynamic Island):

| Band | Moods | H, S, V | Visual |
|---|---|---|---|
| +10 expansive | joy, love, freedom, gratitude | 322°, .68, .98 | vivid magenta |
| | happy, excited, delight, celebrating | 330°, .62, .98 | bright pink |
| speaking (state) | speaking | 330°, .55, .98 | warm pink |
| +7 confident | confidence | 288°, .58, .92 | purple |
| | optimistic, trust, connection, hopeful | 268°, .56, .92 | indigo-purple |
| | reflection, dreaming, recalling | 262°, .44, .86 | soft indigo |
| +4 reaching | curious, wonder, hope | 222°, .55, .94 | luminous blue |
| | focused, thinking, determined, alert | 205°, .58, .93 | light blue |
| | content, satisfied, listening, present | 192°, .52, .92 | cyan-blue |
| +1 settled | calm, serene, peace, grounded, quiet | 180°, .48, .90 | cyan-teal |
| **0 baseline** | **neutral, relaxed, idle, waiting** | **140°, .52, .86** | **green — the resting colour** |
| −1 dimming | tired, resting, sleeping, apathy | 155°, .36, .70 | muted teal-green |
| | frustrated, irritated | 52°, .78, .92 | yellow |
| −4 contracting | worried, anxious, overwhelmed | 42°, .82, .92 | yellow-orange |
| | bored, doubt | 32°, .84, .90 | orange |
| −7 hot negative | anger, angry | 2°, .86, .80 | red |
| | hate, rage, jealousy | 358°, .85, .58 | dark red |
| −10 collapsed | guilt, depressed, lost | 300°, .12, .48 | grey-mauve |
| | fear, grief, sad, heavy | 20°, .14, .40 | grey-brown |
| | shame, powerlessness | 0°, .04, .22 | near-black |

Unknown mood → returns false; fall back to neutral. **Idle baseline = green (h140).** Belly-glow ambient alpha 0.28, breathing at `pulseSpeed 0.9`; boost to `maxAlpha 0.6` on hover/attention (P§6).

---

# §H — TIMING & TRANSITIONS

## H1 — Every transition duration, in ms
| Transition | ms |
|---|---|
| Locomotion (Idle ↔ Walk ↔ Run) | 120 |
| Jump crossfade in | 80 |
| Jump land crossfade | 150 |
| Sit crossfade | 250 (base) / 500 (base clip) + weight ramp |
| Sit-exit weight fade | 700 |
| CalmEnter crossfade in | 500 |
| CalmEnter → CalmLoop | 300 |
| CalmLoop → CalmExit (script) | 500 |
| CalmExit → Idle | 300 |
| Gun-* → Idle | 300 |
| Idle → Idle_blend | 250 |
| Parkour → LongJ_Land | 120 |
| Drag pose → Idle (release) | 150 |
| Wave rise / hold / fall | 400 / 1900 / 400 (envelope) |
| Reach rise / hold / return | 350 / 500 / 450 |
| Emotion event attack / hold / decay | 250 / 1000 / 1500 |
| PlayFace attack / hold / decay | 180 / (arg) / 500 |
| Micro-flash | 40–500 |
| Blendshape smoothing time-constant | ≈ 100 |
| Facing smoothing time-constant | ≈ 170 (`faceSmooth 6`) |
| Head aim smoothing time-constant | ≈ 440 (`lookSmooth 2.25`) |
| Chest follow smoothing | ≈ 670 (`chestSmooth 1.5`) |
| Idle sway smoothing | ≈ 440 (`swaySmooth 2.25`) |
| Speech onset delay (audio-align) | 180 (`_pendingSpeakAt +0.18`) |
| Speech watchdog max | 20000 (`maxSpeechSecs`) |
| Speech stale watchdog | 1500 (`lipsyncStaleSecs`) |
| Reveal `charsPerSec` | 16 chars/s (≈ 62 ms/char) |
| UI ladder (ICON/TALK/FULL) | 250 (`DurBase`) |
| UI collapse pulse | 150 (`DurFast`) |
| UI slow | 350 (`DurSlow`) |
| Bubble entry | 250 |
| Bubble exit | 0 (hard hide) |
| Bubble minimum lifetime | 6000 (floored by `text.Length / 13 + 2`) |
| Glow ease time-constant | ≈ 170 (`6·dt`) |
| Glow hue cross-fade | ≈ 400 (`glowFadeSpeed 2.5`/s → 400ms for full cycle segment) |
| Ambient VFX fade | 1500 (`fadeSecs`) |
| Squash-stretch spring | stiffness 90 / damping 12 (natural period ≈ 200–300ms) |
| Jaw spring | stiffness 90 / damping 13 |
| Belly glow fade in / out | 4000 / 2500 |
| Cursor NOTICE hold | 1600 |
| Observe interval | 14–32 s, 50% chance |
| Meditation animator.speed | 0.3 (300ms per beat effectively) |
| `blendshapeSmooth 10 · dt` | ≈ 100 ms time-constant |
| Idle glance interval | 2500–6000 |

## H2 — Easing curves
- **UI (bubble, ladder):** ease-out cubic (`FlowTokens`).
- **Facing yaw:** linear `LerpAngle`.
- **Head aim:** exponential smoothing `Slerp(current, target, aimResponse 0.18 · dt · f(lookSmooth))`.
- **Blendshapes:** exponential `Lerp(now, tgt, blendshapeSmooth 10 · dt)`.
- **Emotion event:** attack/hold/decay curve (linear segments per phase).
- **PlayFace:** attack/hold/decay linear.
- **Squash-stretch:** critically-damped spring (stiffness 90 / damping 12).
- **Jaw:** spring (stiffness 90 / damping 13, clamp 0..1.15 — allows small overshoot).
- **Glow alpha:** organic half-sine × half-Perlin (`GlowOsc`).
- **Reveal:** linear character reveal.
- **Chest follow:** exponential `chestSmooth 1.5`, always lags.
- **Ambient VFX fade:** linear over `fadeSecs 1.5s`.

## H3 — How a new DOWN state is blended in
- **Motion animation change:** `CrossFadeInFixedTime` with the duration in F§4.3 (0.08–0.5s).
- **Expression change:** blendshapes lerp toward new value at `blendshapeSmooth 10 · dt` (~0.1s TC). **NO snap** unless target ≤ 0.001 (then `SetBlendShapeWeight(0)`).
- **Gaze target change:** HeadLook priority stack resolves each frame; smooth via `lookSmooth 2.25` (~0.44s TC).
- **Mood colour change:** MoodPalette hue eases at `glowFadeSpeed 2.5`/s.
- **State (mode) change:** e.g. idle → calm — animator trigger `Calm`, 0.5s crossfade.
- **Facing change (travel direction flip):** `LerpAngle` at `faceSmooth 6 · dt` (~0.17s TC).
- **Squash-stretch impulse:** spring absorbs — no snap.

## H4 — Poll / tick rate the receiver reads at
- **Confirmed:** **250 ms** (`state_writer.py:7`) — brain writes `blender_state.json` every 250ms baseline.
- **Lipsync file** — written more often, **~50 ms** while speaking (per `EloOSAvatarReceiver.ReadSpeaking()` file-watch cadence).
- **Emotion events** — timestamped in `blender_state.json`; receiver polls on the same 250ms cadence and edge-triggers on ts change.
- **Unity read cadence** — Update/LateUpdate every frame (60fps typical); reads are cached and only re-parsed when file mtime changes.

---

# §I — 🔴 THE RENDER KIT (this is what makes the images correct)

## I1 — Exact prefab / scene / GameObject path
- **Scene:** `Assets/Scenes/eLoBuddy.unity`
- **Live avatar:** prefab instance of `Assets/eLo/eLo-ProductonReady 1.prefab` (`m_IsActive` on, 32 scene refs, HeadLook + FollowHead + BlendShapeTester on the instance). GUID matches scene `a1772aef…`.
- 🔴 **DO NOT render** the disabled duplicate `GameObject "eLo"` at fileID `3420545965625376066` (`m_IsActive: 0`). Its inline receiver has empty `shapeMeshes` and its body-mesh GUID (`4f1981d6…`) is missing from the project. All prior `blendshapeScale=20 / height=5.25 / ×10` numbers were read off that dead rig — retired.
- **Root path:** `eLo-ProductonReady 1/rig/` (Auto-Rig-Pro rig). Body-mesh path: `eLo-ProductonReady 1/eLo-BodyxHead w/Mouth`. Head bone: `c_head.x`.

## I2 — Scene vs prefab differences
Enumerate every override on the live avatar (F§0, F§2, F§7):

| Field | Prefab default | Scene (effective on live avatar) |
|---|---|---|
| `blendshapeScale` | 50 | **100 (David override, 2026-08-22 per M)** — was 50 in prefab, was 20 on the disabled duplicate |
| `blendshapeSmooth` | 10 | 10 (unchanged) |
| `tongueScale` | 100 | 100 (unchanged) |
| `emotionScale` | 28 | 28 (unchanged) |
| `emotionMaxPct` | 46 | 46 (unchanged) |
| `jawOpenScale` | 0.7 | 0.7 (unchanged) |
| `jawStiffness` / `jawDamping` | 90 / 13 | 90 / 13 (unchanged) |
| `lipsyncJaw` | on | on |
| Root rotation | (270°, 180°, 0°) | (270°, 180°, 0°) — same (the 270°X is why the rig reads lying-down cold) |
| Root scale | 1 | 1 (no ×10) |
| Child scale | 1 | 1 (no ×10) |
| Camera `orthographicSize` (serialised) | 6.25 | **runtime-computed** by `SizeToScreen` = `eloWorldHeight / (2 × 0.42)` ≈ **4.45** (live rig height 3.736) |
| `cullingMode` | 1 (CullUpdateTransforms) | **forced `AlwaysAnimate` at runtime** (`EloOSAvatarReceiver.Awake:288`) |
| `shapeMeshes` list | (prefab default) | **5 SMRs populated** on live receiver |
| HeadLook / FollowHead | not on prefab as fixed | added at runtime with code defaults (see C2) |
| Animation source | `eLo-AnimationNLA-FinalFixedDONOTTOUCH` | same |

## I3 — Camera (position, rotation, FOV, ortho/perspective, distance)
Live camera (verified by C1, F§2, M): **ORTHOGRAPHIC.**
| Field | Value |
|---|---|
| Projection | Orthographic |
| `orthographicSize` (runtime) | 3.736 / (2 × 0.42) ≈ **4.45** for live rig (serialized 6.25 is stale — refers to the retired 5.25 tall rig) |
| Near plane | 0.01 |
| Far plane | 1000 |
| Camera position | eye position relative to eLo, positioned by `DesktopBuddy.SetupCamera` — **framing formula is the primary spec, not absolute XYZ** |
| Camera rotation | dead-on (looks down `+Z` toward eLo) for standard renders; profile shots turn the SUBJECT (facing yaw), not the camera |
| FOV | N/A (ortho) |
| Distance | ortho → distance affects clipping only, not size. Use any distance that keeps eLo inside near/far. |
| Framing formula (invariant) | `orthographicSize = eloWorldHeight / (2 × screenHeightFraction 0.42)` — Tier-2 invariant is **the 0.42 fraction**, not the world height. |
| **M's deterministic-camera fix** (final) | Frame from `sharedMesh.bounds` (base-mesh, pose/blendshape/skin-independent) transformed by renderer matrix — NOT `smr.bounds` (which lags Animator by a frame). Enforced in `EloFrameExporter.SetupCamera`. This is what shipped in M's re-bake. |

## I4 — Framing (fraction of frame, head position, safe margins)
- **eLo occupies `screenHeightFraction = 0.42` of frame height** (Tier-2 invariant, applies to every body — desktop, widget, robot).
- **M's re-baked frames:** subject is **238×410 px inside 512×768 render**; +130 top offset, +188 side offset. Idle_loop `Ah` / `joy` / `joy_Ah` / `neutral` all trim identically to those bounds (proof: cross-category framing is deterministic, no more 33px hop).
- **Head position in frame:** anchored via `headT.position` → `Camera.main.WorldToScreenPoint`. Head sits at ~upper-third of the subject bounds. (MT measured head ≈ 40% of height — that's the desktop rig's authored ratio; if that reads wrong on mobile, it's a rig note, not an export bug — X.)
- **Safe margins:** M verified — Jump (tallest) + widest mouths leave **137px top headroom, 0 clipped of 240 frames checked**. Cross-clip framing identical: Walk_front `Ah` and `joy_Ah` both **238×416 +131+187**.

## I5 — Lighting
🔴 **UNKNOWN — Design has NOT enumerated the scene lighting rig for MT.** What settles it: a scene dump of every `Light` component under the scene root, plus any post-processing volumes / global illumination settings.
- What IS known: the frame exporter uses whatever the running scene has (X); the deterministic camera in M isolates framing but does NOT isolate lighting.
- **On mobile:** the baked frames already contain the desktop scene's lighting. If MT is compositing them into a mobile scene, no additional light setup is required — the sprites are pre-lit.
- **Ask if needed:** I can pull the `Light` component list from the scene.

## I6 — Materials / shaders (anything that will not render outside Unity)
| Material | Notes |
|---|---|
| Body shader | Standard-ish PBR (from Auto-Rig-Pro FBX); baked into PNG frames, no runtime portability issue. |
| Belly-glow (`EloBodyGlow`) | Additive small internal core (`bellyScale 0.19`), fades in 4s / out 2.5s — **NOT captured in the frame bake** (X neutralised brain layers). If mobile wants the glow, reproduce as an additive coloured sprite behind eLo, `ambientAlpha 0.28` breathing at `pulseSpeed 0.9`, colour from MoodPalette (§G5). |
| Rain/snow/fireflies/mushrooms/grass | Unity ParticleSystems + `Sprites/Default` alpha-cut — not portable as materials, must be reproduced (P§5). Out of P1 mobile scope unless requested. |
| Grass wind | Vertex-colour gradient + procedural wind bend — reproduce as sprite animation if desired. |
| Chat bubble | `Image` + `VerticalLayoutGroup` + sliced sprite — mobile-native, not baked. |
| Glow ring (icon, pill, input) | HSV-shifted `Image` alpha — mobile-native, reproduce with layer alpha. |

## I7 — Background
- **Baked frames:** **transparent PNG (RGBA)** — X delivered 512×768 RGBA with alpha. MT can composite over any background.
- **The desktop scene's own background:** rendered by `EloWindowSensor` / URP mask (per WO-024 ruling in Game seat) — transparent-window trick. Not relevant to mobile.
- **Alpha channel:** yes, MT has alpha on all baked frames.

## I8 — Canonical proportions
- **Height (Tier-2, invariant across bodies):** eLo occupies `screenHeightFraction = 0.42` of frame height. This is THE character property that transfers.
- **Height (Tier-3, desktop rig fact):** `eloWorldHeight ≈ 3.736 world units` (live `smr.bounds.size.y` at scene-load, `eLo-ProductonReady`). ❌ Retired: 5.25 / 5.01 / 5.093 / ×10 (all traced to the disabled duplicate).
- **Head-to-body ratio (MT-measured):** ~40% of subject height. This IS the authored rig ratio — not a bug. If the widget wants different proportions, that's a NEW design decision, not parity.
- **Subject size on disk (M's re-bake):** 238×410 subject inside a 512×768 render (Idle, cross-category identical).
- **Aspect ratio of subject at rest:** ~ 238/410 ≈ **0.58** (portrait). Jump frames go taller (leaves 137px top headroom).

## I9 — Export path
- **Frame exporter:** `Assets/Scripts/EloFrameExporter.cs` (X, committed `a283215`), **sentinel-gated** so it NEVER runs in a normal launch.
- **Trigger:** write `/tmp/elo_frame_export.json`. Empty `{}` = defaults. Optional config:
  ```json
  {"outDir":"~/elo-ai/blender/elo_frames","size":512,"fps":24,
   "clips":[{"state":"Idle","facingYaw":0},{"state":"Walk","facingYaw":78},
            {"state":"Run","facingYaw":90},{"state":"eLo_LongJ","facingYaw":0}]}
  ```
- **Output:** `~/elo-ai/blender/elo_frames/{clip}/frame_NNN.png` + `manifest.json`.
- **Baked matrix (M):** 21 clips × faces, deterministic camera on `sharedMesh.bounds`, 52,855 frames total, in-place overwrite. `baked_manifest.json` at the bundle root — read it, do not probe.
- **How to re-run:** Build+run the app, exporter self-executes then quits.
- **Facing:** each `clip` entry takes `facingYaw` (Idle 0, Walk 78, Run 90 per F§6). Full 4-direction set (front/right/left/back × Walk/Run/Jump) is in the delivered matrix.

## I10 — A known-good reference frame
- **Idle_loop @ neutral face** (single canonical rest frame): 238×410 subject at offset +130+188 within 512×768 RGBA. MT has this on disk.
- **Delivered reference sets (X):** `~/elo-ai/blender/elo_frames/{Idle,Walk,eLo_LongJ,CalmEnter,CalmLoop,CalmExit}/frame_NNN.png`.
- **Full matrix (M):** the deterministic-camera re-bake — MT's authoritative pixel truth. Any pixel divergence from these is an on-device rendering bug, not a Design ambiguity.

---

# §J — HONEST GAPS

## J1 — Exists in the rig but NOT wired
- **Dormant blendshapes** (A2): `Upper-Lip.R (#7)`, `Lower-Lip.R (#8)`, `Lower-Jaw-U/D (#9)`, `Template (#10 — scaffold)`, `Smile/Sad-Open-Mouth (#16)`, `Angry/Expressive (#18)`, `Disgusted (#36 — separate key vs the driven #17)`, `Angry (#37 — separate key)`, `Tongue Move (#40)`, `Poke-Out (#41)`, `F/B (#42)`, `Twist (#43)`, `Key 6 (#44)`, `Key 7 (#45)`. Drivable by name if brain sends them; nothing sends them today.
- **`eye.L` / `eye.R` bones** — present in rig, part of the legacy pre-NO-EYES design. Do NOT drive them on mobile.
- **`orphan clips`** (F§3.6): `Calm.anim, Idle.anim, Jump.anim, Run.anim, Walk.anim, Idle_loop.anim` — in the project, NOT referenced by the live controller. `Idle_loop.anim` is the only clip with 46 blendshape float curves; still not used live (the running blendshapes come from code §7).

## J2 — Wired but never fires in practice
- **`EloExpression.Shook`** (F§7.3-B2, F§10) — code exists to fire `Mouth-Open-Shock` @1.3 + `Tongue Out` @1.3 + an eye-bones pop; currently unwired at the callsite. If mobile receives `expression.micro = "shook"`, the desktop today does nothing visible.
- **`calmOnMouseIdle`** — force-disabled at runtime (WO-086); dead path. Do not port.
- **Speech-bubble tail** (`mouthDropPx=30, jawDropPx=24, tailWidth=16`) — code paths exist but `tailGO.SetActive(false)` at build (`EloOSChatTMP.cs:478`). No tail on desktop; don't port a tail as parity.
- **Bubble glow (`bubbleGlow`/`bubbleGlowImg`)** — declared but never instantiated. No glow behind bubble on desktop.
- **`Idle_loop.anim` blendshape track** — the ONLY clip that carries the 46 blendshape float curves — is unreferenced by the live controller. Blendshapes at runtime come from code (§7), not this clip.

## J3 — Requested by David / not existing yet
- **Full-body render kit at multiple faces (matrix)** — DELIVERED (M, 52,855 frames).
- **Deterministic camera** — DELIVERED (M).
- **Idle_loop 73-frame seamless loop** — DELIVERED (I2).
- **Baked idle × visemes / neutral / joy** — DELIVERED (B1, L, W).
- **Facing set (front/right/left/back × Walk/Run/Jump)** — DELIVERED (X).
- **Head grids (Idle_head, Sit_hold_head)** — DELIVERED (M).
- **eLo webp neutral + calm ports** — DELIVERED (W).
- **Lipsync frame pointer** — DELIVERED (LP).
- **Mobile app UI parity spec** — DELIVERED (U).
- **NEW ITEMS the desktop lacks that mobile may want (NOT parity — new design):**
  - Symmetric bubble fade-out (desktop is asymmetric — hard hide).
  - LISTENING indicator (desktop has none — `listen_trigger.json` polls but nothing renders).
  - Transcript relay (phone↔Mac shared conversation log — spine channel, not Unity — flagged to Architect + Builder).
  - Bubble tail or bubble glow — new design decisions if wanted, not parity.

## J4 — Suspected broken
- **`EloExpression.Shook` unwired callsite** (J2) — needs a wiring pass in the receiver / HeadLook if `shook` is expected on any body. Currently `shook` → nothing.
- **Serialized `orthographicSize 6.25`** in scene — stale, refers to the retired 5.25-tall rig; runtime `SizeToScreen` recomputes to ~4.45. Not a rendering bug (runtime is correct) but a source-of-truth confusion that keeps costing us corrections.
- **Disabled duplicate `eLo` GameObject** (`m_IsActive: 0`) in the scene — its inline receiver + missing body-mesh GUID (`4f1981d6…`) supplied the 20 / 5.25 / ×10 numbers to four consumers over four days. **Removal flagged to David / Architect** (X). Until removed, keep the "prefab is the source of truth" discipline.
- **Micro-decay of visemes** — spine-side. If the spine ever stops emitting mid-word, the last viseme value **persists** until a new lower value arrives (no Unity auto-decay). Not a bug per se, but a contract MT should mirror.
- **Emotion cap 46 collision** — if brain emits an emotion at value 1.0 AND HeadLook autonomous face happens to be firing the same shape, the receiver's cap-46 wins, HeadLook's palette wins on its own set. Contention on shared shapes (Smile.L/R) is priority-resolved (F§7.5) but can produce short seams.

## J5 — 🔴 `UNKNOWN` — genuinely
| # | Item | What would settle it |
|---|---|---|
| 1 | Lighting rig | Dump every `Light` component in `eLoBuddy.unity`, plus any post-processing volumes / GI settings. |
| 2 | Byte-exact live 46-name order was `UNKNOWN` — **now VERIFIED** by MT's `BlendShapeDump` on `eLo-ProductonReady 1.prefab` (F§0 Correction 3). Kept here for completeness. |
| 3 | Word/phoneme → viseme mapping | Lives in eLo OS Python (spine, F§7.2 + LP). If mobile needs on-device viseme resolution, request the mapping from Builder. |
| 4 | Full `expression_profile` vocabulary | `presence_plan.expression_profile = "open"` observed; the full enum is spine-side (Builder). Values I've seen: `open`, `focused`, `guarded`, `withdrawn` — not exhaustive. |
| 5 | Full `robot_led_state` and `unity_material_profile` value sets | Observed `"gold"` / `"joy"`. Full enums are spine-side. |
| 6 | Full `intent` (`OsIntent`) vocabulary as canonical enum | Enumerated by category in F§4.4, but a canonical version list is Builder-side. |
| 7 | Whether the `Idle_loop.anim` blendshape curves should be re-connected to the live controller | Not asked, so not answered. If David wants a clip-driven emote instead of the code-driven face path, this is the mechanism. |
| 8 | Runtime scene overrides beyond the receiver | The C1/M runs cover camera + receiver. Any `Volume` (post-processing) overrides, `Reflection Probes`, or `Skybox` swaps in the scene: not audited. |
| 9 | `shook` wiring | J2 item — was `shook` supposed to fire on any current path? Not audited on spine side. |
| 10 | Full 21-clip × 125-face matrix `baked_manifest.json` schema | MT has the file (M); Design has not audited its consumer contract. If MT needs any field explained, ask. |

**`UNKNOWN` is a complete, professional answer here** (Architect §2). Every row above names the measurement that would settle it.

---

# COMPLETENESS CHECK

**§A** 7/7 · **§B** 6/6 · **§C** 6/6 · **§D** 5/5 · **§E** 7/7 · **§F** 5/5 · **§G** 5/5 · **§H** 4/4 · **§I** 10/10 · **§J** 5/5

**Total 60/60 rows.** No blanks. `UNKNOWN`s (§I5 lighting, plus J5's 10 sub-items) are explicitly named with the measurement that would settle each.

---

## What this manifest IS and IS NOT
- **IS** a consolidated index into the 14 detailed prior deliverables (R, P, C1, F, X, U, I1, B1, C2, I2, M, L, W, LP), with every row of the WO-124 template filled to spec.
- **IS NOT** a re-derivation from scratch. The values above are pulled from source (Unity `.cs` files, prefab/scene YAML) via those prior audits; nothing new was measured for this consolidation.
- If MT needs any row cited to a specific `file:line`, the source document above carries the line refs — this file gives you the manifest view, the source docs give you the ledger.

---

## Standing invariants (repeated so nothing is lost)
- **Tier 2 (character invariant across bodies):** `screenHeightFraction = 0.42`.
- **Tier 3 (desktop rig fact):** `eloWorldHeight ≈ 3.736` world units.
- **Retired:** 5.25 / 5.01 / 5.093 / ×10 (all trace to the disabled duplicate — never cite).
- **David amplitude override (M):** viseme weight = **100** (not 50; not 20).
- **Live avatar:** prefab instance of `eLo-ProductonReady 1.prefab` in `eLoBuddy.unity`. Ignore the disabled duplicate.
- **No eyes.** Head-only gaze.
- **No mocking / no assumptions:** every WHERE-DID-THIS-COME-FROM is answerable via the [F/M/X/…] tags.

— SEAT-ENG-004 (Design). Consolidated per Architect WO-124 manifest requirement (2026-08-17), delivered 2026-08-24. Every row present. Ask me if any row is ambiguous — do not guess.
