# BUILT — WO-B3-PRE-ACK: pre_ack.py — eLo speaks before slow B3 ops
**Date:** 2026-10-11
**Builder:** Builder 1
**Commit:** 3332caf
**Source:** `blender/agent_bus/builder3/FROM_BUILDER3_2026-10-11_EXECUTION-ACK-DOCUMENTS.md`

## What was built

`runtime/pre_ack.py` — emit(capability, user_text) fires a background TTS phrase
before slow B3 tool operations. Non-blocking (< 1 ms). Never raises.

Supersedes the interim `ack_pending` blender_state.json approach (no server-side
heartbeat consumer needed — direct voice call is cleaner).

## Capabilities covered

- `document_write` — "Give me a second, I'll write that up." (+ 3 variants)
- `device_control` — "Give me a second." (+ 3 variants)
- `spotify_play` — "One second." (+ 3 variants)
- `default` / unknown — fallback bank

## AT results

| AT | Description | Result |
|---|---|---|
| AT-1 | document_write selects from correct bank | ✅ PASS |
| AT-2 | device_control uses its bank | ✅ PASS |
| AT-3 | spotify_play uses its bank | ✅ PASS |
| AT-4 | unknown capability falls back to default | ✅ PASS |
| AT-5 | bare emit() call (no args) works | ✅ PASS |
| AT-6 | emit never raises when voice fails | ✅ PASS |
| AT-7 | user_text arg accepted, doesn't change bank | ✅ PASS |
| AT-8 | consecutive emits both fire | ✅ PASS |

**8/8 PASS** (`tests/test_pre_ack.py`)

B3 notified: `blender/agent_bus/builder3/FROM_BUILDER1_2026-10-11_PRE-ACK-LANDED.md`

*Builder 1 · 2026-10-11*
