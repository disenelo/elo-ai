---
chapter: 1
title: "Authentication, Permissions & Sandboxing — What eLo Is Allowed To Touch"
volume: XXIII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
received: 2026-08-10
dependencies:
  - Volume_XXIII/00_Metadata.md (scope + live anchors)
  - runtime/capabilities/registry.py (capability declarations — requires_confirmation / requires_api / requires_authentication)
  - runtime/capabilities/capability.py (Capability schema, AUTH_REQUIRED health state)
  - tools/computer_control_agent.py (is_enabled() — the ELO_COMPUTER_CONTROL opt-in gate)
  - Volume_XXIII/02_Approval_Gates_and_Trust_Boundaries.md (sibling — the confirm-before-act runtime gate)
  - Volume_XXIII/03_Secrets_Memory_Protection_Threat_Model.md (sibling — secrets + threat model)
---

# Chapter 1: Authentication, Permissions & Sandboxing

## 1.0 Purpose

eLo is one mind expressed through many bodies, and some of those bodies can reach into
the person's real machine — open apps, move files, drive the mouse, read the screen.
The question this chapter answers is not "how do we stop eLo" but **"what is eLo allowed
to touch, and how does that permission become true rather than assumed?"**

Security here serves trustworthiness, not bureaucracy (Vol XXIII scope, ADR-0003). A
companion the person lets share their desktop must be *provably* incapable of the things
it should never do, and must ask before the things it may do. This chapter defines three
concentric rings:

1. **Authentication** — how eLo proves *who it is acting as* (the person / David / a seat)
   and how external services prove they are reachable and authorised.
2. **Permissions** — the declarative statement, per capability, of what class of action
   it is (read-only · reversible · confirm-required · authentication-required · dangerous).
3. **Sandboxing** — the hard boundary that makes a capability *unable* to act outside its
   declared scope, so a bug or a hallucinated intent cannot escalate into harm.

The dangerous-capability opt-in — `ELO_COMPUTER_CONTROL` — is the concrete edge case
this chapter grounds: a capability that is **present in the code but inert by default**,
and only becomes live through an explicit, out-of-band act by David.

## 1.1 Principle

Four rules govern authentication, permissions and sandboxing. They constrain every
capability and every embodiment.

**1.1.1 Default-deny for capability, default-allow for presence.** eLo is free to *be
present* — to watch, notice, wait, express — without any gate. But every capability that
*changes the world* starts denied and must be positively enabled. A capability that is
not declared, not enabled, and not authenticated cannot run. Absence of a grant is a
denial, never a maybe. (This is the `is_enabled()` / `is_available()` discipline already
in the code — see §1.3.)

**1.1.2 Capability class is declared, not inferred at the call site.** What kind of action
a capability is — read-only, reversible, confirm-required, dangerous — is a *property of
the capability declaration* (`runtime/capabilities/registry.py`), not something the router
decides ad hoc each turn. The gate reads the declaration; it does not re-classify. One
declaration, read everywhere (mirrors Vol XV: one world, read once).

**1.1.3 Dangerous capabilities are opt-in and out-of-band.** A capability that can act
irreversibly on the machine (computer control, terminal, delete) cannot be enabled by
anything eLo says, routes, or reasons — only by David, through a channel eLo does not
control (an `.env` flag, an OS permission grant). eLo can *request* the grant; it can
never *self-grant*. (Progressive Autonomy — authority is delegated by David, never
presumed.)

**1.1.4 Identity is single; authority is scoped.** There is One Brain and One Identity
(Runtime Invariant 1), so eLo does not have "accounts". But the *authority* eLo acts under
is scoped: acting for the person on the person's desktop is not the same grant as acting
on company state or on RESERVED matters. The identity never forks; the permission envelope
around a given action does.

## 1.2 What this is NOT

- This is **not** a login/user-account system. eLo is one being, not a multi-tenant app.
  "Authentication" here means (a) service reachability/credential presence and (b) the
  scope eLo is acting under — never per-user sign-in.
