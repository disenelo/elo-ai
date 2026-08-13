# Unity ↔ eLo OS — IO Contract (the binding interface)
### Lead Architect, 2026-08-06 · David L3. Binds SEAT-ENG-001 (Builder/eLo OS) + SEAT-ENG-004 (Designer/UI-Unity).

**Why this exists:** the sit loop broke because the Designer wrote the ACK to `unity_events.json` while
the Builder read `blender_state.json` — write-here / read-there. An ACK eLo OS can't read and act on is
pointless. This contract fixes the class of bug, not the one instance.

## The governing rule
> **Channels are defined by DIRECTION and DELIVERY TYPE — never by topic.**
> Emotions, moods, states, new actions are **FIELDS inside an existing channel, never new files.**
> A new file is justified ONLY by a new direction or a genuinely different delivery type (continuous
> state vs discrete event) — and ONLY by updating THIS contract, which both seats sign.

Adding `emotions.json` / `states.json` / `movement.json` is FORBIDDEN — it multiplies the read/write
mismatch surface. One concern = one field in the right channel.

## The channels (this is the whole interface)
| Channel | File | Direction | Delivery | Holds |
|---|---|---|---|---|
| **DOWN — render+command** | `blender/blender_state.json` | eLo OS → Unity | continuous (overwritten each tick) | the complete state Unity renders: `motion` · `expression` · `emotion` · `gaze` · `presence_plan` · `intent` · panel flags · `capability_list` · **action commands** (`sit_command`, `move_command`, …) · `_ts` |
| **UP — events/ACKs** | `blender/unity_events.json` | Unity → eLo OS | discrete (timestamped, CONSUMED after read) | completion ACKs + perceptions: `{"type":"sit_complete","_ts":…}`, `move_complete`, `arrived`, `collided`, … |
| **UP — sensed state** *(only if needed)* | `blender/unity_state.json` | Unity → eLo OS | continuous | Unity's live sensed values eLo OS reads into its self/world model: rendered `position` · `surface` · `occluded` · pose-as-rendered. Add ONLY when continuous sense-back is required; until then, fold single values into an event. |

## The action protocol (Embodied Truth — every action is verifiable or it's pointless)
Every **action command** eLo OS writes DOWN must have a matching **ACK** it reads UP before the Executive
speaks the action. No fire-and-forget.
```
eLo OS: write <action>_command (DOWN, blender_state.json)  →  set _PENDING[action]={since:_ts}
Unity:  execute → write <action>_complete (UP, unity_events.json, with _ts)
eLo OS: each turn read UP → if type==<action>_complete AND _ts > _PENDING.since:
            update self-model (pose/surface/…) · clear pending · CONSUME (clear the event)
            → only NOW may the Executive say the action happened
        on no-ACK within timeout → say so honestly ("I tried to X but couldn't"), never claim success
```
Rules: **timestamp guard** (`_ts > since`) so a stale event can't false-trigger; **consume** (clear the
event) so the next action starts fresh; the ACK `type` names the action (`sit_complete`, `move_complete`).

## Applies to (not just sit)
sit · move (left/right/up/down/shift/to-window) · jump · wave · hide/step-out · return — every action
uses the SAME loop with its own `_command` / `_complete` pair. This is the movement-faculty generalisation
the transcript demands (`agent_bus/DIAGNOSIS_movement_mirror_2026-08-06.md`).

## Change control
Neither seat changes a file's purpose or a field's channel without updating THIS doc. It is the single
source of truth for the interface. If unsure where something goes → relay "which channel?" before writing.
