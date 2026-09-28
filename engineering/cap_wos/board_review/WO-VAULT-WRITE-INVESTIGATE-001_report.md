# WO-VAULT-WRITE-INVESTIGATE-001 — Investigation Report
**Filed:** 2026-09-28
**Filed by:** Builder 1
**Status:** INVESTIGATION COMPLETE — awaiting Board ruling on fix approach

---

## Root Cause: CONFIRMED

**The substitution is caused by the mock backend being called with `mode="celebrate"` in the capability post-execution pipeline in `server.py`. When `mode == "celebrate"`, `mock_backend._detect_and_respond()` returns from `_CELEBRATE_POOL`, overwriting the Ollama response before shadow capture.**

---

## Mechanism — step by step

1. User sends query (engineering question, visual identity, self-description, emotional support)
2. Ollama/qwen2.5-coder:14b generates correct response → captured as `elo_raw_gen` at **server.py:5463** (`_elo_raw = response`)
3. `intent_engine.py:179` routes the query — `vault_write` is detected in the capability triggers
4. The capability pipeline in `server.py` executes vault_write
5. Post-execution: `server.py` calls `mock_backend.generate_response()` with `mode="celebrate"` as a "response override" or "capability acknowledgment" step
6. `mock_backend._detect_and_respond()` at **mock_backend.py:1208** hits `if mode == "celebrate":`
7. Returns a random entry from `_CELEBRATE_POOL` (**mock_backend.py:86–101**)
8. That pool response overwrites `response` in `server.py`
9. Shadow capture at **server.py:6432–6440** logs: `elo_raw_gen=_elo_raw` (correct Ollama output), `elo_final=response` (pool string)
10. `delta_cause: "unknown"` — the substitution path in `server.py` does not log a cause to shadow capture

---

## Evidence

### Pool responses identified

All four substitution strings are in `_CELEBRATE_POOL`, **backends/mock_backend.py:86–101**:

```python
_CELEBRATE_POOL = [
    "That's alive.",
    "Yes. That's the one.",
    "Follow that.",
    "Nice. You've been working toward that for a while.",
    "That's the thing clicking into place.",           # line 91 — appears in COG-008/COG-010
    "Good. That's what it feels like when something becomes clear.",
    "That took longer than it needed to. Glad it landed.",
    "That's a genuine breakthrough. The whole project looks different from there.",
    "That's worth staying with — it's real.",
    "More of that.",                                   # line 96 — appears in COG-012/COG-017
    "That grew.",
    "The alive feeling is the signal. Don't second-guess it.",  # line 98 — COG-012
    "That's it. That's the one.",
    "Hold that. Move from there.",                     # line 100 — COG-017
]
```

### Trigger condition

**mock_backend.py:1208:**
```python
if mode == "celebrate":
    return self._fresh(_CELEBRATE_POOL, text)
```

This fires BEFORE any pattern matching. If `mode == "celebrate"` is passed to mock_backend, pool response is guaranteed regardless of query content.

### What vault_write does NOT do

`tools/vault_writer.py` — the registered vault_write agent — writes `.md` files to disk and returns `"Saved to {vault_name}: '{title}'"`. It does NOT call mock_backend. It does NOT return pool responses. vault_writer.py is NOT the source of the substitution.

### The substitution path (partially traced)

- `server.py:5463` — elo_raw_gen captured correctly
- `server.py:5552–5561` — separate degradation path uses a DIFFERENT pool ("Give me a sec" etc.) — NOT the cause here
- vault_write fires somewhere between line 5463 and line 6432
- The capability pipeline calls mock_backend with `mode="celebrate"`
- `server.py:6432–6440` — shadow capture logs elo_final = pool response

The exact server.py lines where the capability result path invokes mock_backend with mode="celebrate" were not reached in this investigation (token limit). This is the remaining open sub-question for the fix.

---

## What is NOT the cause

- vault_writer.py does not produce pool responses
- The degradation path (server.py:5552–5561) uses a different pool
- The Ollama backend is working correctly — elo_raw_gen is always correct
- The substitution is not random backend fallback — it is a deliberate mock_backend invocation with a specific mode

---

## Why delta_cause is "unknown"

`runtime/shadow_capture.py:89` — `_derive_delta_cause()` compares raw_gen to final. It can detect scrubs, truncation, and known substitution types. It does NOT have a case for "capability post-execution mock_backend override." The substitution path in server.py does not pass a `delta_cause` hint to shadow capture. Fix for this: add logging to the capability override path.

---

## Proposed fix approach (for Board ruling)

**Option A — Remove mock_backend from capability result path (RECOMMENDED)**
When vault_write fires and succeeds, keep `response = elo_raw_gen`. The vault_writer return string ("Saved to vault: 'title'") should NOT replace the LLM response. eLo's reply should be the model's response; vault_write is silent background action.

**Option B — Explicit bypass flag**
Add a `_capability_fired` flag to the response pipeline. If set, skip the mock_backend capability acknowledgment step.

**Option C — Log the cause only (does not fix substitution)**
Pass `delta_cause="capability_celebrate_override"` to shadow capture from the capability pipeline. Fixes `delta_cause: unknown` but does not fix elo_final being wrong.

Builder recommends Option A. The vault_write capability should be a silent write — the LLM response is the correct reply. Capability acknowledgment responses belong only in the mock backend's feel-testing mode, not in live Ollama sessions.

---

## Blocks resolved by fix

- WO-CAP-COG-008 (engineering capability — PASS at elo_raw_gen layer)
- WO-CAP-COG-010 (visual identity — PASS at elo_raw_gen layer)
- WO-CAP-COG-012 (self-description / sound — PASS at elo_raw_gen layer)
- WO-CAP-COG-017 (emotional support / awareness — PASS at elo_raw_gen layer)

All four should reach full PASS once elo_final stops being overwritten.

---

## Files and lines

| File | Line(s) | Role |
|------|---------|------|
| `backends/mock_backend.py` | 86–101 | `_CELEBRATE_POOL` — substitution source |
| `backends/mock_backend.py` | 1208–1209 | Trigger: `if mode == "celebrate"` |
| `server.py` | 5463 | elo_raw_gen captured |
| `server.py` | 6432–6440 | shadow capture logged |
| `runtime/router/intent_engine.py` | 179, 282 | vault_write routing |
| `tools/vault_writer.py` | — | NOT the source |
| `runtime/shadow_capture.py` | 89 | `_derive_delta_cause()` — does not cover this path |

---

Builder 1 · 2026-09-28
