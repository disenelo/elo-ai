**WO:** FALSE-ACTION-GUARD-AUDIT · **Seat:** builder · **Priority:** P2
**Reserved?** no

## Result
- commit: (no new code — read-only audit)
- test: test_canon_vii_executive.py → 0 tests collected (file exists but has no test functions)
- notes: Audit complete. 4 completion paths reviewed.

### 1. `_SYSTEM_DONE_POOL` → spine.py:666-670 → server.py:5906-5932 ✅ CLEAN
   FALSE-ACTION-FIX already in place (see server.py:5907 comment). "Done that." held before
   action runs; restored on success; replaced with "Ran into something on that" on failure.

### 2. `_ANIM_REPLIES` → server.py:3193 ✅ CLEAN
   Uses `honest_outcome()` via `ack_contract`. If `_anim_ok` is False, reply is replaced with
   "That didn't [...]" — honesty beat already enforced.

### 3. `_direct_intercepts` → tool_router.py:1942 ✅ CLEAN (per 8db420e)
   Intercepts for [IMAGE_GEN], [MODEL_GEN], [REMINDER_SET] are data-driven — these prefixes are
   only injected into user_input by server.py AFTER the real tool ran. No false completion possible.

### 4. `_SCALE_REPLIES_UP/DOWN` → server.py:3211/3214 🔴 FALSE ACTION FOUND
   server.py:3215-3216:
   ```python
   except Exception:
       _scale_reply = "Done."
   ```
   When `scale_up()/scale_down()` raises an exception (e.g. Blender bridge not running),
   `_scale_reply = "Done."` fires — eLo claims it scaled when it failed.
   
   Fix needed: replace with an honest failure line (e.g. "Blender's not running — couldn't resize.")
   Filed as spec: this is a P2 fix, not blocking.

### Summary
- 3 paths CLEAN
- 1 path FALSE ACTION: server.py:3216 — scale command failure fallback says "Done."
- No false-completion paths in `_direct_intercepts` post-8db420e
- Spec for scale fix: change `_scale_reply = "Done."` to `_scale_reply = "Blender's not running — couldn't resize."` at server.py:3216
