# AUDIT — INTENT vs CANON: the SUPPORT & GOVERNANCE spine
### Group: I Philosophy · II Cognitive Principles · III System Architecture · IV Cognitive Spine · XIV Plugin Architecture · XX Cognitive Economy · XXIII Security & Trust · XXIV Knowledge · XXV Temporal · XXVI Creative · XXVII Engineering Standards & Canon Governance

**Auditing against:** `00_DAVIDS_VISION_SPINE.md` · `ARCHITECTURAL_PRINCIPLES.md` · `DECISION_LOG.md` ·
**`CANON_RULINGS_2026-08-10.md`** (David L3) — and the standing context that **eLo is now David's PERSONAL
tool; the Kickstarter / sharing / product track is PARKED** (`DISPATCH_BOARD.md` line 67, verbatim:
*"PERSONAL tool — for David's own use, NOT for sharing"*).

**Method:** read every volume chapter, every WO-CANON order in scope, the Decision Log end-to-end, and swept
the whole repo for every ADR/decision ID cited anywhere. Where I say "never written," I grepped for it.

**Lane:** Architect — Markdown audit only. No code, no volume edits. Everything actionable below is a relay.

---

## 0. HEADLINE — three things, blunt

1. **`LAW-017` is cited 20 times as binding law and has never been written.** It is the named authority for
   Volume XXIII's entire approval-scope model (§1.4.2, §2.4) and for four Work Orders. `LAW-001`–`LAW-016`
   do not exist anywhere in the repo. The security volume's trust model rests on a law ID with no
   definition record. That is the single worst governance hole in the canon.
2. **The canon still runs a two-architect, CA-gated review chain for SOFTWARE — which David dissolved on
   2026-08-10.** Volume XXVII encodes it as law across all three chapters, contains **zero** occurrences of
   `LG-2` (so it cannot even express the software/hardware split), and its own open question §3.8 Q1
   *recommends hardening* the second software reviewer. Every WO-CANON in scope still says "Gate: CA
   first-pass → David L3."
3. **The three ADRs David's own 2026-08-10 rulings depend on (`ADR-Exec-003/005/006`) were never written as
   ADRs.** They exist only as rows in a summary index table. Ruling C is justified by ADR-Exec-006; Ruling D
   by ADR-Exec-005. The ratification chain is anchored to entries that have no document.

---

## 1. VERDICT TABLE

