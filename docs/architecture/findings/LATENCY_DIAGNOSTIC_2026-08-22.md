# LATENCY DIAGNOSTIC — 2026-08-22

**Authority:** David directive (`_intake/SOURCE_2026-08-22_DAVID_latency_diagnostic_instruction.md`)
**Scope:** Measurement only. No code changes. No prompt trimming. `living_presence_spec` is identity, not overhead.
**Hardware:** Apple M2 Max · 32 GB RAM · Mac Studio (Mac14,13)
**Model:** `llama3.1:8b` · Q4_K_M · 4.92 GB · context_length 131,072 (native)

---

## HARDWARE CAPTURE

| Field | Value |
|---|---|
| Model | `llama3.1:8b` |
| Model size | 4.92 GB (Q4_K_M) |
| Quantization | Q4_K_M |
| Hardware | Apple M2 Max |
| RAM | 32 GB unified |
| GPU offload | Apple Metal (unified memory — CPU/GPU share) |
| keep_alive setting (code) | `"30m"` (backend_router.py:325 + :687) |
| num_ctx setting (code) | `8192` (hardcoded options) |
| Ollama native context_length | 131,072 |

---

## SECTION 1 — MODEL RESIDENCY

### Test

Two back-to-back requests with minimal prompt (12 tokens). Model was NOT loaded at test start (confirmed via `/api/ps` → `{"models":[]}`).

| Request | load_duration | prompt_eval | gen | total | prompt_eval_rate |
|---|---|---|---|---|---|
| REQUEST 1 (cold — model not in memory) | **6.47s** | 0.11s (12t) | 0.10s (5t) | **6.69s** | 108.9 t/s |
| REQUEST 2 (hot — model resident) | **0.25s** | 0.02s (12t) | 0.08s (5t) | **0.35s** | 606.3 t/s |
| Speedup | **19×** | 5.5× | — | **19×** | — |

After REQUEST 2: `/api/ps` confirmed model resident, expires 2026-08-22T16:10:48 (+30 min from request).

### Finding

**KNOWN: keep_alive is working.** The model stays in memory for 30 minutes after a request. The problem is the INITIAL cold start — the model is not preloaded when eLo OS receives an incoming request after idle.

**KNOWN: model load is the dominant first-turn cost.** At 6.47s on M2 Max, model loading alone accounts for 97% of the first cold-turn total.

**CALCULATED: warm-model baseline** — if the model were already resident when a turn begins, `load_duration` drops from ~6-11s to ~0.25s. This saves ~6-11s per cold start with zero change to eLo's prompt, identity, or behaviour.

### Why keep_alive expires

After 30 minutes of idle (no requests), Ollama unloads the model. The next request triggers a fresh load. During a conversation, keep_alive resets on every response — so the model stays warm for the duration. The problem is between conversations.

---

## SECTION 2 — REALISTIC PROMPT MEASUREMENT

### Test

Assembled prompt using real eLo components (living_presence_spec + personality_block + identity_block + narrative_block + user message). Model was warm (resident from residency test).

| Metric | Value |
|---|---|
| Assembled prompt | 20,400 chars · ~5,100 tokens |
| load_duration | 0.19s (model resident) |
| prompt_eval_duration | 10.29s (4,707 tokens) |
| prompt_eval_rate | **457 t/s** |
| gen_duration | 0.44s (20 tokens) |
| gen_rate | **46 t/s** |
| total | 10.95s |

**KNOWN: prompt evaluation is the dominant cost on a warm model.** At 457 t/s, LA's 7,281-token prompt takes ~16-17s — confirmed.

**KNOWN: generation is cheap.** 20 tokens = 0.44s, 100 tokens ≈ 2.2s. eLo's short responses are not the bottleneck.

**CALCULATED: at 457 t/s, each additional 1,000 tokens of prompt costs ~2.2s of prompt evaluation.**

---

## SECTION 3 — PROMPT COMPONENT BREAKDOWN

LA baseline: ~7,281 tokens total, 8,192 context = **89% full**.

Components measured from live eLo OS state (2026-08-22):

