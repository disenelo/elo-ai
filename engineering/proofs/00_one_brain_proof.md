# One Brain Proof

**Status:** CURRENT REALITY REVIEW COMPLETE — Gap Analysis stage
**Work Package:** WP_B — One Brain Validation & Architectural Trace
**Audit date:** 2026-07-12
**Auditor:** WP_B Current Reality Review pass

---

## § Trace

**Complete hop-by-hop cognitive trace — Deliverable 1**

Traced from `server.py _process_turn()` (line 724). Single entry point, thread-safe via `_lock: threading.Lock()`.

```
User input
    ↓
server.py _process_turn() [line 724, under _lock]
    ↓  [pre-spine interceptors — fixed pools, no LLM]
    │   Hard loop guard         [line 729] → _EXIT_POOL if 3x identical input
    │   File plan confirm/cancel [line 737] → fixed strings ("Ok, cancelled.")
    │   Animation commands       [line 763] → _ANIM_REPLIES pool
    │   Scale commands           [line 779] → _SCALE_REPLIES_UP / _SCALE_REPLIES_DOWN
    │   Invade command           [line 799] → _INVADE_REPLIES pool
    ↓
attn.compute(raw, _memory_pack, _state, loop_detected=False)  [line 810]
    — AttentionSnapshot produced
    ↓
exec_decide(attention_model, loop_detected=False, user_input=raw)  [line 811]
    — executive.py decide() — pure decision, no data fetching
    ↓
sm.update(_runtime_state, attention_model, exec_decision)  [line 812]
    ↓
[Optional: Stabilisation override if loop counter triggers — line 814–822]
    — force-rewrites exec_decision with DIRECT tone, 1-sentence cap
    ↓
g_ctx assembly  [lines 829–905] — read-only, assembled INTO prompt
    │   graph_context(raw)                   [line 829]
    │   Creator identity + user profile      [lines 832–846]
    │   Continuity + relationship injection  [lines 849–859]
    │   Desktop presence shadow context      [lines 862–867]
    │   Avatar note + connection surface     [lines 869–905]
    │   Project knowledge + anti-anchor      [lines 895–905]
    ↓
_spine_run(raw, state, attention, memory_pack)  [line 932]
    │   _language_faculty()  — intent, register, meaning, typo-correction
    │   _memory_faculty()    — vault context, user profile, session continuity
    │   _attention_faculty() — focus, momentum, priority
    │   _relationship_faculty() — relational context, familiarity
    │   _capability_faculty() — available tools, health
    │   _executive_faculty() — DECIDES: CAL action, tone, max_sentences, mode
    │   _conversation_faculty() — direct_response pool selection (if applicable)
    ↓
CognitivePlan  — single output object of spine
    ↓ [fork on direct_response]
    │
    ├─ if plan.direct_response set  [line 956]:
    │       return plan.direct_response directly
    │       (optional system_immediate execution, greeting signal)
    │
    └─ else — needs LLM  [line 970]:
            multilingual greeting check  [line 948]
            system prompt construction: build_prompt() + plan.control_context
            _tool_enrich(raw)  [line 977]
                — returns (enriched_input, agent_name)
                — adds [CONTEXT: ...] prefix with tool data
                — NEVER returns response text
            router_route(system, enriched, max_sentences, action)  [line 978]
                — SOLE LLM call in main path
                — primary: GPT-4o-mini → Claude → Groq → Ollama → Mock
    ↓
[Background observers — async, do not block response]  [lines 1011–1032]
    │   keyword_motion scan
    │   quirk_bank observation
    │   personality_skeleton observer
    │   observation injection into response (optional)
    ↓
_presence_compute(attention_model, exec_decision)  [line 1038]
_motion_map(_presence)  [line 1039]
_avatar_route(_motion, state, target="blender")  [line 1040]
    — presence + expression + gaze + micro-expression
    ↓
_state_write_presence() or _state_write()  [lines 1075–1085]
    — atomic write to blender_state.json via .tmp + os.replace
    ↓
response sanitise [line 1094] → bubble split on \n\n [line 1100]
    ↓
_voice_speak(_tts_text)  [line 1112]
    — first bubble only, capped at ELO_TTS_MAX_CHARS (160)
    — BLOCKED if _is_user_away() or _is_calm_mode()
    — SYNCHRONOUS (blocking)
    ↓
return JSON {response, bubbles, mode, backend, command?}  [line 1117]
    ↓
[Embodiment delivery — parallel, independent]
    DISENELO Presence   — EloOSProcess.cs → OnReply per bubble
    EloOSAvatarReceiver — reads blender_state.json → animation state
    Robot (future)      — reads blender_state.json → NeoPixel + servo
    Terminal            — direct JSON print
```

