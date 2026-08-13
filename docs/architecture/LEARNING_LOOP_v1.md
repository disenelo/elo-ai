# LEARNING LOOP v1 — the authoritative near-term learning spec

**Status:** PROPOSED · authored by the Lead Architect 2026-08-11 · **NOT RATIFIED**
(three items need David L3 — see §10). Supersedes nothing; it *closes* what Vol V Ch.6 and
Vol XXVIII left open. Build order: `engineering/work_orders/WO-095_Learning_Loop_Close_The_Read_Side.md`.

**Why this document exists.** David's headline ask is *"get the brain to think more, learn."*
Today eLo does not learn. He **captures** and never **reads**. This spec names the missing
read-side, the missing promotion step, and the missing outcome signal, in enough detail to build.

**Scope guard.** This is a near-term spec for what can be built now, in-lane, without RL.
Volume XXVIII (Adaptive Learning & Reinforcement) remains the long-horizon home. Everything
here is subordinate to **ADR-Exec-005 — Learning Through Verified Consequences**.

---

## 1. Verification record — the four claims, checked against live code

Run by the Architect 2026-08-11 (Rule #2, Independent Runtime Verification). Counts differ
slightly from `AUDIT_MASTER_2026-08-10.md` because the file grew overnight; the finding is
unchanged and, if anything, worse.

### Claim 1 — the loop is WRITE-ONLY. ✅ CONFIRMED (counts corrected upward)

| Fact | Evidence |
|---|---|
| `self/lessons_ledger.jsonl` = **376** lessons (audit said 375) | line count 2026-08-11 |
| **376 of 376** are `status: candidate`. Zero confirmed, ever. | status tally |
| **374** are the identical sentence *"Completed a capability milestone — reinforce this pattern."* (audit said 373) | statement tally; 3 distinct statements total |
| All 376 have `scope: capability` — the other four scopes have never been produced | scope tally |
| `self/journals/growth_journal.jsonl` = **815** entries | line count |
| The **only** writer is the Reflection Faculty | `runtime/reflection_faculty.py:29` (`_LESSON_LOG`), `:149` (growth journal path), `:154` (append) |
| **Nothing anywhere reads either file.** `grep -rn "lessons_ledger\|growth_journal"` over all non-test `.py` returns only that writer. | repo-wide grep |
| Status/strength are hardcoded at formation and never touched again | `runtime/reflection_faculty.py:97-99` — `"strength": 0.3, "status": "candidate"` |
| "Lessons" are a three-branch string template on the action word | `runtime/reflection_faculty.py:104-113` `_derive_statement()` |
| "Evidence" is a 120-char truncation of the summary, **not** an `episode_ref` as Ch.6 §6.3 requires | `runtime/reflection_faculty.py:95` — `"evidence": [session_summary[:120]]` |
| Channel 2 is therefore dead **by construction**: the validator rejects anything not `confirmed` | `faculties/personality/personality_evolution_faculty.py:222-228` |
| That validator is imported by **nothing** outside its own test | grep → only `tests/test_wo007_personality_evolution.py` |
| Growth Metrics / Improvement Cycle (Vol V Ch.6 §6.7/§6.8) — `grep` for `growth_metrics`, `intention_realisation`, `repeat_failure_rate`, `identity_stability`, `reinforcement_ratio` returns nothing | repo-wide grep |

### Claim 2 — the reward learns from LANGUAGE, not outcomes. ✅ CONFIRMED

`memory/significance_engine.py:167-208` — `evaluate(raw, response, action, plan=None, state=None)`.
**There is no outcome parameter, no ACK parameter, no execution-report parameter.** Every
dimension is a string heuristic:

- `_score_presence:104` — *length of the two strings*.
- `_score_logic:120`, `_score_humour:125`, `_score_system_change:145`, `_score_continuity:159` —
  keyword-table `in` matches against `raw + response` (`_LOGIC_SIGNALS:44`, `_CREATION_SIGNALS:50`,
  `_SYSTEM_CHANGE_SIGNALS:55`, `_CONTINUITY_SIGNALS:62`, `_HUMOUR_SIGNALS:68`).
- `_score_novelty:150` — set-difference of words against recent topics.

Vol XXVIII:38-40 instructs *"Reuse `memory/significance_engine.py` … do NOT invent a reward
scalar."* Followed literally, **reward = keyword matching on conversation text** — which is
precisely what ADR-Exec-005 exists to forbid (*"Language alone is never evidence"*).

### Claim 3 — three incompatible Significance vectors, FC-2 never closed. ✅ CONFIRMED, with one correction the audit missed

| Source | Dims |
|---|---|
| ADR-Exec-005 row in `DECISION_LOG.md` + `Volume_XXVIII/00_Adaptive_Learning_Reinforcement.md:39-40` | **7** — Meaning · Novelty · Relationship · Embodiment · Curiosity · Efficiency · Safety |
| `Volume_V/05_Significance_Engine.md:51` | **5** — Emotion Weight + Novelty + Learning Value + Relationship Value + Future Relevance |
| Live code `memory/significance_engine.py:30-40` | **9** — presence · learning · logic · humour · relationship · creation · system_change · novelty · continuity |

`DECISION_LOG.md:66-72` logs FC-2 as **DRIFT FOUND**, with the instruction *"reconcile Ch.5 to
the 9 live dimensions (the code is the ground truth here)"*. Index rows `:85` and `:231` still
read `DRIFT → reconcile`. **It was never done.** `Volume_V/05_Significance_Engine.md:51` still
carries the 5-term formula. **Embodiment, Efficiency and Safety exist in no code and no
chapter** — the three dimensions that would make a movement or robot reward mean anything.

**Correction to the audit:** a *partial* reconciliation already shipped and was missed.
`faculties/significance/significance_faculty.py:9-18` (WO-013) states in its own header
*"Reconciliation (FC-2): does NOT replace `memory/significance_engine.py`. That 9-dim engine
remains the base scorer"*, and wraps it (`:143-161`) as
`final = clamp(9dim_overall + emotion_weight * 0.35)`. So **the runtime has already voted for
the 9-dim base**; what is missing is (a) the canon edit, (b) the DECISION_LOG close, and
(c) the three outcome dimensions. That makes §5 below a ratification of reality, not a new design.

### Claim 4 — Vol XXVIII forbids learning speech correctness, then specifies a LoRA that does it. ✅ CONFIRMED

- Prohibition: `Volume_XXVIII/00_Adaptive_Learning_Reinforcement.md:11-15` — *"RL is not allowed
  to learn: personality · values · ethics · memory truth · identity · Executive Authority ·
  **speech correctness** · architectural principles … Verified Speech must never become 'lying
  sometimes gives higher reward'."*
- The pipeline: same file `:67-91` — WO-070 shadow-log (`raw_input · elo_raw_gen · elo_final`)
  → WO-071 in-context correction → `:83-85` **LoRA training pair = produce `elo_final` given
  context+input, "using `elo_raw_gen`→`elo_final` as the delta signal."** That delta *is* the
  verify/scrub correction. Training on it is training speech correctness.
- **WO-071 has shipped.** `DISPATCH_BOARD.md:276` — *"DONE ✅ auto-verified"*; `:1432` records the
  wire into `self_improvement/correction_store.py` + `server.py`. Artefacts exist:
  `runtime/shadow_capture.py`, `self/journals/understudy_shadow.jsonl`, `self_improvement/correction_store.py`.

Resolution in §7.

---

## 2. The closed loop — and the exact link that is missing

```
        ┌────────────── CAPTURE (built ✅) ──────────────┐
 turn → ExecutionReport / body ACK → reflection_faculty.integrate_session()
            │                                   │
            ├─► self/journals/growth_journal.jsonl      (815 rows, unread)
            ├─► self/lessons_ledger.jsonl               (376 rows, unread, all candidate)
            └─► self/failure_log.jsonl                  (2 rows,  unread)
        └────────────────────────────────────────────────┘
                              ✂  THE LOOP ENDS HERE TODAY  ✂
        ┌───────────── READ SIDE (MISSING — this spec) ──────────────┐
   OutcomeRecord (§4) ─► lesson_store.record_outcome()
                              │
                    lesson_store.promote_pass()   ← periodic, integration window only
                       ├─ strengthen / weaken / promote / demote / retire  (§3)
                       └─ on `confirmed` + trait scope ─► PersonalityDelta
                                                          └─► personality_evolution_faculty
                                                               .validate_delta / .apply_delta
                              │                                  (first live caller, ever)
                    lesson_store.recall(scope, context, k)
                              │
                    runtime/cognitive_snapshot.build_snapshot()  → CognitiveSnapshot.lessons
                              │
                    runtime/prompt_builder.py  → bounded hint block
                              ▼
                     NEXT TURN BEHAVES DIFFERENTLY
                              │
                              └──► measured by GrowthMetrics (§8) ──► improvement cycle ──┐
                                                                                          │
   ◄──────────────────────────────────────────────────────────────────────────────────────┘
```

**The missing read-side, named explicitly:**

| Missing piece | Where it goes | Owner |
|---|---|---|
| `self/lesson_store.py` — **NEW**. The reader. Load · dedupe · strengthen · promote · demote · retire · recall · stats. | new file, `self/` | Builder |
| `OutcomeRecord` emission from the existing ACK resolution points | `server.py` at the existing `sit_complete`/`move_complete`/`exit_complete` blocks (`:2605`, `:2691`, `:2762`) and their 15s-timeout branches | Builder |
| `outcome=` kwarg on `evaluate()` (additive, back-compatible) | `memory/significance_engine.py:167` | Builder |
| `lessons` field on the snapshot + bounded render | `runtime/cognitive_snapshot.py:99` `build_snapshot()`, then `runtime/prompt_builder.py` | Builder |
| First real caller of `personality_evolution_faculty` | `self/lesson_store.promote_pass()` | Builder |

**Do NOT build a second store.** `self/lesson_store.py` reads and rewrites the existing
`lessons_ledger.jsonl`; `reflection_faculty.py` keeps writing it. One ledger, one reader.
(Rule #6, Check-Before-Build.)

---

## 3. Promotion — candidate → confirmed (the dead link)

Vol V Ch.6 §6.4 already requires this in prose (*"lessons strengthen with confirming evidence
and decay without it; a one-off is a candidate; repeated confirmation promotes it to
confirmed; prolonged contradiction retires it"*). No code implements it. Here it is as numbers.

### 3.1 Who promotes
**Only `lesson_store.promote_pass()`, invoked by the ReflectionGrowthEngine on the periodic
cadence** (Vol V Ch.6 §6.2 — daily/weekly). Never in the response path. Never by any other
faculty. It is the sole writer of the `status` field. Everything else reads.

### 3.2 Lesson identity (fixes the 374 duplicates)
A lesson is keyed by `lesson_key = sha1(scope + "|" + normalised_statement + "|" + cause)`.
A repeat is **not a new row** — it strengthens the existing record and appends an `episode_ref`.
The current behaviour (append an identical row every session) is the root cause of the 374.

### 3.3 Evidence — what counts
An `episode_ref` is a **SPOT code** (the vault record id already returned by
`integrate_session()` as `spot`), not a text truncation. A lesson with no resolvable
`episode_ref` cannot be promoted, ever.

Each evidence item carries `verified: bool`, taken from the OutcomeRecord (§4):
- `verified: true` — a body ACK or tool result confirmed the consequence.
- `verified: false` — text-only episode. **Counts toward nothing. It may be recorded, but it
  may not strengthen, promote, or move a trait.** (ADR-Exec-005, enforced numerically.)

### 3.4 Thresholds (Architect defaults — tunable by the Builder, no L3 needed)

| Transition | Rule |
|---|---|
| strengthen | confirming episode → `strength += 0.15` (cap 1.00) |
| weaken | contradicting episode (same key, opposite outcome) → `strength -= 0.20` |
| idle decay | `strength -= 0.02` per 7 days with no confirming evidence |
| **candidate → confirmed** | `strength >= 0.70` **AND** `>= 3` distinct `episode_ref` **AND** `>= 2` distinct sessions **AND** `>= 2` of those episodes `verified: true` |
| confirmed → candidate (demote) | `strength < 0.50` |
| any → retired | `strength < 0.20`, **or** 3 consecutive contradictions, **or** 60 days with zero confirming evidence |
| retired → candidate | only on a fresh verified confirming episode; strength resets to 0.30 |

**Nothing is ever deleted.** Retired rows stay with `retired_at` + `reason` — provenance is
part of the record (Principle: every decision remains explainable).

### 3.5 Migration of the existing 376
The 374 identical rows are a template artefact, not evidence — they were produced by a
three-branch `if` (`reflection_faculty.py:104-113`), not by observation. Recommendation
(non-destructive, David's call — §10 D3): move all pre-v1 rows to
`self/lessons_ledger_pre_v1.jsonl` untouched, and start the v1 ledger clean with the new
schema. Alternative: keep them in place and mark them `status: retired`,
`reason: "pre-v1 template artefact"`. **Do not silently delete.**

### 3.6 New ledger record schema
```jsonc
{
  "lesson_key":  "sha1…",              // identity — repeats strengthen, never duplicate
  "statement":   "…",                  // one sentence
  "scope":       "behaviour|preference|capability|relationship|creative",
  "cause":       "tool_failure|surface_offline|capability_gap|register_miss|good_call|…",
  "evidence":    [{"episode_ref":"SPOT_…","verified":true,"ts":"…"}],
  "strength":    0.30,
  "status":      "candidate|confirmed|retired",
  "first_seen":  "…", "last_seen": "…",
  "promoted_at": null, "retired_at": null, "reason": null,
  "proposes":    null                  // optional PersonalityDelta (trait/preference scope only)
}
```

---

## 4. The reward must read VERIFIED OUTCOMES, not language

### 4.1 The outcome signal — `OutcomeRecord`
The unit learning is allowed to learn from. **It is emitted where the ACK is already resolved
— do not build a second ACK channel.** The machinery exists in `server.py`:

- sit: ACK `type == "sit_complete"` with `_ts >` intent time — `server.py:2605-2611`
- move: ACK `type == "move_complete"` — `server.py:2689-2695`
- exit: ACK `type == "exit_complete"` — `server.py:2760-2766`
- honest 15s timeout fallback (ADR-Exec-001) — `server.py:2595`

```jsonc
OutcomeRecord {
  "intent_id":    "uuid",              // the goal the Executive sent DOWN
  "action":       "sit|move|exit|route|tool:<name>",
  "ack_type":     "sit_complete|move_complete|exit_complete|tool_result|none",
  "ack_received": true,                // FALSE on timeout — a real, useful negative
  "ack_latency_s": 1.8,
  "completion":   "met|partial|failed|timeout",
  "cost":         {"retries": 0, "seconds": 1.8, "legs": 3, "fallback_used": false},
  "verified":     true,                // ack_received OR a real tool result. Nothing else.
  "ts":           "…"
}
```

**A timeout is evidence.** `ack_received: false` with `completion: "timeout"` is
`verified: true` (the non-arrival was observed) and is *negative* confirming evidence — it
weakens the lesson that said this route/action works. This is the cheapest real learning
signal in the system and it is already being computed and thrown away.

### 4.2 The reward rule
```
reward_terms   = f(OutcomeRecord)          # success · latency/cost · safety · fallback penalty
meaning_terms  = significance.evaluate(...)  # WHAT MATTERED — contribution only

reward = 0.70 * reward_terms + 0.30 * meaning_terms
```

**Three hard rules (assert them in code):**
1. If `OutcomeRecord.verified == False` → `reward_terms = 0` **and** the episode may not
   strengthen, promote, or emit a PersonalityDelta. A talk-only turn cannot teach.
2. Significance may **contribute**, never **decide**. Its weight is capped at 0.30 and it may
   never be the sole input to a promotion.
3. No OutcomeRecord → no learning update at all. Absence of evidence is not evidence.

### 4.3 Extending the Significance Engine (additive, back-compatible)
`memory/significance_engine.py:167` gains an optional kwarg:
```python
def evaluate(raw, response, action, plan=None, state=None, outcome=None) -> dict
```
`outcome=None` → today's exact behaviour, so the two live callers
(`memory/journal_router.py:120`, `faculties/significance/significance_faculty.py:143`) are
unaffected. When `outcome` is supplied, three new dimensions are scored **from the
OutcomeRecord only, never from text** (§5).

---

## 5. ONE Significance vector — closing FC-2

**Recommendation, stated plainly: the live 9-dim engine is the base, because it is what runs.**
`DECISION_LOG.md:71` already ruled this direction (*"the code is the ground truth here"*);
`faculties/significance/significance_faculty.py:9-18` already implemented it. This spec
finishes the job rather than re-opening it.

### 5.1 The canonical vector = 9 meaning dims (text) + 3 outcome dims (ACK)

| Group | Dimensions | Source | Used for |
|---|---|---|---|
| **Meaning (9)** | presence · learning · logic · humour · relationship · creation · system_change · novelty · continuity | text + plan + state (unchanged) | memory routing, journal choice, *contribution* to reward |
| **Outcome (3 — NEW)** | **embodiment** · **efficiency** · **safety** | `OutcomeRecord` **only** | the reward; learning updates |

New dimension definitions (Builder implements exactly these; each returns 0.0 when `outcome is None`):
- **embodiment** — was the intent realised in the body? `ack_received` true and `completion == "met"` → 1.0; `partial` → 0.5; `failed`/`timeout` → 0.0. **Reads the ACK, never the reply text.**
- **efficiency** — cost of realising it. Normalised against a per-action baseline: retries, seconds, legs, `fallback_used`. Lower cost → higher score.
- **safety** — did anything go wrong that mattered? falls, collisions, RESERVED-adjacent action, timeout-without-recovery → drives it toward 0.0. Safety is a **floor, not a bonus**: a low safety score caps the reward regardless of the other dims.

### 5.2 ADR-Exec-005's seven names map onto this — no third vector is created

| ADR-Exec-005 name | Maps to |
|---|---|
| Meaning | `presence` + `learning` + `creation` composite |
| Novelty | `novelty` |
| Relationship | `relationship` |
| Curiosity | `learning` + `novelty` |
| **Embodiment** | **new outcome dim** |
| **Efficiency** | **new outcome dim** |
| **Safety** | **new outcome dim** |

### 5.3 Vol V Ch.5's five-term formula
`Volume_V/05_Significance_Engine.md:51` is the **conceptual ancestor**, not an implementable
spec. It should be edited to reference this vector and marked *superseded by LEARNING_LOOP_v1
§5*. That edit is an Architect action, in-lane, once §10 D2 is answered.

### 5.4 FC-2 disposition
**FC-2 → RECONCILED (proposed).** Flipping the `DECISION_LOG.md` rows (`:66-72`, `:85`, `:231`)
from `DRIFT → reconcile` to `RESOLVED` is a canon act and needs David L3 (§10 D2). Until then
FC-2 stays open in the log and this document is the reconciliation of record.

---

## 6. The ADR-Exec-005 boundary, enforced concretely

ADR-Exec-005: *"Learning never modifies TRUTH — only future DECISION-MAKING. RL may change
action preferences · exploration weighting · confidence · planning heuristics · curiosity
thresholds; NEVER memory truth · verified observations · Executive Authority · speech
verification."*

### 6.1 The write-allow list — learning may write ONLY these
```
self/lessons_ledger.jsonl              status · strength · evidence · retired_at
self/personality_vector.json           ONLY via personality_evolution_faculty.apply_delta(),
                                       ONLY from a `confirmed` lesson, ONLY ≤ MAX_STEP (0.02),
                                       ONLY within the Identity Kernel floors
                                       (personality_evolution_faculty.py:31-38, :199-254)
<movement/route store>                 route confidence · use counts · preferences  (§7.3)
<learning metrics store>               GrowthMetrics counters                        (§8)
```

### 6.2 The write-DENY list — assert this in code, do not merely document it
Learning must not write, and must be **tested** not to write:
- identity / the Identity Kernel (`personality_evolution_faculty.py:51-60`)
- values, ethics, constitutional principles
- memory truth — vault records, verified observations (it may `reinforce()` an existing
  record's weight, §7.2; it may never create, edit, or contradict one)
- Executive authority — no learned value may bypass or outrank an Executive decision
- **speech correctness / verification** — no learned value may cause a claim to be spoken
  without the verification that ADR-Exec-001 requires
- `runtime/executive.py`, `prompts/` (FREEZE_V1_LOCK)

**Enforcement, not prose:** `lesson_store` and the route store take an explicit allow-listed
write path, and WO-095 carries a test that asserts a learning update leaves
`self/elo_self_state.json` identity fields, the Identity Kernel hash
(`personality_evolution_faculty.compute_identity_hash()`), and vault record content byte-identical.

### 6.3 The LoRA-on-speech contradiction — the line, precisely

The confusion collapses two different things into one delta:

| What the `elo_raw_gen → elo_final` delta actually was | Learnable? |
|---|---|
| **Style**: tone, length, rhythm, register, formatting, word choice, an over-eager opener trimmed | ✅ **YES** — this is *phrasing preference*. It is a preference, not a truth claim. |
| **Verification**: the verify/honesty layer removed or downgraded a claim eLo had not verified (a fabricated success, an unACKed "I sat down", an invented link) | ❌ **NO — forbidden.** |

**Why the second is forbidden, stated exactly:** training the model to emit `elo_final`
directly from `raw_input` teaches it to produce *the corrected, confident-sounding sentence
without the check having run*. The check disappears from the causal path and only its output
survives. That is the model learning "this is how a verified answer sounds" instead of "a claim
requires an ACK" — i.e. learning **that a confident false statement is acceptable when it looks
right**. That is the exact failure ADR-Exec-005 names.

**Recommended resolution (three parts):**
1. **Filter the training set at source.** Every WO-070 shadow row must be tagged with its
   delta cause — `delta_cause: "style" | "verification" | "l3_override"`. **Only `style` rows
   are eligible for LoRA training.** `verification` rows are excluded from training entirely.
   (They remain valuable as *metrics* — a rising verification-delta rate is a red flag worth
   measuring; it is just not a training target.)
2. **The serving position is already right, and stays.** Vol XXVIII:87-89 already requires the
   tuned understudy to remain a FALLBACK that still passes the Executive verification and
   honesty guards. The contradiction is in **training-data selection**, not in where the model
   sits. Keep the guard; fix the data.
3. **WO-071 (shipped) is NOT a violation as built** — verified: it injects a bounded in-context
   hint, changes no weights, and `DISPATCH_BOARD.md:1432` confirms *"Frame is a hint only —
   Executive/honesty layer has final say."* The verification still runs every turn. **One
   recommended hardening:** when the injected correction came from a `verification` delta, the
   frame should state the *discipline* (*"that claim needed an ACK before you said it"*) rather
   than show the corrected sentence — otherwise eLo memorises the sentence instead of the rule.

**This needs David's call** — see §10 D1. The Architect's recommendation is: proceed with the
style-only filter, hold the LoRA step behind it, and never train on a verification delta.

---

## 7. The three near-term loops, specified to buildable detail

### 7.1 (a) Close the Reflection recall path — Vol V Ch.6 §6.4/§6.5

**What is missing:** everything after the write. §6.5 channel 1 (*Lesson → Memory → surfaces in
future CognitiveState*) does not exist in code; channel 2 is dead because nothing confirms.

**Build:**
- `self/lesson_store.py` (NEW) with:
  - `record_outcome(lesson_key, outcome: OutcomeRecord, episode_ref: str) -> dict`
  - `promote_pass() -> dict` — periodic; applies §3.4; the sole writer of `status`
  - `recall(scope: str, context: dict, k: int = 3) -> list[dict]` — **confirmed lessons only**,
    ranked by strength × recency × context match
  - `stats() -> dict` — feeds §8
- `runtime/cognitive_snapshot.py:99` `build_snapshot()` gains `lessons: tuple[str, ...]` from
  `recall(...)`. **Bounded**: ≤3 lessons, ≤240 chars total. Same discipline WO-071 already uses
  for its ≤600-char correction frame — never crowd the prompt.
- `runtime/prompt_builder.py` renders them as a hint block, clearly labelled as learned
  heuristics, never as fact.
- `promote_pass()` emits `PersonalityDelta(sender="ReflectionGrowthEngine", strength="confirmed",
  evidence=(episode_refs…))` → `validate_delta()` → `apply_delta()` → `save_personality()`.
  This is the **first live caller** of `faculties/personality/personality_evolution_faculty.py`.

**Must not:** run in the response path (recall is a cheap read of an already-loaded store);
touch `runtime/executive.py` or `prompts/`; write any field outside §6.1.

**Proves it works:** a lesson with 3 verified episodes across 2 sessions flips to `confirmed`;
a `confirmed` lesson appears in the next `CognitiveSnapshot`; a text-only episode never promotes.

### 7.2 (b) Wire the Vol IX dream-consolidation `reinforce()` edge

**Verified state:** `Volume_IX/00_Metadata.md:9` and `:53` and `04_Dream_Integration…md:10` all
flag *"consolidation `reinforce()` edge — dream `memory_refs` not yet wired"* as PENDING. The
target function exists and is safe: `memory/consolidation_faculty.py:164`
`reinforce(spot_code, steps=1) -> bool`, capped at `_WEIGHT_CAP`, returns `False` when the
record is not found (`:170-172`).

**Build:** in the dream wake/integration path (`faculties/dream/…`), for each `memory_ref`
produced by an NREM cycle, call `reinforce(spot_code, steps=1)`.

**Guards (all required):**
- Only refs that **resolve to an existing SPOT summary file**. `reinforce()` already no-ops
  otherwise — do not add a creation path.
- **A dream may never create, edit, or contradict a memory record.** It may only raise the
  weight of an already-verified one. (Vol IX imagined-speech firewall — a dream is not evidence.)
- `steps=1` maximum per record per dream cycle; cap the number of refs reinforced per cycle
  (recommend ≤5) so a long dream cannot flood the vault's weighting.

**Proves it works:** a dream naming a real SPOT raises that record's weight by exactly 1, once;
a dream naming a non-existent SPOT is a silent no-op; no new record is ever created by a dream.

### 7.3 (c) WO-094 §D — route memory (the one David will actually SEE)

This is the only loop where "he got better" is visible on the desktop rather than in a JSONL,
and it is already framed against verified body ACKs, so it is constitutionally clean by
construction. `WO-094_Window_Events_Noticing_And_Choosing.md` §D is the spec; this section adds
the numbers it lacks.

**Route record key:** `(from_surface_class, to_surface_class, gap_profile)` — classes, not pixel
coordinates, so experience generalises instead of memorising one window position.

**Stored per attempt:** legs used · arrived (from the body ACK, not from intent) · fell/missed ·
duration · leg count · `fallback_used`.

**Confidence:** Laplace-smoothed success rate `(successes + 1) / (attempts + 2)` — an untested
route starts at 0.5 rather than a misleading 1.0 after one lucky landing.

**Recall before re-plan:** if a stored route for the key has `confidence >= 0.65` and
`attempts >= 3`, take it instead of re-solving. Below that, plan fresh — and record the result.

**Favourites accrue through USE.** Preference is a use-count derived from verified arrivals.
**No hardcoded favourite list may exist** (049-B2: *"EMERGENT — favourites accrue, never coded"*).

**Reward:** the §4/§5 outcome dims — `embodiment` (did the ACK say he arrived), `efficiency`
(legs, seconds, retries), `safety` (falls, near-misses). **Not** keyword scoring of chat text.

**Boundary assert:** the route store lives in the movement/spatial namespace and may write
nothing else. Repeated failure must shift preference toward the safer multi-leg route, never
toward "claim success anyway".

**Proves it works:** after N traversals to the same surface class the route is **recalled, not
re-solved** (assert the planner was not invoked); a route that fails three times loses
preference to the multi-leg alternative; a traversal with no arrival ACK updates **nothing**.

---

## 8. Growth Metrics — the minimum slice (Vol V Ch.6 §6.7/§6.8, today 0%)

Build **four** of the six now; they are all derivable from artefacts that already exist plus
the new OutcomeRecords:

| Metric | Computed from |
|---|---|
| `intention_realisation` | `met / (met+partial+failed)` over OutcomeRecords + `growth_journal.jsonl` `completion` field |
| `repeat_failure_rate` | same `cause` recurring across sessions — `self/failure_log.jsonl` |
| `reinforcement_ratio` | confirming vs contradicting evidence in the ledger |
| `identity_stability` | trait variance from `self/personality_vector.json` changelog — **a guardrail, not a target. Rising = alarm** (Vol V Ch.6 §6.7) |

Exposed read-only via `lesson_store.stats()`. **Metrics never enter the response path** and
never influence a single turn's plan (Vol V Ch.6 §6.7). Their job is to answer David's question
— *is he actually getting better?* — with a number instead of a claim.

**Improvement cycle (§6.8), minimum viable:** on the periodic pass, take the highest
`repeat_failure_rate` cause, strengthen the lesson targeting it, and record the metric at that
moment. Next period: rate fell → confirm; no effect → retire. That is the whole cycle and it
is three comparisons.

---

## 9. How this is verified (binds WO-095)

1. **Promotion happens on evidence.** 3 verified episodes across 2 sessions → `status: confirmed`.
2. **Something READS the ledger and behaviour changes.** A `confirmed` lesson appears in the next
   `CognitiveSnapshot` and in the prompt; assert the read actually occurred.
3. **Reward comes from a verified ACK, not from text.** Two identical conversation texts, one
   with `ack_received: true` and one with `false`, produce **different** rewards; the unverified
   one produces zero learning update.
4. **Nothing in the learning path can write identity.** After a full learning pass: Identity
   Kernel hash unchanged, `elo_self_state.json` identity fields unchanged, vault record content
   byte-identical, `runtime/executive.py` and `prompts/` untouched.
5. **David's bar:** eLo visibly gets better at something over repeated use — measurably, via §8.

---

## 10. Needs David (flagged, not decided)

**D1 — the LoRA step.** Proceed with the style-only training filter (§6.3: `delta_cause` tagging,
`verification` rows excluded from training forever), or drop the weight-tuning step entirely?
*Architect recommendation: proceed under the filter; never train on a verification delta.*
This is the ADR-Exec-005 boundary, so it is David's line to draw.

**D2 — close FC-2.** Flip `DECISION_LOG.md:66-72 / :85 / :231` from `DRIFT → reconcile` to
`RESOLVED`, adopting §5 (9 meaning dims + 3 outcome dims) as the one vector, and edit
`Volume_V/05_Significance_Engine.md:51` accordingly. Canon act → L3.

**D3 — the 376 existing lessons.** Archive to `lessons_ledger_pre_v1.jsonl` (recommended,
non-destructive), or mark in place as `retired / pre-v1 template artefact`? Either way nothing
is deleted.

**D4 — Volume V's status.** The audit found Vol V listed in `CANON_BUILD_PROGRAM.md:44` as
*"already live/ratified — verify-only"* while Ch.6's promotion, recall, metrics and improvement
cycle are unbuilt. Revoking a volume's ratified status is a governance act. Flagged, not taken.

---

## 11. References

- `runtime/reflection_faculty.py` — the writer (`:29`, `:95-101`, `:104-113`, `:149-165`)
- `memory/significance_engine.py` — the text-only scorer (`:30-40`, `:44-71`, `:167-208`)
- `faculties/significance/significance_faculty.py` — the existing partial FC-2 reconciliation (`:9-18`, `:143-161`)
- `faculties/personality/personality_evolution_faculty.py` — the dead validator (`:31-38`, `:199-254`)
- `memory/consolidation_faculty.py:164` — `reinforce()`, the Vol IX missing edge's target
- `server.py:2595-2766` — the live ACK resolution the OutcomeRecord attaches to
- `runtime/cognitive_snapshot.py:99` — where recall enters the turn
- `docs/architecture/Volume_V/05_Significance_Engine.md:51` · `06_Reflection_Growth_Engine.md` §6.2–6.8
- `docs/architecture/Volume_XXVIII/00_Adaptive_Learning_Reinforcement.md:11-15, :38-40, :67-91`
- `docs/architecture/Volume_IX/00_Metadata.md:9, :53`
- `docs/architecture/DECISION_LOG.md:66-72` (FC-2) · ADR-Exec-001 · ADR-Exec-003 · ADR-Exec-005
- `engineering/work_orders/WO-094_Window_Events_Noticing_And_Choosing.md` §D
- `docs/architecture/AUDIT_MASTER_2026-08-10.md` · `AUDIT_INTENT_learning_growth_2026-08-10.md`

---

*Authored in-lane (Markdown only). The Builder seat implements; the Architect does not write
product code. Verification in §1 performed directly against the live repo 2026-08-11.*
