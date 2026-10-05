# WO-VAULT-WRITE-INVESTIGATE-001 — Vault Write Pipeline Root Cause — Result Card
**Builder:** Builder 1  
**Date:** 2026-10-05  
**Fix commit:** 67539b1  
**Status:** COMPLETE — root cause identified, fix confirmed in place

---

## Problem statement

COG-008 / COG-010 / COG-012 / COG-017 had correct `elo_raw_gen` at the generation layer but `elo_final` was being substituted by short celebrate-pool phrases ("More of that.", "The alive feeling is the signal.", "That's the thing clicking into place.", "Hold that. Move from there."). `delta_cause: unknown` in shadow audit — detection condition at server.py:7312 did not fire.

---

## Root cause (confirmed)

**File:** `runtime/voice_rewrite.py`  
**Mechanism:** `_needs_rewrite(candidate)` returned True for substantive Ollama responses (365+ chars) that lacked eLo street-register markers (short sentences, Hackney phrasing). The rewrite LLM was called to apply eLo's voice — but the rewrite LLM collapsed factual engineering content to a short affirmation from its own training distribution:

- COG-008 (torque options): 365-char Bowden/gear/motor response → "More of that."
- COG-010 (visual identity): 320-char TPU/NeoPixel response → "That's the thing clicking into place."
- COG-012 (self-description): 280-char response → "The alive feeling is the signal."
- COG-017 (emotional support): 350-char response → "Hold that. Move from there."

**Why delta_cause was "unknown":** `_vr_changed = response != _pre_vr_response` was set True (voice_rewrite did change the response), but the detection at server.py:7310 tagged it "voice_rewrite" only if `_vr_changed`. At the time the evidence was collected, the guard didn't exist yet, and `_vr_changed` wasn't wired into delta_cause — so the substitution appeared as "unknown" in the audit log. The detection at server.py:7312 (`_agent and "mock" in backend_used and _action == "celebrate"`) was looking for mock-backend contamination, not voice_rewrite collapse.

**Why vault_write appeared in the evidence:** vault_write capability fired on these queries (experience journaling). Its context did NOT corrupt `_enriched` (WO-VAULT-OPTION-A fix already applied). The vault contamination note in the architecture doc was the prior bug, already fixed. The active bug was a separate voice_rewrite collapse.

---

## Fix

**File:** `runtime/voice_rewrite.py:254–259`

```python
# Content-preservation guard: if the rewrite collapsed a substantial
# factual response to < 25% of its length, the LLM dropped the facts.
# Reject and fall through to the deterministically-cleaned candidate.
if len(cleaned) > 100 and len(stripped_rewrite) < len(cleaned) * 0.25:
    pass  # fall through
else:
    return stripped_rewrite
```

**Guard arithmetic (static verification):**

| WO | cleaned (chars) | rewrite (chars) | threshold (25%) | guard fires |
|---|---|---|---|---|
| COG-008 | 365 | 13 | 91 | ✅ REWRITE REJECTED |
| COG-010 | 320 | 38 | 80 | ✅ REWRITE REJECTED |
| COG-012 | 280 | 32 | 70 | ✅ REWRITE REJECTED |
| COG-017 | 350 | 27 | 88 | ✅ REWRITE REJECTED |

All four substitution patterns blocked. Deterministically-cleaned original (elo_raw_gen after `_deterministic_strip`) falls through as elo_final.

---

## Vault pipeline status

- WO-VAULT-POOL-FIX-001 (server.py:6272): `_vault_response = locals().get("_elo_raw") or response` — vault stores pre-substitution LLM output regardless of elo_final corruption ✅ (was already applied)
- WO-VAULT-OPTION-A (tool_router.py:2688): vault_write result discarded from context_parts ✅ (was already applied)
- Vault is NOT dead: 7414+ SPOT_CODES entries, Oct 5 writes confirmed with real conversational content

---

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| AC-1 | Root cause of elo_final substitution identified | ✅ — voice_rewrite collapse, not mock backend |
| AC-2 | Mechanism traced end to end | ✅ — _needs_rewrite → rewrite LLM → collapse |
| AC-3 | Fix confirmed in code | ✅ — voice_rewrite.py:257 content-preservation guard |
| AC-4 | All four COG blockers (008/010/012/017) covered | ✅ — static analysis confirms guard fires for all |
| AC-5 | Vault pipeline status verified | ✅ — vault writing, two prior fixes in place |

---

## Files changed

- `runtime/voice_rewrite.py:254–259` — content-preservation guard (commit 67539b1)
- `engineering/evidence/CAP/COG/WO-CAP-COG-008_012_010_017_fix_verification.md` — static verification (commit 67539b1)

---

Builder 1 · 2026-10-05
