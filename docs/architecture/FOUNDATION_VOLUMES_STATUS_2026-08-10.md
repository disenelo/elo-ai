# Foundation Volumes — Honest Status (I · II · III · IV · XIV)

**Status:** READY FOR REVIEW · authored by the Lead Architect · **NOT RATIFIED**
**Written:** 2026-08-13 · **Findings dated:** against `AUDIT_MASTER_2026-08-10.md` and
`AUDIT_INTENT_support_governance_2026-08-10.md`, **re-verified directly against the repo
2026-08-13** (Rule #2 — Independent Runtime Verification).

---

## Why this page exists

`00_CANON_INDEX.md` marks Volumes **I, II, III, IV and XIV** as **"✅ Live"**. They are not.

The `✅` was awarded on the strength of *code existing*, not of *canon existing* — and the
Whole-Canon Build Queue then explicitly exempted them:

> `00_CANON_INDEX.md`: *"ALREADY LIVE (canon = code; write spec only if formalisation
> needed): **I, II, III, IV**, VII, IX, XI, XIII, **XIV**"*

That combination is self-sealing: a volume marked live is never queued, so it is never
written, so nothing ever causes it to exist. **Volumes VII, XI and XIII were caught by the
same mechanism on 2026-08-10 and have since been written.** I, II, III, IV and XIV were not.

**This page does not write those volumes.** It makes the hole visible, states exactly what
canon *actually* exists for each, whether it is a real spec or a stub, and what it would take
to bring each to the Volume XV bar. It is the honest replacement for five `✅` marks.

**Recommended Index change (in-lane for the Architect; flagged so it is visible):** the five
rows below should read **⚠️ Partial** or **🔴 Stub**, with `Canon spec:` pointing at this page
until each volume has a directory.

---

## Summary table

| Vol | Title | Index says | **Actually is** | Real spec or stub? | Directory? |
|---|---|---|---|---|---|
| **I** | Philosophy | ✅ Live | **Substantive material, wrong artefacts.** Points at `VISION.md` (a 110-line prospective pitch) + `prompts/living_presence_spec.txt` (a 418-line *runtime prompt* under FREEZE_V1_LOCK). Neither is a volume. `ARCHITECTURAL_PRINCIPLES.md` is the real constitution and is **not** cited by the row. | **Real material, no spec.** Zero contracts, zero tests. | ❌ none |
| **II** | Cognitive Principles | ✅ Live | **Good document, honest about itself.** `17_cognitive_principles.md` (189 lines) is genuinely well written — and states verbatim at line 161: *"Principles are not yet a typed object."* | **Real doc, not a spec.** No faculty contract, no lifecycle, no envelope, no tests. | ❌ none |
| **III** | System Architecture | ✅ Live | **Closest to real.** `16_runtime_contracts.md` (256 lines) defines the four runtime contracts and the loop, and says of itself *"If code conflicts with this document, the document is right."* Carries an undated embedded TODO (§"Passive Awareness (Immediate Fix)", line 221). | **Real spec, partially drifted.** Missing lifecycle/envelope/tests in volume form. | ❌ none |
| **IV** | Cognitive Spine | ✅ Live | 🔴 **The worst hole.** The Index names **code** (`runtime/spine/spine.py`) as the canon. The written spec, `16_spine_runtime.md`, is **5 lines**: `STATUS: PENDING — to be written in a dedicated session.` A task "Build 16_spine_runtime.md" was marked *completed*. It was not built. | **STUB.** Verified 2026-08-13: `wc -l` = 5. | ❌ none |
| **XIV** | Plugin Architecture | ✅ Live | ⚠️ **Better than the audit found — and this page corrects it.** `docs/plugin_system.md` **exists**: 260 lines, `Version 1.0 · Status: Active`, with a plugin interface, capability vocabulary, layer rules, lifecycle, safety constraints, four skeletons, and forbidden patterns. `AUDIT_INTENT_support_governance_2026-08-10.md` recorded *"No canon at all"* — **that finding was wrong.** The real problem is a **boundary conflict** with Volume XXIII. | **Real spec, mis-filed and un-reconciled.** | ❌ none |

