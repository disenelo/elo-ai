---
chapter: 2
title: "Permissions and the Volume XXIII Boundary — an Un-ADR'd Ownership Conflict"
volume: XIV
status: READY FOR REVIEW — CONTAINS A BLOCKING PROPOSAL (F-1). NOT RATIFIED, NOT DECIDED.
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: N/A — this chapter proposes a boundary; it specifies no mechanism until the ADR lands
audit_status: OPEN — 🔴 BLOCKER
received: 2026-08-13
dependencies:
  - docs/architecture/ARCHITECTURE_BIBLE.md §XIV (grants XIV "permissions, sandboxing")
  - Volume_XXIII/00_Metadata.md (grants XXIII "permissions · tool sandboxing")
  - Volume_XXIII/01_Authentication_Permissions_Sandboxing.md (XXIII has ALREADY specified both, in depth)
  - Volume_XXIII/02_Approval_Gates_and_Trust_Boundaries.md (the confirm-before-act gate)
  - docs/plugin_system.md (the origin text's safety constraints — the mechanism half)
  - docs/architecture/FOUNDATION_VOLUMES_STATUS_2026-08-10.md §"Needs David" F-1 (the named blocker)
  - docs/architecture/CANON_RULINGS_2026-08-10.md §XXIII (software RESERVED collapses; hardware does not)
  - Volume_I/02_The_Constants.md §2.5, §2.6 (Executive authority; David sole L3)
---

# Chapter 2: Permissions and the Volume XXIII Boundary

> **🔴 This chapter states a conflict and proposes a resolution. It decides nothing.**
> The resolution needs an **ADR** and **David's confirmation**, because it is a scope
> transfer between two ratified-track volumes. Chapter 3 (hot swap, discovery, dependency
> injection) is **blocked** until it lands — writing it first would be writing into a subject
> this volume may not own.

## 2.0 The conflict, stated plainly

**Two volumes claim permissions and sandboxing. Neither has a decision record.**

**Volume XIV's claim — `ARCHITECTURE_BIBLE.md` §EXPANSION, verbatim:**

> *"**XIV — Plugin Architecture.** Dynamic loading, capabilities, **permissions,
> sandboxing**, extension API, discovery, dependency injection, hot swapping."*

**Volume XXIII's claim — `Volume_XXIII/00_Metadata.md` §Scope (authoritative, from the same
Bible), verbatim:**

> *"Authentication · **permissions** · **tool sandboxing** · secret management · memory
> protection · trust boundaries · human approval gates · safety policies · threat model."*

**The Bible grants the same two subjects to both volumes.** That is the root fact, and it is
worth being precise about: this is not one volume drifting into another's lane. It is a
scope-definition error in the source document, inherited by both.

**What has happened since is what makes it urgent: XXIII has already built it.**
`Volume_XXIII/01_Authentication_Permissions_Sandboxing.md` is a deep, live-anchored chapter
containing the permission model (§1.3 — five capability classes derived from declarations in
`runtime/capabilities/registry.py`), authentication in two kinds (§1.4), sandboxing rules
that make denial structural (§1.5), and the `ELO_COMPUTER_CONTROL` worked example (§1.6). It
is READY FOR REVIEW with the rest of Volume XXIII.

**Volume XIV, meanwhile, has a parallel permission mechanism already shipping in code** — the
`CAPABILITIES` vocabulary, `LAYER`, `KERNEL_SAFE`, and `validate()`-at-registration in
`plugins/base.py` and `plugins/registry.py` (Ch.1 §1.3–§1.4).

**So there are two capability systems in one mind:**

| | Volume XXIII | Volume XIV |
|---|---|---|
| Object | `Capability` (`runtime/capabilities/capability.py`) | `CAPABILITIES: list` on `PluginBase` |
| Registry | `runtime/capabilities/registry.py` | `plugins/registry.py` |
| Vocabulary | `requires_confirmation` · `requires_api` · `requires_authentication` · `enabled` · `future` · `health_state` | `text_generation` · `voice_output` · `hardware_output` · `voice_input` · `vision` · `observability` |
| Gate | confirm-before-act (`execution_gate.py`), env opt-in, OS grant | `validate()` refusal at registration |
| Answers | *may eLo do this?* | *what kind of thing is this plugin?* |

**Two things called a capability registry in one architecture is the same shape as the
failures Rulings A, B and D already corrected** — two world graphs, two attention drivers,
two trait models. Each time the answer was *one*. **This one has not been ruled on**, and
`FOUNDATION_VOLUMES_STATUS_2026-08-10.md` names it **F-1**, the blocker.

