# eLo CAPABILITIES 1–26 — STATE · WHY IT FAILS · WO · THE FIX
### 2026-08-13 19:25 · every line [VERIFIED] by reading the file. No invented diffs.
**VERIFIED: 1 of 26.** PARTIAL counts as zero. Standard: Ruling H — state, never the sentence.

---

# THE TABLE — capability · state · why · WO · fix

| # | Capability | State | WHY IT FAILS | WO | THE FIX | Seat |
|---|---|---|---|---|---|---|
| 1 | IDENTITY | PARTIAL | 🚫 No identity field in `EloSelfState:139-167`. Prompt text only — Executive can't read it | **WO-107** | Add `identity`/`core_values`/`invariants` fields; render prompt **from** them | Builder |
| 2 | WHERE | PARTIAL | 📖 **MISREAD.** Reads `pos_x/pos_y/height_px`; Unity writes `x/y/height`. Defaults to `0.5,0.1` — **fabricates position.** `except: pass` hides it | **WO-100** | Rename 3 keys + delete the swallow | Builder |
| 3 | BODY | PARTIAL | 🔇 `embodiment` field exists, **no live-path writer** | **WO-107** | Write it each turn; compute the tier instead of hardcoding | Builder |
| 4 | SEE | PARTIAL | 🔌 `plan.world` assembled every turn, **zero readers** | **WO-106** | Executive reads the plan, not re-queried sensors | Builder |
| 5 | LOOK | FORWARD | 🚫 No observation record exists. A head turn is not a look | **WO-108** | Build the observation record + directed-perception request | Builder+Design |
| 6 | ATTEND | PARTIAL | 🔌 WM competition runs, **winner discarded** | **WO-106** | WM winner drives attention, not raw `attention_model` | Builder |
| 7 | REMEMBER | PARTIAL | 🔌 `reinforce()` only in `recall_context()` — **zero callers.** Memories decay when used | **WO-109** | Move reinforce **into** `lookup()` | Builder |
| 8 | RECALL | PARTIAL | 📢 Returns text — no `experience_id`/`source`/`confidence` | **WO-109** | Return the §4 provenance set | Builder |
| 9 | KNOW | PARTIAL | 📢 Epistemic tiers cover **body only** | **WO-110** | Tier any fact, not just body state | Builder |
| 10 | INFER | PARTIAL | 🧊 `the_moment.py:85` always emits `"inferred"`; `:67` always `"verified"` | **WO-110** | Compute the tiers | Builder |
| 11 | UNKNOWN | PARTIAL | 🚫 No representation of the unobserved | **WO-110** | Make absence statable | Builder |
| **12** | **ACT** | ✅ **VERIFIED** | — | — | **Done** | — |
| 13 | VERIFY (ACK) | PARTIAL | 📢 ACK for **3 actions.** `anim_trigger:34` returns True **on file write.** Tools/scale/image_gen: no signal | **WO-111** | Generic `action→executor→ACK` contract; timeout = failure | Builder |
| 14 | ROUTE | PARTIAL | 🔌 Designer **now emits** `last_move` ✅ — **zero Python readers.** `route_memory.py` correct, **zero importers** | **WO-118** | Read `last_move`, feed `route_memory` | Builder |
| 15 | CHOOSE | PARTIAL | 🔇 `executive.py:156-235` early-returns one action. **All 35 entries `confidence:null`, `alternatives:[]`** | **WO-112** | Form a candidate set with utilities; persist it | Builder |
| 16 | AFFORD | PARTIAL | 🔌 Computed live, **thrown away** — `prompt_block` zero callers | **WO-113** | Route to Executive; join with body capability | Builder |
| 17 | GAP | FORWARD | 🚫 7-state vocabulary absent; needs 14 consumed for `reliable_range` | **WO-113** | Build the 7 states with real numbers | Builder |
| 18 | INTEND | PARTIAL | 🚫 `plan.intent` has **no `source`** | **WO-114** | Add `intent_source: david\|self\|reflex` | Builder |
| 19 | SELF-CHOOSE | FORWARD | 🔌 `emergent_cognition` **runs live**, emits `source:curiosity_peak` → **prompt text only** | **WO-114** | Route emergent intents into the Executive | Builder |
| 20 | LEARN | PARTIAL | ⚙️ `episode_ref=""` ⇒ gate needs 3 distinct, gets 0. Writer emits `capability`, gate wants `preference`. **1 candidate, 0 confirmed** | **WO-096B**·**WO-104** | Real `episode_ref`; reconcile scope; then LoRA | Builder |
| 21 | REFLECT | PARTIAL | 📢 Writes journals, **never reaches `EloSelfState`** | **WO-115** | `integrate_session` updates the self-model | Builder |
| 22 | ADAPT | BLOCKED | ⛓ on 20 + 24 — no before/after delta exists | **WO-116** | Falls out once 20+24 land | Builder |
| 23 | HISTORY | PARTIAL | 🔌 `append_autobiography` **zero callers**; file **doesn't exist** | **WO-115** | Call it on verified events; read chronologically | Builder |
| 24 | SELF-OBSERVE | PARTIAL | 🔌 `derive_tendencies` runs live; `record_behaviour`+`update_habits` **zero callers** ⇒ inputs empty | **WO-116** | Call `record_behaviour` on every ACKed action | Builder |
| 25 | SELF-INTERPRET | BLOCKED | ⛓ on 21·23·24 | **WO-117** | Falls out once those land | Builder |
| 26 | MEANING | BLOCKED | ⚙️ `evaluate()` accepts `outcome=` and scores it. **Both callers omit it** | **WO-101**·**WO-115** | Pass `outcome=outcome` at 2 sites | Builder |

