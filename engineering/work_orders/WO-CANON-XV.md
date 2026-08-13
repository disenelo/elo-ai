# WO-CANON-XV — World Model: COMPLETE + WIRE + VERIFY the LiveWorldState (it exists; it is not finished)

**Owner:** Builder (eLo OS — `world/`, `runtime/spine/`, faculty migration). **Priority:** P2 — Tier A.
**Status:** OPEN — **REWRITTEN 2026-08-13 on a corrected premise.** The previous version of this WO ordered
*"Build `world/live_world_state.py` (NEW)"*. **That file already exists and is already partly wired.** This
WO is now *complete + wire + verify*, not *build from zero*.
**Board status is misleading:** `DISPATCH_BOARD.md:1461` reads *"DONE ✅ auto-verified (14/14) → IN_REVIEW,
commit `a742cdc`"*. The object is real and the tests pass, but **no faculty consumes it**, the envelope
binding is absent, and the desktop domain never populates (see IRV below). Do not close on the board line.

**Canon refs:** Volume XV — Ch.1 `01_Unified_World_State.md` (ELO-V15-CH01), Ch.2 `02_Sensor_Domains.md`
(ELO-V15-CH02). `Volume_V/CONTRACTS.md` (envelope §2, lifecycle §3, base contract §4);
`16_spine_runtime.md` §6. **Volume XIII** (Presence & Embodied Spatial Intelligence) — Ruling D-XIII-1.

---

## IRV — what is actually on disk (verified 2026-08-13 by reading and running the code)

| Claim | Verified finding |
|---|---|
| The file exists | `world/live_world_state.py` — **379 lines**, 15,320 bytes, mtime **2026-08-10 17:10**. Header: *"Unified World State (WO-002) … Spec: docs/architecture/Volume_XV/01_Unified_World_State.md"*. |
| Volume metadata | `Volume_XV/00_Metadata.md:8` still says `implementation: PENDING`, and `01/02_*.md:9` likewise. **Metadata is stale against disk.** |
| The eleven slices | All present as frozen dataclasses: `DesktopState · UserState · UnityState · BrowserState · FilesState · InternetState · MusicState · CalendarState · EnvironmentState · TimeState · WeatherState`, plus `DomainHealth` and the frozen `LiveWorldState` with `assembled_ts · turn_id · domain_health · degraded`. |
| Assembly | `assemble_world_state(turn_id, perception) -> LiveWorldState` at L156. |
| Spine wiring | `runtime/spine/spine.py:361–368` assembles top-of-turn; `spine.py:450` passes `world_state=_world`; `spine.py:463` sets `plan.world`; `runtime/contracts.py:157` declares `CognitiveState.world_state`. **The wiring-in half is done.** |
| **Consumers** | **NONE.** A repo-wide grep for readers of `plan.world` / `CognitiveState.world_state` returns only `faculties/temporal/faculty.py` — and *nothing imports the temporal faculty either* (see WO-CANON-XXV). **Nothing in the live turn reads the world object.** The drift the volume exists to remove has not been removed. |
| **Direct sensor calls still live** | `tools/tool_router.py:1013, 1155, 1182` · `desktop/desktop_presence.py:18` · `faculties/perception/perception_faculty.py:337` all still call `desktop/window_state` directly during a turn. |
| **Envelope binding** | **Absent.** The file contains zero occurrences of `sender`, `expires`, or any envelope. Ch.1 §1.8 requires `sender = WorldStateFaculty` and a set `expires`. The object is a bare dataclass that is never published on the Faculty Bus. |
| **🔴 Desktop domain never populates** | `world/live_world_state.py:194` does `from desktop.window_state import get_active_window`. **That symbol does not exist** — `desktop/window_state.py` defines `get()` and `_classify()`, nothing else. The import raises `ImportError`, the bare `except` swallows it, and `desktop` is marked `absent` on **every** turn. Reproduced: `assemble_world_state()` returns `DesktopState(active_app='', active_window='', surface='')`, `domain_health['desktop'] = {status: 'absent', confidence: 0.0}`. Platform-independent (the import fails before any `osascript` call). **The same broken import is duplicated at `faculties/perception/perception_faculty.py:337`.** |
| `degraded[]` under-reports | Observed run: `browser · calendar · desktop · files · internet · music · weather` all `status: absent`, but `degraded == ('desktop',)` only. Ch.1 requires an unsensed domain to be added to `degraded[]`. |