| Vol | Spec'd? | Matches "personal tool" intent? | Encodes the 2026-08-10 rulings? | WO delivers? |
|---|---|---|---|---|
| **I — Philosophy** | 🔴 **No volume exists.** Index points at `VISION.md` (a 110-line pitch, zero contracts) + `prompts/living_presence_spec.txt` (a *runtime prompt* under `FREEZE_V1_LOCK`). Marked ✅ Live. | 🔴 `VISION.md` is written to a prospective buyer ("You open your laptop"); the prompt spec says *"help **a human**"* / *"**the person you are with** is a builder…"* and uses `the user` 15×. It refuses to name David. | n/a | ❌ **No WO exists.** |
| **II — Cognitive Principles** | ⚠️ `17_cognitive_principles.md` is a good doc, but line 161 states verbatim: **`Principles are not yet a typed object.`** No contract, no envelope, no tests. Marked ✅ Live; nothing is live. | ⚠️ Mixed — line 51 correctly says "David"; line 77 says "Protect **user** agency"; the constraint table is `| User seems distressed |`. | n/a | ❌ **No WO exists.** |
| **III — System Architecture** | ⚠️ `16_runtime_contracts.md` is real (four contracts, producer/consumer/mutator) but **drifted**: 8 of 9 convergence steps unchecked, and it contains an embedded stale TODO ("Passive Awareness (Immediate Fix) … Fix it before anything else"), undated. | 🟢 Neutral. | n/a | ❌ **No WO exists.** |
| **IV — Cognitive Spine** | 🔴 **The worst hole.** The Index names **code** (`runtime/spine/spine.py`) as canon. The written spec `16_spine_runtime.md` is **5 lines**, verbatim: `STATUS: PENDING — to be written in a dedicated session.` Task #10 "Build 16_spine_runtime.md" is marked *completed*. It was not built. | n/a | n/a | ❌ **No WO exists.** |
| **XIV — Plugin Architecture** | 🔴 **No canon at all.** No `Volume_XIV/` dir, no chapter, no WO-CANON-XIV. Index marks it ✅ Live on the strength of `plugins/` (registry, base, voice, vision, hardware, anthropic, local_llm). | 🔴 Bible scope for XIV is *"capabilities, **permissions, sandboxing**, extension API, hot swapping"* — **XXIII Ch.1 has silently absorbed permissions+sandboxing** with no ADR transferring ownership. Two volumes, one subject, no boundary. | ❌ | ❌ **No WO exists.** |
| **XX — Cognitive Economy** | ✅ **Good.** 3 chapters, all with contract + lifecycle + envelope + FT/ST/IT. Honest about gaps (tier→provider mapping, escalation gate, cost telemetry, mock-honesty gate all marked PENDING, not faked). | ✅ **Best-aligned volume in the group.** Cost-sensitivity is written in as an invariant; the Ollama `llama3.1:8b` floor is the cheap always-on baseline; "never premium-by-default"; "the floor is real, not mute." | ⚠️ Doesn't need the rulings — but its DoD still reserves *"CA review of the flagged open questions"* and *"David L3 on RESERVED-adjacent items"*. API spend is money = genuinely RESERVED, but there is now no second reviewer for it. | ⚠️ WO-CANON-XX is thorough and faithful. **Board says "▶ BUILD NOW"; the WO header still says "QUEUED behind Presentable v1 + Tier A"** and gates on "CA + David L3." Stale. |
| **XXIII — Security & Trust** | ✅ **Strongest governance volume.** 3 deep chapters grounded in live code (`execution_gate.py`, `registry.py`, `computer_control_agent.py`, `.env`), 5 capability classes, 7 safety defaults, T-1…T-11 threat matrix. | ⚠️ Good bones, **wrong gate model post-08-10** — see next column. Ch.1 §1.4.2's three-scope model (PERSON/COMPANY/RESERVED) still assumes a COMPANY seat lane and an org. | 🔴 **NO. This is the priority fix.** §1.4.2 and §2.4.2 say RESERVED = *"money · legal · safety · robot magnetics/force/pump"* requires *"David L3 **plus a second review (LG-2)**"* — **flat, with no software/hardware split.** David ruled the split on 08-10 and the volume was not amended. Also: **no `thermal`, no `battery`, no `pinch points`** in the RESERVED list (the ruling names all three). `OQ-1.8.1` (single flag vs per-capability) is **answered** — single switch — and still sits open in the text. `OQ-2.7.3` ("who is LG-2?") is *partially* answered and still open. | ⚠️ WO-CANON-XXIII is a solid hardening order, but it is **built around the wrong premise**: its stated headline goal is *"the one genuinely-external item — get David to **define LG-2**."* David already ruled: software has no LG-2, hardware keeps it. The WO still gates the **whole volume** on that definition, still blocks on the answered `OQ-1.8.1`, and still says "Gate: David L3 (LG-2 + the RESERVED/safety OQs) + **CA acceptance** before promotion." |
| **XXIV — Knowledge Architecture** | 🔴 **Thinnest volume in the group. 1 of 12 required blocks present.** Ch.1 has a faculty contract; Ch.2 and Ch.3 have none. No lifecycle, no envelope, no acceptance tests in any chapter. Metadata has no Definition of Done and no invariants list. `tests/test_canon_xxiv_knowledge.py` does not exist. | 🔴 **The ontology cannot represent David's life.** `type` enum = `character · companion · state · mechanic · world_stage · brand · system · project`. **No `person`, no `place`, no `event`.** eLo cannot durably know David's family, his address, his appointments. For a daily personal tool that is the biggest hole in the volume. Meanwhile ~⅓ of the live entity graph (`elo_os`, `elo_book`, `elo_game`, `elo_robot`) is canon about the **parked** product track, and §1.0 canonises *"the OS · game · book · robot are four bodies of one being."* | 🔴 **Ruling A landed and the volume was not updated.** Three places still call it *"Blocking decision for CA/David"* / *"Decision required (CA/David)"*; metadata line 25 still lists the retired `identity/world_graph.json` as an anchor; **the file is still on disk.** | ❌ **Under-scoped.** WO-CANON-XXIV delivers Ch.2's field additions and Ch.3's compression rules only. It omits the **promotion threshold** (the knob deciding what eLo learns permanently), **demotion/supersede** (nothing can be unlearned), multi-hop inference (making `kind: inference` unproducible), the id-namespace migration its own determinism rule depends on, and the Ch.1 faculty itself. WO says P3 + *"gated on ruling A … do not touch either store"*; board says P2 + RELEASED. |
| **XXV — Temporal Cognition** | ✅ **Exemplary on paper — 12/12 blocks, every chapter.** 🔴 **Badly landed.** Board says `DONE ✅ 19/19 → IN_REVIEW`. The build (`faculties/temporal/faculty.py`) has **no `Anticipation` class at all**, no envelope, no lifecycle, `expires` is a `bool` instead of a timestamp, `circadian_phase` is 3 values instead of 5 (so FT-3 cannot pass as written), and **nothing imports it** — grep for `faculties.temporal` returns only the test file. It is dead code marked DONE. | 🔴 **The one thing David most wants from temporal cognition is forbidden.** Ch.2 §2.1.4: *"It cannot create a goal, start a task, or **send a reminder**."* And David cannot state his own quiet hours anywhere — `§1.7 Inputs` offers only a fixed curve or learned cadence. Product-era residue: *"Are these **user-configurable**"* (OQ-2), *"a **daily user** vs a **monthly user**"* (Ch.3 §3.11 OQ-2). There is one user. | 🔴 **Direct contradiction with the XXVI taste ruling — the most serious in this audit.** Four sections put **learned cadence on top with nothing above it**: §1.5 *"overridable by the **learned rhythm** of the specific person"*, OQ-1 *"**Leaning learned-from-continuity**"*, §1.4, Ch.3 §3.3 *"**learned via continuity, not hardcoded**."* A circadian rhythm inferred from cadence history is **learned from when David is absent** — i.e. *inferred from silence*, exactly what the 08-10 ruling forbids. No stated-outranks-learned precedence rule exists anywhere in Volume XXV. | ⚠️ WO-CANON-XXV scopes Ch.1/Ch.2/Ch.3 rule-sets faithfully but **silently drops** the message envelope (compressed to one line — which is *why* the build emits bare dataclasses), the lifecycle, `relationship_freshness`/`cadence_history`, the whole Vol XXI thread-arc integration, and **never requires wiring**. Hence a faculty nothing calls. WO header still says "QUEUED"; board says DONE. |
| **XXVI — Creative Intelligence** | ✅ **Well spec'd.** 3 chapters, full contracts/lifecycle/envelope/tests, six-term evaluation with `identity_alignment` as a hard floor, `AestheticProfile` with mandatory provenance. | 🟢 Good — creativity is framed as David's amplifier, not a replacement; generators emit *briefs*, not assets (mirrors D-LANES). ⚠️ §2.6 still gates plushies/toys on *"materials safe for handling, **IP, cost**"* and an *"audience"* — product-track framing on a parked track. | ✅ **The substance is already correct — but recorded as an open question, not as law.** §3.4 states verbatim *"**Stated direction outranks learned preference**"* and *"Learned signals update only from verified consequences … No entry is created from eLo's self-generated praise"*, plus `silence_policy: explore_within_canon`. §2.5 already says music is *"exploration only"* and *"the anchor … is a genuine open input, not something eLo may invent."* **That IS David's 08-10 ruling — but it is written as `D-XXVI-A` / `D-XXVI-D` "Requires David's call", flagged 15× and 9× as still-open.** The ruling closed both; nothing was updated. | ⚠️ WO-CANON-XXVI is a good, detailed build order — and its status line still reads *"**Gated on David L3 (taste)** — nothing dispatches on the identity/brand/canon path until that lands."* **It has landed.** The WO is self-blocking on a decision that is made. It also still routes RESERVED product/fashion to *"David L3 + LG-2"* — correct for the physical robot, **wrong for a plushie spec that is pure software output**. |
| **XXVII — Eng Standards & Canon Governance** | ⚠️ Best-*written*, least-*binding*. 1,058 lines, three chapters, proper frontmatter — but it says of itself *"This chapter **invents almost nothing**"*, *"It authors no new process"*, *"the source wins and this chapter is the one corrected."* It is a pointer table. **No chapter carries FT/ST/IT tests**, and Ch.1 §1.9 Q1 admits it **cannot pass its own Definition of Done**. | 🔴 **XXVII does not know eLo is a personal tool.** It formalises an **eight-seat org** with two architects and three review authorities; §2.4.1 scopes *"User birth data"*; §3.8 Q2 plans *"Release cadence for the Life Era"*; §2.1 sets the handover bar at *"a person who has never seen the project… can start implementing within one session."* That bar is written for onboarding staff who do not exist. | 🔴 **Worst offender.** §1.5: *"a document is **never** marked RATIFIED or COMPLETE by the drafting Architect … IMPLEMENTATION READY and COMPLETE are conferred at review gates by **the Chief Architect and David (L3)** respectively."* §1.7 RFC flow requires *"**Chief Architect first-pass** → David L3 ratification."* §3.3 RESERVED list omits **thermal/battery/pinch points**. **Grep for `LG-2` across `Volume_XXVII/` returns ZERO hits** — the volume that owns canon governance has no vocabulary for the ruling's central distinction. And §3.8 Q1 recommends *"**name it**"* — i.e. formally harden CA first-pass as Gate 1a — three days before David ruled it away. | ❌ WO-CANON-XXVII delivers a *plan* to deliver the volume. It is P4, blocked on **11 rulings**, has **no `Files to touch` / `Must not touch` section** (violating Volume XXVII Ch.3 §3.2's own non-negotiable rule — a governance WO failing the governance standard it enforces), and **five of its six acceptance tests are unfalsifiable** ("holds for a sample promotion" — no sample named). Its one measurable test (the pre-commit secret check) belongs to Volume XXIII. It never cites `CANON_RULINGS_2026-08-10.md`, `LG-2`, `RESERVED`, or "personal tool" once. |

