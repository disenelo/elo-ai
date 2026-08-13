# WO-072 — Intent Gatekeeper (rules-first, cheap-LLM normalizer as fallback)
> **Renumbered from WO-066 → WO-072 (2026-08-07):** WO-066 collided with the Builder's already-committed
> ambient-engine WO (`2c7e6be`). Git history is permanent, so WO-066 = ambient engine; this gatekeeper spec
> moved to WO-072. (Architect's own Check-Before-Build miss — reused a taken number.)

**Owner:** Builder (eLo OS — intent/routing lane). **Priority:** P1. **Status:** OPEN — spec'd 2026-08-07.
**Depends on:** WO-032b (needs a working cheap-LLM path for the fallback tier). **Idea origin:** David
2026-08-07 (external "data-bus / gatekeeper" pattern), mapped onto eLo's existing Faculty Bus.
**Canon:** ADR-Exec-001 (never fabricate an intent) · Reality Before Narrative (ambiguous ≠ invented
command) · verifiable/deterministic first (rules before LLM) · IO Contract (structured intent envelope).

## Problem (from live transcript #2, 2026-08-07)
The front-end intent parse is pure regex/patterns; messy conversational input mis-parses into commands/tools:
- "anything we can press on with? that needs my attention?" → mangled command "press+on+with?+that+needs+".
- "No but it takes time to build you" → "Ok, cancelled." (conversational "No" read as a command cancel).
- "Strange reply what does that mean?" → a GitHub tool fired ("GITHUB_REPO not set").
The regex catches clean phrasings and trips on natural, non-linear input (exactly David's brain-dump style).

## Design — a Gatekeeper STAGE at the front of the bus (does NOT do the reasoning/reply)
Its only job: turn raw input into a CLEAN, structured intent envelope, then publish it. Never composes eLo's
answer (the Processor tier / normal spine does that).

1. **RULES FIRST (deterministic, free, default):** the existing pattern classifiers run first. If they
   produce a HIGH-CONFIDENCE, unambiguous intent → use it, no LLM call. (Fast path — most turns.)
2. **CHEAP-LLM NORMALIZER (fallback only, low-confidence/ambiguous/garbled):** call a cheap fast model
   (`gpt-4o-mini` or `gemini-1.5-flash`) THROUGH the existing `backend_router` (reuse, no new client) with a
   strict prompt: "clean typos/STT noise; classify into one of {conversation, sit, move:<subtype>, exit,
   tool:<name>, company, weather, memory, …}; return ONLY structured JSON {intent, target, cleaned_text,
   confidence}." It NORMALIZES + CLASSIFIES — it does not answer.
3. **CONFIDENCE GATE (kills the false-fires):** a command/tool intent fires ONLY at high confidence. If the
   normalizer is unsure → default to **conversation**, never a command/tool. ("No", "what does that mean?"
   → conversation, not cancel/GitHub.)
4. **HONEST DEGRADE:** if the cheap LLM is unavailable (mock/offline) → fall back to rules-only; if rules
   are also low-confidence → treat as conversation. NEVER fabricate a command when uncertain (ADR-Exec-001).
5. **Publish** the structured intent onto the bus (canonical envelope) for the Processor/spine to consume.

## Definition of Done (full behaviour, end-to-end)
Messy conversational input is understood as conversation; real commands still route; no command/tool fires
on ambiguous input; when the LLM tier is down, it degrades to rules without inventing intents.

## Test — WITHOUT David (`tests/test_wo072_intent_gatekeeper.py`)
- **The transcript misroutes resolve:** "anything we can press on with? that needs my attention?" →
  `conversation` (NOT a command) · "No but it takes time to build you" → `conversation` (NOT cancel) ·
  "Strange reply what does that mean?" → `conversation` (NOT a tool).
- **Real commands still route:** "come sit" → `sit`; "jump to the top of the window" → `move:fire_jump`/
  movement (NOT open-URL); "how's the company" → `company`; "what's the weather" → `weather`.
- **Confidence gate:** a deliberately ambiguous string → `conversation`, never a command/tool.
- **Degrade:** with the LLM tier stubbed unavailable → falls to rules-only; ambiguous → conversation; no
  fabricated intent, no crash.
- **Fast path:** a clean unambiguous command does NOT call the LLM (assert the normalizer wasn't invoked) —
  keeps latency/cost down.
Gate: Builder test green → Chief Architect acceptance → David L3 (a full brain-dump conversation that
doesn't trip commands).

## "Chaos-text" scenarios — David's real dump style (the test corpus + his live L3 script)
The gatekeeper must handle David's fast, non-linear input. Each → expected structured intent:
1. **Multi-intent run-on:** "ok the robot head bowden thing needs sorting and also come sit and whats the
   weather" → recognise MULTIPLE: `sit` (command) + `weather` (query) + robot note (memory) — queue/handle,
   do NOT garble into one mangled command.
2. **Command buried in conversation:** "I was thinking about the company and honestly come sit with me while
   I work this out" → `sit` extracted cleanly; the rest is conversation.
3. **Conversational negation:** "No but it takes time to build you" → `conversation`, NOT a cancel.
4. **Typo / STT mangle:** "waht can yuo tel me abot the compnay" → `company`, cleaned.
5. **Question read as command:** "anything we can press on with that needs my attention?" → `conversation`/
   board-priority query, NOT a command fragment.
6. **Topic-switch mid-dump:** "the invoice for client X — actually no, first what's on the board" → latest
   intent = `board`; invoice = logged note, NOT auto-fired (L3 guard).
7. **Ambiguous fragment:** "hmm the grok tab thing" → `conversation`/low-confidence, no tool fire.
8. **Venting:** "I'm tired and nothing's working" → `conversation` (engage, ground), no command.
These fold into `tests/test_wo072_intent_gatekeeper.py` AND double as David's live L3 script once WO-072 is up.

## Lane / relationship to other WOs
Builder only (Python). GENERALISES the point-fixes in WO-039 (garble) + WO-020 (tool false-fire): those add
the specific live cases as guards NOW; WO-072 is the durable front-door that stops the whole class. Reuses
`backend_router` (no new LLM client) + the Faculty Bus envelope. No new state store (SQLite not needed —
continuity already lives in memory/`blender_state.json`).
