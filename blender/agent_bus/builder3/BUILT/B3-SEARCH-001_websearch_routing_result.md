# Result — B3-SEARCH-001 · Job 1 websearch routing
**Seat:** Builder 3 · **Date:** 2026-10-06 · **Commits:** `9f20607` (plus B3 hunks carried in `e704c53`)
**Covers:**
- START_HERE Job 1
- `FROM_ARCHITECT_2026-10-05_WEBSEARCH-WIRE.md`
- `FROM_ARCHITECT_2026-10-05_SEARCH-WRONG-RESULT.md`
- `FROM_ARCHITECT_2026-10-06_SERVER-RESTART-GO.md`, steps 1–4

**Status: SERVING.** Run on the real server, port 5050, after a fresh restart with Builder 2's 851e3ae/c8645f4/f8ba983 in HEAD. Eight consecutive turns with no outside traffic, plus one music re-run.

## Where the wire lives (WEBSEARCH-WIRE)
The dispatch asked for the call in `spine.py`. David's turns enter through `server.py::_process_turn`, and that is where the web search block already sat, so the wire is there:
- **Turn start:** `server.py` ~2460. `note_input(raw)` adds every input to an 8-turn ring, so "it" can be resolved.
- **Gates:** `server.py` ~3401. `is_search_command(_original_raw)` → `_ws_command`. This skips the P0-Y proper-noun short-circuit for explicit commands.
- **Search:** `server.py` ~3507. `resolve_search_topic` → `search_topic` → `compose_found`, which sets `_ws_direct`.
- **Answer:** `server.py` ~6231. `_ws_direct` becomes the response with `backend=direct:web_search`, and the LLM is skipped.
- **Voice rewrite:** `server.py` ~7198. `direct:` results are exempt (Builder 1 extended this to every direct result).

**Disconnection check:** remove `_ws_command` or the `_ws_direct` hook and turns 3–4 fall back to the LLM path. This is the baseline already on record: "That's real." from backend `mock`, and "I don't have that recorded."

## What eLo does now
| David says | eLo |
|---|---|
| "You'd have to do a websearch to read up about it" | Resolves "it" to "Pinkie and the Brain" from earlier turns. Google's spelling fix gives "Pinky and the Brain". Answers with the Wikipedia lead. |
| "Maybe get a summary from somewhere to understand it more" | Gives the **next** facts, not a repeat. Before, the response gate blanked repeats and the empty turn was refilled with a lesson string. |
| "look it up" after Camberwell | Next facts from the same article. |
| "look up Jitwam Radio Playlist on Spotify" | Music results only. If none come back: "Searched … — nothing solid came back." The ring post no longer gets through. |
| "I was looking up at the sky earlier" | No search (no false trigger). |

## Fine-mesh check
Every sentence in the Pinky turns (e88256bb, cefa8665) appears verbatim in the Wikipedia REST summary extract for "Pinky and the Brain". This was checked by script on an earlier identical run: `[True, True]` for both turns. Only the lead-in ("Looked it up —" / "More on X —") is eLo's own wording.

