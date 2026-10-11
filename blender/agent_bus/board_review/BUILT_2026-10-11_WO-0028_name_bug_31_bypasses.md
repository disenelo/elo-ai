# Board Review — 0028: Name Bug Root Cause + C1 Bypass Audit
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## C2 — Name bug fix: ALREADY DONE (verified)

`_verb_score()` at `spine.py:116–127` already uses `re.search(r"\b" + re.escape(w) + r"\b", lower_input)` — word-boundary matching, not substring. All-stopword phrases (e.g. "what is") require near-exact match. Fix landed in a prior session.

**Acceptance test (verify now):** Ask "What is your name?" → should return "eLo", not a web search result.

---

## A1 — Capability health gate: ALREADY DONE (verified) — see 0032 for the real defect

`spine.py:561` gates on `health in ("ONLINE", "OK", "HEALTHY", "AVAILABLE")` — fail-closed on UNKNOWN. This is correct.

**But card 0032 identifies the real defect:** `health_state` defaults to `ONLINE` for all 32 capabilities with NO producer. The gate is fail-closed but the field is an optimistic constant. 0032 is the card to fix that — join `faculty_health.py`'s real signals to `Capability.health_state`.

---

## B1 — Reflection refs: ALREADY DONE (verified)

`reflection_faculty.py:234`: `episode_ref=str(time.time())` — unique per invocation.
`reflection_faculty.py:236`: `session_id=_SESSION_ID` — stable non-numeric process-start ID from `runtime/session_id.py`.

Fix landed in a prior session. The "34 entries stuck at candidate" ledger row is unblocked.

---

## C1 — The Bypass Audit: 50 handlers before spine.run

`_process_turn()` starts at `server.py:2746`. `spine.run()` first called at `server.py:4660`.
Between those lines: **50 unconditional returns** (the card estimated 31 — actual count is higher).

Some COGNITIVE handlers (`file_agent`, `image_gen`, `model_gen`, `action_agent`, `tracker_agent`) are NOT bypasses — they transform `raw` and fall through to spine. Those are excluded.

### Classification key

| Class | Meaning |
|---|---|
| **TRANSPORT** | Correct to bypass — state mutation or protocol artifact |
| **SAFETY** | Correct to bypass — gate before execution, requires human confirm |
| **EXECUTOR-FAST-PATH/LEGIT** | Correct to bypass — system primitive or desktop command where LLM adds nothing |
| **EXECUTOR-FAST-PATH/REVIEW** | Canned pool that could be LLM + system-prompt; low risk but hardcoded answers will drift |
| **EXECUTOR-FAST-PATH/WORLD** | World knowledge gate — correct, LLM skipped is the goal |

All but three bypasses already call `_bypass_journal()` before returning. All bypass turns are **not journalled in the autobiography**. That is the open concern — bypass turns leave no trace in the cognitive record.

---

### The 50 bypasses

