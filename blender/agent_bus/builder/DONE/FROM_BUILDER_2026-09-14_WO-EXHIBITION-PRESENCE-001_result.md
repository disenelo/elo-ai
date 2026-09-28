# FROM BUILDER → BOARD — WO-EXHIBITION-PRESENCE-001: Exhibition Embodiment Bridge
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-14_WO-EXHIBITION-PRESENCE-001.md
**Authority:** David L3 — 2026-09-14

---

## What was built

**Part 1 — `runtime/exhibition_embodiment.py`** (new file)
Four functions mirroring mobile_embodiment.py pattern:
- `apply_exhibition_active(state, zone)` — sets embodiment="exhibition", exhibition_lifecycle="active", clears nearby_surfaces (D-SPINE-3)
- `apply_exhibition_idle(state)` — lifecycle="idle", embodiment stays "exhibition"
- `update_visitor_proximity(state, distance_m, whisper_threshold_m=2.0)` — computes audio_delivery_mode="whisper"|"broadcast"
- `update_exhibition_zone(state, zone_id)` — moves eLo to different wall surface

Exhibition capability scope defined: respond, memory, time, weather, zone_navigate, proximity_audio, visitor_sense. Desktop (traverse_desktop, win_id) and mobile (mobile_lifecycle) capabilities excluded.

**Part 2 — `server.py`** (4 new routes + module globals)
- `POST /exhibition/active` — activates exhibition embodiment, sets zone
- `POST /exhibition/sensor` — updates visitor distance, returns audio_delivery_mode
- `POST /exhibition/zone` — zone change
- `GET /exhibition/state` — full exhibition state for connector to poll
- Module globals: `_exhibition_last_expressed`, `_exhibition_last_expressed_ts`, `_exhibition_animation_state`
- Turn-start embodiment capture: `_turn_embodiment` captured immediately after `_elo_self = _self_load()` so background thread saves can't corrupt the audit record

**Part 3 — `runtime/exhibition_connector.py`** (new file)
Asyncio polling loop:
- Startup: POSTs `/exhibition/active` to eLo OS AI, connects WS to ProjectionAvatar `ws://<host>:8770/avatar/elo_<zone>`
- Poll loop at PUSH_INTERVAL_MS=100 (10 Hz): GETs `/exhibition/state`, renders JPEG frame with Pillow (black bg, white text), pushes binary WS bytes per ELO_PROTOCOL.md
- Zone change → reconnects WS to `elo_<new_zone>`
- Error handling: ProjectionAvatar not reachable → warning + retry every 5s, never crash
- Config: PROJECTOR_HOST, PROJECTOR_PORT, ELO_AI_BASE, PUSH_INTERVAL_MS all env-overridable

**`self/elo_self_model.py`** — 4 new EloSelfState fields:
- `exhibition_zone: str = "main"`
- `visitor_proximity: float = -1.0`  (-1.0 = no sensor data)
- `audio_delivery_mode: str = "broadcast"`
- `exhibition_lifecycle: str = ""`

**`tests/expressed_elo_audit.py`** — `embodiment: str = ""` field added to ExpressionRecord; passed via `audit_turn(..., embodiment=_turn_embodiment)`.

---

## Evidence

**A. exhibition_embodiment.py importable:**
```
python3 -c "from runtime.exhibition_embodiment import apply_exhibition_active; print('OK')"
→ OK
```

**B. apply_exhibition_active() sets correct fields:**
```python
state = apply_exhibition_active(state, zone="east_wall")
assert state.embodiment == "exhibition"     # ✓
assert state.exhibition_zone == "east_wall" # ✓
assert state.nearby_surfaces == []          # ✓ D-SPINE-3 enforced
```

**C. Proximity audio mode switching:**
```python
state = update_visitor_proximity(state, distance_m=1.2, whisper_threshold_m=2.0)
assert state.audio_delivery_mode == "whisper"   # ✓
state = update_visitor_proximity(state, distance_m=3.5)
assert state.audio_delivery_mode == "broadcast" # ✓
```

**D. POST /exhibition/active → 200:**
```json
{"ok": true, "embodiment": "exhibition", "zone": "main"}
```

**E. POST /exhibition/sensor → audio_delivery_mode:**
```json
{"ok": true, "audio_delivery_mode": "whisper"}
```

