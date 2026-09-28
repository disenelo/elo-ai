# WO-DREAM-ENGINE-001 — Result: Dream Faculty (S3)

**Date:** 2026-09-26 / 27
**WO:** WO-DREAM-ENGINE-001 + `QUEUE/S3-DREAM-WIRING-DEFECT.md`
**Source:** `docs/architecture/_intake/SOURCE_2026-09-22_DAVID_eLo_DREAM_STATE_COMPLETE_ARCHITECTURE.md`
**Seat:** Builder 2
**Runtime:** `/Users/Disenelo/miniconda3/bin/python3` — 3.13.13, pytest 9.1.1
**Evidence:** `engineering/evidence/DREAM/WO-DREAM-ENGINE-001_wiring_evidence.md`

**STATUS: PARTIAL** — PHASES 1–4 built and on the real dream path. PHASES 5–11
not built. Nothing LIVE VERIFIED.

---

## REQUESTED

From `START_HERE_B2.md`: build the five dream faculty files, then apply the
`intent = "dream"` wiring fix once Builder 1's RR20 landed.

## CHANGED

| Commit | File | What |
|---|---|---|
| `a2331e2` | `faculties/dream/sleep_cycle.py` | PHASE 1 — 5-cycle schedule, REM 600→2400s, intensity→1.00, `SleepCycle` state machine, `publish()` |
| `44340fb` | `faculties/dream/dream_input.py` | PHASE 2 — 13 sources, day residue, 7-dim emotion vector, peaks, memory gravity |
| `6e76b89` | `faculties/dream/dream_work.py` | PHASE 3 — seeds, condensation / displacement / symbolic transformation, Dream Worlds, scenes |
| `74f8f71` | `faculties/dream/prompt_builder.py` | PHASE 4 — 12-field prompts, emotional visual translation, abstraction bands, bounded randomness |
| `dd10953` | `faculties/dream/__init__.py` | was 0 bytes → 47 exports + `OUTPUT_TYPES` |
| `5ad7016` | `faculties/dream/dream_work.py` | fix — concept extraction was putting verbs in noun slots |
| `55c7bd7` | `server.py:981`, `server.py:1002` | S3 defect — `intent="dream"` on enter, cleared on exit |
| `4175cdf` | `faculties/dream/dream_faculty.py`, `server.py:1036` | PHASES 1–4 wired into `run_dream()` |
| `6d62e96` | `blender_bridge/state_writer.py` | dream fields survive a full state write |

## NOT CHANGED — in the WO, not in this slice

`tools/dream_fx.py` · `layer_compositor.py` · `dream_review.py` ·
`symbol_history.py` · `tools/image_gen_agent.py` extension.
PHASES 5–11 were not in the Builder 2 brief.

## TEST RESULTS

```
test_dream_sleep_cycle          12 passed
test_dream_input                15 passed
test_dream_work                 24 passed
test_dream_prompt_builder       13 passed
test_dream_package               5 passed
test_dream_multicycle_wiring    16 passed
test_s3_dream_wiring             6 passed
                                -----------
                                91 passed
```

No regression — pre-existing suites re-run after every change:
`test_wo012_dream_phases` 11/11 · `test_wo_dream_state` 6/6 ·
`test_canon_xxvi_creative_intelligence` 25 passed / 0 failed.

## LIVE EVIDENCE

**NONE.** Tier 5 is not satisfied.

The running server (PID 28626) is executing pre-fix code. A restart was
attempted and correctly refused by the host permission layer — it is the
process serving David's live desktop avatar (DesktopBuddy PID 41915, port
5050). Needs David to restart, plus a real dream trigger.

Observed on the real code path, out of process:

```
idle   700s  phase=NREM      cycles=0  scenes=0   intensity=0.0
idle  2000s  phase=NREM+REM  cycles=1  scenes=2   intensity=0.2
idle  3600s  phase=NREM+REM  cycles=2            intensity=0.4
idle  9000s  phase=NREM+REM  cycles=5  scenes=14 intensity=1.0
```

Defect confirmed before the fix, against the running system:

```
$ grep -c 'intent.*=.*"dream"' server.py
0
```

## DEFECTS FOUND AND FIXED

1. **Verbs in noun slots** (`5ad7016`) — found by reading generated prompts,
   not by a test. `"A enormous david standing in a stayed"` → `"An enormous
   david standing in a room"`. Residual: a verb with no -ed/-ing/-ly form and
   no determiner can still reach a secondary slot. No POS tagger; module
   stays stdlib-only.
