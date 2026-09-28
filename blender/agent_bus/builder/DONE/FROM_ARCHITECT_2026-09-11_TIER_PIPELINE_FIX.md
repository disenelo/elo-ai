# FROM BOARD → BUILDER — 2026-09-11 — TIER DATA PIPELINE: ALL CONTEXT UNKNOWN

**Priority:** P0 — nothing else works until this is fixed  
**Source:** `runtime/logs/expressed_elo_audit.jsonl` — live evidence  
**Date:** 2026-09-11

---

## What is broken

Every turn in `expressed_elo_audit.jsonl` shows all 8 context fields as tier_violations:

```
"tier_violations": ["active_window", "pose", "nearby", "mood", "wkg_context", "lessons", "vault_context", "capabilities"]
```

This means `the_moment.compile()` is setting every field to "unknown" or "absent" on every turn. `verify_response_tiers()` returns `hedge_required=True` and `violations=all_fields`. The SpeechLicence fires correctly — but eLo has no verified data about anything. The result: "I'm not certain, but —" prefix on every expressed turn, and eLo inventing context it doesn't have.

## What you diagnose

Read `runtime/the_moment.py`. The tiers depend on:

- `pose_acked`: True only if Unity sent a pose ACK this turn → if False, pose goes to "last-known", not "unknown". But the audit shows pose IS a violation = it is "unknown" or "absent". This means either `perch_state.json` is empty/missing entirely, or the compile path is not running.
- `capabilities_tier`: "live" only if `caps_live` is non-empty. In the audit it's a violation = capabilities registry returning nothing.
- `wkg_context`, `lessons`, `vault_context`: "unknown" if the underlying data is empty. These depend on WKG retrieval running and returning data.

**Diagnose each field:** start the real server, run one turn, then print:
1. What `perch_state.json` contains at the moment of that turn
2. What `pose_acked` and `perch_fresh` were set to when `compile()` was called
3. What `caps_live` contained
4. What the WKG query returned for `wkg_context`
5. What `lessons` and `vault_context` contained

## What you fix

For each field that is "unknown" because its data source is empty or disconnected: fix the data source or the connection, not the tier label. Do NOT change "unknown" to "last-known" to make the violation disappear — that is not a fix, it is a lie.

If Unity is not sending pose ACKs: that is a Design/MT dependency. Flag it. Do NOT paper over it.  
If WKG is not returning context: that is GAP-02 territory. Flag it with specifics.  
If capabilities registry is empty: fix the registry query.

## DoD

- Verbatim diagnosis: for each of the 8 fields, name the exact reason it was "unknown" in the audit
- At least 3 of the 8 fields moved to a real tier (observed/live/remembered) in a live server run
- `expressed_elo_audit.jsonl` after the fix: show the tier_violations list shrinking
- "I'm not certain, but —" must not appear on a turn where David states something clearly and eLo has relevant context

**File result with verbatim server output, not test fixtures.**

*Board / Lead Architect · 2026-09-11*
