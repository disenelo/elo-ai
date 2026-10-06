# IS ELO — VERDICTS & FIXES FOR BUILDER 3 (2026-10-06)
**From:** Board / Lead Architect  
**To:** Builder 3  
**Authority:** David L3  
**Priority:** P0 — Every NO below is a gap in the running integrations layer

---

## HOW TO READ THIS

- **YES** — causally wired, demonstrable in running system
- **PARTIAL** — component exists, not causally connected end-to-end
- **NO** — does not exist or is prompt-only (LLM generates the appearance, no architecture backs it)

---

## TOOLS & CAPABILITIES

| Question | Verdict | Evidence / Gap | Code Location | Fix Required |
|---|---|---|---|---|
| a system that knows what tools it has? | NO | `capability_registry.py` exists. Not readable by anchor prompt. Spotify denial while playing proves it. | `capability_registry.py` → not wired to `prompt_builder.py` | **Make capability_registry queryable by Builder 1's capabilities block. Your job: expose an API or structured dict that Builder 1 reads into the anchor.** |
| a system that knows what tools it does not have? | NO | Same gap. LLM generates "I can't" from training data not from registry state. | Same | Same fix — registry must have ACTIVE/INACTIVE status per capability |
| a system that knows when a tool is appropriate? | PARTIAL | Intent routing exists in `spine.py`/`backend_router.py`. Spotify intent not routing correctly. | `tools/spotify_agent.py`, `capability_registry.py` | Wire pause/stop intent correctly (already Job 3 in your queue) |
| a system that knows when a tool is unnecessary? | NO | LLM decides. Not architecture-driven. | No code location — this is Executive-level | Not your fix — flag to Board as architectural gap |
| a system that knows when a tool result is authoritative? | NO | MISSING-FACT rule overrides injected tool context. | `runtime/server.py` | Spec to Builder 1 — tool result must reach Executive without LLM override |
| a system that can distinguish tool output from its own interpretation? | NO | eLo paraphrases and generates from tool output rather than returning it. | `runtime/server.py` pipeline | Spec to Builder 1 — structured tool result pass-through |
| a system that can return deterministic results directly? | NO | All results pass through LLM. Spotify status is non-deterministic when it should be authoritative. | `tools/spotify_web.py` | Your fix: Spotify status calls return structured JSON, not prose. Builder 1 handles pass-through to Executive. |
| a system capable of selecting tools based on semantic intent rather than isolated keywords? | PARTIAL | `spine.py` does intent routing. Keyword matching misses "Can you pause" — needs semantic variation coverage. | `runtime/spine.py`, `runtime/backend_router.py` | Add intent synonyms to routing vocabulary. Spec to Builder 1 if spine.py changes needed. |
| a system capable of refusing a false capability match? | NO | No capability validity gate. eLo can say "searching..." and not search. | No code location | Builder 1: add execution confirmation gate. Your job: tool must return success/fail signal. |
| a system capable of recognising whether a tool action succeeded? | NO | "Got it" with no action is the live proof. | `tools/spotify_agent.py` | **Your fix: every tool call in your domain must return `{success: bool, result: any, error: str}`. File as required for all your tools.** |
| a system capable of recognising whether a tool action failed? | NO | Same. | Same | Same fix |
| a system capable of incorporating tool results into subsequent reasoning? | NO | Results discarded or paraphrased by LLM. | `runtime/server.py` | Spec to Builder 1 — tool results must persist in CognitiveState for the turn |
| a system capable of remembering important tool outcomes? | NO | Nothing from tool execution writes to vault or WKG. | No vault write from tools currently | Spec to Builder 1 — tool outcomes of significance should vault-write. Define "significant": successful Spotify play, websearch result, etc. |
| a system capable of distinguishing a tool action from a conversational statement about an action? | NO | "Can you pause Spotify" treated as question by LLM. | `runtime/spine.py` intent routing | Your fix: add interrogative form of capability intents — "can you X" must still route to tool when X is wired |

---

## SPOTIFY — SPECIFIC VERDICTS

