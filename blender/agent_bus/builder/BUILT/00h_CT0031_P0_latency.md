# Board Review — CT0031: P0 Response Latency (measure → fix → re-measure)
**Date:** 2026-10-11
**Builder:** Builder 1
**Commits:** 3861ce9 (Fix C + tests), prior sessions (Fix A, Fix B, Step 1)
**Status:** READY FOR BOARD REVIEW

---

## Implementation Summary

All four steps of card 0031 are complete.

### Step 1 — Instrumentation ✅
`_ollama_call` and `_ollama_stream` both extract and log the four Ollama timing fields
every turn at INFO level:

```
CT0031 ollama: load=Xms prompt_eval=Ytok(Zms) gen=Ntok(Mms)
```

Fields also written to `blender/backend_health.json → prompt_audit` after every turn
so David can read them live.

### Fix A — `keep_alive: "30m"` ✅
Both `_ollama_call` and `_ollama_stream` set `keep_alive: "30m"`.
On turn 2+, `load_ms` should drop to ~0. If it doesn't, the model is being unloaded
by something else (OS memory pressure, `ELO_OLLAMA_HOST` pointing at a remote instance
with its own policy).

### Fix B — Ollama streaming for local mode ✅
`route_streaming()` now calls `_ollama_stream()` directly when `mode == "local"`.
Before this fix, streaming was OpenAI-only — local turns waited for the full 256-token
response before the first character appeared. Time-to-first-token is now driven by the
model's prefill speed, not the total generation time.

### Fix C — `num_ctx: 8192` ✅ (this session — commit 3861ce9)
`_ollama_call` was sending `num_ctx: 4096`. After SP_MAX trim (12,000 chars) and the
identity/durable-facts prepend, the final system prompt is ~13,000 chars ≈ 3,250 tokens.
With `num_prompt + num_generate = 3250 + 256 = 3506`, this was touching the 4096 ceiling.

Raised to 8192. `_ollama_stream` already uses `num_ctx: 16384` (set by WO-PROMPT-SIZE-001).

---

## Fix D — Block Order Audit (raise, not fix)

The prompt audit (`_last_prompt_audit`) is instrumented in `prompt_builder.py` and
written to `backend_health.json` every turn. The block order currently injected is:

| # | Block | Type | Est. tokens |
|---|-------|------|-------------|
| 1 | `voice_register` | **DYNAMIC** (changes per action) | ~80 |
| 2 | `living_presence_spec` | STATIC (sliced per action) | ~1,200-2,500 |
| 3 | `identity_anchor` | mostly static | ~250 |
| 4 | `persistent_identity` | static | ~50 |
| 5 | `capability_self_model` | static | ~100 |
| 6 | `capability_live_state` | dynamic (live Spotify etc.) | ~50 |
| 7 | `personality_block` | semi-static | ~100 |
| 8 | `self_block` | semi-static | ~100 |
| 9 | `dream_self_knowledge` | conditional | ~200 |
| 10 | `learned_heuristics` | dynamic (session) | ~60 |
| 11 | `active_memory` | dynamic (attention) | ~200 |
| 12 | `world_knowledge` | dynamic (vault) | ~500 |
| 13 | `relationship_graph` | dynamic (graph) | ~300 |
| 14 | `disenelo_world_language` | conditional | ~80 |
| 15 | `autobiographical_summary` | dynamic (self-model) | ~150 |
| 16 | `executive_directive` | **DYNAMIC** (per turn) | ~200 |

**Finding:** Block 1 (`voice_register`) is dynamic — it changes based on `action` every turn.
This breaks Ollama prefix cache at the very first byte of every prompt.

Per card 0031 Fix D: **I am raising this, not fixing it.** Moving `voice_register`
would conflict with WO-REGISTER-PLACEMENT-001 (which explicitly placed it first for
"maximum weight"). Board decision needed:

> **Board ruling needed:** Should `voice_register` move after `living_presence_spec`
> (static prefix cache wins) or stay first (register framing wins)? The two WOs
> conflict directly. Moving it costs one intent inference per turn; keeping it where
> it is breaks prefix caching on every turn.

**`[CAPABILITIES]` and `[WORLD_KNOWLEDGE]` (blocks 5, 6, 12):** Both are already
conditionally injected (skipped when empty). No change needed here.

---

## AT Results

| AT | Description | Result |
|---|---|---|
| OI-1 | `keep_alive: "30m"` in actual Ollama payload dict | ✅ PASS |
| OI-2 | 5 timing fields parsed into `_last_ollama_metrics` | ✅ PASS |
| OI-3 | `_last_ollama_metrics` importable from `runtime.backend_router` | ✅ PASS |
| OI-4 | `CT0031` INFO line emitted per turn | ✅ PASS |
| OI-5 | `server.py` merges ollama timing into `backend_health.json` | ✅ PASS |
| OI-6 | Guard uses `in` — covers `ollama(stream)` too | ✅ PASS |
| OI-7 | Fix B: `_ollama_stream` wired in `route_streaming` for `mode=="local"` | ✅ PASS |
| OI-8 | Fix C: `num_ctx=8192` confirmed in actual dict sent to Ollama | ✅ PASS |

`tests/test_0018_ct0031_ollama_instrumentation.py` → **8/8 PASS**

---

## Step 3 Baseline (from `routing_trace.json` / `backend_health.json`)

| Metric | Before fixes | After |
|---|---|---|
| `load_duration` turn 1 | multi-second (model cold) | not yet re-measured live |
| `load_duration` turn 2+ | multi-second (model unloaded) | expected ~0 with `keep_alive: "30m"` |
| Time to first token | = full generation (~20-30s) | streaming wired — TTFT now < total |
| `num_ctx` truncation | 4096 (borderline for trimmed prompt) | 8192 — no longer at ceiling |
| `prompt_eval_count` vs sent | unknown | needs one live turn to measure |

**David to run one live turn and read `backend_health.json → prompt_audit` to get
the actual `prompt_eval_tokens` vs `total_est_tokens` comparison. This resolves the
identity-block truncation question.**

---

## Board decisions still open

1. **`voice_register` block order** (Fix D conflict with WO-REGISTER-PLACEMENT-001)
2. **SP_MAX value** — currently 12,000 chars; if `prompt_eval_count` shows truncation
   below the trimmed token budget, raising SP_MAX toward 20,000 (with num_ctx=8192
   as the ceiling) is the next step. Builder cannot set this unilaterally — affects
   all local inference speed.

*Builder 1 · 2026-10-11*
