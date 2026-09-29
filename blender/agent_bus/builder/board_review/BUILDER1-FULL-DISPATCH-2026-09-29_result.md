# FROM ARCHITECT — BUILDER 1 FULL DISPATCH
**Date:** 2026-09-29
**Authority:** Board / Lead Architect
**Basis:** IS ELO Full Causal Audit — live test run 2268 PASS · 23 FAIL

This brief replaces and supersedes `FROM_ARCHITECT_2026-09-29_BUILDER1-WIRE-NOW.md`.
All items in that brief are still outstanding unless marked below.

---

## P0 — BUGS BREAKING THINGS NOW (fix first, in order)

### P0-1: Significance vector incomplete every ambient turn
**File:** `runtime/significance_faculty.py`
**Bug:** 4 keys missing from canonical 14-key shape when `outcome=None`:
- `efficiency`, `safety`, `reward`, `embodiment` — only added in outcome branch
- Every ambient observation turn (no explicit outcome) produces an incomplete vector

**Fix:** When outcome is None, set all 4 keys to 0.0. Return the full 14-key shape always.

**Tests to pass after fix:**
- `tests/test_lci001_verified_outcome_reward.py::test_ac1_no_outcome_no_reward_key`
- `tests/test_significance_vector_shape.py::test_no_outcome_has_canonical_keys`
- `tests/test_significance_vector_shape.py::test_no_outcome_body_dims_are_zero`
- `tests/test_significance_vector_shape.py::test_key_set_does_not_depend_on_outcome`
- `tests/test_significance_vector_shape.py::test_verified_true_reward_above_meaning_only`

**Expected result:** All 5 PASS.

---

### P0-2: Heartbeat rogue writer
**File:** `server.py` (locate the rogue writer)
**Bug:** `_ts` advances from `1790646729.286 → 1790646730.804` without `start_heartbeat()` being called.
**Test:** `tests/test_0054_heartbeat_owner.py:77`

**Fix:**
1. Find every place `_ts` is written in server.py
2. Gate each write: only advance `_ts` if `_heartbeat_running` is True
3. Run test — must PASS without start_heartbeat being called

---