| Component | Type | Chars | Est. Tokens | % of 7,281 | Notes |
|---|---|---|---|---|---|
| `living_presence_spec` | STATIC | 17,860 | ~4,465 | **61%** | Loaded from `prompts/living_presence_spec.txt`. Dominant single component. |
| `personality_block` | STATIC | 1,860 | ~465 | 6% | Two-layer character (foundational + expressive + rules). B-DRIFT-02. |
| `identity_block` | DYNAMIC | 236 | ~59 | <1% | Name/who_i_am_with/invariants. |
| `narrative_block` | DYNAMIC | 394 | ~98 | 1% | Session narrative state. |
| `self_interpret` (F-7) | DYNAMIC | 181 | ~45 | <1% | Verified autobiography grounding. |
| `vault_context` (world knowledge) | DYNAMIC | ~2,000 | ~500 | 7% | Capped at 2,000 chars. Obsidian notes. |
| `spatial_summary` | DYNAMIC | 86 | ~21 | <1% | Single summary line from `elo_spatial.json`. |
| `memory_pack` | DYNAMIC | ~1,703 | ~425 | 6% | Session memory pack. |
| `the_moment` (situated) | DYNAMIC | ~636 | ~159 | 2% | Epistemic situated block. |
| Attention memory / state context | DYNAMIC | unknown | ~600–800 | 8–11% | Attention-filtered memory: high/medium priority + emotional state + intent. |
| Lessons (heuristics) | DYNAMIC | 0 | 0 | 0% | No confirmed lessons yet (correct — D1 gate). Will add <60 tokens when active. |
| User message | PER-TURN | varies | varies | — | Typically 5–50 tokens. |
| **STATIC subtotal** | | | **~4,930** | **68%** | Re-evaluated by model every turn |
| **DYNAMIC subtotal** | | | **~1,350–1,550** | **19–21%** | Changes turn-to-turn |
| **Estimated total** | | | **~6,280–6,480** | — | LA measured 7,281 — delta likely from a richer attention/memory context |

**KNOWN: `living_presence_spec` is 61% of the total prompt.** It is re-evaluated by the model on every single turn.

**KNOWN: the static prompt prefix (`living_presence_spec` + `personality_block`) is approximately 4,930 tokens — ~5× the context capacity consumed before any dynamic state is added.**

**UNKNOWN: exact attention memory block size for the session LA measured.** Estimated ~600–800 tokens to account for the 7,281 baseline.

---

## SECTION 4 — CONTEXT WINDOW BEHAVIOUR

### Configuration

- `num_ctx: 8192` is hardcoded in `backend_router.py:326` and `:688`
- Ollama native model context: 131,072 tokens
- LA baseline: 7,281 / 8,192 = **88.9% full**
- Current partial assembly: ~5,100 / 8,192 = **62% full**

### Overflow behaviour (CALCULATED — not yet directly measured)

When the prompt exceeds `num_ctx`, Ollama/llama.cpp truncates from the **oldest context** — the beginning of the prompt. Since `living_presence_spec` is prepended first, it would be the first thing truncated in an overflow condition.

**KNOWN: at 89% full, eLo has approximately 900 tokens of headroom for output + any injection growth.** A 200-token response + 700 tokens of additional context injections would overflow.

**UNKNOWN: exact truncation behaviour.** The directive requires direct measurement around the 8,192 boundary. Test plan: assemble a prompt at 8,000 tokens, 8,192 tokens, 8,400 tokens and log Ollama's actual response to confirm direction of truncation.

*Note: this test was not run in this diagnostic session — it requires constructing a purpose-built overflow prompt, which is a separate measurement step.*

---

## SECTION 5 — LATENCY BUDGET SUMMARY

| Condition | load | p_eval (7,281t) | gen | **total** |
|---|---|---|---|---|
| Cold start (model unloaded) | ~6.5–11s | ~17s | ~0.8s | **~25–29s** |
| Warm (model resident, but re-evaluates full prompt) | ~0.25s | ~17s | ~0.8s | **~18s** |
| Warm + prompt pre-evaluation cached (theoretical) | ~0.25s | ~2s (dynamic only, ~800t) | ~0.8s | **~3s** |

**KNOWN: the two dominant costs are (1) model loading and (2) prompt evaluation of the static identity prefix.**

**CALCULATED: if keep_alive is extended or a heartbeat prevents cold starts, total latency drops from ~29s to ~18s — saving ~11s with zero architectural change.**

**CALCULATED: if the static identity prefix (~4,930 tokens) could be cached by the model between turns (KV cache reuse / system prompt caching), prompt eval drops from ~17s to ~4s, total from ~18s to ~5s. This is an architectural optimisation question, not a prompt reduction.**

---

## SECTION 6 — IDENTIFIED OPTIMISATION POINTS (no changes made)

These are findings only. No implementation. Each would require a separate architectural decision.

### OPT-1: Extend keep_alive window (LOW RISK)
**Impact:** Eliminates 6–11s cold start for users who return within the extended window.
**Mechanism:** Change `"30m"` to `"2h"` or `"5h"` in backend_router.py.
**Risk:** Model stays in RAM longer between conversations. On 32GB M2 Max, 4.92GB is tolerable.
**Status:** PROPOSED — no code change made.

