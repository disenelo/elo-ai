# eLo OS — Runtime Contracts
## Canonical Reference v2.0

> Read this before reading any implementation.
> If code conflicts with this document, the document is right.

---

> ## 📍 THIS DOCUMENT IS NOW AN ORIGIN TEXT — read the volumes first
>
> **Added 2026-08-13 by the Lead Architect.** This file is kept in place because it is cited by
> path across the canon. It is **not** retired, and nothing below is deleted. But it is no longer
> the whole story, and it has drifted from the runtime it describes.
>
> | If you want… | Read |
> |---|---|
> | The four contracts, expanded — producer · consumer · mutator · freeze point, reconciled against live code | **`Volume_III/01_The_Four_Runtime_Contracts.md`** |
> | What runs where — eLo-OS Python · the bridge · Unity DesktopBuddy — and the DOWN/UP IO boundary (`blender_state.json` / `unity_events.json`), incl. **Ruling E** | **`Volume_III/02_Process_and_Boundaries.md`** |
> | **The turn order** — which faculty runs in which position, transcribed from live `spine.py` with file+line citations | **`Volume_IV/01_The_Turn_Loop.md`** |
> | The ordering **invariants** other volumes depend on, and how to test them | **`Volume_IV/02_Ordering_Guarantees_and_Invariants.md`** |
> | `CognitiveState` slot-by-slot — who writes each, who reads each, and **Ruling F** | **`Volume_IV/03_CognitiveState_The_Carrier.md`** |
>
> **Precedence, corrected.** The line above — *"If code conflicts with this document, the
> document is right"* — was correct in July 2026, when this document led the code. It is no
> longer straightforwardly true: WO-CANON-VI / XII / XV / XVI all landed in the runtime after
> v2.0 and this document did not move. **Volume III §1.0 states the replacement rule:** where the
> canon states an *ownership or mutation law*, the law binds; where it *describes what the
> runtime does*, the code is current truth and the description is dated and sourced. **Every
> disagreement is named** — the register is `Volume_III/01_*` §1.7 (10 rows) and
> `Volume_IV/01_*` §1.5 (9 rows).
>
> **Known divergences from this document, as of 2026-08-13 (IRV):** `CognitivePlan` exists twice
> and the live one is **mutable**, not frozen · `ExecutionReport` has **no producer** · the
> Relationship Faculty does **not** contribute to `CognitiveState` · `integrate_session()` was
> never built · the loop is entered only from a request path. See the registers above.

---

## The Loop

```
Observe
  ↓
Faculties → CognitiveState    everything known
  ↓
Executive  → CognitivePlan    everything decided
  ↓
Execution  → EmbodimentState  everything expressed
  ↓
Subscribers consume independently.
  ↓
           → ExecutionReport  what actually happened
  ↓
Reflection Faculty
  ↓
integrate_session()
  ↓
Updated memory / identity
  ↓
Next observation.
```

This is a continuous loop, not a request-response pipeline.

---

## The Foundational Principle

The runtime has exactly **one cognition**.

- Everything contributes to CognitiveState.
- Only the Executive decides. It produces CognitivePlan.
- Nothing downstream re-thinks.
- Reality never mutates intention.
- Reality informs future cognition through integrate_session() only.

---

## The Four Contracts

### 1. CognitiveState

**Purpose:** Everything the runtime currently knows, before any decision is made.

**Produced by:** All upstream faculties in sequence.
**Consumed by:** The Executive — and only the Executive.
**Mutated by:** Nobody. Frozen after assembly.

```
Language Faculty
  ↓
Memory Faculty
  ↓
Attention Faculty
  ↓
Relationship Faculty
  ↓
Conversation Context Matrix
  ↓
Human Interaction Matrix
  ↓
Environment Faculty
  ↓
Capability Faculty
  ↓
CognitiveState (assembled, frozen)
```

**Key principle:** The Executive never directly queries any faculty. It receives CognitiveState and reasons from it alone. This is the difference between a system that "asks around" and one that receives a complete world model.

