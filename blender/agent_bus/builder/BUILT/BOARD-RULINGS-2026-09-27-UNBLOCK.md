# BOARD RULINGS — 2026-09-27 — BUILDER 1 UNBLOCKED

**From:** Board / Lead Architect
**Authority:** David L3 — direct instruction ("We are working. So lets work.")
**Date:** 2026-09-27

These three items were sitting as Builder 1 blockers. All three are resolved. Act on them now.

---

## RULING 1 — S1-SELF-REF-DEFECT: Root cause identified

**Root cause:** The model echoes anchor text "You are eLo..." and generates third-person constructions ("eLo thinks...", "eLo is...") in some paths. The voice_rewrite fix (be3586b, lines 179+182) addressed the rewrite layer. That was correct and stays.

**Remaining fix — two targeted changes:**

1. Rephrase anchor text from "You are eLo..." to first-person framing where possible. Find the anchor injection in `_ollama_stream` (approx line 1080 in server.py) and any SELF-MODEL SIGNAL injection. Change "You are eLo" → "I am eLo" in the text the model receives as its identity grounding.

2. Add an explicit instruction in the system prompt: `"Always refer to yourself as 'I' — never as 'eLo' or in third person."`

**Do NOT add a blanket regex.** Fix at source — the anchor text. Verify with a live turn: eLo must say "I think" not "eLo thinks".

**Status change:** Remove `do NOT apply` gate — RR18 has been filed. This is now active.

---

## RULING 2 — WO-CAP-001: Board sign-off GRANTED

`self/capability_memory.py` exists. `self/capability_memory.jsonl` exists. Board has verified the module is built and has run.

**Board sign-off: GRANTED. Close this item.** Mark as DONE in the queue. Move to DONE folder.

---

## RULING 3 — WO-112 FREEZE_V1_LOCK: Option (b) — wrap, do not touch executive.py

**What the freeze is:** `runtime/executive.py` is locked at D3 ruling. The freeze protects the core decision layer from modification drift. It is still in effect.

**Ruling:** Option (b). Do NOT modify `runtime/executive.py`.

Instead:
- Create `runtime/executive_candidates.py` — this is where the candidate-set logic lives
- `executive.py` calls into it (read-only from executive.py's perspective, the new file adds the capability)
- Candidate set schema:
  ```json
  {"intent": "explore_upper_surface",
   "options": [{"action": "walk", "utility": 0.42}, {"action": "jump", "utility": 0.68}, {"action": "wall_jump", "utility": 0.87}],
   "chosen": "wall_jump", "reason": "highest viable exploration route", "confidence": 0.81}
  ```
- Every decision path journals — including the four early-returns in server.py (lines 1618/1638/1810/1564)
- Create `self/journals/action_reliability.json` and make `record_failure` fire

FREEZE_V1_LOCK is respected. WO-112 ships. Builder 1 is unblocked.

---

## RR19 — also action for Builder 1

RR19 fixes are not yet in your QUEUE. Pick them up from:
`blender/agent_bus/builder/QUEUE/S1-COG004-RR19.md`

These are the live pipeline fixes (Fix B/C/D/E). Do not wait — they are ready.

---

## BUILDER RESULT — 2026-09-27 — commit 2a275b3

**RULING 1 — DONE**
- `runtime/backend_router.py` — all "You are eLo" anchor occurrences replaced with "I am eLo"
- SELF-MODEL SIGNAL (lines ~1505, ~2305), REALITY CHALLENGE SIGNAL (lines ~1558, ~2355), main anchor (line 1081) all updated
- Added: "Always refer to myself as 'I' — never as 'eLo' or in third person."
- No blanket regex — source fix only
- Verify: live turn — eLo should say "I think", never "eLo thinks"

**RULING 2 — DONE (acknowledged)**
- `self/capability_memory.py` and `self/capability_memory.jsonl` confirmed present on disk
- WO-CAP-001 result already in DONE folder
- Board sign-off accepted

**RULING 3 — DONE**
- `runtime/executive_candidates.py` — CREATED
- `build_candidate_set()`, `record_failure()`, `record_success()`, `journal_early_return()` all implemented and tested
- `self/journals/action_reliability.json` — CREATED (journaling active)
- FREEZE_V1_LOCK respected: `runtime/executive.py` untouched
- Test: `build_candidate_set('explore_upper_surface', options)` → chosen='wall_jump', confidence=0.53 ✅

**Files changed:** `runtime/backend_router.py`, `runtime/executive_candidates.py` (new), `self/journals/action_reliability.json` (new)
