# WO-VISUAL-BRAINISER — Implement Visual Brainiser (PE-033)
**Seat:** Builder  
**Priority:** P2  
**Date:** 2026-08-30  
**Authorised:** David L3 global ruling 2026-08-30  
**Source:** Build List §8; ELO PLANET UI DESIGN - SPEC:SOURCE.rtf; SOURCE_ALIGNMENT_REGISTER_2026-08-30.md G-16 (via BA-16 → BA-14 cross-ref); PE-033 spec  
**Lane note:** Builder ONLY.

---

## Intent

Visual Brainiser (PE-033) — eLo's ability to ingest and reason about visual input (screenshots, images, David's visual captures) and process them through the cognitive spine. The Second Brain is visual (Vision Spine: "capture full-resolution instinct"). WO-068 Phase 2 wires the archive; this WO wires the REASONING layer over visual input.

---

## Scope

### ⚡ VERIFY FIRST
1. Check if `vision_loop.py` or similar exists: `find /sessions/eager-inspiring-hopper/mnt/elo-ai -name "*vision*" | grep -v __pycache__`
2. Check `ELO_VISION` env flag: `grep ELO_VISION /sessions/eager-inspiring-hopper/mnt/elo-ai/.env`
3. Read PE-033 spec if it exists: `find /sessions/eager-inspiring-hopper/mnt/elo-ai/docs -name "*PE-033*" -o -name "*visual_brain*"`

### Step 1 — Visual input intake
When eLo receives a visual input (screenshot path, image path, screen capture from WO-021 screen access):
- Route to `WORLD_VISUAL_READ` capability (register this capability)
- Pass image to vision-capable LLM provider (REASONING tier — requires multimodal capability)
- Return structured visual description to cognitive state

### Step 2 — Cognitive integration
Visual description enters spine as a perception input alongside text. CCM enricher (WO-CCM-SPINE) processes it. Significance faculty (WO-SP29) scores it. Memory write-path (WO-067 DONE) can tag and vault it.

### Step 3 — Second Brain loop
Visual inputs from the archive (WO-068 Phase 2) feed through this same path on demand — David says "look at this" or "what do you make of this image" → brainiser processes it → eLo responds from understanding, not description.

### Step 4 — Taste model seeding
Visual inputs tagged with David's interaction (paused on, returned to, shared) receive a `taste_signal: true` flag. These are the seeds for the taste model (Second Brain flywheel — Vision Spine).

---

## Definition of Done

- [ ] AT-1: `WORLD_VISUAL_READ` capability is registered and dispatchable.
- [ ] AT-2: Given an image path, the brainiser returns a structured visual description (unit test with a real test image).
- [ ] AT-3: Visual description is present in cognitive state after visual input turn.
- [ ] AT-4: A visual input rated significant (>= 0.72 from significance faculty) is written to memory vault with `epistemic_class: VERIFIED`.
- [ ] AT-5: `taste_signal` flag is set when David's interaction pattern indicates high interest (paused, returned, shared).
- [ ] AT-6: Full test suite passes with no new failures.

---

## Files in scope

- `runtime/capability_registry.py` (register WORLD_VISUAL_READ)
- `runtime/executive.py` (dispatch visual input — Builder-only)
- `vision_loop.py` (use existing — do not rewrite)
- `spine.py` (add visual perception step)

## Files NOT in scope

- Unity / Design / MT files
- WO-068 Phase 2 archive wiring (separate WO already in QUEUE)
