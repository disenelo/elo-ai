# WO-CANON-XXIII — Security & Trust: enforce the software/hardware RESERVED split (LG-2 is DEFINED, not open)

**Owner:** Builder (eLo OS — `runtime/router/`, `runtime/capabilities/`, `tools/`) for the software half;
**Builder + Designer + LG-2 reviewer** for the robot-hardware half; **Architect** for the canon corrections.
**Priority:** P4 software hardening (Tier C) · **P0-blocking for any powered robot work** (see §B).
**Status:** OPEN — **REWRITTEN 2026-08-13 against David's ruling.** The previous version was built on the
premise *"the one genuinely-external item is to get David to define LG-2."* **That premise is dead: David
ruled on 2026-08-10.** LG-2 is defined for the software lane (it collapses into David) and retained for the
robot lane. This WO now implements the ruling instead of asking for it.

**Canon refs:** **`docs/architecture/CANON_RULINGS_2026-08-10.md` §XXIII (David L3, verbatim)** ·
**`docs/architecture/adr/LAW-017_Approval_Scope.md` Part B (B2 scopes · B3 sole L3 · **B4 the software/
hardware split** · B5 structural denial · B6 no self-escalation)** · Volume XXIII Ch.1
`01_Authentication_Permissions_Sandboxing.md`, Ch.2 `02_Approval_Gates_and_Trust_Boundaries.md`, Ch.3
`03_Secrets_Memory_Protection_Threat_Model.md` (threat matrix T-1…T-11) · ADR-0003 · D-F (sole writer) ·
D-LANES.

---

## THE RULING (David L3, 2026-08-10 — this WO is written against it, not around it)

Verbatim from `CANON_RULINGS_2026-08-10.md`, restated in `LAW-017` §B4:

1. **Software RESERVED collapses.** For **desktop behaviour · canon · memory · personality**, **David is
   both L3 and LG-2.** No second reviewer. It is a personal tool.
2. **Hardware RESERVED does NOT collapse.** The robot is a physical object. **LG-2 is RETAINED as a real,
   separate second review for the robot lane.**
3. **LG-2 must NOT be the person who designed the part.** The Chief Architect may hold LG-2 for design
   review.
4. **The LG-2 force-limiter / soft-stop scope MUST be DONE before anything is powered near David.** A hard
   precondition, not a checklist item.
5. **`ELO_COMPUTER_CONTROL` stays a single switch**, not per-capability — simpler is safer for one user.

**Robot hardware RESERVED set, as ruled:** force · magnetics · pump · **thermal · battery · pinch points**.
(The first four pre-date the ruling; the last three were added by it.)

**What this retires from the old WO:** OQ-2.7.3 (*"define LG-2"*) — **answered**. OQ-1.8.1 (*single flag vs
per-capability*) — **answered: single flag.** Neither is a blocker any more. Do not re-raise them.

## IRV — verified 2026-08-13