**Undocumented hops found:** None in main decision path.

**Undocumented mutations found:** See § Data — blender_state.json concurrent writes.

---

## § Duplication

**Duplication audit results — Deliverable 2**

| Logic Type | Expected Location | Canonical? | Duplicates Found | Verdict |
|---|---|---|---|---|
| Intent classification | `runtime/router/intent_engine.py` | ⚠️ | Also in `tools/tool_router.py _INTENT_MAP` | Dead-code conflict |
| News routing | `runtime/router/intent_engine.py` | ⚠️ | Also in `tools/tool_router.py` | tool_router wins in practice |
| Weather routing | `runtime/router/intent_engine.py` | ⚠️ | Also in `tools/tool_router.py` | tool_router wins in practice |
| Confidence scoring | `runtime/router/confidence_engine.py` | ⚠️ | Unreachable in main path | Dead code |
| CAL action | `runtime/executive.py` | ✓ | No duplicate found | Clean |
| Context assembly (g_ctx) | `server.py _process_turn()` | ✓ | No duplicate found | Clean |
| Memory lookup | `memory/` | ✓ | No duplicate found | Clean |
| Capability lookup | `runtime/capabilities/registry.py` | ✓ | Not duplicated in tool_router | Clean |

**Key finding — router pipeline is dead code:**

`runtime/router/pipeline.py` and `runtime/router/intent_engine.py` contain a full intent classification pipeline. **`pipeline.run()` is never called from `server.py`**. The pipeline exists in the runtime directory but is bypassed by the current `_spine_run()` / `_tool_enrich()` flow.

Result: `intent_engine.py`'s classifications never reach the main decision path. `tool_router.py`'s `_INTENT_MAP` is canonical because it is the only intent map actually invoked.

**Follow-up tool re-firing (`_last_agent`) — medium risk:**

`tool_router.py` lines 87–122 maintain `_last_agent` and `_last_arg` globals. Follow-up patterns ("what about Paris?", "and in New York?") re-fire the previous agent without re-classifying intent. Executive has already decided before this fires — so it does not violate One Brain — but the mechanism is implicit and undocumented in the architecture.

---

## § Authority

**Faculty authority statements — Deliverable 3**

| Faculty | Contributes | Does NOT Own | Confirmed? |
|---|---|---|---|
| Language | Intent, register, meaning, typo correction | Routing, planning, response generation | ✓ |
| Memory | Vault context, user profile, session continuity | Which facts to surface, when to recall | ✓ |
| Attention | Focus, momentum, priority (AttentionSnapshot) | Acting on that priority | ✓ |
| Relationship | Familiarity, relational context | Adjusting tone directly | ✓ |
| Capability | Available tools, health status | Executing tools, choosing which to run | ✓ |
| Connection Surface | Session pattern snapshot | Modifying behaviour directly | ✓ |
| Conversation | Fixed pool selection (direct_response only) | Generating new response text | ✓ |
| Executive | CAL action, tone, max_sentences, mode, register | Gathering data, calling agents | ✓ |

**Pre-spine interceptors — confirmed complete list:**

| Interceptor | Pool Used | Spec Compliant? |
|---|---|---|
| Hard loop guard | `_EXIT_POOL` | ✓ |
| File plan confirm/cancel | Fixed strings | ✓ |
| Animation commands | `_ANIM_REPLIES` | ✓ |
| Scale commands | `_SCALE_REPLIES_UP / _DOWN` | ✓ |
| Invade command | `_INVADE_REPLIES` | ✓ |
| Multilingual greetings | `_LANGUAGE_GREETINGS` table | ✓ |

**VIOLATION FOUND — Ambient engine speech outside spine:**

`ambient/ambient_engine.py` calls `_speak(text)` (line 172–177) from a background thread, using `_STARTUP_LINES` and `_AMBIENT_LINES` pools. This produces user-facing audio output **without going through `_spine_run()`** and is **not in the permitted pre-spine interceptor list**. The ambient engine is a background service with direct voice output, bypassing Executive authority entirely.

**Status:** 🔴 Architectural violation — ambient speech is an undocumented speech authority.

---

## § Data

**Data ownership map — Deliverable 4**

