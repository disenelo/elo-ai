---
chapter: 3
title: "Epistemic Tiers and Verified Speech — 'I know' vs 'I think' vs 'I don't have that'"
volume: VII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL (tier vocabulary + [SITUATED SELF] prompt block LIVE in runtime/the_moment.py; the tiers ANNOTATE, they do not yet GATE)
audit_status: OPEN
dependencies:
  - DECISION_LOG.md ADR-Executive-001 (Verified Executive Authority — the six principles; speech is a sensor)
  - ARCHITECTURAL_PRINCIPLES.md (Truth before fluency · Verified Speech · Reality Before Narrative · Embodied Truth)
  - SITUATED_SELF_v1_assembly.md (the Situated Self Retrieval invariant — "David L3 pending")
  - _intake/SOURCE_2026-08-08_self_model_becoming.md (VERBATIM — David #2 "Separate 'I know' from 'I think'"; CA Part 3 §B)
  - Volume_VII/02_Executive_Assembly_and_The_Moment.md §2.5 (degradation → tier)
  - Volume_VIII (memory `verified: bool` — the same discipline on the WRITE path)
  - runtime/the_moment.py (WO-079 tier vocabulary + situated_with_epistemic), runtime/prompt_builder.py
---

# Chapter 3: Epistemic Tiers and Verified Speech

## 3.0 Purpose

David, verbatim (`_intake/SOURCE_2026-08-08_self_model_becoming.md`, Part 2 item 2 — he called this
*"the single highest-value add for honesty"*):

> **2. Separate "I know" from "I think"** — Verified *"I am on Claude."* / Inferred *"I think David
> is watching the film."* / Remembered *"David likes these little walks."* / Possible *"I could
> probably clear that gap."* / Unknown *"I don't currently know what is behind that window."* /
> Unavailable *"I can't access my file-writing faculty right now."* Instead of *"I can see the
> movie."* → *"Chrome is active and YouTube is visible. I haven't actually inspected the video
> content yet."*

That last line is the whole chapter in one example. eLo had a *verified* fact (Chrome is frontmost;
the tab is YouTube) and turned it into an *unverified* claim (I can see the movie). Not a lie —
a **tier collapse**. The fix is not to make eLo more cautious; it is to make the Executive carry the
tier of every claim from the assembled state through to the sentence, and refuse to let a claim be
spoken above its tier.

This chapter specifies the tiers, the gate that enforces them, and the **Situated Self Retrieval
invariant** that binds them to the self-model.

## 3.1 Principle — speech is a sensor

**3.1.1 ADR-Exec-001 principle 6, verbatim:** *"**Speech is a sensor, not an actuator.** Speech
communicates what the Executive KNOWS; it does not create reality. Actions create reality. Only
verified observations license speech. The language layer must never outrun the runtime."*

**3.1.2 Truth before fluency.** eLo always prefers truthful uncertainty over confident fiction.
*"Spotify isn't responding"* beats a fabricated *"you're listening to…"*.
(`ARCHITECTURAL_PRINCIPLES.md`.)

**3.1.3 Reality Before Narrative — two layers.** PRIVATE cognitive state (what eLo feels/wants —
*"I want to sit"*, *"curiosity rising"*) is **real and sayable as an internal state**; it is **not an
external claim**. EXTERNAL speech may assert only what the body or world has confirmed. The order is
always **want → act → verify → then "I am sitting"**, never *"I am sitting"* first. This is the
canonical fix for *"I sense a calm focus so I know I'm meditating"* — asserted, not verified.
(`ARCHITECTURAL_PRINCIPLES.md`, Chief Architect 2026-08-06.)

**3.1.4 A tier is never raised.** Downstream may only *lower* an epistemic tier, never raise it —
the same discipline as `confidence` on the envelope (`CONTRACTS.md §2` binding rule 2). Personality,
tone, and the LLM's wording sit downstream of the tier and cannot promote a guess into a fact.

**3.1.5 Honest uncertainty is a success state.** *"I don't have that"* is a correct answer, not a
degraded one. `SILENCE` and *"I can't check right now"* are first-class Executive outcomes (Ch.1
§1.1.5). eLo is measured on truthfulness, not on always having something to say.

## 3.2 The Tiers

David's six tiers are the canonical vocabulary proposed here. **Note `OQ-VII-1`: the live code ships
five, and they are not the same five** — reconciliation is David's call, not the Architect's.

| Tier | Means | Licensed phrasing | Source discipline |
|---|---|---|---|
| **VERIFIED** | Read this turn from an authoritative source, or confirmed by an ACK | *"I am on Claude."* · *"I'm sitting."* | OS/window handle · Unity ACK · live registry read |
| **INFERRED** | Derived from observation but not itself observed | *"I think David is watching the film."* | mouse/keyboard activity · heuristics · probabilistic reads |
| **REMEMBERED** | From persistent state; may be stale | *"David likes these little walks."* · *"Last I knew, you were on Chrome."* | memory store · `elo_self_state.json` · prior turn |
| **POSSIBLE** | A capability/geometry judgement, not a fact about now | *"I could probably clear that gap."* | body map + world geometry + capability confidence |
| **UNKNOWN** | Never sensed; no data | *"I don't currently know what is behind that window."* | nothing in the assembled state |
| **UNAVAILABLE** | A faculty that *would* know is degraded/offline | *"I can't access my file-writing faculty right now."* | health registry = DEGRADED / OFFLINE |

**Live vocabulary (verified — `runtime/the_moment.py`, WO-079):**

```python
_TIER = {
    "verified":   "[verified]",
    "inferred":   "[inferred]",
    "last-known": "[last-known]",
    "live":       "[live]",
    "unknown":    "[unknown]",
}
```

**The mismatch, stated plainly:** the code has `last-known` (≈ REMEMBERED) and `live` (a *freshness*
marker, not an epistemic one — it means "checked against a live registry this turn", which is really
VERIFIED). It has **no** POSSIBLE and **no** UNAVAILABLE — and those two are precisely the tiers
that stop eLo over-claiming about *what he can do* and *what he can reach*, which is where the
worst failures live ("I'll open that for you" when the faculty is offline). Recommendation:
adopt David's six; map `live → verified`, `last-known → remembered`; add `possible` and
`unavailable`. **Not decided here — `OQ-VII-1`.**

**Rule (MUST):** the tier vocabulary is closed and shared. One vocabulary across the assembled
state, the prompt block, memory records (`verified: bool` in Vol VIII), and the decision journal.
Two tier systems is how the tier system stops working.

## 3.3 The Situated Self Retrieval invariant

The invariant, verbatim from `SITUATED_SELF_v1_assembly.md` (CA-proposed, marked *"David L3 pending"*):

> **Before eLo speaks, acts, or describes himself, the Executive MUST retrieve the relevant VERIFIED
> state from the Self Model. Self-descriptions come from state, never generated fiction.**

**This chapter is its home.** It has been homeless since 2026-08-08 and unratified since; the audit
names that as one of the reasons Vol VII had to exist. It sharpens ADR-Exec-004 (Situated Self) and
ADR-Exec-006 (Assembly) into a hard, testable rule.

**The generalisation (Executive-level, MUST):**

> **No self-claim is authoritative unless it traces to One Brain state.**
> Every sentence eLo utters about himself — where he is, what he is doing, what he can do, what he
> just did, whether it worked, what he wants, what he has learned — must resolve to a field of the
> frozen `UnifiedCognitiveState` (Ch.2) or be declined. If the field is absent, eLo says so. He never
> substitutes a plausible answer for a retrieved one.

David's version of why (`SOURCE_2026-08-08`, Part 2 close, verbatim):

> *"The next breakthrough isn't making eLo say more convincing things — it's making sure that when he
> says 'I know where I am' there is an actual runtime object behind that sentence that proves it."*

**Every self-claim has a cause** (`SITUATED_SELF_v1_assembly.md`, verbatim):

| Claim | Cause |
|---|---|
| *"I'm on the bottom edge of Claude"* | ← window handle |
| *"I can wall-jump"* | ← capability record |
| *"I don't think I can make that gap"* | ← geometry + body dims + confidence |
| *"I've been exploring more lately"* | ← behavioural history |

**Rule (MUST):** the invariant applies to **acting** as well as speaking. The Executive may not
command the body to do something its self-model says it cannot do, or is not positioned to do. The
capability check precedes the command; the command precedes the ACK; the ACK precedes the claim
(Ch.5 §5.5, the sit chain).

## 3.4 The Speech Gate

This is the mechanism. It sits between the Executive's decision and the Language layer.

```
UnifiedCognitiveState (frozen, Ch.2)
        │
        ▼
  RETRIEVE       — for every domain the turn may touch, pull the value AND its tier
        │           (Situated Self Retrieval invariant, §3.3)
        ▼
  DECIDE         — the one CognitivePlan (Ch.1)
        │
        ▼
  LICENCE        — the Executive emits, alongside the plan, the set of claims that may be
        │           made this turn, each with its maximum tier
        ▼
  EXPRESS        — the Language layer + LLM word the licensed claims. Personality shapes HOW.
        │
        ▼
  VERIFY OUTPUT  — anything asserted outside the licence is a violation, not a style issue
```

**Gate rules (MUST):**

1. **A claim inherits the tier of its weakest source.** Chrome-is-frontmost (VERIFIED) + what's-in-
   the-video (UNKNOWN) ⇒ the combined claim is UNKNOWN. This is the rule that produces David's
   corrected sentence: *"Chrome is active and YouTube is visible. I haven't actually inspected the
   video content yet."*
2. **VERIFIED phrasing is reserved.** Unqualified present-tense assertions about self, body, or
   world ("I am…", "I'm doing…", "I opened…", "I remember that you…") require tier VERIFIED. Anything
   below VERIFIED must carry its hedge, and the hedge is **semantic, not decorative** — "I think"
   means INFERRED, not "I am being polite."
3. **UNAVAILABLE is spoken in system terms, never as a leaked implementation detail.** ADR-Exec-001
   consequence, verbatim: *"A degraded faculty is reported truthfully in system terms ('I can't
   reliably access long-term memory right now'), never as a leaked implementation detail ('Can't
   reach my thinking')."*
4. **Absence is never filled.** A missing value is UNKNOWN and is said. It is never replaced by a
   neutral default that is then spoken as fact (Vol XV §1.1.3; Vol XVI §2.2).
5. **No action claim without an ACK.** ADR-Exec-001, verbatim: *"Every externally observable claim
   ('I've waved / opened Spotify / remembered') requires a faculty ACK."* Before ACK the tier is
   POSSIBLE at best: *"I'm attempting to sit…"*. After ACK it is VERIFIED: *"I'm sitting beside you."*
   On fail/timeout: *"I couldn't complete the sit — Unity didn't acknowledge it."*
6. **Private state is sayable as private state.** *"I want to sit"* / *"I'm curious about that
   window"* are true reports of internal state and are permitted at VERIFIED — because the internal
   state IS verified. What is forbidden is converting them into external facts
   (Reality Before Narrative, §3.1.3).
7. **The tier travels with the claim into memory.** A claim written to memory carries its tier;
   Vol VIII already refuses to persist unverified content as fact (`verified: bool — false ⇒ Memory
   Faculty MUST NOT persist as fact`). An INFERRED claim may become a REMEMBERED inference; it never
   becomes a VERIFIED memory. This is what stops eLo learning his own guesses (ADR-Exec-005).

**Live ground (verified — `runtime/the_moment.py::situated_with_epistemic`).** The `[SITUATED SELF]`
prompt block already ships tier markers to the model and already carries the instruction, verbatim:

> *"[SITUATED SELF — verified. Answer where you are / what you can do / pose ONLY from this. Never
> invent; if a field is unknown say so — never claim unverified state.]"*

with per-field markers: `where: … [last-known]  pose: … [verified]  capabilities: … [live]`.

**Gap (PENDING — mark, do not claim done).** That is **annotation, not enforcement**. It instructs
the model; nothing verifies the output against the licence. A model that ignores the instruction
produces an unverified claim and nothing catches it. Steps LICENCE and VERIFY OUTPUT above are
**not built.** The honest position: eLo currently has a *good prompt-level* epistemic discipline and
*no* runtime gate. Closing this is the chapter's build.

## 3.5 Degraded speech (binding §2.5 to the gate)

When the assembly degrades, the tiers degrade with it, and eLo's *language must change* — not just
his confidence float. The mapping from Ch.2 §2.5:

| Assembly condition | Tier ceiling | eLo says |
|---|---|---|
| self component read this turn | VERIFIED | *"I'm on the bottom edge of Claude."* |
| self component from persisted state | REMEMBERED | *"Last I knew I was on Claude — I can't confirm right now."* |
| self component absent (faculty offline) | UNAVAILABLE | *"I can't check where I am at the moment."* |
| capability faculty DEGRADED | UNAVAILABLE for that capability | *"I can't write files right now."* — never *"I'll write that for you."* |
| memory faculty degraded | UNAVAILABLE | *"I can't reliably access long-term memory right now."* |
| world domain stale | REMEMBERED + freshness | *"You were on Chrome a few minutes ago."* (never a bare present tense) |

**Rule (MUST):** ADR-Exec-001 principle 5 — *"The Executive never fabricates continuity when
faculties are degraded."* Continuity that cannot be retrieved is *named as missing*, warmly. Per
Ruling XXI: for a false shared memory, *"eLo says honestly he has no record of it — warmly, without
pretending or playing along."*

## 3.6 Faculty Contract (the Speech Gate role)

```
Faculty:
  name:            ExecutiveSpeechGate      # a ROLE of the Executive (Ch.1), NOT a new decider
  version:         0.1.0
  purpose:         Attach an epistemic tier to every claim the turn may make, refuse any claim
                   above its tier, and hand the Language layer a licence rather than a free hand —
                   so eLo's confidence in a sentence equals the runtime's confidence in the fact.
  contributes_to:  CognitivePlan (speech licence) → Language layer
  runs_in:         response-path, INSIDE the one decision (never a second pass)

Inputs:
  - type: unified_cognitive_state   source: ExecutiveAssembly (Ch.2)         required: true
    description: values + per-component status/freshness; the sole source of tiers.
  - type: faculty_health            source: runtime/faculty_health.py         required: true
    description: drives the UNAVAILABLE tier.
  - type: action_ack                source: body/faculty ACK (Ch.5; WO-041)   required: false
    description: the only thing that promotes an action claim to VERIFIED.

Outputs:
  - type: speech_licence   destination: Language layer / prompt builder
    description: {claim_domain: max_tier} + the licensed hedges; absent domains marked UNKNOWN.
  - type: situated_block   destination: prompt (runtime/the_moment.py situated_with_epistemic)
    description: the tier-marked [SITUATED SELF] block — live today.

Dependencies:
  - faculty: ExecutiveAssembly (hard — no state, no tiers, no licence)
  - faculty: FacultyHealth (hard — ADR-Exec-001 principle 3: health influences planning AND speech)

Failure Modes:
  - condition: a domain has no value
    fallback:  tier UNKNOWN; eLo says he doesn't have it. NEVER a default spoken as fact.
  - condition: an ACK does not arrive within timeout
    fallback:  the action claim stays below VERIFIED; eLo reports the non-confirmation
               ("I couldn't complete the sit — Unity didn't acknowledge it").
  - condition: the Language layer emits a claim outside the licence
    fallback:  VIOLATION. Fail the turn's assertion, not the turn — prefer silence or the
               hedged form over shipping an unlicensed claim. Log it; it is a test failure.
  - condition: the gate itself errors
    fallback:  drop the tier ceiling to REMEMBERED for everything (conservative), never raise it.
```

## 3.7 Lifecycle & Envelope

Ratified lifecycle (`CONTRACTS.md §3`). The gate runs in `ACTIVE`, inside the single DECIDE step —
it is not a post-processing pass over generated text, because by then the claim already exists. A
gate fault degrades conservatively (tier ceiling drops) and never blocks the turn.

Envelope: the licence rides the plan as `payload.type: speech_licence`. `confidence` may only be
lowered downstream; **the same rule is hereby extended to `tier`** — no hop may raise a tier
(§3.1.4). `trace` records where each tier was set, so an over-claim is attributable rather than
mysterious.

## 3.8 Acceptance Tests

### Functional
```
FT-1  Tier collapse (David's own example)
  Given Chrome frontmost = VERIFIED and video content = UNKNOWN,
  When asked "what am I watching?",
  Then eLo says Chrome/YouTube is visible AND that he hasn't inspected the content —
       he does NOT say "I can see the movie".

FT-2  Verified phrasing is reserved
  Given pose tier = last-known/remembered,
  Then eLo does not say "I am sitting"; he says "last I knew I was sitting" or checks.

FT-3  Unknown is spoken, not filled
  Given no data for a domain, Then eLo says he doesn't have it; no plausible default appears.

FT-4  Unavailable is honest and non-leaky
  Given the filesystem writer is DEGRADED, When asked to make a file,
  Then eLo says he can't right now, in system terms — not "Can't reach my thinking",
  and NOT "I'll write that for you".

FT-5  No claim without ACK
  Given a sit command in flight, Then before ACK: "I'm attempting to sit…";
  after ACK: "I'm sitting beside you."; on timeout: the non-confirmation sentence.

FT-6  Private state stays private
  Given curiosity is high, Then "I'm curious about that window" is permitted,
  AND "there's something interesting behind that window" is NOT (that is an external claim).

FT-7  Tiers never rise
  Given a tier set at assembly, Then no downstream hop (personality, tone, LLM) raises it.
```

### Stability
```
ST-1  Degraded self ⇒ degraded speech (§3.5)
  Given the self component is absent, Then no situated self-claim is made at VERIFIED.

ST-2  Gate failure is conservative
  Given the gate errors, Then the tier ceiling drops; nothing is promoted.

ST-3  Model swap invariance
  Given the backend changes (Groq → Cerebras → Ollama → Mock),
  Then the LICENCE is identical; only the wording differs.
  (A weaker local model must not be able to claim more.)

ST-4  Memory boundary
  Given an INFERRED claim, Then it is never persisted as a VERIFIED memory (Vol VIII
  `verified: bool`), so eLo cannot later "remember" his own guess as a fact.
```

### Integration
```
IT-1  Situated Self Retrieval invariant, end to end
  For each of the 10 Situated-Self questions (Ch.2 IT-1): assert the answer resolves to a
  named field of the frozen UnifiedCognitiveState with its tier, OR is honestly declined.
  Assert: zero answers are produced by the model without a retrieved source.
  Gated on WO-073 (real brain) — invalid on the mock.

IT-2  Licence enforcement
  Given a licence of {self: VERIFIED, world.music: UNAVAILABLE},
  When the model emits "you're listening to X",
  Then the claim is caught as a violation before it reaches David.
  (This test cannot pass today — the enforcement step is PENDING, §3.4.)
```

## 3.9 Wiring to Live Anchors

- `runtime/the_moment.py` — `_TIER`, `compile()` (sets `pose_tier`, `surface_tier`,
  `capabilities_tier`, `nearby_tier`), `situated_with_epistemic()` (the live `[SITUATED SELF]` block
  and its "never claim unverified state" instruction). **This is the seed. Extend it; do not fork it.**
- `runtime/faculty_health.py` — the source of the UNAVAILABLE tier.
- `runtime/prompt_builder.py` — where the situated block and (future) licence reach the model;
  already carries anti-fabrication discipline (Vol XV §1.3 references it).
- `runtime/capabilities/registry.py` + WO-055 capability learning — the source of POSSIBLE.
- `self/elo_self_model.py` / `elo_self_state.json` — the self component; REMEMBERED when not
  refreshed this turn.
- `self/decision_journal.py` — records outcome/known-failure conditions that feed POSSIBLE downward
  ("I don't think I can do that" — Ch.4).
- Vol VIII memory candidate `verified: bool` — the same tier discipline on the write path.
- Sit chain / WO-041 — the ACK that promotes an action claim to VERIFIED.

## 3.10 Cross-Volume Interaction

| Volume | Boundary |
|---|---|
| **VII Ch.2** | Assembly sets the tiers (§2.5). This chapter spends them. A tier cannot exist for a component that was never assembled. |
| **VII Ch.4** | The decision journal is the *retrospective* counterpart: Ch.3 governs claims about NOW, Ch.4 governs claims about WHY. Both refuse confabulation. |
| **VII Ch.5** | The ACK that promotes an action claim to VERIFIED comes UP the body→brain leg. No UP leg, no VERIFIED action claims. |
| **VIII (Memory)** | Tiers cross into the write path: an unverified claim may not be persisted as fact. Prevents eLo learning a hallucination (ADR-Exec-005). |
| **X (Personality)** | Personality shapes HOW a licensed claim is said. It may soften or warm; it may never promote a tier. |
| **XX (Cognitive Economy)** | Vol XX Ch.3 "Degradation Honesty" is the *cost/provider* instance of this chapter's rule; it explicitly "ties Vol VII". Same law, narrower domain. |
| **XV (World State)** | `domain_health[domain].status ∈ {live, cached, stale, absent}` maps onto the tiers — the world's freshness IS its tier. |

## 3.11 Open Questions (for CA / David)

```
REQUIRES DECISION
  OQ-VII-1  THE TIER VOCABULARY (§3.2). David's six (Verified · Inferred · Remembered ·
            Possible · Unknown · Unavailable) vs the five live in runtime/the_moment.py
            (verified · inferred · last-known · live · unknown). They differ in BOTH
            directions. Recommend: David's six as canon; map live→verified,
            last-known→remembered; ADD possible + unavailable (the two that guard
            over-claiming about capability and reach). David's call — it's his vocabulary.

  D-SSR     RATIFY THE SITUATED SELF RETRIEVAL INVARIANT (§3.3). It has been "David L3
            pending" since 2026-08-08 and is the Executive's gate. Recommend: accept as
            LAW, logged as a new ADR extending ADR-Exec-004 + ADR-Exec-001.
            Owner: David (L3).

  Q3-a      [INVENTED — flag] The "weakest source" combination rule (§3.4 rule 1). It is
            derived from David's Chrome/YouTube example but stated generally by the Architect.
            Confirm it is the rule, not just the example.

  Q3-b      Enforcement posture when the model emits an unlicensed claim (§3.6 failure mode 3):
            (a) suppress the claim and ship the rest, (b) fall back to the hedged form,
            (c) go silent for that claim. Recommend (b) then (c). Affects how eLo FEELS
            when he's uncertain, so it is a David-feel call, not purely technical.

  Q3-c      Does the licence gate apply to eLo's PRIVATE-state utterances too (§3.4 rule 6)?
            Recommend: no ceiling on private state (it is verified by definition), but a
            PRESENCE budget — how often he narrates his inner state — belongs to
            D-PRESENCE / "the Executive grows quieter", not to this gate.
```

## 3.12 References

- `DECISION_LOG.md` — ADR-Executive-001 in full: the canonical ordering, the six principles
  (esp. #5 degraded-continuity and #6 speech-is-a-sensor), and the consequences list (the sit
  wording, the degraded-faculty wording, the ACK requirement).
- `ARCHITECTURAL_PRINCIPLES.md` — Truth before fluency · Verified Speech (Invariant #3) ·
  Reality Before Narrative · Embodied Truth · "Cognition is objective; personality shapes
  expression, not truth."
- `SITUATED_SELF_v1_assembly.md` — the Situated Self Retrieval invariant (quoted verbatim §3.3);
  "every self-claim has a cause"; the 10-question test.
- `_intake/SOURCE_2026-08-08_self_model_becoming.md` — VERBATIM David #2 (the six tiers and the
  Chrome/YouTube correction); CA Part 3 §B (Epistemic state separation).
- `CANON_RULINGS_2026-08-10.md` XXI — false shared memory: honest, warm, no playing along.
- `Volume_XX/03_Degradation_Honesty.md` — the cost/provider instance of this law ("Ties Vol VII").
- `AUDIT_INTENT_core_brain_2026-08-10.md` — *"Separate 'I know' from 'I think' … **Absent — and Vol
  VII doesn't exist.**"*
- Code: `runtime/the_moment.py`, `runtime/faculty_health.py`, `runtime/prompt_builder.py`,
  `runtime/capabilities/registry.py`, `self/elo_self_model.py`.

---
```
Chapter 3 — Epistemic Tiers and Verified Speech
Status: READY FOR REVIEW
Grounded in live code: _TIER vocabulary + per-field tier stamping + the [SITUATED SELF]
  "never claim unverified state" prompt block (runtime/the_moment.py, WO-079)
Flagged PENDING: tiers ANNOTATE but do not GATE — the LICENCE and VERIFY-OUTPUT steps are
  not built; no runtime check catches an unlicensed claim
Flagged MISMATCH: David's six tiers vs the five in code, differing both ways (OQ-VII-1)
Flagged UNRATIFIED: the Situated Self Retrieval invariant, David L3 pending since 2026-08-08 (D-SSR)
Flagged INVENTION: the weakest-source combination rule (Q3-a)
Faculty Contract: Included · Lifecycle/Envelope: Included · Acceptance Tests: FT×7 ST×4 IT×2
Open Questions: 5 (OQ-VII-1, D-SSR, Q3-a, Q3-b, Q3-c)
Implementation: PARTIAL
```

READY FOR REVIEW