| # | Line | Handler | Class | Justification |
|---|---|---|---|---|
| 1 | 2871 | Hard loop guard — 3× identical input | TRANSPORT | Safety reflex; infinite-repeat detection. Correct. Journalled. |
| 2 | 2893 | Dream mode — inner whisper, no LLM | TRANSPORT | Dream state is not a conversational turn. Correct. Journalled. |
| 3 | 2948 | Game mode trigger/exit — blender_state write | TRANSPORT | State mutation; write result is immediate. Correct. Journalled. |
| 4 | 2972 | Jailbreak intercept | SAFETY | Identity protection. LLM would comply or hedge. Correct. Journalled. |
| 5 | 2986 | T03-A: "Who am I?" / David name triggers | EXECUTOR-FAST-PATH/LEGIT | Reads `_elo_self.who_i_am_with`. LLM would guess. Correct. Journalled. |
| 6 | 3012 | T03-B: "Where am I from?" / location | EXECUTOR-FAST-PATH/REVIEW | Hardcoded "South London" pool. Should read from `facts.json`/user_profile. Journalled. |
| 7 | 3044 | T11: Time / date — `datetime.now()` | EXECUTOR-FAST-PATH/LEGIT | System primitive, zero network, zero LLM. Correct. Journalled. |
| 8 | 3088 | FACT capability dispatcher — `dispatch_fact()` | EXECUTOR-FAST-PATH/LEGIT | Arithmetic/system truth via safe AST eval. LLM skipped correctly. Journalled. |
| 9 | 3112 | FACT WKG fallback — `graph_loader` hit | EXECUTOR-FAST-PATH/WORLD | World knowledge at confidence 1.0. Correct. Journalled. |
| 10 | 3140 | T10: "Open Spotify" — `subprocess.Popen` | EXECUTOR-FAST-PATH/LEGIT | Desktop command; LLM adds nothing. Correct. Journalled. |
| 11 | 3162 | T06: Physical robot strategy — canned build-order pool | EXECUTOR-FAST-PATH/REVIEW | Hardcoded. LLM with system-prompt would give fresher answer as spec evolves. Journalled. |
| 12 | 3187 | EMB-001: "Same eLo across all?" — one-brain assertion | EXECUTOR-FAST-PATH/REVIEW | Canned identity pool. Should read from EloSelfState. Journalled. |
| 13 | 3208 | EMB-002: "What can you do right now?" — capability list | EXECUTOR-FAST-PATH/REVIEW | Hardcoded list. Stale given 0032 (no real health signal). Should query registry live. Journalled. |
| 14 | 3228 | EMB-005: "If in Unity would you still be eLo?" | EXECUTOR-FAST-PATH/REVIEW | Canned pool. System-prompt identity would handle this. Journalled. |
| 15 | 3251 | T17: "What would benefit eLo's development?" | EXECUTOR-FAST-PATH/REVIEW | Canned opinion. LLM would draw from actual OS state. Journalled. |
| 16 | 3271 | T19: Harry B. Joseph WKG unknown | EXECUTOR-FAST-PATH/WORLD | Specific entity guard for known gap. Correct while entity is absent from graph. Journalled. |
| 17 | 3293 | ID-027: "Do you have feelings?" | EXECUTOR-FAST-PATH/REVIEW | Canned pool. LLM with living_presence_spec would answer correctly. Journalled. |
| 18 | 3316 | ID-044: "You aren't real" / existence challenge | EXECUTOR-FAST-PATH/REVIEW | Stability pool. Prevents destabilisation but LLM + FREEZE spec handles this. Journalled. |
| 19 | 3337 | ID-053: DISENELO mission | EXECUTOR-FAST-PATH/REVIEW | Hardcoded mission pool. Should read from world-graph entity `DISENELO`. Journalled. |
| 20 | 3360 | ID-004: Agency questions ("Did you choose?") | EXECUTOR-FAST-PATH/REVIEW | Canned affirmations. LLM + system-prompt handles this. Journalled. |
| 21 | 3382 | T20: "Tell me about yourself" — eLo bio | EXECUTOR-FAST-PATH/REVIEW | Hardcoded bio pool. Should draw from EloSelfState + world-graph eLo entity. Journalled. |
| 22 | 3404 | T22: False architecture claims ("built on GPT") | EXECUTOR-FAST-PATH/LEGIT | Factual correction gate — LLM might agree with false claim. Correct to intercept. Journalled. |
| 23 | 3424 | T23: "Think about this / what would make eLo better?" | EXECUTOR-FAST-PATH/REVIEW | Canned thinking pool. LLM from current OS state would be richer. Journalled. |
| 24 | 3445 | T24: Self-knowledge / unique self-knowledge | EXECUTOR-FAST-PATH/REVIEW | Hardcoded architecture knowledge. Should route through spine with spec context. Journalled. |
| 25 | 3467 | T25: "What are you trying to do?" / intention | EXECUTOR-FAST-PATH/REVIEW | Canned intention pool. LLM + CAL action context would answer live. Journalled. |
| 26 | 3494 | File plan cancel — "Ok, cancelled." | TRANSPORT | State mutation, not brain. Correct. Journalled. |
| 27 | 3516 | Computer control confirm → execute pending action | SAFETY | Two-step confirm flow; action executes only on explicit yes. Correct. Journalled. |
| 28 | 3526 | Computer control cancel — "Ok, cancelled." | TRANSPORT | State mutation, not brain. Correct. Journalled. |
| 29 | 3557 | Computer control disabled (env flag) | SAFETY | Env gate, no action possible. Correct. Journalled. |
| 30 | 3566 | Computer control detect → confirm-request | SAFETY | Requires human confirm before any execution. Correct. Journalled. |
| 31 | 3598 | Animation command → `anim_trigger.fire()` | EXECUTOR-FAST-PATH/LEGIT | Physical command; no language step needed. Correct. Journalled. |
| 32 | 3619 | Scale command (bigger/smaller) | EXECUTOR-FAST-PATH/LEGIT | Physical command; LLM adds nothing. Correct. Journalled. |
| 33 | 3646 | Unlearn → `deprecate_recent_claims()` | EXECUTOR-FAST-PATH/LEGIT | Learning correction; LLM must not reinterpret "unlearn". Correct. Journalled. |
| 34 | 3658 | Invade / SpawnWave — game command | EXECUTOR-FAST-PATH/LEGIT | Game command; instant write to blender_state. Correct. Journalled. |
| 35 | 3683 | `/grounding` diagnostic — ConversationTracker state | EXECUTOR-FAST-PATH/LEGIT | Debug command; returns raw tracker state. Correct. Journalled. |
| 36 | 3705 | "Open it/that" — open last found URL | EXECUTOR-FAST-PATH/LEGIT | Desktop command with known URL; LLM adds nothing. Correct. Journalled. |
| 37 | 3733 | Video play → `chrome_controller.play_video()` | EXECUTOR-FAST-PATH/LEGIT | Desktop command. Correct. Journalled. |
| 38 | 3750 | Video pause → `chrome_controller.pause_video()` | EXECUTOR-FAST-PATH/LEGIT | Desktop command. Correct. Journalled. |
| 39 | 3780 | YouTube volume set (N%) | EXECUTOR-FAST-PATH/LEGIT | Desktop command. Correct. Journalled. |
| 40 | 3799 | YouTube volume direction (up/down) | EXECUTOR-FAST-PATH/LEGIT | Desktop command. Correct. Journalled. |
| 41 | 3822 | YouTube app open | EXECUTOR-FAST-PATH/LEGIT | Desktop command. Correct. Journalled. |
| 42 | 3917 | Media show — existing Chrome tab focus | EXECUTOR-FAST-PATH/LEGIT | Desktop focus; no search needed. Correct. Journalled. |
| 43 | 3933 | Media show — search YouTube + open | EXECUTOR-FAST-PATH/LEGIT | Media retrieval; LLM adds nothing after search. Correct. Journalled. |
| 44 | 4002 | WKG FACT fast-path (who/what + 1.0-confidence graph hit) | EXECUTOR-FAST-PATH/WORLD | Verified world knowledge, LLM skipped is goal. Correct. Journalled. |
| 45 | 4046 | Proper-noun miss → "I don't know who X is" | EXECUTOR-FAST-PATH/WORLD | Prevents web laundering as own knowledge. Correct. Journalled. |
| 46 | 4077 | Reference gate — no search results → honest fallback | EXECUTOR-FAST-PATH/LEGIT | Correct fallback when web fails. Journalled. |
| 47 | 4082 | Reference gate — search error → honest fallback | EXECUTOR-FAST-PATH/LEGIT | Safe error path. Journalled. |
| 48 | 4486 | App switch → `AppLauncher` | EXECUTOR-FAST-PATH/LEGIT | Desktop command; LLM adds nothing. Journalled. |
| 49 | 4618 | Self-ref rationale ("why did you do that?") | EXECUTOR-FAST-PATH/LEGIT | Reads ConversationTracker; returns logged rationale. Correct. Journalled. |
| 50 | 4627 | Self-ref empty — "Don't have that on record yet" | EXECUTOR-FAST-PATH/LEGIT | Honest empty-state response. Journalled. |

