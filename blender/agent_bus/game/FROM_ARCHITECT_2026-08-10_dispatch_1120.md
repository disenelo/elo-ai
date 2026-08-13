# FROM ARCHITECT — 2026-08-10 11:20 — DISPATCH (Game / Unity)

**Active WO:** GM-2b — Run-state stuck-in-Walk fix.
**Scope (one line):** Your fix landed (`IsSprinting = running && (moveX != 0f || moveY != 0f)` — sprint fires on any-direction movement incl. depth W/S). Gate to close = **David live A/D + W/S run test** in a fresh Unity Play session; movement-feel is the one thing not verifiable in an autonomous tick.
**If David's live test still fails on A/D:** next lever is the `IsSprinting` dual-write (`OnSprint:847` vs `:276`) — one line, as you flagged.
**Next in-lane after GM-2b closes:** GM-2 (parent). WAVE→GAME + INT-9 remain READY/DAVID-badged in your queue.
**Status:** non-gated, in-lane. Close gate is David's live feel-check, not a build blocker.

**DoD:** on David's confirm → mark GM-2b DONE + commit hash → **WRITE outbox** (done/next/blocker). If cron is alive and no outbox has been written recently, a state-write to outbox is the single next action.
