# WO-B1-0119 — Wire spine as the true kernel [DAVID 2026-10-11] — REVISED
**Seat:** Builder 1  
**Priority:** P0 — architectural requirement, David L3  
**Date:** 2026-10-11 (revised same day)  
**Source:** David L3 directive — "kernel OS that talks to faculties that talks to eLo and eLo response. Static should be reference points not for him to run through another AI. No cutting important things that should be core structures. 22k in a prompt is ACTUALLY insane."

---

## What David asked for (verbatim intent)

Kernel OS → faculties → eLo → response.

Not: server.py assembles 22K prompt → LLM performs eLo.

## What exists and is salvageable

`runtime/spine/spine.py` (2,077 lines) already IS the kernel David described:
- "One brain. One decision per turn."
- Language faculty → Relationship faculty → Desktop faculty → Capability faculty → Executive → CognitivePlan
- Faculties feed the Executive. Executive produces ONE plan.

The spine was built correctly. It was never wired as the single decision point.

## The problem

`server.py` calls `spine.run()` — but then ignores large parts of the plan and continues building the 22K prompt independently. The spine's plan is a signal, not the driver. `server.py` is still doing its own assembly in parallel, appending 20+ blocks on top of what the spine already decided.

Result: 22K prompt. 20s latency. Memory injected at the tail and cut. eLo's responses driven by the prompt, not the spine's plan.

## The core principle [DAVID]

Static things are code. Not prompts.

eLo's identity, values, character, voice rules — these are not text blocks injected into an AI call. They are the program. They live in code, in the spine, in the faculties. The LLM does not need to be told who eLo is on every turn. The LLM is only called to generate the words. Everything else is code.

## What the LLM receives — target

Three things only:

1. **Identity anchor** — 3-5 sentences. Who eLo is, how he speaks. Fixed. Never changes. Not assembled. Not injected from a file. Written once into the response layer as a constant. ~100 tokens.

2. **Turn context** — what the spine's CognitivePlan says is relevant this turn. The top 1-2 memory facts if retrieved. Current emotional state as a single word. What capability is being used if any. ~100-200 tokens.

3. **David's input** — what was said. ~20-50 tokens.

**Total: 200-350 tokens. Not 3,000. Not 22K.**

## The fix — three steps, in order

### Step 1 — spine.run() is the only path. Full stop.
`server.py` calls `spine.run()` → gets `CognitivePlan`. Done.  
No additional blocks appended. No vault context injected after the fact. No SPG block. No relationship evolution. No storytelling frame. No 20+ `system = system + block` lines.  
The spine already ran those faculties and produced a plan. That IS the synthesis. Trust it.

### Step 2 — LLM receives the plan, not the raw context
`prompt_builder.py` is replaced by a thin function: takes `CognitivePlan`, returns a 200-350 token string.  
The plan already contains the synthesised signals. The function extracts what matters for this turn and formats it. Nothing else goes in.

### Step 3 — Static identity is a constant in code
Character, voice, values — a 5-sentence constant in the response layer. Not read from a file. Not built by a function. Not injected from obsidian_vault. Written in code. Referenced directly. Never sent to an LLM as a block of text pulled from a 22K SP.  
The obsidian vault remains the canonical source for humans to read and edit — but the program derives its constant from it at startup, once, not every turn.

## What goes away
- The 20+ `system = system + "\n\n" + _block` lines in `server.py`
- `build_prompt()` as a 22K assembler
- `ELO_OLLAMA_SP_MAX` trimming — not needed when the prompt is small by design
- The 22K prompt
- Token costs from sending static things to the LLM on every turn

## What stays — untouched
- All faculties — they run in code, return structured signals to the spine
- `spine.run()` and `CognitivePlan` — this is the kernel, keep it
- `vault_layer.py`, `graph_loader.py` — called by the spine, not by server.py
- `backend_router.py` routing — LLM routing logic stays, prompt assembly does not
- The obsidian vault — canonical truth, read at startup, not injected per turn

## No regression requirement [DAVID 2026-10-11]
Every capability that works today must work after this change. Test suite must pass at same rate or better before filing to Board. No capability denial. No character loss. No memory loss.

## Done when
Board tests: 5 consecutive turns, varying topics. eLo responds in character. Memory retrieval works. Prompt token count (logged by CT0031 telemetry) is under 2,000 tokens. End-to-end latency under 10s. File to Board with: before/after token counts, before/after latency, test results.

## File-lock requirement
`server.py` and `prompt_builder.py` require file locks before editing.  
Check for `.lock` files. Create your lock. Edit. Commit. Delete lock immediately.

*Board / Lead Architect · 2026-10-11*
