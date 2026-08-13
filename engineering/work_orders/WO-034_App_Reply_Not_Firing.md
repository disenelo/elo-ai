---
id: WO-034
title: "App doesn't fire the reply (thinking/reply stage) — CLI works, app doesn't. OWNERSHIP SPLIT to stop eLo-OS vs UI competing."
owner_seat: SPLIT — SEAT-ENG-001 (Builder / eLo OS) AND SEAT-ENG-004 (UI/Avatar, Unity)
priority: P0
reason: "David 2026-08-03: main.py (CLI) thinks + replies fine, but the desktop APP doesn't fire from the thinking/reply stage. Reported to BOTH eLo OS and UI — they are COMPETING with no clear owner. Coordinator sets the contract line so each fixes only their half."
review_required: L3 (David talks to the app + it replies)
status: OWNERSHIP DEFINED — do NOT both edit the same path
created: 2026-08-03
---

# WO-034 — app reply not firing · ownership split

## The one fact that scopes it
`main.py` (CLI) thinks and replies correctly — same brain, same backend, same routing. So the reply
GENERATION works. The break is only in the **desktop app path**: app → `server.py POST /chat` → reply →
Unity. There is exactly ONE contract line between the two lanes: **the `/chat` HTTP response** (and the
`blender_state.json` it writes).

## THE CONTRACT (the boundary — neither agent crosses it)
- **eLo OS / Builder OWNS:** `server.py POST /chat` must RETURN a valid `{"response":"<real text>", "mode":..., "backend":...}` AND fire its side (`_voice_speak`, `_avatar_route` → `blender_state.json`). It is DONE when a request to `/chat` returns a real reply (not empty, not a hang, not silent mock).
- **UI / Unity OWNS:** CONSUMING that — reading the `/chat` response and/or `blender_state.json` and displaying/animating/speaking the reply in the app.

## ARBITER TEST (settles who owns the fix — run once)
`curl -s -X POST http://localhost:5050/chat -H 'Content-Type: application/json' -d '{"text":"hello"}'`
- Returns a real `{"response":"..."}` → **eLo OS is DONE; the bug is UI's** (app isn't consuming/displaying the reply Unity receives).
- Hangs / empty / error / `backend:"mock"` → **the bug is eLo OS's** (server not producing/returning the reply in the desktop context — check the `/chat` handler + the backend call, distinct from the CLI path).

## Rules to STOP the competing
1. Run the arbiter test FIRST. Its result assigns the owner. The other agent stands down until the owner ships.
2. eLo OS edits ONLY `server.py` `/chat` + reply-fire path. UI edits ONLY the Unity consume/display side. No overlapping edits to the same file.
3. Whoever owns it: py_compile / compile clean, and reproduce a working reply in the app before handback.

## Acceptance
1. David talks to the desktop app → eLo replies (spoken + shown), same as the CLI.
2. Arbiter test recorded in the handback (what `/chat` returned), so the fix is grounded, not guessed.
