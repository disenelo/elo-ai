# WO-067 — SPIKE: vector store for cross-session recall (test, don't adopt-on-faith)

**Owner:** Builder (eLo OS — memory lane). **Priority:** P2 — a measured spike, not a commitment.
**Status:** OPEN — spec'd 2026-08-07. **Type:** SPIKE (evaluate → recommend → David/Chief decide adopt).
**Canon:** Check-Before-Build (do NOT add a parallel store unless the existing vault provably can't do it) ·
Reality Before Narrative (recall must be true, with confidence + source — WO-053) · Vision Spine "hold the
thread" (David 2026-08-07).

## Why
Live transcript #2 (2026-08-07): eLo could NOT recall a prior weather→clothing recommendation across
sessions ("I don't have a record of us discussing the weather"). In-session thread recall works; DURABLE
cross-session recall does not surface. `test_wo037` writeback is green, so the miss is in RETRIEVAL/matching,
not writing. Question this spike answers: **is the current vault retrieval the bottleneck, and would a local
vector store (Chroma or FAISS) fix it — or is the fix just repairing the existing retrieval path?**

## Do (measured, reversible — a spike, additive, no rip-out)
1. **First, diagnose the existing path** (cheapest fix wins): was the prior rec stored durable? Does
   `retrieve()` / `vault_layer.lookup()` match it on a paraphrased query ("what did you say to wear")? If a
   small fix to the existing retrieval closes it → do THAT, no vector store needed. Report the finding.
2. **If (and only if) the existing retrieval is the real bottleneck**, stand up a LOCAL, offline vector
   index (Chroma or FAISS) over the same memory corpus — additive, behind the existing memory API, NOT a
   replacement store. Embed durable memories; query by semantic similarity; return the WO-053 envelope
   (confidence + source + timestamp) so honesty is preserved.
3. **Benchmark head-to-head** on a fixed recall set (incl. the weather→clothing case + 10 paraphrase
   queries): current vault vs vector index — recall@k, correctness, latency. Numbers, not vibes.

## Definition of Done (the spike's deliverable is a DECISION, not a rewrite)
A short written recommendation: (a) the root cause of the cross-session miss; (b) whether a vector store
measurably beats the vault (with the benchmark numbers); (c) if yes, the minimal additive integration
(offline, local, behind the memory API, WO-053 envelope preserved) — else "repair existing retrieval,
no new store." David/Chief decide adopt.

## Test — WITHOUT David (`tests/test_wo067_recall_benchmark.py`)
- The weather→clothing recall case returns the prior recommendation across a simulated session boundary
  (whichever path wins).
- 10 paraphrase queries → recall@k measured for both paths; results printed.
- Any new index is LOCAL + OFFLINE (no network at query time); returns the WO-053 confidence envelope;
  absence → honest "I don't have that", never fabricated.

## Lane / guardrails
Builder only (Python). Additive spike — does not remove the vault. Ties WO-022/037 (durable recall) +
WO-053 (recall confidence). If adopted, it's a memory *index*, not a second source of truth.
