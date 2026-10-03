# WO-FACE-EMOTION-001 — Mood-Triggered Face Expressions
**From:** Board / Lead Architect  
**Date:** 2026-09-01  
**Priority:** P1  
**Authority:** David L3 verbal directive 2026-09-01 — "I want to make some emotions trigger faces so when eLo's mood changes he pulls a face to match."  
**Seats:** Designer (D-1) · Game (D-2 + D-4) · Builder (D-3 — verification only)  
**Source:** `faculties/emotion/emotional_processing_faculty.py` · `runtime/spine/spine.py`  
**Updated:** 2026-09-03 — David L3 refinement: use existing faces, jaw constraint, add speech lip sync

---

## What this is

The eLo OS emotion faculty already produces a `dominant_emotion` signal every turn. That signal already reaches `world_dict["mood"]` in spine.py, which feeds `world_state.json` that Unity reads. The runtime plumbing exists. This WO connects the existing signal to visible face expressions in Presence.

**Two systems, two Animator layers — they must stack, not fight:**
1. **Emotion face layer** — pose-based, expression-driven. Primarily eyes, brows, mouth shape. Jaw kept LOW (≤20% JawOpening) so it doesn't conflict with speech.
2. **Speech jaw layer** — phoneme/amplitude-driven. `JawOpening` blendshape only. Runs additively on top of the emotion layer.

**Design principle:** The face should feel like eLo noticing something or reacting — not a cartoon snap-change. A short blend (not an instant swap) keeps it natural. Subtle is better. Same eLo in different moments — not different characters.

---

## The emotion set (from `faculties/emotion/emotional_processing_faculty.py` — [VERIFIED])

| `dominant_emotion` | What it means | Face direction |
|---|---|---|
| `neutral` | Default resting state | Soft, present, default face |
| `joy` | Positive valence — something good | Happy, bright, slight smile |
| `curiosity` | Open signals, building momentum | Raised brow, head tilt |
| `distress` | Negative + high arousal, or distress_signal | Worried, pained, compressed |
| `challenge` | Challenge signals — effort/focus | Determined, focused, slight tension |
| `connection` | Relational warmth | Warm, open, receptive |
| `identity` | Introspective / self-referential | Thoughtful, inward, still |

**Phase 1 minimum viable set** (David can expand later): `neutral`, `joy`, `curiosity`, `distress`. These four cover the most common emotional territory and are the most visually distinct.

`regulation_state` (`flooded`, `guarded`, `regulating`, `open`) is available for Phase 2 if David wants a second layer (e.g. flooded → overwhelmed face regardless of emotion). Not in scope for this WO.

---

## D-1 — Designer: Map David's Existing Faces to Emotion States

David has already authored face expressions. **Do NOT create new faces from scratch.** The task is to match David's existing faces to the emotion states and record the blendshape weights for each.

**`eLo_v2` rig confirmed as the delivery target.** Available blendshapes [VERIFIED 2026-09-02]: `MouthOpen.Slight`, `Mouth-Open-Shock`, `Tongue Out`, `F/B`, `Key 6`, `JawOpening`, `Smile.L`.

**Jaw constraint — critical:** Emotion expression poses must keep `JawOpening` at ≤20% (0.0–0.20 range). The speech jaw layer drives JawOpening during speech — the emotion pose must leave room for it. Over-deforming the jaw in an expression pose will conflict with lip sync.

For each emotion face David supplies, record:
- Blendshape name → weight for every non-zero shape
- Which emotion state it maps to
- Confirm jaw is within constraint

**Naming convention for baked clips:** `elo_face_neutral`, `elo_face_joy`, `elo_face_curiosity`, `elo_face_distress` (+ others as David provides them — tongues, additional expressions, etc.)

**David will supply additional faces** (tongue-out and others) — wait for those before declaring D-1 complete. Each new face David sends: record weights, map to emotion/state, bake clip, confirm jaw constraint. Report running state to DONE/ as faces arrive.

---

## D-2 — Game: Unity Face Expression Trigger

Wire the `mood` field from `world_state.json` → face expression change in Unity.

**VERIFY FIRST:** Confirm that `world_state.json` currently contains a `mood` key and that its value is a string (e.g. `"joy"`, `"neutral"`). If `mood` is a dict/object rather than a string — STOP and report BLOCKED with the raw value you see. Do not implement until Builder's D-3 confirmation is in.

**After confirmation:**

1. Read `mood` from the world_state on each poll cycle (same tick as gaze / presence updates).
2. Map string → face expression target:
   - `"joy"` → `elo_face_joy`
   - `"curiosity"` → `elo_face_curiosity`
   - `"distress"` → `elo_face_distress`
   - anything else → `elo_face_neutral`
