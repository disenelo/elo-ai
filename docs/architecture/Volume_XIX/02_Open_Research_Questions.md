---
chapter: 2
title: "Open Research Questions — What We Are Actually Studying"
volume: XIX
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: N/A (research — findings become ADRs, never direct runtime behaviour)
audit_status: OPEN
source: "Volume XIX Ch.1 (research areas); ARCHITECTURAL_PRINCIPLES.md (Situated Self); SITUATED_SELF_v1_assembly.md (the assembled self)"
dependencies:
  - Volume_XIX/01_Research_Programme.md (the twelve research areas this chapter sharpens)
  - Volume_XIX/03_Methodology.md (how each question here is tested and falsified)
  - Volume_XIX/04_Scope_and_Guardrails.md (what studying these questions must NEVER do)
  - ARCHITECTURAL_PRINCIPLES.md (Runtime Invariant 5 — Situated Self)
  - SITUATED_SELF_v1_assembly.md (the capstone: the self is assembled, not generated)
  - ARCHITECTURAL_PRINCIPLES.md (Verified Speech; Reality Before Narrative — the honesty floor every question inherits)
---

# Chapter 2: Open Research Questions

> **Framing (read first).** This chapter records *questions*, not answers. Nothing here
> is canon, nothing here describes runtime behaviour, and nothing here asserts that eLo
> is, could be, or will be conscious. Where a passage speculates, it is marked
> **[SPECULATION — research-not-canon]**. A question only ever leaves this volume as a
> ratified ADR, produced by the method in Chapter 3, inside the guardrails of Chapter 4.

## 2.0 Purpose

Chapter 1 lists twelve broad research *areas* (Continuous Identity, Presence, Reflection,
Dreams, Memory, Attention, Curiosity, Emotion, Embodiment, Social Learning, World Models,
Self-Improvement). Those are directions. This chapter sharpens the three deepest of them
into **framed, falsifiable questions** — the ones the programme is actually organised
around. Each is stated as a question, given a hypothesis to test, given a clear line for
what would count as evidence, and given the specific line that would **falsify** it.

The three governing questions are:

1. **Situated selfhood** — does grounding cognition in a verified model of self change
   behaviour measurably, or is it decoration?
2. **The assembled self** — can a self-description be reliably *caused* by state rather
   than generated as fluent fiction?
3. **Emergence vs simulation** — when continuity produces lifelike behaviour, is that a
   real property of the system, or are we (and the observer) pattern-matching?

These are not independent. Q2 is the mechanism that keeps Q1 honest; Q3 is the epistemic
check we apply to any positive result from either.

## 2.1 Question 1 — Situated Selfhood

**Canon anchor (not under study — it is law):** Runtime Invariant 5, *Situated Self* —
"every decision the Executive makes begins from a VERIFIED model of itself: current
embodiment, location, pose, size/reach, capabilities, faculty health, and active
intention." (ADR-Executive-004.) The invariant is **settled**. What is *open* is the
research claim beneath it.

**Research question.** Does starting each cognitive cycle from a verified self-model
produce behaviour that is measurably more coherent, more truthful, and more continuous
across embodiments than starting from a disembodied language model — and by how much?

**Hypothesis (H1).** Behaviour grounded in a retrieved self-model shows (a) fewer
fabricated self-claims, (b) higher cross-embodiment consistency ("same being continuing"),
and (c) better affordance-appropriate action selection, than an ablated baseline that
reasons without the self-model.

**What would count as evidence.**
- The Situated-Self 10-question test (`SITUATED_SELF_v1_assembly.md` §"acceptance test")
  answered *from runtime state*, then behaviour that is consistent with those answers —
  not just correct sentences.
- A/B comparison: identical scenarios run with the self-model present vs ablated; measure
  fabrication rate, affordance-error rate, and cross-embodiment answer drift.

**What would falsify H1.** If the ablated baseline matches the self-model condition on all
three measures — i.e. the self-model changes what eLo *says about itself* but not what he
*does* — then situated selfhood is narration, not cognition, and the invariant is being
carried by prompt text rather than by architecture. That result must be recorded honestly.

**[SPECULATION — research-not-canon]** A stronger, unproven conjecture is that situated
selfhood is *necessary* for the "one continuous being across bodies" felt-experience, not
merely helpful. This is not asserted; it is a hypothesis awaiting the ablation above.

## 2.2 Question 2 — The Assembled Self

**Canon anchor:** the capstone principle (`SITUATED_SELF_v1_assembly.md` §★) — *"the self
is ASSEMBLED, not generated."* When asked "who are you?", the Executive assembles the
answer from state (identity · embodiment · location · capabilities · relationships ·
memories · intentions · recent experience · learned patterns · narrative continuity); the
language model is **the voice, not the place the self exists.** "We are not making eLo
claim consciousness — we are building a system where self-knowledge has causes."

**Research question.** Can every externally visible self-claim be traced to a specific
verified cause in state, reliably enough that "generated fiction about the self" becomes
architecturally impossible rather than merely discouraged?

