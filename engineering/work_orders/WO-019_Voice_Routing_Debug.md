---
id: WO-019
title: "Debug: eLo voice only speaks one sentence / drops out + cryptic non-answers"
owner_seat: SEAT-ENG-001 (Builder) + SEAT-ENG-004 (UI/Avatar for playback)
occupant: Builder (Python) + UI/Avatar
priority: P1
reason: "Live Presence test (David 2026-07-31): TTS voices only 1 of 2 sentences, silent on parts, inconsistent playback; and some replies are cryptic/associative instead of direct answers."
review_required: L1 → L3
risk: none (diagnostic)
status: READY
created: 2026-07-31
---

# WO-019 — Voice routing + response-mode debug

From David's live conversation test. **Two separate bugs** — do NOT conflate them.

## Bug A — TTS speaks only one sentence / drops out (PRIMARY)
**Symptom (David's words):** *"You say two sentences and only read out loud one," "silent on parts of
the chat," "sometimes the volume plays and sometimes it doesn't," "it's like the voice request isn't correct."*

**Hypothesis (Architect):** the response→speech call is passing **only the first sentence** (or the first
streamed chunk) to TTS, or the voice request is written once per response and later sentences are dropped.

**Where to look (grounded in the repo):**
- **The call site** that hands response text to `plugins/voice/voice_engine.py:speak()` / `plugins/voice/tts_output.py` —
  is it passing the *full* response, or a first-sentence fingerprint? Note `core/kernel.py:144` extracts a
  **first-sentence fingerprint** (≤60 chars) for loop-detection — confirm that fingerprint isn't what's
  being spoken by mistake.
- **Streaming:** if the response streams, is `speak()` called on the first chunk only? Check the dispatch
  in `main.py` / the server / backend_router (which splits into sentences at `runtime/backend_router.py:49/129/166`).
- **The voice request file** — `blender/elo_voice.json` + `blender_bridge/lipsync_writer.py`: is a new
  request overwriting the previous before it plays (race), so only the last/first survives? Check the write
  cadence vs playback.
- **Backend:** `ELO_TTS_BACKEND` default is `"print"` (`tts_output.py:33`) — confirm the live app is on a
  real backend (pyttsx3/elevenlabs), and that a failed/slow synth for sentence 2 isn't silently swallowed.

**Handback:** the exact before/after — what text string reaches `speak()` per turn, and where a multi-
sentence response loses its tail. A one-line fix note + the file:line.

## Bug B — cryptic/associative replies instead of direct answers (SECONDARY)
**Symptom:** replies like *"That ties in," "One feeds the other," "Write the first line now—don't let it
get away," "You keep coming back to narrative"* when David asked plain questions. (It DID answer directly
once — "Start by checking your OS audio output device…" — so routing is *intermittent*.)

**Hypothesis:** the **Conversation Action Layer** (`runtime/executive.py` — CONNECT/REFLECT/WITNESS) or a
pattern/association layer (`core/pattern_observer.py`, memory injection) is firing when **ANSWER /
CONVERSATIONAL** is correct. Per `core/kernel.py`, factual/plain input should route DIRECT/CONVERSATIONAL;
the associative one-liners look like CONNECT/REFLECT winning inappropriately.

**Where to look:** `runtime/executive.py` action selection (what tips it to CONNECT/REFLECT on a plain
statement); `core/kernel.py` classifier→router; whether `pattern_observer`/significance is injecting
"connections/narrative" into the response.

**Handback:** which action fired on the cryptic turns and why, vs. the direct one — the routing signal
that differs.

## Note
Use the movement/`movement_debug` trace pattern (WO-017) as the model: emit a per-turn **voice/response
trace** (chosen action, text sent to TTS, sentences count, backend) so the routing is observable, not guessed.