## 2.1 Why it cannot be left to sort itself out

Three concrete failures follow from leaving it, and they are not hypothetical:

**2.1.1 A plugin can name itself into a permission.** Today a plugin declares
`CAPABILITIES = ["hardware_output"]` and `KERNEL_SAFE = True` and — if `validate()` passes —
it is registered. Nothing in that path consults `runtime/capabilities/registry.py`, the
confirm-before-act gate, or `ELO_COMPUTER_CONTROL`. `plugins/hardware/` already exists
(`robot_body.py`, `orb_engine.py`). **The declaration that says what a plugin is and the
declaration that says what eLo is allowed to do are different declarations, read by different
registries, and they do not meet.**

**2.1.2 Sandboxing means two different things.** XXIII §1.5 sandboxing is *capability
isolation* — an agent may only perform the verbs it declares, may not shell out, may not
borrow another agent's reach. Plugin sandboxing is *layer isolation* — `plugin → core/` is
forbidden. Both are real; **neither covers the other.** A plugin perfectly obeying the layer
rule can still drive hardware it was never authorised to drive, and a capability perfectly
gated by XXIII can still be reached by a caller that imported a plugin directly.

**2.1.3 Whoever writes it second writes it wrong.** If XIV specifies capability classes and
gates, it forks XXIII's model. If XXIII specifies the plugin contract, it reaches into the
extension API. **This is precisely why the prior assessment said XIV was blocked**, and it is
why this chapter proposes rather than specifies.

## 2.2 What is NOT in dispute

Worth isolating, because the contested area is smaller than it looks and the agreed part is
already firm:

- **XXIII owns** authentication, secrets, memory protection, the threat model, approval gates,
  trust boundaries, and RESERVED / L3 / LG-2. Uncontested.
- **XIV owns** the registry-as-choke-point, the plugin contract, dynamic loading, discovery,
  dependency injection, the layer rules, the fallback chain, and hot swapping. Uncontested.
- **Both agree on the invariant.** XXIII §1.1.1: *default-deny for capability, default-allow
  for presence.* Plugin system: *plugins extend output layers only.* Same instinct, two
  vocabularies.
- **Both defer to the Executive.** Nothing either volume specifies may let a plugin or a
  capability produce an externally visible assertion around the Executive (Volume I Ch.2
  §2.5).

**The contested area is exactly one thing:** *when a plugin wants to do something in the
world, whose model says whether it may — and what is the object that carries the answer?*

## 2.3 🔴 Proposed split — POLICY vs MECHANISM

**Architect recommendation (a proposal; needs an ADR + David):**

> ### **Volume XXIII owns the security POLICY. Volume XIV owns the plugin MECHANISM.**
>
> **XXIII decides *what is allowed*.** Capability classes (read-only · reversible ·
> confirm-required · auth-required · dangerous), approval gates, confirm-before-act,
> authentication, RESERVED, L3/LG-2, the sandbox boundary, the threat model. **One permission
> model for the whole mind — plugins included.**
>
> **XIV decides *how a plugin declares and receives capability*.** The declaration a plugin
> must make, how the registry validates it, how a granted capability is handed to a plugin at
> activation, how a plugin degrades when a capability is denied or revoked, and how all of
> that survives a hot swap. **One extension mechanism — carrying XXIII's decisions, never
> making its own.**
>
> **The seam: a plugin's `CAPABILITIES` declaration is a *request*, not a *grant*.** The
> registry resolves each declared capability against XXIII's model at registration and
> activation. A capability XXIII does not grant is not available to the plugin, whatever the
> plugin declared. `KERNEL_SAFE` / `LAYER` stay XIV's — they are statements about the
> plugin's *shape*, not about its *authority*.

**Why this way round, in one line each:**

- **XXIII has already built the model, with the threat matrix and the live anchors.** Moving
  it to XIV would discard working canon and re-open a settled security design (CHECK-BEFORE-
  BUILD: extend, never duplicate).
- **A security policy must be one policy.** Two permission models is the One-Brain violation
  in its most consequential form — the place where "two answers" means an unauthorised
  physical action, not a stylistic inconsistency.
- **XIV is genuinely the mechanism volume.** Everything else in its Bible scope — dynamic
  loading, discovery, dependency injection, hot swapping — is mechanism. Permissions was the
  odd item in that list; policy in a mechanism volume is what created the overlap.