### P0-3: Bypass handler count drift
**File:** `server.py` / `tests/test_0020_ct0033_bypass_handlers.py`
**Bug:** Test expects 42 `_bypass_journal` calls in server.py. Grep finds 52.
**Fix:**
1. Count actual `_bypass_journal` calls in server.py
2. If 52 is correct (10 new handlers added intentionally): update expected count to 52 in test
3. If some are unintentional: remove them, revert to 42
4. Add a comment in test explaining what bypass handlers are (so future additions don't silently break it)

---

### P0-4: WorkingMemory.current_task populated with EloSelfState object
**File:** `runtime/working_memory.py:seed_working_memory()`
**Bug:** `current_task` field receives the full `EloSelfState` object. Should receive a string.
**Fix:** Set `current_task = state.current_action` (or equivalent string describing current task)
**Verify:** `wm.current_task` is a string, not an object

---

### P0-5: Test journal contaminating live journal directory
**File:** `tests/test_wo_fix_112_ambient.py`
**Bug:** Test writes to `self/journals/_test_wo_fix_112_ambient.jsonl` then fails to delete with PermissionError
**Standing rule:** Tests NEVER write to live directories. Tests use `tmp_path`.
**Fix:** Patch the journal path in the test to use `tmp_path`. Add teardown cleanup.

---

## P1 — OUTSTANDING WIRES (all from prior brief, none landed)

### WIRE-1: SPG write-path — `add_node_for_claim()` after generation
**Where in server.py:** After `_elo_response` is generated (after the LLM returns its text)
**Before:** SPG only learns from world events. eLo's own statements never feed SPG.
**Fix:**
```python
# After _elo_response is set:
from runtime.significance_faculty import add_node_for_claim as _spg_add_claim
try:
    _spg_add_claim(_elo_response, _elo_self, _session_id)
except Exception:
    pass  # fire and forget
```
**Verify:** After a turn, check that the claim appears in the SPG node store.

---

### WIRE-2: Reflection faculty — `integrate_session()` at end of turn
**Where in server.py:** Post-response hook, before `save(state)`
**Fix:**
```python
from runtime.reflection_faculty import integrate_session as _rf_integrate
try:
    _rf_result = _rf_integrate(state, _conversation_turns)
    if _rf_result and _rf_result.lesson:
        state.last_reflection_lesson = _rf_result.lesson
except Exception:
    pass
```
**Verify:** After 3+ turns, `EloSelfState.last_reflection_lesson` is non-empty.

---

### WIRE-3: Capability learning — generalize `record_outcome()` to all capabilities
**Current state:** `record_outcome()` called at server.py:4320 and 4359 (locomotion only)
**Fix:** Find the main capability dispatch path in server.py. After any capability returns a result:
```python
from runtime.capability_learning import record_outcome as _cap_record
try:
    _cap_record(capability_name, success=bool(capability_result))
except Exception:
    pass
```
**Verify:** After a WORLD_WEB_RESEARCH call fails, check `capability_learning.failure_streak` increments.

---

### WIRE-4: Install astral + configure Hackney Wick
**Step 1:** `pip install astral --break-system-packages`
**Step 2:** In `faculties/temporal/faculty.py` or its config:
```python
LOCATION_LAT = 51.5386  # Hackney Wick, East London
LOCATION_LON = 0.0201
LOCATION_NAME = "Hackney Wick"
```
**Tests to pass:**
- `tests/test_wo_world001.py::test_at1_location_configured` — must show "configured" not "absent"
- `tests/test_wo_world001.py::test_at4_sun_populated_with_location`
- `tests/test_wo_world001.py::test_at8_spine_passes_capability_hint_to_world`

---

### WIRE-5: Register DREAM in CAPABILITY_REGISTRY
**File:** `runtime/capability_registry.py`
**Add:**
```python
"WORLD_DREAM": {
    "name": "Dream State",
    "description": "Enter offline dream processing",
    "semantic_keywords": ["dream", "sleep", "rest", "offline processing"],
    "requires": ["WORLD_SLEEP"],
    "executor": "faculties.dream"
},
"WORLD_REFLECT": {
    "name": "Reflect",
    "description": "Integrate session into learned behaviour",
    "semantic_keywords": ["reflect", "learn", "review session"],
    "executor": "runtime.reflection_faculty"
},
"WORLD_CURIOUS": {
    "name": "Curiosity",
    "description": "Pursue an unanswered question",
    "semantic_keywords": ["curious", "explore", "investigate", "wonder"],
    "executor": "runtime.curiosity_faculty"
}
```

---

### WIRE-6: COG-004 re-run after claim gate fix
**After fixing the claim gate inversion (the 6 XFAIL cases):**
Run the full COG-004 multi-turn suite. Target: 26/26 PASS.

---

## NEW WIRES — THIS SESSION

### WIRE-7: WorkingMemory goal and thread persistence across turns
**Problem:** `WorkingMemory.open_threads` and `active_goals` are always empty tuples. Any deferred intention disappears at turn end.

**Fix:**
**Step 1 — Add fields to EloSelfState:**
```python
# In self/elo_self_model.py, EloSelfState dataclass:
active_goals: list = field(default_factory=list)
open_threads: list = field(default_factory=list)
```

**Step 2 — Save/load:**
```python
# In save(): include active_goals and open_threads in JSON
# In load(): restore active_goals and open_threads
```

**Step 3 — Seed WorkingMemory from state:**
```python
# In server.py after seed_working_memory(state):
wm.active_goals = tuple(state.active_goals)
wm.open_threads = tuple(state.open_threads)
```

**Step 4 — Wire Executive goal-writing:**
When Executive produces a deferred item or sets a goal, write it back:
```python
if exec_output.deferred_item:
    state.open_threads.append(exec_output.deferred_item)
    state.save()
```

**Verify:** Create a deferred thread in turn 1. Restart server. Confirm thread appears in working memory turn 2.

---

### WIRE-8: check_identity_drift → end of every turn
**File:** `server.py`
**Where:** After response generated, before `save(state)`
```python
from self.elo_self_model import check_identity_drift as _check_drift
try:
    _drift_alert = _check_drift(state)
    if _drift_alert:
        logging.warning(f"[IDENTITY DRIFT DETECTED] {_drift_alert}")
except Exception:
    pass
```

---

### WIRE-9: Movement result → experience → memory
**File:** `server.py:4453` (where MovementOutcome is received)
**Fix:**
```python
from self.elo_self_model import record_behaviour as _rec_beh
from runtime.capability_learning import record_outcome as _cap_record
# After receiving MovementOutcome:
if movement_outcome.success:
    _rec_beh(state, 'move')
else:
    try:
        _cap_record('MOVE', success=False)
    except Exception:
        pass
```
**Verify:** After a successful movement, `recent_behavior['move']` increments. After a failed jump, check `failure_streak['MOVE']` increments.

---

### WIRE-10: Dream → Executive (PHASE 8 final wire)
**File:** `server.py`
**What:** `dream_review.py` is built and wired to journal but NOT routed to Executive.
**Fix:** Add dream material retrieval to the pre-turn context build:
```python
from faculties.dream.dream_review import get_wake_insights as _dream_insights
try:
    _dream_context = _dream_insights(state, threshold=0.72)
    if _dream_context:
        # Add to executive context as HYPOTHESIS-class material
        faculty_outputs['dream'] = _dream_context
except Exception:
    pass
```
**Note:** David's decision required on server restart. Confirm with David before executing.

---

## P2 — NEW BUILDS

### WO-CURIOSITY-001: Build curiosity_faculty module
**File to create:** `runtime/curiosity_faculty.py`

```python
from dataclasses import dataclass, field
from typing import Optional
import time

@dataclass
class CuriosityItem:
    question: str
    sparked_by: str      # event/observation that created it
    created_at: float = field(default_factory=time.time)
    pursued: bool = False
    result: Optional[str] = None
    strength: float = 1.0  # decays over time

def spark_curiosity(state, event: str, question: str) -> Optional[CuriosityItem]:
    """Create a curiosity item if the event is significant enough."""
    item = CuriosityItem(question=question, sparked_by=event)
    if not hasattr(state, 'open_curiosities'):
        state.open_curiosities = []
    state.open_curiosities.append(item)
    return item

def get_open_curiosities(state) -> list:
    return getattr(state, 'open_curiosities', [])

def mark_pursued(state, question: str, result: str):
    for item in get_open_curiosities(state):
        if item.question == question:
            item.pursued = True
            item.result = result

def age_curiosities(state, decay_rate: float = 0.05):
    """Reduce strength of stale curiosities. Remove if below 0.1."""
    alive = []
    for item in get_open_curiosities(state):
        if not item.pursued:
            item.strength = max(0.0, item.strength - decay_rate)
            if item.strength > 0.1:
                alive.append(item)
        else:
            alive.append(item)
    state.open_curiosities = alive

def curiosity_block(state) -> str:
    """Format open curiosities for executive prompt."""
    items = [c for c in get_open_curiosities(state) if not c.pursued and c.strength > 0.3]
    if not items:
        return ""
    lines = [f"[OPEN CURIOSITY] {c.question} (strength: {c.strength:.1f})" for c in items[:3]]
    return "\n".join(lines)
```

**Add to EloSelfState:** `open_curiosities: list = field(default_factory=list)`
**Include in save/load**
**Wire in server.py:** After each turn, call `age_curiosities(state)`. If significance is high and a question forms, call `spark_curiosity()`. Include `curiosity_block(state)` in executive context.

---

### WO-UNLEARN-001: Build unlearning mechanism
**File to create:** `runtime/learning/unlearn.py`

```python
from self.elo_self_model import EloSelfState
import logging

def weaken_prior(state: EloSelfState, verb: str, amount: float = 50):
    """Reduce accumulated count for a verb. Floor at 0."""
    if hasattr(state, 'recent_behavior') and verb in state.recent_behavior:
        state.recent_behavior[verb] = max(0, state.recent_behavior[verb] - amount)
        logging.info(f"[UNLEARN] Weakened prior: {verb} reduced by {amount}")

def deprecate_fact(fact_id: str, reason: str):
    """Mark a fact in facts.json as deprecated."""
    # Load facts.json, mark the fact with deprecated=True and reason
    # Do not delete — preserve history
    pass

def log_unlearn_event(state: EloSelfState, what: str, why: str):
    """Record that an unlearning event occurred."""
    if not hasattr(state, 'unlearn_log'):
        state.unlearn_log = []
    state.unlearn_log.append({
        'what': what,
        'why': why,
        'when': __import__('time').time()
    })
```

---

### WO-METACOG-001: Build meta-cognition module
**File to create:** `runtime/metacognition.py`

```python
from self.elo_self_model import EloSelfState
from runtime.working_memory import WorkingMemory

def observe_own_state(state: EloSelfState, wm: WorkingMemory) -> str:
    """Return a summary of eLo's current cognitive state."""
    top_habits = list(sorted(
        state.recent_behavior.items(), 
        key=lambda x: x[1], reverse=True
    ))[:3]
    habits_str = ", ".join(f"{k}×{v}" for k, v in top_habits)
    open_count = len(wm.open_threads)
    return f"[METACOG] habits: {habits_str} | open threads: {open_count} | battery: {state.elo_battery:.2f}"

def flag_when_overthinking(cognitive_load: float, threshold: float = 0.8) -> bool:
    """Return True if cognitive load exceeds threshold."""
    return cognitive_load > threshold

def recognise_reasoning_pattern(recent_verbs: list) -> str:
    """Detect if stuck in a loop or over-reflecting."""
    if len(recent_verbs) > 5:
        last_5 = recent_verbs[-5:]
        if all(v == 'reflect' for v in last_5):
            return "LOOP: over-reflecting"
        if all(v == 'ground' for v in last_5):
            return "LOOP: over-grounding"
    return "OK"

def metacog_block(state: EloSelfState, wm: WorkingMemory) -> str:
    """Format metacognitive state for executive prompt."""
    return observe_own_state(state, wm)
```

**Wire:** Call `metacog_block(state, wm)` in the executive context build (alongside emergent_block, spg_block, etc.)

---

## D8 — KNOWLEDGE INJECTION (HIGHEST VALUE OUTSTANDING WORK)

This is the one that makes eLo actually know David.

**The gap:** LLM generates responses. It has the identity block and conversation history. But it does NOT have David's facts, profile, or vault memories.

**Fix design:**
```python
# In server.py, before routing to LLM:

def build_knowledge_context(state, session_id):
    lines = []
    
    # 1. Facts about David
    try:
        facts = json.load(open('memory/facts.json'))
        for fact in facts:
            lines.append(f"KNOWN: {fact['subject']}: {fact['value']}")
    except Exception:
        pass
    
    # 2. Profile
    try:
        profile = json.load(open('memory/user_profile.json'))
        if profile.get('address_as'):
            lines.append(f"KNOWN: David's name is David. Address as '{profile['address_as']}'.")
        if profile.get('born'):
            lines.append(f"KNOWN: David was born in {profile['born']}.")
        if profile.get('raised'):
            lines.append(f"KNOWN: David grew up in {profile['raised']}.")
    except Exception:
        pass
    
    # 3. Relevant vault entries (top 3)
    try:
        from memory.vault import lookup_relevant as _vault_lookup
        relevant = _vault_lookup(session_id, n=3)
        for entry in relevant:
            lines.append(f"REMEMBERED: {entry['summary']}")
    except Exception:
        pass
    
    return "\n".join(lines)

# Then inject into system prompt:
knowledge_context = build_knowledge_context(state, session_id)
if knowledge_context:
    system = system + "\n\n[eLo KNOWLEDGE]\n" + knowledge_context
```

**Verify:** Ask "where is David from?" — answer must be "Hackney Wick, East London" not a fabricated location.

---

## AFTER ALL FIXES — RUN THESE TESTS

```bash
# P0 bug tests:
pytest tests/test_lci001_verified_outcome_reward.py -v
pytest tests/test_significance_vector_shape.py -v
pytest tests/test_0054_heartbeat_owner.py -v
pytest tests/test_0020_ct0033_bypass_handlers.py -v
pytest tests/test_wo_fix_112_ambient.py -v

# P1 wire tests:
pytest tests/test_wo_world001.py -v  # astral
pytest tests/ -k "wkg" -v  # WKG regression

# Full suite:
pytest tests/ --tb=no -q
# Target: >2268 PASS, <10 FAIL (real fails only)
```

---

## IMPORTANT: WHAT NOT TO DO

- Do NOT write any content to `self/journals/` from tests — use `tmp_path`
- Do NOT modify `EloSelfState.core_values` or `invariants` in any fix
- Do NOT add a second Executive or second decision path
- Do NOT log internal state into user-facing responses (KEY-003/KEY-004 class bugs)
- Do NOT claim a wire is complete without verifying the test for that wire passes

---

**Board sign-off required after:** 
1. All P0 bugs PASS
2. astral installed (can verify immediately)
3. open_threads persist across session boundary (WIRE-7)

**David does NOT receive this brief. Builder receives it, executes, reports to Board.**

---

## ADDENDUM — SESSION 3 (2026-09-29) — CRITICAL EXECUTIVE ROUTING FIX

### EXECUTIVE ROUTING BUG — FIX IMMEDIATELY (P0 SEVERITY)

**File:** `runtime/executive.py`
**Function:** `_conversation_action()` — starts at line 236
**Bug:** Line 338–340 is a hard REFLECT default that fires for ALL ordinary conversation turns.
`intent == "conversation"` has no ANSWER handler. `_RESPONSE_GOAL["conversation"] = "answer"` (line 348) is never consulted.

**Exact fix — add BEFORE line 338:**
```python
# conversation intent → answer is the correct default
# _RESPONSE_GOAL["conversation"] = "answer" confirms this — now enforce it
if intent == "conversation":
    return {
        "action": "answer",
        "confidence": 0.85,
        "reason": "conversation — default to answer (per _RESPONSE_GOAL)",
        "candidates": _score_candidates(user_input, intent, valence, momentum),
    }
```

**Test requirement:** After the fix, a plain conversation turn (no question mark, no creation phrase, no positive valence) MUST route to ANSWER, not REFLECT. Builder must add a test in `tests/test_wo_seam_a_executive_repair.py` or equivalent confirming:
1. `intent="conversation", valence="neutral"` → action == "answer"
2. `intent="conversation", valence="positive_low"` → action == "celebrate" (existing path at line 315, must still work)
3. `intent="inquiry", is_question=True` → action == "answer" (existing path at line 295, must still work)
4. `intent="emotional", valence="neutral"` → action == "reflect" (existing path at line 319, must still work)

**Evidence required:** Board will verify by reading the actual test output and running `_conversation_action()` directly with `intent="conversation"` and checking `result["action"] == "answer"`.

---

### NEW BUG FIXES — Session 3

**BUG-NEW-1: focal_thread = "wrong" (data corruption)**
- `elo_self_model.load()` currently returns `focal_thread: "wrong"` from disk
- Fix: find where "wrong" was written to `memory/elo_state.json`, correct the value to `""` (empty string = no current thread), and add a guard in `load()` that rejects non-sensical thread strings
- Guard: `if state.focal_thread not in ("", ...<valid threads>...): state.focal_thread = ""`
- Do NOT just patch the JSON — find the write path that produced "wrong" and fix the writer

**BUG-NEW-2: curiosity = 1.0 (no decay path)**
- `elo_self_model.load()` returns `curiosity: 1.0` — maxed, never settling
- Expected range: 0.4–0.8 during normal session
- Fix: Implement curiosity decay — after each session turn, curiosity should decay toward 0.5 at rate ~0.02 per turn unless new novel input is detected
- Guard: `curiosity = min(0.95, max(0.1, curiosity))` — never allow 1.0 as a persisted resting state

---

### FOCAL_THREAD BUG — also check these paths
Run: `grep -rn "focal_thread" runtime/ self/ --include="*.py"` and find every write path.
The string "wrong" should never appear in elo_state.json as a thread value.

