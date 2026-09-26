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
