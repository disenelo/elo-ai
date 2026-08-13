# → DESIGN (UI/Avatar) — REBUILD the desktop app from the current commit (David 2026-08-06)
Your sit chain is correct and committed — but David's LIVE session still narrates instead of sitting.
Diagnosis: **committed ≠ running.** The Python backend was reloaded (picks up `server.py`), but your sit
work is Unity C# (`EloOSAvatarReceiver.ApplySitCommand` · `EnterSit` · `SitInPlace` · `SitAckCo` ·
`ExitSit`/`StandFromSit`) — those only exist in the app David runs if it's been REBUILT/replayed since
your commit. He's very likely on a stale build, so `sit_command` lands and nothing consumes it.

**Do this:**
1. **Rebuild the desktop app from the current commit** (the one containing ApplySitCommand/EnterSit/
   SitInPlace/SitAckCo). Confirm those symbols are actually in the build (not just in the repo).
2. Hand David the fresh build (or confirm the exact way he should run it — standalone build vs Editor
   Play mode) so what he launches = your committed code.
3. **Then run the end-to-end arbiter and report the result:** say "come sit" →
   - `blender/blender_state.json` gets a fresh `sit_command._ts` (eLo-OS emitted), →
   - `ApplySitCommand`→`EnterSit`→`SitInPlace` plays (eLo visibly sits, held), →
   - `unity_events.json` gets `sit_complete` (your ACK), →
   - eLo says it's sitting truthfully.
   Report each link that fired. If `sit_command` is NOT written even on the fresh build → it's the
   Builder's emit (intent match on "come sit" variants), not you — relay back and we route to Builder.

**Not yours this round:** the "perched while standing" line = `[BODY POSITION]` hardcode at
server.py:2627 → Builder/WO-052A (reads the self-model pose). You own the build + the visible sit.
Do not rebuild a parallel sit path — this is confirming the EXISTING committed chain runs in David's app.
Ref: `../DIAGNOSIS_movement_mirror_2026-08-06.md` · `../../docs/architecture/UNITY_ELOOS_IO_CONTRACT.md`.
