---
id: LAW-017
title: "Approval Scope & Runtime Composition — authority routes through the Executive; David is sole L3; RESERVED needs a second review"
status: ACCEPTED · CANON · LAW  (Part B §B4 carries David's L3 ruling of 2026-08-10; Part A is reconstructed — see PROVENANCE)
date: 2026-08-10                 # date this document was written
ratified: 2026-08-10             # for §B4 only (CANON_RULINGS_2026-08-10.md, David L3). Part A: see PROVENANCE.
owner: David Charles
author: Claude (Lead Architect)
supersedes: []
related: [ADR-Exec-001, ADR-Exec-002, ADR-0001, D-M (Change Control), D-I (Builder write-scope), Ruling XXIII (2026-08-10)]
canon_home: this document
---

# LAW-017 — Approval Scope & Runtime Composition

> **Why this file exists.** `LAW-017` is cited **25 times** across the canon — including as the
> named authority for **Volume XXIII's entire approval model** (§1.4.2 authority scope, §2.4
> approval gates) and for four Work Orders — and it had **no definition inside the repo.** Volume
> XXIII cites *"`00_DAVIDS_VISION_SPINE.md` — LAW-017"*, but the Vision Spine only **uses** the
> token in passing (line 43); it never defines it. This document closes that hole.

---

## PROVENANCE — read this first (two different laws share one ID)

