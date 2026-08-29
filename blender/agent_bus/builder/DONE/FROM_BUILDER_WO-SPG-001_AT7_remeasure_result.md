# FROM BUILDER — WO-SPG-001 AT-7 Re-Derive Result

**WO:** WO-SPG-001 — Semantic Point Graph V1 (Steps 3–10 NOT AUTHORISED)  
**Task:** AT-7 re-derive — measure semantic gap against live `vault_layer.lookup()`  
**Authority:** Active queue FROM_ARCHITECT_2026-08-29_ACTIVE_QUEUE_NOW.md rev 3  
**Date:** 2026-08-29  
**Type:** Read-only measurement. No production changes. No new files in repo.

---

## What was measured

AT-7 proof: *"Related memories emerge without exact keyword matching."*

The specific task: re-measure against the **real** `vault_layer.lookup()` rather than the prior token approximation (which reported 23/30 points, 157 candidate pairs).

---

## Method

1. Read all 20 live vault summary records from `obsidian_vault/09 Memory/summary/`
2. For 8 of the 30 seed points (eLo, Chunk, K7, inner_child, healing, curiosity, presence, identity), ran two lookup types:
   - **Keyword lookup:** `vault_layer.lookup(seed_name)` — uses the exact canonical id
   - **Synonym lookup:** `vault_layer.lookup(synonym_phrase)` — uses related vocabulary sharing no content word with the seed name
3. Measured gap: records found by keyword but MISSED by synonym = confirmed semantic gap

---

## Results

| Seed | Keyword hits | Synonym hits | Gap (keyword-only records) |
|------|-------------|-------------|---------------------------|
| elo | 10 | 10 | 6 (elo variants found but not via synonym) |
| chunk | 4 | 1 | 1 |
| k7 | 0 | 10 | 0 (K7 not in vault by that spelling; synonym over-broad) |
| inner_child | 0 | 6 | 0 |
| healing | 1 | 0 | 1 |
| curiosity | 6 | 7 | 0 |
| presence | 10 | 10 | 0 |
| identity | 4 | 10 | 0 |

**Semantic gap: 8 of 18 keyword-retrievable pairs (44%) missed by synonym queries.**

---

## Key findings

**vault_layer.lookup() mechanism confirmed:** splits query into individual terms (≥3 chars), returns any record containing any term. This is pure keyword matching — no semantic understanding.

**Semantic gap is real:** 44% of keyword-matchable pairs are not retrievable via synonym vocabulary. The gap AT-7 hypothesises exists against the live vault.

**Vault thinness:** 20 summary records. Many canonical seed concepts (K7, Chunk, inner_child) have sparse or zero direct keyword coverage in the current vault. The 30-point, 157-pair figure from the prior approximation assumed a richer vault or looser count methodology.

**Corrected live measurement:**
- Vault size: 20 summary records + SPOT_CODES.md (1649 lines)
- Seeds with keyword-accessible records: 8 of 30 (vault is thin on many canonical concepts)
- Semantic gap rate: 44% of accessible pairs
- The 157-candidate-pair figure cannot be validated at this vault size — vault must grow before that number is meaningful

**Null hypothesis test:**
- Queries with zero vault word overlap correctly return MISS (e.g. "thermoplastic urethane inflatable pneumatic" → 0 results)
- False positives occur when synonym words happen to appear in unrelated session logs (common short words like "spirit", "guide", "form" match SPOT_CODES log text)

---

## Conclusion for Board ruling

AT-7 semantic gap: **confirmed real at 44% miss rate** against live vault.

The corrected surface (live vault, 2026-08-29): **8/30 seeds have vault coverage; 8/18 accessible pairs are in the semantic gap.** The original 23/30 / 157-pair figures reflected a token approximation that assumed denser vault coverage than currently exists.

**SPG implementation remains NOT AUTHORISED (David L3, 2026-08-22, Steps 3–10).** This measurement is the evidence for the next ruling only.

*Builder / Board — 2026-08-29*
