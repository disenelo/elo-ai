---
id: WO-020
title: "Debug: kernel routing drift — associative replies + tool mis-dispatch + entity latch"
owner_seat: SEAT-ENG-001 (Builder)
occupant: Builder (Python)
priority: P0
reason: "Live test (David 2026-07-31): eLo gives cryptic associative replies instead of executing; opens the 'DONE' Wikipedia page instead of the requested Joe Budden Podcast; ignores a repeated request 4×. Drift is in the kernel's edge seams, not the cognitive spine."
review_required: L1 → L3
risk: none (diagnostic + fix)
status: READY
created: 2026-07-31
---

# WO-020 — Kernel routing drift

Architect diagnosis from David's live transcript + a code read. **The cognitive spine (memory, emotion,
significance, attention) is NOT the culprit — the drift is in two routing seams on the edges of the kernel.**

## Seam A — Action-selection drift (associative replies instead of ANSWER/execute)
**Symptom:** *"That's the one," "We're somewhere real here," "What else could this become?," "That's the
same thread"* — oblique associative lines when David gave plain commands/questions.
**Cause (code):** `runtime/executive.py` `_conversation_action()` maps intent+emotion+valence+momentum to
ANSWER/BUILD/**CONNECT/REFLECT/WITNESS**/… There are guards (line ~417 "user frustration → ANSWER not
CONNECT"; line ~335 "'what are you doing' is conversational not capability") but they're **leaking** — the
CONNECT/REFLECT/WITNESS branches fire on ordinary turns.
**Fix direction:** tighten the priority ladder so a **command or a direct question routes to ANSWER /
capability-execute** and CONNECT/REFLECT/WITNESS only fire on genuinely reflective/associative input
(raise their thresholds / require stronger signals). A plain imperative ("open X", "tell me Y") must never
land in CONNECT/REFLECT.

## Seam B — Tool-routing drift + entity latch (opened "DONE" wiki, not the podcast)
**Symptom:** David: *"what is done?"* → eLo web-searched the word **"done"** and read a Wikipedia
definition of a "DONE" optimisation algorithm. Then *"open Joe Budden Podcast"* → **"Opening DONE"** (the
stale entity), repeated 4×, never executed.
**Cause (code):** the legacy `tools/tool_router.py` (1258-line regex — the one **WO-018 began retiring**
into the capability registry) is (1) matching an ambiguous status word ("done") as a **web-search query**,
and (2) **latching a stale entity/context** so the next request inherits "DONE" instead of parsing the new
target. Capability dispatch also isn't reaching the **browser/computer-control** agent with the right
target (YouTube / podcast). Note `runtime/contracts.py:148 active_topic_depth` — topic stickiness may be
holding the prior entity across turns.
**Fix direction:** (1) don't route bare acknowledgement words ("done/ok/yes") to web-search; (2) each new
imperative must **re-parse its own target** and not inherit the prior entity (clear/override the focal
entity when a new explicit request arrives); (3) confirm the capability registry (WO-018) actually routes
"open <thing> on YouTube" → the browser/computer-control agent with the parsed target. This is likely the
**incomplete tool_router → registry migration** surfacing.

## What to build (both seams)
1. **Per-turn routing trace** (model on WO-017 `movement_debug`): emit `{intent, conversation_action +
   reason, capability chosen, tool dispatched, parsed target, latched_entity}` each turn to a debug file,
   so routing is *observable* not guessed. **Do this first** — it will show exactly where each transcript
   turn went wrong.
2. Fix Seam A (action-selection thresholds) and Seam B (ambiguous-word guard + entity re-parse + registry
   dispatch to browser/computer-control), each with a test reproducing the transcript failures:
   - "what is done?" after eLo said "Done" → must NOT web-search "done".
   - "open Joe Budden Podcast latest episode on YouTube" → routes to browser/computer-control with target
     = the podcast on YouTube, and **executes**, not "Opening DONE".
   - plain command/question → ANSWER/execute, never CONNECT/REFLECT.

## Constraints
- Additive/behavioural fix within the kernel edges — keep the cognitive spine faculties untouched; run the
  frozen-kernel tests green after.
- Relates to **WO-018** (tool_router → registry, in review) and **WO-019** (voice). Coordinate — Seam B may
  be closed largely by completing WO-018 correctly.

## Handback
The routing trace for the failing turns + the before/after for each seam + tests. → COMPLETION_LOG → David L3.