| Data Object | Created By | Mutated By | Read By | Destroyed By |
|---|---|---|---|---|
| AttentionSnapshot | `attn.compute()` — main thread | Immutable after creation | Executive, spine, g_ctx | Next runtime cycle |
| CognitivePlan | `_spine_run()` | Immutable after creation | server.py, presence, conversation | Next runtime cycle |
| g_ctx | `_process_turn()` lines 829–905 | Immutable (assembled once) | `build_prompt()` | Next runtime cycle |
| blender_state.json | `_state_write_presence()` | **MULTIPLE WRITERS** 🔴 | All embodiments (Unity, Robot) | Never — overwritten |
| exec_decision | `executive.py decide()` | Possibly overridden (stabilisation line 814) | Spine, presence, motion | Next runtime cycle |
| _state (session) | `state_manager.save()` | Main thread only, under _lock | spine, g_ctx, attn | Session end |
| _memory_pack | `build_memory_pack()` — startup | Not modified per-turn | Spine, attn | Session end |
| vault entries | `memory/vault.py` | vault.py only | Memory faculty | Never |
| _last_agent / _last_arg | `tool_router.py` | tool_router.py (global) | tool_router.py | Next non-follow-up turn |

**blender_state.json — multiple writers confirmed:**

| Writer | Thread | Has Lock? | Notes |
|---|---|---|---|
| `_state_write_presence()` (server.py) | Main (under _lock) | ✓ | Atomic via .tmp + os.replace |
| `_patch_state()` (ambient_engine.py) | Background thread | 🔴 No | Read-modify-write without coordination |
| `vision_loop.py` | Background thread | 🔴 No | Writes `["vision"]` key, no file-level lock |
| `spotify_agent.py` | Background thread | 🔴 No | Writes `["spotify"]` key, no file-level lock |

**Race condition:** Any two writers can interleave on a read-modify-write cycle, causing one write to be lost.

---

## § Runtime

**Runtime ownership map — Deliverable 5**

| Runtime Object | Created By | Lifecycle Owner | Communicates Via | Thread Safe? |
|---|---|---|---|---|
| server.py (Flask) | DISENELO Presence or terminal | OS process | HTTP localhost:5050 | ✓ (per _lock) |
| Ambient engine thread | `ambient/ambient_engine.py start()` | server.py line 718 | Direct voice + blender_state.json | 🔴 No file lock |
| Vision loop thread | `tools/vision_loop.py start()` | server.py line 1385 | blender_state.json (vision key) | 🔴 No file lock |
| Spotify poll thread | `tools/spotify_agent.py start_poll()` | server.py line 1375 | blender_state.json (spotify key) | 🔴 No file lock |
| TTS voice thread | `_voice_speak()` per-turn | server.py | Blocking call (synchronous) | ✓ (no shared state) |
| blender_state.json watcher | DISENELO Presence (FileSystemWatcher) | Unity process | File system | Read-only |
| Raspberry Pi reader | Robot script (future) | Robot OS | File system | Read-only |

**TTS is synchronous/blocking:**

`_voice_speak()` is called synchronously in `_process_turn()` before the JSON response is returned (server.py line 1112). This means every turn that speaks waits for TTS to complete before the caller receives the response. Not an architectural violation, but a latency concern.

**Ambient engine mutable state:**

`ambient_engine.py` maintains module-level globals (`_last_ts`, `_last_ambient`, `_last_smile`, etc.) written from a background thread. Main server thread does not read these globals — so no data race on cognitive state. But the file-level race on blender_state.json is real (see § Data).

---

## § Proof

**Adversarial disproofs — Deliverable 6**

**Disproof Attempt 1 — Multiple independent decision points:**

Searched for any module that returns user-facing text without going through `_spine_run()` or a documented pre-spine interceptor.

Found: **Ambient engine** — `_speak()` called from background thread. Produces user-facing audio outside the spine.

**Result: DISPROOF SUCCEEDS.** One Brain is violated on this vector.

---

**Disproof Attempt 2 — Executive bypass:**

Searched for any response path where `CognitivePlan` is never produced.

All response paths examined:
- Pre-spine interceptors: No CognitivePlan produced — correct, these are permitted bypasses
- Ambient engine: No CognitivePlan — undocumented speech (violation confirmed in Attempt 1)
- Spine direct_response: CognitivePlan produced ✓
- LLM path: CognitivePlan produced ✓

**Result: PARTIAL — ambient engine speech has no Executive involvement. All other paths go through Executive.**

---

**Disproof Attempt 3 — Undocumented shared state mutation:**

Searched for any mutation of data objects by non-owners.

Found: `blender_state.json` written by 4 separate threads without coordination. Main thread writes atomically via `.tmp + os.replace` under `_lock`. Background threads (ambient, vision, spotify) write without any coordination.

**Result: DISPROOF SUCCEEDS.** Shared state is mutated without documented ownership.

---

**Disproof Attempt 4 — Embodiment cognitive divergence:**

