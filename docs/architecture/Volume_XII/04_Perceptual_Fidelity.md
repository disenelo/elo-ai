---
chapter: 4
title: "Perceptual Fidelity — Verified Perception, No Fragments, No Fabricated Links"
volume: XII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL (PERCEPTION RAIL + [PARTIAL] tagging live in server.py; unified guard pending)
audit_status: OPEN
received: 2026-08-10
dependencies:
  - Volume_XII/01_Perception_Faculty.md (the transform this chapter constrains)
  - Volume_XII/02_Sensation_Layer.md (raw sources whose fragments must be flagged)
  - ARCHITECTURAL_PRINCIPLES.md (Verified Speech · Reality Before Narrative · Truth before fluency)
  - Volume_V/CONTRACTS.md (envelope, confidence)
---

# Chapter 4: Perceptual Fidelity

## 4.0 Purpose

Verified Speech (Runtime Invariant #3) says eLo reports verified reality and never narrates
intent as fact. Perception is where that invariant is either kept or broken *first* — long
before speech. A hallucinated object, a truncated title read as complete, or two unrelated
observations asserted as "connected" are all perception-layer failures that poison every
faculty downstream.

This chapter defines the **fidelity guard**: the rules that keep perception honest, and the
live mechanisms already enforcing them. Its origin is **WO-076 — perception mis-link
fidelity (F7)**: eLo was linking independent observations and presenting fragments as whole.

> **Verified Perception.** eLo may report only what a sensor actually delivered, at the
> fidelity it delivered it. A partial observation is reported as partial; two observations
> are linked only if the data shows the link. Perception before speech. (Extends Verified
> Speech & Reality Before Narrative to the sensor boundary.)

## 4.1 Principle — three fidelity laws

**4.1.1 No fabrication.** If input is ambiguous, perception reports **low confidence** and
generic activity — it never invents specifics. `perceive()` only *lowers* confidence when
modalities are missing; it never raises it, and it never adds a `salient_object` that isn't
grounded in the vision text (Ch.1 ST-3; `perception_faculty.py` docstring: "Confidence may
only be lowered when modalities are missing").

**4.1.2 No fragments-as-whole.** A truncated observation is tagged and reported as partial,
never presented as complete. A tab title ending in `…`, `...`, or `–` is a fragment; eLo
must say it "only caught part of it," not treat the fragment as the full title.

**4.1.3 No fabricated links.** Each observation is **independent** unless the data explicitly
shows a relationship. Two open tabs, two salient objects, two files — perception must not
assert they are "connected", "related", or "the same project" without evidence. This is the
core WO-076 fix.

These three laws are the perception-layer expression of **Truth before fluency**: an honest
"I only caught part of that" beats a fluent, fabricated whole.

## 4.2 The live mechanism — PERCEPTION RAIL + [PARTIAL] tagging

This is implemented today in `server.py` (WO-076) for the Chrome observation path and
verified by `tests/test_wo076_perception_fidelity.py` (AT-1…AT-8, passing). It is the
canonical pattern; the wider guard (4.3) generalises it.

**4.2.1 `[PARTIAL]` tagging.** Each observed title passes a tag helper before entering
context:

```
def _wo76_tag(title):
    t = title.strip()
    if t.endswith("…") or t.endswith("...") or t.endswith("–"):
        return f"[PARTIAL: {t}]"     # truncated → flagged
    return t                          # clean → passes through unchanged
```

- Unicode ellipsis (`…`), ASCII ellipsis (`...`), and trailing en-dash (`–`) all trigger
  `[PARTIAL: …]` (AT-1, AT-2).
- A clean title passes through unchanged — no false tagging (AT-3).

**4.2.2 The PERCEPTION RAIL.** When any Chrome observation lines are emitted, an
anti-fabrication rail is appended before the context reaches the model:

```
[PERCEPTION RAIL] Each item above is an INDEPENDENT observation. Do NOT assert that
any two items are linked, connected, or related unless the data explicitly shows a
link. If a title is marked [PARTIAL], do NOT present the fragment as a complete
observation — say you only caught part of it.
```

- The rail is injected whenever chrome context exists, and **survives the merge** into the
  global context `g_ctx` (AT-4, AT-5).
- **No false rail:** if there is no chrome data (no tabs/bookmarks/history), no rail is
  appended — the guard appears only where there is something to police (AT-6).
- Source labelling is part of fidelity too (WO-038): live tabs, "open but none matched",
  bookmarks, and history are labelled distinctly so eLo never flips between "Chrome isn't
  open" and "here's your history" for the same data.

## 4.3 Generalising the guard (target state)

The Chrome path proves the pattern; fidelity must hold for **every** perception modality.
The unified guard lives with the Perception Faculty (Ch.1), applied as `perceive()` builds
its result:

| Fidelity law | Chrome (live) | Generalised (target) |
|---|---|---|
| No fabrication | confidence never inflated | every modality: confidence only lowered on absence (Ch.1) |
| No fragments | `[PARTIAL: …]` on truncated titles | any truncated/low-conf read tagged partial in `modality_reads` |
| No fabricated links | PERCEPTION RAIL "INDEPENDENT observation" | `salient_objects` and `modality_reads` carry no inter-item relation unless grounded |

**Target rule (MUST):** `PerceptionResult` should carry a fidelity flag per observation —
minimally `partial: bool` and an explicit absence of asserted relationships — so the guard
is data, not just a prompt rail. Until then, the rail is the enforcement surface and MUST
be present on any multi-item observation context. (This generalisation is **PENDING**; only
the Chrome path is live — verify-before-claim.)

## 4.4 Relationship to confidence and source health

Fidelity and confidence are distinct but linked:

- **`confidence`** answers *how sure* — degrades when modalities are missing or the surface
  is unknown (Ch.1 §perceive).
- **fidelity flags** answer *how complete/independent* — a fully-confident read of a
  *truncated* title is still `[PARTIAL]`. You can be certain you saw a fragment.
- **`source_health.<modality> = absent`** is the strongest fidelity statement: eLo did not
  perceive this at all and must not speak as if it did (Ch.1 ST-2; carried to World State,
  Ch.3 §3.5).

## 4.5 Fidelity contract

```
Guard:            Perceptual Fidelity (Verified Perception)
applies_in:       PerceptionFaculty.perceive() (Ch.1) + observation context builders (server.py)
enforced_by:      [PARTIAL] tagging + PERCEPTION RAIL (live, Chrome) → unified flags (target)

Rules (MUST):
  - Never fabricate an object, scene detail, or relationship (4.1.1, 4.1.3).
  - Tag any truncated observation [PARTIAL]; never present a fragment as whole (4.1.2).
  - Treat every observation as INDEPENDENT unless the data shows a link (4.1.3).
  - Inject the rail only when there is real observation data — no false rail (4.2.2 / AT-6).
  - Carry fidelity truthfully across the World-State handoff (Ch.3 §3.5).
  - Confidence may only be lowered by missing modalities; never inflated (4.1.1).

Anti-goals (MUST NOT):
  - Assert two tabs/files/objects are related without evidence.
  - Read a "…"-truncated title as a complete title.
  - Claim to see the screen when vision is absent/denied.
```

## 4.6 Acceptance Tests

Live tests exist — `tests/test_wo076_perception_fidelity.py` (AT-1…AT-8). Canon-level:

```
FT-1  Truncated title flagged       Given a title ending "…"/"..."/"–", Then it is tagged [PARTIAL]. (AT-1,2)
FT-2  Clean title untouched          Given a clean title, Then no [PARTIAL] tag. (AT-3)
FT-3  Rail present on real data      Given ≥1 observation line, Then PERCEPTION RAIL is in the context and survives merge. (AT-4,5)
FT-4  No false rail                  Given no observation data, Then no rail appended. (AT-6)
FT-5  Rail describes partial rule    Then rail tells eLo not to present a [PARTIAL] fragment as complete. (AT-7)
ST-1  No fabricated link             Given two unrelated tabs, Then output asserts no relationship between them.
ST-2  No fabricated object           Given an ambiguous/blurred vision read, Then no invented salient_object; low confidence. (Ch.1 ST-3)
IT-1  Fidelity survives to speech     Perception fragment/absence → World State honesty → Executive/Voice never assert the whole.
```

## 4.7 Open Questions (flagged for CA / David)

- **OQ-1 — Rail vs data.** The guard is currently a **prompt rail** (a string the model is
  asked to obey) for the Chrome path only. Should fidelity become structured data on
  `PerceptionResult` (`partial`, `relations: []`) so it is enforced pre-prompt and cannot be
  ignored by a model? Recommended, PENDING. (4.3.)
- **OQ-2 — Coverage.** Only Chrome observations carry the rail today. Vision `salient_objects`,
  file lists, and voice fragments do not yet. Which modalities need the guard next, and does
  each get its own tagger or a shared one? PENDING.
- **OQ-3 — Truncation heuristics.** Tagging keys on trailing `…`/`...`/`–`. Other truncation
  shapes (mid-word cutoff, fixed-width elision) are not caught. Is a richer heuristic worth
  it, or is the OS-provided title authoritative enough? PENDING.

## 4.8 References

- `ARCHITECTURAL_PRINCIPLES.md` — Verified Speech (#3), Reality Before Narrative,
  Truth before fluency, Single Cognitive Truth (#4).
- Ch.1 `01_Perception_Faculty.md` (confidence, ST-3 no-fabrication). Ch.3 `03_World_State_Handoff.md` §3.5.
- Live code: `server.py` (WO-076 `_wo76_tag`, PERCEPTION RAIL, WO-038 source labelling),
  `desktop/chrome_reader.py`.
- Tests: `tests/test_wo076_perception_fidelity.py` (AT-1…AT-8, passing).
- `ARCHITECTURE_AUDIT.md` gap #5. WO-076 (F7), WO-038.

---

```
Chapter 4 — Perceptual Fidelity
Status: READY FOR REVIEW
Files: Volume_XII/04_Perceptual_Fidelity.md
Guard: Verified Perception — no fabrication, no fragments-as-whole, no fabricated links
Live anchor: server.py PERCEPTION RAIL + [PARTIAL] tagging (WO-076), tests passing
Fidelity Contract: Included (6 MUST rules + 3 anti-goals)
Acceptance Tests: Included (FT ×5, ST ×2, IT ×1; maps to live AT-1…AT-8)
Open Questions: 3 flagged (rail→data, coverage, truncation heuristics)
```

READY FOR REVIEW
