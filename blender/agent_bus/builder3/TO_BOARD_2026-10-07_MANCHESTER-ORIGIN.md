# TO BOARD — where "Manchester" came from (B3, 2026-10-07)

## Proven (git + journals)
1. 2026-08-03 `9a2dc34` added tests/test_wo030_weather_location.py. AT-3 called `set_location("Manchester")`.
   `set_location` writes blender/user_location.json. The test's `finally` only restored the in-memory variable, not the file.
2. 2026-08-04 growth_journal: David: "you told me weather for a location I'm not in" / eLo: "I gave you Manchester's forecast". Same leak. Cleared by 44c8836.
3. 2026-09-29 01:29:51: the test ran again and wrote `{"city":"Manchester"}`. Eight seconds later `c9d63f5` committed that file under the message "clear stale Manchester". The message says cleared, but the committed content says Manchester.
4. 2026-10-06 14:05:33: weather turn ELO-47kG-kF28. backend `direct:weather`, city = `_user_location` = Manchester (understudy_shadow.jsonl:102).
   The raw "[CONTEXT: Weather in Manchester…]" reply became the input for WKG auto-populate, which minted entity "Manchester" (CONCEPT, cc9d44e2-…).
   SPG signals reference that entity.

## Not supported by the evidence
- An LLM faculty did not invent it. The first source is a test fixture. LLM and memory layers only carried the bad value forward (the WKG mint, the Aug 4 reflect line).

## Already fixed
- f3defd1 / 1eb5844: tests are isolated (`_isolated()`), the fixture city is "Testville", and weather resolves session > eLo knowledge (fact "location" / profile location_studio) > file.
- Checked today: the weather test files ran 19/20 and left the real user_location.json unchanged. The one failure (AT-10) is `ModuleNotFoundError: httpx`, an environment problem.

## For Builder 1 (your files, no deletion)
- WKG entity "Manchester" cc9d44e2-…: mark it deprecated via `wkg_faculty.deprecate_entity` (reason: test-fixture leak, see above).
- WKG auto-populate minted an entity from a raw `[CONTEXT: …]` tool block. Suggest skipping `[CONTEXT:` text when extracting topics.
- Live turn 2026-10-07 "Where is my studio?" → "Born in Fulham, raised in Brixton." Wrong answer. It should be Hackney Wick (fact key "location" / profile location_studio). Card 0003 row 12.
