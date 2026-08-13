---
id: ADR-XIV-001
title: "Plugin permissions — XXIII owns POLICY, XIV owns MECHANISM"
status: ACCEPTED · CANON (Architect ruling — David confirmation invited, not required to unblock)
date: 2026-08-13
owner: David Charles
author: Claude (Lead Architect)
related: Volume_XIV (Plugin Architecture) · Volume_XXIII (Security & Trust) · LAW-017 (Approval Scope) · ADR-Exec-001
unblocks: WO-CANON-XIV
---

# ADR-XIV-001 — Plugin permissions: XXIII owns POLICY, XIV owns MECHANISM

## Context
Volumes XIV and XXIII both claimed permissions and sandboxing. Volume XIV was blocked waiting on the question
being settled. It is a technical ownership question, not a values question, so the Architect rules it here.

**The real gap this protects (verified in code):** there are **TWO capability registries** —
`plugins/registry.py` and `runtime/capabilities/registry.py` — **and they never meet.** A plugin declaring
`hardware_output` passes plugin validation **without ever consulting Volume XXIII's approval gates**.
`plugins/hardware/robot_body.py` already exists. As the robot lane advances, that is a real hole: a plugin
could reach hardware without crossing a safety gate.

## Decision
**One permission model for the whole mind. Two distinct responsibilities.**

- **Volume XXIII owns the POLICY — *what is allowed*.** Capability classes, approval gates, authentication,
  sandboxing rules, and the RESERVED set (money · legal · safety · robot hardware). This applies to **every**
  actor in the system, plugins included. Plugins get no separate rulebook.

- **Volume XIV owns the MECHANISM — *how a plugin asks*.** How a plugin declares the capabilities it wants,
  how it is resolved and loaded, how capability is granted or withheld at runtime, how it is revoked, and how
  that survives a hot swap.

**The seam — the load-bearing rule:**
> **A plugin's `CAPABILITIES` declaration is a REQUEST, not a GRANT.**

Declaring a capability must never confer it. The grant is issued by the XXIII policy layer, which the plugin
registry must consult. The two registries reconcile: `plugins/registry.py` asks
`runtime/capabilities/registry.py`; it does not decide for itself.

## Consequences
**Forbidden:** a plugin holding a capability it merely declared · a second permission model for plugins ·
any path to hardware, money, legal or safety actions that bypasses XXIII's gates.
**Enabled:** plugins can be added freely without widening the trust surface, because capability is granted
centrally and can be refused or revoked centrally.
**Corollary (recommended, flagged for David):** **a plugin may never HOLD a RESERVED capability — only
propose an action for approval.** This constrains the robot lane deliberately: `robot_body.py` proposes;
it does not act unilaterally. *This is the one line here with a values edge — David can overrule it.*

## How it is enforced
1. `plugins/registry.py` calls the XXIII capability registry before activating any declared capability.
2. A declared-but-not-granted capability leaves the plugin loaded and **functional-but-limited**, with the
   refusal **logged**, never silently swallowed (the WO-096 failure class).
3. Test: a plugin declaring `hardware_output` is **refused** unless XXIII grants it; the refusal appears in
   the log; the plugin does not crash.

## Open — David's call, does not block the build
- **O-1:** confirm the corollary — plugins may only *propose* RESERVED actions, never hold them.
- **O-2:** whether third-party plugins are ever in scope (currently eLo is David's personal tool, so every
  plugin is his own; this ADR holds either way but matters more if that changes).