---

## 2. ADR SWEEP — every decision ID cited across the canon

Swept `docs/` + `engineering/` for every `ADR-*`, `LAW-*`, `D-*`, `CA-*`, `EA-*`, `FC-*`, `DEC-*` token.
"Written" = there is a document or a `##` section that *defines* it, not merely a row or a citation.

| ID | Written? | Where defined | Cites | Gap |
|---|---|---|---|---|
| **ADR-0001 / D-A** — Faculty Bus envelope + 7 laws | ✅ Full | `DECISION_LOG.md` §11 | 19 | — |
| **ADR-0002 / D-B** — Unified faculty lifecycle | ✅ Full | `DECISION_LOG.md` §26 | 11 | — |
| **ADR-0003** — Vols XXIII–XXVII become Canon | ✅ Full | `DECISION_LOG.md` §89 | 12 | — |
| **ADR-Exec-001 / ADR-Executive-001** — Verified Executive Authority | ✅ Full | `DECISION_LOG.md` §271 | 67 + 6 | ⚠️ **Two live spellings for one ADR** in the same file. |
| **ADR-Exec-002 / ADR-Executive-002** — Single Cognitive Truth | ✅ Full | `DECISION_LOG.md` §340 | 28 + 4 | ⚠️ Same dual-spelling problem. |
| **ADR-Exec-003** — Embodied Truth + Embodied Cognition + Situated Cognition + Affordance-Before-Action + Presence-is-a-state | 🔴 **NO** | **Index table row only** (`DECISION_LOG.md` line 238). Substance lives in `ARCHITECTURAL_PRINCIPLES.md` + `EMBODIED_COGNITION.md`, un-ADR'd. | 14 | **HOLE.** Five separate principles bundled into one ID that has no document. Cited as `ACCEPTED · LAW (David L3)`. |
| **ADR-Exec-004** — Situated Self (Invariant #5) | 🟠 Row only | Index row (line 239) — substantive, but not an ADR section. Principles Inv. #5 + `SITUATED_SELF_v1_assembly.md` carry the real content. | 34 | Form gap. Cannot be cited by section. |
| **ADR-Exec-005** — Learning Through Verified Consequences | 🟠 Row only | Index row (line 240) | **103 — most-cited ADR in the canon** | **HOLE.** The single most-referenced law in eLo's canon exists only as a table cell. **Ruling D (2026-08-10) is justified by it.** |
| **ADR-Exec-006** — Executive Assembly / UnifiedCognitiveState | 🟠 Row only | Index row (line 241) | 80 | **HOLE.** **Ruling C (2026-08-10) is justified by it.** |
| **ADR-Learn-001** | ⚠️ Absorbed | Noted inside ADR-Exec-005's row as *"one learning ADR, not two"* | 1 | Orphan prefix; acceptable. |
| **ADR-Corp-001** | 🔴 **NEVER WRITTEN** | Cited once, in `_intake/SOURCE_2026-08-08_self_model_becoming.md`, as **"Canon: ADR-Corp-001"** for WO-080 (Company Knowledge Interface). No such ADR exists anywhere. | 1 | **REAL HOLE** — a WO is specced against a canon reference that does not exist. |
| **LAW-017** — "actions route through the Executive + David's L3" | 🔴 **NEVER WRITTEN** | Nowhere. Volume XXIII cites *"`00_DAVIDS_VISION_SPINE.md` — LAW-017"*; the Vision Spine only **uses** the token in passing (line 43), it never defines it. | **20** | **THE BIGGEST HOLE.** It is the named authority for Vol XXIII §1.4.2 (authority scope) + §2.4 (approval gates), `WO-CANON-XXIII`, `WO-EA2-1/-2`, `WO-INT7-HEAT`, `AGENT_HANDOFF_PACKETS`. Also cited as **"LAW-017 Amendment 7"** — an amendment to an undefined law. **`LAW-001`–`LAW-016` do not exist anywhere in the repo.** |
| **D-C**, **D-D** | 🔴 Never existed | — | 0 (the two `D-C` hits are an unrelated dispatch-board cell) | Letter series runs A, B, **skip**, E. Cosmetic, but breaks "IDs are immutable, append-only" auditability. |
| **D-E** Dream=Vol IX · **D-F** Memory ownership · **D-G** Working-memory ownership | ✅ Full | `DECISION_LOG.md` §40/§46/§52 | 8 / 48 / 35 | — |
| **D-H** CEO-Agent target · **D-I** Builder write-scope · **D-J** INT-6b · **D-K** prompts unlock · **D-L** Debug mode | ✅ Full | `DECISION_LOG.md` §118/§129/§140/§160/§197 | 8/35/11/27/5 | — |
| **D-M** Change Control | ✅ Full (delegating) | `DECISION_LOG.md` §212 → `engineering/work_orders/CHANGE_CONTROL.md` | 18 | — |
| **D-PRESENCE · D-SESSIONS · D-LANES · D-VOL-V-READY · D-FREEZE · D-BUILD-NOW** | ✅ Full | `DECISION_LOG.md` (own `##` sections) | 33/4/23/3/9/7 | ⚠️ Vol XXVII quotes **D-FREEZE** as live doctrine; `DECISION_LOG.md` line 405 says D-BUILD-NOW **SUPERSEDES** it and *"D-FREEZE misread the intent."* |
| **D-AUTONOMY · D-CONTINUITY** | 🟠 Row only | Index rows (lines 236–237) | 1 each | Minor form gap. |
| **FC-1** `elo_state.json` | ✅ RESOLVED | `DECISION_LOG.md` §61 | 5 | — |
| **FC-2** Significance formula (9 dims vs V Ch.5's 5-term) | ✅ Written | `DECISION_LOG.md` §66 | 29 | ⚠️ **Still `DRIFT → reconcile`, open since 2026-07-27.** 29 citations of an unreconciled drift. |
| **CA-001 · CA-002 · CA-006 · CA-010 · CA-011 · CA-012** | 🔴 **Not in `docs/`** | Cited from `00_MANIFESTO.md` + `01_PRINCIPLES.md` as if authoritative; no definition file found in the canon tree. | 1/1/2/1/4/3 | **HOLE** — Chief-Architect recommendation IDs cited as settled with no record. |
| **EA-0 · EA-2 · EA-3** | 🟠 Partial | **`EA-3` = `Output/DISENELO_UNIVERSAL_RUNTIME_EA3.md` — exists, but OUTSIDE the repo**, in the Output tree that is off-limits to the Builder (D-I). `EA-0` / `EA-2` not located. | 4/2/24 | **HOLE** — 24 citations of a canon document that lives outside the canon, in a lane no seat may write to. |
| **DEC-EMERGENCE** | 🟠 Defined off-ledger | `00_MANIFESTO.md` line 101 — *"✅ RATIFIED by David 2026-07-29"* | 3 | Ratified but never appended to `DECISION_LOG.md`. Violates XXVII §1.1 (*"All ADRs live in one append-only ledger"*). |
| **Ruling A / C / D + the XXIII/XXVI/XXI/XXII rulings (2026-08-10)** | ⚠️ Written, **mis-filed** | `CANON_RULINGS_2026-08-10.md` (standalone file) | — | **HOLE (procedural).** XXVII §1.1: *"All ADRs live in one append-only ledger, `DECISION_LOG.md`."* They don't. `DECISION_LOG.md` carries **one un-headed bullet at line 413** — no ID, no status, absent from all three indexes. **There is no Ruling B** (A → C → D). By XXVII §1.2's own test (*"a promotion not reflected in the Index did not happen for governance purposes"*), **the most consequential rulings in the canon did not happen.** |
| **D-XXVI-A…I · D-XVI-A/B/C · D-IX-A…G · D-VI-*** | ⚠️ Volume-local | Defined in their own volumes' open-question sections; never elevated to the Decision Log | 15/9/… | **D-XXVI-A and D-XXVI-D are ANSWERED by the 08-10 ruling and still flagged open in three files each.** |

**Six incompatible ID schemes are live simultaneously** (`ADR-NNNN`, `ADR-Exec-NNN`, `ADR-Executive-NNN`,
`D-<letter>`, `D-<WORD>`, `CA-NNN`, `EA-N`, `FC-N`, `LAW-NNN`, `DEC-<WORD>`, untagged `Ruling A/C/D`).
Three have unexplained gaps (`D-C/D-D`, `Ruling B`, `LAW-001`–`016`). One has two spellings. Volume XXVII
§1.9 Q2 flags exactly this and proposes `ADR-YYYY-NNN` — **still unratified**, and the 08-10 rulings were
filed *after* that recommendation with no ID scheme at all.

---

## 3. DETAIL — the gaps that matter

### 3.1 XXIII does NOT encode the software-vs-hardware LG-2 split ⚠️ PRIORITY

David's ruling, verbatim (`CANON_RULINGS_2026-08-10.md` §XXIII):

> **Software RESERVED collapses:** for desktop behaviour, canon, memory, personality — **David is both L3
> and LG-2.** No second reviewer needed; it's a personal tool.
> **Hardware RESERVED does NOT collapse.** **The robot is a physical object** — magnets, actuators, force,
> pump, thermal, battery, pinch points. **LG-2 is RETAINED as a real, separate second review for the robot
> lane**, and must not be the same person who designed the part.

What Volume XXIII actually says (unamended, §2.4.2):

> The RESERVED set — money · legal · safety · robot magnetics/force/pump — requires David L3 **and a second
> review (LG-2)** before any commit … **One authority is insufficient; RESERVED needs two.**

**Three concrete defects:**
- **No split.** RESERVED is one flat set with one flat dual-gate. Software RESERVED (money, legal) and
  hardware RESERVED (force, magnetics) are governed identically. The ruling's entire point is that they
  are not.
- **Incomplete hardware list.** Volume XXIII (and XXVII) name `magnetics/force/pump`. The ruling names
  **thermal, battery, pinch points** as well. Three physical hazard classes are outside the canon's
  RESERVED set today.
- **The "not the designer" clause is missing entirely.** The ruling's hardest constraint — *"must not be
  the same person who designed the part"* — appears nowhere in Volume XXIII, Volume XXVII, or any WO.
  Neither does the operational gate: *"**LG-2 (force limiter / soft-stop scope) must be DONE before
  anything is powered near David.**"* That is a safety pre-condition with no canon home.

**What XXIII *does* get right:** §2.5.3 already states *"`ELO_COMPUTER_CONTROL` on the desktop does not
authorise physical actuation on the robot … the safety envelope is per-body."* That is the correct
instinct — the ruling makes it law. And **`OQ-1.8.1` is answered**: the ruling says *"`ELO_COMPUTER_CONTROL`
stays a **single switch** (not per-capability) — simpler is safer for one user."* The volume still lists it
as *"Flagged — needs David's call."*

### 3.2 XXVI has the taste rule right in the body and wrong in the status ✅/⚠️

Volume XXVI §3.4 already reads, verbatim: **"Stated direction outranks learned preference. An explicit
David directive always beats an inferred pattern."** And **"Learned signals update only from verified
consequences … No entry is created from eLo's self-generated praise, an imagined conversation, or a thing
eLo merely proposed."** And `silence_policy: "explore_within_canon"` — *"Silence is explored, not filled."*
§2.5 already treats music as **exploration-only** and says *"the anchor (David's sonic direction) is a
genuine open input, not something eLo may invent."*

**That is David's ruling, already written.** The failure is purely one of status: it is recorded as the
*proposed default* answer to **`D-XXVI-A`** and **`D-XXVI-D`**, both still marked *"Requires David's
call"* / *"LOAD-BEARING"* in the metadata, both chapters, and `WO-CANON-XXVI`. The WO's status line still
reads *"Gated on David L3 (taste) — nothing dispatches on the identity/brand/canon path until that lands."*
**It landed on 2026-08-10.** The whole volume is self-blocked on a closed question.

One residual mismatch: §2.6 routes plushie/product *specs* to *"David L3 + a second gate"*. Under the
ruling, a **design brief** is software output → David alone. Only the **physical build** keeps LG-2.
As written it re-imposes the collapsed gate on Markdown.

### 3.3 XX serves a cost-sensitive single user — the best-aligned volume here ✅

`Volume_XX/00_Metadata.md` states it plainly: *"it never spends premium cost by default (**David is
cost-sensitive**; the Ollama `llama3.1:8b` floor is the cheap always-on baseline)."* Invariants 2 and 3
encode cheapest-capable-by-default and a real (not mute) local floor. Ch.2 §2.3 makes the posture explicit:
*"prefer the floor; escalate on demonstrated need, not by default."*

**Gaps that a single user actually feels:**
- **No cost telemetry exists.** Ch.2: *"there is no cost telemetry, no per-turn budget accounting, and no
  expected-value estimate in the router today."* David cannot see what eLo costs him.
- **The escalation gate has no home in code** and no ruled owner (OQ-1: Executive vs pre-router policy).
- **`_AUTO_LOCAL_MAX_CHARS = 80` is declared and unwired** — a dormant lever, flagged retire-or-wire.
- **No spend ceiling.** Nothing in the volume lets David set a hard monthly cap. For a personal tool
  paid from a personal card, that is the missing control.
- **Streaming privileges the premium engine** (OpenAI-only) against the cheap-first bias — flagged, unresolved.

### 3.4 XXV's learned-cadence model contradicts the taste ruling 🔴

Four sections of Volume XXV put **learned** rhythm on top with no precedence rule above it (§1.4, §1.5,
Ch.1 OQ-1 *"Leaning learned-from-continuity"*, Ch.3 §3.3). A circadian curve inferred from *cadence
history* is a model built from **when David did not speak** — inference from silence. The 08-10 ruling
forbids exactly that: *"eLo may learn taste **only from decisions David actually made** — never inferred
from silence."* The ruling is scoped to XXVI/taste, but the mechanism is identical and Volume XXV has no
stated-outranks-learned rule at all. **This needs a written amendment, not a review-log note.**

Compounding it: **David has no way to state his rhythm.** `§1.7 Inputs` lists a fixed local-time curve and
`cadence_history`. There is no "David says quiet hours are 1am–9am" input anywhere in the volume.

### 3.5 The Volume I–IV foundation is marked ✅ and is not there

`00_CANON_INDEX.md` marks all four ✅ Live. In reality: I is a pitch document plus a **frozen runtime
prompt**; II admits *"Principles are not yet a typed object"*; III has drifted and carries an embedded
stale TODO; **IV is a 5-line stub that says `STATUS: PENDING`** while the Index names `spine.py` (code) as
its canonical spec.

That last one inverts the canon's own supreme rule, three times over:
- `16_runtime_contracts.md` line 5: *"If code conflicts with this document, **the document is right**."*
- `00_philosophy.md` line 127: *"When architecture changes, spine.py changes to match. **Not the other way around.**"*
- Volume XXVII Ch.1 §1.0: *"**Canon before implementation.**"*

Also found in passing: **duplicate document numbers** (`16_runtime_contracts` + `16_spine_runtime`;
`17_cognitive_principles` + `17_memory_update`) violating XXVII §2.1's *"Sequential numbering, never
reused"*; and `00_philosophy.md`'s own document index does not know `17_cognitive_principles.md` — Volume
II's canonical spec — exists.

### 3.6 Volume XIV is a ghost

No directory, no chapter, no WO, no mention outside four index/audit rows. The Bible's XIV scope is
*"dynamic loading, capabilities, **permissions, sandboxing**, extension API, discovery, dependency
injection, hot swapping."* **Volume XXIII Ch.1 now owns permissions and sandboxing** (`registry.py`,
`capability.py`, capability classes, filesystem scope, capability isolation) with no ADR transferring
ownership. Meanwhile `plugins/` (registry, base, voice, vision, hardware, anthropic, local_llm) has **no
canon and no security review at all** — a dynamic code-loading surface sitting outside the threat model.
T-1…T-11 does not mention plugins once.

