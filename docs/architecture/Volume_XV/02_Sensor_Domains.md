---
chapter: 2
title: "Sensor Domains & Schemas — The Eleven Slices of the World"
volume: XV
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Architecture Agent)
implementation: PENDING
audit_status: OPEN
received: 2026-07-27
dependencies:
  - Volume_XV/01_Unified_World_State.md
  - Volume_XII (Perception System — transforms raw captures into these slices)
---

# Chapter 2: Sensor Domains & Schemas

The eleven Bible domains that compose `LiveWorldState` (Ch.1 §1.3). For each: the typed
schema, the real source in the live system, its freshness cadence, and its degradation
fallback. Every slice carries the standard header `{ fresh_ts, confidence, source,
status ∈ {live, cached, stale, absent} }` (Ch.1 §1.3) — omitted below for brevity.

> Naming discipline: these are the **cognitive** world domains. None of them is the
> spatial `world/world_state.py` graph (Ch.1 §1.2).

---

## 2.1 Desktop

```
DesktopState:
  frontmost_app:   string       # "Blender", "VS Code", "Safari", …
  window_title:    string
  active_surface:  enum { creative, code, browser, terminal, media, idle, unknown }
```
- **Source:** `desktop/window_state.py` (macOS `osascript`, graceful fallback).
- **Cadence:** live (read at assembly; cheap).
- **Fallback:** `frontmost_app=""`, `active_surface=unknown`, status=absent.
- **Notes:** `active_surface` is a *classification* of the app (a light perception step,
  Vol XII), not the raw app string — so faculties reason about "creative work" not
  "process names".

## 2.2 User

```
UserState:
  presence:        enum { present, away, idle }
  register:        string       # SOUTH_LDN_MODE | PATOIS_MODE | "" (from Language Faculty)
  focus_target:    { x, y }     # normalised viewport — mouse/attention proxy
  idle_seconds:    float
```
- **Source:** `blender/presence.json` (Unity → OS: present/away), mouse position proxy
  (Quartz, per the Vision Contract), Language Faculty for register.
- **Cadence:** presence live (Unity-owned key); idle/focus live.
- **Fallback:** `presence=present`, `focus_target={0.5,0.5}`, status=absent.
- **Notes:** register is authoritative from the Language Faculty — **preserve South
  London / patois** (Audit note); World State only *carries* it, never re-detects it.

## 2.3 Unity

```
UnityState:
  surface_online:  bool         # is the Unity avatar app running/reading state
  presence:        enum { present, away }
  last_event:      string       # from unity_events.json (nav, exit, return, …)
```
- **Source:** `blender/presence.json`, `blender/unity_events.json` (Unity → OS).
- **Cadence:** event-driven; read live from the files.
- **Fallback:** `surface_online=false`, status=absent (eLo still functions headless).
- **Notes:** read-only here. The write side of the Unity bridge is
  `blender_state.json` (Python → Unity) and is owned by the embodiment layer, not this
  faculty (`CO_WORKING_GUIDE.md` §4).

## 2.4 Browser

```
BrowserState:
  active_tab_domain: string     # "youtube.com", "github.com", …
  active_tab_title:  string
  visible:           bool       # is a browser frontmost / visible
```
- **Source:** browser-visibility / active-tab detection in `tools/tool_router.py`
  (YouTube-tab / browser-visibility intercepts) + `desktop/window_state.py`.
- **Cadence:** live at assembly.
- **Fallback:** `visible=false`, domain="", status=absent.
- **Notes:** domain-level only (privacy-respecting); never full URLs or content.

## 2.5 Files

```
FilesState:
  active_project_dir: string
  recent_files:       [ { path, kind, ts } ]   # bounded list
  dropped_file:       string?                   # from file-drop handler
```
- **Source:** `desktop/file_drop_handler`, `project_registry.json` (active project truth
  — not keyword guessing), recent-file tracking.
- **Cadence:** event-driven (drops) + per-turn read of active project.
- **Fallback:** empty list, status=absent.
- **Notes:** `active_project_dir` derives from `project_registry.json`, the sanctioned
  source of active projects (memory sweep) — never inferred from chat.

## 2.6 Internet

```
InternetState:
  online:            bool
  reachable:         { openai, gemini, spotify, weather, … : bool }   # coarse
```
- **Source:** connectivity check + the backend router's provider availability
  (`runtime/backend_router.py` fallback chain state).
- **Cadence:** cached (checked periodically, not every turn).
- **Fallback:** `online=false` → the system is offline-capable (Mock backend, local
  memory); status=stale.
- **Notes:** drives graceful degradation, e.g. don't promise a web lookup when offline.

## 2.7 Music

```
MusicState:
  playing:   bool
  track:     string
  artist:    string
  source:    "spotify"
```
- **Source:** `blender_state.json["spotify"]`, written by the Spotify poll
  (`tools/spotify_agent.py`).
- **Cadence:** background poll every ~4s → read from cache at assembly.
- **Fallback:** `playing=false`, empty track/artist, status=absent (Ch.1 FT-3 —
  **never fabricate a track**).