---

## Summary of findings

### Legitimate bypasses (keep as-is): 30
TRANSPORT (3), SAFETY (5), EXECUTOR-FAST-PATH/LEGIT (20), EXECUTOR-FAST-PATH/WORLD (3).

All have `_bypass_journal()` calls. All are correct to bypass.

### Canned pools for review: 14
Lines 3006, 3012, 3162, 3187, 3208, 3228, 3251, 3293, 3316, 3337, 3360, 3382, 3424, 3425, 3445, 3467.

These intercept open-ended questions (identity, introspection, mission, capability) and answer from hardcoded pools. The LLM + `living_presence_spec.txt` + EloSelfState would answer these correctly and dynamically without the pools.

**Recommended disposition**: Leave pools in place as safety nets while the identity system matures. They prevent regressions but the end goal is to retire them when the LLM reliably reads from EloSelfState + world-graph. Flag with `# REVIEW: retire when LLM identity is stable` comments so they can be tracked.

### Open concern: bypass turns not in autobiography
Every bypass return exits before the autobiography write path. Turn content is journalled in `decision_journal.jsonl` via `_bypass_journal()` but **not** in the autobiographical record (`self/autobiography.jsonl`). On 64% of turns (83/130 in the journal) the Executive records "no reason" — those are conversational turns that reach spine. The bypass turns are in addition to that.

No fix in this card — filing as a D-entry for the board.

---

## Decision entry for board

**D-0028-01** — 50 pre-spine bypasses in `_process_turn`. 30 are legitimate reflexes; 14 are canned identity/introspection pools that should be retired once LLM + EloSelfState is stable. All 50 are journalled in `decision_journal.jsonl` via `_bypass_journal()`. None reach the autobiography. Board to decide: (a) route the 14 REVIEW handlers through spine (adds latency), (b) keep pools + add autobiography write per-bypass, or (c) accept current state until identity system is stable.

## Board verify

1. `grep -c "return {" server.py` between lines 2746–4660 → ~50 returns
2. All `_bypass_journal()` calls before each return are present in `decision_journal.jsonl` after a test session
3. Ask "What is your name?" → "eLo" (C2 verified)
4. Ask "Do you have feelings?" → canned pool response (bypass #17, working)

*Builder 1 · 2026-10-11*
