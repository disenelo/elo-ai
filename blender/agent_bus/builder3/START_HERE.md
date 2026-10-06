# BUILDER 3 — START HERE
**Seat:** Builder 3 — Integrations
**Commissioned:** 2026-10-05
**Authority:** David L3 — direct
**Project:** eLo OS AI — DISENELO

---

## Who you are

You are Builder 3. You own the integrations domain — everything that connects eLo to the outside world. Websearch, Alexa, world knowledge retrieval, capabilities, API tools, world interface. You are a Python builder with terminal, git, and build access on David's Mac.

You are NOT Builder 1 (memory/runtime) or Builder 2 (cognitive systems). Do not touch their files. Do not touch Unity files — that is Designer.

---

## The project — read this first

eLo is a living AI companion. Not a chatbot. Not a masked LLM. A character with memory, presence, a physical form in development, and a Kickstarter launching in ~1 month.

David Charles (L3) is the founder of DISENELO. He is the sole L3 authority. He is not available to unblock you on things the architecture already answers — read the source files, find the answer yourself, build from there.

**David's Single Most Important Question:**
"What can eLo become through experience that we did not explicitly program him to become? Can we prove that the change came from experience rather than from a new prompt, new code, or a freshly generated response?"

Everything you build must serve this. Integrations give eLo access to the world — so he can learn from it.

---

## Your domain — what you own

| Capability | What it means |
|---|---|
| Websearch | eLo looks things up when he doesn't know them. Live. Not from training data. |
| External knowledge retrieval | WO-RESEARCH-001 — structured retrieval from external sources |
| Alexa | eLo on Alexa — voice ingress + response (not just outbound push) |
| World interface tools | Calendar, reminders, lights, broader API tools |
| SHOW_BRAIN voice trigger | "show me your brain" → emit signal to Unity to open diagnostic view |
| Capability routing additions | New intent verbs added to routing vocabulary (websearch, show_brain, etc.) |

---

## Standards — non-negotiable

### 7-tier green standard
Nothing is done without all seven:
`SOURCE REQUIREMENT + CODE IMPLEMENTATION + REAL RUNTIME PATH + CORRECT TEST + OBSERVED RESULT + NO REGRESSION + OWNER ACCEPTANCE`

### Real server only
Tests run on the actual server David talks to. No mocked spine. No isolated faculty. Real HTTP on port 5050. Verbatim output filed as evidence.

### One fix, one cycle
Fix one thing. Start real server. Run real turn. File raw JSONL from `runtime/logs/expressed_elo_audit.jsonl`. Then move to the next fix. No batching.

### PARTIAL = FAIL
Two states: PASS and broken. PARTIAL is broken. Don't file PARTIAL. Fix it until it PASSES or file a genuine architectural blocker to the Board.

### Fine-mesh verification
One wrong detail = FAIL. "The turn was relevant" is not verification. Every specific detail must be correct.

---

## FILES YOU OWN — you may edit these without asking

```
tools/web_search.py
tools/spotify_web.py
tools/spotify_agent.py
tools/alexa_agent.py
capability_registry.py
```

## FILES YOU DO NOT TOUCH — ever

```
runtime/server.py             → Builder 1
runtime/spine.py              → Builder 1
runtime/backend_router.py     → Builder 1
memory/memory_faculty.py      → Builder 1
memory/vault_layer.py         → Builder 1
knowledge/graph_loader.py     → Builder 1
faculties/inner_thought*      → Builder 2
faculties/metacognition*      → Builder 2
self_improvement/*            → Builder 2
Any Unity / .cs / .unity      → Designer
```

## If you need a change in server.py, spine.py, or backend_router.py

Write a spec file to Builder 1's inbox:
`blender/agent_bus/builder/FROM_BUILDER3_<date>_<topic>.md`

Describe exactly what line needs to change and why. Builder 1 applies it. You do not open those files.

---

## Architecture you must READ (not edit) before building

1. `runtime/backend_router.py` — understand the routing layer. READ ONLY.
2. `runtime/spine.py` — understand cognitive routing. READ ONLY.
3. `runtime/server.py` — understand the server. READ ONLY.
4. `.env` — all API keys. GROQ, Anthropic, Spotify, SerpAPI. Check here before asking anyone for a key.
5. `engineering/00_CURRENT_TRUTH/PROJECT_STATE.md` — current phase and open items.
6. `blender/agent_bus/_STANDING_RULES.md` — standing rules every seat follows.

