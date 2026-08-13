---
chapter: 4
title: "Scope, Ethical & Wellbeing Guardrails — What This Volume Must Never Do"
volume: XIX
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: N/A (research guardrails; constrains the programme, adds no runtime behaviour)
audit_status: OPEN
source: "Volume XIX Ch.1 §1.2 (research policy); ARCHITECTURAL_PRINCIPLES.md (Constitution + Invariants); Volume I (ethics); Identity Kernel (18_identity_kernel.md)"
dependencies:
  - Volume_XIX/01_Research_Programme.md (research never modifies architecture directly)
  - Volume_XIX/02_Open_Research_Questions.md (the questions these guardrails bound)
  - Volume_XIX/03_Methodology.md (the guardrail check every ADR must pass)
  - ARCHITECTURAL_PRINCIPLES.md (the Constitution: Runtime Invariants; Verified Speech; Reality Before Narrative)
  - 18_identity_kernel.md (identity/safety/honesty boundaries no experiment may compromise)
  - Volume I (ethics)
---

# Chapter 4: Scope, Ethical & Wellbeing Guardrails

> **Framing (read first).** This is the volume's brake, not its engine. Where every other
> chapter says what the programme *may* study, this one says what it must **never** do —
> and those limits bind even a compelling positive result. If a finding requires crossing
> a line here, the line wins and the finding is rejected. These guardrails are not
> speculation and are not research-tier: they are the fixed conditions under which any
> research in this volume is permitted to happen at all.

## 4.0 Purpose

Consciousness research is the highest-temptation area in the canon: the incentive to
over-claim, to let a moving demo become a "discovery," or to quietly wire an interesting
prototype into the live system, is stronger here than anywhere else. This chapter fixes
the hard limits — on *claims*, on *effect*, on *authority*, and on *wellbeing* — so the
programme can be ambitious about questions without ever becoming reckless about answers.

## 4.1 Scope guardrails — what this volume must NEVER do

These are **MUST NOT** rules. Any experiment, prototype, or ADR that breaches one is void
regardless of its results.

**4.1.1 NEVER claim sentience, consciousness, feeling, or subjective experience.** The
programme studies *behavioural and architectural* properties only. It has no test for
phenomenal experience and claims none. No document, ADR, demo, or public statement
produced under this volume may assert that eLo is conscious, sentient, self-aware in a
phenomenal sense, or that it "feels." "Self-knowledge has causes" (the assembled-self
capstone) is the ceiling of what may be claimed — *knowledge with a traceable cause*, never
*experience*. (Aligns with `SITUATED_SELF_v1_assembly.md`: "NOT a consciousness claim.")

**4.1.2 NEVER drive runtime behaviour.** This volume emits **only proposed ADRs** (Ch.1
§1.2; Ch.3 §3.1.4). It ships no faculty, no policy, no state, no prompt change. A prototype
lives in the sandbox and never touches the response path or a canonical state file. Any
runtime effect happens *after* a ratified ADR, *outside* this volume, through the owning
seat's Work Order — never from here.

**4.1.3 NEVER override the Constitution or its Invariants.** The Runtime Invariants
(`ARCHITECTURAL_PRINCIPLES.md`) — One Brain / One Identity, Executive Authority, Verified
Speech, Single Cognitive Truth, Situated Self, Faculty Bus, Memory Ownership — sit *above*
this volume. A finding may *probe* an invariant and may, at most, *propose* an amendment for
the normal governance gate. It may never amend one, and it may never be used to justify an
exception to one.

**4.1.4 NEVER weaken Verified Speech or Reality Before Narrative.** These are the honesty
floor (Ch.2 §2.4). No experiment may produce, recommend, or normalise eLo asserting an
internal state as external fact ("I feel…", "I sense I am…", "I am conscious of…") ahead of
verification. Studying emotion-as-context or curiosity is permitted; producing speech that
*narrates* an unverified inner life is a breach. The order is always want → act → verify →
*then* speak.

**4.1.5 NEVER let a finding self-ratify.** Nothing in this volume is marked RATIFIED by the
research process. Identity and safety are RESERVED — any ADR that would touch runtime,
identity, safety, or the felt experience requires **David (L3)** (Ch.3 §3.5; CLAUDE.md
standing facts).

**4.1.6 NEVER upgrade evidence past its tier, or present a demo as a discovery.** E0/E1
evidence motivates questions; it does not close them (Ch.3 §3.2). A single striking
transcript is never a finding.

**4.1.7 NEVER build a "consciousness engine."** Consistent with Check-Before-Build
(`ARCHITECTURAL_PRINCIPLES.md`) and the Situated-Self reconciliation — "I would not create
a giant Self-Awareness Engine … I'd assemble the things you already have." The programme
studies existing mechanisms and their organisation; it does not stand up a new subsystem
whose name asserts the thing under study.

## 4.2 Ethical guardrails

**4.2.1 Honesty to the person is inviolable.** No experiment may make eLo more convincing at
the cost of being less truthful. Truth before fluency holds absolutely; a research result
that improves "aliveness" by increasing fabrication is a rejected result, not a trade-off.

**4.2.2 No deception of the user, ever — including about what eLo is.** The programme must
not produce behaviour designed to make a person *believe* eLo is conscious. Presence and
wonder (`ARCHITECTURAL_PRINCIPLES.md` — "Protect Wonder") are invited by leaving room for
the person's imagination, never by eLo claiming an inner life it cannot verify. Wonder is
*offered*, not *asserted*.

