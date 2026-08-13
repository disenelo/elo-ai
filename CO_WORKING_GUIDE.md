# eLo OS — Co-Working Guide & System Map

**Read this first if you are an agent joining the eLo OS build.**

This is the orientation map produced from a full sweep of `~/elo-ai/` (2026-07-27).
It explains how the system actually runs (not just how it's specified), who owns what,
the shared contracts between agents, and the footguns that will break things silently.

- `README` / `engineering/` = **how eLo evolves** (process, phases, freezes).
- `docs/architecture/` = **what eLo is** (the 27-volume canon; see `docs/architecture/00_CANON_INDEX.md`).
- **This file** = **how the pieces fit and how the agents co-work** (operational).

> Core principle (David Charles, 2026-07-10): *"Presence comes less from adding more
> capabilities and more from ensuring the cognitive pipeline accurately tracks what
> matters in the moment before deciding whether to speak."*

---

## 1. The agents and their boundaries

| Agent | Owns | Must not |
|---|---|---|
| **Architecture Agent(s)** (you + one other) | The canon in `docs/architecture/` — specs, contracts, volumes. Protect consistency. | Write implementation code, or edit frozen runtime. |
| **Builder Agent** (Claude Code) | Implements approved specs into `runtime/`, `core/`, `faculties/`, etc. | Invent architecture; skip the freeze gate. |
| **UI / Avatar Agent** (Unity side) | The DesktopBuddy Unity project (`~/Desktop/Output/DISENELO-eLoDesktopBuddy/`) — *how* eLo looks and moves. | Decide *what* eLo says/feels; change the shared-state field names unilaterally. |

**The boundary that matters most:** *eLo OS (Python) decides what eLo says and feels;
Unity renders how eLo looks and moves.* They meet at exactly one file (§4). Neither
side reasons on the other's turf.

Coordination between OS and Unity agents happens through session-numbered handovers in
`handovers/` (currently up to **S17**; `UNITY_AGENT_HANDOVER_S*.md` = OS→Unity,
`OS_AGENT_HANDOVER_S16.md` = Unity→OS). Each supersedes the prior.

---

## 2. How one turn actually runs

Entry: `server.py` `POST /chat` → `do_POST` → `_process_turn(raw)` (~L1290), under a
**single global `threading.Lock`** (one turn at a time). Order:

```
1. Reflex shortcuts        loop guard, pending confirmations, anim/scale/nav commands
                           → can return BEFORE any LLM (tools/tool_router.py intercepts)
2. attention.compute()     core/attention.py  → intent/valence/momentum
3. executive decide()      runtime/executive.py  → the ONE decision  [FROZEN]
4. build_prompt()          runtime/prompt_builder.py  (assembles system prompt + memory)
5. Cognitive Spine run()   runtime/spine/spine.py  → CognitivePlan (runtime/spine/plan.py)
6. backend_router.route()  runtime/backend_router.py  (LLM call + guards)  unless direct_response
7. post-turn:              spine.update_session, journal_router, pattern_observer,
                           embodiment publish → blender/blender_state.json
```

**Spine faculty order** (in `spine.run`): Environment → Language → Memory(refresh) →
Relationship → Control-Plane → Capability → System → **Executive (decides once)** →
enrichment → Light Engine (presence plan) → Conversation Faculty (direct responses) →
Presence Faculty.

**Backend fallback:** OpenAI → Gemini → Claude → Groq → Cerebras → Ollama → **Mock**
(Mock always works, deterministic). Guards: lore-drift, pure-preamble, duplicate,
38-word cap. Modes via `ELO_BACKEND` (auto/cloud/local/mock).

---

## 3. Contracts: spec vs reality (important)

`runtime/contracts.py` defines the four v2.0 contracts — `CognitiveState`,
`CognitivePlan`, `EmbodimentState`, `ExecutionReport` — but **only `CognitivePlan` is
live** (via the looser `runtime/spine/plan.py`). The other three are **aspirational**:
the running turn still passes **dicts** (`attention_model`, `exec_decision`) and writes
`blender_state.json` inline.

**Do not assume `CognitiveState`/`ExecutionReport` are populated at runtime.** The
`16_spine_runtime.md` alignment spec is the plan to converge the live code onto the
contracts — it hasn't happened yet. When you write specs, mark clearly what is
target-state vs current-state.

---

## 4. THE shared state file — `blender/blender_state.json`

This is the single IPC surface between the Python brain and every embodiment (Unity,
Blender, robot, desktop). **Python writes; Unity/Blender read.**

Shape (keys): `motion{animation,speed,intensity,duration,mood,mode}` ·
`expression{shape_keys{}, head_lean, pacing, intensity}` ·
`state{energy,mode,emotion,emotional_state,intensity}` · `gaze{yaw,pitch,active}` ·
`vision{active,attention,focus{x,y},app,description}` ·
`presence_plan{primary_hue_*, pulse_*, brightness, bloom, animation_profile,
movement_style, voice_*, robot_led_state, unity_material_profile, …}` · `_ts` ·
(optional) `intent/trigger/gesture/spotify/hud_image/user_nav_event/exit_event`.

**Rules — break these and you corrupt live rendering:**

1. **Never raw-write this file.** Always go through
   `blender_bridge/state_writer.py` — `write()`/`write_with_presence()` (per-turn
   coordinator) or `patch()` (deep-merge for background writers). Atomic tmp+`os.replace`
   under a shared `_STATE_LOCK`.
2. **Read-merge-write only.** Unity-owned event keys are in `_PRESERVE_KEYS`; a full
   overwrite drops `presence_plan` and Unity's keys mid-render.
3. Sibling files: `lipsync_state.json` (speech gate, OS→Unity), `presence.json`
   (present/away, Unity→OS), `unity_events.json`, `elo_volume.json`.

**Cross-agent agreements (OS ↔ Unity) that silently drift if unsynced:**

- **Animation clip names** must be `eLo_<clip>` (`eLo_Idle, eLo_Walk, eLo_Run,
  eLo_LongJ, eLo_Calm`). Alias tables exist on **both** sides (Python
  `animation_driver.py` and Unity `EloOSAvatarReceiver.cs`) — keep them in sync.
- **Mood vocabulary**: Python's 20-state presence collapses to Unity's ~8 via
  `embodiment_publisher._UNITY_MOOD`. A mood Unity doesn't know → falls back to neutral.
- **Never send `JawOpening`** — Unity auto-derives jaw from open visemes. Sending it
  breaks the jaw/squash system.
- Shape-key values are clamped to ±1.0 (mesh range is a non-standard −5..5).
- `head_lean` sign/units convention must match on both sides.

**Character constants (immutable):** eLo has **NO EYES** (expression = mouth shape keys
+ head lean only). No Rigidbody — CharacterController only. Same brain, every body.

---

## 5. Memory — safe vs dangerous

Read path into a turn: `[CREATOR]` block (`memory/user_profile.json`) + `_vault_ctx`
(via `memory/obsidian_loader.py`, the **only** sanctioned reader of `obsidian_vault/`) +
`_memory_pack` (`memory/memory_pack_builder.py`) + knowledge graphs.

Write path: per-turn `spine.update_session` / `_memory_faculty` refresh (one-shot,
self-clearing) → periodic `tools/truth_sync.py` → `vault_layer.compress_session()` →
three-tier vault (`SPOT_CODES.md` index + `summary/<code>.md` + `deep/<code>-deep.md`).
`integrate_session()` (session-end, aspirational contract) is the only path where reality
feeds future cognition. Continuity across restarts: `continuity/continuity_engine.py`.

**Anti-fabrication** is enforced by ~40 `FORBIDDEN` directives in
`runtime/prompt_builder.py` (never invent milestones/versions/causes/bridges), plus
the design choice to store **meaning, not transcripts**.

| Safe to delete (regenerates) | Dangerous — hand-authored / stateful |
|---|---|
| `memory/obsidian_cache.json`, `memory/memory_pack.json`, `memory/embedding_cache.json` | `memory/user_profile.json`, `project_registry.json`, all `*_graph.json` / `viewpoints.json` / `identity_map.json`, `elo_state.json`, `memory/session.json`, everything under `obsidian_vault/09 Memory/` (esp. `SPOT_CODES.md` — append-only coded ledger) |

Footguns: editing `obsidian_vault/` directly (bypasses the loader contract); breaking
YAML frontmatter (`type:`) → note silently skipped; rebuilding the pack without
`invalidate_cache()`; overwriting `elo_state.json`/`session.json` (destroys session
count / emotional history that "Welcome back…" depends on).

Knowledge graphs: `relationships/world_graph.json` = the **fiction** universe (eLo,
Chunk, K-7, Sugarcore); `identity/world_graph.json` = the **product** universe (eLo-OS,
Planet, book, robot). All hand-seeded, cached once per process.

---

## 6. Background loops (daemon threads from `server.py`)

| Loop | Cadence | Writes | Gate |
|---|---|---|---|
| Vision (`tools/vision_loop.py`) | 2s → 6s idle | `blender_state.json["vision"]` | `ELO_VISION=true`; macOS screen-record perm |
| Spotify poll (`tools/spotify_agent.py`) | 4s | `["spotify"]` | Web creds present |
| Ambient thoughts (`ambient/ambient_engine.py`) | 2–4 min | idle self-talk | — |
| Project knowledge (`tools/project_knowledge.py`) | 300s | connection stream | — |

Don't spawn duplicates (loops guard on `is_alive()`); all state writes still go through
`state_writer.patch`. These burn OpenAI/Gemini/Spotify quota — be aware before enabling.

---

## 7. Tools & plugins

`tools/tool_router.py` `enrich()` sits between `server.py` and the LLM — it prepends a
`[CONTEXT: …]` line, never mutates kernel/identity. Reflex (no LLM): time, calculator,
lore, nav, game-entry, browser visibility. LLM-triggered data agents: weather, search,
news, github, calendar, reminders, messages, image_gen, etc. Side-effecting agents
(`system_agent`, `computer_control_agent` [opt-in `ELO_COMPUTER_CONTROL=1`],
`messages_agent`, `vault_writer`, `truth_sync`) are **confirm-gated** via
`runtime/router/execution_gate.py` — don't bypass the gate.

Plugins (`plugins/registry.py`, `base.py`): safety-enforced (`KERNEL_SAFE`, layer∈
output/input/observability). Live: anthropic (Claude), local_llm (Ollama). **Stubs:**
voice, vision, hardware/robot. Keys all in `.env` (GROQ, CEREBRAS, OPENAI, GOOGLE,
ELEVENLABS, ACCUWEATHER, SERPAPI, SPOTIFY). Dashboard (`dashboard/`) is read-only SSE.

---

## 8. What is FROZEN — never edit

- `runtime/executive.py` and everything in `prompts/` — **FREEZE_V1_LOCK**
  (`FREEZE_V1_LOCK.md`, active since 2026-06-29). Unlock requires a logged reason.
- Kernel = the 9-action CAL Executive; routing + StateBus frozen at v1.0
  (`VERSIONING.md`; MAJOR bump required for any routing change).
- **Wrap, don't modify.** Infrastructure evolves *around* the frozen core.

Architecture Constants every review checks: **One Brain · One Executive · Faculties
observe / Executive decides / Embodiment executes · Silence is valid output · Evidence
gates expansion · Freeze is permanent.**

---

## 9. Current status (from the governance sweep)

- **Version:** v1.0.0, architecture frozen (`TRACKER.md`, session 17, 2026-07-22).
- **Phases:** 0 & 1 FROZEN; **Phase 2 (Cognitive Infrastructure) REVIEW→FREEZE**; 2.5
  playbook-ready but validations **not run**; 3 / 3.5 architecture-only; 6 & 8 partial
  (Desktop Buddy + voice live).
- **Work packages** (`engineering/work_packages/`, `proofs/`): all at gap-analysis /
  review stage, **none frozen**. ⚠️ **WP_D (Memory)** and **WP_H (Spine)** carry
  **HIGH-severity unresolved gaps** — treat memory + spine as not-yet-proven.
- **Canon:** Volume V drafted (10 ch + `CONTRACTS.md`); `16_spine_runtime.md` +
  `17_memory_update.md` drafted; 5 volumes (XXIII–XXVII) still unnamed. See
  `docs/architecture/00_CANON_INDEX.md`.

---

## 10. Golden rules for any co-working agent

1. Don't touch `runtime/executive.py` or `prompts/` (FREEZE_V1_LOCK).
2. Don't call `_process_turn` concurrently — the whole turn holds one lock.
3. Never raw-write `blender_state.json` — go through `state_writer` (read-merge-write).
4. Never send `JawOpening`; keep the `eLo_*` clip + mood alias tables in sync with Unity.
5. Don't edit `obsidian_vault/` directly or hand-edit `SPOT_CODES.md`.
6. `contracts.py` is target-state, not runtime — verify before assuming.
7. No implementation before the prior phase's validation passes (evidence gates).
8. Stay on your side of the boundary: OS decides what; Unity renders how.
9. Preserve David's South London / patois register end-to-end — never strip it.
10. When specs and code disagree, the canon in `docs/architecture/` is the intent — but
    say so and reconcile; don't silently diverge.

---

*Generated by the Architecture Agent from a full repo sweep, 2026-07-27.*
*Companion to: `README`(none at root — see `engineering/README.md`), `TRACKER.md`,
`docs/architecture/00_CANON_INDEX.md`, `docs/architecture/16_runtime_contracts.md`,
`handovers/EloOS_Wiring_Spec.md`.*
