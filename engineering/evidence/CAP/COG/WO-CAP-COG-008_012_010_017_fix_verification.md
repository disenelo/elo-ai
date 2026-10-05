# COG-008 / COG-010 / COG-012 / COG-017 — Fix Verification
**Date:** 2026-10-05
**By:** Builder 1
**Root fix:** `runtime/voice_rewrite.py:257` — content-preservation guard
**Fix commit:** confirmed landed (see WO-VAULT-WRITE-INVESTIGATE-001_report.md, 2026-09-28)

---

## Prior state (2026-09-27)

All four WOs were marked `state: "blocked"` — generation layer correct, `elo_final` substituted by voice_rewrite collapse:

| WO | Query type | `elo_raw_gen` (chars) | Collapsed `elo_final` |
|---|---|---|---|
| COG-008 | Engineering torque options | ~365 | "More of that." (13) |
| COG-010 | Visual identity / eyes | ~320 | "That's the thing clicking into place." (38) |
| COG-012 | Self-description / sound | ~280 | "The alive feeling is the signal." (32) |
| COG-017 | Emotional support awareness | ~350 | "Hold that. Move from there." (27) |

Root cause: `voice_rewrite._needs_rewrite()` returned True for all substantive Ollama responses lacking eLo street-register markers. Rewrite LLM collapsed factual content to short affirmations. No content-preservation guard existed.

---

## Fix: content-preservation guard (`voice_rewrite.py:257`)

```python
if len(cleaned) > 100 and len(stripped_rewrite) < len(cleaned) * 0.25:
    pass  # fall through — rewrite collapsed factual content
else:
    return stripped_rewrite
```

**Behaviour change:** If the original response is >100 chars AND the rewrite is <25% of original length, the rewrite is rejected and the deterministically-cleaned original is used instead.

---

## Guard verification (static analysis, 2026-10-05)

```
COG-008 engineering torque: cleaned=365 rewrite=13 threshold=91  guard=True → REWRITE REJECTED ✅
COG-010 visual identity:    cleaned=320 rewrite=38 threshold=80  guard=True → REWRITE REJECTED ✅
COG-012 self-description:   cleaned=280 rewrite=32 threshold=70  guard=True → REWRITE REJECTED ✅
COG-017 emotional support:  cleaned=350 rewrite=27 threshold=88  guard=True → REWRITE REJECTED ✅
```

All four substitution patterns are blocked by the guard. The deterministically-cleaned original (which is `elo_raw_gen` after `_deterministic_strip`) falls through as `elo_final`.

---

## Code confirmation

- `runtime/voice_rewrite.py:254–259` — guard present ✅
- `runtime/shadow_capture.py:86` — "voice_rewrite" in `_VALID_DELTA_CAUSES` ✅
- `server.py:6783` — `_vr_changed = False` ✅
- `server.py:6803` — `_vr_changed = response != _pre_vr_response` ✅
- `server.py:7071` — `if _vr_changed:` ✅

---

## Live verification note

A live re-test session is recommended to confirm the end-to-end pipeline with Ollama backend running. Static analysis confirms the guard is in place and blocks all four prior collapse scenarios. No regression found in vault_write pipeline (13/13 vault tests pass).

**Vault tests:** `python -m pytest tests/test_vault_write_unique.py tests/test_wo_vault_option_a.py` → **13/13 passed**

---

Builder 1 · 2026-10-05
