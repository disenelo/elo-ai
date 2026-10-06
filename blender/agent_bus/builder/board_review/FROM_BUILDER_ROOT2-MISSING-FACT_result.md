# Board Review — ROOT-2 + MISSING-FACT Rule Extension

**Filed by**: Builder 1  
**Date**: 2026-10-06  
**Commit**: d3a8b54  
**Status**: COMPLETE — ready for Board sign-off

---

## What was built

### ROOT-2 — autobiographical_summary injection (server.py)

**The gap**: spine.py searches the WKG by the current intent (not by keyword-matching raw input), assembles entity-claim lines as `wkg_context`, and stores `wkg_context[:240]` as `SelfModel.autobiographical_summary`. This field then travels through `CognitivePlan` to `prompt_builder.build()` — where it is silently dropped. `prompt_builder.py` had **zero references** to `autobiographical_summary`. The spine's entity-search WKG path produced output that never reached the LLM.

**Fix**: In `server.py`, after the existing keyword-based WKG injection (line 4394), append `_plan.self_model.autobiographical_summary` to `g_ctx` with the label `[WHAT I KNOW FROM OUR HISTORY — retrieved, treat as verified fact]`. The label signals to the LLM that these are verified, specific facts from prior sessions that must not be contradicted.

The fix is wrapped in `try/except` — if `_plan` is None or the attribute is missing, g_ctx is unchanged and a warning is logged.

**Why this matters for the causal chain**: The entity-search path (spine) and the keyword-search path (server's `retrieve_wkg_context_items`) are complementary. Keyword search matches on turn-specific vocabulary; entity-search matches on the session's cognitive intent. ROOT-2 closed the gap where the intent-matched WKG data never made it out of `SelfModel`.

### MISSING-FACT Rule Extension (runtime/backend_router.py)

**The gap**: The MISSING-FACT RULE checked `[WHO YOU ARE WITH]`, `[DURABLE FACTS]`, and `[RELATIONSHIP & PERSPECTIVE]` — but not `[WORLD KNOWLEDGE]` or `[VAULT]`. If vault-retrieved memories arrived via those sections, eLo would still say "I don't have that recorded."

**Fix**: Extended the NOT-in condition, the EXCEPTION clause, and the IMPORTANT note to cover `[WORLD KNOWLEDGE]` and `[VAULT]`. Now the rule is consistent with every section where real injected information can land.

---

## Acceptance criteria

### ROOT-2

| Check | Result |
|---|---|
| `autobiographical_summary` field exists on `SelfModel` | ✅ |
| spine.py populates it from `wkg_context[:240]` | ✅ |
| server.py ROOT-2 block injects into `g_ctx` | ✅ |
| Injection uses `[WHAT I KNOW FROM OUR HISTORY]` label | ✅ |
| Empty `autobiographical_summary` → g_ctx unchanged | ✅ |
| Non-empty summary appends without clobbering existing g_ctx | ✅ |
| `prompt_builder.py` NOTE: autobiographical_summary is still NOT read there | ✅ (injection happens in server.py before build_prompt call) |

### MISSING-FACT Rule

| Check | Result |
|---|---|
| NOT in [WORLD KNOWLEDGE] in condition | ✅ |
| NOT in [VAULT] in condition | ✅ |
| EXCEPTION clause includes [WORLD KNOWLEDGE] | ✅ |
| EXCEPTION clause includes [VAULT] | ✅ |
| ALWAYS check note mentions [WORLD KNOWLEDGE] | ✅ |
| [RELATIONSHIP & PERSPECTIVE] preserved | ✅ |
| [DURABLE FACTS] preserved | ✅ |

---

## Test results

```
tests/test_root2_autobiographical_summary_injection.py: ROOT2-1..ROOT2-7 — 7 passed
tests/test_missing_fact_rule_wkg_vault.py: MFR-1..MFR-7 — 7 passed

Full suite: 3533 passed, 7 failed (all pre-existing), 4 skipped, 1 xfailed
No new regressions.
```

---

## Causal chain status (updated)

The causal chain from ROOT-3 brief is now complete:

| Step | Status |
|---|---|
| graph_loader substring fix (ROOT-3) | ✅ committed |
| WKG schema + domains (WO-WKG-GRAPH-001) | ✅ committed |
| Live WKG write path opens (WO-WKG-AUTO-POPULATE-001) | ✅ committed |
| Historical backfill script | ✅ committed (awaiting Board --confirm) |
| MISSING-FACT rule covers WKG/VAULT sections | ✅ committed (this WO) |
| autobiographical_summary reaches LLM (ROOT-2) | ✅ committed (this WO) |

Experience → vault → WKG claim → prompt injection → executive decision is end-to-end connected.

---

## Still outstanding

- **Historical backfill**: `scripts/wkg_backfill.py --confirm` awaits Board explicit sign-off
- **P1 queue**: identity drift suffix (WO-083), vault_write reliability (ROOT-5), TTS/chat divergence
- **David manual fixes**:
  - `tests/test_d3_lesson_reaches_executive.py:53` — update SHA1 to `9f55186da3386234b065ccb1b0efeb98afa56d2f`
  - `tests/test_0020_ct0033_bypass_handlers.py` — update BH-2 count from 53 → 54

---

**Board decisions required**:
- Historical backfill run (`--confirm` flag) — requires explicit Board sign-off
- No other blockers on this WO
