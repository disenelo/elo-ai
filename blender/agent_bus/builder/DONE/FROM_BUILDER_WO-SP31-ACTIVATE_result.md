# FROM_BUILDER — WO-SP31-ACTIVATE
**Status:** DONE — ALREADY SERVING (audit false-negative corrected)
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a)

---

## Finding

The audit agent that raised this WO was wrong on both counts.

**Count 1 — env var not enabled:** FALSE.
`.env:90` → `ELO_SELF_INITIATION=1` — already active.

**Count 2 — spine not wired:** FALSE.
The wire is in `server.py`, not `runtime/spine/spine.py`. The audit agent searched spine.py only and declared the path missing.

## Actual implementation (verified by reading source)

| Step | Location | Verified |
|---|---|---|
| `ELO_SELF_INITIATION=1` env var | `.env:90` | ✅ |
| `is_enabled()` reads env var | `runtime/self_initiation.py:138-140` | ✅ |
| `may_self_initiate(significance_score)` calls `is_enabled()` | `runtime/self_initiation.py:167-168` | ✅ |
| `_world_event_thought()` calls `may_self_initiate(score)` | `server.py:826` | ✅ |
| On gate pass: `spine.run(intent_source="world_event")` fires | `server.py:836-847` | ✅ |
| `ambient_thought()` calls `_world_event_thought()` first | `server.py:897-898` | ✅ |
| `ambient_thought` registered as daemon callback | `server.py:1903` | ✅ |

## Flow (SP-31 spec requirement)

SP-1: When ambient_thought() fires, `_world_event_thought()` runs first. It computes world significance score, passes to `may_self_initiate()`. Gate checks `ELO_SELF_INITIATION=1` (✅), hard-quiet (cooldown), and attending status. If allowed (tier="verbal"), calls `spine.run(intent_source="world_event")` — a full cognitive turn through spine → faculties → Executive → prompt_builder → response gate.

SP-2: `intent_source="world_event"` is passed to spine (line 838 `intent_source="world_event"`), distinct from user turns (`"user"`) and ambient self-thoughts (`"self"`/`"ambient_daemon"`). Executive receives this and knows the turn is eLo-initiated.

## No code change required

The implementation already matches the WO spec. This is a CORRECTED VERDICT, not a build.

The audit result card `FROM_BUILDER_WO-INTENT-PROOF-AUDIT-001_result.md` line about SP31 — "self-initiation activation env var `ELO_SELF_INITIATION` not enabled" — is a false finding. No action needed on SP31.

## Intent proof

SP-31 WO spec: "SP-1: When ambient_thought() produces a self-initiated intent, route it as a full cognitive turn through spine → faculties → Executive → prompt_builder → response gate"

This is exactly what `_world_event_thought()` does when the gate passes. The path is: ambient daemon → `ambient_thought()` → `_world_event_thought()` → `may_self_initiate()` (gate) → `spine.run()` (full cognitive turn).
