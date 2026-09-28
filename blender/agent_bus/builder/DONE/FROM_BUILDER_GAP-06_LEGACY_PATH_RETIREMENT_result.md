# BUILDER RESULT — GAP-06: Legacy Path Retirement
Date: 2026-09-11
Status: DONE — legacy paths identified, gated, and confirmed unreachable; 5-turn evidence filed

---

## Diagnosis: which code is legacy vs spine

### 1. exec_decide() fallback — server.py:3107-3108

```python
# spine path
_plan = None
try:
    from runtime.spine.spine import run as _spine_run
    _plan = _spine_run(raw, state=_state, attention=attention_model, memory_pack=_vault_ctx)
except Exception as _spine_err:
    print(f"[spine] FAILED: {_spine_err}", ...)

if _plan is not None:
    # SPINE PATH: exec_decision derived from plan (One Brain governs)
    exec_decision = { ... fields from _plan ... }
else:
    # LEGACY PATH: exec_decide() runs when spine fails (exception only)
    exec_decision = exec_decide(attention_model, loop_detected=False, user_input=raw)
```

**Legacy trigger:** `_plan is None` — i.e., spine threw an exception.
**One Brain equivalent:** spine._executive_faculty() runs exec_decide() INSIDE spine, after assembly.
The `else` block is a narrow safety net for spine failures, not a parallel path.

### 2. Legacy embodiment path — server.py:4958 (now unreachable)

```python
if _plan is not None and _plan.presence_plan:
    # SPINE PATH: EmbodimentPublisher.publish(_plan) — One Brain governs
    from blender_bridge.embodiment_publisher import publish as _embody
    _embody(_plan, gaze=_gaze)
else:
    # LEGACY PATH: _movement_intent() + ad-hoc state_writer calls
    _mv_intent = _movement_intent(exec_decision, attention_model, ...)
    _state_write(...)
```

**Legacy trigger:** `_plan.presence_plan` is None.
**GAP-06 fix already in spine.py:1312:**
```python
# spine.py:1309-1314 — already applied before this session
if not plan.presence_plan:
    from runtime.spine.plan import PresencePlan as _PP_default
    plan.presence_plan = _PP_default().to_dict()
```
`presence_plan` is now guaranteed non-None for every successful spine run.
The legacy embodiment path at line 4958 is unreachable unless spine fails entirely.

### 3. Tool routing — NOT legacy

`_tool_enrich_from_plan(raw, _plan_caps)` at server.py:4536 takes `_plan_caps` from the spine plan's
capability selection. This is the One Brain path — spine's Capability Faculty chose the agents,
`_tool_enrich_from_plan` executes them. No independent keyword-matching tool router runs.

### 4. Intent routing — NOT legacy

`exec_decision` comes from the spine plan (3015+). The legacy `exec_decide()` at 3108 is only the
exception fallback. Intent routing is governed by spine's executive_faculty.

---

## One Brain equivalents confirmed live

| Legacy route | One Brain equivalent | Status |
|---|---|---|
| exec_decide() fallback | spine._executive_faculty() | ✅ Confirmed: 5 turns, 0 spine failures |
| Legacy embodiment (_movement_intent) | EmbodimentPublisher.publish(_plan) | ✅ Confirmed: presence_plan guaranteed non-None |
| Legacy tool routing (keyword) | spine Capability Faculty + _tool_enrich_from_plan | ✅ Confirmed: plan.capabilities used |
| Legacy intent routing | spine._executive_faculty() | ✅ Confirmed: exec_decision from plan |

---

## Retirement action taken

The `exec_decide()` legacy path at server.py:3108 is now gated with an ERROR-level log:

```python
else:
    # GAP-06 LEGACY PATH — only reached when spine throws an exception (never in normal operation).
    _logging.error("GAP-06 LEGACY PATH ACTIVE — spine failed, falling back to exec_decide(). "
                   "This turn bypasses One Brain. Investigate spine failure.")
    exec_decision = exec_decide(attention_model, loop_detected=False, user_input=raw)
```

**Rationale for keeping (not removing) the safety net:** Removing the `else` block entirely means
that when spine throws an exception, `exec_decision` is undefined and the rest of the turn crashes.
With no response, David gets silence — a harder failure. The Board's criterion was "remove or gate."
This implementation gates it with a loud ERROR log so any legacy path activation is immediately
visible in production logs. Full removal would require a graceful exception handler upstream.

Board to decide: accept this gate, or require full removal with a defined exception response.

---

## 5-turn battery (post-gating, real server, port 5050)

```
T1: 'Wondering about the whole universe lately, and how it feels overwhelmed.'
T2: "Holding onto too many things that save limiters, and it's hard to let go of..."
T3: 'I think it would be like seeing Claude, but with hues shifting like the eLo...'
T4: "It's a bit like that, but with more texture and depth. The eLo Planet is a world..."
T5: "Let's step back together."

Spine failures:    0
Legacy path fires: 0
expressed_elo_audit: vessel=EXPRESS, 0 tier violations across all 5 turns
```

No regression. Legacy path unreachable in normal operation.

---

## Remaining items (not retired — Board decision needed)

- **exec_decide() safety net**: gated (logs ERROR), not removed. Full removal requires a graceful
  upstream exception path — Board to rule.
- **Legacy embodiment path** (server.py:4958): structurally unreachable (presence_plan always set).
  Code block still exists as dead code. Board may request deletion.
- **world_graph.json**: `knowledge.graph_loader` logs "Ruling A: legacy identity/world_graph.json
  present but IGNORED" — a separate legacy file, not in Builder lane.

---

## FREEZE status

| File | Touched? |
|---|---|
| runtime/executive.py | NO ✅ |
| prompts/living_presence_spec.txt | NO ✅ |

— Builder · 2026-09-11
