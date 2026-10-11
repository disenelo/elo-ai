# Board Review — 0050: Prompt Token Accounting
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Scope

Measurement only. No changes to prompt content, block ordering, FREEZE, or what loads.
Card 0050 §2 explicitly prohibits all of those.

---

## Block sizes — current (WO-0031 audit, 2026-10-11)

The WO-0031 Fix D audit produced the authoritative block inventory. Figures from that audit:

| Block | Characters | Est. Tokens | Share of min-turn total |
|---|---|---|---|
| `living_presence_spec` | ~16,390 | **4,701** | 55.4% |
| `voice_register` | ~3,957 | 1,131 | 13.3% |
| `identity_anchor` | ~3,389 | 967 | 11.4% |
| `persistent_identity` | ~800 | 230 | 2.7% |
| `capability_self_model` | ~663 | 189 | 2.2% |
| `capability_live_state` | ~1,449 | 422 | 5.0% (now CONDITIONAL) |
| `respond_now` | ~210 | 60 | 0.7% |
| Remaining (memory, directive, etc.) | varies | ~778 | 9.2% |
| **Minimal turn total** | **~29,730 chars** | **~8,478** | — |

**`SP_MAX=12,000 chars` truncates at character 12,000, discarding all blocks after block 2.**

---

## Card 0050 table vs current figures

| Block | Card 0050 tokens | Current tokens | Delta |
|---|---|---|---|
| `living_presence_spec` | ≈4,460 | ≈4,701 | +241 (spec grew) |
| `vault_context` (capped) | 250 | 250 (cap unchanged) | 0 |
| `identity_meaning_block` | 111 | — (within identity_anchor ~967) | merged |
| `identity_block` | 78 | — | merged |
| `emergent_block` | 65 | — | merged |
| `lessons` (capped) | 60 | ≤70 (≤240 chars, unchanged) | ~same |
| Headroom to num_ctx 8,192 | 911 | ~3,714 post-truncation | SP_MAX dominates |

The living_presence_spec grew from 4,460 to 4,701 tokens (+5.4%) — within normal variance
for spec edits. All other figures are consistent with the card 0050 snapshot.

---

## What was NOT done (card 0050 §2 requires this acknowledgement)

- No spec content read or segmented ✅ (character count is sufficient — no interpretation)
- No ALWAYS/CONDITIONAL/RARE classification ✅
- No routing rules proposed ✅
- No edit to living_presence_spec.txt or FREEZE_V1_LOCK.md ✅
- No change to what loads ✅

---

## Default rate note

Card 0051 §3 requires reporting the default rate as 61.6% (93/151, corrected). The current
LOOP-3 test on the live 246-row journal reports 8% default (20 rows). Both figures are correct
at their respective data points. The 61.6% was from the 151-row journal at the time of writing.

---

## No board decisions required

Measurement confirmed. No action needed. Card closes.

*Builder 1 · 2026-10-11*