**A definition WAS found — outside the repo.** `Output/DISENELO_UNIVERSAL_RUNTIME_EA3.md` §3
defines LAW-017 as **"Runtime Composition (Amendment 3)"**. That is a real, quotable definition,
and it matches roughly half the citations (`WO-EA2-1`, `WO-EA2-2`, `WO-INT7-HEAT`,
`AGENT_HANDOFF_PACKETS`, `DISPATCH_BOARD` — all of which cite LAW-017 for *"additive only / must
not modify the frozen kernel / observer surfaces must not write state directly"*).

**But the Volume XXIII citations mean something else.** Vol XXIII Ch.1 §1.4.2 and Ch.2 §2.4 cite
LAW-017 for *"actions route through the Executive + David's L3"*, *"sole L3"*, and *"RESERVED under
LG-2"* — an **approval-scope** law, not a runtime-composition law. That content is real canon
(Vision Spine + `ARCHITECTURAL_PRINCIPLES.md` §Governance), but it was **never LAW-017's stated
text**. One ID, two meanings, drifted apart.

**How this document handles it — conservatively:**
- **Part A** restates the found EA-3 definition **verbatim**, unchanged.
- **Part B** states the approval-scope rules the canon actually relies on, sourced to their real
  origins (Vision Spine · Principles · Vol XXIII · David's 2026-08-10 ruling), so the 25 citations
  resolve to something true.
- **Nothing is invented.** Where the two halves are only conventionally linked, that is said.

⚠️ **`LAW-001`–`LAW-016` DO NOT EXIST.** A repo-wide sweep of `elo-ai/` **and** `Output/` finds no
LAW-001 through LAW-016 anywhere — the only hits are the audit noting their absence. "017" appears
to be an arbitrary number inherited from the EA-3 document, not the seventeenth of a series.
**Recommendation (needs David — do not act without it):** keep the ID `LAW-017` (renumbering breaks
25 citations for cosmetic gain) and record in the canon that the `LAW-NNN` series has exactly one
member. **Do NOT back-fill sixteen laws to make the numbering look complete.** The alternative —
re-issuing this as `ADR-Gov-001` with `LAW-017` as a permanent alias — is cleaner but costs a
citation sweep. **David's call.**

---

## PART A — Runtime Composition (the found EA-3 definition, verbatim)

> **LAW-017.** A runtime **may**: observe · extend · compose · specialise.
> A runtime **may never**: duplicate Executive authority · bypass the Faculty Bus · mutate frozen
> kernel primitives.
> **Every runtime is a composition of canonical runtime primitives.**
>
> — `Output/DISENELO_UNIVERSAL_RUNTIME_EA3.md` §3 (Amendment 3)

**Amendment 7 (same source, §7) — the clause cited as "LAW-017 Amendment 7":**

> Dashboards observe; they never control.
> `RUNTIME → EVENTS → OBSERVER → DASHBOARD (Presence Faculty)`
> `DASHBOARD → (action request) → EXECUTIVE → Approval Faculty → state change`
> A dashboard **cannot alter runtime state directly.** When you tap **Approve**, it does not write
> state — it **emits an action request** (an Envelope, `payload.type: approval_request`) to the
> Executive, which routes it to the Approval Faculty, which performs the L3 approval and updates
> the State Model. The dashboard then re-renders from the new state.

**Consequences of Part A:** it encodes the `FREEZE_V1_LOCK` discipline (additive composition only),
prohibits nested executives, and is why every observer surface writes *requests* rather than state.

## PART B — Approval Scope (the rules the canon relies on)

**B1 — Authority routes through the Executive.** No surface, dashboard, faculty, tool or agent
effects an externally visible change on its own. It emits a request; the Executive is the
authority. (This is Part A + ADR-Exec-001 Executive Authority stated as one rule — it is the
sentence Vol XXIII §1.4.2 attributes to LAW-017.)

**B2 — Three authority scopes, ascending.** *(Vol XXIII Ch.1 §1.4.2 — as-written canon.)*

| Scope | Meaning | Gate |
|---|---|---|
| **PERSON** | acting for David on his own desktop/session (open an app, organise a folder) | in-flow confirmation (`execution_gate.py`); `_IMMEDIATE_SAFE` runs unasked |
| **COMPANY / SEAT** | acting on company state (`company_state.json`) | **read-only for eLo today**; actions route through the Executive + David's L3 |
| **RESERVED** | money · legal · safety · robot magnetics/force/pump | **David L3 + a second review (LG-2)** — see B4 |

**Authority ascends; it never self-promotes.** A PERSON-scope "yes" authorises PERSON-scope actions
only. eLo can carry a request up the ladder; it can never act as if it stood a rung higher.
Identity is one across scopes — only the *scope envelope* differs. eLo never says "this is a
different eLo"; it says *"that's a RESERVED decision, that's David's."*

**B3 — David is the sole L3.** Money, legal, safety and identity-level decisions are David's,
always. The runtime confirm-gate does **not** stand in for L3 — an L3 matter is escalated out of
band, never resolved by a "do it" in chat. (`ARCHITECTURAL_PRINCIPLES.md` §Governance; Vision
Spine; D-M Change Control.)

**B4 — The software / hardware split.** ✅ **DECIDED — David L3, 2026-08-10**
(`CANON_RULINGS_2026-08-10.md` §XXIII, verbatim source):

- **Software RESERVED collapses.** For **desktop behaviour · canon · memory · personality**,
  **David is both L3 and LG-2.** No second reviewer is needed — it is a personal tool.
- **Hardware RESERVED does NOT collapse.** **The robot is a physical object** — magnets, actuators,
  force, pump, thermal, battery, pinch points. **LG-2 is RETAINED as a real, separate second review
  for the robot lane.**
- **LG-2 must NOT be the person who designed the part.** The Chief Architect may hold LG-2 for
  design review.
- **The LG-2 force-limiter / soft-stop scope MUST be DONE before anything is powered near David.**
  This is a hard precondition, not a checklist item.
- `ELO_COMPUTER_CONTROL` stays a **single switch** (not per-capability) — simpler is safer for one
  user.

**Robot hardware RESERVED set (as ruled):** force · magnetics · pump · **thermal · battery · pinch
points**. (The first four appear in the pre-existing Vol XXIII text; thermal/battery/pinch points
were added by David's ruling and are **not yet reflected in Volume XXIII** — see OPEN.)

**B5 — Structural denial.** RESERVED actions have **no** `_IMMEDIATE_SAFE` path and **no**
single-confirmation path, and cannot be added to the gate's allow-list. eLo's role in RESERVED
scope is strictly to (a) recognise the matter is RESERVED, (b) refuse to act autonomously, (c)
route it to David **with the second-review requirement stated**. eLo never *asserts* an
L3/RESERVED outcome as decided ("I've committed the print") — it reports the state.

**B6 — No self-escalation.** Nothing in the response path may write `ELO_COMPUTER_CONTROL`, edit
`.env`, or grant an OS permission. eLo requesting a grant is speech; performing it is David's.

## How it is enforced

| Mechanism | Where |
|---|---|
| Confirm-before-act gate; single pending slot; consent never inherited | `runtime/router/execution_gate.py` · `runtime/router/pipeline.py` Stage 06 |
| Capability class as single choke point (`is_available()`) | `runtime/capabilities/registry.py` · `capability.py` |
| Dangerous capability inert by construction (env opt-in + OS grant) | `tools/computer_control_agent.py::is_enabled()` · WO-021 |
| Observer surfaces write requests, never state | `blender/company_actions.json` pattern — WO-EA2-1 / WO-EA2-2 |
| Additive-only composition; frozen kernel untouched | `FREEZE_V1_LOCK` · D-I (Builder write-scope) · WO-INT7-HEAT |
| Change control: Propose → Spec → **Gate 1** → build → verify → **Gate 2** | D-M · `engineering/work_orders/CHANGE_CONTROL.md` |
| Robot force/magnetics/pump/thermal stays RESERVED after the 08-10 ruling | `CANON_RULINGS_2026-08-10.md` §"Net effect" |

## Citations (25 references repo-wide)

- `Volume_XXIII/01_Authentication_Permissions_Sandboxing.md` §1.4.2, §1.9, OQ-1.8.2 — authority scope.
- `Volume_XXIII/02_Approval_Gates_and_Trust_Boundaries.md` frontmatter, §2.4, §2.8 — approval gates.
- `Volume_XXIII/00_Metadata.md`; `WO-CANON-XXIII.md`.
- `00_DAVIDS_VISION_SPINE.md` line 43 (company awareness is read-only).
- `01_PRINCIPLES.md` line 106 (consistency check vs EA-0/EA-3).
- `WO-EA2-1_Company_State_Writer.md`, `WO-EA2-2_Presence_Panel_And_Requests.md` (Amendment 7),
  `WO-INT7-HEAT_Cognitive_Heatmap.md`, `AGENT_HANDOFF_PACKETS.md`, `DISPATCH_BOARD.md` (×2).
- `Output/DISENELO_UNIVERSAL_RUNTIME_EA3.md` §3, §7, §8 — the source definition.

## OPEN — needs David

- **O-17.1 — one ID, two laws.** Ratify one of: (a) LAW-017 covers both Part A and Part B under one
  ID (status quo, zero churn); or (b) split — `LAW-017` = Runtime Composition, and Approval Scope
  becomes its own ADR with a citation sweep. **Recommend (a) for now**, given the canon freeze on
  churn; revisit post-Presentable.
- **O-17.2 — LAW-001…016 do not exist.** See the boxed note above. Do not invent them.
- **O-17.3 — EA-3 lives outside the canon.** The only written definition of LAW-017 sits in
  `Output/DISENELO_UNIVERSAL_RUNTIME_EA3.md`, a tree the Builder may not write to (D-I). 24
  citations point at a document outside the repo. **Recommendation:** copy EA-3 into
  `docs/architecture/_intake/` as a primary source (verbatim, unedited) so the canon is
  self-contained. Not done here — that is an intake decision.
- **O-17.4 — Volume XXIII is stale against B4.** Vol XXIII still treats RESERVED as one flat set;
  it does **not** encode the software/hardware split, thermal/battery/pinch points, "LG-2 must not
  be the part's designer", or "force-limiter DONE before anything is powered near David."
  Vol XXVII contains **zero** occurrences of `LG-2`. Volume XXIII needs a revision pass to match
  this law. (Architect's lane — canon edit, tracked separately.)
- **O-17.5 — LG-2's composition is still undefined** (Vol XXIII OQ-2.7.3): a named human, a second
  agent under human sign-off, or David-plus-one? The 08-10 ruling says *"the Chief Architect may
  hold LG-2 for design review"* — which answers it **for the robot design lane only**, not
  generally. **Still open for the physical build/power lane, which is exactly where it matters.**