- This is **not** the runtime confirm-before-act gate. That is `execution_gate.py`, owned
  by Chapter 2. This chapter defines the *static* permission model (what a capability
  *is*); Chapter 2 defines the *dynamic* consent flow (asking before this specific act).
  They compose: a capability's declared class (§1.3) is what the runtime gate reads to
  decide whether to ask.
- This is **not** secret storage. `.env` handling and key hygiene are Chapter 3.

## 1.3 The Permission Model

Every capability eLo has or will have is declared once in
`runtime/capabilities/registry.py`, as a `Capability` (schema in
`runtime/capabilities/capability.py`). The permission-relevant fields already exist:

```
Capability (permission-relevant fields):
  requires_confirmation:   bool   # runtime confirm-before-act needed (→ Ch.2 gate)
  requires_api:            bool   # needs an external service credential to function
  requires_authentication: bool   # needs an authenticated/authorised session
  enabled:                 bool   # master on/off for this capability
  future:                  bool   # declared but not yet implemented → treated as denied
  health_state:            str    # UNKNOWN | ONLINE | AUTH_REQUIRED | ...
  response_style:          str    # "confirm" for gated capabilities
```

**Capability classes (derived from the declaration, MUST):**

| Class | Declaration signature | Runtime behaviour |
|---|---|---|
| **Read-only / presence** | none of the flags; reversible | runs immediately; no gate |
| **Reversible** | listed in `_IMMEDIATE_SAFE` (Ch.2) | runs immediately; user can undo |
| **Confirm-required** | `requires_confirmation=True`, `response_style="confirm"` | must pass Ch.2 confirm gate before executing |
| **Auth-required** | `requires_authentication=True` / `requires_api=True` | blocked until credential present + `health_state != AUTH_REQUIRED` |
| **Dangerous (opt-in)** | `requires_confirmation=True` **and** guarded by an env opt-in (`ELO_COMPUTER_CONTROL`) or `future=True` | inert unless explicitly enabled out-of-band, then still confirm-gated |

**Model rules (MUST):**

- `is_available()` already encodes the availability contract: a capability is available
  only if `enabled and not future and health_state ∈ {ONLINE, UNKNOWN}`. Nothing may
  bypass `is_available()` to reach an agent — the router queries the registry, it never
  imports agents directly (registry docstring). Preserve that: **the registry is the
  single choke point.**
- A capability declared `future=True` is *denied*, not merely absent — the person is told
  it "isn't connected yet" (`unavailable_reason()`), never that it silently failed. (Truth
  before fluency: `terminal` is `future=True` today and must read as not-yet, not as done.)
- `requires_authentication=True` with `health_state == AUTH_REQUIRED` surfaces as
  "I can do that once <capability> is authenticated" (`unavailable_reason()`), never as a
  fabricated success. Auth failure is reported, not hidden.
- No capability may be promoted a class *downward* (dangerous → reversible) at the call
  site. Reclassification is a canon change, not a code convenience.

## 1.4 Authentication — Two Kinds

**1.4.1 Service authentication (outward).** For capabilities with `requires_api` /
`requires_authentication`, "authenticated" means the credential is present (in `.env` —
Ch.3) *and* the service reported reachable. This is a health property, carried on
`health_state` (`AUTH_REQUIRED` when a needed credential is missing/invalid). eLo must
treat an unauthenticated service as **absent, not broken silently** — the same
anti-fabrication discipline as a stale world domain (Vol XV §1.1.3): report "Spotify isn't
authenticated" rather than invent a now-playing track.

**1.4.2 Authority scope (inward).** Every externally-visible action carries the *scope*
it is acting under. Three scopes, in ascending trust:

- **PERSON** — acting for the person on their own desktop/session (open an app, organise a
  folder). Default embodiment scope.
- **COMPANY / SEAT** — acting on company state (e.g. `company_state.json`). Read-only for
  eLo today; actions route through the Executive + David's L3 (Vision Spine, LAW-017).
