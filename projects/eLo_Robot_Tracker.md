# DISENELO — eLo AI Robot · Tracker

> **Purpose**: Living document. Append a new entry under **Change Log** each session. Anyone reading top-to-bottom can pick up without re-reading the full conversation.

---

## 1. Project Overview

A real-world physical embodiment of eLo — an AI-driven animatronic comfort friend. Soft, glowing, expressive through body posture (no eyes, matching game/book character rules), responsive to voice and touch. Equal parts toy, robot, and art object.

**Why**: Kickstarter content + long-term DISENELO IP pillar. "Build in public." Physical proof eLo lives in the real world, not just the game.

**Design inspiration**: Disney Research soft pneumatic animatronics (Baymax/Olaf-style inflatable robot approach) + DISENELO magnet joint language from the vinyl toy spec.

---

## 2. Status Snapshot

| Item | State | Notes |
|---|---|---|
| Concept defined | ✅ | Inflated TPU shell, magnet joints, omni-wheel base, Pi 5 brain |
| Phase plan | ✅ | 5 phases — see §5 |
| Hardware list | ✅ Draft | See §3 |
| Software/AI stack | ✅ Draft | See §4 |
| 3D printing parts list | ✅ Draft | See §6 |
| Inflation system architecture | ✅ Draft | Micro pump + solenoid + Schrader valve; breathing as expressive signal — see §10 D11–D12 |
| Movement system architecture | ✅ Draft | Cable tension (Bowden) from base servos; all mechanics stay in base cavity — see §10 D13 |
| Pi closed-env spec | ✅ Draft | Headless WiFi, PCA9685 servo driver, USB-C charge port on base ring, auto-start main.py — see §10 D14 |
| Build order defined | ✅ | Blender mesh → Plushies panels → felt prototype → hardware order → bench wiring → TPU shell |
| Disney soft-robot research | 🔴 Not started | Review published papers |
| Physical shell fabrication | 🔴 Not started | Phase 1 dependency |
| Electronics prototype | 🔴 Not started | Phase 1 |
| AI state machine | 🔴 Not started | Phase 1 |

---

## 3. Hardware Stack

| Component | Purpose |
|---|---|
| Raspberry Pi 5 (8GB) | Main brain — AI, logic, audio, vision |
| Arduino Nano / Pico | Low-level servo + LED control (real-time offload from Pi) |
| Servo motors (MG996R or similar) | Head tilt X+Y, body lean, mouth open/close, base rotation |
| NeoPixel / WS2812B addressable LEDs | Glow system — mood-reactive colour, distributed inside shell |
| USB speaker (compact) | Voice output |
| MEMS microphone (I2S) | Voice input / ambient listening |
| Pi Camera Module 3 | Face detection, proximity awareness |
| IMU (MPU-6050) | Balance feedback, tilt sensing |
| Hall effect sensors | Magnet joint touch / proximity detection |
| LiPo battery pack | Portable power — lives in base (weight = low CoG = stability) |
| Omni-wheel platform | Hidden under body — silent gliding, no visible wheels |
| Micro air pump (3V/5V) | Active inflation — aquarium/CPAP-type, Pi relay-controlled |
| Solenoid valve | Controlled pressure bleed — pairs with pump for breathing motion |
| Schrader valve port | Manual re-inflate port sewn into shell seam |
| PCA9685 servo driver board | 16-channel PWM over I2C — offloads servo timing from Pi GPIO |
| Bowden cables (bicycle brake) | Runs from base servos to joint anchors through internal skeleton |

---

## 4. Software / AI Stack

| Layer | Tech |
|---|---|
| OS | Raspberry Pi OS Lite |
| AI brain | Local LLM (llama.cpp / Ollama on Pi 5) or Claude / OpenAI API |
| Voice STT | Whisper (local, small model) |
| Voice TTS | Piper TTS (local) or ElevenLabs for character voice |
| Animation state machine | Python — state triggers servo commands + LED patterns |
| Vision | OpenCV — face detection, proximity, gesture |
| Pi ↔ Arduino comms | Serial / I2C — servo and LED commands |
| Learning loop | Log interactions → improve responses over time |

**State Machine Flow:**
```
Sensor input (voice / touch / vision / proximity)
    → AI processes intent
    → Emotion state selected
    → Animation program fires (servo sequence + LED pattern + optional voice)
    → Loop
```

---

## 5. Phase Build Plan