---

## 4. PRODUCT-ERA ASSUMPTIONS STILL LINGERING

The board is unambiguous (line 67): *"**PERSONAL tool — for David's own use, NOT for sharing.** The
sharing/business tracks (Kickstarter, MK-*, …) are PARKED."* The canon has not caught up.

| # | Where | Verbatim | Verdict |
|---|---|---|---|
| 1 | `Volume_XXVII` (all 3 ch) | An **eight-seat role table**, two architects, three review authorities; *"CA review sits between the Architect's first-pass and David's ratification"*; *"IMPLEMENTATION READY and COMPLETE are conferred … by the Chief Architect and David (L3)"* | 🔴 **Retire.** Software canon = David alone (08-10). |
| 2 | `Volume_XXVII` §2.1 | Handover bar: *"a person who has never seen the project… can start implementing within one session"* | 🔴 Written for staff who don't exist. Re-scope to "future-me after a compaction." |
| 3 | `Volume_XXVII` §3.8 Q2 | *"Release cadence for the **Life Era**"* | 🟠 There is no release audience. Re-scope to "when David feels it's coherent." |
| 4 | `Volume_XXVII` §2.4.1 | security scope includes *"**User** birth data"* | 🟠 It's David's birth data. |
| 5 | `Volume_XXIV` §1.0 + `type` enum | *"the OS · game · book · robot are **four bodies of one being**"*; entities `elo_os`, `elo_book`, `elo_game`, `elo_robot`; enum includes `brand`, `project` | 🟠 ~⅓ of the knowledge graph is canon about a parked venture, while `person`/`place`/`event` don't exist. **Re-scope the ontology to David's actual life.** |
| 6 | `Volume_XXV` Ch.1 OQ-2, Ch.3 §3.3/OQ-2 | *"Are these **user-configurable**"* · *"a **daily user** vs a **monthly user**"* · *"the person's cadence"* | 🟠 One user. Replace learned-cadence abstraction with David-stated values. |
| 7 | `Volume_XXVI` §2.6 | product constraints incl. *"**IP**, cost"*, *"audience (the book's **readership**)"*, §2.7 *"player audience"* | 🟠 Legitimate for the *creative canon*; not for a parked commercial track. Re-scope to "David's own read." |
| 8 | `Volume_XXIII` §1.4.2 | COMPANY/SEAT scope as a first-class authority tier | 🟠 The seat structure is real (Builder/Designer/Game) but "COMPANY state" as a governed asset is org-era. |
| 9 | `prompts/living_presence_spec.txt` (Vol I) | *"help **a human** think"* · *"**the person you are with** is a builder, artist…"* · `the user` ×15 · line 404 *"When a user is developing a **product** idea, pitch…"* | 🔴 **The spec deliberately avoids naming David.** For a personal tool that is backwards. (Note: `prompts/` is under `FREEZE_V1_LOCK` — this needs a D-K-style scoped unlock, Builder lane.) |
| 10 | `VISION.md` (Vol I) | *"**You** open your laptop"* · *"knows **your** work"* · *"when **you ship it**"* | 🔴 A pitch deck sitting where Volume I should be. |
| 11 | `00_DAVIDS_VISION_SPINE.md` line 55 | *"Embodied interaction is **the product**; conversation lives inside it"* | 🟠 Vision Spine is append-only and David's words — do **not** edit. But "the product" now means "the thing David uses," and downstream volumes should stop inheriting a commercial reading of it. |
| 12 | `_intake/RD-1.md:48`, `RD-2.md:42,59,62` | *"opens RD-5 (**Kickstarter build-in-public notes**)"* · *"makes great **Kickstarter build-in-public** content (RD-5) **today**"* | 🟠 Live R&D intake still queuing work against a parked track. Mark RD-5 PARKED. |

