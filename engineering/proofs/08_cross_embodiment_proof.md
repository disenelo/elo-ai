# WP-I Cross Embodiment — Current Reality Review

**Status:** REVIEW COMPLETE — 3 gaps, 1 critical
**Audit date:** 2026-07-12

---

## Embodiment inventory

| Embodiment | Status | Delivery mechanism | Receives CognitivePlan? |
|---|---|---|---|
| Terminal (main.py) | Active | HTTP JSON response | ✓ |
| DISENELO Presence (Desktop) | Active | `blender_state.json` poll (~100ms) | ✓ (via file) |
| eLo-Planet (Unity game) | Partial | `blender_state.json` watcher | ✓ (schema ready, game not deployed) |
| Robot (Raspberry Pi) | Future | `blender_state.json` file read | Schema clear, hardware not built |
| Voice (TTS) | Active | First bubble, synchronous blocking | Delivery mechanism, not an embodiment |
| Presence Reflex (ambient) | Active | Fixed pools only | Permitted exception — not CognitivePlan |

---

## Invariant 07 — No embodiment owns cognitive state

**Status: COMPLIANT ✓**

All embodiments are pure consumers. Confirmed:
- No embodiment modifies response text after generation ✓
- No embodiment reads AttentionSnapshot ✓
- No embodiment writes to session state ✓
- Presence Reflex operates orthogonally — no Executive involvement ✓

---

## Invariant 12 — Single coordinator for blender_state.json

**Status: PARTIAL (fixed for main thread; background threads need verification)**

Writers of `blender_state.json`:
1. `_state_write_presence()` (main thread) — **uses `_STATE_LOCK` ✓** (WP-B fix applied)
2. `ambient_engine.py` (background) — **imported `patch()` from state_writer ✓** (WP-B fix applied)
3. `vision_loop.py` (background) — **imported `patch()` from state_writer ✓** (WP-B fix applied)
4. `spotify_agent.py` (background) — **imported `patch()` from state_writer ✓** (WP-B fix applied)

**All writes now route through `state_writer.patch()` under `_STATE_LOCK`.** WP-B resolved this.

---

## Violations Found

### V1 — Voice (TTS) is synchronous and blocks response delivery (MEDIUM)

TTS call at `server.py:1112` is synchronous and blocking. Every speaking turn waits for:
- OpenAI TTS API response (~1–3s)
- Audio playback completion (~2–5s)
- Total: 5–8s before HTTP response returns to client

**Not an architectural violation** (voice is inside `_lock`, correctly serialised), but latency impact is significant.

**Architecture designation needed:** Voice is a delivery mechanism, not an embodiment. Should be formally documented as such.

---

## Gaps Found

### G1 — Presence Reflex freeze criteria not documented (MEDIUM)

Presence Reflex is now formally designated as a "permitted presence exception" (2026-07-12 resolution). But there is no document specifying:
- What makes a speech line acceptable for the fixed pool
- Who can add new lines and under what review
- How to verify the pool is not growing into input-dependent logic

**Fix:** Add a freeze annotation block to `ambient/ambient_engine.py` header specifying:
- Pool contents are frozen. New entries require architecture review.
- Lines must be unconditional (no branching on user input).
- No LLM generation permitted in this module.

### G2 — Terminal _av_note missing prohibitions present in server (HIGH)

`server.py` `_av_note` explicitly forbids:
- Self-reference as "the Avatar", "the system", "the platform", "the software"
- Names the app: "DISENELO Presence"

`main.py` `_av_note` has no such prohibition. Terminal mode could inadvertently accept "Avatar" self-reference from an LLM.

**Fix:** Update `main.py` avatar note to include the same explicit prohibitions. The identity rules should be embodiment-independent.

### G3 — Robot NeoPixel colour mapping not updated for current mood vocabulary (LOW)

WP_I architecture document specifies colour mapping using `state.mode`. Current `blender_state.json["state"]["mode"]` values come from `_presence_compute()`. The colour mapping in the robot spec may reference an earlier vocabulary.

**Fix:** Verify robot spec colour map against current `_presence_compute()` output vocabulary before any physical implementation.

---

## Cross-embodiment contract (confirmed stable)

All embodiments receive identical CognitivePlan. Schema:

```json
{
  "motion":   { "animation": str, "speed": float, "intensity": float, "mood": str },
  "expression": { "shape_keys": dict, "head_lean": float },
  "state":    { "energy": float, "mode": str, "emotion": str },
  "gaze":     { "yaw": float, "pitch": float, "active": bool },
  "presence_plan": { ... }
}
```

No embodiment-specific variants. Contract is stable. Future embodiments implement readers only.

---

## Summary Table

| Expectation | Reality | Match? |
|---|---|---|
| All embodiments receive same CognitivePlan | ✓ Identical response gen + state write | ✓ |
| No embodiment modifies cognition | ✓ All consumers only | ✓ |
| Single writer coordinator for shared state | ✓ (post WP-B fix) | ✓ |
| Future embodiment interface clear | ✓ Schema documented | ✓ |
| Voice positioning clarified | ✗ Not formally documented as delivery mechanism | ⚠️ |
| Presence Reflex pool frozen and documented | ✗ No freeze annotation on module | ⚠️ |
| Terminal and server _av_note consistent | ✗ Terminal missing prohibitions | 🔴 |