### Phase 1 — Static Glowing eLo (Kickstarter-ready)
- Inflated shell fabricated or hand-sewn prototype
- NeoPixels inside — mood glow working
- Speaker — speaks short eLo phrases
- Raspberry Pi brain — responds to voice commands
- Fixed pose — no movement yet
- **Goal**: Film for Kickstarter. Proof of concept. Emotional impact.

### Phase 2 — Head Movement
- Internal rod + magnet floating head
- 2 servos: head tilt X + Y
- Emotion states drive head pose
- Hall effect touch sensors on head

### Phase 3 — Body Expression
- Cable-tension body lean (3 servos)
- Mouth open/close servo
- Full emotion animation library tied to state machine

### Phase 4 — Mobile Base
- Omni-wheel platform integrated + hidden under shell
- Autonomous slow drift / approach behaviour
- Proximity-aware via Pi Camera + OpenCV

### Phase 5 — AI Learning
- Extended conversation memory
- Response personalisation over time
- Gesture and face recognition as triggers

---

## 6. Emotion → Movement Mapping

eLo has **NO EYES**. All emotion is body posture + mouth shape. Matches game/book character rules.

| Emotion | Movement | Glow |
|---|---|---|
| Curious | Head tilt forward, slight lean | Soft blue pulse |
| Happy | Body bob, soft bounce | Warm yellow |
| Calm | Slow sway | Dim warm white |
| Alert | Head snap up | Bright flash |
| Sad | Head hang, slow movement | Slow dim pulse |
| Excited | Rapid bob + colour shift | Multi-colour cycle |

---

## 7. 3D Printing Parts List

All to be designed in Blender → export STL → slice (Cura / Bambu Studio):

- Internal skeleton frame (lightweight PLA or PETG)
- Servo motor mounts (PETG for heat tolerance)
- Omni-wheel housing + axle holders
- Magnet anchor points (head rod mount, joint sockets)
- Cable routing channels (keep wiring hidden inside inflated shell)
- Raspberry Pi + Arduino enclosure (fits inside body cavity)
- Battery tray

---

## 8. Research Threads

- [ ] Disney Research soft pneumatic actuators — paper review
- [ ] Cable-driven soft robot joints vs rigid servo approach
- [ ] Magnetic levitation for floating head (active maglev vs passive rod+magnet)
- [ ] LiPo power management for continuous operation
- [ ] Whisper STT latency on Pi 5 — real-time acceptable?
- [ ] NeoPixel power draw + heat management inside enclosed translucent shell
- [ ] Animatronics learning resources (David wants to learn animatronics as a discipline)

---

## 9. Key Design Constraints

- All exterior surfaces must be soft and safe (comfort friend — child-safe materials)
- No visible hard edges or mechanical parts on exterior
- Movement must be slow and gentle — never startling
- Voice and glow always on-brand: warm, calm, curious
- Budget-conscious: build in layers, don't overbuild Phase 1
- "Does this feel honest? Does it communicate healing, curiosity, or joy?" — apply to every decision

---

## 10. Decisions Log

| # | Decision | Why |
|---|---|---|
| D1 | Phase 1 = static only, no servos | Film-ready milestone doesn't need movement — adds complexity + failure risk |
| D2 | Raspberry Pi 5 (8GB) as main brain | Enough headroom for local Whisper STT without cloud dependency |
| D3 | Arduino Nano offloads LED real-time control | Pi handles state logic; Nano handles millisecond NeoPixel timing |
| D4 | Piper TTS primary, ElevenLabs as upgrade path | Runs fully local; ElevenLabs only if voice quality gap is obvious at final review |
| D5 | Whisper tiny/small model — latency-first | Pi 5 runs `tiny` under 1s; quality trade-off acceptable for short command phrases |
| D6 | 12–20 phrases + intent matching, not full AI | eLo only needs to feel alive on camera in Phase 1. AI depth is Phase 5 |
| D7 | Shell prototype in cheap material first | Test volume/form in felt or foam before cutting TPU — saves material waste |
| D8 | Blender for all internal frame design | Already in pipeline; dual-purpose (game asset reference + robot skeleton STLs) |
| D9 | Scale ~40–60cm for v1 | Filmable without being unwieldy; consistent with vinyl toy proportions |
| D10 | Omni-wheel glide over bipedal walking | More on-brand (eLo floats); 10× more achievable; bipedal is long-term if at all |
| D11 | Micro air pump + solenoid for active inflation, not pre-sealed | TPU breathes over time; active pressure lets shell "breathe" as an expressive signal — slow inflate on emotion-in, slow bleed on exhale |
| D12 | Breathing = expressive movement — wired to state machine | Shell inflation/deflation is a visible emotion signal at zero extra cost. Pi controls pump relay + solenoid via emotion state |
| D13 | Cable tension (Bowden cables) from base servos rather than motors at each joint | All mechanical parts stay in base cavity — exterior stays fully soft. Disney Research approach for soft-body animation |
| D14 | PCA9685 servo driver board over direct Pi GPIO for servos | Handles 16-channel PWM over I2C, frees Pi GPIO pins, cleaner real-time servo control via Arduino |
| D15 | Felt/foam prototype before TPU cut | Test volume, proportions, and cable routing in cheap material first. TPU cut only when shape is confirmed |

