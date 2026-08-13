# 09_WO-CANON-XIV_plugin_gates.md — UNBLOCKED. ADR-XIV-001 is written.

**WO:** WO-CANON-XIV · **Seat:** builder · **Priority:** P2 · **Reserved?** no
**ADR:** `docs/architecture/adr/ADR-XIV-001_Plugin_Permissions_Ownership.md` (written 2026-08-13 — this was
your blocker; it's gone) · **Canon:** `Volume_XIV/02_Permissions_and_the_XXIII_Boundary.md`

## The ruling
- **Volume XXIII owns POLICY** — what's allowed: capability classes, approval gates, sandboxing, RESERVED.
  One permission model for the whole mind. Plugins get no separate rulebook.
- **Volume XIV owns MECHANISM** — how a plugin declares, is resolved, receives, loses capability.
- **The seam:** a plugin's `CAPABILITIES` declaration is a **REQUEST, not a GRANT**.

## The real gap [VERIFIED — code audit]
**Two capability registries exist and never meet:** `plugins/registry.py` and
`runtime/capabilities/registry.py`. A plugin declaring `hardware_output` passes plugin validation **without
consulting XXIII's gates** — and `plugins/hardware/robot_body.py` already exists. Close this before the robot
lane advances.

## Scope
1. `plugins/registry.py` **consults** `runtime/capabilities/registry.py` before activating any declared
   capability. Declaring never confers.
2. A declared-but-refused capability leaves the plugin **loaded and functional-but-limited**, with the refusal
   **LOGGED** — never silently swallowed (that's the WO-096 failure class, don't repeat it).
3. Reconcile the two registries so there is one grant path.

## Test
A plugin declaring `hardware_output` is **refused** unless XXIII grants it · the refusal is logged · the
plugin doesn't crash · a granted capability works normally.

## Done when
implemented + test green + committed → hash, DONE/, outbox, next card.
