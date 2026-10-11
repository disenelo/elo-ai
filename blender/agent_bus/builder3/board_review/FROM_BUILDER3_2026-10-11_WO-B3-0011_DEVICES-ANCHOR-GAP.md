# TO BOARD — WO-B3-0011 devices anchor gap closed
**Date:** 2026-10-11
**From:** Builder 3
**To:** Board
**Card:** WO-B3-0011 Company Control (follow-on fix for the "eLo denies live capability" anti-pattern applied to Devices)
**Commit:** 5bcd882

---

## Gap found

`tools/capability_status.capabilities_block()` carried **Devices** as a flat "Also:" name — no live state. `tools/device_control.match()` correctly returned `None` for ability questions ("can you control the lights?") because they are not run instructions. With no capability fact in the anchor and no match, the LLM guessed — same anti-pattern the IS-ELO verdicts (2026-10-06) flagged for Spotify ("denied capability while actively playing").

Live-shaped probes:

| Query | Before | After |
|---|---|---|
| "can you control the lights?" | LLM guess (often "I can't") | eLo answers directly, names the route + allow-list, flags offline Echo |
| "do you control the lights?" | LLM guess | Same |
| "what lights can you control?" | LLM guess | Same |
| "turn on the lights" | handled by match() → run() | unchanged |
| anchor Devices line | flat name | "Devices — via Alexa over the Mac speakers (lights on, lights out, …)" |
| Devices with Echo offline | ACTIVE flat | INACTIVE with exact reason "Echo isn't connected over Bluetooth (speak-to-Alexa route)" |

---

## What built (B3-owned files only)

**`tools/capability_status.py`**
- `devices_status()` live probe: `{route, controllable, echo_connected, can}`
- `_b3_live()` adds `"devices"` entry; display name overridden to `"Devices"` (stale "Devices (Shortcuts)" from registry no longer accurate — speak-to-Alexa is the default route per David 2026-10-10)
- `"devices"` added to `_LIVE_FIRST` so the anchor shows live state, not just the name
- `capabilities_block()` renders " — via Alexa over the Mac speakers" / " — via macOS Shortcuts" after the Devices name

**`tools/device_control.py`**
- `capability_answer(text)`: mirrors `spotify_play.capability_answer()`. Returns a factual answer naming the route and allow-list; appends an "Echo isn't on Bluetooth" warning when the speak route can't reach the Echo. Rotates three line variants (same shape as spotify).
- `awareness_context(text)`: mirrors `spotify_play.awareness_context()`. Returns `[CAPABILITY_RESULT: Devices — …]` for mentions (lights, lamp, Alexa, scenes) when `match()` isn't going to run anything — carries the fact through Builder 1's missing-fact exception without LLM paraphrase.

No shared files touched. No router/spine changes. No new config.

---

## Tests

`tests/test_b3_capability_status.py` — 19 pass (+5 new):
- `test_devices_live_entry_marks_speak_route_inactive_without_echo`
- `test_devices_live_entry_marks_speak_route_active_with_echo`
- `test_devices_live_entry_shortcut_route_is_active_when_anything_listed`
- `test_devices_appear_in_live_first_block`
- `test_devices_status_shape`

`tests/test_b3_device_control.py` — 34 pass (+9 new):
- 5 × `test_ability_question_gets_a_direct_answer[…]`
- `test_ability_answer_names_shortcut_route_when_set`
- `test_ability_answer_warns_when_echo_offline_in_speak_route`
- `test_ability_answer_omits_echo_warning_when_connected`
- 3 × `test_non_ability_questions_return_none[…]`
- `test_awareness_context_fires_on_mention_but_not_on_direct_run`
- `test_awareness_context_carries_allow_list`

Full B3 suite: **231/231 pass** on my Mac (local run, sandbox-independent — no server or sockets touched).

---

## File lock

Not required: both edited files are Builder 3-owned and not on CLAUDE.md's shared-files list (`server.py`, `spine.py`, `backend_router.py`, `prompt_builder.py`, `identity_kernel.py`, `memory_faculty.py`, `vault_layer.py`, `graph_loader.py`, `ambient_engine.py`).

---

## Live turn needed (David) — proves the fix

1. Say to eLo: *"Can you control the lights?"* → eLo should name the route and the four allow-listed commands, not deny.
2. Say to eLo: *"What lights can you control?"* → same answer, different lead-in (3-line rotation).
3. With Echo offline on Bluetooth: *"Can you turn on the lights?"* → eLo says what he can, and flags Echo isn't reachable so Alexa won't hear.
4. With Echo on Bluetooth: *"Can you control the lights?"* → no Echo warning; and ask to see the anchor (`capabilities_block()`) via DISENELO Presence brain view → "Devices" appears in the "You CAN:" line, not "Also:".

If any of 1–3 return an LLM denial, Builder 1 should check that `capabilities_block()` output and `[CAPABILITY_RESULT:]` tags are reaching the anchor layer. The data is there now; the pipe is theirs.

---

## Not in scope for this fix

- Richer contextual output decision (foreground app, time-of-day) — Board scoping, not built.
- Expanding the allow-list beyond the four shortcuts David already has — needs David to specify what else.
- Smart-home via HomeKit / direct Hue — parked per David 2026-10-10 ("I don't want more APIs for no reason").

---

*Builder 3 · 2026-10-11*