## Verbatim HTTP responses — closing run
```
>>> Same thing as always Pinkie try to take over the world
'The same thing we do every night, Pinkie — try to take over the world!'   ollama(stream)
>>> It's a Pinkie and the Brain reference
'I understand you're frustrated. Let's focus on the search results for "Pinky and the Brain."'   ollama(stream)   ← emotional misfire: Builder 1 Pinkie Bug 1, not B3
>>> You'd have to do a websearch to read up about it
'Looked it up — Pinky and the Brain is an American animated television series about two genetically enhanced laboratory mice, Pinky and The Brain or "Brain", who consistently try and take over the world. The show was created by Tom Ruegger for the Kids' WB programming block of The WB, as a collaboration with Steven Spielberg and his production company Amblin Entertainment, and Warner Bros.'   direct:web_search
>>> Maybe get a summary from somewhere to understand it more
'More on Pinky and the Brain — This was the first animated television series to ever be presented in Dolby Surround. The characters first appeared in 1993 as a recurring segment on the animated television series Animaniacs.'   direct:web_search
>>> can you look up the Camberwell College of Arts
'Looked it up — Camberwell College of Arts is a constituent college of the University of the Arts London, a public art and design university in London, England. The college offers further and higher education programmes, including postgraduate and PhD awards.'   direct:web_search
>>> look it up
'More on Camberwell College of Arts — The college has retained single degree options within Fine Art, offering specialist Bachelor of Arts courses in painting, sculpture, photography and drawing. It also runs graduate and postgraduate courses in fine art as well as design courses such as graphic design, illustration and 3D design.'   direct:web_search
>>> look up Jitwam Radio Playlist on Spotify
'Searched Jitwam Radio Playlist on Spotify — nothing solid came back.'   direct:web_search   (SerpAPI timed out → DDG had 0 music results → honest absence)
>>> I was looking up at the sky earlier
'That sounds peaceful. What did you see?'   ollama(stream)
>>> look up Jitwam Radio Playlist on Spotify      (re-run, SerpAPI up)
"Looked it up — Jitwam's Top Spotify Playlists in the past 3 Months · Housewerk · Summer Dance Hits · Summer House 2026 · Tech House 2026 · Funk Rock · EDM Hits 2026."   direct:web_search
```
Server log:
```
[web_search] command q='Pinkie and the Brain' name='Pinky and the Brain' source=serpapi relevant=6
[web_search] command q='Pinkie and the Brain' name='Pinky and the Brain' source=serpapi relevant=6
[web_search] command q='the Camberwell College of Arts' name='Camberwell College of Arts' source=serpapi relevant=6
[web_search] command q='Camberwell College of Arts' name='Camberwell College of Arts' source=serpapi relevant=6
[web_search] SerpAPI (google) failed: The read operation timed out
[web_search] command q='Jitwam Radio Playlist on Spotify' name='Jitwam Radio Playlist on Spotify' source=ddg relevant=0
[web_search] command q='Jitwam Radio Playlist on Spotify' name='Jitwam Radio Playlist on Spotify' source=serpapi relevant=3
```

