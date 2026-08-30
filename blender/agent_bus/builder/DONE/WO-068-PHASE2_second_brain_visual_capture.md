# WO-068 Phase 2 — Second Brain: Visual Capture + Vision Recall

**Owner:** Builder (eLo OS — Python only)
**Priority:** P1 — David explicitly asked why this was paused (2026-08-30). Board deferred it; David did not.
**Status:** DISPATCHED 2026-08-30
**Depends on:** WO-068 Phase 1 ✅ DONE · WO-067 write-path ✅ DONE · `tools/vision_loop.py` ✅ live · `ELO_VISION` on · WO-021 screen access ✅ live
**Source:** WO-068 §Phase 2 (verbatim David 2026-08-07) + David ruling 2026-08-30 (unblock now)
**LANE:** Builder Python only. No executive.py (Builder-only per new rule, but not needed here).

---

## David's intent (verbatim, WO-068 §Phase 2)

> "A text note is you at ~50 bits/sec transcribing what your brain ingested at ~10M bits/sec — it drops the 99% you felt but can't word. A screenshot keeps the whole signal cheaply (~a couple hundred tokens), and AI vision can read the archive back into the principles you couldn't name. Capture what stops you — screenshots + transcripts + drafts — into an archive, don't pre-sort; let eLo's vision study the whole folder and, walking it with David, turn 'why this is here' into an instruction set; then create FROM the archive, never from blank."

**The iteration loop (David 2026-08-07 — flywheel, not a one-shot):**
CAPTURE → BUILD → FEED BACK → REFINE. Built assets feed BACK into the second brain as new reference. Taste model sharpens every cycle.

**Creative engine prompt (David verbatim — canonical, do not reword):**
```
You are the creative engine for this brain. The files in this folder are its second brain: a curated
archive of screenshots, writing, products, interfaces, typography, ideas, and cultural references. Study
them to understand the brand's taste, values, patterns and point of view. Do not copy any single reference.
Collage, remix and translate their underlying principles into one coherent, recognisable brand system.

Use that system to create whatever the brand needs: content, campaigns, websites, apps, products, emails and
experiences that promote the brand, serve its audience and feel unmistakably part of the same world.
```

---

## Scope — three additions, all Python, all Builder

### A. second_brain/ archive + capture action
- Create `self/second_brain/` directory structure
- Extend the CAPTURE action from Phase 1: on capture intent, if a screenshot is available (`tools/vision_loop.py` already returns frames), save it alongside the text note to `self/second_brain/` with provenance (`ts`, `source`, `type: screenshot|text|draft`, `tagged: david_reference|elo_made`)
- L3: capture is safe (write-only, no send, no delete/sort without David)
- eLo-made assets land in the archive too, tagged `elo_made: true` so provenance stays honest

### B. Vision-indexing so eLo can recall by content
- On capture, extract a brief vision description of any screenshot (use existing `tools/vision_loop.py` — pass the saved image through, get a description string)
- Store description in a lightweight index (`self/second_brain/index.jsonl`: `{ts, path, type, description, tags}`)
- On "find that moody typography ref" or "what was that screenshot of" → search index by description keywords; return the match with path + description

### C. Recall integration (ties WO-067)
- `self/second_brain/` is a recall source alongside `self/ideas_log.jsonl` (Phase 1)
- "Where did we leave off on X" → check both logs
- Archive is never auto-sorted or deleted; eLo only says what it found, never invents

---

## Definition of Done
1. Say "capture this" or "write this down" (with screen active) → screenshot + note saved to `second_brain/`, confirmed with path
2. Say "find that typography reference" → eLo searches the index and returns the match (or "nothing found yet" if archive empty)
3. `second_brain/` archive structure exists, provenance fields correct, index readable
4. eLo-made output (if any) tagged `elo_made: true`; references tagged `david_reference: true`
5. Nothing deleted or sorted without David

## Tests (WITHOUT David)
- Capture intent + vision frame → assert `second_brain/` entry exists with correct provenance fields
- Recall query → assert index search returns matching entry or honest "not found"
- Empty archive → "nothing in archive yet", never fabricated
- eLo-made tag → assert `elo_made: true` on simulated generated output

## VERIFY FIRST
Run `~/miniconda3/bin/python3 -m pytest tests/test_wo068_capture_prepare_hold.py` — confirm Phase 1 still green before adding Phase 2. Do not touch Phase 1 behaviour.

*Board — 2026-08-30*
