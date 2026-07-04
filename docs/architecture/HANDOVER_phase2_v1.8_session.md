# eLo OS Phase 2 — Handover: v1.8 Emotional Light Engine

## What you are

eLo OS AI Agent. You work strictly within `~/elo-ai/`. Never touch Unity `.cs` files.
Never modify `runtime/executive.py` or `prompts/` — protected by FREEZE_V1_LOCK.md.

## What v1.8 is

The Emotional Light Engine (ELE). A pure translation layer between the cognitive decision and every embodiment. It never reasons. Never decides. It only expresses what the Executive already decided.

**File**: `runtime/light_engine/light_engine.py`

## The two-plan boundary

```
Executive Faculty →  [COGNITIVE PLAN]  →  Emotional Light Engine  →  [PRESENCE PLAN]
                     (internal truth)      (pure translation)         (external truth)
                     emotional_vector                                  presence_plan
```

The ELE reads `plan.emotional_vector` (set by v1.5 Executive Faculty).
It writes `plan.presence_plan` (read by all embodiments: Unity, robot LEDs, desktop avatar).

## What was built

```python
# runtime/light_engine/light_engine.py

_STATE_TABLE = {
    # 20 states — each with H, S, V, pulse, pulse_speed, brightness, bloom,
    # movement_style, animation_profile, expression_profile,
    # voice_pacing, voice_energy, voice_warmth, transition_speed
    "calm":              dict(h=180, s=0.55, v=0.50, ...),
    "curiosity":         dict(h=200, ...),
    "creative_discovery":dict(h=175, ...),
    "momentum":          dict(h=35,  ...),
    "joy":               dict(h=45,  ...),
    "play":              dict(h=15,  ...),
    "reflection":        dict(h=270, ...),
    "repair":            dict(h=28,  ...),
    "comfort":           dict(h=158, ...),
    "connection":        dict(h=195, ...),
    "wonder":            dict(h=238, ...),
    "focus":             dict(h=210, ...),
    "celebration":       dict(h=46,  ...),
    "challenge":         dict(h=28,  ...),
    "listening":         dict(h=190, ...),
    "thinking":          dict(h=262, ...),
    "waiting":           dict(h=185, ...),
    "exploring":         dict(h=162, ...),
    "witnessing":        dict(h=248, ...),
    "neutral":           dict(h=185, ...),
}

_resolve_state(vec) -> str
    # Priority: use vec['state'] if it's a known ELE state.
    # Otherwise derive from vector values (curiosity, energy, calm, etc.)

translate(plan: CognitivePlan) -> CognitivePlan
    # Reads plan.emotional_vector → resolves state → builds PresencePlan
    # Secondary hue = (primary_hue_h + 180) % 360
    # Writes plan.presence_plan = pp.to_dict()
    # Returns the same plan object
```

## Colour system rules

- HSV: H = primary hue in degrees (0–360), S/V = 0.0–1.0
- Secondary hue = (H + 180) % 360 — direct opposite (complement)
- Unity and robot read H, S, V directly. No predefined named colours.
- Full table: `docs/architecture/11_emotional_light_engine.md`

## How to verify it works

```bash
cd ~/elo-ai
python3 -c "
from runtime.spine.plan import CognitivePlan
from runtime.spine.relationship_faculty import RelationshipContext
from runtime.spine.executive_faculty import enrich
from runtime.light_engine.light_engine import translate

plan = CognitivePlan(raw='yo building the os', conversation_action='build',
                     valence='positive', momentum='building', confidence=0.9)
rel  = RelationshipContext(relationship_type='creator', familiarity=0.95, trust=0.90)
plan = enrich(plan, rel, {})
plan = translate(plan)

pp = plan.presence_plan
print('state  :', pp['emotional_state'])       # creative_discovery
print('H      :', pp['primary_hue_h'])         # 175.0
print('sec H  :', pp['secondary_hue_h'])        # 355.0
print('bloom  :', pp['bloom'])                 # 0.52
print('robot  :', pp['robot_led_state'])        # turquoise
print('unity  :', pp['unity_material_profile']) # creative
print('keys   :', len(pp))                     # 20
"
```

## Freeze state

This commit is tagged: `v1.8-emotional-light-engine` and `phase2-complete`

What is frozen:
- `_STATE_TABLE` — the 20 emotional states, their H values, and the field names
- `translate()` interface: takes CognitivePlan, returns CognitivePlan (in-place)
- `_resolve_state()` logic — do not alter the priority order without spec review

Do not add reasoning logic to the ELE. If you find yourself wanting to "check context" or "look at memory" inside `light_engine.py`, stop — that belongs in the Executive Faculty.

## What comes next

- **Unity integration**: `handovers/UNITY_AGENT_HANDOVER_presence_plan.md` — Unity reads `presence_plan` from blender_state.json, applies HSV to EloBodyGlow.cs and EloOSChatTMP.cs. Unity Agent handover is ready.
- **Robot LED integration**: Pi 5 reads `presence_plan.robot_led_state` from blender_state.json (same file). Colour language: idle=teal, thinking=amber, speaking=coral, calm=violet.
- **Ambient engine feeding ELE**: random ambient events (wanders, micro-expressions, idle utterances) should eventually update `emotional_vector` and re-run translate() to shift the presence_plan.

---
Built: Phase 2 session — 2026-07-04
Status: LIVE ✅ ELE produces correct presence_plan, verified writing to blender_state.json
Full HSV table: docs/architecture/11_emotional_light_engine.md
