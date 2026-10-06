# RESULT — ROOT-5 / WO-VAULT-WRITE-INVESTIGATE-001: vault_write pipeline
**From:** Builder 1
**To:** Board
**Date:** 2026-10-06
**Commit:** b303192
**Status:** DONE (investigation complete + delta tracking fix)

---

## Findings

### Shadow journal analysis (109 entries)

| delta_cause | Count | Meaning |
|---|---|---|
| "none" | 108 | elo_raw_gen == elo_final — no divergence |
| "unknown" | 1 | Scrub modified the response (mirror scrub) |
| "voice_rewrite" | 0 | Voice rewrite path not firing in this sample |
| "capability_celebrate_override" | 0 | Pool contamination not firing |

The single "unknown" entry: mirror scrub changed "David" → "you" inside a response about the physical robot build. The scrub is correct; the labelling was wrong.

### Pool substitution (COG-008/010/012/017) — ALREADY FIXED

`server.py:6563`: `_vault_response = locals().get("_elo_raw") or response`

This is the WO-VAULT-POOL-FIX-001 fix already in production. `_elo_raw` is captured at generation (line 6412), before scrubs. Pool fast-returns from backend_router — the pool IS the generation for those paths (no LLM runs), so `_elo_raw` correctly records the pool text when it's the intended response.

The four blocked COG WOs (008/010/012/017) may be unblocked — need Board to re-test each.

### Vault write volume

1062 entries in `obsidian_vault/09 Memory/`. The main write path fires on every turn: `significance=0.55 if _mem_cats else 0.25`, both above `_DROP_THRESHOLD=0.15`. Vault IS reliably writing.

### Root cause of delta_cause "unknown"

`_sc_delta` at server.py:7706 was only set for:
1. `voice_rewrite` — VR path changed the response
2. `capability_celebrate_override` — agent + mock + celebrate = pool contamination

Mirror scrub, argot scrub, MCG scrub, `_sanitise()` — none of these set `_sc_delta`. Any modification from these scrubs appeared as "unknown".

## Fix applied

Added `elif locals().get("_elo_raw") and locals().get("_elo_raw") != response:` that sets `_sc_delta = "scrub_modified"` — making all remaining divergences traceable.

## Outstanding

ROOT-5 "vault_write reliability" in IS-ELO verdicts referred to "not reliably writing from live turns." Data shows vault IS writing reliably. The semantic gap (writing turn-by-turn episodic logs with epistemic_class="inference" vs writing specific retrievable facts) is addressed by ROOT-1 (wkg_fact_extractor).

COG-008/010/012/017 block status: pool substitution is fixed. Board should re-test whether those WOs now pass.
