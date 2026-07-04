# eLo OS Phase 2 — Handover: v1.6 Cognitive Plan Object

## What you are

eLo OS AI Agent. You work strictly within `~/elo-ai/`. Never touch Unity `.cs` files.
Never modify `runtime/executive.py` or `prompts/` — those are protected by FREEZE_V1_LOCK.md.

## What v1.6 is

The Cognitive Plan Object. The single runtime object that carries one decision per turn through every layer of the system.

**File**: `runtime/spine/plan.py`

## What was built

```python
# runtime/spine/plan.py

@dataclass
class EmotionalVector:
    state:       str   = "neutral"   # canonical ELE state name
    energy:      float = 0.50
    warmth:      float = 0.55
    curiosity:   float = 0.50
    focus:       float = 0.50
    playfulness: float = 0.40
    confidence:  float = 0.55
    reflection:  float = 0.30
    momentum:    float = 0.50
    connection:  float = 0.55
    calm:        float = 0.50
    def to_dict(self) -> dict: ...

@dataclass
class PresencePlan:
    primary_hue_h:       float = 185.0
    primary_hue_s:       float = 0.55
    primary_hue_v:       float = 0.72
    secondary_hue_h:     float = 5.0    # (primary_hue_h + 180) % 360
    pulse_profile:       str   = "slow"
    pulse_speed:         float = 0.50
    brightness:          float = 0.65
    bloom:               float = 0.30
    animation_profile:   str   = "calm"
    idle_profile:        str   = "ambient"
    movement_style:      str   = "gentle"
    expression_profile:  str   = "open"
    desktop_presence:    str   = "ambient"
    emotional_state:     str   = "calm"
    voice_energy:        float = 0.50
    voice_pacing:        str   = "measured"
    voice_warmth:        float = 0.70
    transition_speed:    float = 2.0
    robot_led_state:     str   = "teal"
    unity_material_profile: str = "calm"
    def to_dict(self) -> dict: ...

@dataclass
class CognitivePlan:
    # ... all existing v1 fields (raw, meaning, intent, etc.) ...

    # v1.4 — Relationship Faculty additions
    relationship_type:   str   = ""
    familiarity:         float = 0.50
    trust:               float = 0.50
    expression_posture:  str   = "open"
    active_projects:     list  = field(default_factory=list)

    # v1.6 — Presence Plan additions
    emotional_vector:    dict  = field(default_factory=dict)
    presence_plan:       dict  = field(default_factory=dict)
```

## How to verify it works

```bash
cd ~/elo-ai
python3 -c "
from runtime.spine.plan import CognitivePlan, EmotionalVector, PresencePlan

# EmotionalVector to_dict
ev = EmotionalVector(state='creative_discovery', energy=0.82)
d = ev.to_dict()
print('ev keys:', list(d.keys()))   # 11 keys

# PresencePlan to_dict
pp = PresencePlan()
d = pp.to_dict()
print('pp keys:', len(d), 'emotional_state:', d['emotional_state'])  # 20 keys, calm

# CognitivePlan has presence_plan field
plan = CognitivePlan(raw='test')
print('plan.presence_plan:', plan.presence_plan)  # {}
print('plan.emotional_vector:', plan.emotional_vector)  # {}
"
```

## The two-plan boundary

```
[COGNITIVE PLAN]    internal — everything the brain decided
        ↓
[Emotional Light Engine]   pure translation — never reasons
        ↓
[PRESENCE PLAN]     external — what every embodiment reads
```

`CognitivePlan` carries both for transport. All embodiments read `presence_plan` only. They never read `emotional_vector` directly.

## Freeze state

This commit is tagged: `v1.6-cognitive-plan`

What is frozen at this tag:
- `plan.py` — `PresencePlan` field names and types (Unity reads these from blender_state.json)
- `plan.py` — `EmotionalVector` field names (Light Engine reads these)

Do NOT rename fields in `PresencePlan` without updating:
- `blender_bridge/state_writer.py` (writes to JSON)
- Unity scripts that read `presence_plan.*` from blender_state.json

## What the next session (v1.7) builds on top of

v1.7 — Spine Runtime Alignment: `spine.py` wires all faculties in the correct order. The Cognitive Plan flows from Language Faculty through Relationship → Executive → Enrich → Light Engine → Conversation Faculty. One plan object, one direction.

---
Built: Phase 2 session — 2026-07-04
Status: LIVE ✅ plan.py ships with all three dataclasses — tested in server pipeline
