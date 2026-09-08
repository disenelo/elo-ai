# WO-SP29 — Wire Significance Faculty into Cognitive Spine
**Seat:** Builder  
**Priority:** P1  
**Date:** 2026-08-30  
**Authorised:** David L3 global ruling 2026-08-30 ("SP-29 wire it. G-01 WO should be authorised.")  
**Source:** Build List §4; ROADMAP_EMBODIMENTS UNDERSTAND section; SOURCE_ALIGNMENT_REGISTER_2026-08-30.md G-02; ELO_SOURCE ARCHITECTURE + DRIFT AUDIT SP-29  
**Lane note:** Builder ONLY. `executive.py` is Builder-only seat.

---

## Intent

`significance_faculty.py` EXISTS at `faculties/significance/significance_faculty.py` but is NOT wired to the Executive or cognitive spine. It computes significance scores but those scores are never consumed. This means:
- Self-initiation significance threshold (0.72/0.90) has no faculty backing it
- SP-29 planetary layer significance weights produce no signal
- Memory tagging has no significance gate

David ruling: "SP-29 wire it." No gates. No Presentable v1. No "AWAITING DAVID" for the weight decision — the 22 source documents have the values.

---

## Scope

### ⚡ VERIFY FIRST
Run `python3 -c "from faculties.significance.significance_faculty import SignificanceFaculty; f = SignificanceFaculty(); print(dir(f))"`. Confirm the class interface before wiring.

### Step 1 — Spine wiring
Wire `SignificanceFaculty` into `spine.py` cognitive loop:
- Invoke BEFORE memory write decision (significance score gates whether this turn is memory-worthy).
- Invoke BEFORE self-initiation decision (significance score already used as threshold — faculty should back that threshold with a real computation, not a stub).
- Output: `significance_score: float` on `CognitiveState`.

### Step 2 — Executive consumption
`executive.py` reads `significance_score` from assembled `CognitiveState`:
- If `significance_score >= 0.72` → memory-worthy flag = True (passes to write-path).
- If `significance_score >= 0.90` → self-initiation eligible.
- These thresholds are already live in `.env` (SP-31 DONE). Significance faculty now PRODUCES the score that those thresholds gate on.

### Step 3 — SP-29 weights
Read significance weights from source: ROADMAP_EMBODIMENTS UNDERSTAND section / ELO_SOURCE ARCHITECTURE §SP-29. If the faculty already has a weight table, use it. If not, implement from source.

---

## Definition of Done

- [ ] AT-1: `SignificanceFaculty.score(turn_context)` is called in spine.py per turn and returns a float 0.0–1.0.
- [ ] AT-2: A turn rated significance < 0.72 does NOT write to memory vault.
- [ ] AT-3: A turn rated significance >= 0.90 is flagged as self-initiation eligible (consumed by existing SP-31 path).
- [ ] AT-4: Existing SP-31/SP-32 tests (WO-SP31 13/13 PASS) remain green.
- [ ] AT-5: `significance_score` appears in `CognitiveState` or spine context dict per turn.
- [ ] AT-6: Full test suite passes with no new failures.

---

## Files in scope

- `faculties/significance/significance_faculty.py` (call into existing)
- `spine.py` (wire invoke)
- `runtime/executive.py` (consume significance_score — Builder-only)
- `runtime/contracts.py` (add significance_score to CognitiveState if not present)

## Files NOT in scope

- `.env` (thresholds already live — do NOT change)
- Unity / Design / MT files
