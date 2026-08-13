# FROM ARCHITECT — dispatch 2026-08-10 12:15

**GM-2b — Run→gun-fire blend.** Your root-cause fix landed (IsSprinting now fires on any-direction movement, incl. W/S depth). This now needs **David's Unity feel-verify** (focus Unity to recompile → Play → run, esp. W/S → Run state should fire). That verify is a David L3 (animation feel) — surfaced to him. Until it clears, GM-2c (arm+gun positioning) stays QUEUED on GM-2b; do not start it.

**While waiting:** keep self-testing GM-2b via inject/log and capture any residual A/D edge case (the IsSprinting dual-write OnSprint:847 vs :276 is the next lever if A/D still fails). Append findings to `outbox.json` (never overwrite). Outbox `ts` read stale this run — please refresh so the poll sees you 🟢.
