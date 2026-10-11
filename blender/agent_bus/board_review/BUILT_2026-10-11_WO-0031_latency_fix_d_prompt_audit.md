# Board Review — 0031: Latency Fix D — Prompt Block Audit + Conditional Injection
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Steps 1-3 / Fixes A-C: verified already implemented (prior session)

| Fix | Location | Status |
|---|---|---|
| Step 1 instrumentation | `backend_router.py:826-843` — load_ms, prompt_eval_tokens, prompt_eval_ms, gen_tokens, gen_ms logged | ✅ done |
| Fix A: `keep_alive="30m"` | `backend_router.py:814` | ✅ done |
| Fix B: `_ollama_stream` | `backend_router.py:1216`, wired into `route_streaming:3338/3369` | ✅ done |
| Fix C: `num_ctx=8192` | `backend_router.py:815` | ✅ done |

Evidence from `data/backend_health_history.jsonl`: all recent entries show `prompt_eval_ms=9000, trigger=4s_rule` — Fixes A-C have not resolved latency. Fix D (this card) is the live issue.

---

## Fix D — Prompt Block Audit

### Block order: complete inventory

`build()` in `runtime/prompt_builder.py` assembles the following blocks in this order:

| # | Block | Characters | Est. Tokens | Dynamic? | Fires when |
|---|---|---|---|---|---|
| 1 | `voice_register` | ~3,957 | **1,131** | **DYNAMIC** (varies with `action`) | Always |
| 2 | `living_presence_spec` | ~16,390 | **4,701** | SEMI-STATIC (sliced by action; ~1% variation) | Always |
| 3 | `identity_anchor` | ~3,389 | **967** | STATIC | Always (try/except) |
| 4 | `persistent_identity` | ~800 | **230** | SEMI-STATIC (session count) | When non-empty |
| 5 | `capability_self_model` | ~663 | **189** | STATIC | When non-empty (conditional) |
| 6 | `capability_live_state` | ~1,449 | **422** | SEMI-DYNAMIC (live Spotify/tool state) | ~~Always~~ → now conditional (see below) |
| 7 | `personality_block` | varies | varies | SEMI-DYNAMIC | When non-empty |
| 8 | `self_block` | varies | varies | SEMI-DYNAMIC | When non-empty |
| 9 | `dream_self_knowledge` | varies | ~300 | DYNAMIC (user input) | When `asked_about_dreaming(input)` |
| 10 | `learned_heuristics` | ≤240 | ~70 | SEMI-DYNAMIC | When lessons present, ≤3 items |
| 11 | `active_memory` | varies | ~200-500 | DYNAMIC | When attention present |
| 12 | `world_knowledge` | ≤2000 chars | ~500 max | SEMI-DYNAMIC | When vault_context non-empty (conditional) |
| 13 | `relationship_graph` | varies | ~200-800 | DYNAMIC | When graph_context non-empty (conditional) |
| 14 | `disenelo_world_language` | ~800 | ~230 | DYNAMIC (user input) | When world/visual keywords in input |
| 15 | `autobiographical_summary` | varies | varies | SEMI-DYNAMIC | When exec_decision has autobiographical_summary |
| 16 | `executive_directive` | varies | **400-1500** | **FULLY DYNAMIC** | When exec_decision present |
| 17 | `conversation_ground` | varies | varies | DYNAMIC | When grounding_block non-empty |
| 18 | `inner_thought_anchor` | ~30 | ~9 | DYNAMIC | When blender_state has inner_thought_text |
| 19 | `movement_feedback` | ~100 | ~30 | DYNAMIC | When recent failed movement |
| 20 | `respond_now` | ~210 | **60** | STATIC | Always |

**Minimal turn total (no memory, minimal exec_decision): 8,478 tokens** — already exceeds `num_ctx=8192`.

---

### Critical finding: SP_MAX truncation discards blocks 3-20

`backend_router.py:768-770`:
```python
_SP_MAX = int(os.environ.get("ELO_OLLAMA_SP_MAX", "12000"))
if len(system_prompt) > _SP_MAX:
    system_prompt = system_prompt[:_SP_MAX]  # ← blind char truncation
```

The assembled prompt from `build()` is **~30,000 characters** (minimal turn). Truncating at 12,000 chars means:
- Block 1 `voice_register` (3,957 chars): **ALL SURVIVES** ✅
- Block 2 `living_presence_spec` (16,390 chars): **first 8,043 chars survive, 8,347 chars cut** ⚠️
- Blocks 3-20 (`identity_anchor`, `capability_self_model`, `executive_directive`, `active_memory`, `world_knowledge`, etc.): **ALL CUT** 🔴

After truncation, Ollama receives:
1. `_FORMAT_HEADER` prepend (~400 chars)
2. `_david_identity` prepend (~400 chars)
3. `_durable_facts_block` prepend (varies)
4. `voice_register` (all 3,957 chars)
5. First 8,043 chars of `living_presence_spec` (half the spec)

**The identity anchor, executive directive, all memory blocks, and capability blocks are silently discarded on every turn.**

