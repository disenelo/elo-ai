# WO-VAULT-WRITE-INVESTIGATE-001 — Investigation Report
**Filed:** 2026-09-28
**Filed by:** Builder 1
**Status:** INVESTIGATION COMPLETE — root cause confirmed, fix landed (commit in this PR)

---

## Correction to initial report (2026-09-28)

The initial report (commit f9680d0) stated the substitution was caused by vault_write calling mock_backend with `mode="celebrate"`. This was **incorrect**. Deeper shadow-log analysis disproved it:

- `executed_action: ""` on ALL substituted shadow entries — vault_write did NOT fire for these queries
- `backend_used: "ollama(stream)"` on ALL substituted entries — the main LLM route was Ollama, not mock

The actual root cause is the **voice_rewrite register-absent trigger** (WO-REGISTER-ABSENT-001), confirmed below.

---

## Root Cause: CONFIRMED (corrected)

**The substitution is caused by `voice_rewrite._needs_rewrite()` firing on substantive Ollama responses that contain no eLo register markers. When the response is > 80 chars and contains none of `_AUDIT_REGISTER_MARKERS` (nah, seen, man, look, yeah, right, proper, low-key, vibe, innit, init, real talk), `_needs_rewrite()` returns True and voice_rewrite calls the backend LLM to rewrite the response. The rewrite LLM collapses the factual content to a short eLo-style affirmation. No content-preservation length guard existed to catch this collapse.**

---

## Mechanism — step by step

1. User sends query (engineering question, visual identity, self-description)
2. Ollama/qwen2.5-coder:14b generates correct, factual response → captured as `elo_raw_gen` at **server.py:5463** (`_elo_raw = response`)
3. `_elo_raw` is correct. `executed_action = ""` (vault_write did not fire)
4. **server.py:6163–6192**: voice_rewrite block runs
5. **voice_rewrite.py:121–123**: `_needs_rewrite()` checks register-absent fallback:
   - `len(response) > 80` → True (engineering/factual responses are long)
   - `not any(m in response for m in _AUDIT_REGISTER_MARKERS)` → True (formal Ollama responses have no street markers)
   - → `_needs_rewrite()` returns True
6. `voice_rewrite()` calls `_vr_llm(msgs)` → `router_route(action="voice_rewrite", tier=0)`
7. The rewrite LLM (Groq via lore-drift → `_mock_fallback`, or Ollama producing short eLo-style output) returns a very short string: "More of that.", "The alive feeling is the signal.", etc.
8. **voice_rewrite.py:236**: No content-preservation guard existed — the short rewrite passed the 3× length check and was returned
9. `response` = short pool-like string. `_elo_raw` = correct Ollama output
10. **server.py:6451**: shadow capture logs `elo_raw_gen=_elo_raw` (correct), `elo_final=response` (pool string), `delta_cause="unknown"` (no voice_rewrite tagging existed)

The pool strings appearing in elo_final are either:
- Produced by Groq's mock fallback when Groq detects lore-drift on the voice_rewrite inner call
- OR produced by Ollama itself generating short affirmational eLo-style text for the constrained rewrite prompt

They are NOT from vault_write → mock_backend. vault_write played no role.

---

## Why the pool strings match `_CELEBRATE_POOL`

`_CELEBRATE_POOL` strings are short, eLo-voice affirmations specifically crafted to sound like eLo. When any backend is asked to "Speak as eLo. Output only eLo's words" with a constrained 2-sentence max, these same types of strings emerge — they're the natural output of the voice constraint, not specifically from mock_backend's celebrate pool.

---

## Evidence

### Shadow log entries (all substituted)

| Query | `elo_raw_gen` (truncated) | `elo_final` | `executed_action` |
|-------|--------------------------|-------------|-------------------|
| torque options | "If the shoulder joint can't produce enough torque, eLo has several options..." | "More of that." | "" |
| idle sounds | "My primary sound is a soft low-frequency hum..." | "The alive feeling is the signal." | "" |
| my team doesn't understand | "I understand that it's frustrating when your team doesn't see the value in eLo. Let's work through..." | "Hold that. Move from there." | "" |
| list shell constraints | "The design constraints for eLo's outer shell include: 1. **Material Selection**..." | "That's worth staying with — it's real." | "" |
| read JSON config | "The configuration you provided is a JSON object with three key-value pairs: 1. `temperature`..." | "The alive feeling is the signal." | "" |

All: `backend_used: "ollama(stream)"`, `executed_action: ""`, `delta_cause: "unknown"`

### Why the 80-char register-absent check fires on good responses

Engineering and factual responses from qwen2.5-coder:14b are typically:
- > 80 chars ✓
- Formal/technical register — NO nah/seen/man/look/yeah/right/proper/etc. ✓
- → `_needs_rewrite()` always True for these

### Why NOT substituted: "You've sent an HTTP POST request to the \"/chat\" endpoint."

This response is 53 chars — below the 80-char register-absent threshold. `_needs_rewrite()` returns False. Passes through unchanged. (This is why COG-004 C16 still FAILS at the generation layer — the response is too short and lacks detail, not because it's being substituted.)

---

## Fix landed

Three changes in this commit:

### 1. voice_rewrite.py — content-preservation guard
**`runtime/voice_rewrite.py:239–242`**:
```python
if stripped_rewrite:
    # Content-preservation guard: if the rewrite collapsed a substantial
    # factual response to < 25% of its length, the LLM dropped the facts.
    if len(cleaned) > 100 and len(stripped_rewrite) < len(cleaned) * 0.25:
        pass  # fall through to cleaned / candidate
    else:
        return stripped_rewrite
```
Prevents a 400-char engineering answer from being replaced with a 13-char pool string.

### 2. shadow_capture.py — "voice_rewrite" delta cause
**`runtime/shadow_capture.py:86`**:
```python
_VALID_DELTA_CAUSES = ("none", "style", "verification", "l3_override", "voice_rewrite", "unknown")
```
Enables voice_rewrite substitutions to be tagged in the shadow log.

### 3. server.py — track voice_rewrite delta, pass to shadow capture
**`server.py:6163–6192`**: `_vr_changed = False`, `_pre_vr_response = response` before voice_rewrite call; `_vr_changed = response != _pre_vr_response` after.
**`server.py:6451`**: `delta_cause="voice_rewrite" if _vr_changed else None` passed to `record_turn()`.

---

## Why `delta_cause` was "unknown" (Option C resolved)

`runtime/shadow_capture.py:89` — `_derive_delta_cause()` compares raw_gen to final. It had no case for voice_rewrite substitutions, and server.py passed no `delta_cause` hint. Now server.py tracks `_vr_changed` and passes `delta_cause="voice_rewrite"` when the rewrite changed the response.

---

## Blocks resolved by fix

- WO-CAP-COG-008 (engineering capability) — content-preservation guard prevents collapse
- WO-CAP-COG-010 (visual identity) — same
- WO-CAP-COG-012 (self-description / sound) — same
- WO-CAP-COG-017 (emotional support / awareness) — same

All four should reach PASS once the content-preservation guard prevents elo_final from being replaced by a collapsed voice_rewrite output.

---

## Files and lines changed

| File | Line(s) | Change |
|------|---------|--------|
| `runtime/voice_rewrite.py` | 239–246 | Content-preservation guard added |
| `runtime/shadow_capture.py` | 86 | "voice_rewrite" added to `_VALID_DELTA_CAUSES` |
| `server.py` | 6163–6165, 6192, 6457 | Track `_vr_changed`, pass `delta_cause` to shadow capture |

---

Builder 1 · 2026-09-28 (corrected)
