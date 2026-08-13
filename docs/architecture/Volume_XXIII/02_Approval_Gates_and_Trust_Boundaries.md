---
chapter: 2
title: "Approval Gates & Trust Boundaries — Confirm Before Act"
volume: XXIII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
received: 2026-08-10
dependencies:
  - runtime/router/execution_gate.py (the confirm-before-act gate — primary anchor)
  - runtime/router/pipeline.py (Stage 06 wiring — where the gate runs)
  - Volume_XXIII/01_Authentication_Permissions_Sandboxing.md (capability classes the gate reads)
  - docs/architecture/00_DAVIDS_VISION_SPINE.md (LAW-017, sole L3, RESERVED under LG-2)
  - docs/architecture/ARCHITECTURAL_PRINCIPLES.md (Executive Authority, Verified Speech, Progressive Autonomy)
---

# Chapter 2: Approval Gates & Trust Boundaries

## 2.0 Purpose

There is a moment between eLo *deciding* to act on the world and the world *actually
changing*. This chapter governs that moment. It defines:

1. The **confirm-before-act gate** — the runtime mechanism (`execution_gate.py`) that
   holds a world-changing action until the person says "go".
2. The **human approval gates** — where a human, and specifically *which* human authority,
   must stand between intent and effect. David is sole L3.
3. **RESERVED actions** — the narrow set (money · legal · safety · **robot force · magnetics ·
   pump · thermal · battery · pinch points**) that no confirmation-in-the-flow can satisfy.
   **Since David's 2026-08-10 ruling these split into two lanes** (§2.4.2): **software
   RESERVED** — desktop behaviour, canon, memory, personality — where **David is both L3 and
   LG-2**; and **robot hardware RESERVED**, where **LG-2 is retained as a real, separate second
   review** because the robot is a physical object.
4. **Trust boundaries** — the seams between faculties, tools, and embodiments across which
   authority does not silently flow.

