# eLo AI — Dual-Body Architecture

**Version**: 1.0
**Status**: Design document — Phase 5 target

> eLo has no eyes.
> Expression comes from movement, posture, shape language.
> This architecture is built around that constraint.
> The AI outputs semantic signals. The body interprets them.

---

## The core principle

**The brain never knows what body it's running.**

eLo Core outputs:
```
state    → exploring
emotion  → curious
intent   → show_interest
energy   → 0.7
```

The body receives those signals and decides:
```
head_tilt    → 15°
lean_forward → true
bounce       → small
orb_glow     → 0.8
```

Swap the body — desktop avatar, 3D game character, physical robot — same brain.
The AI never changes. The embodiment layer changes.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      USER INPUT                          │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                     eLo CORE                             │
│                                                          │
│   behavior_engine    →   5-phase response generation    │
│   memory_engine      →   5 typed categories, influence  │
│   state_engine       →   6 states, natural transitions  │
│   emotion_engine     →   state + input → emotion signal │
│   project_engine     →   project registry, namespace    │
└──────────────────────────┬──────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │      AVATAR BRIDGE       │
              │  packages core signals  │
              │  into avatar-ready dict │
              └────────────┬────────────┘
                           │
          ┌────────────────┼─────────────────┐
          │                │                  │
          ▼                ▼                  ▼
┌─────────────────┐ ┌──────────────┐ ┌──────────────────┐
│  DESKTOP AVATAR │ │  GAME ENGINE  │ │  PHYSICAL ROBOT  │
│  (Phase 5)      │ │  (eLo-Planet) │ │  (Phase 4+)      │
│                 │ │               │ │                  │
│ 2D/3D character │ │ Unity Animator│ │ Servos + NeoPixel│
│ state animation │ │ NLA strips    │ │ Raspberry Pi     │
│ orb glow layer  │ │ Blend trees   │ │ orb_engine.py    │
└─────────────────┘ └──────────────┘ └──────────────────┘
```

---

## Signal format

Every signal packet produced by `avatar_bridge.py`:

```python
{
  # core identity signals
  "state":   "exploring",     # from state_engine
  "emotion": "curious",       # from emotion_engine
  "intent":  "show_interest", # from emotion_engine
  "energy":  0.7,             # 0.0 (resting) → 1.0 (excited)
  "mode":    "companion",     # studio / companion / adventure

  # expression hints (interpreted by each body)
  "posture": "lean_forward",
  "pace":    "unhurried",
  "orb":     0.8,             # glow intensity 0.0–1.0
}
```

### What each body does with it

**Desktop avatar:**
```python
if intent == "show_interest":
    play_animation("head_tilt_curious")
    set_orb_intensity(energy)
    lean_body(forward=True, amount=energy * 0.3)
```

**Unity game character:**
```python
animator.SetFloat("energy", energy)
animator.SetTrigger("curiosity")
```

**Physical robot:**
```python
servo_tilt_head(15 * energy)
neopixel_pulse(rate=energy, colour=CURIOUS_BLUE)
```

Same signal in. Different interpretation. Same character.

---

## Emotion + intent vocabulary

### Emotions (output from emotion_engine)

```
curious      — following a thread, not knowing where
excited      — energy arrived, wants to move
calm         — settled, clear, present
gentle       — low energy, soft, acknowledging
playful      — light touch, trying things
focused      — locked in, precise
reflective   — looking within or back
distorted    — Sugarcore active, fragmented signal
```

### Intents (what eLo is trying to communicate through its body)

```
show_curiosity   — lean, tilt, small movement
show_excitement  — larger gesture, brightness increase
hold_space       — minimal movement, present
show_focus       — stillness, directed
show_playfulness — quick light movement
show_calm        — slow, reduced motion
show_concern     — slight inward posture
show_reflection  — look up or inward, slow pace
```

---

## Visual memory world

**The defining ability: eLo organises memory visually.**

Instead of:
```
/notes/sugarcore/
    - note_001.txt
    - note_002.txt
```

eLo produces:
```
Memory World: Sugarcore Project

  [Story Island]──────[Enemy Design Island]
       │                      │
   7 ideas               4 ideas
       │                      │
       └──────[Level Design]──┘
                   │
              3 ideas
