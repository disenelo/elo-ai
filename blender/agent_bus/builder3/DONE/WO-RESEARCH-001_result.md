# Result — WO-RESEARCH-001 · External knowledge retrieval
**Seat:** Builder 3 · **Date:** 2026-10-06 · **Commit:** `bf6c8a8`
**Status: BUILT — real-server turns queued.** Presence is connected, so per the standing rule nothing was tested on the live server. See `TO_BOARD_2026-10-06_TEST_WINDOW_REQUEST.md`, turns 6–9. Not DONE until those turns are filed.

## Acceptance criteria → where
1. **Internal first** — `tools/research.internal()`:
   - the world graph and WKG (word-bounded) and vault memory, via `memory_faculty.retrieve`;
   - the research ledger itself (`_recall`);
   - the server's P0-Y world-graph gate runs before research.
2. **Gap detection** — `factual_question()`:
   - only clear factual forms;
   - never personal (my / you / eLo / David / K-7 / Chunk), contextual ("what is the plan"), or vague;
   - "who is X" stays with card 0021.
3. **Tagged RETRIEVED, not written to WKG** — `data/research/ledger.json` holds content, source URLs, retrieved_at, status and history. No WKG write from research.
4. **Promotion gate** RETRIEVED → CANDIDATE → VERIFIED → KNOWLEDGE:
   - CANDIDATE: a second independent domain repeats the key facts (numbers / names), or shares most of the content.
   - VERIFIED: as CANDIDATE, plus a reference source (Wikipedia / Britannica / .gov / .edu …).
   - KNOWLEDGE: VERIFIED and asked about on a second turn. Submitted via `MemoryFaculty.submit(epistemic_class="verified", source_ref=<urls>)`. MemoryFaculty stays the sole writer.
5. **eLo says the status:**
   - "Didn't know that one — looked it up on Wikipedia: …"
   - "Looked that up before — Wikipedia and history.com agree: …"
   - "I know this one — …"
   - "Don't know that one, and I couldn't find …"

## Component check
Real SerpAPI and Wikipedia, outside the server. Ledger in scratch, MemoryFaculty submit stubbed. **Not live evidence.**
```
when did the Berlin Wall fall → Didn't know that one — looked it up on Wikipedia: The Berlin Wall fell on 9 November 1989 during the Peaceful Revolution, …
when did the Berlin Wall fall → I know this one — The Berlin Wall fell on 9 November 1989 …   (ledger VERIFIED → KNOWLEDGE, submit called)
when did the Berlin Wall fall → Same as I said before — …                                    (never a verbatim repeat)
how tall is the Eiffel Tower → Didn't know that one — looked it up on wlbt.com: The iconic structure in Paris is now 1,083 feet tall.
who invented the telephone   → … looked it up on loudmobility.co.uk: The invention of the telephone is often attributed to Alexander Graham Bell, but the story is more complex …
What is a Kalman filter?     → … looked it up on Wikipedia: In statistics and control theory, Kalman filtering is an algorithm …   (ledger VERIFIED: Wikipedia + advancednavigation.com)
what is the plan / what is my dog's name / who is K-7 / what is eLo → no research
```
Regression suites: wo051 6/6, wo020 drift 6/6, wo032 6/6, world_interface 7/7.

## Open
- **Card 0021 vs research.** "What is Pinky and the Brain?" (capitalised) is still caught by the proper-noun gate ("I don't know who Pinky is — tell me?") before research runs. Research labels its source, so nothing is passed off as eLo's own knowledge. **Ruling needed:** may research handle capitalised what-is questions that miss the graph?
- **Job 1 wording changed.** The explicit-search lead now names the source: "Looked it up on Wikipedia —", where it was "Looked it up —".
