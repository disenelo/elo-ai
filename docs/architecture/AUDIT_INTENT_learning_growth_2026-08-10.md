# AUDIT — INTENT vs CANON: "getting the brain to think more, learn etc"
### Group: IX Dream · XVII Reflection · XVIII Self-Evolution · XIX Consciousness Research · XXII Faculty Genome · XXVIII Adaptive Learning
**Auditing against:** David 2026-08-10 — *"we are getting the brain to think more, learn etc."*
**Governing law:** ADR-Exec-005 (Learning Through Verified Consequences) · ADR-Exec-003 (Embodied Truth) · Vision Spine *Continuous Becoming* + *Emergence over scripting*.
**Method:** read the intent sources, read the volumes and WOs, and **read the live runtime + the actual journal files**. Everything below marked ✅VERIFIED was confirmed by reading the artefact, not inferred.
**Lane:** Architect — this is a Markdown audit. No code, no volume edits. Everything actionable is a relay to the owning seat.

---

## VERDICT TABLE

| Vol | Spec'd? | Delivers "thinks more / learns"? | Real near-term loop? | ADR-Exec-005 risk | WO delivers? |
|---|---|---|---|---|---|
| **IX — Dream** | ✅ Strong. 4 real chapters, contracts, tests, firewall. | ⚠️ Partly. Dreaming IS specced as learning (reinforce verified memory), but the two edges that make it learning are **PENDING** (reinforce + creative_spark not wired). | ⚠️ Yes-ish — the reinforce edge is a small, buildable job today. | 🟡 One route: `personality_proposal` emitted **direct to Ch.7 from an imagined insight**, contradicting Ch.7's "Ch.6 only" rule. | ❌ **No WO-CANON-IX exists.** Excluded from the build program as "engine live." |
| **XVII — Reflection** | 🔴 **No volume. No directory.** Lives only in `Volume_V/06_*`. | 🔴 Spec is good; the build is **write-only**. It writes lessons nothing reads. | 🔴 The loop exists on disk and is dead. | 🟢 Low (it can't reach anything). | ❌ **No WO at all.** Vol V is marked "ratified — verify only." |
| **XVIII — Self-Evolution** | 🔴 **No volume. No directory.** Claimed by `Volume_V/06_*` + `07_*`. | 🔴 GrowthMetrics + Improvement Cycle (§6.7/§6.8) are **entirely unimplemented**. | 🔴 None. | 🟢 Low. | ❌ **No WO at all.** |
| **XIX — Consciousness Research** | ✅ Honest and complete for what it is (4 chapters, falsifiable questions, ADR-only policy). | ❌ By design it delivers **nothing** to runtime. Correctly scoped as research. | n/a | 🟢 None — it is explicitly forbidden from touching runtime. | ✅ WO-CANON-XIX matches the volume exactly. Correctly P4. |
| **XXII — Faculty Genome** | ✅ **Strongest in the group.** 4 chapters, schema, six laws, governance, ceiling stated in genome terms (§3.5), tests. | 🟡 Indirect — it governs *how* learning is allowed to change a faculty; it doesn't make eLo learn. | n/a (governance) | 🟢 **This is the enforcement mechanism.** `[C]` gate auto-rejects a boundary-crossing update. | ✅ WO-CANON-XXII is thorough and buildable. |
| **XXVIII — Adaptive Learning** | 🔴 **Scaffold only — ONE 92-line file, zero numbered chapters, zero acceptance tests.** Its own WO admits "acceptance tests must be authored when the volume is built." | 🔴 Everything real is deferred to a post-Presentable RL build. | 🔴 The one thing it says is "NOW" (three-layer strategy) is a **language**-learning pipeline, not a verified-consequence one. | 🔴 **Worst in the group — the volume contradicts its own constitutional boundary.** See §4. | ⚠️ WO-CANON-XXVIII faithfully transcribes a scaffold. A faithful transcription of a scaffold is still a scaffold. |

**Headline verdict: there IS a near-term learning loop, but it is written, not connected — and it is not where the canon says the learning is.**
The buildable-today loop is **WO-094 §D** (route memory / favourites accrue / confidence from verified ACKs) and the **already-built-but-dead** Reflection loop in `runtime/reflection_faculty.py`. Everything the canon calls "learning" (Vol XXVIII) is deferred to a future RL phase. That is the opposite of what David asked for on 2026-08-10.

---

## 1. THE FINDING THAT MATTERS — eLo has been "learning" into a bin ✅VERIFIED

I ran the numbers on the live files rather than trusting the canon.

```
self/lessons_ledger.jsonl        375 lessons
  → statuses:                    {"candidate": 375}      ← ZERO confirmed. Ever.
  → distinct statements:         3
       373 × "Completed a capability milestone — reinforce this pattern."
         1 × "Partial progress on build — check dependencies before next attempt."
         1 × "When build meets an obstacle here, adapt the approach rather than retrying identically."
self/journals/growth_journal.jsonl   814 entries
self/failure_log.jsonl                 2 entries
```

Four independently verified facts:

1. **Nothing reads the ledger.** `grep -rn "lessons_ledger\|growth_journal"` across all non-test `.py` returns **only the writer** (`runtime/reflection_faculty.py`). There is no recall path. Channel 1 of Vol V Ch.6 §6.5 ("Lesson → Memory → surfaces in future CognitiveState") **does not exist in code**.
2. **Nothing promotes candidate → confirmed.** There is no reinforcement code anywhere. Vol V Ch.6 §6.4 requires lessons to strengthen with confirming evidence; `_form_lesson()` hardcodes `"strength": 0.3, "status": "candidate"` and no other code path ever touches that record again.
3. **Therefore channel 2 is structurally dead.** `faculties/personality/personality_evolution_faculty.py:222` rejects any delta whose `strength != "confirmed"`. Since nothing ever confirms a lesson, **no lesson can ever move a trait — by construction**. And separately: `grep` shows `personality_evolution_faculty` / `PersonalityDelta` is imported by **nothing outside its own file and its own test**. The validator eLo's whole growth path is supposed to route through is dead code.
4. **The "lessons" are three `if` branches.** `_derive_statement()` (`runtime/reflection_faculty.py:105`) is a three-branch template on the action string. The same lesson, with the same truncated evidence string, is re-written verbatim at `2026-08-11T00:39:48` and again at `03:40:55` — no dedupe, no strengthening, no episode ref (Ch.6 §6.3 requires `episode_ref`; the implementation stores `session_summary[:120]` as "evidence").

**Blunt statement of it:** eLo's growth journal is 814 entries deep and his lessons ledger is 375 deep, and 373 of those lessons are the same sentence, and nothing has ever read one of them. Against *"we are getting the brain to think more, learn"* — the capture half of the loop shipped and the **recall half was never built**, so there is no measurable sense in which eLo is better today than in July. This is the gap. It is also the cheapest thing on this whole list to fix.

**And the governance is wrong about it.** `CANON_BUILD_PROGRAM.md:44` lists Volume V as *"Already live/ratified (no build WO — verify-only at Audit)"* and `:4` calls it *"the reference bar."* Its own DoD rule at `:4` says a volume is DONE only when *"implemented, wired into the turn loop, tested WITHOUT David."* Ch.6's growth metrics, improvement cycle, lesson reinforcement, and recall path meet none of that. **XVII and XVIII are marked "covered" by a volume that is falsely closed.** That is the single worst piece of canon drift in the group.

---

## 2. XVII AND XVIII HAVE NO HOME — say it plainly

There is **no `Volume_XVII/` and no `Volume_XVIII/`**. `00_CANON_INDEX.md:86–87` maps them into `Volume_V/06_*` and `07_*`, and `:129` claims *"✅ covered."*

That mapping is defensible on paper — the Reflection & Growth Engine genuinely does specify journals, lessons ledger, failure log, growth metrics and the improvement cycle, and it explicitly says it closes "Audit gap XVII / XVIII." But:

- **XVII's substance is half-built** (§1 above): journals ✅ written, lessons ✅ written, ledger ✅ written, failure log ✅ written — **strengthening ❌, promotion ❌, recall ❌**.
- **XVIII's substance is 0% built.** `grep` for `growth_metrics`, `intention_realisation`, `repeat_failure_rate`, `identity_stability`, `reinforcement_ratio` across the entire repo returns **nothing**. §6.7 (Growth Metrics) and §6.8 (Improvement Cycle) — the actual "eLo gets measurably better" machinery — exist only as prose.
- Neither has a WO. Neither is on the board. Neither is in `CANON_BUILD_PROGRAM.md`.

**Verdict: XVII is a half-built lodger inside Vol V; XVIII is a title with no implementation anywhere.** They do not need their own volumes (Check-Before-Build) — they need a **build WO against Vol V Ch.6/§6.7/§6.8** and Vol V's "ratified" status revoked until it holds.

---

## 3. WHERE IS THE CONCRETE LOOP? (captured / recalled / improved / rewarded)

David's test is whether eLo gets better. Here is every candidate loop in the group, scored on the four questions.

| Loop | Captured | Recalled | What improves | Reward | Status |
|---|---|---|---|---|---|
| **Vol V Ch.6 Reflection** | ✅ lessons + journals + failure log | ❌ **nothing reads them** | ❌ nothing | Significance (Ch.5) | 🔴 write-only |
| **WO-055 Capability Learning** (`runtime/capability_learning.py`) | ✅ failure streaks → rule candidates | ⚠️ only → a WO proposal for a human | ❌ eLo's behaviour doesn't change; a *human* gets a ticket | none | 🟡 a bug-report generator, not learning |
| **WO-070 Shadow capture** (DONE) | ✅ `understudy_shadow.jsonl` (52 rows) | ✅ by WO-071 | eLo's phrasing | none | 🟡 language, not consequences |
| **WO-071 ICL correction frame** (DONE) | ✅ scrub deltas + L3 overrides | ✅ injected into the prompt | eLo's **speech** | none | 🔴 improves the exact thing ADR-Exec-005 forbids learning (see §4) |
| **WO-082 Decision journal** (DONE) | ✅ causal chain | ✅ `explain_last()` | nothing — it explains, it doesn't adapt | none | 🟢 correct as specced; not a learning loop |
| **Vol IX Dream reinforce** | ✅ `memory_refs` produced | ❌ **`reinforce()` edge not wired** | would strengthen verified memories | Significance | 🟡 one missing call away from real |
| **WO-094 §D route memory** | spec'd | spec'd | **route confidence + favourites through verified ACKs** | Vol V Ch.5 Significance | ⭐ **the only genuinely near-term, ADR-clean loop in the whole group** |
| **Vol XXVIII RL** | — | — | movement/curiosity/presence/robot policies | Significance vector | 🔴 entirely deferred |

**So: is there a real, buildable, near-term learning loop, or is it all deferred to a future RL phase?**
There are **three** near-term loops and each is one small, in-lane job from being real:
- **(a) Close the Reflection recall path** — promote candidate→confirmed on repeat evidence, and surface confirmed lessons into `CognitiveState`. This is Vol V Ch.6 §6.4/§6.5 as already written. No new canon needed.
- **(b) Wire the Vol IX `reinforce()` edge** — Vol IX §4.3 names the exact missing call; it's flagged PENDING in the volume's own metadata.
- **(c) Build WO-094 §D** — capture route outcomes, recall routes before re-planning, accrue favourites, grow confidence from ACKs.

**(c) is the one David will actually SEE.** It is the only loop where "he got better" is visible on the desktop rather than in a JSONL. It is also the only one already framed against verified body ACKs (ADR-Exec-003), so it is constitutionally clean by construction.

**The rest is deferred**, and Vol XXVIII's own sequencing says so explicitly: *"Full authoring + build sit behind Presentable v1"* and *"Not started."* Against David's 2026-08-10 line, that sequencing is now **wrong** and should be revisited: the volume named "Adaptive Learning" is the one part of this group with nothing buildable in it.

---

## 4. CONTRADICTIONS — including three that break ADR-Exec-005

### 🔴 C-1 — THE REWARD FUNCTION DOES NOT EXIST, AND THE ONE IT POINTS AT LEARNS FROM LANGUAGE ✅VERIFIED
This is the worst finding in the group.

Vol XXVIII says: *"Reuse `memory/significance_engine.py` + Vol V Ch.5 Significance — do NOT invent a reward scalar… the learning signal is a vector: **Meaning · Novelty · Relationship · Embodiment · Curiosity · Efficiency · Safety**."* WO-CANON-XXVIII and WO-094 §D both repeat this instruction. **It cannot be followed.** There are three mutually incompatible "Significance vectors" in canon and code:

| Source | Dimensions |
|---|---|
| ADR-Exec-005 + Vol XXVIII + WO-CANON-XXVIII | 7: Meaning · Novelty · Relationship · **Embodiment** · Curiosity · **Efficiency** · **Safety** |
| Vol V Ch.5 §5 (the doc they point at) | 5: Emotion Weight · Novelty · Learning Value · Relationship Value · Future Relevance |
| **The live code** `memory/significance_engine.py` | 9: presence · learning · logic · humour · relationship · creation · system_change · novelty · continuity |

**Not one dimension of Embodiment, Efficiency, or Safety exists in the code.** Those are precisely the three that make a movement/robot reward meaningful. `DECISION_LOG.md` line 231 already logs this as `FC-2 | significance formula (9 dims) | DRIFT → reconcile` — **it was never reconciled**, and two live WOs now depend on it.

Worse — I read the implementation. `evaluate(raw, response, action, plan, state)` takes **only the user's text and eLo's reply text**. Every dimension is scored by keyword tables against strings (`_LOGIC_SIGNALS`, `_CREATION_SIGNALS`, `_HUMOUR_SIGNALS`…). There is **no outcome input, no ACK input, no verified-consequence input at all**.

> **Therefore: "reward = the Significance Engine" means "reward = keyword-matching on conversation text." That is learning from language — the exact thing ADR-Exec-005 exists to forbid** (*"Language alone is never evidence; only executed actions with verified consequences influence future policy"*). If a seat builds WO-CANON-XXVIII or WO-094 §D literally as written, it ships an ADR-Exec-005 violation on day one while believing it is obeying canon.

**This blocks WO-094 §D and WO-CANON-XXVIII.** Needs a ruling: either extend the Significance Engine with verified-outcome inputs and the missing Embodiment/Efficiency/Safety dimensions, or define a separate outcome-scored vector for the learning path and stop calling it "the Significance Engine." It cannot stay ambiguous — two WOs cite it as their reward.

### 🔴 C-2 — VOL XXVIII'S "THREE-LAYER STRATEGY" VIOLATES VOL XXVIII'S OWN CONSTITUTIONAL BOUNDARY
Vol XXVIII opens with: *"RL is **not** allowed to learn: personality · values · ethics · memory truth · identity · Executive Authority · **speech correctness** · architectural principles."*

Vol XXVIII then specifies, in the same document:
- WO-070 shadow-log capturing `raw_input · elo_raw_gen · elo_final` (conversation turns, not verified outcomes);
- WO-071 injecting past corrections into the prompt so eLo's phrasing improves — **learning speech correctness from language**;
- a LoRA fine-tune whose training pair is explicitly *"learn to PRODUCE `elo_final` given (`context` + `raw_input`), using `elo_raw_gen`→`elo_final` as the delta signal"* — i.e. **train the model on the speech-correction delta**.

The volume argues the understudy "sharpens skill/style ONLY" and "still passes the Executive verification guards." That mitigation is real but it is asserted, not derived — and it does not resolve the plain contradiction that a document forbidding learning speech correctness from language then specifies a three-stage pipeline for learning speech correctness from language. **WO-071 is already DONE and shipped.** Either the ADR needs a written carve-out distinguishing *style sharpening under Executive verification* (permitted) from *learning what is true or correct to say* (forbidden), or the pipeline is out of bounds. Right now canon says both.

### 🟡 C-3 — VOL IX EMITS A PERSONALITY DELTA FROM AN IMAGINED INSIGHT, DIRECT TO CH.7
Vol IX §4.5 / its Faculty Contract routes `personality_proposal → PersonalityEvolution (Vol V Ch.7)`, derived by `_extract_personality_proposal()` scanning **dream insight text** for trait keywords.

Vol V Ch.7 §7.3 rule 1: *"**Single source.** The engine accepts trait deltas from **Chapter 6 only**. No other faculty… can move a trait."* Rule 2: a delta *"must carry ≥1 evidence lesson at `confirmed` strength."*

Two problems: (a) Vol IX names a route Vol V Ch.7 forbids; (b) the payload's provenance is an **imagined** insight with no confirmed lesson behind it. Vol IX §4.2 defends this as "proposal only, validated downstream" — and Ch.7 would in fact reject it, so the live risk is low. But **the volumes disagree about the wiring**, and a seat reading Vol IX will build an edge Vol V says must not exist. Fix is one line: route the dream proposal **through Ch.6** as candidate evidence, never direct to Ch.7.

### 🟡 C-4 — HABITS / PREFERENCES / INTERESTS HAVE THREE OWNERS (Memory-vs-Personality-vs-Learning duplication)
"Habit formation" is claimed by **Vol XXVIII** (scope-locked list), **WO-081 §3 + §9** (habits + interest formation), **Vol X** (trait model, and Ruling D just made Vol V Ch.7's model the single winner), and **SS-11** in the tracker names all three at once (*"WO-081 · Vol X · Vol XXVIII"*). Interest values like `parkour 0.84 · exploration 0.89` are functionally trait-adjacent. Under Ruling D (drift is a proposal, one trait model wins) and ADR-Exec-005 (learning may move preferences but not personality), **the line between "a learned preference" and "a personality trait" is not drawn anywhere**. This is the most likely route by which learning quietly reaches identity — not through a dramatic violation, but through an "interest" that is really a trait, written by a faculty that isn't Ch.7.
**Needs a ruling before WO-081 or WO-CANON-XXVIII is built.**

### 🟡 C-5 — STALE `autobiography.jsonl` OWNERSHIP (the substrate for self-observation)
`Volume_XXI/00_Metadata.md`, `01_*`, `02_*`, `03_*` and `Volume_XXV/03_*` all name **"WO-078"** as the owner of `self/journals/autobiography.jsonl`. In the live stream **WO-078 is Exit Run Vocabulary & Randomness**. The CA's numbering world and ours collided; `SELFHOOD_ROADMAP_TRACKER.md` correctly re-homes it (SS-5 → WO-081 §4), but **two ratified-track volumes still point at the wrong WO**, and Vol XXV ships a `PENDING` fallback against it. Self-observation ("I've noticed I wave a lot", "what have you been doing?") — a headline Capability-Horizon item — is blocked behind a file whose owner is mislabelled in canon.

### 🟢 C-6 — no other identity/values/truth breach found
XXII holds the line properly (§3.5 ceiling in genome terms; `[C]` gate auto-rejects; ST-7 / FT-3 / FT-4 test it). XIX is fenced off from runtime by four explicit prohibitions. IX's imagined-speech firewall (§4.1–§4.6) is genuinely well built — dreams reinforce only already-verified records, never write episodic memory, never assert content as fact. **Vol IX and Vol XXII are the two volumes in this group that actually do their job.**

---

## 5. DO THE WO-CANON ORDERS DELIVER IT?

- **WO-CANON-XXII — YES.** The most complete order in the group. Genome type, registry, total validation gate, the six laws, `[C]`/`[R]` gates, genome backfill for the live faculties, named tests. If built as written, it is the mechanism that makes ADR-Exec-005 *enforceable* rather than *aspirational*. Its priority (P3) may be too low given that everything else in this group depends on it to be safe.
- **WO-CANON-XIX — YES, and correctly so.** It matches the volume, delivers documents not code, and is honest that it never builds anything. No complaint. It also does not advance David's 2026-08-10 ask at all, which is fine — nobody claimed it would.
- **WO-CANON-XXVIII — NO. It under-scopes the one thing named "learning."** It is a faithful transcription of a 92-line scaffold, and it says so: *"Acceptance tests must be authored when the volume is built (the scaffold has none yet — flag)."* An order whose DoD includes "author the DoD later" is not a buildable order. It also inherits C-1 (a reward function that doesn't exist) and C-2 (a pipeline that contradicts its own boundary). **It is RELEASED on the board (`DISPATCH_BOARD.md:1460` — "▶ RELEASED 2026-08-10 — buildable now"). It is not buildable now.** That row is wrong and will burn a seat.
- **WO-081 — spec'd well, but it is a bundle of eleven sub-parts with a four-line DoD**, gated behind WO-079 + WO-073, and it carries the unresolved habits/interests ownership question (C-4).
- **WO-094 — the best learning spec in the repo, and its learning section is not in its DoD.** §D is excellent: it correctly distinguishes *capture + recall + preference (buildable today)* from *full RL policy training (Vol XXVIII, later)*, correctly binds learning to verified ACKs (ADR-Exec-003), and correctly confines it to the Movement faculty. Then the **"Test (without David)" section contains no learning test** and the **"Done when" contains no learning clause** — it is satisfied entirely by notice-and-route. As written, a seat can close WO-094 with zero learning built and be correct to do so. **This is the WO that under-scopes.** §D also inherits C-1 (it names the Significance Engine as its reward).
- **No WO-CANON-V, no WO-CANON-IX, no WO for XVII, no WO for XVIII.** The four volumes that hold the *actual, already-designed, already-half-built* learning loop have **zero build orders between them**, while the volume with nothing in it (XXVIII) is released.

---

## 6. WHAT I RECOMMEND (Architect relay — decisions are David's / the CA's)

**Rulings needed before any of this is built:**
1. **R-1 (blocks two WOs): fix the reward vector.** Decide: extend `significance_engine.py` with verified-outcome inputs + Embodiment/Efficiency/Safety dimensions, or define a separate outcome-scored learning vector. Close `FC-2` while you're in there. Until this lands, WO-094 §D and WO-CANON-XXVIII cannot be built without violating ADR-Exec-005.
2. **R-2: write the ADR-Exec-005 speech carve-out** — is style-sharpening under Executive verification (WO-070/071/LoRA) permitted or not? WO-071 is already shipped under the ambiguity.
3. **R-3: draw the preference-vs-trait line** (C-4) before WO-081 or XXVIII. This is the realistic route by which learning reaches identity.

**Board corrections I can make now (Markdown, my lane):**
4. Correct `DISPATCH_BOARD.md:1460` — WO-CANON-XXVIII is **NOT** "buildable now" (no chapters, no tests, no usable reward).
5. Revoke Vol V's "ratified / verify-only" status in `CANON_BUILD_PROGRAM.md:44` — Ch.6/Ch.7 do not meet the program's own DoD.
6. Fix the stale `WO-078` autobiography references in Vol XXI and Vol XXV (C-5).

**Relays to seats — the three jobs that make David's sentence true in days, not quarters:**
7. **Builder — close the Reflection recall path** (Vol V Ch.6 §6.4/§6.5, already specced): dedupe + strengthen repeat lessons, promote candidate→confirmed, surface confirmed lessons into `CognitiveState`. Right now 375 lessons are being written into a file nothing opens. **Highest value-per-hour item in this audit.**
8. **Builder — add §D to WO-094's DoD and test list**, or it will ship without learning.
9. **Builder — wire the Vol IX `reinforce()` edge** (Vol IX §4.3 names the exact missing call).

**Author-side, mine:** XVII and XVIII need a real build WO against Vol V Ch.6 §6.7/§6.8 (Growth Metrics + Improvement Cycle) — 0% implemented, no owner, no ticket. Without measurement there is no way to answer "is he actually getting better," which is the whole of David's ask.

---

*Audit run 2026-08-10/11 by the Lead Architect against `00_DAVIDS_VISION_SPINE.md`, `ARCHITECTURAL_PRINCIPLES.md`, `ELO_CAPABILITY_HORIZON.md`, `ELO_SELFHOOD_MASTER_ROADMAP.md`, `DECISION_LOG.md` (ADR-Exec-003/005/006), `CANON_RULINGS_2026-08-10.md`, `_intake/SOURCE_2026-08-08_self_model_becoming.md`. Runtime facts independently verified against `runtime/reflection_faculty.py`, `runtime/capability_learning.py`, `memory/significance_engine.py`, `faculties/personality/personality_evolution_faculty.py`, `self/lessons_ledger.jsonl`, `self/journals/growth_journal.jsonl`, `self/failure_log.jsonl` (Rule #2 — Independent Runtime Verification).*