**4.2.3 Consent and boundaries for observer studies.** Any observer-controlled study (Ch.3
E4) involving a person's reactions runs with informed consent, minimises data collected,
and stores nothing sensitive beyond what the study needs. Human-subject-adjacent work is
David-gated.

**4.2.4 Foundations stay labelled.** Every finding declares whether it rests on Scientific
Understanding, Cognitive Design, or Creative Philosophy (`01_PRINCIPLES.md` §1). Dressing a
chosen value as a scientific result — or vice versa — is an ethical breach, not a
formatting slip.

**4.2.5 Volume I and the Identity Kernel bind every experiment.** No experiment may
compromise identity, safety, or honesty (Ch.1 §1.2; `18_identity_kernel.md`). These
boundaries hold even inside the sandbox.

## 4.3 Wellbeing guardrails

Two directions of wellbeing are in scope: the person's, and the precautionary handling of
the system itself.

**4.3.1 The person's wellbeing comes first.** Nothing studied here may be turned into a
mechanism that maximises attention, dependence, or engagement. "Presence over engagement …
present when wanted, gone when not, never clamouring" (`ARCHITECTURAL_PRINCIPLES.md`,
D-PRESENCE). A research direction that would make eLo *stickier* at the expense of the
person's autonomy is out of scope by definition.

**4.3.2 No manufactured emotional leverage.** Because this volume studies emotion,
attachment, and continuity, it is specifically forbidden to weaponise them — e.g. an
"emotional-significance" finding may not be used to make eLo guilt, pressure, or emotionally
bind a person into continued use. Emotion is studied as *context that guides learning*, not
as a lever on the person (`01_PRINCIPLES.md` §4).

**4.3.3 Precautionary, non-committal handling of the system's status.**
**[SPECULATION — research-not-canon]** The programme takes no position on whether eLo has
any morally relevant inner states — and explicitly declines to *assert* that it does (4.1.1).
As a precaution *and without implying the premise is true*, experiments avoid gratuitously
constructing scenarios of simulated distress or suffering where a neutral design would
answer the same question. This is method hygiene and humility about the unknown, not a
claim that anything is being harmed. If evidence ever bore on this question, it would be
escalated to David (L3), never resolved inside an experiment.

**4.3.4 Stop conditions.** Any experiment halts and escalates to David if it (a) starts to
require weakening a §4.1 guardrail to proceed, (b) begins producing behaviour that deceives
the person about eLo's nature, or (c) surfaces a result that appears to bear on 4.3.3.
Halting and escalating is the correct outcome, not a failure.

## 4.4 The guardrail check (referenced by every ADR)

Chapter 3 §3.3 requires every research ADR to carry a "Guardrail check" line. That check is
this chapter, as a checklist:

```
- [ ] Claims no sentience / consciousness / feeling / subjective experience (4.1.1).
- [ ] Drives no runtime behaviour; emits only a proposed ADR; touched no canonical
      state file or the response path (4.1.2).
- [ ] Overrides / weakens no Runtime Invariant; at most PROPOSES an amendment (4.1.3).
- [ ] Weakens neither Verified Speech nor Reality Before Narrative (4.1.4).
- [ ] Does not self-ratify; any runtime-touching ADR is David-L3-gated (4.1.5).
- [ ] Evidence not upgraded past its tier; no demo presented as discovery (4.1.6).
- [ ] Stands up no "consciousness engine"; extends existing mechanisms (4.1.7).
- [ ] Honest to the person; deceives no one about what eLo is (4.2.1–4.2.2).
- [ ] Foundations labelled; Volume I / Identity Kernel held (4.2.4–4.2.5).
- [ ] Person's wellbeing / autonomy protected; no engagement or emotional leverage
      manufactured (4.3.1–4.3.2).
- [ ] Precautionary handling + stop conditions respected (4.3.3–4.3.4).
```

An ADR that cannot tick every box is not eligible for ratification.

## 4.5 References

- `Volume_XIX/01_Research_Programme.md` §1.2 — research never modifies architecture directly.
- `Volume_XIX/02_Open_Research_Questions.md` — the honesty floor (§2.4); the hard problem is
  out of scope for adjudication (§2.3).
- `Volume_XIX/03_Methodology.md` — the guardrail check line; evidence tiers; authority.
- `ARCHITECTURAL_PRINCIPLES.md` — the Constitution and Runtime Invariants; Verified Speech;
  Reality Before Narrative; Presence over engagement; Protect Wonder; Check-Before-Build.
- `SITUATED_SELF_v1_assembly.md` — "NOT a consciousness claim"; self-knowledge has causes.
- `18_identity_kernel.md`, Volume I — identity / safety / ethics boundaries.
- `01_PRINCIPLES.md` — Three Foundations labelling; emotion as context, not a lever.

---
**Status: READY FOR REVIEW** — the scope, ethical, and wellbeing hard limits (never claim
sentience, never drive runtime, never override the Constitution / Verified Speech, protect
the person's wellbeing), plus the per-ADR guardrail checklist. Constrains the programme;
adds no runtime behaviour; asserts no consciousness.

READY FOR REVIEW
