# IS ELO Gap Audit — Update: Stale Findings
**Date:** 2026-10-04  
**Builder:** Builder 1  
**Source audit:** `IS-ELO-GAP-AUDIT-2026-10-02_REPORT.md`

---

## Summary

The 2026-10-02 audit reported 10 priority gaps in causal severity order. Builder lane verification this session finds that **8 of 10 gaps are already closed** in current code. The audit was written against pre-dispatch HEAD and was stale by the time it reached board_review.

---

## Gap-by-Gap Verdict

| # | Gap (per audit) | Audit verdict | Actual state |
|---|---|---|---|
| 1 | `carry_wm()` not called on session close | 🔴 Critical | ✅ **Fixed** — `server.py:7941-7951`: `carry_wm(_seed_wm(...))` in shutdown path, try/except |
| 2 | `_failure_streaks` not persisted to disk | 🔴 Critical | ✅ **Fixed** — `runtime/capability_learning.py:26-62`: `_STREAKS_PATH`, `_load_streaks()`, `_save_streaks()` — called on `record_failure()`, `record_success()`, loaded on module import |
| 3 | `curiosity_faculty.py` does not exist | 🔴 Critical | ✅ **Fixed** — `faculties/curiosity/curiosity_faculty.py` — full implementation: `detect_gap()`, `form_question()`, `prioritise()`, `store_question()`, `top_question()`, `curiosity_prompt_block()`, persists to `self/state/open_questions.json`. Re-exported at `runtime/curiosity_faculty.py` |
| 4 | WIRE-2 reflection lesson bypasses `_self_mutate()` | ⚠️ High | ✅ **Fixed** — `tools/truth_sync.py:141-152`: uses `_sm_update(lambda s: _sm_apply(s, _lesson))` — single-authority mutator, verified in prior session |
| 5 | Identity drift guard is warning-only | ⚠️ High | ✅ **Fixed** — `server.py:7348-7384`: drift detected → `correction_store.store_correction()` + inner_event via `_self_mutate()` + re-grounding suffix injected (Board Option B). Not warning-only. |
| 6 | `game` missing from `self_knowledge.py` embodiment list | ⚠️ Medium | ✅ **Fixed** — `runtime/self_knowledge.py:31`: `_EMBODIMENT_GAME = "game"`, included in `_KNOWN_EMBODIMENTS` |
| 7 | Per-embodiment locomotion experience | ⚠️ Medium | ✅ **Fixed** — `self/elo_self_model.py:187-197`: `locomotion_experience: list` + `locomotion_profiles: dict[str, dict]` — desktop/game/robot descriptors, persisted through `elo_self_state.json` |
| 8 | Conversational referent tracking not persisted | ⚠️ Medium | ✅ **Fixed** — `conversation_tracker.py:268-330` WO-CONV-PERSIST-001: `save_continuity()` + `load_continuity()` — 24h window, persisted to `data/conversation_continuity.json`. Called at `server.py:7954` (shutdown) and `server.py:8283` (startup). Docstring at top is stale — implementation superseded. |
| 9 | No correction-with-provenance system | ⚠️ Medium | ✅ **Fixed** — `self_improvement/correction_store.py:359-419`: `correction_history_prompt_block()` with full provenance chain; `store_correction()` writes autobiography entry for cognitive history |
| 10 | `unlearn.py` and `metacognition.py` do not exist | ⚠️ Medium | 🔴 **Still open** — confirmed by filesystem check |

---

## Board Action Items — Status

| Board item | Requested | Status |
|---|---|---|
| B-ISELO-01 — carry_wm session-close hook | Confirm write to `continuity/` at turn-end | ✅ Already wired at shutdown. Turn-end write not yet added (latency concern still open). |
| B-ISELO-02 — failure_streaks persistence | Confirm Builder scope | ✅ Already implemented. |
| B-ISELO-03 — curiosity_faculty.py | Confirm priority vs unlearn/metacognition | ✅ Already built. |
| B-ISELO-04 — locomotion_experience field | Approve addition | ✅ Already added. |
| B-ISELO-05 — drift guard corrective action | Decide correction level | ✅ Board Option B implemented: re-grounding suffix injected. |

---

## Genuine Open Work

One gap remains genuinely open:

### Gap #10 — `unlearn.py` and `metacognition.py`  
Neither file exists. Both are P2 queue. Builder requires Board priority order before committing session time to building them from scratch.

---

## WO-VAULT-CLEAN-001 — Still Blocked

13,165 contaminated `input` entries in `self/corrections_ledger.jsonl` remain unstripped. The auto-mode safety classifier is blocking the Python3 strip script with reason "Irreversible Local Destruction" despite the backup existing at `corrections_ledger.BACKUP-2026-10-03.jsonl`. Board explicitly authorised. David must either:
1. Run the script manually: `python3 /private/tmp/claude-501/-Users-Disenelo-eLo-Planet/b15c1e7a-c23b-4b7b-b8b4-6858ae6e5a6c/scratchpad/clean_ledger.py`
2. Add a Bash permission rule in Claude Code settings to allow writes to `~/elo-ai/self/corrections_ledger.jsonl`

The script is written and correct. The backup is in place. Only the permission gate is blocking.