**File:** `runtime/contracts.py → CognitiveState`

---

### 2. CognitivePlan

**Purpose:** The single intention produced by the Executive for this turn.

**Produced by:** The Executive — once per turn.
**Consumed by:** Every downstream system (LLM context assembly, voice, avatar, desktop, Unity, Robot, Dynamic Island).
**Mutated by:** Nobody. Frozen at production.

This object already partially exists as `runtime/spine/plan.py`. The v2.0 contract in `contracts.py` expands and eventually supersedes it.

**Key principle:** Everything downstream reads CognitivePlan. Nobody re-decides. Voice derives speech from it. Presence derives posture. Unity derives animation. The same intention becomes different expression across surfaces — but the intention is the same object.

**File:** `runtime/contracts.py → CognitivePlan`
**Legacy:** `runtime/spine/plan.py` (v1.x — keep until spine alignment is complete)

---

### 3. EmbodimentState

**Purpose:** How CognitivePlan becomes visible — across every surface simultaneously.

**Produced by:** Execution layer (from CognitivePlan).
**Consumed by:** All surfaces independently.
**Mutated by:** Nobody. Published once.

```
CognitivePlan
  ↓
EmbodimentState (assembled from plan)
  ↓
Publish

Subscribers (independent, non-blocking):
  Unity           reads animation_profile, motion_command, glow_*
  Desktop Avatar  reads desktop_presence, emotional_state
  Robot           reads robot_led_state, robot_led_intensity
  Dynamic Island  reads island_mode, island_color
  Voice           reads tts_text, voice_energy, voice_pacing
  Lights          reads glow_hue_*, pulse_profile, brightness
```

**Key principle:** CognitivePlan is internal intention. EmbodimentState is distributed expression. They are not the same object. The plan is never exposed to subscribers directly — only the embodiment is.

Each subscriber uses `published_at` and `sequence_id` to handle staleness. No subscriber blocks another. The publisher never waits.

**File:** `runtime/contracts.py → EmbodimentState`
**Legacy publisher:** `blender_bridge/state_writer.py` (will become the EmbodimentState publisher)

---

### 4. ExecutionReport

**Purpose:** What actually happened. Observed reality, not intention.

**Produced by:** Execution layer, after turn completes.
**Consumed by:** Reflection Faculty, integrate_session().
**Mutates:** Nothing. Never touches CognitivePlan.

**Key principle:** The delta between `CognitivePlan.primary_objective` and `ExecutionReport.completion_state` is the signal that drives growth. If a tool failed, a surface was offline, a capability was missing — that gap becomes learning. Reality is measured separately from intention so that learning occurs through integration, not through mutation of the plan.

```
CognitivePlan  →  what was intended
ExecutionReport → what occurred
      ↓
    delta
      ↓
Reflection Faculty
      ↓
integrate_session()  (replaces compress_session())
      ↓
Updated memory, identity, relationship understanding
```

**File:** `runtime/contracts.py → ExecutionReport`

---

## Convergence Strategy

Do not rewrite the runtime. Converge it.

### Step 1 — Contracts defined ✅
`runtime/contracts.py` defines all four objects.
No behaviour changes.

### Step 2 — Type hints
Add type annotations pointing to contract classes throughout existing code.
No behavioural changes.

### Step 3 — Replace dicts
Gradually replace dict-assembled state with typed contract objects.
One subsystem at a time. Identical behaviour.

### Step 4 — Executive output
Executive outputs `CognitivePlan` (contracts.py) only.
`runtime/spine/plan.py` aligns to v2.0 schema.

### Step 5 — Context Composer
`runtime/prompt_builder.py` becomes `runtime/context_composer.py`.
Receives `CognitiveState + CognitivePlan`.
Assembles `LLMContext` — serialised differently per backend.

### Step 6 — Embodiment Bus
`blender_bridge/state_writer.py` becomes the publisher.
Produces `EmbodimentState` explicitly.
Writes `blender_state.json` as one serialisation format.