**One-line reading:** Volume IV is a stub while being the most load-bearing of the five.
Volumes I, II, III and XIV have real material in the wrong shape or the wrong place. **None
of the five has a directory, a work order, or a Definition of Done.**

---

## Volume I — Philosophy

### What actually exists

| Artefact | Size | What it is | Verdict |
|---|---|---|---|
| `ARCHITECTURAL_PRINCIPLES.md` | 139 lines | **The real constitution.** 7 Runtime Invariants + the enduring values + governance. Actively maintained; cited everywhere. | ✅ **This is Volume I's substance** — and the Index row does not mention it. |
| `prompts/living_presence_spec.txt` | 418 lines | A **runtime prompt** under FREEZE_V1_LOCK. Character DNA, voice, continuity. | ⚠️ Real material, wrong artefact class. A prompt is an implementation, not canon. |
| `VISION.md` | 110 lines | A prospective pitch — *"You open your laptop."* | ⚠️ Written to a reader who might buy eLo, not to an engineer building him. |
| `00_MANIFESTO.md` · `00_philosophy.md` · `00_DAVIDS_VISION_SPINE.md` · `01_PRINCIPLES.md` | — | Adjacent philosophy documents, none indexed as Volume I. | ⚠️ Scattered. |

### Real spec or stub?
**Neither.** Substantive philosophy exists in abundance — across at least six files, none of
which is Volume I. There is no contract, no test, no Definition of Done.

### Second finding (from the 2026-08-10 audit, still true)
The Volume I artefacts **refuse to name David**. `living_presence_spec.txt` says *"help **a
human**"* and *"**the person you are with** is a builder"*, and uses `the user` 15 times.
`VISION.md` addresses a prospective buyer. eLo is a personal tool with exactly one person in
it. This is product-era residue in the volume that defines who eLo is *for*.

### What would need writing to reach the Vol XV bar
1. `Volume_I/00_Metadata.md` naming `ARCHITECTURAL_PRINCIPLES.md` as the **origin text** (the
   same origin/home relationship Volume XVII sets with Vol V Ch.6) — not a rewrite of it.
2. One chapter: **"The Constitution and its Layering"** — Constitution → Canon → Engineering
   → Runtime → Behaviour; what an Invariant is; what it takes to change one; why the
   principle wins over a design choice.
3. One chapter: **"Identity and Voice"** — the relationship between the Identity Kernel
   (`18_identity_kernel.md`), the personality vector (Vol V Ch.7), and the runtime prompt.
   Resolve the artefact-class problem: state plainly that `living_presence_spec.txt` is an
   **implementation of** Volume I, not Volume I.
4. Acceptance tests. A philosophy volume's tests are **conformance** tests: *"no shipped
   artefact contradicts an Invariant"*, *"the one-person framing is consistent"*.
5. Optional but recommended: retire or reframe `VISION.md` as a marketing artefact so it
   stops being cited as canon.

**Effort:** ~2 chapters. **The material is written; the volume is not.**

---

## Volume II — Cognitive Principles

### What actually exists

`17_cognitive_principles.md` — 189 lines, six sections (Runtime Philosophy · What This
Document Is · The Principles · How Principles Constrain the Executive · What Principles Are
Not · Implementation Reference). It is a **good document**, and it is honest about its own
state.

### Real spec or stub?
**A real document, not a spec.** Its own line 161 is the finding:

> **`17_cognitive_principles.md:161` — *"Principles are not yet a typed object."***

It then sketches the intended form (`runtime/cognitive_principles.py`, a frozen dataclass
loaded once at startup). **Verified 2026-08-13: `runtime/cognitive_principles.py` does not
exist.** So the principles constrain the Executive *by convention and by prompt*, not by any
structure the runtime can check. Nothing enforces them; nothing can test that a turn obeyed
them.

Missing for volume status: faculty contract, lifecycle, message envelope, acceptance tests,
Definition of Done.

### What would need writing to reach the Vol XV bar
1. `Volume_II/00_Metadata.md` naming `17_cognitive_principles.md` as origin text.
2. One chapter: **"The Principles as a Typed Object"** — the frozen `CognitivePrinciples`
   dataclass the existing doc already sketches; loaded once at startup, never passed per-turn,
   never mutable, and **never learnable** (ADR-Exec-005 D3 names *"architectural principles"*
   in the never-evolve list — Vol XVIII §1.4.1).
