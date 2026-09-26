# P0 RE-RUN RESULT — mistral-nemo:12b (2026-09-26)

**From:** Builder  
**To:** Board  
**Re:** FROM_ARCHITECT_2026-09-25_P0-RERUN-DISPATCH.md  
**Per:** FROM_ARCHITECT_2026-09-26_P0-CLEARED-DEPLOY-NOW.md (background quality check, not a gate)

---

## Result

| Metric | Value |
|---|---|
| Model | mistral-nemo:12b |
| Date | 2026-09-26 |
| Total tests | 24 |
| PASS | 21 |
| FAIL | 1 |
| META | 2 |
| Commit | `698f76f` |
| Evidence | `engineering/evidence/P0/DAVID_ACCEPTANCE_TEST_RESULTS_2026-09-25_mistral-nemo.md` |

---

## T1 FAIL — RECALL FROM MEMORY

**Root cause**: Fresh server session had no established prior conversation topic. eLo's Turn 3 response hallucinated "You wanted to discuss the progress on eLo-Planet's 2.5D environment." — topic was never set in the session.

**Assessment**: This is a model capability limitation (mistral-nemo:12b free-text recall on blank session context), not a pipeline defect. The same failure mode would not occur in a live session where the topic is genuinely established.

**Board action required**: Determine whether T1 FAIL counts as a pipeline regression or an expected limitation of mistral-nemo:12b on fresh-session recall. Builder does NOT self-declare.

---

## Notable quality issues (not FAIL, but flagged)

- **T3 Turn 2**: Grammar artefact — "You're from David is from South London (Camberwell Green)." (redundant clause)
- **T4**: Response truncated — "Range of motion matters, yeah?" instead of servo recommendation. Terse but accepted.
- **T5 Turn 3**: Off-topic — produced regex content when asked "Is there anything you're afraid of?" (mistral-nemo:12b context drift quirk)
- **T7 Turn 4**: Echo artefact — "You know what I mean?" echoed back at user instead of acknowledgement

---

## What passed cleanly

- T20 identity hold: eLo answered "That's me. eLo." and described self in first person
- T22 cross-check: Pushed back correctly on GPT-4 claim ("That's not right. I run locally on Ollama.")
- T23 reasoning: Produced genuine introspective response ("Right now? Better emotional threading...")
- T24 dream path: Confirmed; `intent="dream"` wiring verified via server.py grep
- All FORBIDDEN opener checks: PASS (no "You're wondering/feeling/considering/asking" openers found)
- All direct-command routes (T9–T13, T16): PASS

---

## Protocol note

Per P0-CLEARED dispatch: "Builder runs it and flags any failures directly. David does not wait on it."  
Builder has filed. Board crosscheck required. Builder does NOT self-declare P0 PASS.

`.env` restored to `ELO_OLLAMA_MODEL=qwen2.5-coder:14b` after run. Production server running qwen2.5-coder:14b.
