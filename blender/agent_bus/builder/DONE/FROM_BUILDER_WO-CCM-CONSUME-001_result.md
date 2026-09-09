# FROM_BUILDER — WO-CCM-CONSUME-001
**Status:** DONE — investigation complete; trace documented; AT-3 answered YES with evidence
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a)

---

## Intent

Prove CCM dims reach Executive decision. Identify every consumer. Answer YES/NO: does CCM actually affect any decision eLo makes?

---

## AT-1 — `ccm_enricher.enrich()` on 3 real inputs

### Input 1: casual / street
```
"bruv wagwan that was bare peak man allow it seen safe fam"
```
Scored dims (27 total, 9 non-null):
```
intent: conversation
relationship: creator
street_terminology: [bruv, wagwan, safe, allow it, fam, bare, peak, seen, man]
street_language: 1.0
cultural_references: [london_street]
conversation_rhythm: medium
vocabulary_preferences: [street]
response_pacing: normal
social_expectations: greeting
```

### Input 2: building / technical
```
"implement the WKG faculty trace from spine to the executive decision dict"
```
Scored dims (27 total, 6 non-null):
```
intent: conversation
relationship: creator
cultural_references: [film]
conversation_rhythm: medium
vocabulary_preferences: [simple]
response_pacing: normal
```
No street_language. No emotional signals.

### Input 3: creative / curious
```
"I wonder what if we built something that could actually feel real, curious about how curiosity itself works"
```
Scored dims (27 total, 12 non-null):
```
intent: question
relationship: creator
conversation_energy: reflective
humour_style: absurd
creative_philosophy: present
conversation_rhythm: medium
vocabulary_preferences: [simple]
tone_shifts: present
response_pacing: normal
social_expectations: greeting
context_transitions: present
curiosity: present
```

---

## AT-2 — ccm_context call chain trace

**Full path: enricher → spine plan → exec_decision → prompt_builder**

1. `runtime/spine/spine.py:1010-1011` — `_ccm_context = _ccm_enrich(raw, language, None)` — runs every turn
2. `spine.py:1055` — passed to `executive_faculty(ccm_context=_ccm_context, ...)`
3. `spine.py:1120` — passed to `planetary_kernel(ccm_context=_ccm_context, ...)`
4. `spine.py:1695` — `plan.ccm_context = ccm_context or {}`
5. `server.py:2971` — `"ccm_context": getattr(_plan, "ccm_context", {})` — in exec_decision dict
6. `runtime/prompt_builder.py:579` — `_ccm = exec_decision.get("ccm_context") or {}` — consumed here

---

## AT-3 — Does CCM actually affect any decision eLo makes? **YES**

**At what layer?** Not at Executive layer. At Prompt layer.

### Executive layer: NO

```python
grep "ccm" runtime/executive.py → 0 results
```

`executive.py` receives `ccm_context` as a parameter (spine passes it in) but makes zero decisions based on it. The Executive decides action, tone_mode, agency_level, relationship_mode, vessel_phase — none of these are shaped by CCM dims.

**This is not a bug.** FREEZE_V1_LOCK governs executive.py. The Executive was spec'd to decide from attention + affective state + cognitive state, not from CCM signals directly. CCM is a context enricher for the prompt layer.

### Prompt layer: YES — three consumption points

**Point 1 — Generic context injection (`prompt_builder.py:578-583`):**
```python
_ccm = exec_decision.get("ccm_context") or {}
_ccm_items = [f"{k}: {v}" for k, v in list(_ccm.items())[:4] if v]
if _ccm_items:
    directive_lines.append("Context enrichment: " + "; ".join(_ccm_items))
```
Top 4 non-null CCM dims are injected as a context enrichment directive. For the casual/street input above, this would inject: `"Context enrichment: intent: conversation; relationship: creator; street_terminology: ['bruv', ...]; street_language: 1.0"`.

**Point 2 — Creative philosophy (`prompt_builder.py:587`):**
```python
_creative_phil = (_ccm or {}).get("creative_philosophy")
```
When `creative_philosophy: present`, a creativity directive fires.

**Point 3 — Street language register (`prompt_builder.py:594-607`):**
```python
_street = float((_ccm or {}).get("street_language", 0.0) or 0.0)
if _street >= 0.65:
    directive_lines.append("Voice register: South/West London...")
elif _street >= 0.35:
    directive_lines.append("Voice register: contemporary idiom...")
```
`street_language` float directly gates eLo's linguistic register instruction. This was broken (always 0.0) before WO-ELO-VOICE-IDENTITY-001 fixed `_STREET_TERMS`. Now live.

---

## Integration status summary

| CCM dim | Scored? | Reaches prompt_builder? | Affects decision? |
|---|---|---|---|
| street_language (float) | ✅ now live (WO-ELO-VOICE-IDENTITY-001) | ✅ via exec_decision.ccm_context | ✅ gates voice register directive |
| creative_philosophy | ✅ (when philosophy signals present) | ✅ | ✅ fires creativity directive |
| intent | ✅ every turn | ✅ (top-4 dump) | ⚠️ injected as context text only |
| relationship | ✅ always "creator" | ✅ (top-4 dump) | ⚠️ injected as context text only |
| conversation_energy | ✅ sometimes | ✅ (top-4 dump, position 4) | ⚠️ injected as context text only |
| curiosity | ✅ when present | ✅ (top-4 dump) | ⚠️ injected as context text only |
| cultural_references | ✅ when detected | ✅ | ⚠️ injected as context text only — no dedicated consumer |
| 12 remaining dims | Scored but not individually consumed | — | No dedicated consumer |

**Gaps flagged to Board (not Builder's scope to fix without spec):**
- The generic top-4 CCM dump is a weak consumer — it passes raw field names and values to the LLM, which may or may not act on them. Individual dims like `conversation_rhythm`, `response_pacing`, `tone_shifts`, `curiosity` deserve dedicated instructions (as `street_language` and `creative_philosophy` have).
- WO-CCM-SPINE-19-001 (ratified 19 dims) addresses this gap — it is in the INBOX as a separate WO.
- `executive.py` could consume `conversation_rhythm` or `response_pacing` to set `turn_mode`, but this is gated by FREEZE_V1_LOCK. Board must spec the shim.

---

## INTENT PROOF

The WO intent: "Prove CCM dims reach Executive decision."

**Partial YES:** CCM dims reach exec_decision (board-visible). They are consumed by prompt_builder in 3 specific ways (street_language, creative_philosophy, top-4 context dump). The Executive itself does not consume CCM — this is by design given FREEZE_V1_LOCK.

The 19-dim ratification spec (WO-CCM-SPINE-19-001) will add more dedicated consumers per dim.
