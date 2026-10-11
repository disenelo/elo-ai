# Board Review — B3-DEFECT-ADDRESS-GUARD: fix direct-address David rewrite
**Date:** 2026-10-11
**Builder:** Builder 1
**Commit:** 520ed19
**Source:** `blender/agent_bus/builder/FROM_BUILDER3_2026-10-11_HELLO-YOU-ADDRESS-GUARD.md`
**Status:** READY FOR BOARD REVIEW

## The Bug

`address_rule_guard` D-4 catch-all `\bDavid\b(?! Charles)` was rewriting
direct-address vocatives:
- "I'm here, David." → "I'm here, you."
- "Hello David, how are you?" → "Hello you, how are you?"
- All greeting + name forms broken on every Alexa reply 2026-10-10

## The Fix

`runtime/address_rule_guard.py`:

Added `_mask_direct_address()` / `_restore_direct_address()` step before and
after `_SUBS`. Direct-address patterns protected:
1. `, David` (end-of-clause vocative) — "I'm here, David." / "Great, David."
2. `David,` (start-of-clause) — "David, I think…"
3. Greeting + David — "Hello David" / "Hey David" / "Hi David" / "wagwan David"
4. `David!` / `David?` (solo exclamation/question)

Third-person uses still rewrite correctly:
- "David's work is impressive." → "your work is impressive."
- "David said he would come." → "you said he would come."
- Mixed sentence: both third-person rewrite AND vocative preserved.

Also fixed _SUBS ordering: "David's been" precedes "David's" to prevent
partial-match truncation.

## AT Results

| AT | Description | Result |
|---|---|---|
| AT-1 | End-of-clause vocative preserved: "I am here, David." | ✅ PASS |
| AT-2 | Greeting+comma preserved: "Hello David, how are you?" | ✅ PASS |
| AT-3 | Hey-form preserved: "Hey David what you saying?" | ✅ PASS |
| AT-4 | Start-of-clause vocative preserved: "David, I think we should go." | ✅ PASS |
| AT-5 | Exclamation vocative preserved: "I am right here, David!" | ✅ PASS |
| AT-6 | Period-ended vocative preserved: "Great to see you, David." | ✅ PASS |
| AT-7 | Third-person subject rewritten | ✅ PASS |
| AT-8 | Possessive rewritten | ✅ PASS |
| AT-9 | Mixed: third-person rewritten, vocative preserved in same sentence | ✅ PASS |
| AT-10 | No David — no-op | ✅ PASS |
| AT-11 | Live bug case: "I'm here, David." | ✅ PASS |
| AT-12 | Greeting hi form: "Hi David how's it going?" | ✅ PASS |

`tests/test_address_guard_direct_address.py` → **12/12 PASS**
Existing CANON-I tests → **6/6 PASS** (no regression)

Board to formally close. B3 response filed.

*Builder 1 · 2026-10-11*
