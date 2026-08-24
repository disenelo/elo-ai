# BUILDER CARD — BLATENCY-01: Ollama Latency Diagnostic
**Date:** 2026-08-22
**Authority:** `_intake/SOURCE_2026-08-22_DAVID_latency_diagnostic_instruction.md` (David Charles, verbatim)
**Type:** MEASUREMENT ONLY — no code changes permitted
**Lane:** Builder (terminal access, read-only observation)

---

## Objective
Establish a measured latency baseline for the current Ollama runtime. Identify where the ~29s total latency is being spent. Produce **KNOWN / MEASURED / CALCULATED / UNKNOWN** findings only. No prompt trimming, no identity changes, no architectural changes.

**David's constraint verbatim:** *"The objective is: make the existing eLo respond faster without changing what eLo is, what he knows, how he speaks, or what he can do. Any optimisation that changes expressed eLo behaviour becomes a separate architectural decision and must not be silently implemented."*

---

## What already exists (read before instrumenting)

`backend_router.py` already captures timing after every Ollama call into `_last_ollama_metrics`:
```python
{
    "load_ms":              ...,   # load_duration from Ollama API
    "prompt_eval_tokens":   ...,   # prompt_eval_count
    "prompt_eval_ms":       ...,   # prompt_eval_duration
    "gen_tokens":           ...,   # eval_count
    "gen_ms":               ...,   # eval_duration
}
```

`prompt_builder.py` captures per-section sizes into `_last_prompt_audit` after every `build()` call (card 0047 F-B).

**Start by reading these — they exist. Do not reinvent them.**

---

## Test 1: Model Residency (most likely culprit)

**Purpose:** Determine whether `keep_alive: "30m"` is actually holding the model between turns.

**Code path:** `backend_router.py:_ollama_call()` and `_ollama_stream()` both send `"keep_alive": "30m"`.

**Procedure:**
1. Restart the eLo backend fresh (no prior Ollama activity this session).
2. Send a short test message: `"Hello eLo"`.
3. Immediately after the call completes, read `_last_ollama_metrics["load_ms"]` from the backend. Record as **REQUEST 1 load_ms**.
4. Without restarting anything, send the same message again within 10 seconds.
5. Read `_last_ollama_metrics["load_ms"]` again. Record as **REQUEST 2 load_ms**.
6. Send a third time. Record as **REQUEST 3 load_ms**.

**Also check Ollama's process state between requests:**
```bash
curl -s http://localhost:11434/api/ps | python3 -m json.tool
```
This shows whether the model is currently loaded in VRAM/RAM and with what `keep_alive` setting Ollama actually received.

**Interpretation:**
- REQUEST 2 load_ms ≈ 0 → `keep_alive` working; model residency is not the problem.
- REQUEST 2 load_ms ≈ REQUEST 1 load_ms → model is unloading between requests; `keep_alive` is failing.
- REQUEST 2 load_ms ≈ 0 but REQUEST 3 load_ms ≈ REQUEST 1 → model evicted between turn 2 and 3 (OS pressure).

**Record:** load_ms for each of 3 requests in the findings table below.

---

## Test 2: Hardware Profile

**Purpose:** Capture the hardware baseline so CALCULATED estimates can be derived.

**Procedure:**
```bash
# What model is actually running?
echo "ELO_OLLAMA_MODEL=$ELO_OLLAMA_MODEL"
ollama list

# Model metadata (size, quantization, context length)
ollama show $ELO_OLLAMA_MODEL --modelfile
ollama show $ELO_OLLAMA_MODEL

# Memory and GPU state
ollama ps

# System hardware
system_profiler SPHardwareDataType | grep -E "Model|Chip|Memory|CPU"

# Check what GPU/Metal Ollama is actually using
cat ~/.ollama/logs/server.log 2>/dev/null | tail -50 | grep -E "GPU|Metal|VRAM|layers"
# or
cat ~/Library/Logs/ollama/server.log 2>/dev/null | tail -50 | grep -E "GPU|Metal|VRAM|layers"
```

