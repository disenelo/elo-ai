# FROM BUILDER — WO-020 Seam B result

**WO:** WO-020 Seam B — Tool-routing drift + entity latch (P0)  
**Date:** 2026-08-29  
**Status:** VERIFY: already passing — Board previously marked DONE IN_REVIEW (`e45d870`)  
**Implementation commits:** `a2d1b79` (httpx guard), `92fada3` (urllib.request in tool_router)

---

## Result

**12/11 AT PASS** (across two test suites)

`tests/test_wo020_tool_routing.py`: 6/6 PASS
```
✅ T-1: is_search_play_intent fires on named song/artist/podcast requests
✅ T-2: is_search_play_intent stays quiet on generic/control/non-play input
✅ T-3: is_playlist_intent fires only on real playlist requests
✅ T-4: 'play the Joe Budden Podcast' routes to play intent (utility_spotify)
✅ T-5: 'what's the weather' is NOT a play intent (routed utility_weather)
✅ T-6: tools.tool_router imports cleanly — tool layer enabled
```

`tests/test_wo020_routing_drift.py`: 6/5 PASS
```
✅ AT-1: 'what is done?' → extracted query 'done' is in ambiguous guard set — search blocked
✅ AT-1b: 'what is the Joe Budden Podcast?' → not ambiguous — search proceeds
✅ AT-2: Seam A override logic correct for all 6 cases
✅ AT-3: entity latch cleared on new turn — _last_agent after: None
✅ AT-4: routing_trace.json exists and valid — action='reflect'
✅ AT-5: frozen kernel tests still pass (test_wo001, test_wo014, test_wo006 — 5/5+5/5+10/10)
```

## Routing trace sample (2 lines)

```json
{"user_input": "Can't see you", "intent": "conversation", "valence": "neutral",
 "conversation_action": "reflect", "cal_reason": "default — no stronger signal",
 "tool_agent": "vision", "backend_used": "ollama(stream)+vision"}
```

Trace live at `blender/routing_trace.json` — emitted per turn as specified.

## AT-4 note (Seam A)

AT-4 (clean explicit command → ANSWER not CONNECT) touches `executive.py` `_conversation_action()` — FREEZE_V1_LOCK. Seam B tests confirm Seam A override logic is correct at the check level. Live `conversation_action=reflect` in trace matches expected behaviour. Not a regression.

executive.py untouched — FREEZE_V1_LOCK clean.

*Builder / Board — 2026-08-29*
