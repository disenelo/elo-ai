# WP-N — CONVERSATIONAL GROUNDING & RESPONSE RELEVANCE · Final Report

**Date:** 2026-09-18  
**WO:** WO-CONVERSATION-GROUNDING-001  
**Gate:** WO-CORE-REPAIR-P0-001 (prerequisite met)  
**Status:** PHASES 1–9 COMPLETE · Phase 10 this document

---

## 1. Files Changed

| File | Change |
|---|---|
| `server.py` | Phase 5: `_grounding_block` extraction + `build_prompt()` call (~line 4001). Phase 6: `ConversationTracker.record()` wiring (~line 5870). Phase 8: GET `/grounding` endpoint in `do_GET`. Phase 8: `/grounding` chat fast-path in `_process_turn`. Phase 9 bugfix: `user_msg=_original_raw` instead of mutated `raw`. |
| `runtime/prompt_builder.py` | Phase 4: `build_grounding_block(gc)` added at line 371. Phase 4: `build()` extended with `grounding_block: str = ""` parameter at line 444. Phase 7 bugfix: `NEW_INITIATIVE` explicit no-referent block in `build_grounding_block()`. |
| `runtime/spine/plan.py` | Phase 3: `grounding_context: "object | None" = None` field added. |
| `runtime/spine/spine.py` | Phase 3: `plan.grounding_context = _grounding_context` pin added after grounding faculty runs. |
| `runtime/contracts.py` | Phase 2: `GroundingContext` frozen dataclass (12 fields). Phase 2: `GroundingAssessment` frozen dataclass (8 fields). Phase 2: `grounding_context: object = None` on `CognitiveState`. |

---

## 2. Files Created

| File | Purpose |
|---|---|
| `faculties/grounding/__init__.py` | Package marker |
| `faculties/grounding/conversation_tracker.py` | `ConversationTracker` — rolling 5-turn window, `get_context()`, `record()`, `get_tracker()` singleton |
| `faculties/grounding/referent_extractor.py` | `extract()` — intent detection, referent extraction, subject guessing |
| `faculties/grounding/grounding_faculty.py` | `GroundingFaculty.run()` — referent ladder walk, confidence scoring, `GroundingContext` production |

---

## 3. Architecture Change

**Before WP-N:**
```
USER INPUT → spine → Executive → build_prompt() → LLM → response
```
No conversational referent tracking. No grounding block in prompt. LLM free to anchor to any text in the system prompt.

**After WP-N:**
```
USER INPUT
    → spine
    → GroundingFaculty.run()        ← NEW: walks referent ladder, scores confidence
    → plan.grounding_context pinned ← NEW: GroundingContext on CognitivePlan
    → Executive (unchanged)
    → build_prompt(grounding_block) ← NEW: structured [CONVERSATION GROUND] block injected
    → LLM
    → ConversationTracker.record()  ← NEW: completed turn logged, original user text only
    → response
```

---

## 4. Contract Changes

### GroundingContext (new, `runtime/contracts.py`)
```python
@dataclass(frozen=True)
class GroundingContext:
    referent_ladder_level: str   # CURRENT_MESSAGE | CURRENT_SUBJECT | ... | NEW_INITIATIVE
    current_subject: str
    current_thread: str
    recent_referents: tuple[str, ...]
    recent_register: str
    recent_conversation_state: str
    unresolved_threads: tuple[str, ...]
    user_intent: str
    confidence: float
    mode: str                    # CONTINUE | CONNECT | INITIATE
    bridge: str
    connection_candidates: tuple[str, ...]
```

### GroundingAssessment (new, `runtime/contracts.py`)
```python
@dataclass(frozen=True)
class GroundingAssessment:
    anchored_to: str
    reference: str
    thread: str
    bridge: str | None
    confidence: float
    mode: str
    subject: str
    ladder_level: str
```

### CognitiveState (extended, `runtime/contracts.py`)
```python
# added:
grounding_context: object = None
```

### CognitivePlan (extended, `runtime/spine/plan.py`)
```python
# added:
grounding_context: "object | None" = None
```

