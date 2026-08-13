# WO-071 — Real-time correction memory (in-context reflection loop)

**Owner:** Builder (eLo OS). **Priority:** P2 — after WO-070 has data; does NOT block Presentable.
**Status:** OPEN — spec'd 2026-08-07 (David's "real-time learning" Phase 2). **Depends on:** WO-070
(the shadow log it reads). **Canon:** ADR-Exec-005 (learn from verified consequences) · Volume XXVIII.

## The idea (real-time learning WITHOUT changing weights)
Not weight updates (that's the batch fine-tune, Vol XXVIII). Real-time = **in-context**: before a turn hits
the LLM, retrieve eLo's recent SLIPS (rows where `elo_raw_gen != elo_final`, i.e. the verify/scrub caught
something) + any `l3_rating` overrides from the WO-070 shadow log, and inject a tight reminder into the
system prompt: "recently you produced X, corrected to Y, David marked it Z — don't repeat that slip." eLo
then adjusts on the fly, learning from its last mistake with no training pass.

## Check-Before-Build (do NOT build a parallel ICL loop)
eLo ALREADY has the substrate: **`self_improvement/correction_store.py`** + `evaluator.py` (WO-027 —
"self_improvement golden-set + LLM-judge + ICL correction-memory", 8/8 AT). EXTEND that store to (a) ingest
the WO-070 shadow log as a correction source and (b) serve a retrieval at turn-time. Do NOT create a second
correction memory.

## Scope
1. **Retrieve (turn-time, lightweight):** pull top-N (3–5) recent corrections from the correction store /
   shadow log, preferring ones RELEVANT to the current input (not just the tail), plus recent L3 overrides.
2. **Inject (bounded):** append a short, capped "recent-corrections" frame to the system prompt via the
   existing prompt_builder — small token budget, never crowding the turn. Format: the slip, the correction,
   the L3 verdict, the trace_id.
3. **Guardrails (ADR-Exec-005 + honesty):** ICL sharpens STYLE/behaviour only; it must NOT override the
   Executive, the verified self-model, or the honesty guards. It is a hint, not an authority. If no relevant
   correction exists, inject nothing (no filler).

## Definition of Done
A turn that resembles a past slip gets the corrected behaviour without a training pass; the injected frame is
bounded (token-capped, top-N); irrelevant turns get no injection; the Executive/honesty layer still has final
say.

## Test — WITHOUT David (`tests/test_wo071_realtime_correction.py`)
- Seed the store with a slip (raw_gen≠final) + L3 override → a similar new input's system prompt contains the
  correction frame (slip, correction, verdict).
- Unrelated input → no injection (no filler, token budget respected).
- Injection never exceeds the cap; malformed store entry → skipped, no crash.
- The correction frame is a HINT: a contrived case where the hint conflicts with a verified fact → the
  Executive/honesty layer wins (ICL does not override truth).

## Lane
Builder only (Python). Extends `self_improvement/correction_store.py` (WO-027) + reads WO-070. Sits between
capture (WO-070, now) and the batch fine-tune (Vol XXVIII, post-Presentable).
