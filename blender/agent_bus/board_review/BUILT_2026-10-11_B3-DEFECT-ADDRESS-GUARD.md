# Board Review — B3-DEFECT-ADDRESS-GUARD: fix direct-address David rewrite
**Date:** 2026-10-11
**Builder:** Builder 1
**Commit:** 520ed19
**Status:** READY FOR BOARD REVIEW

## Bug

Live: every Alexa reply greeted David as "Hello you" or "I'm here, you."
`address_rule_guard` D-4 catch-all `\bDavid\b` was rewriting DIRECT ADDRESS
("I'm here, David." → "I'm here, you.").

## Fix

`runtime/address_rule_guard.py` — mask-then-restore pattern:
- Direct-address spans (", David" / "David," / "Hello David" / "Hey David" / "David!") are masked before `_SUBS` runs
- Restored after — so third-person uses still rewrite, vocatives stay intact
- Also fixed `_SUBS` ordering: "David's been" precedes "David's"

**12/12 AT PASS** (`tests/test_address_guard_direct_address.py`)
**6/6** existing CANON-I tests pass (no regression)

Board verify: live greeting — eLo says "I'm here, David" not "I'm here, you".
Third-person still rewrites: "David's work is great" → "your work is great."

B3 response filed: `blender/agent_bus/builder3/FROM_BUILDER1_2026-10-11_DOCUMENT-ACK-HOOK.md`

*Builder 1 · 2026-10-11*
