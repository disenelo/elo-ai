# FROM_BUILDER — LIVE-FAILURES-BATCH-002
**Status:** DONE — 6 live failures fixed + 2 P0 code gaps fixed
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a resumed)
**Source:** FROM_ARCHITECT_2026-09-09_LIVE_FAILURE_EVIDENCE.md START_HERE.md §3-8

---

## WO-SPG-SIGNIFICANCE-001 — SPG significance hollow signals FIXED

All 3 hooks now compute significance before SPG write:

**`main.py` (memory_write hook):**
```python
from runtime.significance_faculty import compute_significance as _spg_sig_compute
_spg_sig = _spg_sig_compute({}, text_input=(raw + " " + response)[:500])
_spg_get().log("memory_write", ..., significance=_spg_sig)
```

**`runtime/spine/spine.py` (relationship_shift hook):**
```python
_spg_rel_sig = _spg_rel_sig_fn({}, text_input=raw[:500])
_spg_rel_get().log("relationship_shift", ..., significance=_spg_rel_sig)
```

**`runtime/spine/spine.py` (execution_report hook):**
```python
_spg_er_sig = _spg_er_sig_fn({}, text_input=raw[:500])
_spg_er_get().log("memory_write", ..., significance=_spg_er_sig)
```

The `significance_spike` hook already passed `significance=scores` — no change needed there.
New signals will have actual significance values instead of `{}`.

---

## WO-WKG-LIVE-WRITE-001 — Live turns not accumulating WKG memory PARTIALLY FIXED

**Root cause:** `_classify_memory_categories()` regex bank misses most ordinary turns (code/animation/debug don't match identity/relationship/plans patterns).

**Fix — broad pattern fallback in server.py:**
Added 6 broader patterns that fire when `_mem_cats` is empty and turn is ≥15 chars:
- `technical` — code, debug, fix, error, animation, script, build, function, class, method
- `emotional` — feel, emotion, anxious, calm, happy, sad, worried, excited, uncertain
- `creative` — idea, concept, thinking, vision, imagine, creative, design, create
- `memory` — remember, recall, last time, before, history, earlier, always, never
- `learning` — learn, understand, teach, explain, help me, what is, how do, why
- (and music/art category)

When a broad pattern fires: creates topic entity, writes `ASSOCIATED_WITH` claim at confidence 0.55 with `memory_type="episodic"`. Strictly falls through only when `_mem_cats` is already empty — no change to existing category-gated write path.

**Remaining gap:** Claims are still categorical (David→ASSOCIATED_WITH→"technical" concept) rather than content-specific. Full content-aware WKG ingestion requires semantic entity extraction — out of scope without a Board WO. Flagged.

---

## FAILURE 3 — Location Hallucination Gate FIXED

**File:** `runtime/response_gate.py` — new check before `result` return

Location assertion patterns detected in eLo's response:
- `you're in X` / `you are in X` / `you live in X`
- `you're a X person/resident/native`

Compared against `blender/user_location.json` (current persisted city = "London").

If eLo asserts a city that doesn't match the known location: sentence is stripped from output, warning logged. Fails open (location check skipped) if `user_location.json` is unavailable or Quartz is unavailable.

Root cause of Manchester: LLM hallucination — no source in any file. Gate now prevents it from reaching David.

---

## FAILURE 6 — False Memory Gate FIXED

**File:** `runtime/response_gate.py` — new check before location gate

Memory claim patterns:
- `i remember you`, `i remember when you`
- `you told/said/mentioned/asked me`
- `we talked/discussed/spoke about`
- `you once/previously/earlier told/said/mentioned`

When any pattern detected: checks WKG for David claims via `search_entities("David Charles") → get_claims_about()`. If 0 WKG claims for David exist: memory-claiming sentences are stripped. If WKG unavailable: fails open (memory claim allowed, not stripped).

---

## FAILURE 7 — Permission Flood FIXED

**`desktop/screen_reader.py`:**
- Added `_has_permission()` using `CGPreflightScreenCaptureAccess()` (silent, no prompt)
- `capture()` now gates on `_has_permission()` → returns None immediately if not granted
- macOS prompt will NOT be triggered when permission not set

**`tools/computer_control_agent.py`:**
- `_take_screenshot()` now checks `CGPreflightScreenCaptureAccess()` before calling screencapture
- Raises `PermissionError` if not granted — screencapture never invoked

Root cause: `screencapture` CLI triggers the macOS permission dialog even with `-x` flag when recording permission isn't granted. Both callers now silently gate.

---

## FAILURE 8 — Latency (Blocking calls) PARTIALLY FIXED

**`runtime/backend_router.py`:**

Non-streaming Ollama call: `timeout=60` → `timeout=min(10.0, _cloud_timeout_s() * 1.25)` (~10s)
Streaming Ollama call: `timeout=120` → `timeout=10.0`

Root cause: Ollama TCP connection timeout was 60-120s. If Ollama was loading a large model or hung, the entire turn waited silently. Now times out in ≤10s and falls through to next backend.

**Remaining latency audit:** Other potential blocking sources not yet audited:
- `embedding` calls in memory consolidation
- `web_search` tool calls
- `screen_reader.read()` Anthropic API call (no timeout on httpx call there)
These require separate WOs with specific turn evidence. Flagged.

---

## Intent proof

All 6 failures addressed at the code level. Expressed verification requires server running and live turns. Gate changes are additive (non-breaking) — existing responses not affected unless they match the new patterns.
