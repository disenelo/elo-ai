# Board Gate — Inner Thought: UI display restored
**Date:** 2026-10-11  
**Verdict:** SIGNED OFF — pending David live-turn confirmation

---

## David's complaint
"I don't see it on any turns anymore." (earlier: "I hear it but the -- thoughts don't show anymore")

## Root cause found (Board verified via code read)
Commit `dd3aecf` (WO-INNER-THOUGHT-ORDERING) moved speaking to Beat 2, pre-LLM. `collect()` is idempotent — marks `_collected = True` on first call. The post-response `_run_inner_thought` thread called `collect()` a second time → got `""` → the `_it_patch({"inner_thought_text": ...})` block was gated on the non-empty result → UI line never updated.

Inner thought was spoken (Beat 2 fires `_voice_speak_inner`). Never written to `blender_state.json`. Hence: heard, not displayed.

## Fix verified
Commit `ae71326` (2026-10-11 23:13) — `_publish_text()` added to `early_runner.py`. Called from inside `collect()` at the point of production — whichever call site consumes the thought, the UI sees it exactly once. If collect returns `""`, nothing overwrites the last displayed thought.

Builder 2's lane: `faculties/inner_thought/early_runner.py`. No `server.py` touch. Correct.

## Did the Board ask Builder 2 to remove inner thoughts?
**No.** Board searched all B2 filings for any instruction to remove/disable/suppress inner thoughts. Zero results. The disappearance was a side-effect of the ordering change (`dd3aecf`), not an intentional removal. David's question is answered here for the record.

## Live-turn gate
Next session: David should hear the inner thought before eLo's reply AND see the `-- [inner thought text]` line in the Unity chat log. Board signs this as DONE when David confirms both.

*Board / Lead Architect · 2026-10-11*
