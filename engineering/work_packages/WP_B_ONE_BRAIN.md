# WP_B — One Brain Validation & Architectural Trace

**Status:** NEXT — pending WP_A completion
**Priority:** CRITICAL
**Depends On:** WP_A
**Architecture Reference:** `docs/architecture/01_one_brain.md`
**Freeze Reference:** `FREEZE.md`, `FREEZE_V1_LOCK.md`
**Proof Output:** `proofs/00_one_brain_proof.md`

---

## Purpose

Prove that the entire runtime is one cognition. Not "does it work?" — that is the wrong question.

The question is: **can we prove every thought originates from one cognition?**

That changes what this work package is. WP_B is not an improvement phase. It is an investigation.

If this passes, every future work package builds on a verified foundation rather than assumptions. Instead of asking "does this faculty work?", WP_C through WP_I each ask "does this faculty behave consistently with the One Brain map?" That is a much smaller, more precise question.

---

## The Ten Deliverables

WP_B is structured as ten deliverables. Each produces a concrete output artifact. The phase does not freeze until all ten are complete and the Freeze Report scores pass.

---

## Deliverable 1 — Complete Cognitive Trace

**Artifact:** `proofs/00_one_brain_proof.md` § Trace

Not conceptually. **Literally.**

Trace one message through the complete runtime. Every function. Every object. Every file. Every runtime object.

```
User input
    ↓
server.py — _process_turn()
    ↓  [pre-spine interceptors]
    │   loop guard     → returns fixed string if 3+ identical consecutive messages
    │   farewell pool  → _FAREWELL_POOL_SOUTH_LDN if "safe" / departure phrase
    │   anim commands  → _ANIM_CMD_MAP match → _ANIM_REPLIES pool
    │   scale commands → _SCALE_CMD_RE match → _SCALE_REPLIES_* pool
    │   invade command → _INVADE_RE match → _INVADE_REPLIES pool
    │   multilingual   → _LANGUAGE_GREETINGS table lookup
    ↓
attn.compute()          — Attention Faculty
    │   intent weight, valence, momentum
    ↓
exec_decide()           — Executive (first pass — attention only)
    ↓
_spine_run()            — Spine
    ↓  [Faculty collection — contributes, never decides]
    │   Language Faculty    — intent, register, meaning, typo-correction
    │   Memory Faculty      — vault context, user profile, session continuity
    │   Attention Faculty   — focus, momentum, priority (already computed)
    │   Relationship Faculty — relational context, familiarity
    │   Capability Faculty  — available tools, health status
    │   Executive Faculty   — DECIDES: CAL action, tone, max_sentences, mode, register
    │   Conversation Faculty — direct_response pool selection (if applicable)
    ↓
CognitivePlan           — the single output object of the spine
    ↓
g_ctx assembly          — [CREATOR], continuity, relationship, shadow, avatar note,
                          connection surface, project knowledge, [ANTI-ANCHOR]
    ↓
build_prompt()          — system prompt construction from CognitivePlan + g_ctx
    ↓
_tool_enrich()          — data agents if intent matched (news, weather, search)
    │   prepends [CONTEXT: ...] to user message
    │   does NOT select response — only adds context
    ↓
router_route()          — LLM backend call
    │   primary: GPT-4o-mini → Claude → Groq → Ollama → Mock
    ↓
normalise()             — sentence cap, paragraph preservation
    ↓
multi-bubble split      — response → bubbles[] on \n\n boundary
    ↓
_voice_speak()          — TTS (first bubble only, capped at 280 chars)
    ↓
_write_blender_state()  — atomic write to blender_state.json via .tmp + os.replace()
    ↓
return JSON             — {response, bubbles, mode, backend, command?}
    ↓
[Embodiment delivery — parallel, independent]
    DISENELO Presence   — EloOSProcess.cs → OnReply per bubble, 0.5s delay
    EloOSAvatarReceiver — reads blender_state.json → animation state
    Robot (future)      — reads blender_state.json → NeoPixel + servo
    Terminal            — direct JSON print
    ↓
Memory update           — session continuity, relationship faculty, vault (if applicable)
```

**Audit questions:**
- Does any hop pass a different object than what the next hop expects?
- Is there any hop where an object is mutated by something other than the documented writer?
- Are there any hops not in this diagram?

**Pass criteria:** Complete hop-by-hop map. No undocumented hops. No undocumented mutations.

---

## Deliverable 2 — Duplication Audit

**Artifact:** `proofs/00_one_brain_proof.md` § Duplication

**Question:** Does another faculty already do this?

Ask this for every responsibility in the runtime.

This is the highest-risk deliverable. Duplication means two modules can reach different conclusions from the same input. That violates One Brain.

