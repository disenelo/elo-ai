# WO — Builder Expression / Creative Mode (RTR-020)

**Owner:** Builder
**Priority:** P2
**Status:** DISPATCHED 2026-08-30
**Spec:** `docs/architecture/specs/SPEC_builder_expression_2026-08-30.md`
**Source:** `docs/architecture/_intake/SOURCE_2026-08-30_david_global_authorisation.md` — "G-07 not started start it, get the R&D spec→BA-13" [DAVID]
**Planetary source:** `docs/architecture/_intake/SOURCE_2026-08-30_planetary_kernel_living_presence_pool.md` — SUN (Builder/Capricorn) + GEMINI Explorer Child

---

## Intent

When eLo is in building/creative mode it speaks and operates differently — structured, committed, output-oriented. This is not a personality shift; it is a mode emphasis. RTR-020 specifies Builder expression as one of eLo's named creative modes. Currently not wired.

## Scope

### A. Register BUILD mode in the Mode Engine (WO-PLANETARY-KERNEL dependency)

WO-PLANETARY-KERNEL creates the Mode Engine (BUILD / PLAY / EXPLORE / REFINE) and `kernel/voice_pool.yaml`. This WO assumes that is done. If not, do WO-PLANETARY-KERNEL first.

### B. Wire BUILD mode language constraints into `language_faculty.py`

When mode = BUILD:
- Language is structured, sequential, output-first
- Voice: "Make it real." / "Build before announcing." / "One thing at a time." / "Finish before replacing."
- Outputs have a clear next action — not open-ended
- No tangential expansion unless David explicitly asks
- Reduces option-generation; produces the thing, not a menu of things

### C. Gemini Explorer Child — EXPLORE mode complement

When mode = EXPLORE:
- Language is connective, curious, remix-oriented
- Voice: "Try three versions." / "Curiosity before perfection." / "Play reveals structure."
- Generates variation, not completion
- Short-horizons on each variant — prototype, don't perfect

### D. Mode switching trigger

Builder (SUN) and Explorer (GEMINI) combine as: `Dream → Sort → Build → Test → Play → Refine`
NOT: `Dream → Perfect → Freeze`

Mode switching is determined by the Mode Engine in spine.py (WO-PLANETARY-KERNEL). This WO wires the language output layer for each mode, not the switching logic itself.

## Definition of Done

BUILD mode → eLo response contains a clear next action, not a menu. EXPLORE mode → eLo response contains variation, not finalisation. Both verifiable without David.

## Acceptance Tests (self-running, no David)

1. BUILD mode + creative input → response has one clear next action, no option list
2. BUILD mode → response does not contain "you could also" or similar branching phrases
3. EXPLORE mode + same input → response generates 2-3 variations, not one definitive answer
4. EXPLORE mode → response does not finalise ("the best option is…")
5. Mode switch within turn → language register shifts detectably between BUILD and EXPLORE outputs

## VERIFY FIRST

```bash
grep -n "mode" /sessions/eager-inspiring-hopper/mnt/elo-ai/runtime/spine.py | head -30
grep -rn "RTR.020\|builder_expression\|creative_mode" /sessions/eager-inspiring-hopper/mnt/elo-ai/
```

## Lane

Builder only. Runtime language shaping layer. No prompt changes.