3. One chapter: **"How a Principle Constrains a Turn"** — the enforcement point. Today this
   is prose; it needs a named hook in the Executive path with a test that a principle-violating
   plan is refused rather than merely discouraged.
4. Acceptance tests: the principles object is immutable · it is loaded exactly once · a
   learning pass cannot alter it (this test already has a home in `LEARNING_LOOP_v1.md §6.2`).

**Effort:** ~2 chapters. **Lower risk than IV** — the doc is good and the gap is form.

---

## Volume III — System Architecture

### What actually exists

`16_runtime_contracts.md` — 256 lines, `Canonical Reference v2.0`. Defines the loop
(Observe → Faculties → `CognitiveState` → Executive → `CognitivePlan` → Execution →
`EmbodimentState` → `ExecutionReport` → Reflection → `integrate_session()`) and the four
runtime contracts with producer/consumer/mutator discipline. It opens with
*"If code conflicts with this document, the document is right."*

This is the most-cited foundation document in the canon — Vol XV, Vol V Ch.6, and the spine
all take their contract vocabulary from it.

### Real spec or stub?
**A real spec, partially drifted.**

- Verified 2026-08-13: it carries an **undated embedded TODO** at line 221 — a
  `## Passive Awareness (Immediate Fix)` section reading like an in-flight note inside a
  canonical reference. A canonical document with a live TODO in it is either stale or is
  a work order wearing the wrong hat.
- It has no volume frontmatter, no Definition of Done, no acceptance tests, and no
  lifecycle/envelope sections in the form every other volume now carries.
- Its named consumer, `runtime/spine/spine.py`, has evolved substantially since
  (WO-CANON-VI/XII/XV/XVI markers are visible in the live turn order) and the contract
  document does not reflect that assembly order. **This is the drift Volume IV would close.**

### What would need writing to reach the Vol XV bar
1. `Volume_III/00_Metadata.md` naming `16_runtime_contracts.md` as origin text.
2. Promote the four contracts to a chapter with the standard blocks; **resolve or date the
   embedded TODO** (either it is done, or it becomes a WO — it does not stay in canon).
3. One chapter: **"Contract Ownership and Mutation"** — who may produce, consume, and mutate
   each of the four contracts, made testable. This is what stops future faculties writing
   into state they do not own.
4. Acceptance tests: each contract is frozen at its stated point · no non-owner mutates ·
   the document and `spine.py` agree on the contract shapes.

**Effort:** ~2 chapters. **Must be written alongside Volume IV** — III defines the contracts,
IV defines the order they are produced in. Splitting them across sessions will re-create the
drift.

---

## Volume IV — Cognitive Spine 🔴 **PRIORITY**

### What actually exists

| Artefact | State |
|---|---|
| `docs/architecture/16_spine_runtime.md` | **5 lines. `STATUS: PENDING — to be written in a dedicated session.`** Verified `wc -l` = 5 on 2026-08-13. |
| `runtime/spine/spine.py` | **610 lines of live, load-bearing code** — the actual turn loop. |
| `runtime/spine/` siblings | `plan.py` (203) · `presence_faculty.py` (452) · `control_plane.py` (213) · `relationship_faculty.py` (187) · `executive_faculty.py` (172) · `executive_extension.py` (52). **1,889 lines total.** |
| Callers | `server.py:2920` (`spine.run`), `:3345` (`update_session`) — **this is the live path every turn takes.** |

### Real spec or stub?
**STUB — and it is the load-bearing one.**

The Index names **code as canon**. That is not a shortcut; it is a category error with a
consequence: *the code cannot be wrong.* There is no document to check it against, so the
turn order — the single thing every other volume's chapters assume — is whatever `spine.py`
currently happens to do, and it changes without a canon amendment.

`AUDIT_INTENT_support_governance_2026-08-10.md:40` records that a task *"Build
16_spine_runtime.md"* was **marked completed**. It was not built. That is worth stating
plainly: the tracking said done, the artefact is five lines.

### Why this is the priority

**Volume IV is the turn loop everything else assumes.** Concretely, from the live code
(2026-08-13), `spine.run()` executes an ordered assembly that at least four written volumes
depend on being exactly this order:

