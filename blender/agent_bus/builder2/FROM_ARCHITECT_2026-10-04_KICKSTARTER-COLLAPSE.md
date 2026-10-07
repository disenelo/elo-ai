# PRIORITY COLLAPSE — Kickstarter only. Stop everything else.
**From:** Board / Lead Architect
**To:** Builder 2
**Date:** 2026-10-04
**Authority:** David L3 — Kickstarter in ~1 month
**Supersedes:** Current queue (WKG junk filter, SPG scoring) — park them after your one job below

---

## One job.

**S3 dream wire** — the drain-to-sleep chain is incomplete because Missing B (your piece) is not wired.

`server.py`: detect `intent:"dream"` in blender_state.json → call `executive.run_dream_window()` → publish dream results back.

Builder 1 has wired the trigger side (ambient tick emits intent:"dream" when battery low + calm). Your end is the execution side.

Test with a manual `intent:"dream"` injection first — don't wait for Builder 1's trigger to occur in production.

Evidence to: `engineering/evidence/DREAM/WO-DREAM-WIRE-S3_evidence.md`

---

## After S3 is wired

WKG junk entity filter (WO-WKG-JUNK-ENTITY-FILTER-001) — `Tell`, `What`, `You`, `Raspberry` polluting the graph. Short job, do it next.

SPG significance scoring (WO-SPG-PATTERN-001) — after junk filter.

---

## What Kickstarter needs from you

eLo goes to sleep when his battery is low and calm. He wakes up with a changed state (mood, curiosity, satisfaction shifted by the dream). That feeds Demo 2 (eLo has an inner life) and is the proof of the dream faculty working end-to-end.