**Net:** Vol XV shipped an object and a wire, not a world. The 14/14 test pass is real but does not cover
"a faculty reads it" or "the desktop domain is non-empty."

## Problem / Goal

Each faculty still finds out "what is true in David's world right now" its own way, at its own time, from
its own source — the stale-data/race drift the volume exists to kill. A frozen `LiveWorldState` is now
assembled once per turn and pinned to the plan, but **no consumer reads it and its largest domain is
empty**, so the drift is untouched. Goal: finish the job — fix the assembly bugs, bind the envelope,
migrate faculties off direct sensor calls domain by domain, and prove by test that the world is read once.

## ⚠ Boundary with Volume XIII — do NOT build a rival spatial model

The audit finding (`AUDIT_MASTER_2026-08-10.md` §3) is that **Vol XV §1.2 institutionalises the split by
excluding geometry from the World Model** — "a World Model with no space in it" — while three route
planners exist unreconciled. That is now resolved *by ownership, not by absorption*:

- **Volume XIII Ch.2 owns spatial reasoning** (Ruling D-XIII-1): the Spatial Faculty is the sole component
  that may answer *"can I reach that?"* / *"how do I get there?"*.
- **Volume XV supplies the geometry it reasons over** — window rects, z-order, screen bounds, focus — as
  ordinary sensed domain data inside `DesktopState`, carrying the same freshness header as every other
  domain. That is *supply*, not *reasoning*.
- **This WO MUST NOT** add surface graphs, affordances, body schema, reachability, route selection or
  movement cost to `world/live_world_state.py`. Any of those appearing here is a second spatial model and
  is a build-time failure.
- **Canon correction owed (Architect lane, not this WO):** `Volume_XV/01_Unified_World_State.md` §1.2
  describes `world/world_state.py` as *"the spatial node graph Unity uses for navigation and presence
  movement."* The file's own header says it converts memory snapshots into an **eLo Planet game world
  graph**. Vol XIII Ch.2 flags §1.2 as stale. Builder: do not act on §1.2 as written.

## Scope to DoD

**A. Fix the assembly (bugs found by IRV — these come first).**
- Repair the desktop domain: `world/live_world_state.py:194` must call the symbol that exists
  (`desktop.window_state.get()` returning `WindowState`), map `app`/`title`/`activity` into `DesktopState`,
  and set `surface` honestly. Fix the identical broken import at
  `faculties/perception/perception_faculty.py:337`. **Do not widen the `except`** — narrow it so an
  `ImportError` in the assembly path is logged loudly rather than silently degrading a domain forever.
- Reconcile `degraded[]` with `domain_health`: every domain whose `status ∈ {absent, stale}` appears in
  `degraded[]`, or the chapter rule changes — one of the two, stated, not left inconsistent.
