# WO-DREAM-STATE — Executive Dream/Sleep Processing Window
**Seat:** Builder  
**Priority:** P1  
**Date:** 2026-08-30  
**Authorised:** David L3 global ruling 2026-08-30 (no gates; no Presentable v1 gate)  
**Source:** ELO_SOURCE ARCHITECTURE + DRIFT AUDIT §10; SOURCE_2026-08-30_dream_state_ruling.md; Vision Spine (eLo has a Dream State — sleep is active, not off)  
**Lane note:** Builder ONLY. No other seat touches executive.py.

---

## Intent (verbatim source)

> "When eLo sleeps, he is not switched off. Sleep is a real internal state: memory consolidating, creative imagination running, experience processing."

David ruling 2026-08-30: Dream State is an **intended programme behaviour**, not a speculative feature. The machinery already exists: `faculties/dream/dream_faculty.py`, `creative_imagination.py` (spine.py LOOP-8), memory write-path (WO-067-WRITE-PATH DONE). The missing piece is the **Executive recognising `asleep: true` as a processing window** and dispatching to that machinery.

---

## Scope

1. **Read `asleep` signal** — `executive.py` reads `asleep` field from `blender_state.json` (written by WO-MOBILE-PHASE2, already live).
2. **Dream window dispatch** — When `asleep: true`, Executive enters a Dream Processing window:
   - Invoke `dream_faculty.py` (processing cycle, not a user-facing response).
   - Invoke `creative_imagination.py` (already wired to LOOP-8 — verify it also runs in asleep window).
   - Invoke memory consolidation write (contextual_state + experiences categories, using write-path live from WO-067).
3. **Boundary: output stays internal** — Dream window output is NEVER surfaced to David as a message. It writes to memory/vault/dream log only. No response emitted.
4. **Dream log write** — Append dream window activity to `data/dream_log.jsonl` (create if absent): `{ts, cycle_type, faculty_outputs_summary, memory_written: bool}`.
5. **Exit condition** — When `asleep` returns to `false`, dream window halts cleanly. No state leaks into the next waking turn.

---

## Definition of Done

- [ ] AT-1: With `asleep: true` in blender_state.json, Executive enters dream window and does NOT emit any user-facing response.
- [ ] AT-2: `dream_log.jsonl` is written with a valid entry after a dream cycle completes.
- [ ] AT-3: `dream_faculty.py` is invoked during asleep window (log evidence or unit assertion).
- [ ] AT-4: `creative_imagination.py` runs during asleep window (LOOP-8 or asleep branch — confirm one path).
- [ ] AT-5: When `asleep` flips to `false`, next waking turn is clean (no dream state leakage in response).
- [ ] AT-6: Full test suite (`python3 -m pytest tests/`) passes with no new failures.

---

## Files in scope

- `runtime/executive.py` (Builder-only; read `asleep`, dispatch dream window)
- `faculties/dream/dream_faculty.py` (invoke)
- `creative_imagination.py` (verify asleep path)
- `data/dream_log.jsonl` (create)

## Files NOT in scope

- `blender_state.json` (read-only — asleep signal already written)
- Any Unity/Design/MT files

---

## ⚡ VERIFY FIRST

Check: does `dream_faculty.py` already have a runnable `process()` or `cycle()` method? Run `python3 -c "from faculties.dream.dream_faculty import DreamFaculty; print(dir(DreamFaculty()))"`. If it does, integrate that; do not rewrite it.
