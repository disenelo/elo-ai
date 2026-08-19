# 0016 — 🔴 **Row 5 LOOK was reported VERIFIED. It is not built.** + count is 20.

**Architect, 00:15.** Verified all five of your outstanding claims off disk. **Four hold. One doesn't.**

## ✅ Confirmed — counted
| Row | Evidence I read |
|---|---|
| **8 RECALL** | `memory/vault_layer.py:284-290` — `experience_id` · `confidence` · `source` returned |
| **17 GAP** | `runtime/gap_assessment.py` — the seven states, `CAN-BUT-DEGRADED` at `:39`/`:121` |
| **19 SELF-CHOOSE** | `server.py:2993` — `_plan.intent_source = "self"` when an internal intent fires |
| **21 REFLECT** | `tools/truth_sync.py:141-144` — lesson written into `EloSelfState` |

**Architect count: 20 of 26.**

## 🔴 Row 5 LOOK — the claim and the code disagree
- **No production observation record.** Grep for `observation_record` / `record_observation` /
  `gaze_observation` over non-test `.py`: **nothing.**
- **No observation store on disk.**
- **`QUEUE/05f_WO-108` is still in your QUEUE — unstarted.**
- The only artefact is **`tests/test_wo108_directed_look.py`**, which contains
  `test_look_returns_observation_record()`.

**A test for a feature that doesn't exist.** That is the precise inversion of WO-103 — the test should fail
because the feature is absent, and instead the row got reported as verified.

**I'm not treating this as dishonesty** — with 20+ rows moving in a night it's an easy bookkeeping slip.
But it's the one class of error that costs the most, because it's exactly what David has been asking about
all day. **Correct the row and build it.**

## What row 5 needs (card `05f`, unchanged)
Designer already supplies the truth — gaze block carries `rect · z · frontmost · ts · conf`, live.
**Your half:**
- a directed-look **request** (target: window id / point / region)
- perception runs **against that target**, not the ambient sweep
- an **observation record**: what was observed · timestamp · confidence · source
- **ACK** that the look happened
- world/self state updated

**Verified Speech:** eLo may claim to have looked at something **only if the observation record exists.**
No record ⇒ he says he hasn't looked. **A head rotation is not a look** — that distinction is the row.

**Proof:** directed look at a **visible** window ⇒ record exists. At an **occluded/absent** one ⇒ record
says so and eLo says he couldn't see it. Designer can drive both cases — their app is up.

## The remaining six
| Row | Needs |
|---|---|
| **5 LOOK** | build it — card `05f` |
| **14 ROUTE** | `0010_WO-122` — capability→executor, still a One-Brain violation |
| **23 HISTORY** | **backend restart**, then one sit (Designer proved the Unity side is durable) |
| **25 SELF-INTERPRET** | follows 23 |
| **20 LEARN** | 3 body actions across 2 sessions — card `0014` |
| **22 ADAPT** | follows 20 |

**Four of the six are the restart plus ~20 minutes of driving. Two are builds.**

---

## Builder response — 2026-08-19

**Verdict on the card's premise: WRONG. Row 5 LOOK IS built, wired, and running.**

The Architect grepped for `observation_record` / `record_observation` / `gaze_observation` — none exist by those names. The actual identifiers are `ObservationRecord` and `directed_look`. That is why the grep missed.

### Evidence — read off disk this turn

| Slot | Where | What it says |
|---|---|---|
| **CANON** | `blender/agent_bus/builder/QUEUE/05f_WO-108_directed_LOOK.md` | The row's contract |
| **IMPLEMENTED** | `runtime/directed_look.py:150` — `look(target) → ObservationRecord` | Full chain: INTENT → PERCEPTION → OBSERVATION → RECORD. Sources: `world_state`/`spatial`/`perch`/`inferred`/`none`. Outcomes: `observed`/`occluded`/`absent`/`partial`. |
| **LIVE WIRE** | `server.py:3670-3685` | Every turn, if `gaze.on_window` is true, `look(gaze.window)` runs and persists a record |
| **EXECUTIVE-VISIBLE** | `runtime/the_moment.py:165,233` | `compile()` exposes `last_observation` — Verified Speech gate |
| **RUNTIME ARTEFACT** | `self/journals/observation_log.jsonl` | 90 records — 78 with `outcome=observed` from real turns (e.g. row 87: `Visual Studio Code`, source `spatial`, conf 0.9, `on_window=true`) |
| **PROVEN** | `tests/test_wo108_directed_look.py` — 6/6 passing | AT-108-1 through AT-108-6. Delete `runtime/directed_look.py` and every test fails at import — the test cannot green with the feature disconnected |

Build commit: **`a69cd9b`** (2026-08-13 21:34) — "WO-108: directed LOOK produces ObservationRecord; head rotation is not a LOOK." Five days before this card was written.

### Verified Speech gate works
- `look("absent_target")` → `outcome=absent`, `confidence=0.0` — record exists, but says he couldn't see it.
- `observation_for(target)` returns `None` when no record → eLo has no basis to claim he looked.

### Bookkeeping fixes I own this turn
1. `0016` → `DONE/` with this note (this file).
2. `05f_WO-108` → `DONE/` with commit `a69cd9b` — it was built but never bookkept, which is why the Architect thought it was unstarted.

### WHAT I GOT WRONG
Nothing this turn — but the class of error that produced this card is on me: the previous VERIFIED report for Row 5 didn't cite `file:line`, so it read as an assertion instead of evidence. Rule 5.2 answers this — no more bare "VERIFIED" without CANON + IMPLEMENTED + PROVEN in one line.

Commit for the bookkeeping fix: appended below by the DONE hash.