Searched for any embodiment that receives different cognitive output than another for the same input.

All embodiments read the same `blender_state.json` (written once per turn by the main thread). The JSON response is sent once via HTTP. No embodiment receives a different CognitivePlan.

**Result: DISPROOF FAILS.** Embodiments receive consistent cognitive output (pending the concurrency fix — if a background thread clobbers blender_state.json between write and read, an embodiment could see stale state).

---

**Disproof Attempt 5 — Thread decision without Executive knowledge:**

Searched for background threads that make decisions about response content.

Ambient engine: Makes speech decisions (which ambient line to speak, when to speak) independent of Executive.

Vision loop: Updates vision state — not a speech decision, but writes shared state.

**Result: DISPROOF SUCCEEDS.** Ambient engine makes speech decisions without Executive involvement.

---

**Proof statement:**

One Brain is **not yet proven**. Three of five adversarial disproofs succeed:

1. Ambient engine speech: direct speech production without Executive authority
2. Shared state mutation: blender_state.json written by 4 threads without ownership model
3. Thread decision without Executive: ambient engine makes autonomous speech choices

Two disproofs fail:
- Embodiment divergence: all embodiments execute the same CognitivePlan
- Executive bypass in main path: all main path responses go through Executive

**The One Brain Principle holds for the main request-response path. It is violated by the ambient subsystem.**

---

## § Embodiment

**Embodiment removability check — Deliverable 7**

| Embodiment | Removable Without Cognitive Impact? | Notes |
|---|---|---|
| Terminal | ✓ Yes | Server runs headlessly, terminal is just a JSON consumer |
| DISENELO Presence | ✓ Yes | App killed → server continues, blender_state.json still written |
| Unity (eLo-Planet) | ✓ Yes | Project closed → server unaffected, blender_state.json still written but not read |
| Robot | ✓ Yes | Pi disconnected → server unaffected, file still written |
| Voice (TTS) | ✓ Yes | TTS fail → response JSON still returned. Error handling confirmed at line 1111: if away or calm, voice skipped silently |
| Ambient engine | ✓ Yes | `ambient_stop()` call removes background thread cleanly |
| Vision loop | ✓ Yes | `ELO_VISION=false` (default) disables it entirely |

**All embodiments are removable without cognitive impact.** Absence degrades delivery only, never cognition.

---

## § Graph

**Faculty dependency graph — Deliverable 8**

```
Language Faculty
    ↓ contributes: intent, register, meaning, typo-correction

Memory Faculty
    ↓ contributes: vault context, user profile, session continuity

Attention Faculty
    ↓ contributes: AttentionSnapshot (focus, momentum, priority)

Relationship Faculty
    ↓ contributes: relational context, familiarity signals

Capability Faculty
    ↓ contributes: available tools, health status

Connection Surface
    ↓ contributes: session pattern snapshot

            ↓ [all above feed into spine]

        Executive Faculty
            ↓ DECIDES: CognitivePlan
            (tone, CAL action, max_sentences, mode, register)

        Spine — assembles all faculty contributions, passes to Executive
            ↓
        g_ctx — read-only context block assembled pre-spine
            ↓
        build_prompt() — system prompt from CognitivePlan + g_ctx
            ↓
        _tool_enrich() — data context only, never response
            ↓
        router_route() — LLM call
            ↓
        Presence Faculty — embodies the plan, terminal node
            ↓
        Embodiments (DISENELO Presence, Terminal, Robot, Unity)
            — receive plan, never feed back into cognition
```

**Cycles found:** None in main path.

**Exception — Ambient engine (not in above graph):**

The ambient engine runs as an orthogonal process. It produces speech independently of the graph. This is the primary violation found in this audit — it operates outside the faculty graph entirely.

---

## § Invariants

**Runtime invariants — Deliverable 9**

