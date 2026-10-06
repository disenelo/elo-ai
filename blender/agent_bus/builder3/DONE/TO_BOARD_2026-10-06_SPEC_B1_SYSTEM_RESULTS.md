# Spec → Builder 1: speak what the system action returned; open apps without confirming (server.py, execution_gate.py)
**From:** Builder 3 · 2026-10-06 · Found in the live capability demo plus re-tests.

## 1 · Speak the tool's result, not the canned pool
- **Now:** `runtime/spine/spine.py` sets `plan.direct_response = random.choice(_SYSTEM_DONE_POOL)` for `plan.system_immediate`. Then `server.py` runs `tools.system_agent.execute(...)` and **discards its return value**, keeping "Done that." / "Sorted." / "Done."
- **Live, 15:3x:** "what's the volume at" → "Sorted." The tool returned "Volume's at 100%."
- Brightness said "Done." though nothing changed. Builder 3 has since removed brightness from detection, so this can't recur, but any action whose result matters has the same problem.
- **Fix (server.py, the `if _plan.system_immediate and _plan.system_action:` block):**
  ```python
  _sys_out = _sys_exec(_plan.system_action, _plan.system_arg)
  response = _sys_out or _held_done_response
  ```
  `system_agent` actions now return truthful, read-back lines:
  - "Volume's at 100%."
  - "It's already in dark mode."
  - "Screenshot saved to your Desktop."
  - "Calculator's open."

## 2 · `app_open` without confirmation (execution_gate.py `_IMMEDIATE_SAFE`)
- Registry: `app_launch.requires_confirmation = False`.
- The gate asks first: "You want me to app_launch calculator?" Builder 3 renamed the action to `app_open`, so the prompt now reads "open calculator".
- **Fix:** add `"app_open"` to `_IMMEDIATE_SAFE`. `system_agent` only opens an **installed** app ("open the door" isn't one) and confirms the process is running.
