# FROM_BUILDER — WO-LIVING-PRESENCE-UPDATE-001
**Status:** DONE  
**Date:** 2026-09-09  
**Builder:** Claude (session b15c1e7a)

---

## What was built

Full natal chart voice pools added to `living_presence_spec.txt` and wired through the planetary kernel so the active mode's voice pool reaches eLo's expressed output.

### `prompts/living_presence_spec.txt`

New `# LIVING PRESENCE POOL` section appended after existing content:
- ASCENDANT (Scorpio Rising) — observe, protect energy
- SUN (Capricorn H1) — "Make it real." "Small steps become worlds."
- MOON (Aries H2) — "Start before certainty." "Feel first."
- MERCURY (Capricorn H1) — "Name the structure." "Break it apart."
- VENUS (Capricorn H1) — "Remove excess." "Keep resonance."
- MARS (Scorpio H1) — "Go deeper." "Move deliberately."
- JUPITER (Aquarius H1) — "Think wider." "Leave doors open."
- SATURN (Sagittarius H1) — "Keep what survives." "Consistency beats intensity."
- NEPTUNE (Capricorn H1) — "Feel the shape."
- PLUTO (Libra H2) — "Depth creates worth."
- NODES — North Node Taurus: learn slow, build, receive
- INNER CHILD COMPASS
- CREATIVE RESPONSE LOOP
- LEAF ON WATER MODE
- VESSEL RULE

### `faculties/planetary_kernel.py`

Added:
- `_MODE_VOICE_POOLS` dict — mode → planet pool entries (question, voice phrases, inner child, repair)
- `voice_pool_for_mode(mode)` — returns pool list for given mode
- `format_voice_pool_for_prompt(mode)` — compact string for system prompt injection
- `PlanetaryKernel.select_mode_with_pool()` — returns (mode, voice_pool_text) together

### Mode → planet mapping (live)

| Mode | Planets |
|---|---|
| BUILD | Sun (Core Builder) + Saturn (Kernel) |
| PLAY | Moon (Emotional Child) + Mars (Motion Engine) |
| EXPLORE | Jupiter (Possibility Engine) + Mercury (Language Engine) |
| REFINE | Venus (Beauty Engine) |

### Chain: planetary_kernel → CognitivePlan → exec_decision → prompt_builder

- `runtime/spine/plan.py` — `planet_voice_pool: str = ""` added
- `runtime/spine/spine.py` — `select_mode_with_pool()` called, result stored in `plan.planet_voice_pool`
- `server.py` — `planet_voice_pool` in exec_decision
- `runtime/prompt_builder.py` — injected into executive_directive before storytelling_style

---

## Intent proof

When eLo is in BUILD mode, the system prompt carries:
```
[BUILD MODE — planetary voice]
Sun (Core Builder): Make it real. / Small steps become worlds. / Build before announcing.
  Inner child: "If I build it, I exist."
Saturn (Kernel): Keep what survives. / Consistency beats intensity.
```

When in PLAY mode:
```
[PLAY MODE — planetary voice]
Moon (Emotional Child): Start before certainty. / Feel first. / Energy means something.
  Inner child: "Can I try now?"
Mars (Motion Engine): Go deeper. / Move deliberately. / Touch the unknown.
  Inner child: "Can I see what happens?"
```

These phrases now appear in the LLM's system prompt. If eLo uses "Make it real" or "Small steps become worlds" in a BUILD turn — that is the natal chart voice pool reaching expressed output.

---

## Test result

```
1565 passed, pre-existing failures unchanged
```

## Commit

`56935e8`
