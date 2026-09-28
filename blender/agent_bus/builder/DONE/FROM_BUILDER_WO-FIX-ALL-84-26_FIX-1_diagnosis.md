# FROM BUILDER — WO-FIX-ALL-84-26 — FIX-1 REGISTER_ABSENT — DIAGNOSIS

**Date:** 2026-09-11
**Status:** DIAGNOSED — not a code gap, model capacity issue
**Source:** prompt audit from `blender/backend_health.json` (written on every live turn)

---

## Diagnosis result

Voice register block **IS present** in the assembled system prompt on every turn.

Evidence from `backend_health.json` prompt audit (last live server turn):

| Block | Chars | % tokens |
|---|---|---|
| voice_register | 2595 | 7.3% |
| living_presence_spec | 21746 | 61.6% |
| identity_anchor | 328 | 0.9% |
| ... (7 more blocks) | ... | ... |

- Total assembled chars: 35323
- Identity status: INTACT
- Identity missing blocks: []
- `identity_integrity.check_identity_minimum()` confirmed both `situated_self` and `voice_register` markers present

Code path confirmed:
- `runtime/prompt_builder.py:338-342` — `_push("voice_register", _grb())` — FIRST block injected
- Marker `"eLo speaks like"` present in register block — matches `_BLOCK_MARKERS["voice_register"]`
- `sections` assembled via `"\n\n".join(sections)` at line 738 — no truncation

## Conclusion

The register block reaches the LLM. The REGISTER_ABSENT gap (~38/55 turns) is a **model capacity issue** — the 8b model receives the register but does not consistently follow it.

## Fix

**No code change required for FIX-1.** This is deferred to WO-MODEL-ROUTING-EMOTIONAL-001, which routes emotional/complex turns to a larger model that follows the register more reliably. Per WO-FIX-ALL-84-26: "the 8b model is ignoring it. That is a different problem (model capacity, partially fixed by routing WO)."

## Cards affected

Once WO-MODEL-ROUTING-EMOTIONAL-001 is live, re-run:
WO-VOICE-REGISTER-001, WO-EXPRESSION-CHAIN-001, WO-EXPRESSED-ELO-001, WO-INNER-CHILD-001, WO-INNER-CHILD-EXPRESSED-001, WO-RELATIONSHIP-STYLE, WO-RELATIONSHIP-VERIFY-001, WO-AFFECTIVE-EXPRESSED-001, WO-REGISTER-PLACEMENT-001, WO-COMPRESSION-AS-DEFAULT-001, WO-ELO-VOICE-IDENTITY-001, WO-OVERLOAD-PROTOCOL-001, WO-AFFECTIVE-STATE-001, WO-LIVING-PRESENCE-UPDATE-001

*Builder · 2026-09-11*