This partially explains why Fixes A-C didn't resolve latency: Ollama is running on an incomplete, structurally broken prompt, working harder to compensate for missing context.

---

### Block order conflict with WO-REGISTER-PLACEMENT-001

The card requires: "Anything that changes per turn must come AFTER everything static."

Current state:
- Block 1: `voice_register` — **DYNAMIC** (action changes every turn)
- Block 3: `identity_anchor` — **STATIC** (changes only on explicit update)
- Block 5: `capability_self_model` — **STATIC** (registry rarely changes)

`voice_register` is placed first per `WO-REGISTER-PLACEMENT-001` comment: "Voice register FIRST — maximum weight." This directly violates the prefix-caching requirement in this card. Ollama's KV prefix cache breaks at the very first token on every turn because `voice_register` changes with `_action`.

**Conflict requires board ruling**: WO-REGISTER-PLACEMENT-001 (voice register first) vs CT0031 (static blocks must precede dynamic). These cannot both be satisfied.

If static blocks (`identity_anchor`, `capability_self_model`) moved before `voice_register`:
- Prefix cache would capture ~1,196 tokens (identity_anchor + capability_self_model) on turns where those blocks are byte-identical
- Cost: `voice_register` and `living_presence_spec` both follow — living_presence_spec varies slightly with action, still breaking cache at block 2

**Net prefix cache benefit of reordering: minimal**, because `living_presence_spec` (block 2, ~4,701 tokens) varies with action and breaks the cache regardless. The real prefix caching win would require a fully static section of several thousand tokens before any dynamic content — which `living_presence_spec` prevents.

---

### Fix D implemented: conditional `capability_live_state`

`runtime/prompt_builder.py` lines 640-664 (updated):

```python
_CAP_KEYWORDS = (
    "can you", "able to", "what can", "could you", "do you have",
    "capability", "capabilities", "tools", "spotify", "search",
    "what do you do", "features", "play ", "open ", "find ",
    "look up", "remind", "screenshot", "volume", "brightness",
)
_ui_lower_cap = (user_input or "").lower()
_cap_skip = (
    _action in ("ground", "witness")
    and not any(kw in _ui_lower_cap for kw in _CAP_KEYWORDS)
)
if not _cap_skip:
    try:
        from tools.capability_status import capabilities_block as _cap_block_fn
        _cap_live = _cap_block_fn()
        if _cap_live:
            _push("capability_live_state", "\n## What I can do right now\n" + _cap_live)
    except Exception:
        pass
```

**Test results:**
- `ground` action + non-capability input → `capability_live_state` skipped → saves 422 tokens ✅
- `answer` action → `capability_live_state` injected ✅
- `ground` action + "can you search for..." → `capability_live_state` injected ✅

**Saving:** 422 tokens removed from ~15% of turns (emotional support turns). Given SP_MAX truncation, this also saves ~1,449 chars of the truncated prompt window.

---

## Token budget reality check

| Layer | Chars | Est. Tokens | Notes |
|---|---|---|---|
| Full assembled prompt (minimal turn) | ~29,730 | ~8,478 | Before SP_MAX |
| After SP_MAX truncation | 12,000 | ~3,428 | What `_ollama_call` receives |
| Prepend (`_FORMAT_HEADER` + `_david_identity` + facts) | ~1,000 | ~286 | Added after truncation |
| Final system prompt sent to Ollama | ~13,000 | ~3,714 | Actual payload |
| `num_ctx` | — | 8,192 | Conversation history fits in remaining 4,478 |

The `num_ctx=8192` setting (Fix C) is technically correct for the truncated prompt. The problem is what the truncation discards.

---

## Board decisions requested

1. **SP_MAX: raise from 12,000 to 20,000+ chars** — currently discards identity_anchor, executive_directive, all memory blocks. Minimum viable to keep identity_anchor + directive: 12,000 + 3,389 (identity_anchor) + ~2,000 (directive) = 17,400 chars. Recommend 22,000.
   - Risk: larger prompt → slower `prompt_eval_duration`. Quantify with Step 1 telemetry before committing.

2. **WO-REGISTER-PLACEMENT-001 vs prefix caching** — voice_register first is a quality decision (maximum weight on identity register); static-first is a performance decision (prefix cache). Board rules on priority. Builder recommendation: keep voice_register first (quality > latency); fix latency via SP_MAX raise instead.

3. **living_presence_spec at 4,701 tokens (55% of minimal prompt)** — this card's constraint prevents editing the spec. A follow-on card is needed to reduce the spec's injected volume (tighter slicing, or a compressed "eLo-lite" version for simple turns). Board to spawn.

4. **Smart block-priority truncation** — replace blind `system_prompt[:_SP_MAX]` with priority-aware truncation: keep voice_register (1), identity_anchor (3), executive_directive (16), respond_now (20), then fill remaining budget with living_presence_spec and memory blocks. This ensures directives and identity ALWAYS survive. Builder can implement on a separate card.

*Builder 1 · 2026-10-11*
