# FROM BUILDER — WO-067 Vector Recall SPIKE — Step 1 Result

**WO:** WO-067 — Vector Recall SPIKE (P2, "David GO")  
**Step:** 1 — Diagnose existing path (read-only)  
**Date:** 2026-08-30  
**Type:** Read-only diagnostic. No production changes. No new files in repo.

---

## Question

> "Was the prior clothing recommendation stored durable? Does `retrieve()` / `vault_layer.lookup()` match it on a paraphrased query?"

---

## Evidence gathered

### 1. `memory/facts.json` — 1 entry total

```json
[{ "key": "location", "fact": "Studio / home location: Bristol", "ts": ... }]
```

No clothing or weather recommendation. Write path never stored it here.

### 2. `interactions.json` — raw turns (searched for wear/jacket/coat/outfit)

Two clothing exchanges found. Both have `"memory_categories": []`:

```
turn @ 2026-08-06T00:14:32Z:
  user: "How many layers should I wear for the weather?"
  response: "Two light layers should keep you comfortable."
  memory_categories: []    ← NOT lifted to vault

turn @ 2026-08-07T17:46:03Z:
  user: "What should I wear?"
  response: "Choose something comfortable that suits the weather and fits your plans."
  memory_categories: []    ← NOT lifted to vault
```

### 3. Summary vault (20 records in `obsidian_vault/09 Memory/summary/`)

Searched all 20 records: no weather→clothing recommendation found in any summary file.

### 4. `SPOT_CODES.md`

Single clothing hit (`GN·CV·2607·5`) is Session 412 — "there is also a brand behind disenelo as well which is clothing." About the DISENELO brand, not a clothing-for-weather rec.

---

## Root cause

**WRITE PATH — recommendation was never stored as a durable vault record.**

The conversation happened and the response was generated, but `memory_categories` was empty for both turns. Empty categories = no lift to facts.json, no journal write, no vault summary. The record does not exist in any searchable durable store.

`vault_layer.lookup()` is not the bottleneck — the data was never written to the vault.

A vector store (SPG, Chroma, FAISS) would NOT fix this miss. You cannot retrieve what was never stored.

---

## Conclusion

| Question | Answer |
|---|---|
| Was it stored durable? | **NO** — `memory_categories: []` on both turns |
| Is the retrieval gap the cause? | **NO** — write path is the root cause |
| Would vector store fix it? | **NO** — nothing to index |
| Cheapest fix path | Tag clothing/outfit recommendations with a memory_category so the write path lifts them to the vault |

---

## Recommendation for Board

Step 1 finding: the miss is structural (write path), not semantic (retrieval). Building vector infrastructure (WO-067 Step 2) is premature. The correct next action is a write-path fix — ensure `memory_categories` is populated for contextual recommendations (clothing, weather, plans). This is a small targeted change, not SPG scope.

**Step 2 (Chroma/FAISS benchmark) NOT recommended at this time** — write path must be fixed first or any vector store will have the same gap.

*Builder / Board — 2026-08-30*
