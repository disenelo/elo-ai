# WP_B — Gap Analysis

**Status:** COMPLETE — Current Reality Review passed 2026-07-12
**Next stage:** Implementation Plan
**Proof document:** `engineering/proofs/00_one_brain_proof.md`

---

## What the architecture expects vs. what exists

| Architecture Expectation | Current Reality | Gap? |
|---|---|---|
| Executive is sole decision-maker | ✓ Main path only — ambient engine bypasses | 🔴 GAP |
| One CognitivePlan per turn | ✓ Main path — ambient has no plan | 🔴 GAP |
| One LLM call per turn | ✓ Only router_route() at server.py:978 | ✓ Match |
| All pre-spine bypasses use fixed pools | ✓ 6 interceptors, all use pools | ✓ Match |
| blender_state.json owned by one writer | 4 concurrent writers, no coordination | 🔴 GAP |
| No duplicate intent classification | intent_engine.py dead code / tool_router canonical | ⚠️ Debt |
| All faculty contributions, never decide | ✓ Confirmed | ✓ Match |
| Embodiments removable without cognitive impact | ✓ Confirmed for all 5 embodiments | ✓ Match |
| No faculty generates LLM responses | ✓ Confirmed | ✓ Match |
| tool_enrich adds context only | ✓ Confirmed | ✓ Match |
| FREEZE_V1_LOCK respected | ✓ Confirmed | ✓ Match |

---

## Gaps requiring implementation

### GAP 1 — Ambient speech authority (🔴 HIGH)

**What architecture expects:** Every speech act originates from Executive authority. Background services do not produce user-facing output independently.

**What exists:** `ambient/ambient_engine.py` calls `_speak()` directly from a background thread using `_STARTUP_LINES` and `_AMBIENT_LINES` pools. No Executive, no CognitivePlan, no spine.

**Two valid resolutions:**

**Option A — Route through Executive (full compliance)**
- Ambient engine posts an "ambient intent" event to a queue
- Server processes queue between turns, runs a lightweight spine pass
- Executive decides whether to speak and what from the pool
- More complex, adds latency between ambient impulse and delivery

**Option B — Formal exception (pragmatic)**
- Designate ambient engine as a permitted speech exception (alongside pre-spine interceptors)
- Freeze its speech pools (no LLM, fixed content only)
- Document in architecture: "Ambient engine speech is a presence layer, not a cognitive layer"
- Update Invariant 01 and 09 to reflect the exception
- Simpler, preserves current UX

**Recommendation:** Option B. Ambient speech is by definition not cognitive — it is presence maintenance, not a response to the user. The One Brain principle applies to response cognition. Ambient is a separate concern.

---

### GAP 2 — blender_state.json concurrent writes (🔴 HIGH)

**What architecture expects:** blender_state.json written atomically by one owner.

**What exists:** 4 writers — main server thread, ambient engine thread, vision loop thread, spotify poll thread — all writing to the same file without coordination. Main thread uses atomic replace; background threads do not.

**Specific risk:** Ambient engine uses read-modify-write (`_patch_state`). If main thread writes between ambient's read and write, ambient's write overwrites main's changes. Same risk with vision and spotify.

**Resolution — Shared file lock:**
- Create a `threading.Lock()` in a shared module (e.g. `blender_bridge/state_writer.py`)
- All writers acquire this lock before read-modify-write
- Main thread already uses atomic write — add lock acquisition before the write
- Ambient, vision, spotify patch functions acquire same lock

**Implementation scope:** 3–4 files — state_writer.py, ambient_engine.py, vision_loop.py, spotify_agent.py.

---

### GAP 3 — Router pipeline dead code (⚠️ MEDIUM)

**What exists:** `runtime/router/pipeline.py`, `intent_engine.py`, `confidence_engine.py`, `context_matrix.py`, `conversation_matrix.py`, `meaning_engine.py`, `typo_engine.py`, `agent_router.py`, `learning_buffer.py` — a full router pipeline that is never called from `server.py`.

**Risk:** If anyone adds a call to `pipeline.run()` without knowing it's dead code, a second decision path is created. Intent classification would then happen in two places.

**What the spine actually uses:** `intent_engine.detect()` IS called from `runtime/spine/spine.py` — so intent_engine is not fully dead, just the full pipeline is.

**Resolution options:**

**Option A — Formally integrate:** Call `pipeline.run()` in server.py before spine, pass result into spine. This makes the full pipeline live.

**Option B — Clean dead code:** Remove `pipeline.py`, `confidence_engine.py`, `context_matrix.py`, etc. Keep `intent_engine.py` (used by spine). Document that intent_engine is canonical and tool_router is the tool-routing layer.

**Recommendation:** Option B. The spine already uses intent_engine directly. The pipeline wrapper adds orchestration overhead without benefit. Keep intent_engine, remove the pipeline wrapper files.

---

## What already satisfies the architecture (no implementation needed)

- Main request-response path: One Brain compliant
- Executive authority in main path: Clean
- All pre-spine interceptors: Compliant
- Faculty authority model: Clean
- Embodiment removability: Confirmed
- Data ownership for session state and memory: Clean
- tool_enrich context-only contract: Confirmed
- FREEZE_V1_LOCK: Respected

---

## Implementation priority order

1. **GAP 2 first** — concurrent writes are a live data corruption risk. Implement shared file lock.
2. **GAP 1 second** — resolve ambient speech authority (Option B: formal exception, freeze pools).
3. **GAP 3 last** — dead code cleanup. Lower risk, but creates clarity for future WPs.

---

## Invariants that unblock after gaps are resolved

| Invariant | Status Now | Status After Gaps |
|---|---|---|
| 01 — Executive is sole decision-maker | ⚠️ PARTIAL | ✓ (after GAP 1 resolved) |
| 09 — Every response from one CognitivePlan | ⚠️ PARTIAL | ✓ (after GAP 1 resolved) |
| 12 — blender_state.json atomic writes | ⚠️ PARTIAL | ✓ (after GAP 2 resolved) |

After all three gaps are resolved: **12/15 invariants confirmed**. Invariant 11 (memory update once) deferred to WP_D. Two invariants deferred to later WPs. Freeze threshold reached.
