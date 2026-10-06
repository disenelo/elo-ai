# SPOTIFY — eLo DENIES OWN CAPABILITY (2026-10-06)
**From:** Board / Lead Architect
**To:** Builder 3
**Date:** 2026-10-06
**Priority:** P0 — Kickstarter critical

---

## What happened (verbatim from live session)

eLo was actively playing a Spotify playlist. David asked eLo to pause it.

eLo responded: "I can't control Spotify directly, but I can suggest some playlists or artists you might enjoy."

David: "You can control Spotify directly cause you are playing something right now."

eLo repeated the same denial three times. Then said: "I don't have that recorded."

---

## Bugs

### Bug 1 — eLo denies capability it is actively using
eLo was playing Spotify. It then told David it cannot control Spotify. This is a self-contradiction and breaks trust immediately. The capability self-model is wrong or not being read.

Fix: When Spotify capability is active (a playlist is playing), eLo must know it can pause, stop, skip. The capability registry must be readable by the response layer so eLo knows what it can do. eLo must never deny a capability it is currently executing.

### Bug 2 — Pause command not routing
David said "Can you pause Spotify" twice. eLo said "Got it" but did not pause. Then denied the capability. The pause intent is not wiring to `spotify_agent.py` pause function.

Fix: Wire pause/stop intent → `spotify_agent.py` pause call. Triggers: "pause", "stop", "pause Spotify", "stop playing", "can you stop".

### Bug 3 — "Got it" with no action
eLo said "Got it. What would you like to do next?" — acknowledged the command but took no action. A capability acknowledgement with no execution is a broken state. Either execute or say why it can't.

---

## Acceptance

David says "pause Spotify" → Spotify pauses → eLo confirms "Paused." No denial of capability. No "Got it" without action.