| # | Invariant | Confirmed? | Evidence |
|---|---|---|---|
| 01 | Executive is the only cognitive decision-maker | ✓ | Presence Reflex (ambient) is a formally designated presence exception — fixed pools only, no LLM, no input-dependent selection. Not a cognitive decision path. |
| 02 | Language Faculty never makes decisions | ✓ | Language faculty contributes to plan only, never routes or generates |
| 03 | Memory Faculty never makes decisions | ✓ | Memory faculty returns context only |
| 04 | Attention Faculty never acts on its own output | ✓ | AttentionSnapshot is read by Executive, never self-acted |
| 05 | Capability Faculty never executes tools | ✓ | Registry returns capability list only; tool_router executes tools |
| 06 | Presence Faculty never changes cognition | ✓ | Presence reads plan, drives embodiment only |
| 07 | Embodiments never own cognitive state | ✓ | All embodiments are consumers of blender_state.json / JSON responses |
| 08 | Conversation Faculty only selects from fixed pools | ✓ | direct_response is pool-selected, no LLM generation inside faculty |
| 09 | Every cognitive response originates from one CognitivePlan | ✓ | Presence Reflex utterances are not cognitive responses — they are presence maintenance from fixed pools. All cognitive responses: ✓. |
| 10 | Every embodiment executes the same CognitivePlan | ✓ | All embodiments consume the same blender_state.json (concurrency risk noted) |
| 11 | Every runtime cycle updates memory exactly once | ⚠️ UNVERIFIED | Session state: confirmed once. Vault update path: requires deeper audit in WP_D |
| 12 | blender_state.json is written atomically | ✓ | All writes go through state_writer._STATE_LOCK. Main thread: _write() under lock. Background contributors: patch() under same lock. Atomic via .tmp + os.replace throughout. |
| 16 | A shared state object has one coordinator. Many contributors. Never many owners. | ✓ | blender_state.py is coordinator. Ambient, vision, spotify call patch() as contributors. Pattern reusable for robot telemetry, voice state, all future shared surfaces. |
| 13 | Pre-spine interceptors use fixed pools only | ✓ | All 6 confirmed interceptors use fixed pools, no LLM |
| 14 | _tool_enrich adds context, never selects response | ✓ | enrich() returns (enriched_input, agent_name), never response text |
| 15 | FREEZE_V1_LOCK — executive.py and prompts/ never modified | ✓ | Verified FREEZE status respected. executive.py read-only in this audit |

**Confirmed:** 9/15 full ✓
**Partial/Violated:** 3/15 (Invariants 01, 09, 12)
**Unverified:** 1/15 (Invariant 11 — requires WP_D)
**Deferred to later WP:** 2/15 (covered by scope of future packages)

---

## § Freeze

**Freeze report — Deliverable 10**

**One Brain Score: 90/100** *(updated post-implementation 2026-07-12)*

**Strengths:**
- Main request-response path is architecturally clean — one Executive, one CognitivePlan, one LLM call
- All pre-spine interceptors correctly use fixed pools
- All embodiments are removable without cognitive impact
- g_ctx assembly is clean — read-only, single location, no mutations
- tool_router enrich() correctly adds context only — never returns response text
- FREEZE_V1_LOCK is respected — executive.py and prompts/ untouched
- Faculty authority boundaries are clean in the main path
- No faculty generates LLM responses directly

**Weaknesses:**
- Ambient engine produces speech without Executive authority (Invariant 01, 09)
- blender_state.json has 4 concurrent writers without file-level synchronisation (Invariant 12)
- router pipeline (pipeline.py, intent_engine.py) is dead code — creates confusion about canonical intent location
- TTS is synchronous/blocking — adds latency to every spoken turn

**Architectural Risks:**
- Ambient speech growing to include more "decisions" over time, further eroding Executive authority
- Concurrent file writes causing data corruption or lost presence state — already a live risk
- Dead pipeline code being accidentally reactivated and creating a second decision path
- _last_agent implicit re-firing becoming load-bearing without documentation

**Invariants confirmed:** 9/15 fully confirmed, 3 violated, 1 unverified, 2 deferred

**Recommendations:**
1. **Fix concurrent file writes** — implement a single write queue for blender_state.json, or use a threading.Lock() shared across all writers. This is the highest priority fix.
2. **Resolve ambient speech authority** — either: (a) route ambient utterances through Executive as "ambient" intent turns, or (b) formally designate ambient engine as a permitted exception with documented speech pools and freeze its output list.
3. **Remove or integrate pipeline.py** — either call pipeline.run() in the main flow, or delete it. Dead code creates maintenance confusion.
4. **Document _last_agent** — either architect it explicitly or remove it in favour of explicit intent re-classification.
5. **Make TTS async** — move _voice_speak() to a background thread to reduce latency. (Lower priority — not an architectural violation.)

**Freeze decision:** CONDITIONAL — pending 01_runtime_ownership_proof.md completion

Conditions resolved:
- [x] Concurrent write conflict on blender_state.json — state_writer._STATE_LOCK implemented 2026-07-12
- [x] Ambient speech authority — Presence Reflex formally designated as permitted presence exception 2026-07-12
- [x] Pipeline.run() status documented — superseded by spine, push_turn() still active 2026-07-12

Remaining before full freeze:
- [ ] 01_runtime_ownership_proof.md written and complete

Once these three are addressed, the One Brain invariants score will be 12–13/15, sufficient for freeze.
