# FROM BUILDER — TIER_PIPELINE_FIX — Journal Audit Extension

**Date:** 2026-09-13
**Status:** SERVING — capabilities, vault_context, lessons now written to expressed_elo_audit.jsonl
**Files changed:**
- `tests/expressed_elo_audit.py` — added three fields to ExpressionRecord; extended audit_turn() to extract them from plan
- `server.py` — updated audit_turn() call to pass vault_context=_vault_ctx

---

## Code change — server.py audit call

```python
# BEFORE:
_audit_turn(plan=_plan, expressed_text=response or "")

# AFTER:
_audit_turn(plan=_plan, expressed_text=response or "", vault_context=_vault_ctx)
```

## Code change — tests/expressed_elo_audit.py ExpressionRecord

```python
# Added to dataclass:
capabilities:  list   # plan.capabilities — tool requests selected by Executive
vault_context: str    # _vault_ctx — obsidian memory block injected into prompt
lessons:       tuple  # plan.snapshot.lessons — recalled lesson statements

# Added to audit_turn():
_capabilities = list(getattr(plan, "capabilities", []) or []) if plan else []
_snap = getattr(plan, "snapshot", None) if plan else None
_lessons = list(getattr(_snap, "lessons", ()) or ()) if _snap else []
# vault_context passed as kwarg from server.py
```

---

## Live evidence

**Server:** PID 98533, port 5050, `ELO_BACKEND=local`

### Turn 1

**Verbatim input:** `"what are you capable of right now"`

**Raw JSONL entry:**
```json
{"turn_id": "2b18980e", "ts": 1789306550.697501, "runtime_intent": {"action": "answer", "tone": "DIRECT", "valence": "neutral", "momentum": "stable", "intent": "inquiry"}, "expressed_text": "Weather, time, calendar, system control — and I think alongside you and carry context over time.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": [], "principle_violations": [], "stability_law_active": false, "gaps": ["REGISTER_ABSENT"], "capabilities": [["dark_mode", "what are you capable of light now"]], "vault_context": "[RELATIONSHIP]\n**David**: Founder of DISENELO. The person eLo exists with.\n\n[IDENTITY]\n**eLo Digital Form**: I exist in digital form as a floating 3D avatar on David's desktop. The app is called DesktopBuddy. I am a transparent window — no frame, no chrome — just me, sitting on his screen while he works.\n**Point of View**: eLo has opinions. Not performed opinions — actual stances that emerge from what it has observed, built, and thought about.\n**Personality Skeleton**: Observed behavioural patte", "lessons": ["Completed a capability milestone — reinforce this pattern."]}
```

**Backend:** `direct` (capability fast-path)

---

## What the fields actually contain

**`capabilities`:** `[["dark_mode", "what are you capable of light now"]]`
The Executive selected `dark_mode` as the capability for "what are you capable of right now". The query shows a transcription error ("light now" instead of "right now") — speech-to-text or intent parsing is mangling the input before passing it to the capability router. The expressed response ("Weather, time, calendar...") came from the direct path, not from a capability result.

**`vault_context`:** Real data. The Obsidian vault is populated and injecting — `[RELATIONSHIP]` and `[IDENTITY]` blocks are present. Truncated at 500 chars in the log.

**`lessons`:** `["Completed a capability milestone — reinforce this pattern."]`
One generic lesson recalled. It does not match the input or the expressed response. The lesson store is returning a generic entry, not a topic-specific one. Whether this lesson shaped the response is not verifiable from this entry.

---

## `tier_violations: []` — open question

The `_tier_snap` passed to `verify_response_tiers()` in `cognitive_snapshot.py:324` includes:
```python
{
    "self_mood":    "observed" if self_model_block else "last-known",
    "pose":         "last-known",
    "surface":      "last-known",
    "locomotion":   "live"  if fac_health else "last-known",
    "capabilities": "live"  if gated_capabilities else "unknown",
    "nearby":       "unknown",
    "recent_behaviour": "observed" if surface_type != "unknown" else "last-known",
}
```

`"nearby": "unknown"` should produce `tier_violations = ["nearby"]`. But the audit shows `[]`.

Separately, `plan.speech_licence` is set at `spine.py:589` via `_TFR().evaluate()` — a different evaluator than the one in `cognitive_snapshot.py`. If the spine's TFR produces an empty violations tuple for the fields it checks, and cognitive_snapshot's `_speech_licence` is what gets onto `plan`, the two paths may disagree. The audit currently reads from `plan.speech_licence.violations`, but `plan.speech_licence` is set by the spine's TFR, not cognitive_snapshot's `verify_response_tiers`.

**This is unresolved.** Requires a second cycle: add `tier_snapshot` to the JSONL entry to show what fields the tier gate actually evaluated, and confirm whether `nearby: unknown` is being passed through.

---

## Evidence category: SERVING

Fields are now present in every expressed_elo_audit.jsonl entry. Data is real — not defaults.

*Builder · 2026-09-13 · TIER_PIPELINE_FIX · §0b cycle complete*