```
perceive()                     → frozen PerceptionResult     (Vol XII — "WO-CANON-XII")
LiveWorldState assembled FIRST → frozen, read by all          (Vol XV  — "WO-CANON-XV")
Working Memory + Attention     → top-of-turn, before faculties(Vol VI  — "WO-CANON-VI")
CognitiveSnapshot              → assembled BEFORE any faculty decides (WO-052)
Language → Relationship → Capability → System faculties
UnifiedCognitiveState assembled BEFORE the Executive          (Vol XVI / ADR-Exec-006)
Executive Faculty              → ONE DECISION
… enrichment → Light Engine → Presence → EmbodimentState → Conversation
```

Every one of those markers is a **volume's core guarantee** — *"assembled once, at the top of
the turn, before faculties reason"* (Vol XV §1.4), *"assembled BEFORE the Executive"*
(ADR-Exec-006), *"one decision per turn"* (Runtime Invariant #2). **All of them are
guaranteed by an ordering that exists only as comments in a Python file.** Reorder two lines
in `spine.py` and four ratified volumes become quietly false, with nothing to detect it.

That is the argument for priority in one sentence: **Volume IV is the only place the
architecture's ordering guarantees can be written down, and it is currently five words
long.**

### What would need writing to reach the Vol XV bar
1. `Volume_IV/00_Metadata.md`. **There is no origin text** — this is the one of the five that
   must be written from the live system rather than promoted from an existing document.
2. **Chapter 1 — The Turn Order.** The canonical sequence above, each step with: what it
   produces, what freezes at that point, what may read it, and what must NOT run before it.
   This is the document Vol XII/XV/VI/XVI currently assume exists.
3. **Chapter 2 — Assembly and Freezing Discipline.** What "frozen" means at each stage, who
   may mutate what (this is where Volume III's contract-ownership chapter binds), and what
   happens when a contributor fails mid-assembly (degradation, never a blocked turn).
4. **Chapter 3 — Spine Failure and Degradation.** What a turn does when perception, world,
   working memory, or a faculty is unavailable. Volume XX (Cognitive Economy) has tiers;
   Volume IV must state where in the turn a tier drop is applied.
5. Acceptance tests — the highest-value tests in the whole canon:
   `FT: assembly order is exactly as specified` · `FT: the Executive decides exactly once` ·
   `ST: no faculty reads a contract before it is frozen` · `ST: any single contributor failing
   never blocks the turn` · `IT: the document and spine.py agree` (an executable
   canon-vs-code check — the thing whose absence let this drift happen).
6. Retire the 5-line `16_spine_runtime.md` with a pointer to `Volume_IV/`.

**Effort:** ~3 chapters, and the most research-heavy of the five (it is written *from* 1,889
lines of live code, not promoted from prose). **This is the one to do first.**

---

## Volume XIV — Plugin Architecture

### What actually exists — and a correction to the 2026-08-10 audit

`AUDIT_INTENT_support_governance_2026-08-10.md` recorded Volume XIV as *"**No canon at all.**
No `Volume_XIV/` dir, no chapter, no WO-CANON-XIV."* The first clause is **wrong** and is
corrected here (Rule #2 — verified 2026-08-13):

**`docs/plugin_system.md` exists: 260 lines, `Version 1.0 · Status: Active`.** It contains a
Principle section (*"Plugins extend output layers only… ALLOWED: core → plugin; FORBIDDEN:
plugin → core"*), a plugin interface, a capability vocabulary, layer rules (output / input /
observability), a lifecycle, safety constraints, four plugin skeletons (Unity · voice ·
memory visualiser · robot control), registration, and a forbidden-patterns section.

Live code matching it: `plugins/registry.py` (9.3 KB — registration, activation, fallback
chain, *"the behavior layer never imports plugins directly — it always calls the registry"*),
`plugins/base.py`, and five plugin packages (`anthropic`, `local_llm`, `vision`, `voice`,
`hardware`).

### Real spec or stub?
**A real spec — mis-filed, un-indexed, and in an unresolved boundary conflict.**

Three distinct problems, in order of severity:

1. 🔴 **Ownership conflict with Volume XXIII, with no ADR.** `ARCHITECTURE_BIBLE.md`'s scope
   for XIV is *"capabilities, **permissions, sandboxing**, extension API, hot swapping."*
   **Volume XXIII Ch.1 has absorbed permissions and sandboxing** — capability classes,
   approval gates, the threat matrix. No decision record transfers ownership. Two volumes,
   one subject, no boundary. **This must be resolved before XIV is written, or XIV will be
   written into a subject it may not own.**
2. ⚠️ **`docs/plugin_system.md` is outside the canon tree** (`docs/`, not
   `docs/architecture/`) and is not referenced by `00_CANON_INDEX.md`. It is canon nobody
   is pointed at.
3. ⚠️ **Missing volume blocks:** no frontmatter, no faculty contract, no lifecycle in the
   `CONTRACTS.md §3` form, no message envelope, no acceptance tests, no Definition of Done.
   Hot-swapping — named in the Bible scope — is not covered at all.

### What would need writing to reach the Vol XV bar
1. **Resolve the XXIII boundary first** (see Needs-David below). Everything else waits.
2. `Volume_XIV/00_Metadata.md` naming `docs/plugin_system.md` as origin text, with the
   ownership split stated explicitly in the metadata (as Vol XVII does with Vol V Ch.6).
3. **Chapter 1 — The Plugin Contract and the Registry.** Promote the existing interface,
   capability vocabulary and layer rules; add the faculty contract, lifecycle, envelope and
   tests. Ground in `plugins/registry.py` and `plugins/base.py`.
4. **Chapter 2 — Extension, Hot-Swap, and Degradation.** The un-covered part of the Bible
   scope: what a hot swap is, what it may not interrupt (never mid-turn), and how the
   fallback chain degrades — which is the same Groq→Cerebras→Ollama→Mock discipline the
   backend router already runs.
5. Acceptance tests: `ST: no plugin writes kernel state` (this is the volume's central
   guarantee and it is currently a prose rule) · `ST: a failing plugin degrades to the
   fallback chain and never blocks a turn` · `FT: a hot swap never interrupts a turn`.
6. Move or symlink `docs/plugin_system.md` into the canon tree, and add the Index row.

**Effort:** ~2 chapters, **but blocked** on the XXIII boundary ruling.

---

## Recommendation — priority order

**1. Volume IV — Cognitive Spine. Do this first, and do it with Volume III.**

It is the most load-bearing and the only genuine stub. It is the turn loop everything else
assumes, and today that loop's guarantees — *world assembled first* (XV), *working memory
before faculties* (VI), *unified state before the Executive* (ADR-Exec-006), *one decision
per turn* (Invariant #2) — exist **only as comments in `spine.py`**. Four written volumes
depend on an ordering with no canonical statement and no test. It is also the highest-value
target because its `IT: document and spine.py agree` test is the mechanism that prevents this
class of drift recurring anywhere.

Pair it with **Volume III** in the same push: III defines the contracts, IV defines the order
they are produced in. Written apart, they will drift from each other exactly as III has
already drifted from `spine.py`.

**2. Volume II — Cognitive Principles.** Cheap and self-contained. The document is good; the
gap is that principles are not a typed object and nothing can check that a turn obeyed them.
Two chapters, low risk, and it closes a gap the document itself already names at line 161.

**3. Volume XIV — Plugin Architecture.** The spec largely exists. **Blocked** on the
Volume XXIII ownership ruling — writing it before that is writing into a contested subject.
Unblock, then it is a short promotion job.

**4. Volume I — Philosophy.** Last, deliberately. The material is the most abundant and the
least urgent to formalise: `ARCHITECTURAL_PRINCIPLES.md` is already read, cited and enforced
in practice. Formalising Volume I changes little about how eLo is built; formalising Volume IV
changes whether the architecture can be verified at all. **Write the load-bearing one first.**

### What must not happen again

The `✅ Live (code)` mark is the mechanism that produced all five holes, and it produced three
more (VII, XI, XIII) that were only caught on 2026-08-10. **Recommended rule for the Canon
Index:** *code existing is never evidence that canon exists.* An implementation may be cited
as a volume's **grounding**; it may never be cited as its **spec**. The Index's `Canon spec:`
column should refuse a `.py` path.

---

## Needs David

- **F-1 — Volume XIV vs Volume XXIII ownership.** The Bible gives XIV *"permissions,
  sandboxing"*; Volume XXIII Ch.1 has already specified both, with no ADR transferring
  ownership. **Architect recommendation: XXIII keeps permissions, sandboxing, capability
  classes and approval gates (it is the security volume and has already built the threat
  model); XIV keeps the extension API, the registry, the plugin contract, and hot-swapping,
  and cites XXIII for anything a plugin is permitted to do.** Needs an ADR either way,
  because it is a scope transfer between two ratified-track volumes. **XIV is blocked until
  this lands.**

- **F-2 — Does `prompts/living_presence_spec.txt` become Volume I canon, or stay an
  implementation of it?** It is under FREEZE_V1_LOCK and D-K governs prompt unlock.
  **Architect recommendation: it stays an implementation.** Volume I's origin text is
  `ARCHITECTURAL_PRINCIPLES.md`; the prompt is where Volume I is *expressed*. But this
  determines whether editing the prompt becomes a canon act, which is David's call.

- **F-3 — The one-person framing.** `living_presence_spec.txt` uses *"the user"* 15 times
  and *"a human"* rather than David; `VISION.md` addresses a prospective buyer. This is
  product-era residue in the volume that defines who eLo is *for*. **Architect
  recommendation: name David in Volume I canon, and treat `VISION.md` as a marketing
  artefact rather than a cited spec.** Identity-level, therefore L3.

- **F-4 — `16_runtime_contracts.md`'s embedded TODO** (line 221, `Passive Awareness
  (Immediate Fix)`, undated). Either it is done and should be removed, or it is live and
  should be a WO. **Architect recommendation: the Architect drafts it out of canon and into
  a WO after the Builder confirms its state** — I cannot confirm from the document alone
  whether the fix shipped.

- **F-5 — Index correction authority.** Flipping five `✅ Live` marks to `⚠️ Partial` /
  `🔴 Stub` and pointing them at this page is an Index edit, which is in-lane for the
  Architect — but it changes five volumes' apparent status at once. **Flagged rather than
  done unilaterally.** Say the word and it is a five-minute edit.

---

## References

- `docs/architecture/00_CANON_INDEX.md` — the `✅ Live` rows and the Build Queue exemption.
- `docs/architecture/AUDIT_MASTER_2026-08-10.md:11-12` — the finding.
- `docs/architecture/AUDIT_INTENT_support_governance_2026-08-10.md:40, :178` — the per-volume
  verdicts (Vol XIV's *"no canon at all"* is **corrected** by this page).
- `docs/architecture/Volume_XV/` — the bar.
- Vol I: `ARCHITECTURAL_PRINCIPLES.md` · `prompts/living_presence_spec.txt` (418 lines) ·
  `VISION.md` (110) · `00_MANIFESTO.md` · `01_PRINCIPLES.md`.
- Vol II: `17_cognitive_principles.md` (189 lines; **line 161** is the finding).
- Vol III: `16_runtime_contracts.md` (256 lines; **line 221** the embedded TODO).
- Vol IV: `16_spine_runtime.md` (**5 lines, STATUS: PENDING**) · `runtime/spine/spine.py`
  (610) + `runtime/spine/*` (1,889 total) · `server.py:2920`, `:3345` (the live callers).
- Vol XIV: `docs/plugin_system.md` (**260 lines, v1.0 Active**) · `plugins/registry.py` ·
  `plugins/base.py` · `plugins/{anthropic,local_llm,vision,voice,hardware}/` ·
  `ARCHITECTURE_BIBLE.md` (XIV scope) · `Volume_XXIII/` (the conflicting owner).

---

```
Foundation Volumes — Honest Status (I · II · III · IV · XIV)
Status: READY FOR REVIEW · NOT RATIFIED
Files: docs/architecture/FOUNDATION_VOLUMES_STATUS_2026-08-10.md
Replaces: five misleading "✅ Live" Index marks
Corrects: AUDIT_INTENT_support_governance_2026-08-10's "Vol XIV — no canon at all"
Priority recommendation: IV (with III) → II → XIV (blocked on F-1) → I
Needs David: F-1 … F-5
```

READY FOR REVIEW