### Step 7 — ExecutionReport
Every execution path returns `ExecutionReport`.
Reflection Faculty wired to consume it.
`integrate_session()` replaces `compress_session()`.

### Step 8 — Reflection Faculty
`offline_engine.py` becomes `runtime/reflection_faculty.py`.
Runs on idle + session close.
Produces insights, pattern observations, memory compression, identity consistency.
Writes to vault. Never answers users.

### Step 9 — Environment Faculty
`desktop/` modules unified under `runtime/environment_faculty.py`.
Desktop + Calendar + Weather + Spotify state = one Environment contribution to CognitiveState.

---

## Renamed Concepts

| Current | v2.0 | Reason |
|---|---|---|
| `prompt_builder.py` | `context_composer.py` | It assembles cognition, not prompts |
| `state_writer.py` | Embodiment Bus publisher | It publishes state to all surfaces |
| `compress_session()` | `integrate_session()` | Compression stores. Integration grows. |
| `offline_engine.py` | Reflection Faculty | It produces insight, not offline responses |
| `world_state.py` | Environment Faculty | Desktop, Robot, Calendar, Weather — all environment |

---

## Passive Awareness (Immediate Fix)

> ⚠️ **UNDATED EMBEDDED TODO — flagged 2026-08-13, not resolved.** This section is an in-flight
> engineering note sitting inside a canonical reference. A canon document with a live TODO in it
> is either stale or is a work order wearing the wrong hat. It is logged as **F-4**
> (`FOUNDATION_VOLUMES_STATUS_2026-08-10.md`) and **III-4** (`Volume_III/00_Metadata.md`), and it
> needs David + a Builder confirmation of whether the fix shipped.
>
> **A deeper finding, since recorded:** `Volume_IV/03_CognitiveState_The_Carrier.md` §3.3 shows
> that `CognitiveState.graph_context` (`runtime/contracts.py:133`) is **never written by the
> assembler at all** — so the one-line fix below would append an always-empty string. The
> Architect's recommendation is to route passive desktop awareness through `LiveWorldState`
> (Volume XV's eleven domain slices already carry it) rather than revive a dead slot, and to
> move this section out of canon into a WO. **Retained verbatim below until David rules.**

`graph_context` in CognitiveState must reach the LLM.

Currently: `shadow_context()` is computed each turn but `graph_context` is passed to `prompt_builder.build()` and never appended to `sections`. The LLM never sees it.

Fix: One line in `runtime/prompt_builder.py`:
```python
if graph_context.strip():
    sections.append(f"[DESKTOP CONTEXT]\n{graph_context}")
```

This gives eLo passive awareness — knowing what you're in without being asked.
This is presence. Fix it before anything else.

---

## Success Criteria

The runtime is correct when:

- Every object has one responsibility.
- Every faculty has one responsibility.
- Every decision occurs exactly once.
- Every embodiment originates from the same cognition.
- Every surface receives the same intention.
- Reality is measured separately from intention.
- Learning occurs through integration, not mutation.
- The architecture is obvious.
- Future contributors understand the runtime by reading this document and `runtime/contracts.py` before any implementation.

---

*eLo OS v2.0 — DISENELO*
*Architecture defined: 2026-07-05*
*Authors: David Charles · Claude (Chief Runtime Architect) · Systems Architect Agent*

---

```
STATUS 2026-08-13 — ORIGIN TEXT, kept in place (cited by path across the canon)
Promoted into volume form by:
  Volume_III/  — System Architecture   (the contracts · the boundaries · Ruling E)
  Volume_IV/   — The Cognitive Spine   (the turn order · the invariants · the carrier · Ruling F)
Superseded in NOTHING; expanded and reconciled. Divergence registers:
  Volume_III/01_* §1.7 (canon vs code, 10 rows) · Volume_IV/01_* §1.5 (9 rows)
Open against this file: the undated "Passive Awareness (Immediate Fix)" TODO (F-4 / III-4).
```
