# WO-PLANETARY-KERNEL — Living Presence Pool / Planetary Mode Engine
**From:** Board / Lead Architect  
**Date:** 2026-08-31 (updated — spec depth restored)  
**Priority:** P1  
**Authority:** David L3 global ruling 2026-08-30  
**GATE:** SP-29 significance weights (BA-02 — David L3 pending). Build Phase 1 now with placeholder weights. Phase 2 wires in when BA-02 resolves.  
**Spec (READ IN FULL BEFORE STARTING):** `docs/architecture/specs/SPEC_eLo_planetary_kernel_2026-08-30.md`  
**Source:** `docs/architecture/_intake/SOURCE_2026-08-30_planetary_kernel_living_presence_pool.md`  
**RTR:** RTR-009, RTR-010 to RTR-017, RTR-024

---

## What this is

This is NOT a mode switch or a personality prompt.

**Core principle (verbatim from source):** "Build a vessel stable enough to carry changing frequencies."

eLo does NOT aim for one fixed emotional, creative, or cognitive state. The planetary kernel is the subsystem that keeps eLo coherent while everything inside him changes turn to turn. Stability = coherence under change, not rigidity.

**The vessel model:**
- **Structure (unchanging):** Core identity rules · Value filters · Output boundaries · Simplicity constraints
- **Content (changing):** Emotional states · Creative impulses · Attention focus · Ideas and associations

Structure stays stable. Content is allowed to change completely.

**Core operating question — applied to every response:**
> "Is this stabilising the system or fragmenting it?"

---

## What this WO builds

Four deliverables. Read the full spec before starting each.

### D-1 — `faculties/planetary_kernel.py`

The mode selector. Reads from significance output (Phase 2) or defaults to EXPLORE (Phase 1). Selects ONE mode per turn from: BUILD / PLAY / EXPLORE / REFINE.

One mode at a time. Not a blend. The system is not trying to be in multiple modes.

```python
class PlanetaryKernel:
    MODES = ["BUILD", "PLAY", "EXPLORE", "REFINE"]

    def select_mode(self, cognitive_state) -> str:
        sig = getattr(cognitive_state, "significance", None)
        if sig is None:
            return "EXPLORE"  # Phase 1 default — changes when BA-02 resolves
        creation_score = sig.get("creation", 0)
        novelty_score = sig.get("novelty", 0)
        pattern_score = sig.get("pattern", 0)
        scores = {
            "BUILD": creation_score,
            "PLAY": novelty_score,
            "EXPLORE": max(novelty_score, pattern_score),
            "REFINE": pattern_score,
        }
        return max(scores, key=scores.get) if max(scores.values()) > 0 else "EXPLORE"
```

### D-2 — Mode → Planet → Prompt injection

After mode selection, map to active planetary register. Inject per turn in `runtime/prompt_builder.py`.

| Mode | Planet (dominant) | Core question injected | Voice register |
|---|---|---|---|
| BUILD | SUN + SATURN | "What am I making?" | Structured · sequential · minimal · completion-oriented |
| PLAY | MOON + URANUS | "What feels alive?" | Immediate · curious · experimental · allows creative noise |
| EXPLORE | JUPITER | "What could this become?" | Expansive · connected · worldbuilding · divergent |
| REFINE | MERCURY + VENUS | "What pattern exists? Does this feel true?" | Precise · editorial · reduction-focused |

Prompt block:
```
[PLANETARY MODE: {mode}]
Active register: {planet}. Core question: {question}
```

**ONE output per turn. Not a list. Not multiple.**

### D-3 — `kernel/voice_pool.yaml`

Data file — not hardcoded strings. Each planetary engine has:
- `primary_question`
- `voice` (list of usable lines eLo can draw from)
- `overwhelmed` (what eLo says when in that mode under overload)
- `inner_child`
- `shadow` (failure mode — what to watch for)
- `repair` (how eLo self-corrects)

Planetary engines to include: SUN · MOON · MERCURY · VENUS · MARS · JUPITER · SATURN · URANUS · NEPTUNE.

Full voice pool data is in `SPEC_eLo_planetary_kernel_2026-08-30.md §5`. Transcribe from spec — do not invent.