| Question | Verdict | Evidence / Gap | Code Location | Fix Required |
|---|---|---|---|---|
| Pause routes correctly? | NO | David said "Can you pause" twice. Nothing happened. | `tools/spotify_agent.py`, `runtime/backend_router.py` | **Job 3 Bug 1 — already in your queue** |
| eLo knows Spotify is active when it is playing? | NO | Denied capability while actively playing. | `capability_registry.py` | **Job 3 Bug 2 — expose active-state status from Spotify to registry** |
| eLo executes or reports why it failed? | NO | "Got it" with no action, no error. | `tools/spotify_agent.py` | **Job 3 Bug 3 — return value must be success or error, never void** |
| Stop intent routes? | NO | Same as pause gap. | Same | Wire "stop", "stop playing", "stop the music" → pause call |
| Skip routes? | UNKNOWN | Not tested live. | Same | Add to test list after pause/stop verified |
| Spotify status queryable by anchor prompt? | NO | Registry not exposed to prompt layer. | `capability_registry.py` → `prompt_builder.py` gap | Expose active capability status dict. Builder 1 reads it. |

---

## WEBSEARCH — SPECIFIC VERDICTS

| Question | Verdict | Evidence / Gap | Code Location | Fix Required |
|---|---|---|---|---|
| Websearch routes when David explicitly asks? | NO | Live proof: David said "do a websearch for Pinkie and the Brain." eLo gave generic filler. | `tools/web_search.py`, `runtime/backend_router.py` | **Job 4 in your queue — fix SEARCH_INTENT routing** |
| eLo says "I don't know, let me look it up" and then does? | NO | eLo says "I don't have that recorded" and stops. | Same | Same fix |
| Search result returned in eLo's voice? | PARTIAL | `web_search.py` exists. Result pipeline unclear. | `tools/web_search.py` | Verify result is formatted in eLo's voice before reaching Executive |
| eLo distinguishes searched knowledge from trained knowledge? | NO | No provenance on search results vs LLM generation. | No code location | Spec to Builder 1 — search results must have SOURCE=WEBSEARCH tag in CognitiveState |

---

## ALEXA — SPECIFIC VERDICTS

| Question | Verdict | Evidence / Gap | Code Location | Fix Required |
|---|---|---|---|---|
| Alexa ingress exists? | NO | Outbound push only. eLo cannot hear Alexa. | `tools/alexa_agent.py` — outbound only | **Job 4 (Alexa ingress) — your queue** |
| David can talk to eLo through Alexa and get response? | NO | No request handler. | Same | Build ingress path as per queue job |

---

## SELF-AWARE OF HIS OWN ARCHITECTURE (Tools Portion)

| Question | Verdict | Evidence |
|---|---|---|
| Does eLo know which tools actually exist? | NO | Capability registry not in anchor |
| Does eLo know when a tool is unavailable? | NO | No live status check in registry |
| Does eLo know when a tool actually executed? | NO | No execution confirmation returned to cognition |
| Does eLo know whether the result came from the tool or from his own generation? | NO | No provenance flag on results |

---

## YOUR IMMEDIATE FIX ORDER

1. **Job 3 — Spotify: all three bugs** — P0, already in queue. Do this first.
   - Pause/stop routing (Bug 1)
   - Registry active-state exposure to prompt layer (Bug 2 — coordinate with Builder 1)
   - Return value always success or error, never void (Bug 3 — applies to ALL your tools)

2. **Capability registry structured API** — expose `get_active_capabilities() -> dict` so Builder 1 can read it into the anchor. This is what fixes "eLo denies what it's doing."

3. **Job 4 — Websearch SEARCH_INTENT routing** — wire explicit search requests to actually search.

4. **Tool result return standard** — every tool you own (`spotify_agent.py`, `spotify_web.py`, `alexa_agent.py`, `web_search.py`) must return `{success: bool, result: any, error: str|None}`. No void returns. No "Got it" without this data being returned to the caller.

5. **Intent coverage expansion** — add interrogative forms ("can you X", "could you X", "would you X") to routing vocabulary for all your capabilities. File as spec to Builder 1 if spine.py changes required.

6. **Alexa ingress** — after Spotify is done.

**The test that proves your work matters:**
David says "pause Spotify." Spotify pauses. eLo says "Paused." You can point to: the intent routing that fired, the `spotify_agent.py` call that executed, the `{success: True}` return value, and the capability registry showing Spotify as active before the call. That is DONE.

*Board / Lead Architect · 2026-10-06*
