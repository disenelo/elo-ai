---
chapter: 3
title: "Consolidation & the Forgetting Curve — What Lasts, What Fades"
volume: VIII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL (consolidation faculty + forgetting curve LIVE via WO-011; reinforce-on-retrieval wiring PENDING)
audit_status: OPEN
dependencies:
  - Volume_VIII/01_Memory_Architecture.md (§1.3 consolidation, §1.4 forgetting — this deepens both)
  - Volume_VIII/02 (weight field, spot code — the data the curve operates on)
  - runtime/reflection_faculty.py (integrate_session — shared integration act, Vol V Ch.6)
  - Volume_V/05 Significance (selects what consolidates), Volume_V/07 & Volume_X Personality (delta target)
  - memory/consolidation_faculty.py (LIVE anchor), memory/summariser.py (compress/theme detect)
---

# Chapter 3: Consolidation & the Forgetting Curve

## 3.0 Purpose

Retrieval-relevance is a moving target: a store that keeps everything forever becomes noise,
and a store that keeps nothing loses the relationship. This chapter specifies the two timed
processes that keep the vault meaningful over weeks and months — **consolidation** (what is
strengthened and promoted) and the **forgetting curve** (what is allowed to fade) — grounded
in the live `memory/consolidation_faculty.py` (WO-011). Chapter 1 §1.3–1.4 states the model;
this is the operational spec with the actual parameters.

This closes **Architecture Audit gap #4** (Consolidation) at spec level and makes the
forgetting behaviour auditable.

## 3.1 Principle — Timed, Never in the Hot Loop

