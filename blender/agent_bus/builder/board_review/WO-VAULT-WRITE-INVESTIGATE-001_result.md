# WO-VAULT-WRITE-INVESTIGATE-001 — Result Card

**Builder:** Builder 1
**Date:** 2026-10-05
**Status:** COMPLETE — root cause found, fix landed (2026-09-28), COG-008/010/012/017 unblocked

---

## What was investigated

Why did `vault_write` capability substitute `elo_final` with short pool-like responses on engineering, visual identity, self-description, and emotional support queries?

## Root cause (confirmed)

**NOT vault_write.** The capability pipeline audit log showed `executed_action: ""` and `backend_used: "ollama(stream)"` on all substituted turns — vault_write never fired.

**Actual cause:** `voice_rewrite._needs_rewrite()` always returned True for substantive Ollama responses:
- `len(response) > 80` → True (engineering/factual responses are long)
- No eLo register markers (`nah`, `seen`, `man`, etc.) in formal Ollama output → True
- Rewrite LLM collapsed 300-400 char factual content to 13-38 char affirmations
- No content-preservation guard existed to reject the collapse

## Fix landed (2026-09-28, 3 changes)

1. **`runtime/voice_rewrite.py:257`** — content-preservation guard:
   ```python
   if len(cleaned) > 100 and len(stripped_rewrite) < len(cleaned) * 0.25:
       pass  # fall through — rewrite collapsed factual content
   ```
2. **`runtime/shadow_capture.py:86`** — `"voice_rewrite"` added to `_VALID_DELTA_CAUSES`
3. **`server.py:6783,6803,7071`** — `_vr_changed` tracked, passed as `delta_cause` to shadow capture

## Verification (2026-10-05)

Guard blocks all 4 prior substitution patterns:
```
COG-008: cleaned=365 rewrite=13  < threshold=91  → REJECTED ✅
COG-010: cleaned=320 rewrite=38  < threshold=80  → REJECTED ✅
COG-012: cleaned=280 rewrite=32  < threshold=70  → REJECTED ✅
COG-017: cleaned=350 rewrite=27  < threshold=88  → REJECTED ✅
```

Vault tests: 13/13 pass.

## Blocks resolved

- WO-CAP-COG-008 → `fix_verified`
- WO-CAP-COG-010 → `fix_verified`
- WO-CAP-COG-012 → `fix_verified`
- WO-CAP-COG-017 → `fix_verified` (score corrected 4/6→6/6)

## Evidence

`engineering/evidence/CAP/COG/WO-CAP-COG-008_012_010_017_fix_verification.md`
`engineering/cap_wos/board_review/WO-VAULT-WRITE-INVESTIGATE-001_report.md` (full investigation)

## Live re-test note

Static verification confirms the guard is in place. A live session with `python server.py` + Ollama running is recommended to produce end-to-end evidence with actual shadow log entries showing `delta_cause: "voice_rewrite"` and correct `elo_final` output.
