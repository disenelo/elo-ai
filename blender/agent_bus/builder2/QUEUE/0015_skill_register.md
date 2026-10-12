# WO-B2-0015 — Skill register
**Seat:** Builder 2  
**Priority:** P2  
**Date:** 2026-10-12  
**Source:** IS ELO REMAINING-DOMAINS — SKILLS & HABITS domain

---

## What

eLo has no concept of his own skills developing. He doesn't track what he's gotten better at, what he's failed at repeatedly, or what he's learned to do reliably. `self_improvement/` exists but nothing measures competence.

## What to build

1. `data/skill_register.json` — list of skills with fields: `skill_id`, `name`, `skill_type` (PROCEDURAL | CONVERSATIONAL | TOOL | EMBODIMENT), `confidence_score` (0-1), `last_updated`, `evidence[]`
2. SPG updates confidence scores from scored events — high-significance positive events increase score, failures decrease
3. Builder 3: `capability_registry.py` to track success rate per tool — feeds into skill_register for TOOL type skills
4. eLo can answer "what are you good at?" and "what are you still learning?" from the register

## Done when

`skill_register.json` populated with ≥5 skills. SPG scoring live. eLo answers "what are you good at?" with real confidence scores, not generated. File to Board: the register contents, the retrieval, the response.

*Board · Lead Architect · 2026-10-12*