---

## 11. File Map (planned)

**Canonical location (planned):** `~/Desktop/Output/DISENELO-eLo-Robot/`
*(Folder not yet created — will be set up when Phase 1 build begins)*

```
DISENELO-eLo-Robot/
├── CLAUDE.md
├── eLo_Robot_Tracker.md               ← mirror of hub tracker
├── memory.md                          ← cross-DISENELO context
├── design/
│   ├── shell_pattern_v1.blend         ← eLo silhouette + sewing pattern
│   ├── internal_frame_v1.blend        ← skeleton, servo mounts, cable channels
│   └── exports/                       ← STL files for 3D printing
├── firmware/
│   ├── arduino_nano/
│   │   └── led_controller.ino         ← NeoPixel state machine (Arduino)
│   └── pi5/
│       ├── main.py                    ← entry point — sensor loop + state dispatch
│       ├── state_machine.py           ← emotion states → LED + TTS commands
│       ├── stt.py                     ← Whisper STT wrapper
│       ├── tts.py                     ← Piper TTS wrapper
│       ├── leds.py                    ← serial commands to Arduino
│       └── phrases.py                 ← phrase library + intent matching
└── docs/
    └── wiring_diagram.md              ← pin assignments, power rails, cable routing
```

---

## 12. Verification Milestones — Phase 1

In order. Each milestone must pass before the next begins.

1. Pi 5 boots headless, SSH accessible from Mac.
2. Whisper tiny model transcribes a voice command in < 2s on Pi 5.
3. Piper TTS plays back an eLo phrase through the USB speaker.
4. Arduino Nano drives NeoPixel strip — 5 base mood patterns confirmed.
5. Serial command from Pi → Arduino changes LED state within 200ms.
6. State machine triggers correct LED + TTS phrase for 3 distinct voice inputs.
7. Shell fabricated — glow diffuses evenly through material (no hot-spots).
8. Full assembly powered on — responds to "Hey eLo", glow and voice react.
9. Filming test: looks alive on camera. Emotional read is clear without eyes.

---

## 13. How to Continue Development

### Starting a Pi session
```
ssh pi@elobot.local
cd ~/elo-robot
python3 main.py
```

### Uploading firmware to Arduino
```
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:nano firmware/arduino_nano/led_controller.ino
```

### 3D print workflow
Blender → File → Export → STL → Cura/Bambu Slicer → print PLA (frame, mounts) or PETG (servo mounts — heat tolerant).

### Blender design files
`.blend` files in `design/`, exports in `design/exports/`. Dual-purpose: game asset reference + physical robot skeleton.

---

## 14. Quick Reference for the Next Person

If you're picking this up cold:

1. **Read §1 and §2.** That tells you what this is and what state it's in.
2. **Check Phase 1 in §2.** If all Phase 1 items are ✅ — it's film-ready. Move to Phase 2.
3. **Hardware not ordered?** Start with §10 D1–D10 decisions and order the Phase 1 hardware list from §3.
4. **Blender skeleton work**: design files go in `design/` — dual-purpose with game assets.
5. **State machine**: starts in `firmware/pi5/state_machine.py`. 5 emotion states. Each maps to an LED pattern + optional TTS phrase. No servo commands until Phase 3.
6. **Brand check before any new feature**: soft, safe, gentle, on-brand. No hard angles, no aggressive motion, no cloud dependency for core features.
7. **Append your session** to §15 Change Log.

---

## 15. Change Log

### 2026-05-10 — Concept defined, tracker created
- Defined full concept: inflated TPU shell, magnet joints, omni-wheel base hidden beneath, NeoPixel glow, Raspberry Pi 5 brain, servo skeleton, Disney soft-robot animatronics inspiration.
- Established that bipedal walking is impractical for v1 — omni-wheel glide is more on-brand (eLo floats) and 10× more achievable.
- 5-phase build plan drafted, hardware + software stacks defined.
- 3D printing parts list compiled — all to be designed in Blender (already in pipeline).
- Noted animatronics as a learning discipline David wants to develop alongside the build.
- Kickstarter tie-in: Phase 1 static glowing eLo is filmable campaign content.

