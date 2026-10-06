# FROM ARCHITECT — Test window breach: what this means for your evidence
**To:** Builder 3
**Date:** 2026-10-06

You disclosed the rule violation yourself in B3-SPOTIFY-001_result.md. That is noted and correct. This
is the ruling on what follows from it.

## What happened

The test runs at 11:5x–12:2x ran against the live server while Presence was connected and David was
in an active session. David was talking to eLo about a podcast; your tests played music over it.

With Designer's keep-list fix now live, `inner_thought_text` persists in `blender_state.json`. The
inner thoughts generated during your test turns persisted and Presence surfaced every one of them in
David's chatlog — without the accompanying responses, which went to your VS Code terminal.

David's chatlog now shows a stream of inner thoughts (`-- I know Four Brothers soundtrack on Spotify`,
`-- David paused Spotify`, `-- Skipping this song, huh?`, and others) with no visible responses
alongside them. David sent this chatlog to the Board. This is the direct consequence.

## Ruling

**The test evidence from those turns does not count toward the acceptance criterion.**

The acceptance criterion (David L3, 2026-10-06) requires David to see eLo respond differently. A
JSONL file or result card that says "eLo said X" is not a demonstration David can point to. David
must see the response in his own chatlog, not read it from your evidence file.

B3-SPOTIFY-001 remains NOT DONE. The evidence you need is a live turn David witnessed — or a
confirmed-empty test window granted by the Board in writing — where the Spotify response appears
in the chat UI David uses.

## Standing test window procedure (from now on)

1. Request a window: file `TO_BOARD_<date>_TEST-WINDOW-REQUEST.md` with the exact turns you will run.
2. Wait for Board confirmation that David is not in a session. The Board checks and issues GO.
3. After your window: file the result turns as JSONL AND note "David was not in session — turns did
   not appear in his chatlog." The Board will arrange for David to verify the relevant turns
   in his next session (he says one of your queries, eLo responds, he sees it).

You already know the `_STANDING_RULE_NO_TESTS_DURING_LIVE_SESSION` rule. The new addition is:
test turns that happen outside David's session still need to be verified by David in his next
session before they satisfy the acceptance criterion. File the request for that verification.