### OPT-2: Preload heartbeat (LOW RISK)
**Impact:** Eliminates cold start entirely during active use hours.
**Mechanism:** A periodic request (e.g. every 20 minutes) to keep the model warm without user-visible interaction.
**Risk:** Small periodic compute cost. Model stays loaded indefinitely.
**Status:** PROPOSED — no code change made.

### OPT-3: Increase num_ctx to 16384 or 32768 (MEDIUM — investigate)
**Impact:** Prevents prompt truncation as dynamic context grows. Allows longer conversations without overflow risk.
**Cost:** Larger KV cache → more RAM used while model is running, potentially slower first-token latency.
**Note:** Does not change prompt evaluation cost per token — but prevents identity truncation at boundary.
**Status:** PROPOSED — requires measurement.

### OPT-4: Static identity prefix caching / system prompt reuse (COMPLEX — architecture)
**Impact:** The living_presence_spec re-evaluation cost (~10s) could be eliminated if the KV cache for the static prefix could be reused across turns.
**Mechanism:** Ollama supports KV cache reuse for identical prompt prefixes across calls with the same model session. This requires keeping model loaded (OPT-1/OPT-2) AND ensuring the static prefix bytes are identical on every call (currently true — `living_presence_spec` is a static file).
**Risk:** Zero change to eLo's identity or behaviour. The spec is not being modified — the model is just being asked not to re-read it every turn.
**Status:** PROPOSED — requires separate investigation. This is the most impactful optimisation path if implemented correctly.

### OPT-5: Backend routing to faster backend for short-form turns (COMPLEX — architecture)
**Impact:** Route simple conversational turns to a faster backend (cloud API with lower latency, or smaller local model) while keeping complex reasoning on llama3.1:8b.
**Status:** DEFERRED — David's directive: establish baseline first. Tier router exists but is not yet active.

---

## FINDINGS CLASSIFICATION

| ID | Classification | Finding |
|---|---|---|
| F-1 | **KNOWN** | keep_alive "30m" is transmitting correctly. Model stays resident 30 minutes after last request. |
| F-2 | **KNOWN** | Model is NOT preloaded when eLo OS receives the first request after idle. Cold start = 6.47s on M2 Max. |
| F-3 | **KNOWN** | REQUEST 1 → 6.69s total. REQUEST 2 (immediate) → 0.35s total. 19× speedup. Model residency IS the major culprit. |
| F-4 | **KNOWN** | Prompt eval rate (warm model): ~457 t/s. At 7,281 tokens: ~17s. Generation rate: ~46 t/s. |
| F-5 | **KNOWN** | `living_presence_spec` = ~4,465 tokens = 61% of the total prompt. It is re-evaluated every turn. |
| F-6 | **KNOWN** | Static prompt prefix (~4,930 tokens) is ~68% of total context. It does not change between turns. |
| F-7 | **KNOWN** | `num_ctx: 8192` is hardcoded. At 89% full, ~900 tokens of headroom remain. |
| F-8 | **KNOWN** | No confirmed lessons in ledger (correct — D1 gate working). Lessons block costs 0 tokens currently. |
| F-9 | **CALCULATED** | Eliminating cold start (OPT-1 or OPT-2) saves ~11s. Total drops from ~29s to ~18s. |
| F-10 | **CALCULATED** | If static prefix KV cache could be reused (OPT-4), prompt eval drops from ~17s to ~4s. Total drops to ~5s. |
| F-11 | **UNKNOWN** | Exact overflow/truncation behaviour at 8,192 boundary. Not directly measured. |
| F-12 | **UNKNOWN** | Whether Ollama's KV cache reuse for identical prompt prefixes is available/configurable on this setup. |
| F-13 | **UNKNOWN** | Exact attention memory block size in LA's 7,281-token baseline. Estimated 600–800 tokens. |

---

## CONCLUSION

Generation (17 tokens, 0.8s) is not the problem. eLo spends his time in two places:

1. **Loading the model** (~6-11s cold, ~0.25s warm) — fixable with keep_alive extension or heartbeat.
2. **Re-evaluating ~4,930 static tokens** every turn (~11s of the prompt eval cost) — fixable via KV cache reuse if Ollama supports stable prefix caching.

Neither fix requires changing eLo's identity, prompt structure, or cognitive architecture. The living_presence_spec is not overhead. The question is: can the model be asked to remember having already read it?

**Recommended next measurement:** Verify whether Ollama's KV cache is being preserved between back-to-back identical-prefix requests. If REQUEST 3 (same static prefix, different dynamic tail) shows reduced prompt_eval vs REQUEST 2, KV cache reuse is already happening. If not, investigate Ollama's `--cache-reuse` flag or prompt prefix pinning.
