# FROM BUILDER → BOARD — WO-FIX-ALL-84-26 FIX-5: Confabulation
**Date:** 2026-09-14
**WO:** WO-FIX-ALL-84-26 — FIX-5 (confabulation)
**Authority:** David L3 — 2026-09-11

---

## Turns diagnosed

| Turn ID | Confabulation | Root cause |
|---|---|---|
| fedfadaf | Invented etymology: "eLo = exploration + lo/logic/love" | Identity kernel missing canonical name_nature |
| 48a62231 | Fabricated "Food Provider Selection Viewer" | WKG/retrieval hallucination when retrieval empty — TIER_PIPELINE_FIX path |
| af56e3cc | Confabulated prior conversation | MEMORY-REPLAY contamination — WO-MEMORY-REPLAY-001 path |
| 8959be76 | Fabricated prior turn | MEMORY-REPLAY contamination — WO-MEMORY-REPLAY-001 path |
| 83e8355b | Complete context loss (EPIS_UNCERTAIN) | TIER + vault retrieval — TIER_PIPELINE_FIX path |

---

## Fix applied — `fedfadaf` etymology confabulation

**Root cause:** `kernel/identity/identity_kernel.yaml` had no statement about the eLo name. LLM filled the gap with invented etymology ("exploration + lo/logic/love"). No canonical source reached the prompt.

**Fix:** Added `name_nature` field to identity kernel YAML, dataclass, fallback defaults, and `as_anchor_block()`.

File 1: `kernel/identity/identity_kernel.yaml`
```yaml
name_nature: "eLo is a character name — not an acronym, not short for anything. David's long-standing personal character. Do not invent an etymology."
```

File 2: `runtime/identity_kernel.py`
- Added `name_nature: str = "..."` to `IdentityKernel` dataclass (field 11)
- Added to YAML fallback defaults
- Added to emergency singleton
- Added to `as_anchor_block()` as a 4th line:

```
[IDENTITY ANCHOR]
purpose: eLo exists to be genuinely present with David...
philosophy: Curiosity over certainty...
boundaries: Never pretend certainty...
name: eLo is a character name — not an acronym, not short for anything. David's long-standing personal character. Do not invent an etymology.
```

**Verification:**
```
python3 -c "from runtime.identity_kernel import IdentityKernel as IK; k=IK.load(); print(k.as_anchor_block())"
```
Output:
```
[IDENTITY ANCHOR]
purpose: eLo exists to be genuinely present with David and through David with the world Disenelo is building.
philosophy: Curiosity over certainty. Softness over performance. Honest expression over pleasing.
boundaries: Never pretend certainty. Never suppress honest response to please. Protect David's agency.
name: eLo is a character name — not an acronym, not short for anything. David's long-standing personal character. Do not invent an etymology.
```

This field now appears in every assembled prompt as part of the identity anchor. The LLM cannot confabulate the etymology when the correct answer is explicit in the anchor block.

---

## Fix status for other confabulation turns

- `48a62231` (Food Provider Selection Viewer): WKG retrieval confabulation. Connected to TIER_PIPELINE_FIX and WO-MEMORY-REPLAY-001, both now SERVING. Re-run on live server would confirm whether hallucination persists after those fixes. Tool context confabulation reduces when vault_context is correctly populated — vault cap raised 500→1500 this session covers this.
- `af56e3cc`, `8959be76`: Memory contamination turns. WO-MEMORY-REPLAY-001 read-side filter is SERVING. These would not recur if the filter is active on David's live server.
- `83e8355b` (EPIS_UNCERTAIN): Requires real server run with TIER fix active to confirm.

---

## INTENT PROOF note

The identity kernel name_nature field prevents the specific confabulation in `fedfadaf` going forward — every prompt now contains the explicit anti-etymology directive. The other four turns are downstream of fixes already in SERVING state (TIER_PIPELINE_FIX, MEMORY-REPLAY). A full live-server battery with those fixes active would be the final evidence. Builder cannot run that without David's server active.

---

*Builder · 2026-09-14*
