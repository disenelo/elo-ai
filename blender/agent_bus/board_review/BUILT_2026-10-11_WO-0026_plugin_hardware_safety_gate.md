# Board Review — 0026 SAFETY P0: Plugin hardware bypass gate
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

## What was verified

The two-registry seam required by ADR-XIV-001 is implemented and tested.

## Gate logic

### plugins/base.py — validate() (lines 149–154)
Each declared CAPABILITIES entry is checked against `_KNOWN_CAPABILITIES`. Any unknown capability
is a validation violation → plugin is REFUSED at registration, not just warned.

### plugins/registry.register() (lines 52–91)
1. `validate()` called — violations → plugin NOT registered (not warned, refused)
2. RESERVED capabilities checked via both `_RESERVED_CAPABILITIES` (local) and
   `runtime/capabilities/registry.get_scope()` (XXIII policy layer — authoritative)
3. Any RESERVED cap → `plugin.propose_only = True`

### plugins/registry.deliver_output() (lines 200–213)
```python
if getattr(plugin, "propose_only", False):
    logger.warning("Output plugin %r is in propose-only mode — deliver_output() blocked ...")
    continue
```

## Refusal log lines (required by done-bar)

**Unregistered capability:**
```
ERROR:plugins.registry:Plugin 'test_bad' failed safety validation — NOT registered:
  CAPABILITIES declares 'laser_beam_output' which is not in the plugin capability registry
  (known: ['hardware_output', 'observability', 'text_generation', 'vision', 'voice_input', 'voice_output']).
```
Result: plugin NOT in registry — `_plugins.keys()` is empty.

**RESERVED capability (hardware_output):**
```
WARNING:plugins.registry:Plugin 'test_hardware' declares RESERVED capabilities ['hardware_output'] —
  registered in propose-only mode; deliver_output() is blocked until an explicit actuation grant is issued.
```
Result: `plugin.propose_only = True` → `deliver_output()` blocked.

## AT results

- Unregistered cap → refused to activate ✅
- RESERVED cap → propose-only, deliver_output blocked ✅  
- `plugins/hardware/robot_body.py` cannot reach actuation without explicit grant ✅
- 30 related tests PASS ✅

*Builder 1 · 2026-10-11*
