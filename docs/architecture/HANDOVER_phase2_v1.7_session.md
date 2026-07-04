# eLo OS Phase 2 — Handover: v1.7 Spine Runtime Alignment

## What you are

eLo OS AI Agent. You work strictly within `~/elo-ai/`. Never touch Unity `.cs` files.
Never modify `runtime/executive.py` or `prompts/` — those are protected by FREEZE_V1_LOCK.md.

## What v1.7 is

The Spine Runtime Alignment. `spine.py` is the main entry point — it orchestrates every faculty in sequence and returns one CognitivePlan per turn.

**File**: `runtime/spine/spine.py`

## The canonical pipeline

```
spine.run(raw, state, memory_pack, attention)
    │
    ├── Language Faculty      _language_faculty(raw)
    │   (normalise, typo repair, intent detect)
    │
    ├── Relationship Faculty  rel_analyse(raw, memory_pack)
    │   (who is speaking, familiarity, trust, register)
    │
    ├── Capability Faculty    _capability_faculty(meaning, intent)
    │   (candidate capabilities — no decision)
    │
    ├── System Faculty        _system_faculty(meaning)
    │   (detect system control intents)
    │
    ├── Executive Faculty     _executive_faculty(raw, language, attention, caps, sys)
    │   (the ONLY decision maker — produces initial CognitivePlan)
    │
    ├── Executive Enrich      enrich(plan, relationship, attention)         ← v1.5
    │   (stamps relationship context + emotional_vector onto plan)
    │
    ├── Light Engine          translate(plan)                               ← v1.8
    │   (maps emotional_vector → presence_plan — never reasons)
    │
    └── Conversation Faculty  _conversation_faculty(plan)
        (direct response for social/system turns; LLM handles the rest)
```

## How to verify it works end-to-end

```bash
cd ~/elo-ai

# Full pipeline test
python3 -c "
from runtime.spine.spine import run
plan = run('yo building the os', state={}, attention={
    '_exec_decision': {
        'action': 'build', 'valence': 'positive', 'momentum': 'building',
        'tone': 'DIRECT', 'max_sentences': 3, 'response_goal': 'answer',
        'cal_reason': '', 'register': ''
    }
})
print('action         :', plan.conversation_action)          # build
print('ev state       :', plan.emotional_vector.get('state'))# creative_discovery
print('pp state       :', plan.presence_plan.get('emotional_state'))  # creative_discovery
print('pp H           :', plan.presence_plan.get('primary_hue_h'))    # 175.0
print('pp bloom       :', plan.presence_plan.get('bloom'))             # 0.52
print('pp robot LED   :', plan.presence_plan.get('robot_led_state'))   # turquoise
print('pp keys        :', len(plan.presence_plan))                     # 20
"

# Verify it reaches blender_state.json
curl -s -X POST http://localhost:5050/chat -H 'Content-Type: application/json' \
  -d '{"text":"yo building the os"}' > /dev/null
python3 -c "
import json; d = json.load(open('blender/blender_state.json'))
pp = d.get('presence_plan', {})
print('in file:', bool(pp), '| state:', pp.get('emotional_state'))
"
```

Expected: `pp state: creative_discovery | H: 175.0 | bloom: 0.52`

## The write fix (critical — do not revert)

The `presence_plan` write in `server.py` is isolated in its own try/except block. It comes AFTER the main avatar computation block. Before the fix, the write was trapped inside the same try block as `_pstate_derive()` etc. and was silently abandoned when any earlier call failed.

```python
# server.py — correct pattern
_cmd = {"animation": "idle", ...}  # safe defaults before the try
_expr = None
_emotion = None
try:
    _cmd = _avatar_cmd(_pstate)
    # ... other avatar work ...
    _emotion = _expr_map_emotion(...)
except Exception:
    pass

# Write is in its own block — always runs
try:
    _pp = _plan.presence_plan if _plan and _plan.presence_plan else None
    if _pp:
        _state_write_presence(_cmd, _expr, _presence, _emotion, _pp)
    else:
        _state_write(_cmd, _expr, _presence, _emotion)
except Exception:
    pass
```

## Freeze state

This commit is tagged: `v1.7-spine-aligned`

Also tagged: `v1.8-emotional-light-engine` and `phase2-complete` (same commit — all versions shipped together).

What is frozen:
- `spine.py` — faculty order is canonical. Do not reorder without architecture review.
- The `attention['_exec_decision']` contract between `server.py` and `spine.py`
- The two-plan boundary: Light Engine receives `emotional_vector`, writes `presence_plan`

## What comes next

The pipeline is complete. Future sessions build on top of this:

- **Random ambient behaviors** — events that feed into the ELE and update presence_plan without user input (idle wanders, unprompted observations, micro-expressions)
- **Relationship Faculty spec** — `docs/architecture/05_relationship_faculty.md` is a stub; deserves a dedicated session
- **Unity integration** — `handovers/UNITY_AGENT_HANDOVER_presence_plan.md` defines how Unity reads `presence_plan` from blender_state.json

---
Built: Phase 2 session — 2026-07-04
Status: LIVE ✅ server running, presence_plan verified in blender_state.json
Git tag: phase2-complete (+ v1.4 through v1.8 tags, all same commit)
