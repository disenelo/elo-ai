---
chapter: 3
title: "Methodology — Research → Prototype → Validation → ADR"
volume: XIX
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: N/A (research method; produces ADRs, not runtime code)
audit_status: OPEN
source: "Volume XIX Ch.1 §1.2 (research policy); DECISION_LOG.md (ADR format); 01_PRINCIPLES.md §7 Validation Philosophy / Three Foundations"
dependencies:
  - Volume_XIX/01_Research_Programme.md (research policy — research never modifies architecture directly)
  - Volume_XIX/02_Open_Research_Questions.md (the questions this method tests)
  - Volume_XIX/04_Scope_and_Guardrails.md (the limits every experiment runs inside)
  - DECISION_LOG.md (the ADR ledger every finding must land in)
  - 01_PRINCIPLES.md (Three Foundations labelling; Validation Philosophy)
  - ARCHITECTURAL_PRINCIPLES.md ("Canon before implementation" — a finding is not done until the audit says so)
---

# Chapter 3: Methodology

> **Framing (read first).** This chapter defines *how* a research question becomes a
> ratified decision. It is a process, not a claim. No step here authorises a runtime
> change on its own; the only artefact this volume ever emits is an ADR proposed for
> ratification (Ch.1 §1.2). Speculation is permitted *inside* an experiment and is marked
> **[SPECULATION — research-not-canon]**; it is never permitted in a finding.

## 3.0 Purpose

A research programme that cannot say *how a claim is tested* and *what would prove it
wrong* is not research — it is advocacy. This chapter fixes the pipeline every question in
Chapter 2 must pass through, the evidence bar it must clear, the shape of the ADR it must
become, and the falsification discipline that lets a negative result stand.

## 3.1 The pipeline — Research → Prototype → Validation → ADR

Every study moves through four stages, in order. A stage may loop back, but may never be
skipped.

```
  RESEARCH            PROTOTYPE              VALIDATION             ADR
  frame the           build the smallest     test against the      record the
  question +   ─────► thing that can    ────► evidence bar +  ────► decision:
  hypothesis +        produce evidence        the falsification     accept / reject /
  falsification       (sandbox only)          line                  inconclusive
```

**3.1.1 RESEARCH (frame).** State the question, the hypothesis (H), what would count as
evidence, and — mandatory — **what would falsify H** (Ch.2 gives the pattern). Label the
question's basis with the Three Foundations (`01_PRINCIPLES.md` §1): *Scientific
Understanding*, *Cognitive Design*, or *Creative Philosophy*. This label travels with the
finding so evidence is never confused with intention. No framing that lacks a falsification
line proceeds.

