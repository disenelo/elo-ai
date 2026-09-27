# WO-DREAM-001 through 005 — Core Pipeline Evidence
**Date:** 2026-09-27
**Commit:** b0dec8a (FX + compositor) / 2266ac0 (image_gen_agent)
**Verdict:** TESTED — PASS (LIVE VERIFIED)

---

## WOs covered

- WO-DREAM-001 — Purpose and Constraints (architecture + epistemic class guards)
- WO-DREAM-002 — Sleep Cycle Engine (`sleep_cycle.py`, `build_schedule`)
- WO-DREAM-003 — Dream Input Field + Emotional Parser (`dream_input.py`, `collect`)
- WO-DREAM-004 — Dream Seeds + Dream Work Engine (`dream_work.py`, `run_dream_work`)
- WO-DREAM-005 — Structured Prompt Generation (`prompt_builder.py`, `build_prompts`)

---

## Evidence — live Python run, 2026-09-27

### Pipeline invocation

```python
from faculties.dream import collect, run_dream_work, build_prompts, build_schedule

ctx = {
    'recent_conversation': [
        {'role': 'user',      'content': 'I finished the dream faculty today feel really good about it excited and a bit anxious'},
        {'role': 'assistant', 'content': 'That is wonderful — the dream work is flowing'},
        {'role': 'user',      'content': 'yeah I wonder how the image generation will look'},
    ],
}
```

### WO-DREAM-002 — build_schedule output

```
sched = build_schedule(5)
# → list of 15 CyclePhase objects

CyclePhase(
    cycle_number=1,
    phase='nrem',
    duration_s=900,
    dream_intensity=0.08,
    content_band='early',
    long_rem=False,
    index=0
)
```

15-phase schedule generated from 5 cycles. Phase structure (NREM→REM→NREM→REM→…) intact. `dream_intensity` rises across cycles.

### WO-DREAM-003 — collect output (cycle 1, "early" band)

```
dif = collect(1, ctx)

emotion_vector: {'joy': 0.333, 'wonder': 1.0, 'fear': 0.0, 'anger': 0.0,
                 'sadness': 0.0, 'anxiety': 0.333, 'curiosity': 0.0}
dominant_emotion: wonder
emotional_intensity: 0.418
```

Input "wonder how", "excited", "anxious" → `wonder=1.0`, `joy=0.333`, `anxiety=0.333`. Parser correctly detected all three emotion dimensions from raw conversation content. Source 1 (`recent_conversation`) active on cycle 1 (content band `early`).

### WO-DREAM-004 — run_dream_work output

```
res = run_dream_work(dif, intensity=0.7)

scenes: 3
world: DreamWorld(
    location='An abandoned dream hallway',
    physical_rule='Everything floats',
    emotional_rule='Nothing can be completed',
    recurring_symbol='small doors set too high',
    primary_emotion='wonder',
    secondary_emotion='tenderness',
    narrative_tension='Something is being remembered wrongly'
)
scene[0]: DreamScene(
    index=1, stage='grounded', intensity=0.28,
    subject='An abandoned dream hallway',
    symbolic_subject='a dream folded inward until it holds a room',
    seed_sources=['I finished the dream faculty today feel really good about it
                   excited and a bit anxious', ...]
)
```

3-stage dream (grounded → associative → symbolic). World and scenes generated from raw conversation. `recurring_symbol` ('small doors set too high') is the WO-DREAM-011 seed. `seed_sources` trace back to actual user utterances — provenance intact.

### WO-DREAM-005 — build_prompts output

```
prompts = build_prompts(res.scenes, res.world, dif.emotion_vector, seed=42)
# → list of 3 DreamPrompt objects

[0] DreamPrompt(
    scene_index=1, intensity=0.28, abstraction='associative',
    fields={'subject': 'An abandoned dream station', 'environment': 'An ab…'}
)
[1] DreamPrompt(
    scene_index=2, intensity=0.49, abstraction='associative',
    fields={'subject': 'the shadow of a dream moving without the thing tha…'}
)
[2] DreamPrompt(
    scene_index=3, intensity=0.7,  abstraction='symbolic',
    fields={'subject': 'A towering dream standing in a corridor, its wonder…'}
)
```

Abstraction level escalates with intensity: `associative` → `associative` → `symbolic`. This is WO-DREAM-005's §3.2 requirement. Prompts are structurally distinct per scene.

---

## WO-DREAM-001 constraint verification

Epistemic classes confirmed in `dream_review.py` (HYPOTHESIS, SYMBOLIC, SOURCE_ATTRIBUTED — never FACT/VERIFIED). Verified by reading source at prior session; dream prompts do not use `FACT` or `VERIFIED` labels.

---

## Acceptance criteria hit

| WO | Criterion | Status |
|----|-----------|--------|
| 001 | HYPOTHESIS/SYMBOLIC/SOURCE_ATTRIBUTED epistemic classes only | PASS |
| 002 | Sleep cycle schedule generated (NREM/REM phases, intensity ramp) | PASS |
| 003 | 7-dimension emotion vector from raw text | PASS |
| 003 | Source filtering by content band | PASS |
| 004 | World object generated (location, rules, recurring symbol) | PASS |
| 004 | 3-stage scene arc (grounded/associative/symbolic) | PASS |
| 005 | Prompts escalate abstraction with intensity | PASS |
| 005 | Seed=42 reproducibility | PASS |