3. Blend to the new expression over `0.3–0.5s` (not instant swap). Use existing animator blend or Lerp — whichever is already live in the eLo rig.
4. Only trigger a change when the emotion actually changes (debounce — do not re-trigger if the same emotion is reported twice consecutively).
5. Do NOT change face during `flooded` regulation override in this phase — that is Phase 2.

**One Brain boundary:** The face expression read from `world_dict["mood"]` is a Living Presence layer — bodily, atmospheric. It does NOT require a brain command per turn. This is the same class as head-look and breathe.

---

## D-4 — Game: Speech Jaw Sync (JawOpening blendshape driven by phoneme class)

A **separate** Animator layer from D-2. Runs additively on top of the emotion face layer. Only drives `JawOpening`. The emotion layer controls face shape; this layer controls jaw movement during speech.

**Phoneme class → JawOpening weight mapping:**

| Sound class | Examples | JawOpening |
|---|---|---|
| Silence / closed | pause, M, B, P | 0.00 |
| Near-closed | F, V, TH | 0.05 |
| Sibilant | S, Z, SH, ZH | 0.15 |
| Alveolar | T, D, N, L | 0.15 |
| Velar | K, G, NG | 0.25 |
| Close vowel | EE, I | 0.30 |
| Mid vowel | EI, OU, EH | 0.42 |
| Near-open | AE | 0.55 |
| Open | AH, A | 0.72 |
| Rounded open | AW, O | 0.65 |

**Implementation (Phase 1 — amplitude approximation, no TTS phoneme feed yet):**
- Sample audio output amplitude per frame (RMS or peak)
- Map amplitude → JawOpening with a short smoothing window (0.05–0.08s lag to feel natural)
- Silence → JawOpening decays to 0.0 over 0.1s
- Cap: even at full amplitude, JawOpening should not exceed 0.75 (leaves 25% of range as safety margin against over-deform)

**Phase 2 (when TTS is live):** Replace amplitude driver with proper phoneme class lookup from TTS viseme stream. The JawOpening layer wiring stays the same — only the input signal changes.

**Layer setup:**
- New Animator layer above (or behind) emotion layer, weight 1.0, Additive blending
- Mask: jaw bone + JawOpening blendshape only — nothing else
- Does NOT affect eye, brow, or mouth shape blendshapes

---

## D-3 — Builder: Verify mood signal is a clean string in world_state

**VERIFY:** Check `runtime/spine/spine.py` line where `_world_dict["mood"]` is set. Currently reads:
```python
_world_dict["mood"] = getattr(cognitive_state, "emotional_tag", "")
```

`emotional_tag` on `cognitive_state` is an `EmotionalTag` dataclass (not a plain string). Confirm:
- Whether this serialises to a string or a dict/object in `world_state.json`
- If it serialises as a dict/object: fix to emit `dominant_emotion` string:
  ```python
  _et = getattr(cognitive_state, "emotional_tag", None)
  _world_dict["mood"] = getattr(_et, "dominant_emotion", "neutral") if _et else "neutral"
  ```

**This is a one-line verification or a one-line fix.** Report exact finding to DONE/ before Game seat implements D-2.

---

## Acceptance tests

| AT | Seat | Pass condition |
|---|---|---|
| AT-1 | Builder | `world_state.json` `mood` field is a plain string (e.g. `"joy"`) — not a dict |
| AT-2 | Game | When OS emits `joy`, eLo's face blends to `elo_face_joy` within 0.5s |
| AT-3 | Game | When OS emits `distress`, eLo's face blends to `elo_face_distress` within 0.5s |
| AT-4 | Game | No face change when same emotion is reported twice consecutively |
| AT-5 | Game | Face returns to `elo_face_neutral` when emotion is `neutral` or unknown |
| AT-6 | Designer | Phase 1 face assets exist, baked, named per convention, jaw ≤20% in each pose |
| AT-7 | Game | During speech: `JawOpening` varies with amplitude — not locked at 0 |
| AT-8 | Game | During silence: `JawOpening` decays to 0.0 within 0.1s |
| AT-9 | Game | `JawOpening` layer is Additive — emotion face shapes unaffected when jaw opens |
| AT-10 | All | Existing movement, breathe, head-look behaviour unaffected |

---

## Sequencing

Builder D-3 → then Game D-2 (depends on confirmed string format). Designer D-1 is independent — can run in parallel with Builder D-3.

---

## Phase 2 (not in scope now — record for future)
- Full 7-emotion set (add `challenge`, `connection`, `identity` faces)
- `regulation_state` overlay (flooded → overwhelmed face regardless of dominant_emotion)
- Transition sound / micro-animation on face change
- Mobile Presence face parity

---

*Board / Lead Architect · 2026-09-01 · Authority: David L3 directive 2026-09-01 · Source: `faculties/emotion/emotional_processing_faculty.py` [VERIFIED] · `runtime/spine/spine.py` [VERIFIED]*
