# WP_A — eLo OS Engineering Manual

**Status:** FOUNDATION — ACTIVE
**Priority:** CRITICAL
**Owner:** David Charles / DISENELO
**Date Established:** 2026-07-11

---

## Purpose

This work package is the engineering constitution of eLo OS. It does not add cognition. It defines how every future architectural change is reviewed, designed, implemented, validated, frozen, and handed forward.

No future development begins without following this process. This manual governs the build of eLo itself — not eLo's cognition.

---

## Scope

**In scope:**
- Engineering philosophy
- Development lifecycle
- Work package structure
- Architecture review process
- Runtime review process
- Implementation standards
- Coding standards
- Testing standards
- Conversation validation standards
- Presence / Desktop / Unity / Robot validation standards
- Freeze procedures
- Rollback procedures
- Documentation standards
- Handover standards
- Contributor responsibilities

**Out of scope:**
- eLo's cognition (architecture/)
- Specific implementations
- Feature decisions

---

## Engineering Philosophy

### The One Brain Principle

The Executive Faculty is the sole decision-maker. Every other component observes, computes, or contributes information. Nothing else decides.

> Does this work package add a second decision-maker? If yes — reject.

### Preserve Behaviour Before Adding Capability

Before adding any new capability, confirm that existing behaviour is validated and frozen. New capability built on unvalidated foundations accumulates cognitive debt.

### Prefer Extending Existing Faculties

Before creating a new faculty, ask whether the requirement can be met by a new signal in an existing faculty. New faculties add coordination complexity. New signals add data only.

### Embodiment Follows Cognition

The Desktop Avatar, Unity Avatar, and Robot are output surfaces. They execute decisions. They do not make them. Embodiment changes follow cognitive freeze, not the other way around.

### Routing Exists to Understand, Not Restrict

The routing pipeline classifies input so the right faculty can respond. Classification failures degrade gracefully. Routing is never a gatekeeper.

### Every Phase Ends With a Freeze

No phase is complete without a signed freeze document. Evidence gates expansion.

### Silence Is a Feature

A well-built cognitive system speaks less and more accurately. Constant output is a red flag.

---

## The Standard Engineering Lifecycle

Every work package executes these steps in order. None are skipped.

```
1.  Architecture Review      Read everything. Produce a report. No code.
2.  Current State Audit      What exists. What works. What is broken.
3.  Gap Analysis             What is missing. What this WP needs.
4.  Architecture Design      Exact runtime flow. Interfaces. Contracts.
5.  Implementation Plan      Ordered steps. File list. Rollback plan.
6.  Implementation           Write the code.
7.  Code Review              Senior Architecture Engineer checks implementation.
8.  Unit Tests               Isolated component tests.
9.  Conversation Validation  Talk to eLo. Break eLo. Validate behaviour.
10. Desktop/Embodiment Validation  DISENELO Presence, Unity, Robot.
11. Regression Testing       Prior frozen baselines. Zero tolerance.
12. Stress Testing           Long sessions. Edge cases. Load.
13. Freeze Decision          Approve / Reject / Rollback.
14. Documentation Update     Architecture docs updated to match reality.
15. Handover                 What the next WP needs to know.
```

Steps 1–5 must be complete before step 6. Steps 7–12 must be complete before step 13.

---

## Standard Claude Roles

Each role has a defined responsibility. Roles do not overlap.

| Role | Responsibility |
|---|---|
| **Senior Architecture Engineer** | Architecture reviews, design approval, code review. Does not write implementation code. |
| **Runtime Engineer** | Implementation. Follows the implementation plan exactly. Does not design. |
| **Systems Integrator** | Integration between faculties and embodiments. Owns runtime flow across boundaries. |
| **Conversation Reviewer** | Runs conversation validation. Records exact exchanges. Does not debug code. |
| **Presence Reviewer** | DISENELO Presence and Desktop validation. Embodiment behaviour. |
| **Memory Reviewer** | Memory faculty validation. Retrieval accuracy. |
| **Executive Reviewer** | One Brain compliance. Traces every data path to the Executive. |
| **Diagnostics Engineer** | Runtime health checks. Log analysis. Root cause identification. |
| **Regression Engineer** | Runs the full regression suite. Zero tolerance for failures. |
| **Release Engineer** | Freeze decisions. Rollback procedures. Documentation sign-off. |

At session start, the active role is declared. A single Claude session should not switch between roles mid-session.

---

## Repository Structure

```
engineering/
    README.md                        ← Engineering Programme (main entry point)

    /templates/
        architecture_review.md       ← Standard review template
        implementation_plan.md       ← Standard plan template
        diagnostics.md               ← Standard diagnostic template
        regression.md                ← Standard regression template
        freeze.md                    ← Standard freeze template
        handover.md                  ← Standard handover template

    /playbooks/
        phase_template.md            ← Full playbook for any work package

    /standards/
        architecture.md              ← Architectural rules and invariants
        coding.md                    ← Code style and rules
        testing.md                   ← Testing protocol
        documentation.md             ← Documentation rules

    /work_packages/
        WP_A_ENGINEERING_MANUAL.md   ← This document
        WP_B_ONE_BRAIN.md
        WP_C_LANGUAGE_FACULTY.md
        WP_D_MEMORY_FACULTY.md
        WP_E_ATTENTION_FACULTY.md
        WP_F_RELATIONSHIP_FACULTY.md
        WP_G_EXECUTIVE_FACULTY.md
        WP_H_COGNITIVE_PLAN_SPINE.md
        WP_I_CROSS_EMBODIMENT.md

    /Volume_1_Framework/             ← Existing in-depth framework documents
    /TEMPLATE_PhasePlaybook/         ← Existing phase playbook template
    /Phase_02_*/                     ← Completed phase playbooks
    /Phase_025_*/
    /Phase_03_*/
    /Phase_035_*/
```

`engineering/` defines **how eLo evolves**.
`docs/architecture/` defines **what eLo is**.
These are separate and must stay separate.

---

## Work Package Roadmap

| WP | Name | Dependency | Status |
|---|---|---|---|
| A | Engineering Manual | None | ACTIVE |
| B | One Brain Audit + Freeze | A | NEXT |
| C | Language Faculty Audit | B | PENDING |
| D | Memory Faculty Audit | B | PENDING |
| E | Attention Faculty Audit | B | PENDING |
| F | Relationship Faculty Audit | C, D, E | PENDING |
| G | Executive Faculty Audit | C, D, E, F | PENDING |
| H | Cognitive Plan + Spine Audit | G | PENDING |
| I | Cross-Embodiment Validation | H | PENDING |

---

## Deliverables of WP_A

- [x] Engineering Manual (this document)
- [x] Engineering Templates (6 template files)
- [x] Phase Playbook Template (`playbooks/phase_template.md`)
- [x] Architecture Standards (`standards/architecture.md`)
- [x] Coding Standards (`standards/coding.md`)
- [x] Testing Standards (`standards/testing.md`)
- [x] Documentation Standards (`standards/documentation.md`)
- [x] Work Package Definitions (WP_B through WP_I)

---

## What Comes Next

**WP_B — One Brain Audit and Freeze** is the immediate next step.

Before any cognition work continues, the One Brain architecture is audited, validated, and frozen. This establishes the regression baseline for all subsequent work packages.