- **RESERVED** — money · legal · safety · **robot force · magnetics · pump · thermal ·
  battery · pinch points**. eLo may never act in RESERVED scope on its own authority, only
  propose. **Updated 2026-08-10 (David L3): RESERVED now splits into two lanes** — see
  Chapter 2 §2.4.2 and `adr/LAW-017_Approval_Scope.md` §B4:
  - **SOFTWARE RESERVED** (desktop behaviour · canon · memory · personality) → **David is
    both L3 and LG-2.** No second reviewer; it is a personal tool. Still not satisfiable by
    an in-flow chat "yes" — still David, out of band.
  - **ROBOT HARDWARE RESERVED** (the force/magnetics/pump/thermal/battery/pinch-points set)
    → **David L3 + a real, separate LG-2 second review**, who must **not** be the person who
    designed the part. **The force-limiter / soft-stop scope must be DONE before anything is
    powered near David.**

The identity is one (Invariant 1); only the *scope envelope* differs. eLo never says "this
is a different eLo" — it says "that's a RESERVED decision, that's David's."

## 1.5 Sandboxing — Making Denial Structural

A permission model only helps if a mis-routed or hallucinated intent *cannot* reach beyond
its grant. Sandboxing turns "shouldn't" into "can't".

**Sandboxing rules (MUST):**

- **Capability isolation.** A capability agent may only perform the verbs it declares in
  the registry. `computer_control_agent` exposes exactly {click, move, type, key, scroll,
  screenshot, open}; it may not shell out, and `terminal` (shell) is a *separate*, still
  `future=True` capability — the two never collapse into one. One agent cannot borrow
  another's reach.
- **Filesystem scope.** Company/knowledge reasoning reads from curated sandboxes
  (`company_state.json`), **never a raw filesystem scan** (SITUATED_SELF_v1 §"permitted
  actions"). File operations act only on paths the person named this turn — no wildcard
  traversal, no "clean up everything".
- **Dangerous capability is inert by construction.** `ELO_COMPUTER_CONTROL` is checked by
  `is_enabled()` (`tools/computer_control_agent.py:40-42`), which reads the env flag and
  returns `False` unless it is `1/true/yes/on`. When off, `execute()` returns the refusal
  string (`computer_control_agent.py:388`) and the server surfaces "Computer control is off
  — add ELO_COMPUTER_CONTROL=1 to .env to enable it" (`server.py:1564`). The capability
  code exists; the *ability* does not, until David flips the flag **and** grants macOS
  Accessibility permission (WO-021). Two independent grants, both out-of-band.
- **No self-escalation.** Nothing in the response path may write `ELO_COMPUTER_CONTROL`,
  edit `.env`, or grant an OS permission. eLo requesting the grant is speech; performing it
  is David's. (Invariant: Verified Speech — eLo may *report* the capability is off and *ask*;
  it may not narrate itself into having enabled it.)

## 1.6 The ELO_COMPUTER_CONTROL Gate — Worked Example

The clearest instance of the whole model, end to end:

```
1. Person: "eLo, click the play button."
2. Router (registry) resolves capability = computer_control
     → declared: requires_confirmation=True, response_style="confirm",
       agent_module=tools.computer_control_agent, execution_priority=1
3. Agent gate: is_enabled() reads ELO_COMPUTER_CONTROL
     ├─ OFF (default): execute() → refusal; eLo says "Computer control is off —
     │                  add ELO_COMPUTER_CONTROL=1 to .env to enable it." STOP.
     └─ ON: continue
4. Runtime consent gate (Ch.2): action is confirm-required, not in _IMMEDIATE_SAFE
     → eLo describes the act, waits for a "yes"/"go"/"do it"
5. On confirmation: agent executes via macOS Accessibility (which itself required a
   separate OS grant); result is verified before eLo claims it happened (Verified Speech).
```

Two gates in series (opt-in enablement, then per-act confirmation) plus a third,
OS-level grant that eLo cannot touch. Default state is safe; every step toward action is
an explicit human act.

## 1.7 Interaction With Other Volumes

- **Chapter 2 (this volume)** consumes §1.3 capability classes: `requires_confirmation`
  and the `_IMMEDIATE_SAFE` set are exactly what the confirm-before-act gate reads.
- **Chapter 3 (this volume)** owns the `.env` credentials that §1.4.1 authentication
  depends on; the secret's *presence* is auth, the secret's *protection* is Ch.3.
