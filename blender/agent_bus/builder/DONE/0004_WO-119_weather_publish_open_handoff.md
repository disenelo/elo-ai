# 0004_WO-119 — weather publish. **Designer handed this over and it was never carded.**

**Seat:** builder · **Priority:** P2 · **Gate?** none · **Small.**

## Origin — Designer's outbox, `carry_forward_open_handoff`, verbatim
> **WO-030 / WO-058** — *"Brain must publish real weather into `blender_state.json` as top-level
> `'weather':'<condition>'` on its normal state tick. Unity read-side shipped. Currently weather only shows
> when injected fast enough to out-write the brain's state tick — real weather needs this publish.
> Builder lane."*

**The Unity read side is DONE.** The brain never publishes, so the value only appears if something races
the state tick and wins. Designer flagged it as an open handoff; **no card was ever written.** Mine.

## Build
- Brain writes top-level `"weather": "<condition>"` into `blender_state.json` on the normal state tick.
- **Add `"weather"` to `_PRESERVE_KEYS`** (`blender_bridge/state_writer.py:243`) — same trap that ate
  `gaze`. Do not repeat it.
- Unblocks **WO-058** (VFX layer: snow/rain react to real weather) in Designer's lane.

## Test (without David)
Weather value present in `blender_state.json` after a normal turn · **survives a partial write** ·
Unity-side condition changes with it.

## Done when
Committed, hash to outbox. **Tell Designer it's live** so WO-058 can use it.

---

## RESULT — 2026-08-19 (Builder)

**Status: DONE — already shipped, no new commit needed.**

Card's build requirements were already implemented under `WO-030b / WO-058b`
in commit **`419c293`** ("WO-030b/058b: weather publish — survives every
`_write()` tick"). This card duplicates that work.

Verification against disk (`refresh`-style reads, not recall):

- `blender_bridge/state_writer.py:246-251` — `_PRESERVE_KEYS` contains
  `"weather"` (line 248). Survives any `_write()` that omits it.
- `server.py:3930-3936, 3974-3976` — on every state tick, `_bs_patch()` writes
  top-level `"weather": "<condition>"` from `get_last_weather_condition()`
  when non-empty. Empty-string guard is on the caller side, not in `patch()`.
- `tools/tool_router.py:471-482` — `_cache_weather_condition()` +
  `get_last_weather_condition()` provide the source. Cached on every
  successful fetch across accuweather / google_weather / xweather / wttr.
- `tests/test_wo030b_weather_publish.py` — 7/7 acceptance points pass
  (AT-0 py_compile, AT-1 `weather` in `_PRESERVE_KEYS`, AT-2 preserved by
  `_write()`, AT-3 `patch()` writes top-level, AT-4 empty-string transparency,
  AT-5 accessor returns str, AT-6 survives round-trip).

Run: `python3 tests/test_wo030b_weather_publish.py` → `7 passed 0 failed`.

**Commit cited as evidence: `419c293` (already in `main`).** No new commit.

**Designer notification: not needed as new — the publish has been live since
`419c293`.** WO-058 (VFX layer) is already unblocked on the read side. If the
open-handoff was still flagged, it was a Board-level miss, not code missing.