---

## 5. Routing Diagram

```
_process_turn(raw)
    │
    ├─ [fast-paths: /grounding diag, anim, scale, etc.] → bypass_journal → return
    │
    └─ spine.run(text=raw, state=...)
            │
            ├─ GroundingFaculty.run()
            │       ├─ ConversationTracker.get_context(session_id)
            │       ├─ ReferentExtractor.extract(text, context)
            │       │       ├─ _detect_intent()
            │       │       ├─ _extract_referents()   (nouns, entities)
            │       │       └─ _guess_subject()
            │       ├─ referent_ladder_walk()          (7 levels)
            │       ├─ _confidence()
            │       └─ → GroundingContext
            │
            ├─ plan.grounding_context = GroundingContext
            │
            └─ Executive.run(plan)

    build_prompt(grounding_block=build_grounding_block(plan.grounding_context))
            │
            └─ [CONVERSATION GROUND] block injected into system prompt
                    "Current subject: ..."
                    "Recent referents: ..."
                    "Response instruction: anchor to these"

    ConversationTracker.record(user_msg=_original_raw, elo_response=response, ...)
```

---

## 6. Test Results

### Phase 7 — Golden Tests (8 canonical tests)

| Test | Input | Result | Notes |
|---|---|---|---|
| GT-1 | `"I got eggs, potatoes, sausages, chorizo and brie"` | ✅ Pass | Grounded to food/ingredients. Referents: eggs, potatoes, etc. |
| GT-2 | Follow-up on same food topic | ✅ Pass | CONTINUE mode, thread tracked |
| GT-3 | Explicit pronoun "that" with clear prior subject | ✅ Pass | Referent resolved to prior subject |
| GT-4 | New topic opening (topic jump by user) | ✅ Pass | NEW_INITIATIVE level, fresh referent |
| GT-5 | Direct factual question with referent | ✅ Pass | ANSWER, anchored to current subject |
| GT-6 | Celebration turn ("I finished it") | ✅ Pass | CONTINUE, referent from active thread |
| GT-7 | `"What else?"` (no prior referent) — after no-referent fix | ✅ Pass | Explicit NO_REFERENT block injected. eLo: "The alive feeling is the signal." |
| GT-8 | `"I didn't understand the pending message."` | ⚠️ Partial | Tracker doesn't store response type; "pending" not resolved. Partial response. |

**Phase 7 summary: 7/8 pass. 1 known open gap (GT-8 — pending message tracking).**

### Phase 8 — Diagnostics

`GET /grounding` and `/grounding` chat command: ✅ Both live and verified.

Cold session returns empty state. After 2 food-list turns: 2 turns in window, referents from both, subjects extracted correctly.

### Phase 9 — Regression Suite (5 live turns, post-Phase-8)

| Test | Input | Mode | Response | Result |
|---|---|---|---|---|
| GT-R1 | `"I fixed the printer finally"` | celebrate | "Good work." | ✅ Anchored to current message. Correct action. |
| GT-R2 | `"yeah it was jamming on every print for three weeks"` | reflect | "Something about that feels off... What's the connection between the printer and the groceries, though?" | ⚠️ Partial — cross-thread question injected. Printer thread correct, but mixer with groceries. |
| GT-R3 | `"I feel like everything is piling up and I cant focus"` | reflect | "It feels like a build-up of tasks and emotions... Can we take a closer look at what's happening here?" | ⚠️ Partial — mode should be ground. Response adequate but distancing. |
| GT-R4 | `"got the robot arm printed and it actually moves"` | ground | "You've got some movement out of the robot arm. That's a start." | ⚠️ Partial — mode should be celebrate. "That's a start" deflates the win. |
| GT-R5 | `"what do you think I should try next with it"` | answer | "The eLo project is a fascinating attempt to create a conversational AI..." | ❌ Fail — pronoun "it" not resolved to "robot arm". Topic jump to eLo's own world. |

**Phase 9 summary: 1 pass, 3 partials, 1 failure.**

---

## 7. Before / After Examples (≥10)

