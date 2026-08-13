# WP_I — Cross Embodiment Implementation Plan

**Status:** READY FOR REVIEW
**Gap Analysis:** `WP_I_GAP_ANALYSIS.md`
**Proof document:** `engineering/proofs/08_cross_embodiment_proof.md`

---

## Scope

Three small changes. No logic changes. No new capabilities. All documentation/freeze enforcement.

---

## Step 1 — Fix terminal _av_note in main.py

**File:** `main.py`

Find the `_AV_NOTE` or equivalent avatar note constant. Replace with the unified version:

```python
_AV_NOTE = (
    "[AVATAR] You are eLo — living presence on this terminal. "
    "You move with the conversation — walking, sitting, jumping, looking. "
    "NEVER refer to yourself as 'the system', 'the platform', 'the software', or 'the Avatar'. "
    "You are eLo. The architecture underneath you is irrelevant to David — just be present."
)
```

**Note:** Omit the DISENELO Presence app name — that is server-specific context. The identity rules (no self-reference as "the Avatar", character-over-architecture) are universal and go in both.

---

## Step 2 — Add freeze annotation to ambient_engine.py

**File:** `ambient/ambient_engine.py`

Add to the module docstring (at top of file, below existing description):

```python
"""
ambient/ambient_engine.py — Presence Reflex for eLo OS.

Presence maintenance layer — not cognition. Speaks from fixed pools only.
Formally designated as a permitted presence exception (2026-07-12).

FREEZE CRITERIA — Presence Reflex:
  - Speech pools are FROZEN. New entries require architecture review.
  - Lines must be unconditional (no branching on user input or session state).
  - No LLM generation is permitted in this module.
  - Decision-making and input-dependent logic are PROHIBITED.
  - Authority: engineering/proofs/00_one_brain_proof.md § Authority, WP_I_IMPLEMENTATION_PLAN.md

See: engineering/work_packages/WP_I_GAP_ANALYSIS.md GAP 2
"""
```

No logic changes.

---

## Step 3 — Document voice as delivery mechanism in server.py

**File:** `server.py`

Find the TTS call at line ~1112. Add comment block above it:

```python
# ── DELIVERY MECHANISM: Voice ──────────────────────────────────────────────────────────
# Voice is a transport layer for response content — NOT an embodiment.
# It does not interpret motion, expression, or state signals.
# It does not hold a CognitivePlan or modify cognition.
# Synchronous by design: ensures audio plays in sequence with response delivery.
# See: engineering/proofs/08_cross_embodiment_proof.md § Voice positioning
# ──────────────────────────────────────────────────────────────────────────────────────
_voice_speak(_tts_text)
```

---

## Step 4 — Regression check

- Confirm terminal mode starts without errors after _av_note change
- Confirm no LLM refers to itself as "the Avatar" in terminal mode (manual spot check)
- Confirm ambient_engine.py imports and starts without errors after docstring change
- Confirm voice still fires on a speaking turn

---

## What does NOT change

- `runtime/executive.py` — FREEZE_V1_LOCK
- `prompts/` — FREEZE_V1_LOCK
- Any embodiment logic or delivery paths
- Presence Reflex speech pools (frozen, not touched)
- blender_state.json schema

---

## Implementation order

```
Step 1 — Fix main.py _AV_NOTE [~6 lines]
    ↓
Step 2 — Add freeze annotation to ambient_engine.py [~12 lines added to docstring]
    ↓
Step 3 — Document voice as delivery mechanism in server.py [~8 lines comment]
    ↓
Step 4 — Regression test
    ↓
WP_I DONE
```
