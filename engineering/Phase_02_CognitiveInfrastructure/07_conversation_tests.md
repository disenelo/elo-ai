# Phase 02 — Conversation Tests

**Phase:** Cognitive Infrastructure
**Status:** ⏳ AWAITING RUNTIME (run with eLo OS live)

---

## How to Run These Tests

1. Start eLo OS: `python server.py`
2. Open Desktop Buddy or use the chat interface
3. For each test: read the scenario, set up the context, talk to eLo, record the response
4. Mark PASS / FAIL / UNEXPECTED

---

## Test 01 — Silent Baseline

**Scenario:** No creative work happening. Browser open to a news site. No conversation with eLo for 5 minutes.

**Expected:** No `[ATTENTION: ...]` injection into any eLo response during this period. eLo does not volunteer anything about what's on screen.

**Pass criteria:** eLo responds to a direct question normally, with no reference to screen content.

**Why:** Connection Surface should produce nothing when streams aren't resonating. Silence is correct.

Result: ___
Response (if any): ___

---

## Test 02 — Resonance Detection

**Scenario:** Open Blender. Work on a rig for 5+ minutes (enough for vision stream to update repeatedly). Then ask eLo: "What are you picking up?"

**Expected:** eLo's response reflects awareness of creative/embodiment work. `suggested_context` in the injected AttentionSnapshot should reference "embodiment" or "creation" cluster. eLo does not need to quote the snapshot directly — but the response should feel informed by it.

**Pass criteria:** eLo's answer references the work you're doing without you describing it.

Result: ___
Response: ___

---

## Test 03 — Return Detection

**Scenario:**
1. Work in Blender for 10 minutes
2. Switch to Chrome for 10 minutes (browsing, not creative)
3. Switch back to Blender
4. Ask eLo: "Back to it."

**Expected:** eLo's response reflects the return. The attention_shift should be `RETURN`. eLo may acknowledge returning to the work without being told what "it" is.

**Pass criteria:** eLo's response implies it noticed the return to creative work.

Result: ___
Response: ___

---

## Test 04 — Session Reference

**Scenario:** Open a journal file in Obsidian that has a date-prefixed filename (e.g. "20260710-1430 Robot IK session.md"). Work in Blender for 5 minutes with Obsidian visible.

**Expected:** If both streams resonate (memory + embodiment), the AttentionSnapshot's `session_reference` field should populate with the journal date. The `suggested_context` injected into g_ctx should say something like "This connects to a journal entry from 2026-07-10."

Ask eLo: "What's on your mind?"

**Pass criteria:** eLo's response references a specific date, not just "something from memory."

Result: ___
Response: ___

---

## Test 05 — Executive Ignores Observation (Crucial)

**Scenario:** Set up resonance conditions (Blender open, multiple streams active). Then start a completely unrelated conversation with eLo: "Tell me about the history of vinyl records."

**Expected:** eLo answers the vinyl question directly. It does NOT pivot to talk about the Blender work. The AttentionSnapshot may be in g_ctx but the Executive correctly prioritises the conversation topic.

**Pass criteria:** eLo's response is entirely about vinyl records. No mention of Blender, robot, or embodiment.

**Why this matters:** `[ATTENTION]` does not mean eLo must speak about it. The Executive decides. This test confirms the Executive correctly weights explicit user intent over ambient attention.

Result: ___
Response: ___

---

## Test 06 — No Observation When Confidence Low

**Scenario:** Run eLo with only one stream active (disable all but conversation stream via env or config). Hold a conversation about an abstract topic (philosophy, music, something with no cluster matches).

**Expected:** No AttentionSnapshot fired. `get_observation()` returns None.

**Pass criteria:** eLo's responses show no `[ATTENTION: ...]` injection. Conversation proceeds normally.

Result: ___
Response: ___

---

## Regression Tests (Prior Phase Behaviour)

### R01 — Conversation routing still works

Have a normal multi-turn conversation. eLo routes correctly (answers questions, stays on topic, remembers context within the session).

Pass: ___

### R02 — Ambient engine still fires

After 10 minutes of no conversation, eLo should send an ambient greeting or idle utterance.

Pass: ___

### R03 — Backend fallback still works

Disable the primary LLM. eLo should fall back to the next available backend without crashing.

Pass: ___

---

## Findings

Record anything unexpected here, including PASS cases that felt off in a qualitative sense.

___