**Required hardware profile fields (David's spec):**
| Field | Value |
|---|---|
| MODEL | |
| MODEL SIZE | |
| QUANTIZATION | |
| HARDWARE | |
| GPU / OFFLOAD | |
| RAM | |
| MODEL LOAD TIME (cold, ms) | |
| PROMPT TOKENS | |
| PROMPT EVAL RATE (tok/s) | |
| GENERATION TOKENS | |
| GENERATION RATE (tok/s) | |
| KEEP_ALIVE | |
| TOTAL LATENCY (ms) | |

**CALCULATED fields** (derive from MEASURED, tag as [CALCULATED]):
- Prompt eval rate (tok/s) = `prompt_eval_tokens` ÷ (`prompt_eval_ms` / 1000)
- Generation rate (tok/s) = `gen_tokens` ÷ (`gen_ms` / 1000)
- Expected eval time for 7,281 tokens at measured rate = 7281 ÷ rate

---

## Test 3: Prompt Component Breakdown

**Purpose:** Identify which sections of the assembled prompt are consuming the most tokens.

**`_last_prompt_audit` is already being populated.** Read it after one real turn.

The sections (in assembly order per `prompt_builder.py`):
1. `living_presence_spec` — `prompts/living_presence_spec.txt`
2. `personality_block` — if non-empty
3. `self_block` — if non-empty
4. `lessons` — up to 3, ≤240 chars total
5. `active_memory` (attention path) or `persistent_memory` + `world_memory` (legacy path)
6. `vault_context` — world knowledge, capped at 1200 chars
7. `executive_directive` — action + tone

**Procedure:**
1. Send a normal test turn through the real runtime (not a mock).
2. Immediately after, call the endpoint that exposes `_last_prompt_audit` (check `server.py` for `backend_health` or `/api/prompt_audit` endpoint, which card 0047 F-B may have added — **verify before assuming it exists**).
3. Alternatively, add a one-line print to the backend start script to log `_last_prompt_audit` after each call — no code change to production paths required; this is observation only and can be removed.
4. Record each section's char count and estimated token count (chars ÷ 3.5 per code comment in `prompt_builder.py:17`).

**Important:** Do NOT remove or compress any section. This is measurement only. Whether `living_presence_spec` is "large" is not the question — it is identity and not available for reduction (David's direct instruction).

**The question is:** What is static vs dynamic? What is growing each turn?

---

## Test 4: Context Window Overflow Behaviour

**Purpose:** Know what Ollama actually does at and beyond the 8,192 token limit.

**Current state:** ~7,281 tokens assembled (~89% of context).

**Procedure:**
1. Log the full assembled system prompt (char count and estimated tokens) going into a real Ollama call.
2. Compare the estimated token count against the `prompt_eval_count` Ollama reports in `_last_ollama_metrics["prompt_eval_tokens"]`. If these differ significantly, Ollama may be truncating or the 3.5 chars/tok estimate is off for this model.
3. Identify which direction truncation happens if it occurs: does Ollama drop from the front (losing identity), the back (losing memory/conversation), or does it error?
4. Do NOT deliberately overflow in production. Observe behaviour via the reported token counts only at this stage.

**Record:**
- Assembled prompt chars (from `_last_prompt_audit`)
- Estimated tokens (chars ÷ 3.5)
- Ollama's `prompt_eval_count` (actual tokens evaluated)
- Delta between estimated and reported — large delta = [UNKNOWN] until investigated

---

## Test 5: `.env` / Config Verification

**Purpose:** Confirm the model actually running matches the standing fact.

**Standing fact (CLAUDE.md):** `ELO_OLLAMA_MODEL=llama3.1:8b`
**Code default:** `os.environ.get("ELO_OLLAMA_MODEL", "mistral")` — if env var is unset, the code silently uses `mistral`.

**Procedure:**
```bash
# Check what's in .env
grep -E "OLLAMA|ollama" /path/to/elo-ai/.env

# Check what model is actually loaded
ollama ps
```

If `ELO_OLLAMA_MODEL` is not set in `.env` and the session doesn't export it, the backend is calling `mistral` not `llama3.1:8b`. Different models have different context processing speeds. This is a **KNOWN** if confirmed.

---

## Findings Table

Builder populates this table. Every row must carry a tag.

| # | Finding | Tag | Value / Evidence |
|---|---|---|---|
| H-1 | Model actually running | MEASURED | |
| H-2 | Model quantization | MEASURED | |
| H-3 | Hardware (chip / GPU) | KNOWN | |
| H-4 | GPU offload layers | MEASURED | |
| H-5 | `keep_alive` in code | KNOWN | `"30m"` (backend_router.py:325, :687) |
| H-6 | `keep_alive` Ollama received | MEASURED | |
| R-1 | Request 1 load_ms (cold) | MEASURED | |
| R-2 | Request 2 load_ms (warm) | MEASURED | |
| R-3 | Request 3 load_ms | MEASURED | |
| R-4 | Model resident between R1→R2? | MEASURED | Y/N from `/api/ps` |
| P-1 | Total prompt tokens (Ollama reported) | MEASURED | |
| P-2 | `living_presence_spec` chars / est. tokens | MEASURED | |
| P-3 | `personality_block` chars / est. tokens | MEASURED | |
| P-4 | `self_block` chars / est. tokens | MEASURED | |
| P-5 | `lessons` chars / est. tokens | MEASURED | |
| P-6 | `active_memory` or `persistent_memory` chars / est. tokens | MEASURED | |
| P-7 | `vault_context` chars / est. tokens | MEASURED | |
| P-8 | `executive_directive` chars / est. tokens | MEASURED | |
| P-9 | Static sections (spec + personality + self) % of total | CALCULATED | |
| P-10 | Dynamic sections (memory + lessons + exec) % of total | CALCULATED | |
| C-1 | Prompt eval rate (tok/s) | CALCULATED | |
| C-2 | Generation rate (tok/s) | CALCULATED | |
| C-3 | Expected eval time at measured rate for P-1 tokens | CALCULATED | |
| C-4 | Overflow headroom remaining (8192 − P-1) | CALCULATED | |
| U-1 | Why load_ms ≈ non-zero on R-2 if keep_alive set | UNKNOWN until measured | |
| U-2 | Actual truncation direction if tokens > 8192 | UNKNOWN until measured | |
| U-3 | Whether `_last_prompt_audit` endpoint exists or needs observation | UNKNOWN — check first | |

---

## Outputs Required

Builder produces ONE file: `docs/architecture/findings/LATENCY_DIAGNOSTIC_2026-08-22.md`

Contents:
1. Hardware profile table (filled)
2. Findings table (filled)
3. Three proposed optimisation points — tag each as [ZERO_IDENTITY_IMPACT] or [REQUIRES_DAVID_RULING]
4. Dominant culprit call: model residency / context processing / both / other (with evidence)

**No changes to any production file.** No `.py` edits. This card is complete when the findings file exists with all MEASURED rows populated.

---

## What this card does NOT authorise

- Trimming `living_presence_spec` or any identity section
- Changing `keep_alive` value (even if it appears to be failing — report the failure, don't fix it without a ruling)
- Changing `num_ctx`
- Adding Llama to the live path
- Modifying Executive, memory, or prompt assembly logic
- Changing backend routing order

Any proposed optimisation goes into the findings file as a proposal only. David decides.

---

## CLOSED — 2026-08-23

**Status:** ✅ COMPLETE

**Findings file produced:** `docs/architecture/findings/LATENCY_DIAGNOSTIC_2026-08-22.md`

**Dominant culprit:** PROMPT SIZE + PROMPT EVALUATION TIME. At 482 tok/s prompt eval rate × 7,544–8,800 estimated tokens = **15–19s per turn**. Model load, generation, and Python overhead are minor contributors.

**Root source:** `living_presence_spec` = 17,860 chars / 5,103 est. tokens / 67.6% of total prompt. Static every turn. Re-evaluated from scratch every request.

**Key measurements:**
- R-1 (cold): load_ms = 3,823ms
- R-2/R-3 (warm): load_ms ≈ 170-180ms — keep_alive working
- Prompt eval rate (large prompt): 482 tok/s
- Generation rate: 49 tok/s
- Overflow headroom: 648 tokens remaining (~9%)

**Three optimisation proposals (findings file §4):**
- O-1: Prefix caching (`num_keep`) — [REQUIRES_DAVID_RULING]
- O-2: Cap `relationship_graph` more aggressively — [ZERO_IDENTITY_IMPACT]
- O-3: Measure actual token count via `/api/tokenize` — [ZERO_IDENTITY_IMPACT]

**No production files modified.** David decides on all proposals.
