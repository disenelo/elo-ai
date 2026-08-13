# WP_I — Cross Embodiment Gap Analysis

**Status:** REVIEW COMPLETE — 3 gaps (1 HIGH, 2 MEDIUM)
**Proof document:** `engineering/proofs/08_cross_embodiment_proof.md`
**Next stage:** Implementation Plan

---

## What the architecture expects vs. what exists

| Architecture Expectation | Current Reality | Gap? |
|---|---|---|
| All embodiments receive identical CognitivePlan | ✓ Same response gen + state writes | ✓ Match |
| No embodiment modifies cognition | ✓ All pure consumers | ✓ Match |
| Single coordinator for blender_state.json | ✓ (post WP-B fix — all writers use patch()) | ✓ Match |
| Future embodiment interface clear | ✓ Schema documented | ✓ Match |
| Avatar identity rules consistent across embodiments | ✗ Terminal _av_note missing prohibitions | 🔴 GAP |
| Presence Reflex pool frozen and documented | ✗ No freeze annotation on module | 🔴 GAP |
| Voice positioning formally documented | ✗ Not designated as delivery mechanism | ⚠️ GAP |

---

## Gaps requiring implementation

### GAP 1 — Terminal _av_note missing avatar identity prohibitions (🔴 HIGH)

**What exists — server.py (DISENELO Presence):**
```
"NEVER refer to yourself as 'the system', 'the platform', 'the software', or 'the Avatar'."
"You are eLo. The architecture underneath you is irrelevant to David — just be present."
"The app is called DISENELO Presence — not Desktop Buddy."
```

**What exists — main.py (Terminal):**
```
"You have a small visual window in the bottom-right corner of the user's screen."
```
No self-reference prohibition. No character-over-architecture directive.

**Resolution:**
- Update `main.py` avatar note to include:
  - Self-reference prohibition (identical to server.py)
  - "You are eLo. The architecture underneath you is irrelevant." directive
  - Note: "DISENELO Presence" name is server-specific, but the identity rules are universal

**Implementation scope:** `main.py` (~6 lines in the `_AV_NOTE` or equivalent constant)

---

### GAP 2 — Presence Reflex freeze criteria not documented on module (🔴 MEDIUM)

**What exists:** `ambient/ambient_engine.py` was renamed to "Presence Reflex" and formally designated as a permitted exception. But the module itself has no freeze annotation.

**Resolution:** Add a freeze annotation block to `ambient_engine.py` module header:
```
FREEZE CRITERIA (Presence Reflex):
  - Speech pools are FROZEN. New entries require architecture review.
  - Lines must be unconditional (no branching on user input).
  - No LLM generation permitted in this module.
  - Decision-making and input-dependent logic are PROHIBITED.
```

**Implementation scope:** `ambient/ambient_engine.py` docstring (~10 lines added)

---

### GAP 3 — Voice (TTS) not formally designated as delivery mechanism (⚠️ MEDIUM)

**What exists:** Voice is called synchronously inside `_process_turn()` (`server.py:1112`). Architecturally it is a delivery mechanism (like the HTTP response), not an embodiment. But this designation is not documented anywhere.

**Resolution:**
- Add a comment block in `server.py` at the TTS call site:
  ```
  # DELIVERY MECHANISM: Voice is a transport layer for response content.
  # It is NOT an embodiment — it does not interpret motion/expression/state.
  # Synchronous by design: ensures audio plays in sequence with response.
  ```
- Add to architecture overview: "Voice is a delivery mechanism, not an embodiment."

**Implementation scope:** `server.py` (~6 lines comment), architecture doc update

---

## What already satisfies the architecture

- Cross-embodiment plan consistency: Clean (post WP-B)
- No embodiment modifies cognition: Clean
- blender_state.json single coordinator: Clean (post WP-B)
- Future embodiment interface: Clear schema documented
- Robot NeoPixel mapping: Verify vocabulary against current `_presence_compute()` output before physical build (low priority, no code change needed now)

---

## Implementation priority order

1. **GAP 1** — terminal _av_note. Simple edit, high identity-consistency value.
2. **GAP 2** — freeze annotation on ambient_engine.py. Protects Presence Reflex designation.
3. **GAP 3** — comment documentation. Lowest risk, highest clarity.

---

## Invariants unblocked

| Invariant | Status Now | Status After |
|---|---|---|
| Identity consistent across embodiments | ✗ Terminal weaker | ✓ (after GAP 1) |
| Presence Reflex formally frozen | ✗ No freeze doc on module | ✓ (after GAP 2) |
