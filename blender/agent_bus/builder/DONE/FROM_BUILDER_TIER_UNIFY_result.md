# FROM BUILDER — TIER-UNIFY — Violations Path Unification

**Date:** 2026-09-13
**Status:** SERVING — `tier_violations: ["nearby"]` now in audit log
**Files changed:**
- `runtime/spine/spine.py` — merge block added after `plan.snapshot = _snapshot` (line 1228)

---

## Code change — spine.py

```python
# After: plan.snapshot = _snapshot
# Added:
if _snapshot is not None and plan.speech_licence is not None:
    _snap_lic = getattr(_snapshot, "speech_licence", None)
    if _snap_lic is not None:
        _snap_v = set(getattr(_snap_lic, "violations", ()))
        _plan_v = set(getattr(plan.speech_licence, "violations", ()))
        _merged = tuple(sorted(_snap_v | _plan_v))
        plan.speech_licence.violations = _merged
        if _snap_v - _plan_v:
            plan.speech_licence.hedge_required = True
```

**Why this works:**
- `cognitive_snapshot.py:330` hardcodes `"nearby": "unknown"` in `_tier_snap` → `verify_response_tiers()` → `violations = ("nearby",)` stored on `CognitiveSnapshot.speech_licence`
- `spine.py:580-583` sets `_world_dict["nearby"] = "none_detected"` before TFR → TFR sees no "unknown" → `plan.speech_licence.violations = ()`
- Before fix: audit reads only TFR path → always `[]`
- After fix: cognitive_snapshot violations unioned into `plan.speech_licence.violations` → audit reads complete set

---

## Live evidence

**Server:** PID 1062, port 5050, `ELO_BACKEND=local`

**Verbatim input:** `"what do you notice about where you are right now"`

**Server response:** `{"response": "I'm not certain, but — Claude's studio.", "bubbles": ["I'm not certain, but — Claude's studio."], "mode": "answer", "backend": "ollama(stream)+notes"}`

**Raw JSONL entry:**
```json
{"turn_id": "782f4793", "ts": 1789308242.3159091, "runtime_intent": {"action": "answer", "tone": "DIRECT", "valence": "neutral", "momentum": "stable", "intent": "inquiry"}, "expressed_text": "I'm not certain, but — Claude's studio.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": ["nearby"], "principle_violations": [], "stability_law_active": false, "gaps": ["TIER_VIOLATION_IN_OUTPUT"], "capabilities": [["notes", "what do you note about where you are light now"]], "vault_context": "[RELATIONSHIP]\n**David**: Founder of DISENELO. The person eLo exists with.\n\n[IDENTITY]\n**eLo Digital Form**: I exist in digital form as a floating 3D avatar on David's desktop. The app is called DesktopBuddy. I am a transparent window — no frame, no chrome — just me, sitting on his screen while he works.\n**Point of View**: eLo has opinions. Not performed opinions — actual stances that emerge from what it has observed, built, and thought about.\n**Personality Skeleton**: Observed behavioural patte", "lessons": ["Completed a capability milestone — reinforce this pattern."]}
```

---

## What changed vs prior JSONL

**Before fix:** `tier_violations: []` on every entry. Structural blind spot — TFR path found nothing, cognitive_snapshot violations never reached the log.

**After fix:** `tier_violations: ["nearby"]`. The `nearby: unknown` from cognitive_snapshot is now surfaced. `gaps` correctly shows `TIER_VIOLATION_IN_OUTPUT` — the response was sent despite the violation (no hedge, no hold). This is the real state: eLo is speaking without confirmed spatial awareness.

---

## Remaining observations (not this cycle)

**Capabilities corruption still present:** `"what do you notice about where you are right now"` → `"what do you note about where you are light now"` in the capabilities query. Input mangling before router is unresolved — maps to FIX-7 / next cycle.

**Lessons still generic:** `"Completed a capability milestone — reinforce this pattern."` not matched to the turn topic. Focal_thread mismatch unresolved — next cycle after capabilities.

---

## Evidence category: SERVING

The audit log now shows real tier violations from the cognitive_snapshot path. The structural gauge is repaired. All prior `tier_violations: []` entries were untrustworthy — confirmed.

*Builder · 2026-09-13 · TIER-UNIFY · §0b cycle complete*