## THE TALLY — why they fail
| Mode | Rows | Count |
|---|---|---|
| 🔌 **BUILT, NEVER WIRED** — correct, zero callers | 4·6·7·14·16·19·23·24 | **8** |
| 🚫 NOT BUILT | 1·5·11·17·18 | 5 |
| 📢 NEVER TALKS BACK / incomplete output | 8·9·13·21 | 4 |
| ⚙️ Producer/consumer disagree · argument omitted | 20·26 | 2 |
| 🔇 NEVER FIRES | 3·15 | 2 |
| 📖 MISREAD | 2 | 1 |
| 🧊 HARDCODED constant | 10 | 1 |
| ⛓ BLOCKED on the above | 22·25 | 2 |
| ✅ VERIFIED | 12 | **1** |

**20 of 25 failures are wiring, not missing design.** Components exist, are correct, are tested. Nothing
calls them. **Only 5 rows need something genuinely built — and nothing is stopping any of them.**

## WHAT IS STOPPING THE 5 NOT-BUILT ROWS
| Row | Blocked by |
|---|---|
| 1 IDENTITY field | **Nothing.** A dataclass field. |
| 5 LOOK | **Nothing.** Needs an observation record type; gaze already reaches Unity. |
| 11 UNKNOWN | **Nothing.** The tier machinery exists for the body already. |
| 18 INTEND `source` | **Nothing.** One field. The values are already produced and discarded. |
| 17 GAP | **One card** — `WO-118` consuming `last_move`, emitted 19:30. |

**No gate. No decision from David. No missing technology.** They were not built because no card existed
for them until 2026-08-13.

---

# THE CODE — where the fix is a code-level change

## WO-100 · row 2 WHERE — `desktop/spatial_state.py:97-99`
```python
# BEFORE
spatial.pos_x     = float(d.get("pos_x", 0.5))
spatial.pos_y     = float(d.get("pos_y", 0.1))
spatial.height_px = int(d.get("height_px", 120))
# AFTER
spatial.pos_x     = float(d["x"])          # KeyError if absent — do NOT default
spatial.pos_y     = float(d["y"])
spatial.height_px = int(d["height"])
spatial.on_window = bool(d.get("on_window", False))
spatial.edge      = d.get("edge", "")
```
**And `:105-106`** — `except Exception: pass` → log WARNING + flag `degraded=True`.

## WO-101 · row 26 MEANING — `memory/journal_router.py:121`
```python
# BEFORE
profile = evaluate(raw, response, action, plan=plan, state=state)
# AFTER
profile = evaluate(raw, response, action, plan=plan, state=state, outcome=outcome)
```
Same at `faculties/significance/significance_faculty.py:144`. **Two keyword arguments.**

## WO-096B · row 20 LEARN — `server.py:2675` and `:2715`
```python
# BEFORE
lkey=_sit_lkey, episode_ref="", verified=True,
        contradicting=False, session_id="sit",
# AFTER
lkey=_sit_lkey, episode_ref=_trace_id, verified=True,
        contradicting=False, session_id=_session_id,
```
Gate filters empty strings (`lesson_store.py:296-303`) against `_PROMOTE_EPISODES = 3` ⇒ 0 forever.

## WO-109 · row 7 REMEMBER — `memory/vault_layer.py:355-364`
Move the `reinforce()` loop out of `recall_context()` and **into `lookup()`**, so every retrieval path
reinforces and no future caller can miss it. *(Swapping the 3 call sites also works but leaves the trap.)*

## WO-114 · row 18 INTEND — `runtime/spine/plan.py:26`
Add `intent_source: str = "david"`. Set `"self"` from the `emergent_cognition` output that already runs
at `server.py:2909-2917`; `"reflex"` for body-initiated.

## WO-118 · row 14 ROUTE — `desktop/spatial_state.py` (beside `:129`) + `world/live_world_state.py` (beside `:325`)
Read `last_move{goal,route,legs,arrived,fell,outcome,issued_by,cost_secs,cost_dist,retries}` — live in the
file since 19:30 — and feed `self/route_memory.py`, which already computes success rates and has zero
importers.

## WO-106 · rows 4·6·16 THE SEAM — `runtime/spine/spine.py:204`
```python
exec_out = _exec_decide_fn(_attention_in, loop_detected=False, user_input=raw)
```
The Executive must consult the assembled state — world, WM winner, embodiment, capabilities, affordances.
**Test that decides it:** blank `plan.world` — **the decision must change or fail.** Identical behaviour
with the state present and absent = the seam is not open.

---

# DISPATCH
Every WO above has a card in `blender/agent_bus/<seat>/QUEUE/`. **The card is the dispatch; the board is
the tracker; this document is the detail.** Nothing is parked. Nothing waits on David.