**3.1.1 Consolidation is an integration-window act, never a response-path act.** It runs at
session close or idle/nightly, never inside a turn (`consolidate()` docstring: *"Must only be
called at session close or idle. Never call from the response path."*). This is the same
discipline as Reflection (Vol V Ch.6 `integrate_session`); consolidation is Reflection
specialised for memory (hippocampal replay).

**3.1.2 Consolidation is atomic.** A failed run leaves prior memory intact and retries next
window. In the live faculty each stage is independently wrapped so one failure (e.g. decay)
cannot corrupt another (e.g. integration) — errors are collected, not raised.

**3.1.3 Consolidation integrates, it does not archive.** It changes weights, promotes
episodic → semantic, and extracts patterns; it does not silently delete. Forgetting is a
*weight floor of 1* ("faded"), never removal — nothing the relationship was built on is ever
destroyed.

## 3.2 The Consolidation Cycle (live)

`consolidate(session_summaries, execution_reports, project)` runs three stages:

```
1. FORGET     apply_forgetting_curve()            → decay old, weak, non-identity records (§3.3)
2. INTEGRATE  compress_session() → integrate_session(weight=7, tags=["consolidated","session-close"])
                                                   → write ONE session-level record via the writer (Ch.4)
3. PATTERN    _extract_patterns()                 → themes repeated ≥3× across turns → semantic elevation
   ↓
return { forgetting, integrated:[spot], patterns:[theme], errors:[] }
```

**Rules (MUST):**

- The integration write goes through the **one writer** (`vault_layer.write_memory` via
  `reflection_faculty.integrate_session`) — consolidation does not open a second write path
  (Ch.4 D-F).
- Session-level consolidation writes at `weight=7` (important) by default; the primary action
  of the session is the most frequent CAL action across its turns.
- Pattern extraction uses `summariser._detect_themes`; a theme seen in **≥3** turns is
  elevated as a `pattern` output. Pattern → *semantic* memory (Vol V Ch.3 Layer 5) and may
  feed a personality proposal (§3.4).

## 3.3 The Forgetting Curve (live parameters)

`apply_forgetting_curve(dry_run=False)` scans `summary/` notes and decays the weak and old.
The **live constants** (`consolidation_faculty.py`) are canon until a tuning WO changes them:

```
_IDENTITY_FLOOR   = 8    weight ≥ 8 → PROTECTED, never decays (identity + pinned)
_DECAY_THRESHOLD  = 6    weight < 6 → eligible for decay
_DECAY_AGE_DAYS   = 14   record must be ≥ 14 days old before it can decay
_DECAY_STEP       = 1    weight −1 per consolidation pass
_REINFORCE_STEP   = 1    weight +1 per reinforcement event
_WEIGHT_CAP       = 9    maximum weight
minimum after decay = 1  (a faded record floors at 1 — never deleted)
```

Strength model (Ch.1 §1.4 made concrete): a record's `weight` is its strength.

```
decay eligible  ⟺  weight < 6  AND  age ≥ 14 days  AND  weight < 8
protected       ⟺  weight ≥ 8  (identity / pinned — never touched)
between 6 and 7 ⟺  stable: useful/important, neither decayed nor floored
```

**Rules (MUST):**

- **3.3.1 Identity never decays.** `weight ≥ _IDENTITY_FLOOR (8)` is untouchable. This
  operationalises Runtime Invariant 7 and Ch.1 §1.4 "identity-level & pinned memories do NOT
  decay." Significance-pinned records (Vol V Ch.5) are written at weight ≥ 8 precisely so the
  curve cannot reach them.
- **3.3.2 Decay is bounded and slow.** One step per pass, only after 14 days, only below
  weight 6, floored at 1. Forgetting is a gentle relevance filter, not deletion.
- **3.3.3 `dry_run` is the audit hook.** `apply_forgetting_curve(dry_run=True)` reports what
  *would* fade without writing — the mechanism by which the Audit can inspect forgetting
  behaviour safely.

## 3.4 Reinforcement — Use Strengthens Memory

`reinforce(spot_code, steps=1)` raises a record's weight (capped at 9) when it is
retrieved and actually used in a turn — "referenced = relevant" (Ch.1 §1.4; Vol V Ch.3
"a memory grows stronger when referenced again / influences decisions / proves useful").

**Rules (MUST):**

- Reinforcement is the *counterforce* to decay: a low-weight record that keeps proving useful
  climbs back above the decay threshold and survives. A record no one revisits fades.
- Reinforcement can never push a record past `_WEIGHT_CAP (9)`.

**GAP (PENDING) — reinforcement is not yet wired into retrieval.** `reinforce()` exists and
is tested (`tests/test_wo011_consolidation_faculty.py` FT-2), but the retrieval path
(`vault_layer.lookup` / `recall_context`, Ch.4) does **not** call it — retrieved-and-used
records are not currently strengthened. Until wired, the forgetting curve runs *without* its
counterforce, so useful-but-old records can still fade. Flag for the owning seat: call
`reinforce(spot)` for each record the Executive actually uses in a turn (integration-window,
not hot-loop). This is the single missing edge to make §3.4 real.

## 3.5 Consolidation → Personality (proposals only)

When consolidation surfaces a pattern that implies eLo has changed ("David consistently
prefers X"), that is a **proposal** to Personality (Vol V Ch.7 / Vol X), validated against
the Identity Kernel — **never self-applied**. Memory strengthens and promotes its own
records freely; it does not mutate personality or identity directly.

**Rule (MUST):** any personality-affecting consolidation output is emitted as a validated
proposal (`VALIDATION_REQUIRED` → Ch.7). Identity, values, and truth are immutable
(Learning-From-Consequences principle); only skills/preferences adapt, and only through the
validated path.

## 3.6 Faculty Lifecycle (consolidation sub-component)

Universal lifecycle (Volume_V/CONTRACTS.md §3). Consolidation is the
`LEARNING → VALIDATION_REQUIRED → UPDATING → STABLE` arc, entered only in the integration
window:

```
ACTIVE (idle)
  └─ session close / nightly ─► LEARNING (replay: forget · integrate · pattern)
        └─ pattern implies trait shift ─► VALIDATION_REQUIRED (proposal → Ch.7)
              └─ validated ─► UPDATING (write reinforced/pattern records via the one writer)
                    └─ STABLE ─► ACTIVE
  fault at any stage ─► ERROR_RECOVERY → preserve prior vault → ACTIVE (retry next window)
```

## 3.7 Acceptance Tests

```
FT-1  Timed only            Given a live turn, Then consolidate() is never invoked in the response path.
FT-2  Atomic on failure     Given integration raises mid-run, Then decay+prior vault are intact; errors[] populated; retry next window.
FT-3  Identity floored      Given a weight-9 identity record aged 200 days, Then apply_forgetting_curve leaves it untouched (protected++).
FT-4  Bounded decay         Given a weight-4 record aged 20 days, Then one pass yields weight 3 (−1), never below 1, never on <14-day records.
FT-5  Episodic → semantic   Given a theme in ≥3 turns, Then _extract_patterns returns it for semantic elevation.
ST-1  dry_run writes nothing Given apply_forgetting_curve(dry_run=True), Then decayed[] is reported but no file is modified.
ST-2  Reinforce counters decay  Given a used low-weight record reinforced +1, Then its weight rises toward the cap and it escapes the decay band. (blocked on §3.4 wiring)
ST-3  No unvalidated trait shift Given a pattern implying a trait change, Then it is a proposal to Ch.7, never self-applied.
IT-1  Significance → consolidation → personality  Ch.5 pins a turn (weight≥8) → survives decay → consolidation promotes its theme + proposes a validated trait nudge (Ch.7) → retrievable after restart.
```

## 3.8 References
- Code: `memory/consolidation_faculty.py` (LIVE — cycle, curve, reinforce), `memory/summariser.py`
  (`compress_session`, `_detect_themes`), `runtime/reflection_faculty.py` (`integrate_session`).
- Tests: `tests/test_wo011_consolidation_faculty.py` (WO-011).
- Canon: Vol VIII Ch.1 (§1.3/§1.4 model), Ch.2 (weight/spot), Ch.4 (the one writer);
  Vol V Ch.5 (significance → weight ≥ 8 pins), Ch.6 (integrate_session), Ch.7 / Vol X (personality proposals).
- `ARCHITECTURE_AUDIT.md` gap #4.

---
**Status: READY FOR REVIEW** — the live consolidation cycle, the forgetting-curve parameters,
reinforcement, and the proposals-only personality boundary, with lifecycle + tests. Closes
Audit gap #4 at spec level. FLAG: `reinforce()` is not yet wired into the retrieval path
(§3.4) — decay currently runs without its counterforce.