- **Read caches, never trigger.** `desktop/window_state.get()` shells out to `osascript` with a 2s timeout
  and holds no cache; calling it inline makes assembly a sensor trigger, against Ch.1 (*"reads caches, never
  triggers"*) and against the per-domain time budget. Either read the cached window block from
  `blender_state.json` / the perception cache, or give the call an explicit budget and a `stale` fallback.

**B. Bind the envelope (Ch.1 §1.8 — currently absent).**
- `sender` MUST be `WorldStateFaculty`; `expires` MUST be set to the turn TTL (a world snapshot is
  perishable and must never be reused across turns); `payload.type: live_world_state`; per-domain freshness
  stays in `payload.body.domain_health`, never in the envelope. Publish per `Volume_V/CONTRACTS.md §2`.
- Faculty lifecycle per CONTRACTS §3; the only `UPDATING` is tuning sensor budgets/cadence — no
  personality-affecting learning.

**C. Migrate consumers — the actual missing work, one domain at a time.**
- Replace each direct sensor call in the turn path with a read from the frozen `LiveWorldState`:
  `tools/tool_router.py` (3 sites) · `desktop/desktop_presence.py` · `faculties/perception/*` (perception
  *populates* the world, so it stays a supplier — but it must not be re-read as a second source
  mid-turn) · any spotify/weather/calendar/browser/file-drop/OS-time read inside a turn.
- Assert **behaviour parity at each step** before moving to the next domain: same correct output, one
  fewer source of truth. A faculty needing a freshness guarantee checks `domain_health[domain].status`.
- `server.py`'s pre-spine path decides at `server.py:2322` before `spine.run()` assembles anything
  (see WO-CANON-VII, Ruling C). Until that closes, **do not** paper over it by assembling a second world
  earlier in `server.py` — one assembly per turn stays the law. Coordinate with WO-CANON-VII.

**D. Do NOT touch `world/world_state.py`** (the eLo Planet game world graph — a different object; naming is
architecture, do not overload "World State").

## Files to TOUCH
- `world/live_world_state.py` (complete: bug fixes, envelope binding, degraded reconciliation)
- `faculties/perception/perception_faculty.py` (the duplicated broken import at L337 only)
- `tools/tool_router.py` (L1013 / L1155 / L1182 — migrate to the frozen world)
- `desktop/desktop_presence.py` (L18 — migrate)
- `runtime/spine/spine.py` (envelope publication; no second assembly)
- `tests/test_canon_xv_world_state.py` (extend — see Tests)
- `docs/architecture/Volume_XV/00_Metadata.md` — **Architect lane**, relayed: `implementation:` is stale.

## Files MUST-NOT-TOUCH
- `world/world_state.py` (game world graph — Vol XIII Ch.5)
- `desktop/spatial_state.py` (Vol XIII's supplier; its route-planning demotion is WO-CANON-XIII's, not this WO's)
- `runtime/executive.py` (FROZEN — `FREEZE_V1_LOCK.md`)
- Anything under `faculties/spatial/` (WO-CANON-XIII owns it)

## Definition of Done
- `LiveWorldState` assembled + frozen exactly **once** per turn, published with `sender=WorldStateFaculty`
  and a set `expires`.
- **The desktop domain is non-empty on David's Mac** with a real app/title, and no domain is silently
  `absent` because of a swallowed `ImportError`.
- **At least the migrated domains have a real consumer** — a faculty that previously called a sensor
  directly now reads the frozen world, with parity asserted. "Assembled and pinned" is NOT done.
- Every domain carries `{fresh_ts, confidence, source, status}`; absent/stale honestly flagged and reflected
  in `degraded[]`; nothing fabricated.
- One domain down never blocks the turn; cold start yields a time-only world and proceeds.
- No spatial reasoning of any kind exists in `world/live_world_state.py`.
- Architect can then re-check Vol XV and update `00_Metadata.md` off `PENDING`. **This WO does not confer
  DONE** — that is `COMPLETION_LOG.md` with David's sign-off.

## Tests (`tests/test_canon_xv_world_state.py` — extend the existing 14)
Existing FT-1…FT-4 / ST-1…ST-4 / IT-1…IT-2 stay. **Add, and these are the ones that would have caught the
current state:**
- **RT-1 (regression, the bug):** every symbol `live_world_state` imports actually exists — import the
  assembly module's sensor entry points explicitly and fail on `ImportError` rather than degrading. Assert
  `domain_health['desktop'].status != 'absent'` when a window is present.
- **RT-2:** no bare `except:` in the assembly path silently converts a code error into `status: absent` —
  a code error must log; only a genuine sensor absence yields `absent`.
- **RT-3 (consumer proof — fails today by design):** at least one named faculty that previously read a
  sensor directly now reads `CognitiveState.world_state`, and the direct call site is gone. Assert the
  removed import is absent from that module.
- **RT-4 (envelope):** the published envelope has `sender == "WorldStateFaculty"` and a non-null `expires`;
  a prior-turn snapshot is rejected as expired.
- **RT-5 (degraded consistency):** `set(degraded) == {d for d,h in domain_health.items() if h['status'] in
  ('absent','stale')}`.
- **RT-6 (Vol XIII boundary):** `world/live_world_state.py` contains no route/affordance/reachability/
  surface-graph symbol — a grep-level assertion that the rival spatial model was not re-created.

## Dependencies + blocked-by
- **Blocked by:** none. Buildable now.
- **Coordinates with:** **WO-CANON-VII** (Ruling C — the decision currently precedes assembly at
  `server.py:2322`; do not fix that by assembling twice) · **WO-CANON-XIII** (consumes `DesktopState`
  geometry; owns all spatial reasoning) · **WO-CANON-XXV** (reads `TimeState`/`CalendarState` — and is
  itself unwired, so it is not yet a consumer) · **WO-CANON-XII** (Perception populates the slices) ·
  Vol VI (attention candidates) · Vol XVI (`world` component of the assembled state).
- **Gate:** none. No CANON_REVIEW_QUEUE ruling and no David L3 blocks this. Build-then-verify.

## Lane
Builder (Python — `world/live_world_state.py` completion + envelope + incremental consumer migration).
Architect coordinates only (D-LANES) and owns the `Volume_XV/00_Metadata.md` / §1.2 corrections.