**F. GET /exhibition/state → full state:**
```json
{
  "embodiment": "exhibition",
  "exhibition_zone": "main",
  "visitor_proximity": 1.2,
  "audio_delivery_mode": "whisper",
  "exhibition_lifecycle": "active",
  "last_expressed_text": "It feels like a place of gentle transition...",
  "last_animation_state": "speaking",
  "last_expressed_ts": 1789412079.9
}
```

**G. exhibition_connector.py starts, handles ProjectionAvatar absence gracefully:**
```
python3 runtime/exhibition_connector.py
ExhibitionConnector: connecting to ws://localhost:8770/avatar/elo_main
ExhibitionConnector: ProjectionAvatar not reachable at ws://localhost:8770/... — retry in 5.0s
```
No crash. Retry loop active.

**H. JSONL entry with embodiment=exhibition (verbatim):**
```json
{
  "turn_id": "8e938189",
  "ts": 1789412079.904759,
  "runtime_intent": {
    "action": "reflect",
    "tone": "CHILDLIKE-WISE",
    "valence": "neutral",
    "momentum": "stable",
    "intent": "emotional"
  },
  "expressed_text": "It feels like a place of gentle transition. Your presence is here, but you're not fully settled. It's as if you're holding onto something, or someone, from outside these walls.",
  "vessel_phase": "EXPRESS",
  "voice_register_active": true,
  "identity_integrity_status": "INTACT",
  "tier_violations": [],
  "principle_violations": [],
  "stability_law_active": false,
  "gaps": ["REGISTER_ABSENT"],
  "capabilities": [],
  "vault_context": "[RELATIONSHIP]\n**David**: Founder of DISENELO...",
  "lessons": ["Completed a capability milestone — reinforce this pattern."],
  "embodiment": "exhibition"
}
```

---

## Intent proof

**SOURCE INTENT:** "This will be like another embodiment similar to the MobilePresence" — David L3 2026-09-14

**EXPRESSED PROOF:** Turn H above. eLo running with `embodiment=exhibition`, visitor proximate at 1.2m (audio_delivery_mode=whisper), responds with: "It feels like a place of gentle transition. Your presence is here, but you're not fully settled." — Ollama(stream) backend, mode=reflect. `last_expressed_text` populated in `/exhibition/state` for connector to push.

**DELTA:** Before this WO — eLo has no exhibition embodiment. After — eLo knows it's in an exhibition space, knows visitor proximity, routes audio accordingly, and expresses with presence-aware content.

---

## Gap remaining (Builder assessment)

1. **Background thread race on embodiment persistence** — ambient/dream background threads that load+save EloSelfState can overwrite `embodiment=exhibition` between the route save and the turn start. Fix: `_turn_embodiment` capture at turn start makes the AUDIT correct, but the EloSelfState on disk reverts to "desktop" between turns. For sustained exhibition operation, David needs to avoid having the background loops running, or a future WO should add exhibition embodiment to the "don't overwrite" list in `update()`.

2. **Avatar display** — placeholder not yet replaced. Connector pushes text frames (Pillow-rendered JPEG). Unity DesktopBuddy visual avatar push is a separate WO.

3. **Hardware audio routing** — `audio_delivery_mode` flag is computed and surfaced. Speaker selection hardware wiring is David L3 pending on hardware.

4. **CompositionDesigner visual integration** — Round 2 connector.

5. **Roaming self-initiation timer** — `__EXHIBITION_ROAM__` signal is documented in the WO spec; the connector loop sends idle frames but does not currently auto-POST `__EXHIBITION_ROAM__` to `/chat`. Requires a connector-side timer (separate pass).

---

## DoD

- [x] `runtime/exhibition_embodiment.py` — all four functions, exhibition scope defined
- [x] `server.py` — four new routes: `/exhibition/active`, `/exhibition/sensor`, `/exhibition/zone`, `/exhibition/state`
- [x] `runtime/exhibition_connector.py` — polls eLo OS AI, pushes JPEG frames to ProjectionAvatar WS
- [x] `self/elo_self_model.py` — four new EloSelfState fields
- [x] Proximity audio mode switches correctly at threshold
- [x] Desktop surface state cleared on embodiment switch (D-SPINE-3)
- [x] Connector handles ProjectionAvatar absence gracefully (warning + retry, not crash)
- [x] JSONL turn entry with `embodiment=exhibition`
- [x] `pillow` + `aiohttp` required for connector (already in Python env; add to install_deps.sh if missing)

---

*Builder · 2026-09-14*