- **It matches how the code already wants to work.** Both are registries-as-choke-points. The
  fix is to make one call the other, not to merge them.

**Consequence for the Bible:** XIV's scope line loses *"permissions, sandboxing"* and gains
*"capability declaration and grant-carrying (per Volume XXIII)"*. That is the scope transfer
the ADR records.

## 2.4 What XIV would then specify (post-ADR, not now)

Scoped so the ADR's consequences are visible before it is signed. **None of this is
specified in this chapter** — it is what Chapter 3 would carry if the split lands:

1. **Declaration → resolution.** At `register()`, each declared capability resolves against
   XXIII's model. Unrecognised capability → registration refused (Ch.1 FT-3). A capability
   whose XXIII class is `dangerous` → the plugin registers but cannot exercise it until the
   XXIII opt-in and gate are satisfied.
2. **Grant delivery.** How an activated plugin *receives* a capability it may use — the
   dependency-injection half of the Bible scope. Proposed shape: the registry injects a
   capability handle at `on_load()`; a plugin never reaches for one itself. **The plugin never
   holds the grant; it holds a handle the registry can revoke.**
3. **Denial and revocation.** What a plugin does when a capability is denied at activation or
   revoked mid-session (David flips `ELO_COMPUTER_CONTROL` off; a credential expires).
   Proposed: degrade to the fallback chain, report honestly, never fabricate the action
   (Ch.1 §1.5; Volume XXIII Ch.1 §1.4.1).
4. **Hot swap under permission.** A swap may never widen authority silently. **The incoming
   plugin's capabilities are re-resolved against XXIII before it becomes active**, and the
   swap never interrupts an in-flight turn (Ch.1 FT-2).
5. **The two-registry seam, made testable.** `ST: no plugin exercises a capability XXIII has
   not granted` — the test that closes §2.1.1.

## 2.5 The hardware edge — the case that makes this urgent

`plugins/hardware/` exists today, with `robot_body.py` and `orb_engine.py`, and the
`hardware_output` capability is in the plugin vocabulary. Meanwhile
`CANON_RULINGS_2026-08-10.md` §XXIII rules that **robot hardware RESERVED does not collapse**:
force · magnetics · pump · thermal · battery · pinch points require **David L3 plus a real,
separate LG-2** who did not design the part, and *"the force limiter / soft-stop scope must be
DONE before anything is powered near David."* Volume XXIII Ch.1 §1.8 OQ-1.8.4 adds the sharp
line: **the single-switch simplification is a SOFTWARE-lane decision and must not be carried
onto robot actuation; `ELO_COMPUTER_CONTROL` never authorises physical actuation.**

**Under the current un-ADR'd state, a plugin declaring `hardware_output` passes plugin
validation without any of that being consulted.** Nothing bad has happened — nothing is
powered — but the gap is structural, not hypothetical, and it sits on the one lane where the
canon explicitly refuses to relax the gate.

**Proposed rule, for confirmation as D-7:**

> **A plugin may never hold a RESERVED capability. It may only propose an action that a
> RESERVED gate then authorises.** Physical actuation is never reached through the plugin
> layer's own authority — the plugin is the *delivery* path, never the *authorisation* path.

This is the plugin-layer form of Volume I Ch.2 §2.6 (*eLo may request a grant; it may never
self-grant*) and of Volume XXIII §1.5 (*no self-escalation*).

## 2.6 What this chapter deliberately does not do

- It does not specify a permission mechanism. Specifying one now would be writing into a
  contested subject — the failure the prior assessment warned against.
- It does not amend Volume XXIII. That volume is READY FOR REVIEW and its model stands.
- It does not edit `ARCHITECTURE_BIBLE.md`. The scope correction is the ADR's output, not a
  unilateral Architect edit to a David-authored source.
- It does not touch `plugins/` or any code (D-LANES). The two-registry seam is relayed as a
  requirement to the owning seat once the ADR lands.

## 2.7 🔴 Needs David — the ADR that unblocks this volume

**F-1 (from `FOUNDATION_VOLUMES_STATUS_2026-08-10.md` §"Needs David"), restated with the
proposal attached.**

**Draft ADR decision statement, for David's yes/no/amend:**