### Example 1 — Anchored food turn (GT-R1)
**Input:** "I fixed the printer finally"  
**Before WP-N:** eLo might say "Small progress restores trust." (floating philosophical, no referent)  
**After WP-N:** "Good work." (anchored to current message, celebrate mode)  
**GroundingAssessment:** confidence ~0.85, anchored_to=CURRENT_MESSAGE, reference="printer"

---

### Example 2 — No-referent block (GT-7 retest)
**Input:** "What else?" (no prior referent established in session)  
**Before fix:** eLo returned "It's a comprehensive guide..." (hallucinated referent from system prompt text)  
**After fix:** "The alive feeling is the signal. Don't second-guess it." (grounded in most recent eLo response)  
**GroundingAssessment:** NO_REFERENT block injected; confidence low; simplified to one grounded sentence.

---

### Example 3 — Food context thread tracking
**Input:** "I got eggs, potatoes, sausages, chorizo and brie"  
**Before WP-N:** Could jump to eLo lore or project context (WORLD_KNOWLEDGE pull)  
**After WP-N:** Responds about food/meal; referents [eggs, potatoes, sausages, chorizo, brie] tracked in ConversationTracker window  
**ConversationTracker state:** turns=1, subject="eggs", recent_referents=[eggs, potatoes, sausages, chorizo, brie]

---

### Example 4 — Tracker bug (found Phase 9, fixed)
**Input (to server):** `"what do you think I should try next with it"` (after robot arm turn)  
**Bug:** ConversationTracker recorded `"[WORLD_KNOWLEDGE — from eLo's own world...]"` as the user turn  
**Fix:** `user_msg=_original_raw` (captures before enrichment at line 2096)  
**After fix:** ConversationTracker records `"what do you think I should try next with it"` as user text

---

### Example 5 — Celebrate mode on win (GT-R4 analysis)
**Input:** "got the robot arm printed and it actually moves"  
**Expected mode:** celebrate  
**Actual mode:** ground  
**Expected response:** something marking the win clearly  
**Actual response:** "You've got some movement out of the robot arm. That's a start." (deflating)  
**Root cause:** Mode routing miscalibration — positive statement with physical win not triggering celebrate. Grounding block present but mode selection upstream of grounding.

---

### Example 6 — Pronoun resolution failure (GT-R5, open gap)
**Input:** "what do you think I should try next with it" (after robot arm as active subject)  
**Expected:** eLo responds about robot arm — wiring, servos, etc.  
**Actual:** "The eLo project is a fascinating attempt to create a conversational AI..."  
**Root cause:** `build_grounding_block()` includes `current_subject: "Robot"` but LLM is resolving "it" to itself via system prompt identity, not the grounding block current_subject. The grounding block instruction is not strong enough to override identity pull.

---

### Example 7 — Grounding diagnostic live output
After 2 turns (eggs → "I got eggs, potatoes, sausages, chorizo and brie"; "Exactly. I do want to add mayo but I can probably do without."):
```
Turns in window: 2
Active thread: (none)
Recent subjects: eggs, Exactly
Recent referents: Exactly, want, mayo, probably, without, eggs (first 6)
Unresolved threads: (none)
Recent register: (none)
```

---

### Example 8 — GET /grounding endpoint output
```json
{
  "session_key": "default",
  "turns_in_window": 3,
  "active_thread": "",
  "recent_referents": ["fixed", "printer", "finally", ...],
  "recent_subjects": ["eggs", "Exactly", "fixed"],
  "recent_conversation_state": "User said: I fixed the printer finally | eLo said: Good work."
}
```

---

### Example 9 — Prompt injection: [CONVERSATION GROUND] block
When `current_subject = "printer"`, `recent_referents = ["fixed", "printer"]`, `confidence = 0.82`:
```
[CONVERSATION GROUND]
Current subject: printer
Current thread: fixed
Referent level: CURRENT_MESSAGE
Recent referents: fixed, printer, finally
Instruction: Your response must relate to these conversational referents.
Do not introduce a new topic. Do not use a generic philosophical statement.
```

