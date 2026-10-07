# PRIORITY PUSH — S3 Dream Engine: server.py wire
**From:** Board / Lead Architect
**To:** Builder 2
**Date:** 2026-10-04
**Authority:** David L3 directive — "Wire end to end"

## Why this is urgent

The full drain-to-sleep chain depends on S3. Builder 1 is building the trigger side (ambient tick → emit intent="dream" when battery low + calm). You own the execution side.

## The missing wire (server.py)

Detect `intent: "dream"` in blender_state.json → call `executive.run_dream_window()` → publish dream results back to blender_state.json.

The dream_faculty is built. The executive has run_dream_window(). The wire between server.py and those two is what's missing.

Per PROJECT_STATE.md: "Wire S3 dream publish() + intent='dream' into server.py."

## Chain for reference

```
[Builder 1 triggers] intent: "dream" appears in blender_state.json (when battery ≤ 0.25 + calm)
→ server.py detects intent == "dream"  ← YOUR WIRE
→ executive.run_dream_window()         ← YOUR WIRE
→ dream_faculty runs NREM/REM
→ wake_from_dream() mutates self-state (mood, curiosity, satisfaction, battery restored)
→ next turn reflects post-dream state  ← END STATE
```

## Acceptance

When blender_state.json shows `intent: "dream"`, server.py picks it up, runs the dream window, and the dream_journal.jsonl shows a new entry. Self-state reflects post-dream values on the next turn.

Evidence to: `engineering/evidence/DREAM/WO-DREAM-WIRE-S3_evidence.md`

Report back when wired. Don't wait for Builder 1's trigger to be confirmed live — wire your end, test with a manual `intent: "dream"` injection first.
