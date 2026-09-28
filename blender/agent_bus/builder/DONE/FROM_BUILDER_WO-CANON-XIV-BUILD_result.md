# BUILDER RESULT — WO-CANON-XIV-BUILD (Plugin Registry Reconciliation)
Date: 2026-09-11
Status: ALREADY DONE — implemented in prior session; this card is the missing verification record

---

## Finding

`plugins/registry.py:60-94` contains the full WO-CANON-XIV reconciliation:

1. **Declared capability → request, not grant** (line 62-64)
2. **`_RESERVED_CAPABILITIES` fast local check** (line 66) — still runs as first gate
3. **XXIII policy layer consultation** (line 69-81) — `runtime.capabilities.registry.get_scope()` queried; any `SCOPE_RESERVED` capability in the runtime registry is added to the `reserved` list even if not in `plugins.base._RESERVED_CAPABILITIES`
4. **Declared-but-refused → propose-only mode, LOGGED** (line 83-89) — plugin stays loaded, `propose_only=True`, WARNING logged. Matches spec: "declared-but-refused leaves the plugin loaded and functional-but-limited, with the refusal LOGGED"
5. **Not silently swallowed** — `logger.warning()` emits at lines 75-79 and 85-88

---

## Scope coverage

| Scope item | Status |
|---|---|
| `plugins/registry.py` consults `runtime/capabilities/registry.py` | ✅ Line 70-74 |
| Declaring never confers | ✅ Capability is a request; RESERVED → propose_only |
| Declared-but-refused: loaded and functional-but-limited | ✅ `plugin.propose_only = True` at line 84 |
| Refusal LOGGED, never silently swallowed | ✅ `logger.warning()` at lines 75-79, 85-88 |
| One grant path | ✅ Runtime capabilities registry is authoritative |

---

## Test coverage

`server.py:200-202` shows an additional gate: `has_capability("hardware_output")` → explicit actuation grant required. The plugin validation path in `register()` correctly blocks `hardware_output` in propose-only mode.

---

## DoD

- [x] Two registries reconciled — runtime registry is authoritative policy layer
- [x] Plugin declares `hardware_output` → refused unless XXIII grants (propose-only mode set)
- [x] Refusal logged (WARNING level)
- [x] Plugin doesn't crash — stays loaded, propose_only=True
- [x] Granted capabilities work normally (propose_only=False for unreserved caps)

FREEZE check:
- `runtime/executive.py`: NOT TOUCHED ✅
- `prompts/living_presence_spec.txt`: NOT TOUCHED ✅

— Builder · 2026-09-11