**Search for duplicated logic across:**

| Logic Type | Expected Location | Check These Files |
|---|---|---|
| Intent classification | `runtime/router/intent_engine.py` | Also: `tools/tool_router.py` `_INTENT_MAP` |
| News/tool routing | `runtime/router/intent_engine.py` | Also: `tools/tool_router.py` |
| Confidence scoring | `runtime/router/pipeline.py` | Also: `tools/tool_router.py` |
| Conversation action (CAL) | `runtime/executive.py` | Any other location? |
| Context assembly (g_ctx) | `server.py` — `_process_turn()` | Any other location? |
| Memory lookup | `memory/` | Also: `continuity/`, `runtime/spine/`? |
| Capability lookup | `runtime/capabilities/registry.py` | Also: `tools/tool_router.py`? |
| Register detection | `runtime/router/intent_engine.py` | Also: `runtime/executive.py`? |

**Known duplication requiring resolution:**

`tools/tool_router.py` contains its own `_INTENT_MAP` with news, weather, search, and other agent patterns. `runtime/router/intent_engine.py` contains overlapping patterns. If both fire on the same input and reach different conclusions, there is no single cognitive decision — there are two competing answers.

**Duplication audit questions:**
- Can the same input produce two different intent classifications from different parts of the code?
- If `intent_engine.py` says "conversation" and `tool_router.py`'s `_INTENT_MAP` says "news" — which wins?
- Is there dead code in either file that the other has superseded?

**Pass criteria:** Every logic type lives in exactly one canonical location. Duplicates are removed or one is formally designated canonical and the other is a thin wrapper that defers to it.

---

## Deliverable 3 — Authority Audit

**Artifact:** `proofs/00_one_brain_proof.md` § Authority

**Question:** Who owns each decision?

For every runtime object and every faculty: what does it own? What does it explicitly NOT own?

**Authority map — complete faculty ownership:**

| Faculty | Owns | Does NOT Own |
|---|---|---|
| Language | Normalisation, registers, typos, semantics | Intent, planning, routing, conversation |
| Memory | Journal, vault, importance scoring, embeddings | Which facts to surface, when to recall |
| Attention | Focus, momentum, priority | Acting on that priority |
| Relationship | Familiarity, relational context, trust signals | Adjusting tone directly |
| Capability | Available tools, health status | Executing tools, choosing which to run |
| Connection Surface | Session pattern snapshot | Modifying behaviour directly |
| Conversation | Fixed pool selection (direct_response) | Generating new text |
| Executive | Conversation action, tone, max_sentences, mode, register | Gathering data, calling agents |

**Audit method:**

Search `server.py`, `runtime/`, `tools/`, `ambient/`, `presence/` for any `return` that produces a user-facing string without going through `_spine_run()` or one of the documented pre-spine interceptors.

**Permitted pre-spine interceptors — full list:**

| Interceptor | Why Permitted | Pool |
|---|---|---|
| Loop guard | Safety — prevents infinite loops | Fixed string |
| Farewell | Speed — no LLM needed for "safe" | `_FAREWELL_POOL_SOUTH_LDN` |
| Anim commands | Speed — direct hardware trigger | `_ANIM_REPLIES` |
| Scale commands | Speed — direct hardware trigger | `_SCALE_REPLIES_*` |
| Invade command | Speed — direct hardware trigger | `_INVADE_REPLIES` |
| Multilingual greetings | Speed — fixed table | `_LANGUAGE_GREETINGS` |
| Ambient engine | Presence — not conversational | Separate ambient pool |

Every other decision path is a violation.

**Pass criteria:** Zero undocumented decision points. Every faculty completes its authority statement. No faculty performs an action reserved for another.

---

## Deliverable 4 — Data Ownership

**Artifact:** `proofs/00_one_brain_proof.md` § Data

**Question:** For every major data structure, who creates it, who mutates it, who reads it, who destroys it?

This is one of the most valuable diagrams in the programme. Data without a clear owner has multiple owners. Multiple owners means multiple decisions.

**Data ownership map — required output:**

| Data Object | Created By | Mutated By | Read By | Destroyed By |
|---|---|---|---|---|
| AttentionSnapshot | Attention Faculty | — (immutable) | Executive, Conversation, Presence | Next runtime cycle |
| CognitivePlan | Spine | — (immutable after creation) | server.py, Presence, Conversation | Next runtime cycle |
| g_ctx (graph context) | `_process_turn()` | — (assembled once) | `build_prompt()` | Next runtime cycle |
| blender_state.json | `_write_blender_state()` | Same (atomic replace) | All embodiments | Never deleted — overwritten |
| user_profile.json | `memory/user_profile.py` | `memory/user_profile.py` | g_ctx assembly, [CREATOR] block | Never |
| session_context | `continuity/session.py` | Same | Spine, g_ctx | Session end |
| vault entries | `memory/vault.py` | `memory/vault.py` | Memory Faculty | Never deleted |
| intent_result | `intent_engine.py` | — (immutable) | Router, Executive, Spine | Next runtime cycle |
| shadow_context | `presence/desktop_shadow.py` | Same | g_ctx assembly | Next runtime cycle |

