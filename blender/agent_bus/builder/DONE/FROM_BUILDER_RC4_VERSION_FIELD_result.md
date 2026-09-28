# FROM BUILDER — RC-4 — Significance Vector Version Field

**Date:** 2026-09-13
**WO:** WO-ROOT-CAUSE-FIX — RC-4
**Status:** SERVING — `version: "2.0.0"` present in significance record
**Files changed:**
- `memory/significance_engine.py` — `scores["version"] = "2.0.0"` added before `return scores`

---

## Code change

```python
# Added before `return scores` in significance_engine.evaluate():
# RC-4 2026-09-13: ADR-007 §3 — a vector without a version is invalid data.
scores["version"] = "2.0.0"
```

Version field now present on every dict returned by `evaluate()`. Flows into:
- `profile` in the `decision` dict returned by `journal_router.route()`
- `"profile"` written to `self/state/last_significance.json` each turn

---

## Live evidence

**Server:** PID 3964, port 5050, `ELO_BACKEND=local`
**Note:** pyc cache cleared before restart — previous server run had stale bytecode, version field was MISSING. Cleared and restarted.

**Verbatim input:** `"you calm today"`

**Raw JSONL entry (expressed_elo_audit.jsonl):**
```json
{"turn_id": "32660ddf", "ts": 1789311808.855892, "runtime_intent": {"action": "celebrate", "tone": "JOYFUL", "valence": "positive_low", "momentum": "stable", "intent": "conversation"}, "expressed_text": "That's okay.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": ["nearby"], "principle_violations": [], "stability_law_active": false, "gaps": ["TIER_VIOLATION_IN_OUTPUT"], "capabilities": [["calendar", "you calm today"]], "vault_context": "[RELATIONSHIP]\n**David**: Founder of DISENELO. The person eLo exists with.\n\n[IDENTITY]\n**eLo Digital Form**: I exist in digital form as a floating 3D avatar on David's desktop. The app is called DesktopBuddy. I am a transparent window — no frame, no chrome — just me, sitting on his screen while he works.\n**Point of View**: eLo has opinions. Not performed opinions — actual stances that emerge from what it has observed, built, and thought about.\n**Personality Skeleton**: Observed behavioural patte", "lessons": ["Completed a capability milestone — reinforce this pattern."]}
```

**Significance record — `self/state/last_significance.json` (this turn's profile):**
```
version:  2.0.0
overall:  0.1344
reward:   0.0
embodiment: 0.0
```

`version: "2.0.0"` is present. ADR-007 §3 satisfied.

---

## What is still 0.0

`reward: 0.0` and `embodiment: 0.0` — expected. `_w1_outcome` is still a plain string at `server.py:4828`. RC-1 fixes this. Until then, `outcome=None` reaches `evaluate()` → all outcome dims zero → reward zero. RC-4 closes the version validity violation only; the significance values remain inert pending RC-1.

---

## Evidence category: SERVING

`version: "2.0.0"` confirmed in significance record on a real server turn.

*Builder · 2026-09-13 · RC-4 · §0b cycle complete*
