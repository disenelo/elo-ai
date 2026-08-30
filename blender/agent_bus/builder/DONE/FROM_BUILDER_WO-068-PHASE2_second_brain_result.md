# FROM_BUILDER — WO-068-PHASE2 Result: Second Brain Visual Capture + Vision Recall

**WO:** WO-068-PHASE2  
**Commit:** 7b20381  
**Date:** 2026-08-30  
**Status:** DONE — All ATs PASS

---

## What was done

Extended `faculties/thread_keeper.py` with three Phase 2 additions per WO-068 §Phase 2.

### A. `second_brain/` archive + capture action
- `_SECOND_BRAIN_DIR` = `self/second_brain/`
- `_SECOND_BRAIN_INDEX` = `self/second_brain/index.jsonl`
- `capture_visual(text, image_bytes, elo_made)` — saves PNG to `second_brain/` with timestamp filename, appends provenance entry `{ts, saved, path, type, note, description, tags}` to index
- `_describe_screenshot(image_bytes)` — calls `tools/vision_loop._analyse()` to extract a description string (gracefully skips if vision not available)
- Provenance tagging: `david_reference: True` by default; `elo_made: True` when caller sets it

### B. Vision-indexed recall
- `search_second_brain(query)` — keyword scoring across `description + note` in `index.jsonl`; returns best match with path + description, or honest "nothing found yet" / "nothing in archive yet"

### C. `recall_thread()` integration
- `_archive_suffix(topic)` nested helper calls `search_second_brain` and returns `"\n\nAlso in archive — ..."` when a real match is found
- Added to both topic-match and topic-no-match branches of `recall_thread`
- No-topic branch: archive not checked (empty query would match nothing useful)

---

## AT results

### New tests: `tests/test_wo068_phase2_second_brain.py` (9/9 PASS)
- AT-P2-1 ✅ capture_visual with image → PNG saved in second_brain/
- AT-P2-2 ✅ index.jsonl entry has correct provenance fields (type, note, ts, saved, path, tags)
- AT-P2-3 ✅ capture_visual without image → text only, no second_brain index entry
- AT-P2-4 ✅ search_second_brain keyword match → returns path + description
- AT-P2-5 ✅ empty archive → honest "nothing yet" reply
- AT-P2-6 ✅ no keyword match → honest "nothing matching" reply
- AT-P2-7 ✅ elo_made=True → tags: {elo_made: true, david_reference: false}
- AT-P2-8 ✅ recall_thread with topic → includes archive suffix when match found
- AT-P2-9 ✅ py_compile clean on thread_keeper.py

### Phase 1 regression: `tests/test_wo068_capture_prepare_hold.py` (10/10 PASS — no regression)

---

## Notes

- `_describe_screenshot` calls vision_loop's private `_analyse()` — this is intentional; the vision loop already uses Gemini/OpenAI for structured description and this reuses that path without starting the background loop
- Archive is never auto-sorted or deleted; `search_second_brain` only reads; `capture_visual` only writes
- `self/second_brain/` directory is created on first capture