**Audit questions:**
- Is there any data object mutated by more than one writer?
- Is there any data object read before it is fully written?
- Are there any data objects with no clear owner?

**Pass criteria:** Every major data object has exactly one writer. Every mutation is documented. No object has ambiguous ownership.

---

## Deliverable 5 — Runtime Ownership

**Artifact:** `proofs/00_one_brain_proof.md` § Runtime

**Question:** For every runtime object (processes, threads, loops, singletons), who owns it?

**Runtime ownership map — required output:**

| Runtime Object | Created By | Lifecycle Owner | Communicates Via |
|---|---|---|---|
| server.py (Flask) | Launched by DISENELO Presence or terminal | OS process | HTTP on localhost:5050 |
| Ambient engine thread | `ambient/engine.py` — spawned on startup | server.py | Shared queue / direct call |
| Vision loop thread | `tools/vision_loop.py` — spawned on startup | server.py | Updates blender_state.json |
| TTS thread | `_voice_speak()` — per-turn | server.py | Blocking or threaded? |
| blender_state.json watcher | DISENELO Presence (Unity FileSystemWatcher) | Unity | File system |
| Raspberry Pi reader | Robot script | Robot OS | File system (future) |

**Audit questions:**
- Are there any threads that can outlive their expected lifecycle?
- Is there any shared mutable state between the ambient engine thread and the main server loop?
- Does the vision loop ever write to blender_state.json in a way that conflicts with `_write_blender_state()`?
- Is there any race condition between the TTS thread and the response return path?

**Pass criteria:** Every runtime object has a documented owner and lifecycle. No undocumented shared state between threads.

---

## Deliverable 6 — One Brain Proof

**Artifact:** `proofs/00_one_brain_proof.md` § Proof

**Question:** Can we disprove the One Brain Principle? If not — prove it.

This is the adversarial deliverable. The approach is to assume eLo does NOT satisfy One Brain and search for evidence.

**Attempt to disprove by finding:**

1. A message path where more than one module reaches an independent decision about the response
2. A message path where the Executive's CognitivePlan is bypassed entirely
3. A faculty that mutates shared state without going through its documented interface
4. An embodiment that receives different cognitive output than another embodiment for the same input
5. A thread that makes a decision (ambient engine, vision loop) without Executive knowledge

**If all five disproofs fail:**

The proof stands. Document it exactly: "We attempted to find evidence that eLo violates One Brain across these five vectors. We found none. The One Brain Principle holds."

**Pass criteria:** All five disproofs attempted. All fail. Proof statement written in `proofs/00_one_brain_proof.md`.

---

## Deliverable 7 — Future Embodiment Check

**Artifact:** `proofs/00_one_brain_proof.md` § Embodiment

**Question:** If we unplug any embodiment — does cognition still work?

Embodiments should be removable. Nothing else changes.

**Check for each active and future embodiment:**

| Embodiment | If unplugged... | Cognition continues? | Notes |
|---|---|---|---|
| Terminal | No /chat calls | Yes — server still runs | |
| DISENELO Presence | App killed | Yes — server still runs | |
| Unity (eLo-Planet) | Project closed | Yes — blender_state.json still written | |
| Robot | Pi disconnected | Yes — blender_state.json still written, Pi not reading | |
| Voice (TTS) | TTS fails | Yes — response still returned, voice silently skipped | |

**Audit questions:**
- Does any faculty require a specific embodiment to be present?
- Does the absence of an embodiment prevent the CognitivePlan from being produced?
- Does the robot disconnecting affect the server's ability to serve other embodiments?
- Does TTS failure block the response JSON from returning?

**Pass criteria:** Every embodiment is provably removable with zero impact on cognition. Absence degrades delivery only — never cognition.

---

## Deliverable 8 — Faculty Dependency Graph

**Artifact:** `proofs/00_one_brain_proof.md` § Graph

**Question:** Does the faculty dependency graph have any loops, cycles, or recursive ownership?

**Expected graph (no cycles):**