---

## 5. CONTRADICTIONS REGISTER

| # | A | B | Severity |
|---|---|---|---|
| C-1 | Vol XXV: circadian rhythm *"overridable by the **learned** rhythm"*, *"leaning learned-from-continuity"* (×4 sections) | Ruling 08-10: *"David's **stated** direction OUTRANKS anything learned … never inferred from silence"* | 🔴 **High** — needs a written amendment. |
| C-2 | Vol XXIII §2.4.2: RESERVED is one flat set, always David L3 **+ LG-2** | Ruling 08-10: software RESERVED collapses to David alone; hardware keeps LG-2 | 🔴 **High** |
| C-3 | Vol XXVII §1.5/§1.7: CA first-pass is a **required** gate for canon; CA confers IMPLEMENTATION READY | Ruling 08-10: *"for … **canon**, memory, personality — David is both L3 and LG-2. **No second reviewer needed**"* | 🔴 **High** |
| C-4 | Vol XXVII §3.1: *"Chief Architect … **issues ADRs / rulings that become law**"* | Vol XXVII §1.3: *"only David (L3) confers ratification"*; Vision Spine: David is sole L3 | 🟠 In tension **inside the same volume**. |
| C-5 | Vol XXIV ×3 places: canonical world graph is *"a **blocking** decision for CA/David"* | Ruling A: `relationships/world_graph.json` is CANONICAL; `identity/` RETIRED — **and the retired file is still on disk** | 🟠 Medium |
| C-6 | Vol XXVI: `D-XXVI-A` + `D-XXVI-D` flagged *"Requires David's call"* (24 citations) | Ruling XXVI answered both | 🟠 Medium |
| C-7 | Vol XXIII OQ-1.8.1: *"single flag, or per-capability opt-ins? **Flagged — needs David's call**"* | Ruling: *"`ELO_COMPUTER_CONTROL` stays a **single switch**"* | 🟠 Medium |
| C-8 | Board: `WO-CANON-XXV` **DONE ✅ 19/19 → IN_REVIEW** | WO file: *"QUEUED behind Presentable v1"*; Vol XXV DoD: *"blocked on … WO-078"*; build has **no `Anticipation`, no envelope, and is imported by nothing** | 🔴 **High** — a DONE row over dead code. |
| C-9 | Board: `WO-CANON-XXIV` **P2, RELEASED, buildable now** | WO file: *"P3 … gated on ruling A … **do not touch either store**"* | 🟠 Medium |
| C-10 | Board: `WO-CANON-XX` **▶ BUILD NOW — no hold** | WO file: *"QUEUED behind Presentable v1 + Tier A"*, gates on *"CA + David L3"* | 🟠 Medium |
| C-11 | Vol XXVII quotes **D-FREEZE** as live doctrine (*"the Architect's job becomes protection, not authorship"*) | `DECISION_LOG.md` §405: **D-BUILD-NOW SUPERSEDES D-FREEZE** — *"D-FREEZE misread the intent"* | 🟢 Low |
| C-12 | Vol XXVII §1.1: *"All ADRs live in one append-only ledger, `DECISION_LOG.md`"* | The 08-10 rulings live in a standalone file, unnumbered, with one un-headed bullet in the ledger and no index entry | 🔴 **High (procedural)** — by XXVII's own test the rulings "did not happen." |
| C-13 | Index: Vol IV's canonical spec is `runtime/spine/spine.py` (**code**) | `16_runtime_contracts.md`: *"If code conflicts with this document, the document is right"*; XXVII: *"Canon before implementation"* | 🟠 Medium |
| C-14 | Bible: Vol XIV owns *"permissions, sandboxing"* | Vol XXIII Ch.1 owns permissions + sandboxing, with no ADR transferring it | 🟢 Low but real — resolve by retiring XIV's overlap or writing the boundary. |
| C-15 | Vol XX Ch.2: `_AUTO_LOCAL_MAX_CHARS = 80` documented as a *"declared local/cloud split threshold"* | Same paragraph: *"**not referenced** in `route()` — a dormant lever, not a live one"* | 🟢 Low |

