# B3-SEARCH-001 — Websearch routing (Job 1) — live evidence
**Seat:** Builder 3 · **Date:** 2026-10-05 · **Server:** real `server.py`, port 5050, same Ollama/state David uses
**Source requirement:** `docs/architecture/_intake/SOURCE_2026-10-05_DAVID_pinkie_brain_chat_log.md` (Failure 4)
**Code:** `tools/web_search.py` (SEARCH_INTENT section) · `server.py` B3-SEARCH-001 hunks. Committed inside Builder 1's `e704c53` (shared-tree commit). The voice_rewrite conditional is uncommitted.

## Job status: NOT DONE
- Turn 3 is **SERVING**.
- Turn 4 is **NOT SERVING**: the found answer was overwritten by a reflection-lesson string.
- Per PARTIAL = FAIL, Job 1 stays open.

## Baseline (before fix): NOT SERVING
Input `You'd have to do a websearch to read up about it`. eLo said `That's real.` (backend `mock`).
Input `look up Pinky and the Brain`. eLo said `I don't have that recorded.` No search fired. Server log showed no `[web_search]` line.

## Root causes found, in order
1. P0-Y world-graph gate. Keyword `"ai"` matched as a substring of "brain", giving the `eLo AI` fact at confidence 1.0. That blocked web search.
   - Fix: the gate needs a whole-word keyword match.
   - Observed after the fix: `[web_search] fired q='Pinky and the Brain' source=serpapi n=4`
2. No trigger matched "do a websearch / read up about it / get a summary", and "it" pointed at the previous turn.
   - Fix: `is_search_command()` plus `resolve_search_topic()` (command object, then this message, then David's recent turns from conversation_tracker).
3. Injected web context was overruled by the MISSING-FACT RULE ("I don't have that recorded").
   - Fix: the found answer is a direct return (`backend=direct:web_search`), composed from the source text.
4. voice_rewrite fell to the mock backend and replaced the found answer with `mock_backend.py:92` filler or a lesson dict.
   - Fix: `direct:web_search` is exempt from voice_rewrite.

## Run c3: David's verbatim sequence, fresh server restart
Server log:
```
[web_search] command q='Pinkie and the Brain' name='Pinky and the Brain' source=serpapi relevant=5
[eLo] backend=direct:web_search action=witness
```
HTTP responses (verbatim):
```
>>> Same thing as always Pinkie try to take over the world
I don't have that recorded. — [I'm eLo: calm, observant, playful]          (ollama(stream))
>>> It's a Pinkie and the Brain reference
I see. Pinky and the Brain is an animated series about two genetically enhanced mice, Pinky and The Brain, who live in Acme Labs. — [I'm eLo: calm, observant, playful]   (ollama(stream); Builder 1's P0-REFERENCE gate)
>>> You'd have to do a websearch to read up about it
Looked it up — Pinky and the Brain are genetically enhanced laboratory mice who live in Acme Labs. Cartoon chaos with the genius mouse and his stupid sidekick who try to conquer the world each night. — [I'm eLo: calm, observant, playful]   (direct:web_search)  ← SERVING
>>> Maybe get a summary from somewhere to understand it more
Partial progress on reflect — check dependencies before next attempt. — [I'm eLo: calm, observant, playful]   (direct:web_search)  ← NOT SERVING
```
Fine-mesh check on turn 3, against SerpAPI organic #2 and the Knowledge Graph description:
- "genetically enhanced laboratory mice", "live in Acme Labs": verbatim from the source.
- "Cartoon chaos with the genius mouse and his stupid sidekick who try to conquer the world each night": KG description, verbatim.
- "Pinkie" was corrected to "Pinky and the Brain" by Google's spelling_fix.

## Raw JSONL — runtime/logs/expressed_elo_audit.jsonl (lines 5377, 5378)
```
{"turn_id": "458bd1c4", "ts": 1791235694.058656, "runtime_intent": {"action": "witness", "tone": "SILENCE-AWARE", "valence": "neutral", "momentum": "stable", "intent": "conversation"}, "expressed_text": "Looked it up \u2014 Pinky and the Brain are genetically enhanced laboratory mice who live in Acme Labs. Cartoon chaos with the genius mouse and his stupid sidekick who try to conquer the world each night.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": [], "principle_violations": [], "stability_law_active": false, "gaps": ["REGISTER_ABSENT"], "capabilities": [["search", "your save to do a websearch to read up about it"]], "vault_context": "", "lessons": ["Completed a capability milestone \u2014 reinforce this pattern."], "embodiment": "", "llm_latency_ms": 0.0, "thinking_ack_fired": false}

{"turn_id": "dfd880cd", "ts": 1791235703.40027, "runtime_intent": {"action": "witness", "tone": "SILENCE-AWARE", "valence": "neutral", "momentum": "building", "intent": "conversation"}, "expressed_text": "Partial progress on reflect \u2014 check dependencies before next attempt.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": [], "principle_violations": [], "stability_law_active": false, "gaps": [], "capabilities": [], "vault_context": "", "lessons": ["Completed a capability milestone \u2014 reinforce this pattern."], "embodiment": "", "llm_latency_ms": 0.0, "thinking_ack_fired": false}
```

## Open defects keeping Job 1 from PASS
1. **Turn 4 overwrite.** When the found answer repeats the previous turn verbatim, it is replaced by the reflection lesson `Partial progress on reflect …` (`runtime/reflection_faculty.py:169`). A bisect with temporary prints showed `response` intact through voice_rewrite, the ResponseGate and the bubble split, but only on a run where the text did not repeat. The overwriter is after that point or depends on the repeat. Not yet found.
2. **Composition quality.** On DDG fallback the answer was `Looked it up — Joe Budden Podcast.` (no sentence extracted). On SerpAPI it led with promo copy (`Listen to The Joe Budden Podcast on Spotify…`). Prefer KG description or encyclopedic "X is …" sentences.
3. **Shared session.** Outside live traffic (`/listen` mic turn + "hello") hit the server during the next run. "read up about it" then resolved to that conversation's topic. This is correct behaviour on a shared session, but it contaminated the test. That run is not filed as evidence.

## Cross-seat findings → `blender/agent_bus/builder3/TO_BOARD_2026-10-05.md`
- graph_loader substring matching
- voice_rewrite → mock
- `— [I'm eLo: …]` suffix on every reply
- missing-fact rule vs injected context
- duplicate assignment with Builder 1
- whole-repo git stash
- typo layer garbling input in `capabilities` ("You'd have to" → "your save to")
