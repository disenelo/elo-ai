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