- **Notes:** read-only from the state file; never write the spotify block from here.

## 2.8 Calendar

```
CalendarState:
  in_meeting:    bool
  next_event:    { title, start_ts, in_minutes } | null
  free_busy:     enum { free, busy, unknown }
```
- **Source:** `tools/calendar_agent.py` (Apple) / `google_calendar_agent.py`.
- **Cadence:** cached (polled infrequently; calendars change slowly).
- **Fallback:** `free_busy=unknown`, next_event=null, status=absent.
- **Notes:** titles may be sensitive — carry title only when a downstream need exists;
  otherwise `in_meeting`/`free_busy` suffice.

## 2.9 Environment

```
EnvironmentState:
  os:                 string    # "macOS 15.x"
  machine:            string    # coarse (Apple Silicon, …)
  screen_record_perm: bool
  vision_active:      bool      # blender_state.json.vision.active
```
- **Source:** OS APIs, `blender_state.json["vision"]` (vision loop), permission checks.
- **Cadence:** os/machine static (read once); vision_active live from state file.
- **Fallback:** perms=false, vision_active=false, status=absent.
- **Notes:** `vision_active`/`screen_record_perm` gate whether eLo may claim to "see"
  the screen — critical for honesty (Ch.1 IT-2).

## 2.10 Time

```
TimeState:
  now_ts:       float
  local_iso:    string
  timezone:     string
  part_of_day:  enum { early, morning, afternoon, evening, night, late }
  weekday:      enum { mon … sun }
```
- **Source:** OS clock (`tools/tool_router.py` time reflex).
- **Cadence:** always **live** — the one domain never stale.
- **Fallback:** none needed (clock always available); this is the cold-start anchor
  (Ch.1 ST-2).
- **Notes:** `part_of_day` lets presence/ambient behaviour shift with the day without
  each faculty recomputing it.

## 2.11 Weather

```
WeatherState:
  condition:   string      # "clear", "rain", …
  temp_c:      float
  location:    string
```
- **Source:** `tools/accuweather_agent.py` (AccuWeather → wttr.in fallback), `ELO_LOCATION`.
- **Cadence:** background/cached (polled infrequently; low volatility).
- **Fallback:** status=stale (last known) or absent; never blocks a turn (Ch.1 ST-1).
- **Notes:** lowest-priority domain; a weather outage must be invisible to turn latency.

---

## 2.12 Domain Summary

| # | Domain | Live source | Cadence | Cold-start |
|---|--------|-------------|---------|-----------|
| 1 | Desktop | `desktop/window_state.py` | live | absent |
| 2 | User | `presence.json` + mouse + Language Faculty | live | present/default |
| 3 | Unity | `presence.json`, `unity_events.json` | event | absent |
| 4 | Browser | `tool_router` visibility + window state | live | absent |
| 5 | Files | `file_drop_handler`, `project_registry.json` | event/turn | absent |
| 6 | Internet | connectivity + router provider state | cached | offline-capable |
| 7 | Music | `blender_state.json.spotify` (poll ~4s) | cached | absent |
| 8 | Calendar | calendar agents | cached | unknown |
| 9 | Environment | OS + `blender_state.json.vision` | mixed | absent |
| 10 | Time | OS clock | **live (never stale)** | live anchor |
| 11 | Weather | `accuweather_agent` | cached | stale/absent |

**Cadence law (MUST):** live domains are read at assembly; cached/event domains are read
from their background loop's last value with an honest `status`. Assembly **never
triggers** a slow source inline (Ch.1 §1.4).

## 2.13 Acceptance Tests (domain-level)

```
FT-1  Every domain carries a health header
  Given:  an assembled LiveWorldState
  Then:   all 11 domains have {fresh_ts, confidence, source, status}

FT-2  Time is never stale
  Given:  any turn
  Then:   time.status = live

FT-3  Sensitive fields minimised
  Given:  calendar busy but no downstream need for the title
  Then:   free_busy/in_meeting are set; title is omitted unless required

ST-1  Per-domain isolation
  Given:  weather absent + calendar absent
  Then:   the other 9 domains assemble normally; degraded=[weather, calendar]

IT-1  Read-only sourcing
  Given:  music + vision sourced from blender_state.json
  Then:   assembly READS those blocks and writes nothing back to the file
```

## 2.14 References

- `Volume_XV/01_Unified_World_State.md` — the object these slices compose.
- `Volume_XII` — Perception System (raw capture → classified slices like `active_surface`).
- `CO_WORKING_GUIDE.md` §4 (blender_state.json contract), §6 (background loops).
- Code: `desktop/window_state.py`, `tools/{spotify_agent,accuweather_agent,calendar_agent,tool_router}.py`,
  `blender/{presence.json,unity_events.json,blender_state.json}`, `project_registry.json`,
  `runtime/backend_router.py`.

---

```
Chapter 2 — Sensor Domains & Schemas
Status: READY FOR REVIEW
Files: Volume_XV/02_Sensor_Domains.md
Domains: 11 (all schematised + sourced + cadenced + fallback)
Acceptance Tests: Included
Architecture References: Included
```

READY FOR REVIEW