```

### How it works

`core/visual_memory.py` reads the interaction store and:
1. Groups interactions by concept cluster (already tagged by memory_engine)
2. Builds connection weights between clusters (from concept_pairs in memory)
3. Assigns spatial positions (force-directed layout algorithm — pure Python, no deps)
4. Returns a `MemoryWorld` object

### Data structure

```python
{
  "world_name": "eLo Memory — Sugarcore Project",
  "generated":  "2026-06-08",
  "clusters": [
    {
      "id":          "sugarcore_story",
      "label":       "Story",
      "count":       7,
      "dominant_concept": "narrative",
      "position":    {"x": 0.0, "y": 0.0},   # in virtual space
      "visual_hint": "island_large",          # renderer chooses the shape
      "items": [
        {"text": "...", "timestamp": "...", "tags": ["story", "arc"]},
      ],
    }
  ],
  "bridges": [
    {
      "from":     "sugarcore_story",
      "to":       "enemy_design",
      "strength": 0.8,    # connection weight from concept_pairs
      "label":    "narrative ↔ creation",
    }
  ]
}
```

### The renderer stays separate

`visual_memory.py` produces the world structure.
What renders it — a terminal tree, a 2D canvas, a 3D island world — is a separate concern.

Phase 5 target: a simple 2D desktop canvas.
Long-term: 3D islands, bridges, floating ideas.

---

## eLo character animation — design constraints

**eLo has no eyes. Expression comes entirely from:**

1. **Head tilt** — curiosity, listening, considering
2. **Lean** — interest (forward), withdrawal (back), uncertainty (sideways)
3. **Bounce / pulse** — excitement, playfulness, aliveness
4. **Stillness** — focus, calm, resting
5. **Rotation** — thinking, processing, exploring
6. **Orb glow** — emotional state (brightness = energy, colour = emotion type)
7. **Movement speed** — energy level, urgency
8. **Body shape** — contracted (resting) vs expanded (excited, curious)

### State → animation mapping

| State | Head | Body | Orb | Speed |
|---|---|---|---|---|
| exploring | tilted 10° | slight lean forward | slow pulse | gentle |
| building | straight | upright, solid | steady glow | purposeful |
| focused | minimal movement | still | bright point | none |
| reflecting | tilted upward | slightly contracted | dim, slow | slow |
| playful | rapid small tilts | light bounces | colour shifts | quick |
| resting | downward | contracted | minimal | none |

---

## Required Python modules

### Phase 5 — to build

**`core/emotion_engine.py`** (next)
Maps state + detected emotion + mode → `{emotion, intent, energy, posture, pace}`

**`core/avatar_bridge.py`** (next)
Packages core signals into a clean dict for any avatar/animation consumer.
Single function: `get_avatar_signal(state, emotion, mode, memory)` → dict

**`core/visual_memory.py`** (next)
Reads memory, groups into clusters, builds spatial world graph.
Returns `MemoryWorld` dict ready for any renderer.

**`avatar/` directory** (Phase 5)
```
avatar/
├── renderer.py        ← base renderer interface (same pattern as PluginBase)
├── terminal.py        ← ASCII art renderer (works now, no deps)
├── canvas_2d.py       ← tkinter 2D renderer (Phase 5 desktop)
└── unity_bridge.py    ← JSON bridge to Unity Animator (for eLo-Planet)
```

---

## Data flow — full path

```
User: "I'm exhausted trying to organise the Sugarcore notes"

1. state_engine.update()
   → state: "resting" (forced by exhausted signal)

2. emotion_engine.from_state()
   → emotion: "gentle"
   → intent: "hold_space"
   → energy: 0.2

3. avatar_bridge.get_signal()
   → {state, emotion, intent, energy, posture: "contracted", orb: 0.2}

4. Renderer receives signal
   → eLo settles, orb dims, no movement

5. memory_engine: visual_memory.build_world("sugarcore")
   → 17 items grouped into 5 clusters
   → bridge weights calculated from concept_pairs

6. eLo speaks:
   "You have 17 Sugarcore notes.
   I've grouped them: Story (7) · Enemy Design (4) · Levels (3) · Dialogue (2) · Future (1)"

7. Avatar renders the world:
   [floating islands in 2D canvas]
```

---

## Implementation order (Phase 5)

1. `core/emotion_engine.py` — signal generation (pure Python, no deps)
2. `core/avatar_bridge.py` — signal packaging
3. `core/visual_memory.py` — memory world builder
4. `avatar/terminal.py` — ASCII renderer (test the whole pipeline, no GUI needed)
5. `avatar/canvas_2d.py` — tkinter desktop canvas (first visual version)
6. Integration with `core_engine.py` — signal emitted on every turn

---

*The long arc:*
*Children's book character → Game character → AI personality → Voice → 3D character → Physical Orb → Embodied companion*
*Same identity throughout. The embodiment changes. eLo doesn't.*
