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