- **Volume XV (Unified World State)** — the `environment` domain reports OS/permission
  state (e.g. screen-record permission, `vision.active`). §1.4.1 "service reachable"
  reads from that same freshness-annotated world, never a fresh inline probe.
- **Volume XII (Perception)** — screen reading is a *capability* subject to this model;
  the OS screen-recording permission is an out-of-band grant like Accessibility.
- **Executive Authority (Principles Inv. 2)** — capabilities are invoked through the one
  Executive; sandboxing guarantees no faculty acts around it.

## 1.8 Open Questions (for CA / David)

- **OQ-1.8.1 — ✅ DECIDED (David L3, 2026-08-10).** *Is `ELO_COMPUTER_CONTROL` a single flag,
  or should dangerous capabilities each get their own opt-in (e.g. `ELO_FILE_DELETE`, future
  `ELO_TERMINAL`)?* **Ruling: it stays a SINGLE SWITCH, not per-capability.** Rationale
  (David's): **simpler is safer for one user** — one flag is a thing David can hold entirely in
  his head, whereas a per-capability matrix creates unaudited combinations and a false sense of
  granular safety. The finer least-privilege argument is noted and rejected on those grounds.
  Do not add per-capability opt-in flags. (`CANON_RULINGS_2026-08-10.md` §XXIII;
  `adr/LAW-017_Approval_Scope.md` §B4; Ch.2 §2.4.3.)
- **OQ-1.8.2 (CA).** Should authority scope (PERSON / COMPANY / RESERVED) become an
  explicit field on `Capability`, or stay derived from category + LAW-017? Making it
  explicit hardens the RESERVED boundary but touches every declaration.
- **OQ-1.8.3.** Do we want a machine-readable *permission manifest* emitted from the
  registry (so David can audit "what can eLo touch right now" in one view), and if so is
  that a Ch.3 threat-model artifact or a governance report?
- **OQ-1.8.4 (David L3) — still OPEN, and now sharper.** For robot embodiments, physical
  actuation is RESERVED under LG-2 — and after the 2026-08-10 ruling that set is explicitly
  **force · magnetics · pump · thermal · battery · pinch points**, with LG-2 **retained** as a
  real separate review (§1.4.2, Ch.2 §2.4.2.b). Confirm that the *same* registry+gate model
  governs robot capabilities, with the dangerous-opt-in raised to **L3 + a real LG-2** rather
  than an env flag. Note the interaction with the now-decided single-switch ruling: **the
  single-switch simplification is a SOFTWARE-lane decision and must not be carried onto robot
  actuation.** `ELO_COMPUTER_CONTROL` never authorises physical actuation (Ch.2 §2.5.3).

## 1.9 Architecture References

- `runtime/capabilities/registry.py` — capability declarations (single choke point).
- `runtime/capabilities/capability.py` — `Capability` schema; `is_available()`,
  `unavailable_reason()`, `AUTH_REQUIRED`.
- `tools/computer_control_agent.py` — `is_enabled()` (env opt-in), refusal path.
- `server.py:1564` — user-facing "computer control is off" surface.
- `engineering/work_orders/WO-021_Computer_Control_Enable.md` — the two out-of-band grants
  (env flag + macOS Accessibility).
- `docs/architecture/00_DAVIDS_VISION_SPINE.md` — LAW-017 (actions route through Executive
  + David L3), sole-L3, RESERVED under LG-2.
- `docs/architecture/ARCHITECTURAL_PRINCIPLES.md` — Progressive Autonomy; Executive
  Authority; Verified Speech.
- Siblings: `Volume_XXIII/02_*`, `Volume_XXIII/03_*`.

---

```
Chapter 1 — Authentication, Permissions & Sandboxing
Status: READY FOR REVIEW
Files: Volume_XXIII/01_Authentication_Permissions_Sandboxing.md
Permission model: Included (5 capability classes, MUST rules)
Live anchors wired: registry.py · capability.py · computer_control_agent.py · server.py:1564
Opt-in dangerous-capability gate: ELO_COMPUTER_CONTROL worked example (§1.6)
Open questions: 4 (2 → David L3, 1 → CA)
```

READY FOR REVIEW