---

## 6. DO THE WO-CANON ORDERS DELIVER?

| WO | Delivers the volume? | The problem |
|---|---|---|
| **WO-CANON-XX** | ⚠️ Yes, scope-wise | Faithful to all three chapters incl. the mock-honesty gate. **Stale header** (QUEUED vs board's BUILD NOW) and gates on a CA lane that no longer exists. Adds no spend-ceiling control. |
| **WO-CANON-XXIII** | 🔴 **No — wrong premise** | Its stated headline external item is *"get David to **define LG-2**"* — already ruled. Still blocks the **whole volume** on it; still lists the answered `OQ-1.8.1` as a blocker; still requires *"CA acceptance"*. Does **not** scope the software/hardware split, the missing hazard classes (thermal/battery/pinch), the "not the designer" clause, or the *"LG-2 force-limiter DONE before anything is powered near David"* pre-condition. |
| **WO-CANON-XXIV** | 🔴 **No — materially under-scoped** | Delivers Ch.2 fields + Ch.3 compression. Omits: the **promotion threshold** (what eLo learns permanently — undefined and shipping), **demotion/supersede** (nothing can be unlearned), multi-hop inference (making `kind: inference` unproducible by the delivered code), the id-namespace migration its own determinism rule depends on, hot reload, and the Ch.1 faculty structure. Also silently **pre-decides** two unruled OQs (composition confidence, cold-knowledge backfill). |
| **WO-CANON-XXV** | 🔴 **No — and the build proved it** | Drops the message envelope to one line (→ build emits `expires: bool`), drops the lifecycle, drops `relationship_freshness`/`cadence_history`, drops the entire Vol XXI thread-arc integration, and **never requires wiring**. Result: a faculty with no `Anticipation`, no envelope, and **zero importers**, marked DONE on 19/19 tests that were written from the WO rather than the chapters' FT/ST/IT blocks. |
| **WO-CANON-XXVI** | ⚠️ Good order, self-blocked | Detailed and faithful. Status still *"Gated on David L3 (taste)"* on a landed ruling; still routes software design briefs to *"David L3 + LG-2"*. |
| **WO-CANON-XXVII** | 🔴 **No — it is a plan to make a plan** | P4, blocked on **11 rulings**, **no `Files to touch` / `Must not touch`** (violating Vol XXVII Ch.3 §3.2 — a governance WO failing its own standard), **5 of 6 acceptance tests unfalsifiable**, its one measurable test belongs to Vol XXIII, and it never mentions the 08-10 rulings, `LG-2`, or "personal tool." |
| **XIV, I, II, III, IV** | ❌ **No WO exists at all** | Five volumes with no build order and no canon. |

---

## 7. RELAYS (Architect actions — Markdown only; nothing here is code)

**P0 — write the missing law**
1. **Write `LAW-017`.** Either author it as a proper ADR in `DECISION_LOG.md`, or retire the token and
   replace all 20 citations with the ADR that actually carries the rule. As it stands the security volume
   cites a phantom. Same pass: decide what "LAW-017 Amendment 7" refers to.
2. **File the 2026-08-10 rulings as numbered ADRs in `DECISION_LOG.md`** with `##` sections, IDs, status,
   and index entries — per Vol XXVII §1.1/§1.2. Explain or close the missing **Ruling B**.
3. **Promote `ADR-Exec-003/004/005/006` from index rows to real ADR sections.** 231 combined citations,
   including the justification for Rulings C and D, currently rest on table cells.

**P0 — apply the rulings to the volumes**
4. **Amend Vol XXIII §1.4.2 + §2.4.2**: split RESERVED into SOFTWARE-RESERVED (David alone, L3+LG-2 in one
   person) and HARDWARE-RESERVED (David L3 + a real separate LG-2 who did not design the part). Add
   `thermal`, `battery`, `pinch points`. Add the *"LG-2 force-limiter/soft-stop DONE before anything is
   powered near David"* pre-condition as a hard gate. Close `OQ-1.8.1` (single switch, ruled).
5. **Amend Vol XXVI**: promote §3.4's "stated outranks learned" and §2.5's music-dormant from *proposed
   default* to **RATIFIED**; close `D-XXVI-A` and `D-XXVI-D`; un-gate `WO-CANON-XXVI`.
6. **Amend Vol XXV**: add an explicit *stated-outranks-learned* precedence rule; add a David-stated
   quiet-hours/rhythm input to §1.7; strip the "daily user vs monthly user" framing.
7. **Rewrite Vol XXVII Ch.1 §1.5/§1.7 and Ch.3 §3.1/§3.3** to a one-person governance model; withdraw
   §3.8 Q1's recommendation to name CA first-pass as Gate 1a; introduce `LG-2` vocabulary so the volume can
   express the split at all.
8. **Vol XXIV**: close the three stale "blocking ruling A" statements; drop the retired anchor from
   metadata line 25; relay the actual file deletion to the Builder.

**P1 — the real holes**
9. **Author Volume IV.** `16_spine_runtime.md` is a stub marked complete. Code is not canon.
10. **Extend the Vol XXIV ontology** with `person`, `place`, `event` — eLo cannot currently know David's
    life. Then re-scope the product entities.
11. **Rule the Vol XXIV promotion threshold + demotion path** before `WO-CANON-XXIV` builds. Shipping
    "what eLo learns forever" with an undefined knob and no unlearn is the highest-risk item in the group.
12. **Re-scope `WO-CANON-XXV`** to include the envelope, lifecycle, `Anticipation`, and **wiring**; pull the
    board row back from DONE. A faculty nothing calls is not done.
13. **Resolve XIV** — either write it (and bring `plugins/` into the T-1…T-11 threat model, which currently
    ignores it entirely) or formally fold it into XXIII with an ADR.
14. **Answer Vol XXV OQ-1 (proactive reminders).** Software, David alone, no second reviewer. It is the
    single most useful temporal behaviour and it is blocked on a procedure that no longer exists.
15. **Product-era sweep** across items 1–12 in §4; mark **RD-5** PARKED in `_intake/`.

**P2**
16. Reconcile **FC-2** (open drift since 2026-07-27, 29 citations).
17. Ratify a single ID scheme (Vol XXVII §1.9 Q2) and fix the `ADR-Exec-` / `ADR-Executive-` dual spelling.
18. Locate or retire `CA-001/002/006/010/011/012`, `EA-0`, `EA-2`, and `ADR-Corp-001`; move `EA-3` into the
    repo or stop citing it as canon (24 citations of a file in an off-limits tree).
19. Fix the duplicate document numbers (`16_*` ×2, `17_*` ×2) and `00_philosophy.md`'s stale index.

---

```
AUDIT — Support & Governance spine (I–IV · XIV · XX · XXIII–XXVII)
Status: COMPLETE — Architect audit, Markdown only, no code or volume edits made
Volumes audited: 11 · WOs audited: 6 · ADR sweep: 40+ IDs across docs/ + engineering/
Cited-but-never-written: LAW-017 (20 cites) · ADR-Corp-001 · CA-001/002/006/010/011/012 · EA-0/EA-2
Row-only (no ADR document): ADR-Exec-003/004/005/006 (231 combined cites)
Weakest volume: XXIV (1 of 12 required blocks) · Worst-landed: XXV (DONE over dead code)
Most misaligned with the 08-10 rulings: XXVII (zero occurrences of "LG-2")
```

*Written 2026-08-10 by the Lead Architect. Companion to `AUDIT_INTENT_core_brain_*`,
`AUDIT_INTENT_learning_growth_*`, `AUDIT_INTENT_self_embodiment_*`.*