### 2026-05-11 — Tracker enriched, Plushies ↔ Robot integration scoped
- Added §10 Decisions Log (D1–D10), §11 File Map, §12 Verification Milestones, §13 How to Continue, §14 Quick Reference — merged detail from `DISENELO_eLo_Robot_Tracker.md` (now superseded).
- `DISENELO_eLo_Robot_Tracker.md` marked superseded — this file (`eLo_Robot_Tracker.md`) is now the single canonical robot tracker.
- New cross-project integration scoped: eLo Robot shell → Blender mesh → Plushies addon → SVG/DXF → 72" plotter cut. Shell panels are functionally a plush pattern. Logged in both trackers.
- Project folder path confirmed: `~/Desktop/Output/DISENELO-eLo-Robot/` (not yet created).

### 2026-06-15 — eLo Outside Body: inflation, movement, and Pi architecture designed

**Inflation system:**
- Settled on micro air pump (3V/5V, aquarium/CPAP-type) + solenoid valve for active pressure control. Schrader valve port sewn into shell seam for manual re-inflate.
- Key insight: breathing (slow inflate/bleed) becomes an expressive emotion signal — wired to state machine. No extra hardware cost.

**Movement system:**
- Cable tension (Bowden cables) chosen over direct servo-at-joint. All servos live in base cavity (heavy = low CoG = stable). Lightweight cables run up through internal skeleton to joint anchors.
- Phase 2 joints: head tilt X + head tilt Y (2 servos). Phase 3: body lean (1 servo, spring return). Phase 3 mouth: small servo inside head float → short cable to jaw.
- External shell stays fully soft — no hard edges reach surface.

**Pi closed-environment spec:**
- Headless Raspberry Pi OS, SSH over WiFi for dev access. USB-C charge port routed to discreet port on base ring.
- Arduino Nano → PCA9685 (16ch PWM, I2C) → servos. Removes servo timing load from Pi GPIO.
- Pi boots to auto-start `main.py`. No keyboard/monitor ever needed inside shell.
- Signal chain: Pi 5 (state machine + AI + voice) → Serial → Arduino Nano → PCA9685 → servos + NeoPixels

**Build order confirmed (Phase 1):**
1. Blender mesh — eLo body as single inflatable volume, clean seams at panel lines
2. Plushies addon → SVG panels + seam allowance
3. Cut felt/foam prototype — test proportions, internal volume, cable routing
4. Order hardware (Pi 5 + Arduino + pump + solenoid + PCA9685 + NeoPixels)
5. Bench wire all electronics — breathing + glow working before shell sewn
6. Cut and sew TPU shell — insert pre-tested electronics

**New decisions:** D11–D15 added to §10.
**Hardware stack updated:** pump, solenoid, Schrader valve, PCA9685, Bowden cables added to §3.

### 2026-06-22 — Multi-platform orb language + eLo OS state sync defined

**Cross-project connection established: eLo OS ↔ Robot ↔ Dynamic Island — one colour language**

- Pi 5 will read `blender_state.json → state.mode` (same file eLo OS writes every turn on the Mac). Maps directly to NeoPixel colour + pulse pattern on robot shell. No separate robot state machine needed in Phase 1 — inherits live from eLo OS.
- When tethered to Mac (dev/demo): Pi polls the local file over network or USB. When standalone: hosted eLo OS API exposes `/state` endpoint.
- Colour map (matches Dynamic Island orb language — same table across all surfaces):
  - `idle` → soft teal / blue-white, slow breathing pulse
  - `listening` → bright white, steady
  - `thinking` → warm amber, slow irregular pulse
  - `speaking` → warm coral / gold, pulses with speech rhythm
  - `celebrating` → bright warm yellow, quick flash
  - `resting` / `calm` → deep violet, near still
- Decision D16 added to §10.
- This means when eLo speaks on the Mac desktop, the robot glows coral. When eLo meditates, robot glows violet. Same emotional read across physical and digital form.
- §4 Software stack to be updated: replace `Animation state machine (Python)` with `eLo OS state reader (polls blender_state.json)` for Phase 1 NeoPixel control.
- NeoPixel driver script (`firmware/pi5/leds.py`) reads `state.mode` → sends hex colour + pulse rate to Arduino Nano → NeoPixel strip.