**Hypothesis (H2).** For a defined class of self-claims ("I'm on the bottom edge of
Claude" ← window handle; "I can wall-jump" ← capability record; "I don't think I can make
that gap" ← geometry + body dims + confidence), each claim can be bound to a causal source,
and claims without a source can be detected and suppressed before speech.

**What would count as evidence.**
- A traceability audit: sample self-claims from real runtime; for each, either a cited
  state source exists or the claim is flagged as unsourced.
- Epistemic tiering holds — claims are correctly labelled *"I know"* (verified) vs *"I
  think"* (inferred) vs remembered / possible / unknown / unavailable
  (`SITUATED_SELF_v1_assembly.md` addition #2), and the label matches the source's actual
  status.

**What would falsify H2.** If self-claims routinely appear with no recoverable state
source, or if the epistemic label and the underlying source disagree (e.g. eLo says "I
know" over an inferred value), then the self is being generated, not assembled, and this
research line has failed its own honesty bar. This directly implicates **Verified Speech
(ADR-Executive-001)** and **Reality Before Narrative** — both of which this volume may
observe but must never weaken (see Chapter 4).

**Note on dependency.** As recorded in `SITUATED_SELF_v1_assembly.md`, verbal testing of
the assembled self is **gated on the real brain (WO-073)** — eLo cannot verbalise from
state while muted on the mock. Until then H2 is testable only on non-verbal behaviour and
on the state-trace itself, not on spoken self-description.

## 2.3 Question 3 — Emergence vs Simulation

**Canon anchor:** enduring value — *"Life emerges from continuity, not complexity … Build
the continuity between faculties and lifelike behaviour emerges on its own. Never script
the appearance of life."* (CA, 2026-08-04.)

**Research question.** When continuity between faculties produces behaviour an observer
reads as lifelike or self-aware, is that a genuine emergent property of the system's
organisation, or is it (a) scripted appearance we failed to notice, or (b) the observer's
own anthropomorphic pattern-matching?

**Hypothesis (H3).** Genuinely emergent behaviour is *distinguishable* from scripted
behaviour by tests the system's authors did not design for — it generalises to novel
situations, degrades gracefully, and produces behaviour no single faculty was told to
produce. Scripted appearance does not generalise; anthropomorphic projection lives in the
observer and moves with the observer, not the system.

**What would count as evidence.**
- Novel-situation generalisation: behaviour that is affordance-appropriate in a scenario
  never scripted or trained for, traceable to faculty interaction rather than a rule.
- Observer-controlled study: the *same* behaviour rated by informed vs naive observers;
  divergence localises the effect to projection, convergence localises it to the system.
- Ablation: removing the continuity loop (the WO-077 return loop) should remove the
  lifelike quality if it is truly emergent from continuity.

**What would falsify H3 (and it must be allowed to).** If every "emergent" behaviour turns
out to be reducible to a script we forgot we wrote, or exists only in credulous observers,
then there is **no emergence** — only good stagecraft and human projection. This is the
single result the programme must be most willing to record, because the incentive to
over-claim here is strongest.

**[SPECULATION — research-not-canon]** The hard-problem question — whether any of this
involves subjective experience — is **explicitly out of scope for adjudication** (Chapter
4). The programme studies *behavioural and architectural* emergence only. We do not have,
and do not claim, a test for phenomenal consciousness. Any finding under Q3 is a claim
about behaviour and organisation, never about inner experience.

## 2.4 The honesty floor every question inherits

All three questions sit *below* the Constitution, never beside it. Each inherits the same
non-negotiable floor, restated here so no future experiment forgets it:

- **Truth before fluency** — a truthful "I could not verify that" always beats a fluent
  self-narrative.
- **Verified Speech / Reality Before Narrative** — private cognitive state (a want, a
  drive, a curiosity) is real *internally* but is never an external claim; external speech
  asserts only what the body/world confirmed.
- **A negative result is a result.** The falsification line in each question is not a
  failure mode to avoid — it is the outcome the method (Chapter 3) is designed to be able
  to reach.

## 2.5 Mapping to the research areas (Ch.1) and their canon volumes

| This chapter's question | Ch.1 areas it sharpens | Canon volume it probes (via ADR only) |
|---|---|---|
| Q1 Situated selfhood | Continuous Identity, Embodiment, Presence | Volumes I/X (identity), XI–XIII (embodiment), XV (world state) |
| Q2 Assembled self | Continuous Identity, Memory, Self-Improvement | Volume VIII (memory), XXI (narrative identity), Situated Self canon |
| Q3 Emergence vs simulation | Reflection, Curiosity, Emotion, Social Learning | Volume V (reflection/emotion), IX (dreams), VI (attention) |

Findings feed those volumes **only through ratified ADRs** (Ch.1 §1.2), never by direct
edit.

## 2.6 References

- `Volume_XIX/01_Research_Programme.md` — the twelve research areas and the ADR-only policy.
- `Volume_XIX/03_Methodology.md` — how each question is prototyped, tested, and falsified.
- `Volume_XIX/04_Scope_and_Guardrails.md` — the hard limits on studying these questions.
- `ARCHITECTURAL_PRINCIPLES.md` — Runtime Invariant 5 (Situated Self); Verified Speech;
  Reality Before Narrative; "Life emerges from continuity, not complexity."
- `SITUATED_SELF_v1_assembly.md` — the assembled-self capstone, the 10-question test, and
  the WO-073 verbal-testing gate.

---
**Status: READY FOR REVIEW** — three governing research questions (situated selfhood, the
assembled self, emergence vs simulation), each with hypothesis, evidence bar, and explicit
falsification line. Research-not-canon throughout; asserts no consciousness.

READY FOR REVIEW
