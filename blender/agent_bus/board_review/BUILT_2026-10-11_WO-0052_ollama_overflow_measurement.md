# Board Review — 0052: Ollama Overflow Measurement
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Measure-only. No prompt changes, no SP_MAX changes, no num_ctx changes, no truncation guards
added. All modifications prohibited per card 0052 §3. Evidence captured via direct Ollama API
calls (not via the eLo server, which was not started this session).

---

## M1 — Does the live prompt ever actually exceed 8,192 tokens?

**Status: UNKNOWN from available log data.**

`data/backend_health_history.jsonl` (262 rows, all from 2026-10-11) logs only:
`{_ts, trigger, prompt_eval_ms, rerouted_to}`. All 262 rows have `trigger: "4s_rule"` and
`rerouted_to: "groq"` — Ollama timed out consistently, so `prompt_eval_count` was never
captured (Step 1 instrumentation in `backend_router.py:832-835` logs to the logger, not to
the JSONL file).

The 9,000ms `prompt_eval_ms` on rerouted turns is consistent with the full system prompt
(~3,714 tokens post SP_MAX truncation) being evaluated slowly before the 4s threshold fires.
Whether 8,192 was actually exceeded by total context (system + conversation history) is not
measurable from current logs.

**What would settle it:** add `prompt_eval_count` to the JSONL append in
`backend_router.py:114` at the `4s_rule` branch, or capture `_last_ollama_metrics` on
reroute. Separate card if board decides to act.

---

## M2 — What does Ollama do when num_ctx is exceeded?

**Status: MEASURED via scratch call.**

Scratch call: `qwen2.5-coder:14b`, `num_ctx=512`, system prompt ~800 tokens.

| Field | Value |
|---|---|
| HTTP status | 200 OK |
| `done_reason` | `"stop"` |
| `prompt_eval_count` | 258 (not 800+) |
| Response content | Correct (model answered accurately) |
| Any error/warning | None |

**Ollama truncates silently and continues.** No error, no flag, no indication in the response.

---

## M3 — Which block is lost first (from observed behaviour)?

**Status: MEASURED. Finding: Ollama keeps the END, cuts the FRONT.**

Scratch call: `qwen2.5-coder:14b`, `num_ctx=150`, system prompt:
`XBZK7913start` + [500 "word " repetitions] + `QMVP4428end`. Total: ~520 tokens.

| Question | Answer returned | Conclusion |
|---|---|---|
| "What is the START code?" | `"XB"` (partial — start barely included or cut) | START is at risk |
| "What is the END code?" | `"QMVP4428"` (exact — end fully present) | END survives |

**Ollama truncates from the FRONT (oldest content), keeping the END of the system prompt.**

---

## M4 — Is it silent?

**Status: YES — completely silent.**

- HTTP response: 200 OK, `done_reason: stop`
- No `truncated` or `overflow` field in the response body
- `prompt_eval_count` is the ONLY observable indicator (it will be lower than the full token count)
- Our code does NOT check `prompt_eval_count` for shortfall; no downstream warning is emitted

**Consequence for eLo:** With the current assembly order:

```
Block 1: voice_register (~3,957 chars) — assembled FIRST
Block 2: living_presence_spec (~16,390 chars) — assembled SECOND
...
```

After SP_MAX=12,000 char truncation:
- voice_register (all 3,957 chars) + first 8,043 chars of living_presence_spec survive
- All other blocks (identity_anchor, directive, memory) are cut by SP_MAX before Ollama sees them

If Ollama then truncates for num_ctx overflow (system prompt + history > 8,192 tokens):
- It cuts from the FRONT → voice_register is the first to go
- The tail of living_presence_spec (end of character DNA / voice spec) survives

**This means the OLDEST assembled blocks (identity register, voice register) are the first
to disappear at overflow, with no warning, no log line, and no downstream indicator.**

This is the M4 finding the card asked for. No fix is applied here.

---

## M5 — Headroom trend

**Status: UNKNOWN from available log data.**

Token counts are not persisted to any JSONL file. `prompt_eval_ms` shows 9,000ms consistently
(all rerouted), but not the token counts that would establish a trend. The card's earlier
figures (7,281 → 7,477 tokens in ~2 days) are from a prior measurement session not reflected
in current logs.

---

## Summary table

| # | Question | Status | Finding |
|---|---|---|---|
| M1 | Does prompt ever exceed 8,192 tokens? | ⚠️ UNKNOWN | Rerouted every turn; token count not logged to JSONL |
| M2 | What does Ollama do at overflow? | ✅ MEASURED | HTTP 200, done_reason=stop, silent truncation |
| M3 | Which block dies first? | ✅ MEASURED | **FRONT** (voice_register first, living_presence_spec end survives) |
| M4 | Is it silent? | ✅ MEASURED | **YES — completely silent. No error, no flag, no log.** |
| M5 | Headroom trend | ⚠️ UNKNOWN | Token counts not in JSONL; cannot establish trend |

---

## Board decisions required (per card 0052 — measurement only, fixes forbidden here)

None. Evidence captured. The M4 finding (silent truncation, front-first, starts with
voice_register) is the one that matters — independent of direction as the card stated.

If the board wishes to act on this evidence:
- Add `prompt_eval_count` to JSONL logging to make M1 and M5 measurable
- SP_MAX raise and smart truncation are in the 0031 board review (not this card)
- Any prompt assembly changes require a separate authorized card

*Builder 1 · 2026-10-11*