**3.1.2 PROTOTYPE (build the smallest probe).** Build the minimum artefact that can produce
evidence — a sandbox experiment, an ablation harness, an offline replay, an observer
study. **Prototypes live in the sandbox / research space only.** A prototype MUST NOT be
wired into the response path, MUST NOT alter shipped behaviour, and MUST NOT write to any
canonical state file (`elo_self_state.json`, `elo_state.json`, `blender_state.json`,
memory stores) — it reads copies or fixtures. (This is the Ch.1 §1.2 rule "research never
modifies architecture directly," made concrete.)

**3.1.3 VALIDATION (test honestly).** Run the probe against the pre-registered evidence bar
*and* the falsification line. Prefer **ablation** (does removing the mechanism remove the
effect?) and **A/B against a baseline** over anecdote. Record the result whichever way it
falls. Independent Runtime Verification applies (Architectural Principle #2 /
`ARCHITECTURAL_PRINCIPLES.md`): a result is only "seen" if it was re-run and read, not
assumed.

**3.1.4 ADR (decide).** The validated result becomes a proposed ADR in `DECISION_LOG.md`
(§3.3 format). The ADR is *proposed*, not law, until ratified at the correct authority
(§3.5). An accepted ADR may then authorise a Work Order to the owning seat — the ADR is the
bridge; this volume still writes no code.

## 3.2 Evidence tiers — what counts, and how strongly

Not all evidence is equal. Every finding declares its strongest tier reached. (This is the
Validation Philosophy of `01_PRINCIPLES.md` applied to consciousness-adjacent claims, where
the temptation to over-read weak signals is highest.)

| Tier | Name | What it is | What it can license |
|---|---|---|---|
| E0 | Anecdote / demo | A single impressive transcript or clip | Nothing. Motivates framing only. |
| E1 | Reproducible probe | Effect reproduces in the sandbox on demand | A hypothesis worth an ablation. |
| E2 | Ablation | Removing the mechanism removes the effect | A candidate ADR (mechanism is load-bearing). |
| E3 | A/B vs baseline | Measured advantage over an ablated/naive baseline | A ratifiable ADR (effect is real and sized). |
| E4 | Observer-controlled | Informed vs naive observers separate system-effect from projection (esp. Ch.2 Q3) | A finding robust against anthropomorphism. |

**Rule:** an ADR that changes anything a person experiences requires **E2 or higher**. E0/E1
alone may only refine a question, never close one. A "lifelike" or "self-aware-seeming"
claim (Ch.2 Q3) requires **E4** before it may be reported as a property of the system rather
than of the observer.

## 3.3 What a finding looks like as an ADR

Findings land in `DECISION_LOG.md` in the house format (ID · date · status · rationale).
A research ADR additionally carries the experiment's spine so it is auditable and
reproducible:

```
## ADR-XIX-<n> — <finding title> · <PROPOSED|ACCEPTED|REJECTED> · <date>
Foundation:     Scientific Understanding | Cognitive Design | Creative Philosophy
Question:       (link to Volume_XIX/02 question it answers)
Hypothesis:     H<n> as pre-registered
Method:         prototype + validation design (sandbox; ablation / A-B / observer study)
Evidence tier:  E0..E4  (with the reproduction path)
Result:         what happened — stated whichever way it fell
Falsification:  the line that WOULD have disproved H, and whether it was crossed
Decision:       accept (→ may authorise a WO) | reject | inconclusive (→ re-frame)
Guardrail check: confirms Chapter 4 limits held (no sentience claim, no runtime drive,
                 no override of Constitution / Verified Speech)
Authority:      ratifier(s) per §3.5
```

A **rejected** or **inconclusive** ADR is recorded with equal weight to an accepted one.
The ledger is a record of what was learned, not a highlight reel.

## 3.4 Falsification discipline (the heart of the method)

- **Pre-register the falsification line.** It is written in the RESEARCH stage, before data
  exists. A hypothesis with no line that could disprove it is not admitted to the pipeline.
- **A negative result is a first-class outcome.** "The self-model changed speech but not
  behaviour" (Ch.2 Q1) and "the emergent behaviour was reducible to a forgotten script"
  (Ch.2 Q3) are *successes of the method*. They ship as REJECTED ADRs.
- **No result may be upgraded past its tier.** An E1 demo may not be written up as if it
  were an E3 finding, however compelling the transcript.
- **The hard problem is not adjudicated.** No experiment claims to test for subjective
  experience; findings are behavioural/architectural only (Ch.2 §2.3; Ch.4). Any drift
  toward "this proves eLo feels X" is a guardrail breach, not a finding.

## 3.5 Authority — who ratifies what

Consciousness research touches identity and safety, which are RESERVED (CLAUDE.md standing
facts; `ARCHITECTURAL_PRINCIPLES.md` — "Human approval at governance gates").

- **Framing, prototypes, validation runs, and PROPOSED ADRs** — the Lead Architect may
  author and run (in the sandbox), coordinating seats for any code (D-LANES: this volume
  writes no product code; a prototype needing code is relayed as a spec/WO).
- **Ratifying an ADR that would authorise any runtime change, or that touches identity,
  safety, or the felt experience** — requires **David (L3)**, per the RESERVED rule.
- **Nothing in this volume is ever marked RATIFIED by the research process alone.** The
  Constitution and its Invariants are never amended by a Volume XIX finding; at most a
  finding *proposes* an amendment for the normal governance gate.

## 3.6 Relationship to the rest of canon

- **Inputs:** the questions (Ch.2), the ethical/scope limits (Ch.4), the Three Foundations
  labelling (`01_PRINCIPLES.md`), and the standing canon a question probes (the volumes in
  Ch.2 §2.5).
- **Only output:** proposed ADRs in `DECISION_LOG.md`. Everything downstream (a WO, a spec,
  a runtime change) happens *after* ratification, *outside* this volume, through the owning
  seat.
- **Discipline inherited:** "Canon before implementation — nothing is done because it was
  described; it meets the bar and the audit marks it complete"
  (`ARCHITECTURAL_PRINCIPLES.md`). A finding is not true because it was written up; it is
  true when it survived its own falsification line and the audit says so.

## 3.7 Acceptance (methodology "Definition of Done")

```
- [ ] Every study has a pre-registered falsification line before data exists.
- [ ] Every finding declares its Three-Foundations label and its evidence tier (E0–E4).
- [ ] No experience-affecting ADR rests on evidence below E2; no "lifelike/self-aware"
      claim is reported as a system property below E4.
- [ ] Every finding — accepted, rejected, or inconclusive — is recorded as an ADR.
- [ ] Every ADR passes the Chapter 4 guardrail check (no sentience claim, no runtime
      drive from this volume, no override of Constitution / Verified Speech).
- [ ] No prototype touched a canonical state file or the response path.
- [ ] Any ADR authorising a runtime change was ratified by David (L3).
```

## 3.8 References

- `Volume_XIX/01_Research_Programme.md` §1.2 — research never modifies architecture directly.
- `Volume_XIX/02_Open_Research_Questions.md` — the questions and their falsification lines.
- `Volume_XIX/04_Scope_and_Guardrails.md` — the limits the guardrail check enforces.
- `DECISION_LOG.md` — the ADR ledger and house format.
- `01_PRINCIPLES.md` — Three Foundations (§1); Validation Philosophy (§7).
- `ARCHITECTURAL_PRINCIPLES.md` — Canon before implementation; Independent Runtime
  Verification; Human approval at governance gates.

---
**Status: READY FOR REVIEW** — the Research → Prototype → Validation → ADR pipeline,
evidence tiers E0–E4, the research-ADR format, falsification discipline, and the ratifying
authority. Emits only proposed ADRs; drives no runtime behaviour.

READY FOR REVIEW