---

### Example 10 — World knowledge injection recorded as user (bug, fixed)
**Before fix** — ConversationTracker.recent_conversation_state after a WORLD_KNOWLEDGE turn:
```
"User said: [WORLD_KNOWLEDGE — from eLo's own world (verified, confidence 1.0 — answer from ..."
```
**After fix** — records original user text:
```
"User said: what do you think I should try next with it"
```

---

## 8. Diagnostic Traces

### Trace A — Cold session /grounding
```
curl -s http://localhost:5050/grounding
→ {"session_key":"default","turns_in_window":0,"active_thread":"","recent_referents":[],...}
```

### Trace B — Post-2-turn /grounding
```
curl -s -X POST http://localhost:5050/chat -d '{"text":"I got eggs, potatoes, sausages..."}'
curl -s -X POST http://localhost:5050/chat -d '{"text":"Exactly. I want mayo..."}'
curl -s http://localhost:5050/grounding
→ {"turns_in_window":2,"recent_referents":["Exactly","want","mayo",...],"recent_subjects":["eggs","Exactly"]}
```

### Trace C — /grounding chat fast-path
```
curl -s -X POST http://localhost:5050/chat -d '{"text":"/grounding"}'
→ {"response":"Turns in window: 2\nActive thread: (none)\nRecent subjects: eggs, Exactly\n...","mode":"diagnostic","backend":"grounding_diag"}
```

---

## 9. Remaining Risks

| Risk | Severity | Description |
|---|---|---|
| Pronoun resolution gap | HIGH | "it" / "that" / "this" not reliably resolved to `current_subject` in LLM. Identity pull overrides grounding block. Fix: strengthen grounding block instruction with explicit pronoun resolution directive. |
| Cross-thread question injection | MEDIUM | eLo sometimes asks about connections between threads from different sessions (printer + groceries). Grounding window picks up old subjects. Fix: decay weight of subjects older than 2 turns. |
| Mode routing miscalibration | MEDIUM | Positive physical wins routed to ground instead of celebrate. Root cause upstream of grounding (in attention/executive). |
| GT-8 pending message | LOW | `ConversationTracker.record()` doesn't store response type (pending/direct/system). Pronoun "pending message" not resolvable. Fix: add `response_type` field to `_Turn`. |
| Tracker window pollution | LOW | `active_thread` uses subject continuity heuristic (same subject 2 of last 3 turns). Noisy for short sessions. Fix: require 3-turn continuity. |

---

## 10. Legacy Paths

The following pre-WP-N paths were not modified:
- `runtime/executive.py` — FREEZE_V1_LOCK. Unmodified. Receives `grounding_block` as a prompt slot only.
- `core/attention.py` — FREEZE_V1_LOCK. Unmodified.
- `prompts/living_presence_spec.txt` — FREEZE_V1_LOCK. Unmodified.
- All pre-WP-N fast-paths in `_process_turn` — unmodified. Grounding only runs on the LLM path.

---

## 11. Next Work

**Priority 1 (open gap from Phase 9):**
- Strengthen `build_grounding_block()` pronoun resolution directive: explicitly instruct the LLM to resolve "it/that/this" to `current_subject` before generating.
- Example addition to the block: `"If the user refers to 'it', 'that', or 'this' without specifying, treat it as referring to: {current_subject}."`

**Priority 2 (GT-8 fix):**
- Add `response_type: str = ""` field to `_Turn` in `conversation_tracker.py`.
- Pass `response_type` from server.py `record()` call.
- Add "pending" as a resolvable referent in `referent_extractor.py`.

**Priority 3 (mode calibration):**
- Physical wins ("printed and it actually moves") should route to celebrate. This is an attention/executive calibration, not a grounding change. Flag for WO-MODEL-ROUTING work.

**Priority 4 (subject decay):**
- In `ConversationTracker.get_context()`, weight recent_referents by recency. Subjects from 4+ turns ago should not surface as recent_referents in the grounding block.

---

*Builder · WP-N Phase 10 · 2026-09-18*
