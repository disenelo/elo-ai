# WO-B1-0129 — Model swap: pin inner thought to reply model
**Seat:** Builder 1  
**Priority:** P1 — 5s latency gap  
**Date:** 2026-10-12  
**Source:** WO-B1-0118 filing — Board decision deferred from latency card

---

## What

0118 latency fix gets to ~10s. Final 5s gap: Ollama reloads qwen2.5-coder:14b after inner thought loaded mistral-nemo:12b. Option 1 (Board recommendation): set `ELO_INNER_THOUGHT_MODEL=qwen2.5-coder:14b` — one model stays warm, no swap overhead.

## Fix

`.env`: `ELO_INNER_THOUGHT_MODEL=qwen2.5-coder:14b`

`faculties/inner_thought/early_runner.py`: read `ELO_INNER_THOUGHT_MODEL` from env instead of hardcoded mistral-nemo:12b. Same pattern as `ELO_OLLAMA_MODEL` in backend_router.

## Done when

3 consecutive turns, CT0031 log shows `load_duration` ≈ 0ms (no model swap). Total turn time ≤ 8s. File to Board: before/after load_duration from CT0031 log.

*Board · Lead Architect · 2026-10-12*