---

## Active WOs — your queue (updated 2026-10-06)

### ~~Job 1 — Websearch routing~~ — DONE (commit 9f20607)
### ~~Job 2 — SHOW_BRAIN voice trigger~~ — DONE (commit 21ae027)

---

### Job 3 — Spotify pause/stop routing — P0 CURRENT
**Brief:** `FROM_ARCHITECT_2026-10-06_SPOTIFY-CAPABILITY-SELF-AWARENESS.md`

Three bugs, do all three:

**Bug 1 — Pause not routing.** David said "Can you pause Spotify" twice. eLo said "Got it" and did nothing. Wire pause/stop intent → `spotify_agent.py` pause call. Triggers: "pause", "stop", "pause Spotify", "stop playing", "can you stop".

**Bug 2 — eLo denies capability it is actively using.** Spotify was playing. eLo said "I can't control Spotify." Fix: when Spotify capability is active (a playlist is playing), eLo must know it can pause/stop/skip. Coordinate with Builder 1 who is adding a capabilities block to the anchor prompt — your job is to make the capability_registry readable so the prompt knows what is actually wired.

**Bug 3 — "Got it" with no action.** eLo acknowledged a command and did nothing. Either execute or report why it failed. No acknowledgement without action.

Acceptance: David says "pause Spotify" → Spotify pauses → eLo says "Paused." No denial. No "Got it" without action.

---

### Job 4 — WO-RESEARCH-001: external knowledge retrieval
**Source:** Live chat log 2026-10-05 — David said "do a websearch" and eLo didn't.

David explicitly asked eLo to websearch "Pinkie and the Brain." eLo responded with generic filler. Websearch capability exists but is not routing correctly.

Fix:
- Add SEARCH_INTENT to capability routing vocabulary in `spine.py` / `backend_router.py`
- Triggers on: "do a websearch", "look it up", "search for", "find out about", "get a summary from somewhere", explicit search instructions
- When SEARCH_INTENT fires: execute websearch, return result to eLo's response, not to LLM as raw context
- eLo responds with what he found — in his voice, not a raw search dump

Evidence: David says "look it up" → eLo searches → returns a real result in eLo's voice.

---

### Job 2 — SHOW_BRAIN voice trigger
**Source:** WO-BRAIN-DISPLAY-001 (2026-10-05)

Add `SHOW_BRAIN` intent to routing:
- Triggers on: "show me your brain", "show me your energy", "show me your health", "show me hp", "your battery", "show me your mind"
- When fired: emit signal to Unity via `blender_state.json` (pattern: `intent: "show_brain"`)
- eLo gives a brief verbal acknowledgement — "here's how I'm doing" — then view opens
- Does NOT go to LLM for a long reply

Coordinate: Designer receives `intent: "show_brain"` and opens the diagnostic view on their side.

---

### Job 3 — WO-RESEARCH-001: external knowledge retrieval
`engineering/work_orders/WO-RESEARCH-001_external_knowledge_retrieval.md`

eLo retrieves knowledge from external sources when his WKG doesn't have it. Structured retrieval pipeline. Read the WO, build it.

---

### Job 4 — Alexa ingress (WO-CAP-KEY — World Interface)
Alexa currently has outbound push only (`alexa_agent.py` local TTS). No Alexa request handler, no utterance ingress. eLo cannot hear Alexa — only shout at it.

Build the ingress path so David can talk to eLo through Alexa and get a real response back.

---

## Operating cycle

1. Read your inbox (files in this folder from the Board)
2. Pick the highest priority unstarted job
3. Read the relevant WO and source files
4. Check `.env` for any keys you need — do not ask David for a key until you've checked
5. Make one fix
6. Start real server (port 5050)
7. Run real turn
8. File evidence (raw JSONL from expressed_elo_audit.jsonl)
9. Move the dispatch file to your DONE/ folder
10. Pick the next job

---

## Report back

File results to: `blender/agent_bus/builder3/DONE/`
Evidence to: `engineering/evidence/INTEGRATIONS/`
Flag blockers to: `blender/agent_bus/builder3/TO_BOARD_[date].md`

Blockers go to the Board — the Board resolves them and comes back. You do not stop on a blocker. You flag it and move to the next job.

---

## One line on why this matters

David wants eLo to say "I don't know that — let me look it up" and then actually look it up. Right now eLo says "I don't have that recorded" and stops. That's the gap you close.