```
Language Faculty
    ↓ contributes: intent, register, meaning
Memory Faculty
    ↓ contributes: vault context, user profile, continuity
Attention Faculty
    ↓ contributes: focus, momentum, priority
Relationship Faculty
    ↓ contributes: relational context, familiarity
Capability Faculty
    ↓ contributes: available tools, health
Connection Surface
    ↓ contributes: session pattern snapshot
            ↓
        Executive
            ↓ decides: CognitivePlan
            ↓
        Spine (assembles all the above)
            ↓
        Execution Gate
            ↓
        Presence Faculty (embodies the plan)
```

**Verify:**
- No faculty reads output from a later faculty in the graph
- No faculty calls the Executive
- The Executive does not call any data-gathering function (it reads from what the spine assembled)
- Presence is terminal — it receives the plan, it does not feed back into cognition

**Pass criteria:** Acyclic graph confirmed. No loops. No recursive ownership. Graph artifact written.

---

## Deliverable 9 — Runtime Invariants

**Artifact:** `proofs/00_one_brain_proof.md` § Invariants

**These MUST ALWAYS remain true.**

This is the constitution. Every future work package checks against it.

```
INVARIANT 01: Executive is the only decision-maker.
INVARIANT 02: Language Faculty never makes decisions.
INVARIANT 03: Memory Faculty never makes decisions.
INVARIANT 04: Attention Faculty never acts on its own output.
INVARIANT 05: Capability Faculty never executes tools.
INVARIANT 06: Presence Faculty never changes cognition.
INVARIANT 07: Embodiments never own cognitive state.
INVARIANT 08: Conversation Faculty never generates new response text — only selects from fixed pools.
INVARIANT 09: Every response originates from one CognitivePlan.
INVARIANT 10: Every embodiment executes the same CognitivePlan.
INVARIANT 11: Every runtime cycle updates memory exactly once.
INVARIANT 12: blender_state.json is written atomically (via .tmp + os.replace).
INVARIANT 13: Pre-spine interceptors are speed/safety paths only — fixed pools, no LLM.
INVARIANT 14: Tool enrichment (_tool_enrich) adds context. It never selects response text.
INVARIANT 15: FREEZE_V1_LOCK — runtime/executive.py and prompts/ are never modified.
```

**Pass criteria:** All 15 invariants confirmed in code. Any invariant that cannot be confirmed is an architectural debt item requiring resolution before freeze.

---

## Deliverable 10 — Freeze Report

**Artifact:** `proofs/00_one_brain_proof.md` § Freeze

Not "looks good." A scored report.

```
One Brain Score: ___/100

Strengths:
- ...

Weaknesses:
- ...

Architectural Risks:
- ...

Invariants confirmed: ___/15

Recommendations:
- ...

Freeze decision: YES / NO / CONDITIONAL
```

**Freeze criteria:**

| Criterion | Deliverable | Required |
|---|---|---|
| Complete hop-by-hop runtime map | 1 | ✅ |
| Zero duplicate logic (or canonical designation) | 2 | ✅ |
| Every faculty has complete authority statement | 3 | ✅ |
| Every major data object has documented owner | 4 | ✅ |
| Every runtime object has documented lifecycle | 5 | ✅ |
| Adversarial disproofs all fail | 6 | ✅ |
| All embodiments removable without cognitive impact | 7 | ✅ |
| Faculty dependency graph acyclic | 8 | ✅ |
| All 15 invariants confirmed | 9 | ✅ |
| Regression tests pass | — | ✅ |
| Conversation validation complete | — | ✅ |

**What freezes with WP_B:**

1. The complete runtime flow map (Deliverable 1)
2. The canonical location of each logic type (Deliverable 2)
3. The faculty authority statements (Deliverable 3)
4. The data ownership map (Deliverable 4)
5. The runtime ownership map (Deliverable 5)
6. The One Brain proof statement (Deliverable 6)
7. The embodiment removability contracts (Deliverable 7)
8. The faculty dependency graph (Deliverable 8)
9. The 15 runtime invariants (Deliverable 9)

Any future work package that changes any of the above must amend the freeze document and update `proofs/00_one_brain_proof.md`.

---

## What WP_B Does Not Do

- Does not add new capability
- Does not modify FREEZE_V1_LOCK components
- Does not redesign any faculty
- Does not address behavioural quality across embodiments (that is WP_X)

---

## Known Issues to Resolve

| Issue | Deliverable | Severity |
|---|---|---|
| Dual intent maps (intent_engine + tool_router) | 2 | HIGH |
| `_last_agent` follow-up persistence (can re-fire tool without intent) | 2 | MEDIUM |
| tool_router `enrich()` may produce response without LLM in some paths | 3 | MEDIUM |
| Ambient engine direct speech — permitted exception, must be formally documented | 3 | MEDIUM |
| Vision loop potentially writing blender_state.json concurrently | 5 | MEDIUM |