| Item | Finding |
|---|---|
| `LAW-017` | **Now exists** at `docs/architecture/adr/LAW-017_Approval_Scope.md` (it did not when the old WO was written — the audit's *"named authority defined nowhere"* is closed). Part B4 carries the ruling. |
| Volume XXIII vs the ruling | **STALE.** Vol XXIII still treats RESERVED as one flat set; it does not encode the software/hardware split, does not mention thermal/battery/pinch points, does not say *"LG-2 must not be the part's designer"*, and does not carry *"force-limiter DONE before anything is powered near David."* (`LAW-017` O-17.4 flags exactly this.) **Vol XXVII contains zero occurrences of `LG-2`.** |
| Scope enforcement in code | **`RESERVED` appears in no Python file** under `runtime/` or `tools/`. Authority scope is canon-only; nothing in the gate classifies or refuses on it. |
| Live anchors that DO exist | `runtime/router/execution_gate.py` (confirm-before-act) · `runtime/capabilities/registry.py` + `capability.py` (`is_available()`) · `tools/computer_control_agent.py` (`ELO_COMPUTER_CONTROL` opt-in) · `.env` secret store · `runtime/backend_router.py` (Groq→Cerebras→Ollama→Mock honest fallback). |
| Robot safety today | `avatar/safety_controller.py` is a clean state machine (`NORMAL / FREEZE / IDLE_POSTURE / EMERGENCY`) with **no force limiter, no soft-stop, and no thermal / battery / pinch-point monitor**. A grep for `force_limit` / `soft_stop` / `pinch` / `thermal` / `battery` across the runtime finds only a docstring example and a WO-classifier keyword list (`company_runtime/wo_policy.py:37`). **Ruling item 4 is therefore NOT satisfied.** |

## Problem / Goal

The gate, registry and secret discipline are largely live but **authority scope is not enforced anywhere in
code** — RESERVED is a word in canon, not a refusal in the router. And the robot lane, which is the half
that can physically hurt David, has an emergency state machine but none of the named safety scope the
ruling makes a precondition for power.

Goal: make the ruled split mechanically true — one flat gate becomes **two lanes with different rules** —
and make the robot lane's force-limiter/soft-stop scope an enforced precondition rather than an intention.

## Scope to DoD

### A. Software lane — RESERVED collapses to David (build now, ungated)

- **Encode the three authority scopes** (`LAW-017` B2) as a real classification the router computes
  *before* offering to act: `PERSON` · `COMPANY/SEAT` · `RESERVED`. Today the word does not exist in code.
- **PERSON**: in-flow confirmation via `execution_gate.py`; `_IMMEDIATE_SAFE` runs unasked. A PERSON-scope
  "yes" MUST NOT execute a COMPANY or RESERVED action (**authority ascends, never self-promotes**).
  Uncertain scope ⇒ escalate, never assume.
- **COMPANY/SEAT**: read-only for eLo today; actions route through the Executive + David's L3.
- **RESERVED (software: money · legal · safety · canon · memory · personality)**: **David alone is L3 and
  LG-2** — a single David approval is sufficient and no second reviewer is solicited. But **structural
  denial still holds** (`LAW-017` B5): **no `_IMMEDIATE_SAFE` path, no in-chat single-confirmation path,
  and it cannot be added to the gate's allow-list.** An L3 matter is escalated out of band; a "do it" in
  chat does not resolve it. eLo's role is: recognise it is RESERVED, refuse to act autonomously, route it
  to David, and **never assert a RESERVED outcome as decided**.
- **`ELO_COMPUTER_CONTROL` stays one switch.** Do not build per-capability opt-ins. Dangerous capability
  inert by construction: `is_enabled()` False unless the env flag is set; off ⇒ refusal string + the "add
  `ELO_COMPUTER_CONTROL=1` to `.env`" surface. **No self-escalation** (`LAW-017` B6): nothing in the
  response path may write that flag, edit `.env`, or grant an OS permission.
- **Registry as the single choke point:** the router queries the registry, never imports agents directly;
  nothing bypasses `is_available()`; `future=True` ⇒ denied via `unavailable_reason()`, never a silent
  failure; `requires_authentication` + `AUTH_REQUIRED` ⇒ *"I can do that once X is authenticated"*, never
  fabricated success. No capability reclassified downward at a call site.
- **Sandboxing:** an agent performs only its declared verbs; `computer_control_agent` =
  {click, move, type, key, scroll, screenshot, open} and may not shell out; `terminal` stays a separate
  `future=True` capability — the two never collapse. Filesystem: curated sandboxes only, paths named this
  turn, no wildcard traversal, `file_delete` → trash not hard-delete and never `_IMMEDIATE_SAFE`.
- **Gate mechanics:** `execute_pending()` runs AND clears in one step (no replay); the pending check runs
  before re-classification each turn (a "yes" is *consumed as confirmation*, not re-parsed); while
  `system_pending` the pipeline empties `agents`; a non-confirmation utterance calls `cancel_pending()`.
- **Secrets:** `.env` stays gitignored (a committed secret is P0: rotate, purge history, re-audit — T-1);
  no secret in canon/docs/WO/board/prompt/memory-candidate/spoken line/error string/learning buffer;
  missing credential ⇒ `AUTH_REQUIRED`; the fallback chain degrades honestly. One writer for the permanent
  store (Memory Faculty, D-F); Memory Candidates carry provenance; candidates from unverified speech are
  rejected; identity/values/truth immutable in memory.

### B. Robot hardware lane — LG-2 is REAL, and the force-limiter scope gates power ⚠ RESERVED

**This half is not a normal build item. Nothing in it may be closed by the Builder alone.**

- **Encode the hardware RESERVED set as ruled:** force · magnetics · pump · **thermal · battery · pinch
  points**. Any change touching these is RESERVED regardless of how small it looks.
- **Dual review is required and must be recorded:** **David L3 + LG-2**, where **LG-2 is a real, separate
  second reviewer who is NOT the person who designed the part.** The Chief Architect may hold LG-2 for
  design review. Record both sign-offs against the artefact; a single sign-off is not a pass.
- **Force-limiter / soft-stop scope — the power precondition.** Define and complete, under LG-2 review,
  before **anything is powered near David**:
  - force limiting per actuated joint (limit values, how they are enforced, what happens on breach)
  - soft-stop behaviour (controlled deceleration to a safe hold — distinct from the existing hard
    `EMERGENCY` all-actuators-off state)
  - thermal monitoring + a thermal cut-back path
  - battery monitoring + a safe-shutdown path
  - pinch-point identification for every mechanism (neck magnet housing · hip wishbone · forearm bladder)
    and the mitigation for each
  - **`avatar/safety_controller.py` is the natural host** (its existing `NORMAL / FREEZE / IDLE_POSTURE /
    EMERGENCY` ladder is sound), but the scope above **does not exist there today** — verified. This is a
    build, not a review of something built.
- **Sequencing (hard):** scope DONE + LG-2 review recorded **→ then** power. Not in parallel. Not
  "while we test on the bench next to David."
- **Authority re-establishes per embodiment** (T-11): robot force is RESERVED in every embodiment; nothing
  inherits a desktop-scope approval into the robot lane.

### C. Canon corrections (Architect lane — relayed, not built by the Builder)

- **Volume XXIII is stale against the ruling** (`LAW-017` O-17.4): it must encode the software/hardware
  split, add thermal/battery/pinch points to the RESERVED set, state *"LG-2 must not be the part's
  designer,"* and state the force-limiter precondition.
- **Volume XXVII contains zero occurrences of `LG-2`** — the governance volume does not know the approval
  model exists. Route to `WO-CANON-XXVII`.
- `LAW-017` **O-17.5 remains genuinely open**: LG-2's *composition* is settled for the robot **design**
  lane (the CA may hold it) but **not for the physical build/power lane — which is exactly where it
  matters.** This is the one item still needing David (see Gate).

## Files to TOUCH
- `runtime/router/execution_gate.py` · `runtime/router/pipeline.py` (scope classification + structural
  denial for RESERVED)
- `runtime/capabilities/registry.py` · `capability.py` (authority scope on the capability; permission
  manifest emitted from the registry)
- `tools/computer_control_agent.py` (single-switch discipline, no self-escalation)
- `avatar/safety_controller.py` (**§B — force limiter · soft-stop · thermal · battery · pinch-point
  monitors**; RESERVED, dual-signed)
- `tests/test_canon_xxiii_security.py` (new — the T-1…T-11 matrix)
- `docs/architecture/Volume_XXIII/*` — **Architect lane**, the §C corrections

## Files MUST-NOT-TOUCH
- `.env` (never written by code, never committed — T-1/B6)
- `runtime/executive.py` (FROZEN)
- Anything under §B **without** David L3 + a recorded LG-2 sign-off from someone who did not design the part
- The vault / permanent memory writer (D-F sole writer — this WO verifies it, never adds a second)

## Definition of Done
- Authority scope is **computed in code**, not implied: `RESERVED` exists as a real classification and a
  PERSON "yes" provably cannot execute a COMPANY or RESERVED action.
- Software RESERVED requires **David only** — and still has no `_IMMEDIATE_SAFE` and no single-confirm
  in-chat path.
- Hardware RESERVED requires **David L3 + a separate LG-2 who did not design the part**, recorded.
- Every T-1…T-11 threat has an enforced control verified **without David**; no self-escalation path exists;
  `ELO_COMPUTER_CONTROL` remains one switch.
- **§B: the force-limiter / soft-stop / thermal / battery / pinch-point scope is specified, built, and
  LG-2-reviewed BEFORE any powered test near David.** Until that is recorded, powered robot work does not
  start. **This WO does not, and cannot, mark that DONE** — that is David L3 + LG-2 in
  `COMPLETION_LOG.md`.
- Vol XXIII and Vol XXVII carry the split (Architect).

## Tests (`tests/test_canon_xxiii_security.py` — the T-1…T-11 matrix)
- **T-1** secret never committed/leaked (planted secret rejected; no secret in any surfaced string).
- **T-2** unauthorised irreversible action default-denied + gated (`agents == []` while pending).
- **T-3** dangerous capability off without the env flag + OS grant; **no self-grant path exists** (assert
  nothing in the response path writes `ELO_COMPUTER_CONTROL` or `.env`).
- **T-4** consent not replayed across turns (one pending slot; consumed on execute; cleared on non-confirm).
- **T-5** **RESERVED has no safe and no single-confirm path** — and a PERSON-scope "yes" does not execute a
  RESERVED action (scope does not self-promote).
- **T-5b (new, from the ruling)** a **software** RESERVED item requires David and solicits **no** second
  reviewer; a **hardware** RESERVED item (force · magnetics · pump · thermal · battery · pinch points)
  requires **two** recorded sign-offs and is refused with one.
- **T-5c (new)** an LG-2 sign-off whose signer is the part's designer is **rejected**.
- **T-5d (new, the power precondition)** a powered-robot action is **refused** while the force-limiter /
  soft-stop scope is not recorded complete. *(This test fails today — verified: the scope does not exist in
  `avatar/safety_controller.py`. That failure is the point.)*
- **T-6** forged/unverified memory not written (sole writer, verified provenance).
- **T-7** personality/value drift not written as memory.
- **T-8** no fabricated success on tool failure (`AUTH_REQUIRED` surfaced honestly).
- **T-9** perception gated + OS grant (D-PRESENCE).
- **T-10** no faculty acts around the Executive / injects into a peer.
- **T-11** authority re-established per embodiment (a desktop approval never carries into the robot lane).
- Plus the Ch.1 §1.6 worked `ELO_COMPUTER_CONTROL` example as an integration script.

## Dependencies + blocked-by
- **NOT blocked by "define LG-2"** — that premise is retired. The software half (§A) is **buildable now**
  (board: *"▶ RELEASED 2026-08-10"*).
- **§B is blocked by** David L3 + a named LG-2 for the **physical build/power** lane (`LAW-017` O-17.5 — the
  one genuinely-open item; the ruling names the CA for *design* review only). **No powered work proceeds
  without it.**
- Cross-volume: Vol VIII (sole writer D-F, provenance) · Vol XVI (no direct LTM write; Executive sole
  external authority) · **Vol XXVII** (the pre-commit/CI secret check lands there — OQ-3.6.3; and XXVII must
  learn the word `LG-2`) · Vol XI/XIII (robot embodiment inherits, never re-litigates, the scope rules).
- CA (not David) on: authority scope as a `Capability` field (OQ-1.8.2), the machine-readable permission
  manifest (OQ-1.8.3), per-session pending state (OQ-2.7.2), Memory-Candidate typed provenance (OQ-3.6.2).
- **Gate:** §A ungated. **§B RESERVED — David L3 + separate LG-2, and the force-limiter/soft-stop scope
  before power.** Architect promotes Vol XXIII only after CA acceptance + the §C corrections land.

## Lane
Builder (Python — scope classification, gate/registry/secret hardening, permission manifest). Builder +
Designer under LG-2 review for §B. Architect authors the Vol XXIII / Vol XXVII corrections (Markdown) and
carries `LAW-017` O-17.5 (LG-2 for the physical build/power lane) to David. David provides that one
genuinely-external item — and only that one.
