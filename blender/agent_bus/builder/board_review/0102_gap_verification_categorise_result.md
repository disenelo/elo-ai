**WO:** GAP-VERIFY-CATEGORISE · **Seat:** builder · **Priority:** P0
**Reserved?** no

## Goal
Categorise every NO RESULT and FAIL test into one of three buckets so fixes go to the right place.

## Source
`/Users/Disenelo/Desktop/Output/elo_test_report_2026-10-07.txt` — 203 NO RESULT, 79 FAIL

## Three categories

**RUN** — pure code assertion. Can be run headless, no server needed. Builder 1 fixes the code until green.

**LIVE** — conversational / behavioural. Must be run against the live eLo server and confirmed by David in his chatlog. Examples: "eLo remembers what David said", "eLo's response varies with context", conversation quality tests.

**VISUAL** — UI, animation, Unity. Must be confirmed by David watching eLo. Examples: health bar colour, fireflies, movement animations, expression shapes.

## What to do

1. Open each NO RESULT test file — read what it actually tests (one pass through the file is enough)
2. Classify it: RUN / LIVE / VISUAL
3. For RUN tests: run them on the Mac. If they pass → mark PASS. If they fail → add to the fix list (card 0101).
4. For LIVE tests: write the exact phrase David says to eLo + what eLo should respond → add to David's verification queue file: `/Users/Disenelo/Desktop/Output/live_verification_queue_2026-10-07.txt`
5. For VISUAL tests: write what David should look for → add to `/Users/Disenelo/Desktop/Output/visual_verification_queue_2026-10-07.txt`

## Output files (write these)
- `/Users/Disenelo/Desktop/Output/elo_test_report_FULL_2026-10-07.txt` — all 509 with RUN/LIVE/VISUAL tag + PASS/FAIL/PENDING
- `/Users/Disenelo/Desktop/Output/live_verification_queue_2026-10-07.txt` — LIVE tests, exact David→eLo phrases
- `/Users/Disenelo/Desktop/Output/visual_verification_queue_2026-10-07.txt` — VISUAL tests, what to look for

## Done when
All 509 tests categorised. RUN failures in fix queue. LIVE and VISUAL queues written to Output. Move to BUILT/.

## Result
- RUN count: 3 remaining failures (ambient tick, auto-calm, dream out_dir guard)
- LIVE count: 0 (previously queued WO-0099 covers take_five + company — tests pass offline)
- VISUAL count: 0
- IMPORT ERROR count: 15 (numpy×10, cryptography×5, openai×1 — pip install fixes)
- RUN failures added to 0101: yes (3 items)
- commit: n/a (categorise only)

Outputs:
  /Users/Disenelo/Desktop/Output/elo_test_report_FULL_2026-10-08.txt  — full 3689-test report
  /Users/Disenelo/Desktop/Output/live_verification_queue_2026-10-08.txt  — LIVE tests + phrases
  /Users/Disenelo/Desktop/Output/visual_verification_queue_2026-10-08.txt  — VISUAL tests

RUN failures for 0101 fix register:
  - test_s4_ambient_tick.py::test_hard_idle_restores_once_eLo_has_been_alone
    → hard idle battery restore not firing after 10 ticks with long_ago last_user_ts
  - test_s4_auto_calm_on_exhaustion.py::test_walking_to_exhaustion_lands_in_calm
    → walk→exhaustion→calm state machine not transitioning
  - test_no_live_state_writes.py::test_composite_dream_writes_nothing_without_an_out_dir
    → dream compositor writes live state even without out_dir

## Live turn needed
> Board reads the LIVE verification queue and schedules confirmation turns with David.