This is the enforcement of two Principles at once: **Executive Authority** (one authority
for externally-visible action) and **Human approval at governance gates** (money, legal,
safety, identity are David's L3, always). The gate is where "eLo wants to" becomes "eLo
may".

## 2.1 Principle

**2.1.1 No irreversible external effect without a fresh human "yes".** A reversible,
read-only action may run on eLo's own decision. Anything that changes the person's machine
in a way they'd want to have approved waits for confirmation *this turn*. Consent is not
inherited from a previous turn (§2.3.4).

**2.1.2 The gate reads the declared class; it does not re-decide it.** Whether an action
needs confirmation is a property of the capability (Ch.1 §1.3) surfaced to the gate as the
`_IMMEDIATE_SAFE` set vs everything else. The gate is a *checkpoint*, not a *classifier*.

**2.1.3 One pending action at a time.** The gate holds exactly one pending action. A new
gated action, or any non-confirmation utterance, clears the stale one — consent can never
bleed across intents. (This is exactly what `execution_gate._pending` + `pipeline.py`'s
`cancel_pending()` already enforce.)

**2.1.4 Authority ascends; it never self-promotes.** PERSON-scope consent (a "yes" in
chat) authorises PERSON-scope actions only. COMPANY and RESERVED actions escalate to David
L3 (and LG-2 for RESERVED). eLo can carry a request up the ladder; it can never act as if
it stood a rung higher. (Progressive Autonomy: eLo coordinates, David authorises.)

**2.1.5 Speak only what the body confirmed.** After execution, eLo asserts the outcome only
once it is verified (Verified Speech / Embodied Truth). "I opened Spotify" follows the app
actually opening, never precedes it. A failed action is reported as failed, never narrated
as done.

## 2.2 The Confirm-Before-Act Gate (execution_gate.py)

The live gate is `runtime/router/execution_gate.py`. Its contract, as it exists:

```
gate(action, arg) -> {execute, confirmation, why}
    if action in _IMMEDIATE_SAFE:  return {execute: True,  why: "safe_immediate"}
    else:                          store pending(action, arg, desc)
                                   return {execute: False, confirmation: desc,
                                           why: "requires_confirm"}
```

Supporting surface (all present today):

- `_IMMEDIATE_SAFE` — the reversible/read-only allow-list:
  `{folder_list, folder_organise, screenshot, dark_mode, light_mode, window_focus,
  volume, brightness}`. These run with no confirmation because the person can trivially
  undo them.
- `_CONFIRM` / `_CANCEL` — the natural-language vocabularies that count as "yes" / "no"
  ("go ahead", "do it", "yep" … / "cancel", "stop", "never mind" …).
- `_DESCRIPTIONS` — human-readable confirm strings per action ("open {arg}", "trash
  {arg}", "move {arg}" …) so eLo says *what* it will do, in plain words, before doing it.
- `has_pending()` · `should_execute(text)` · `should_cancel(text)` · `execute_pending()`
  · `cancel_pending()` — the state machine around the single pending slot.

**Gate rules (MUST):**

- Only `_IMMEDIATE_SAFE` actions bypass confirmation. Every other action MUST be described
  and MUST wait. Adding to `_IMMEDIATE_SAFE` is a **canon decision** (it widens what eLo
  does unasked), not a code convenience — see OQ-2.7.1.
- The confirm string MUST describe the *actual* action and arg (`_describe()`), never a
  vague "do this?" — the person consents to a specific, legible act.
- `execute_pending()` runs the action **and clears state** in one step; a consumed
  confirmation cannot be replayed.
- Destructive file actions (`file_delete` → "trash {arg}", `file_move`, `file_rename`) are
  correctly *outside* `_IMMEDIATE_SAFE` and MUST remain confirm-gated. `file_delete` maps
  to *trash*, not hard-delete — reversibility is designed in.

## 2.3 Wiring — Where The Gate Runs (pipeline.py)

The gate is Stage 06 of the router pipeline (`runtime/router/pipeline.py`). The turn flow,
as wired:

```
Top of turn:
  if has_pending():
      if should_execute(raw):  → execute_pending(); return system_result   # the "yes"
      else:                    → cancel_pending()   # anything else clears the stale pending
  ... Stages 01–05 (normalise → typo → matrix → intent → route) ...
  Stage 06 (system / file_ops intents, agent == "system"):
      detected = system_agent.detect(query)
      gate_result = gate(action, arg)
      if not gate_result["execute"]:
          system_pending = True
          system_desc    = gate_result["confirmation"]
          agents = []          # DO NOT execute this turn — wait for the "yes"
```

**Wiring rules (MUST):**

- The pending-check runs **before** re-classification each turn, so a "yes" is consumed as
  confirmation of the held action and not re-parsed as a new intent (§2.1.3).
- When `system_pending` is True the pipeline **empties `agents`** — the action does not run
  and eLo instead speaks `system_desc`. This is the structural guarantee that a gated
  action cannot leak through as a side-effect.
- A non-confirmation utterance while pending calls `cancel_pending()` so the confirm prompt
  does not "bleed into subsequent turns" (pipeline comment) — matches §2.1.3.
- The learning buffer records the gated turn as `outcome="confirmed"` for diagnostics; the
  gate's decision, not its own guess, is the recorded truth.

## 2.4 Human Approval Gates — Who Must Say Yes

> ✅ **REWRITTEN 2026-08-10 to carry David's L3 ruling** (`CANON_RULINGS_2026-08-10.md`
> §XXIII; canonised in `adr/LAW-017_Approval_Scope.md` §B4). The previous text treated
> RESERVED as **one flat set** requiring David L3 + LG-2 across the board. That is **no longer
> canon.** RESERVED now splits on **software vs. hardware**, because the two differ in a way
> that matters physically. Nothing below is a relaxation of the robot lane — it is a tightening.

Not every "yes" is equal. The gate in §2.2 collects the *person's* consent for PERSON-scope
acts. Higher gates exist and are **not** satisfiable by an in-flow chat confirmation.

**2.4.1 David L3 (governance gate).** Money, legal, safety, and identity-level decisions
are David's, always (Principle: Human approval at governance gates; Vision Spine: sole L3).
eLo may propose; David disposes. The runtime confirm-gate does **not** stand in for L3 —
an L3 matter is escalated to David out of band, not resolved by a "do it" in chat.

### 2.4.2 ⚖ THE SPLIT — software RESERVED collapses; hardware RESERVED does not

**David's ruling, 2026-08-10, stated as the rule this volume enforces:**

| Lane | What it covers | Who must say yes | LG-2? |
|---|---|---|---|
| **SOFTWARE RESERVED** | **desktop behaviour · canon · memory · personality** | **David** | **NO — David is BOTH L3 and LG-2.** No second reviewer. |
| **ROBOT HARDWARE RESERVED** | **force · magnetics · pump · thermal · battery · pinch points** | **David L3** | **YES — LG-2 RETAINED as a real, separate second review.** |

**2.4.2.a Software RESERVED collapses.** For **desktop behaviour, canon, memory and
personality**, **David is both L3 and LG-2.** There is no second reviewer, and one is not to be
invented. **Rationale (David's, verbatim in effect): it is a personal tool** — one user, one
owner, one person whose companion this is. A second-reviewer requirement on eLo's own
behaviour, canon, memory or personality would be governance theatre: there is no second
stakeholder for it to protect, and it would only slow the one person it belongs to. David's
single "yes" is the complete gate here.

**2.4.2.b Robot HARDWARE RESERVED does NOT collapse — the robot is a physical object.** It
has magnets, actuators, force, a pump, thermal load, a battery, and pinch points. It can hurt
someone in a way software cannot. **LG-2 is RETAINED as a real, separate second review for the
robot lane** — not a formality, not a checkbox, not David reviewing his own work under a second
name. The RESERVED hardware set, as ruled, is:

```
force · magnetics · pump · thermal · battery · pinch points
```

(**thermal · battery · pinch points** were added by David's 2026-08-10 ruling and were absent
from this volume's earlier RESERVED set — that omission is corrected here.)

**2.4.2.c LG-2 must NOT be the person who designed the part.** A second review by the designer
is not a second review. **The reviewer must be someone other than whoever designed the thing
under review.** The Chief Architect may hold LG-2 for **design** review. The physical build /
power lane's LG-2 composition is still open — see OQ-2.7.3.

**2.4.2.d HARD PRECONDITION — force-limiter / soft-stop scope must be DONE before anything is
powered near David.** This is not a checklist item and not a milestone to be traded against
schedule. **Nothing is energised in David's physical proximity until the LG-2 force-limiter /
soft-stop scope is complete and reviewed.** No demo, no "quick test", no partial power-up. If
the scope is not done, the answer is no — and eLo, the seats, and the Architect all state that
plainly rather than negotiating it.

**2.4.3 `ELO_COMPUTER_CONTROL` stays a single switch.** ✅ **DECIDED — David L3, 2026-08-10.**
The dangerous-capability opt-in is **one flag, not per-capability.** **Rationale: simpler is
safer for one user** — a single switch is a thing David can hold entirely in his head and
reason about in one step, whereas a matrix of per-capability flags creates states nobody has
audited and a false sense of granular safety. This closes Ch.1 OQ-1.8.1. (The switch is still
an opt-in *pre-gate*: when it is off the gate is never reached; when it is on, every action is
still confirm-gated per §2.2.)

**Approval-gate rules (MUST):**

- eLo MUST classify scope *before* offering to act — and, within RESERVED, MUST classify
  **which lane** (software or robot hardware), because they carry different gates. If scope or
  lane is uncertain, eLo escalates rather than proceeds (default-deny, Ch.1 §1.1.1).
- A PERSON-scope "yes" MUST NOT execute a COMPANY or RESERVED action of either lane.
- **All** RESERVED actions — both lanes — have **no** `_IMMEDIATE_SAFE` path and **no**
  single-confirmation-in-chat path, and cannot be added to the gate's allow-list. The collapse
  in §2.4.2.a removes the *second reviewer* for software RESERVED; it does **not** make software
  RESERVED satisfiable by an in-flow "go ahead". It is still David, out of band.
- For robot-hardware RESERVED, eLo's role is strictly to (a) recognise the matter is RESERVED,
  (b) refuse to act autonomously, (c) route it to David **with the LG-2 second-review
  requirement stated**, including the designer-exclusion (§2.4.2.c).
- eLo never *asserts* an L3/RESERVED outcome as decided ("I've committed the print") — it
  reports the state ("that's a force-reserved build; it needs your L3 and a separate LG-2
  review by someone who didn't design the part"). Verified Speech applies to authority as much
  as to action.
- **The software collapse never travels to the robot lane.** No precedent set by David
  single-handedly approving a canon, memory, personality or desktop-behaviour change may be
  cited as grounds for single-handedly approving anything on the force/magnetics/pump/thermal/
  battery/pinch-point list. These are different lanes on purpose.

**Cross-reference:** `docs/architecture/adr/LAW-017_Approval_Scope.md` — **Part B §B4** is the
canon home of this split (it carries David's 2026-08-10 L3 ruling); §B2 holds the three
authority scopes; §B5 the structural denial of RESERVED; §B6 no-self-escalation. LAW-017 is
the authority this volume's approval model cites, and until 2026-08-10 it had no definition in
the repo — it does now.

## 2.5 Trust Boundaries

A trust boundary is a seam across which authority, data, or capability does **not** flow
implicitly. Three matter here:

**2.5.1 Faculty ↔ Faculty.** All inter-faculty traffic passes the canonical envelope
(Faculty Bus, ADR-0001); no faculty injects content into another or invokes another's
capability directly. A faculty cannot "reach through" a peer to act — it emits an envelope
and the Executive arbitrates. Externally-visible action is the Executive's alone (Executive
Authority). The gate therefore sits on the Executive's action path, not inside a faculty.

**2.5.2 Executive ↔ Tool/Agent.** The Executive reaches tools only through the capability
registry (Ch.1) and only after the gate. A tool cannot self-invoke, cannot escalate its own
class, and cannot enable a sibling dangerous capability. The `_IMMEDIATE_SAFE` allow-list is
the *entire* set of tool actions permitted without a human in the loop — nothing outside it
is trusted to run unasked.

**2.5.3 Embodiment ↔ Embodiment.** One Brain, many bodies (Invariant 1) — but a grant in
one body is not automatically a grant in another. `ELO_COMPUTER_CONTROL` on the desktop does
not authorise physical actuation on the robot; robot force/magnetics is RESERVED (§2.4.2)
regardless of any desktop opt-in. Identity crosses embodiments freely; *authority to act*
is re-established per embodiment against that embodiment's capability set. The person must
never feel two eLos — but the safety envelope is per-body.

## 2.6 Interaction With Other Volumes

- **Chapter 1 (this volume)** supplies the capability classes and the `_IMMEDIATE_SAFE`
  membership the gate reads; the dangerous-opt-in (`ELO_COMPUTER_CONTROL`) is a *pre-gate*
  — if the capability is disabled the gate is never reached (Ch.1 §1.6).
- **Chapter 3 (this volume)** — the threat model treats a bypassed or replayed confirmation
  as a top-tier threat; §2.2/§2.3 rules are the mitigations it audits against.
- **Volume XV (Unified World State)** — the gate's confirm string and eLo's post-action
  claim both read the frozen world (e.g. "is the app actually frontmost now?") rather than
  re-probing; Verified Speech (§2.1.5) is checked against `LiveWorldState`.
- **Executive / Spine (16_spine_runtime)** — the gate is a response-path stage; it composes
  with, and never bypasses, the single Executive decision per turn.
- **Learning (ADR-Exec-005)** — eLo learns only from *verified* outcomes; a gated action
  that never executed produces no learning signal beyond the diagnostic record.

## 2.7 Open Questions (for CA / David)

- **OQ-2.7.1 (David L3).** Is `_IMMEDIATE_SAFE` correctly scoped? It currently includes
  `folder_organise` (moves files around) and `window_close` is *not* in it but
  `window_focus` is. Confirm that `folder_organise` is reversible enough to run unasked, or
  demote it to confirm-required. **Flagged — this is exactly the "what eLo does without
  asking" line.**
- **OQ-2.7.2 (CA).** The gate holds *one* pending action globally (module-level `_pending`).
  For multi-embodiment / concurrent surfaces, should pending state be per-session/per-body
  to avoid one body's confirmation resolving another body's pending action? (Trust-boundary
  §2.5.3 implication.)
- **OQ-2.7.3 (David L3) — PARTIALLY ANSWERED 2026-08-10; the load-bearing half is still open.**
  How is LG-2 (the second reviewer for robot-hardware RESERVED) constituted — a named human, a
  second agent under human sign-off, or David-plus-one?
  **Answered by the ruling:** LG-2 is **not required at all** for software RESERVED (David is
  both — §2.4.2.a); and **the Chief Architect may hold LG-2 for robot *design* review**, subject
  to the designer-exclusion (§2.4.2.c).
  **Still open — and this is where it matters:** who holds LG-2 for the **physical build /
  power lane**, i.e. the review that must be DONE before anything is powered near David
  (§2.4.2.d). The CA-holds-design-review answer does not cover it. **Needs David.**
- **OQ-2.7.4.** Should the confirm vocabulary (`_CONFIRM`/`_CANCEL`) be hardened against
  accidental affirmation (e.g. "ok" mid-sentence)? Current match is exact-phrase after
  strip; document whether that is sufficient or a threat-model item for Ch.3.

## 2.8 Architecture References

- `runtime/router/execution_gate.py` — the confirm-before-act gate (primary anchor).
- `runtime/router/pipeline.py` — Stage 06 wiring; top-of-turn pending resolution.
- `tools/system_agent.py` — `detect()` (action, arg) feeding the gate; `execute()` invoked
  by `execute_pending()`.
- `runtime/capabilities/registry.py` — capability class the gate honours (Ch.1).
- `docs/architecture/adr/LAW-017_Approval_Scope.md` — **canon home of the approval model**;
  Part B §B4 carries David's 2026-08-10 software/hardware split verbatim. (Written 2026-08-10;
  LAW-017 was previously cited ~25× with no definition in the repo.)
- `docs/architecture/CANON_RULINGS_2026-08-10.md` §XXIII — David's L3 ruling, primary source.
- `docs/architecture/00_DAVIDS_VISION_SPINE.md` — LAW-017 token, sole L3, RESERVED under LG-2.
- `docs/architecture/ARCHITECTURAL_PRINCIPLES.md` — Executive Authority; Verified Speech;
  Embodied Truth; Progressive Autonomy.
- Siblings: `Volume_XXIII/01_*`, `Volume_XXIII/03_*`.

---

```
Chapter 2 — Approval Gates & Trust Boundaries
Status: READY FOR REVIEW
Files: Volume_XXIII/02_Approval_Gates_and_Trust_Boundaries.md
Primary anchor: runtime/router/execution_gate.py (documented as-built) + pipeline.py Stage 06
Human approval gates: PERSON confirm · David L3 · RESERVED — SPLIT (§2.4.2, David L3 2026-08-10):
  SOFTWARE RESERVED (desktop behaviour · canon · memory · personality) → David is BOTH L3 and LG-2
  ROBOT HARDWARE RESERVED (force · magnetics · pump · thermal · battery · pinch points)
    → David L3 + a REAL separate LG-2, who must NOT be the part's designer.
    HARD PRECONDITION: force-limiter / soft-stop scope DONE before anything is powered near David.
  ELO_COMPUTER_CONTROL = single switch, not per-capability (closes OQ-1.8.1).
Canon home of the approval model: adr/LAW-017_Approval_Scope.md §B4
Trust boundaries: faculty · tool · embodiment (§2.5)
Open questions: 4 (OQ-2.7.1 David L3 · OQ-2.7.2 CA · OQ-2.7.3 PARTIAL — physical build/power-lane
  LG-2 still needs David · OQ-2.7.4)
```

READY FOR REVIEW