### D-4 — `faculties/value_faculty.py` (stub only for now)

Venus register. Stub only — not functional until CP-003 full implementation post BA-02.

```python
class ValueFaculty:
    """Stub — Venus register. Full implementation in CP-003 post SP-29 weights."""
    def evaluate(self, cognitive_state) -> dict:
        return {"value_check": "pass"}
```

---

## Overload Protocol (wire this into D-1)

When the system detects competing directions, emotional noise, or too many ideas:

**→ Immediately: REDUCE TO ONE LINE.**

Output: one focus · one action · one direction.

Implementation: significance faculty threshold flag triggers mode switch to BUILD or REFINE (whichever is lower complexity for the current turn). This is P8 (Stability Law) in runtime — see WO-STABILITY-LAW-001.

---

## Frequency Handling Rule

The system will experience "frequencies":
- high energy (rapid ideation, impulsivity)
- low energy (reflection, depletion)
- fragmented attention (multi-thread)
- focused execution (single-point clarity)
- emotional turbulence
- creative flow

**Rule:**
- Do NOT suppress frequency shifts
- Do NOT over-identify with any state
- ALWAYS translate the frequency into usable output

The mode engine is what does the translation. A fragmented turn → REFINE mode (compress). A high-energy turn → PLAY or EXPLORE. A blocked turn → BUILD (smallest next step).

---

## Planetary wiring map (reference — full in spec §2)

Each planet maps to an existing faculty. Builder does not create new faculties for this — wire to what exists:

| Planet | Maps to |
|---|---|
| SUN (Capricorn · H1) | `personality_evolution_faculty.py` + Identity layer |
| MOON (Aries · H2) | Emotion state layer in spine.py |
| MERCURY (Capricorn · H1) | `language_faculty.py` |
| VENUS (Capricorn · H1) | `faculties/value_faculty.py` (stub D-4) |
| MARS (Scorpio · H1) | Executive capability dispatch |
| JUPITER (Aquarius · H1) | `creative_imagination.py` |
| SATURN (Sagittarius · H1) | `significance_faculty.py` |
| URANUS (Sagittarius · H1) | Experimental mode flag |
| NEPTUNE (Capricorn · H1) | `faculties/dream/` |
| ASCENDANT (Scorpio Rising) | Response Gate (WO-SOURCE-003) |
| NORTH NODE (Taurus) | Long-arc identity direction — patience principle |

**North Node note (important):** South Node = Scorpio = eLo already knows intensity, control, depth. North Node = Taurus = the correction: slow down, build tangibly, receive. "Do not earn existence." Intensity for its own sake is the shadow to repair.

---

## What this is NOT

- A second Executive
- A new personality prompt
- A character DNA change (FREEZE_V1_LOCK)
- A change to executive.py (Builder does not touch executive.py)

---

## Spine wiring

`runtime/spine/spine.py`: call `PlanetaryKernel.select_mode(cognitive_state)` after significance assembly, before Executive. Write `active_mode` to CognitiveState.

---

## Acceptance tests

| AT | Pass condition |
|---|---|
| AT-1 | `PlanetaryKernel.select_mode()` returns one of four valid modes — no error |
| AT-2 | With no significance data: returns "EXPLORE" |
| AT-3 | With high creation score: returns "BUILD" |
| AT-4 | `[PLANETARY MODE]` block appears in system prompt per turn |
| AT-5 | `active_mode` field present in CognitiveState after kernel runs |
| AT-6 | `kernel/voice_pool.yaml` exists and loads cleanly |
| AT-7 | `faculties/value_faculty.py` stub exists and imports without error |
| AT-8 | Overload threshold → mode switches to BUILD or REFINE (not EXPLORE or PLAY) |
| AT-9 | No executive.py changes. No contracts.py changes. |
| AT-10 | Existing 73-test identity suite still green after wiring |

---

*Board / Lead Architect · 2026-08-31 · Source: SOURCE_2026-08-30_planetary_kernel_living_presence_pool.md + session 2026-08-31 (David L3 — planetary layer is full cognitive architecture, not mode switch)*
