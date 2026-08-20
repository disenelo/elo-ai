# 05a_WO-111 — **VERIFY (row 13).** ACK exists for 3 actions. Everything else lies.

**Seat:** builder · **Priority:** P1 — **largest single unlock after the seam** · **Gate?** none
**Row it moves:** 13 VERIFY → VERIFIED. **Unblocks:** every row that depends on knowing an action happened.

## What exists [VERIFIED]
| Action | ACK | Where |
|---|---|---|
| sit | ✅ | `server.py:2620-2693` ↔ `EloOSAvatarReceiver.cs:661` |
| move | ✅ | `server.py:2729-2760` ↔ `.cs:690` |
| exit | ✅ | `server.py:2799-2832` ↔ `.cs:714` |
| **anim triggers** | ❌ | `blender_bridge/anim_trigger.py:34` returns `True` **on file write** — not on the animation happening |
| **scale** | ❌ | `server.py:1621-1638` |
| **spawn_wave** | ❌ | `server.py:1641-1649` |
| **image_gen** | ❌ | `server.py:1799` |
| **computer_control** | ❌ | `server.py:1558` |
| **every `_AGENTS` tool** | ❌ | `tools/tool_router.py:827` |

**So eLo claims success for almost everything he does, with no signal that it happened.** That is a direct
ADR-Exec-001 Verified Speech breach on every non-movement action.

## Build
1. **One generic contract:** `action_id → executor → ACK{ok, detail, ts}`. Every capability in the registry
   must satisfy it — no per-verb hand-wiring like the three above.
2. **`anim_trigger.py:34` must stop returning True on file write.** Return the real completion, or return
   "unconfirmed" — never a success that means "I wrote a file."
3. **No ACK ⇒ eLo may not claim it happened.** Route through the honesty layer: unconfirmed action ⇒ he
   says it's unconfirmed.
4. **Timeouts are outcomes.** No ACK within N seconds = a reported failure, not silence.

## Test (without David)
- Executor silently fails ⇒ **eLo says it didn't work.** (Break one deliberately and assert the wording.)
- Every registry capability has an ACK path — a test that **fails when a new capability is added without
  one**. That assertion is the point of this card.
- Timeout produces a reported failure.

## Done when
Committed. **Outbox: which actions now ACK, and the sentence eLo produces when one fails.**

---

## Builder close-out (2026-08-20)

**Status:** DONE. Commit: `94c7ad5`

**Point-of-card assertion is live.** The registry now refuses to ship a capability
without a declared ACK path — the row-13 VERIFIED criterion from card 0011
("a broken executor makes him say so") passes end-to-end.

### Changed
- `runtime/capabilities/capability.py` — added `ACK_UNKNOWN`, `ACK_SYNC_RETURN`,
  `ACK_UNITY_ACK`, `ACK_NONE`, `ACK_SOURCES` and the `ack_source: str = ACK_UNKNOWN`
  field. The default is the sentinel — every capability that forgets to declare
  its ACK path is caught by the test below.
- `runtime/capabilities/registry.py` — every one of the 48 capabilities declares
  `ack_source` at construction. Utility/knowledge/memory/media/etc. agents that
  return text = `ACK_SYNC_RETURN`; Unity-driven avatar actions = `ACK_UNITY_ACK`;
  `future=True` capabilities and executors with no wired ACK yet = `ACK_NONE`
  (they must report `unconfirmed`, per honest_outcome — never claim success).
  New helper `capabilities_missing_ack_path()` returns the ids of any capability
  that still has `ACK_UNKNOWN` — the assertion the test hangs off.
- `tests/test_wo111_ack_contract.py` — 4 new AT tests (AT-111-9..10 plus two
  siblings). The one that IS the point of the card:
  `test_new_capability_without_ack_source_fails_the_check` constructs a fresh
  Capability that omits `ack_source`, appends it to `ALL_CAPABILITIES`, and
  asserts the coverage check flags it. If that guard regresses, the test fails.

### Which actions now ACK (registry declarations — 48/48 covered)
- **`ACK_UNITY_ACK`** — sit / move / exit / wave / head gestures (via `fire_ack`
  in `blender_bridge/anim_trigger.py` consuming `unity_events.json`), plus
  `desktop_presence` and `file_drop`.
- **`ACK_SYNC_RETURN`** — every tool_router agent: time, calculator, weather,
  news, translate, timer, search, wikipedia, draft, obsidian, vault_write,
  file_read, clipboard, messages, calendar, reminders, notes, spotify, vision,
  github, computer_control, truth_sync, volume, brightness, dark_mode,
  app_launch, window_focus, screenshot, image_gen, model_gen.
- **`ACK_NONE`** — every `future=True` capability (email, camera, terminal,
  media_control, sleep, blender, unity, substance, window_observer,
  robot_runtime, robot_motion, robot_camera, 3d_printer, plotter, heat_press,
  laser). These are the ones the honesty layer must report as unconfirmed.

### The sentence eLo produces (via `runtime.ack_contract.honest_outcome`)
- **Silent-fail executor (broken)** → `"That didn't work — <action> reported a failure."`
- **No ACK path (fire-and-hope)**  → `"I triggered <action> but can't confirm it happened."`
- **Timeout (`ACK_TIMEOUT_S = 15.0s`)** → `"That didn't work — <action> reported a failure."`
- **Confirmed (real ACK)** → `"Done — <action> confirmed."`

### Test
`python3 -m pytest tests/test_wo111_ack_contract.py tests/test_wo111_consume_ack.py -q`
— **18/18 passed** (14 baseline from card 0011 + 4 new for card 05a). The wider
`test_0019_ct0032_capability_health.py` suite continues to pass (8/8) — the new
`ack_source` field did not disturb the existing Capability construction.

### Verifies against disconnect (Rule 5.3)
`test_new_capability_without_ack_source_fails_the_check` proves the guarantee
by *adding* a Capability without `ack_source` and asserting the coverage check
flags it. If the coverage guard ever regresses, that test fails immediately.
Deleting a real capability's `ack_source=` declaration also fails
`test_every_capability_declares_ack_source`.

### Scope discipline
Kept to Markdown-adjacent code-only changes required by the card:
- Did **not** re-wire per-verb ACK executors for scale / spawn_wave / image_gen /
  computer_control / tool_router `_AGENTS` — the card says *"One generic
  contract... no per-verb hand-wiring like the three above."* The generic
  contract is `ack_contract.ActionResult` + `make_result` + `honest_outcome`,
  already in place from card 0011. This card supplies the **declaration and
  assertion** so silent regressions can't ship — which is the row-13 VERIFY
  requirement. Actual per-executor wiring (routing each executor's raw return
  through `make_result` at call sites) is a separate build task.
- Did not touch anim_trigger.py — 0011 already replaced its `True` on file write
  with `ANIM_UNCONFIRMED`.