## Raw JSONL — runtime/logs/expressed_elo_audit.jsonl (all 9 turns of the closing run, verbatim)
```
{"turn_id": "d255764d", "ts": 1791246166.525324, "runtime_intent": {"action": "witness", "tone": "SILENCE-AWARE", "valence": "neutral", "momentum": "stable", "intent": "conversation"}, "expressed_text": "The same thing we do every night, Pinkie \u2014 try to take over the world!", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": [], "principle_violations": [], "stability_law_active": false, "gaps": [], "capabilities": [["vault_write", "save nothing as always pinkie try to takes over the works"]], "vault_context": "", "lessons": ["Completed a capability milestone \u2014 reinforce this pattern."], "embodiment": "", "llm_latency_ms": 30782.019790960476, "thinking_ack_fired": false}
{"turn_id": "d5c6b763", "ts": 1791246236.637689, "runtime_intent": {"action": "witness", "tone": "SILENCE-AWARE", "valence": "negative_low", "momentum": "stable", "intent": "conversation"}, "expressed_text": "I understand you're frustrated. Let's focus on the search results for \"Pinky and the Brain.\"", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": [], "principle_violations": [], "stability_law_active": false, "gaps": ["REGISTER_ABSENT"], "capabilities": [], "vault_context": "", "lessons": ["Completed a capability milestone \u2014 reinforce this pattern."], "embodiment": "", "llm_latency_ms": 35308.78370790742, "thinking_ack_fired": false}
{"turn_id": "e88256bb", "ts": 1791246254.1224582, "runtime_intent": {"action": "witness", "tone": "SILENCE-AWARE", "valence": "neutral", "momentum": "stable", "intent": "conversation"}, "expressed_text": "Looked it up \u2014 Pinky and the Brain is an American animated television series about two genetically enhanced laboratory mice, Pinky and The Brain or \"Brain\", who consistently try and take over the world. The show was created by Tom Ruegger for the Kids' WB programming block of The WB, as a collaboration with Steven Spielberg and his production company Amblin Entertainment, and Warner Bros.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": [], "principle_violations": [], "stability_law_active": false, "gaps": ["REGISTER_ABSENT"], "capabilities": [["search", "your save to do a websearch to read up about it"]], "vault_context": "", "lessons": ["Completed a capability milestone \u2014 reinforce this pattern."], "embodiment": "", "llm_latency_ms": 0.0, "thinking_ack_fired": false}
{"turn_id": "cefa8665", "ts": 1791246263.614656, "runtime_intent": {"action": "witness", "tone": "SILENCE-AWARE", "valence": "neutral", "momentum": "building", "intent": "conversation"}, "expressed_text": "More on Pinky and the Brain \u2014 This was the first animated television series to ever be presented in Dolby Surround. The characters first appeared in 1993 as a recurring segment on the animated television series Animaniacs.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": [], "principle_violations": [], "stability_law_active": false, "gaps": [], "capabilities": [], "vault_context": "", "lessons": ["Completed a capability milestone \u2014 reinforce this pattern."], "embodiment": "", "llm_latency_ms": 0.0, "thinking_ack_fired": false}
{"turn_id": "b4b4329b", "ts": 1791246273.292219, "runtime_intent": {"action": "witness", "tone": "SILENCE-AWARE", "valence": "neutral", "momentum": "stable", "intent": "creation"}, "expressed_text": "Looked it up \u2014 Camberwell College of Arts is a constituent college of the University of the Arts London, a public art and design university in London, England. The college offers further and higher education programmes, including postgraduate and PhD awards.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": [], "principle_violations": [], "stability_law_active": false, "gaps": ["REGISTER_ABSENT"], "capabilities": [["search", "can you look up the camberwell college of arts"]], "vault_context": "", "lessons": ["Completed a capability milestone \u2014 reinforce this pattern."], "embodiment": "", "llm_latency_ms": 0.0, "thinking_ack_fired": false}
{"turn_id": "18dae574", "ts": 1791246285.254772, "runtime_intent": {"action": "witness", "tone": "SILENCE-AWARE", "valence": "neutral", "momentum": "stable", "intent": "creation"}, "expressed_text": "More on Camberwell College of Arts \u2014 The college has retained single degree options within Fine Art, offering specialist Bachelor of Arts courses in painting, sculpture, photography and drawing. It also runs graduate and postgraduate courses in fine art as well as design courses such as graphic design, illustration and 3D design.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": [], "principle_violations": [], "stability_law_active": false, "gaps": ["REGISTER_ABSENT"], "capabilities": [["search", "it up"]], "vault_context": "", "lessons": ["Completed a capability milestone \u2014 reinforce this pattern."], "embodiment": "", "llm_latency_ms": 0.0, "thinking_ack_fired": false}
{"turn_id": "aa5d8bbc", "ts": 1791246306.876431, "runtime_intent": {"action": "witness", "tone": "SILENCE-AWARE", "valence": "neutral", "momentum": "stable", "intent": "conversation"}, "expressed_text": "Searched Jitwam Radio Playlist on Spotify \u2014 nothing solid came back.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": [], "principle_violations": [], "stability_law_active": false, "gaps": [], "capabilities": [], "vault_context": "", "lessons": ["Completed a capability milestone \u2014 reinforce this pattern."], "embodiment": "", "llm_latency_ms": 0.0, "thinking_ack_fired": false}
{"turn_id": "8086a548", "ts": 1791246344.867517, "runtime_intent": {"action": "witness", "tone": "SILENCE-AWARE", "valence": "neutral", "momentum": "stable", "intent": "conversation"}, "expressed_text": "That sounds peaceful. What did you see?", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": [], "principle_violations": [], "stability_law_active": false, "gaps": [], "capabilities": [], "vault_context": "", "lessons": ["Completed a capability milestone \u2014 reinforce this pattern."], "embodiment": "", "llm_latency_ms": 25782.927750144154, "thinking_ack_fired": false}
{"turn_id": "e44a5041", "ts": 1791246370.095435, "runtime_intent": {"action": "witness", "tone": "SILENCE-AWARE", "valence": "neutral", "momentum": "stable", "intent": "conversation"}, "expressed_text": "Looked it up \u2014 Jitwam's Top Spotify Playlists in the past 3 Months \u00b7 Housewerk \u00b7 Summer Dance Hits \u00b7 Summer House 2026 \u00b7 Tech House 2026 \u00b7 Funk Rock \u00b7 EDM Hits 2026.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": [], "principle_violations": [], "stability_law_active": false, "gaps": ["REGISTER_ABSENT"], "capabilities": [], "vault_context": "", "lessons": ["Completed a capability milestone \u2014 reinforce this pattern."], "embodiment": "", "llm_latency_ms": 0.0, "thinking_ack_fired": false}
```

## No regression
- Non-command lines ("I was looking up at the sky earlier", "what are you thinking about") do not trigger a search.
- `tier_violations: []` on all 9 turns.
- The old `is_search_intent` context path ("what is …", "who is …") is unchanged. It now runs only when no explicit command is present.

## Not B3 — noted, not touched
- Turn 2's "I understand you're frustrated" is Builder 1 Pinkie Bug 1 (emotional false trigger). It still reproduces on this run.

## Seat note
Board files in `builder3/` are left in place for the Board to move to CLOSED/ (standing rule: seats do not modify dispatch files). This card is the seat's result.

## Next
- Job 2: SHOW_BRAIN voice trigger.
- Then CAPABILITY-PROCESSING: Spotify open / play playlist / list playlists dispatch.
