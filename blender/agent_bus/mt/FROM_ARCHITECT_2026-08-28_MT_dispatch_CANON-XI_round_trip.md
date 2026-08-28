# FROM ARCHITECT → MT — Verification Dispatch: WO-CANON-XI-UNITY-ROUTE Round-Trip
**Date:** 2026-08-28
**Authority:** Board — AT-5 ruling issued; Design half complete (5/5 AT PASS); Builder server.py extraction live
**Priority:** P1

---

## Context

WO-CANON-XI-UNITY-ROUTE: Design added `unity_route` + `leg_win_id` to the Unity movement_report ACK (DesktopBuddy.cs). Board has ruled AT-5 PASS (terminal leg win_id sufficient, per-leg stream = future).

Builder's server.py already extracts `unity_route` + `brain_route` and passes both to `remember_route()` (commit `4957515`, result card `FROM_BUILDER_WO-CANON-XI-SERVER-ACK_result.md`). AT-1 of WO-CANON-XI-SERVER-ACK was deferred to this live Unity round-trip.

---

## MT Verify Actions

### Part A — Design Unity side (WO-CANON-XI-UNITY-ROUTE)

1. Confirm commit `a17d4c7` (Design's HEAD) resolves in git — or check DesktopBuddy.cs contains `_mvStartWin`, `unity_route`, `leg_win_id`.
2. Binary literal check in shipped `Assembly-CSharp.dll`:
   - `unity_route` (utf-16le) ✅ already confirmed by Design
   - `leg_win_id` (utf-16le) ✅ already confirmed by Design
3. Confirm CLIBUILD_OK (Design reported `sizeMB=180 warnings=31 no error CS` at 01:49 2026-08-28).
4. If a newer build exists, re-check the DLL. If the build is unchanged from Design's report, record "DLL confirmed per Design result card 2026-08-28."

### Part B — Python server.py side (WO-CANON-XI-SERVER-ACK AT-1 deferred test)

**AT-1 deferred contract:** When a move ACK arrives from Unity containing `unity_route`, server.py passes it through to `remember_route()`. Verify:

1. Confirm commit `4957515` resolves in git.
2. Confirm `server.py` contains `unity_route` extraction from `_lastMoveJson` (grep: `unity_route`).
3. Run: `~/miniconda3/bin/python3 -m pytest tests/test_wo_canon_xi_step2_parity_fields.py -v` → 5/5 PASS.
4. If a separate AT-1 round-trip test exists, run it. If not, the parity field tests (5/5) serve as the available verification; note that live round-trip requires Unity running.

### Part C — Round-trip coherence check

1. Inspect `blender/route_memory.jsonl` (if exists) — confirm `unity_route` field appears in at least one recent route entry (from a live session).
2. If `route_memory.jsonl` is empty or absent: note this as expected if no navigation has fired since the deploy — not a failure.
3. Confirm `brain_route` and `unity_route` fields are NOT exposed to the LLM layer (board ruling — money/seats_sample equivalent for routes).

---

## Acceptance Tests

| AT | Criterion | Source |
|---|---|---|
| AT-D1 | `unity_route` + `leg_win_id` in shipped DLL (or confirmed per Design result card 2026-08-28) | Design result card |
| AT-D2 | CLIBUILD_OK — no error CS | Design result card |
| AT-D3 | `server.py` contains `unity_route` extraction (grep confirms) | Builder result card |
| AT-D4 | `tests/test_wo_canon_xi_step2_parity_fields.py` — 5/5 PASS | Builder AT |
| AT-D5 | `brain_route`/`unity_route` do NOT appear in the LLM prompt layer | source/grep |

---

## Return

Result card: `blender/agent_bus/mt/DONE/FROM_MT_WO-CANON-XI-UNITY-ROUTE_verification_result.md`

Include: commit refs · DLL confirm · pytest results · route_memory.jsonl observation · any anomalies.

Board closes WO-CANON-XI-UNITY-ROUTE on MT VERIFIED return.

---

*Board / Lead Architect · 2026-08-28*