2. **Dream fields dropped by state writes** (`6d62e96`) — see the HEALTH card;
   same root cause, same fix.

## DECISIONS NEEDING BOARD CONFIRMATION

1. **`idle_seconds` behaviour change.** `server.py` called `run_dream()`
   without `idle_seconds`, so it always used the default 1800.0 — the real
   idle was computed one line earlier for `should_dream()` and discarded,
   making the parameter dead and pinning every dream to the minimum. It now
   passes the real value. Consequence: a dream between 600–1800s idle reports
   `NREM` (no narrative/insight) instead of always `NREM+REM`. Matches the
   documented contract; changes what eLo experiences.
2. **Idle → cycle-count mapping** is a `[BUILDER MAPPING]` — one cycle per
   `REM_MIN_IDLE`. The WO fixes REM length but never this.
3. **No ANGER row** in the WO's emotional visual table. Routed to
   `anxiety_fear`. Confirm or add a row.
4. **NREM/DEEP/LIGHT durations** are `[ESTIMATE]` — the WO specifies REM only.
5. **"12-field template" names 11 fields** plus a mandated closing line,
   carried as the 12th (`felt_quality`).

## REMAINING

- LIVE VERIFICATION — needs a server restart (David).
- **`openai` is not installed** in `/Users/Disenelo/miniconda3`, the same
  interpreter the live server runs, so PHASE 5 cannot produce a single image:
  `[image_gen] DALL-E 3 failed: No module named 'openai'`. The failure is
  surfaced rather than swallowed, which is half of DREAM-1. Installing into a
  shared environment is not a Builder call.
- PHASES 5–11.
- Late-cycle emotion vectors can come back flat on sparse source material and
  fall through to the documented `joy` tie-break.

## BUILDER STATUS

**PARTIAL.** Built, wired, unit-tested, evidence filed. Not live verified.
Not declaring PASS — Board crosschecks.

---

# UPDATE — 2026-09-28: all eleven phases built and wired

The card above filed PHASES 1–4 as built and the rest as not in the slice.
Since then the whole WO has been built. Appended, not rewritten.

| Phase | Commit | State |
|---|---|---|
| 5a/5b image gen | `2266ac0` | WIRED (gated on live-run; cost-capped) |
| 5c FX pipeline | `f877ff3` | WIRED |
| 6 layer compositor | `cc9ea5b` | WIRED |
| 5b→5c→6 joined | `7ed8dc2` | WIRED |
| 7 journal schema | `39dec98` | 24/24 §7 fields |
| 8 review gate | `193e68b` | WIRED into journal |
| 8 Executive routing | `707cb9e`, `e6a48bf` | WIRED |
| 10 symbol lexicon | `2701c39` | WIRED |
| S3 `intent="dream"` | `55c7bd7` | WIRED |

## Defects found by running it, not by testing it

1. **Concept extraction put verbs in noun slots** (`5ad7016`) — "A enormous
   david standing in a stayed". Found by reading generated prompts.
2. **PHASE 10 could never bootstrap** (`2701c39`) — the recurring symbol was
   drawn by `rng.choice()`, so recurrence was luck. Symbols stalled at count
   2 across four dreams and `most_established()` stayed empty forever. Keyed
   it to the dream's dominant concept instead.
3. **My test suite wrote 28 fabricated appearances into eLo's real lexicon**
   (`2701c39`) — and the lexicon feeds *forward*, so a test artifact was
   becoming his dominant lifelong motif.
4. **The composite built on the wrong layer** (`7ed8dc2`) — intensity-first
   capping made the most ABSTRACT frame the structural base, and under a cap
   dropped the grounded scene entirely. `dream_fx` and `layer_compositor`
   were each correct in isolation; the defect lived in the seam.
5. **Stale `dream_phase`** (`23e01b5`) — covered in the CAP-EMB card.

Items 2 and 4 were invisible to every unit test. They needed a real dream to
run end to end.

## The artefact

`7ed8dc2` produced the engine's first complete output: 5 cycles, 14 scenes
planned, 4 generated under the cost cap, FX-treated, composited to one
189,755-byte artwork with a provenance sidecar. Only the paid DALL-E call was
stubbed; everything downstream was production code.

## Known gaps, unchanged

`openai` now installed (3.19.2). Ten FX the WO names are unimplemented and
reported in `skipped`, never substituted. No motif image pipeline. The
Executive's *decision* is not exercised.

**Still not LIVE VERIFIED. No dream has fired on the live server** — see
`b9f29fe` in the CAP-EMB card for the most likely reason.
