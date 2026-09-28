# FROM BUILDER — WO-ROOT-CAUSE-FIX: RC Scan Register
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-13_WO-ROOT-CAUSE-FIX.md
**Authority:** David L3 — 2026-09-13

---

## Scan method

Cards in DONE folder classified by failure type against the 6 root causes. Read-only — no re-runs. Current status based on code inspection + live server evidence (where run).

---

## RC-to-card class mapping

### RC-1 — No OutcomeRecord (plain string instead of dict)
Code: `server.py:4919` — OutcomeRecord dict in place with RC-1 comment.
Live evidence: `last_significance.json` shows `"outcome": {"verified": true, "ack_received": false, "completion": "met", "cost": {}}` — this is a dict, not a string.

**Cards in this class:**
- Any card showing `embodiment: 0.0`, `efficiency: 0.0`, `safety: 0.0`, `reward: 0.0` across all turns (significance dimension zeroing)
- Cards about eLo not learning from consequences
- Cards about significance scoring not reflecting actual outcomes
- Status: **CODE APPLIED — live evidence filed in FROM_BUILDER_2026-09-14_RC-1-RC-4_result.md**

### RC-2 — Two assembled-state objects
Code: `runtime/cognitive_snapshot.py:145` — `UnifiedCognitiveState = CognitiveSnapshot` alias real.
RC-2 comment at line 132. Six missing components folded into CognitiveSnapshot.

**Cards in this class:**
- Cards about Executive receiving contradictory state
- Cards about cognitive truth violations (ADR-002 R1+R2)
- Status: **CODE APPLIED — requires live Executive-receives-one-object evidence**

### RC-3 — executive.py not consuming learning_advice
Code: `runtime/executive.py:432` — `_adv = attention_model.get("learning_advice") or {}`
Learning advice consumed in `decide()`.

**Cards in this class:**
- Cards about eLo not applying lessons to responses
- Cards about learning faculty output being silently ignored
- David L3 confirmed Option A 2026-09-13: unfreeze executive.py
- Status: **CODE APPLIED — requires live server turn showing lesson influence**

### RC-4 — No version field on significance vectors
Code: `memory/significance_engine.py:257` — `scores["version"] = "2.0.0"` with RC-4 comment.
Live evidence: `last_significance.json` shows `"version": "2.0.0"` in profile dict.

**Cards in this class:**
- Any card about significance vector validity (ADR-007 §3)
- Status: **SERVING — live evidence filed in FROM_BUILDER_2026-09-14_RC-1-RC-4_result.md**

### RC-5 — Ambient SPEAK bypasses spine prompt pipeline
Code: `server.py:1137` — RC-5 comment, ambient SPEAK uses spine plan when `direct_response` available.
`server.py:1174` — `_amb_exec_decision` built from spine plan fields (spine-plan-derived).

**Cards in this class:**
- Cards about ambient speech, uninstructed speech
- Cards about eLo speaking without full context
- Status: **CODE APPLIED — non-deterministic; evidence appears when ambient engine fires SPEAK**

### RC-6 — EloDesktopNav route decided inside Unity
Lane: Designer. Not a Python fix.

**Cards in this class:**
- Navigation/movement routing cards citing Unity-side decision
- Status: **ROUTED TO DESIGNER** — not Builder's lane

---

## Code-applied status summary

| RC | Fix location | Code in place | Live evidence |
|---|---|---|---|
| RC-1 | server.py:4919 | ✓ | ✓ (this session) |
| RC-2 | cognitive_snapshot.py:132-145 | ✓ | Pending live turn |
| RC-3 | executive.py:432 | ✓ | Pending live turn |
| RC-4 | significance_engine.py:257 | ✓ | ✓ (this session) |
| RC-5 | server.py:1137-1218 | ✓ | Non-deterministic |
| RC-6 | — | Designer lane | — |

---

*Builder · 2026-09-14*