> **ADR-XIV-001 — Plugin permissions: policy to XXIII, mechanism to XIV.**
>
> `ARCHITECTURE_BIBLE.md` grants *"permissions, sandboxing"* to both Volume XIV and Volume
> XXIII. Volume XXIII Ch.1 has since specified the permission model, capability classes,
> approval gates and sandboxing in depth, grounded in `runtime/capabilities/registry.py`.
>
> **Decision: Volume XXIII owns the security POLICY — what eLo is allowed to do, the
> capability classes, approval gates, authentication, sandboxing and RESERVED — for the whole
> mind, plugins included. Volume XIV owns the plugin MECHANISM — the declaration a plugin
> makes, how the registry resolves it against XXIII's model, how a grant is delivered and
> revoked, and how it survives a hot swap. A plugin's `CAPABILITIES` declaration is a request,
> not a grant.**
>
> Consequence: XIV's Bible scope line drops *"permissions, sandboxing"* and gains *"capability
> declaration and grant-carrying (per Volume XXIII)"*. No change to Volume XXIII's scope.
> Volume XIV Chapter 3 is unblocked on acceptance.

**Three questions for David:**

1. **Is the split right?** (Architect recommendation: yes — POLICY to XXIII, MECHANISM to
   XIV, for the four reasons in §2.3.) If David prefers the opposite, XXIII Ch.1's permission
   model moves to XIV and Volume XXIII is amended — a larger change, and the reason this is
   asked rather than assumed.
2. **D-7 — the RESERVED rule (§2.5).** Confirm that a plugin may never *hold* a RESERVED
   capability, only propose. This constrains the robot lane and should be settled before any
   hardware plugin is exercised.
3. **The Bible edit.** The scope correction touches a David-authored source. Confirm the
   Architect may make it once the ADR is accepted, or keep it as David's edit.

**Until this lands: Volume XIV Chapter 3 stays unwritten, and no permission mechanism is
specified in this volume.**

## 2.8 Architecture References

- `docs/architecture/ARCHITECTURE_BIBLE.md` §XIV — the scope line containing the two contested
  words.
- `Volume_XXIII/00_Metadata.md` — the scope line containing the same two words.
- `Volume_XXIII/01_Authentication_Permissions_Sandboxing.md` — §1.1 principles · §1.3 the
  permission model and five capability classes · §1.4 authentication and authority scope ·
  §1.5 sandboxing · §1.6 the `ELO_COMPUTER_CONTROL` worked example · §1.8 OQ-1.8.4.
- `Volume_XXIII/02_Approval_Gates_and_Trust_Boundaries.md` — the confirm-before-act gate and
  `_IMMEDIATE_SAFE`.
- `docs/plugin_system.md` — the origin text's safety constraints (the mechanism half).
- `plugins/base.py` · `plugins/registry.py` · `plugins/hardware/` — the parallel declaration
  path (§2.1.1, §2.5).
- `runtime/capabilities/registry.py` · `runtime/capabilities/capability.py` — XXIII's model in
  code.
- `docs/architecture/CANON_RULINGS_2026-08-10.md` §XXIII — software RESERVED collapses;
  **hardware RESERVED does not**; single-switch `ELO_COMPUTER_CONTROL`.
- `docs/architecture/FOUNDATION_VOLUMES_STATUS_2026-08-10.md` §"Needs David" **F-1** — the
  named blocker this chapter answers with a proposal.
- `Volume_I/02_The_Constants.md` §2.5 (Executive authority) · §2.6 (David sole L3; no
  self-escalation).

---

```
Chapter 2 — Permissions and the Volume XXIII Boundary
Status: READY FOR REVIEW — CONTAINS A BLOCKING PROPOSAL. NOT DECIDED.
Files: Volume_XIV/02_Permissions_and_the_XXIII_Boundary.md
The conflict: ARCHITECTURE_BIBLE.md grants "permissions, sandboxing" to BOTH XIV and XXIII.
  XXIII Ch.1 has already specified both, in depth, with NO ADR transferring ownership.
  Two capability registries exist in code and they do not meet (§2.1.1).
Proposed split: XXIII owns the security POLICY (what is allowed, capability classes, approval
  gates, RESERVED). XIV owns the plugin MECHANISM (how a plugin declares and receives
  capability). A plugin's CAPABILITIES declaration is a REQUEST, not a GRANT.
Draft ADR: ADR-XIV-001 (§2.7) — needs an ADR + David's confirmation (scope transfer between
  two ratified-track volumes).
🔴 Blocks: Volume XIV Chapter 3 (hot swap · discovery · dependency injection).
Needs David: the split · D-7 (a plugin may never HOLD a RESERVED capability) · the Bible edit.
```

READY FOR REVIEW — NOT RATIFIED — NOT DECIDED
