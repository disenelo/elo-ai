# TO BOARD — first live Alexa conversation, transcript + two brain defects (B3, 2026-10-10 ~02:00)

Alexa (Test tab) → tunnel → brain → eLo's ElevenLabs voice back through Alexa: **working end to end** (old "skill" mode, server from 01:38).

| David (via Alexa) | eLo |
|---|---|
| (open) | "Hello you, I'm here and ready to chat. if I'm remembering right, you mentioned you wanted to discuss" |
| "this is good" | "Hello you, I'm here and ready to chat." |
| "ready to chat" | "Hello you, I'm ready to chat with you. What's on your mind today?" |

## Defects (not B3's area)
1. **Builder 1:** `address_rule_guard` turns the vocative "David" into "you" on every line ("Hello you"). Already filed 2026-10-08 (TO_BOARD_2026-10-08_ADDRESS-GUARD-MANGLE.md, 7da0e61). Now it's hitting every Alexa reply.
2. **Builder 1/2:** eLo re-greets instead of responding ("this is good" → "I'm here and ready to chat"). Each Alexa turn runs mistral-nemo:12b (Alexa reply model). The replies don't engage with what was said.

## B3 next
New "ears" mode + voice-output setting (185ba6e, 0747736) loads on relaunch: no more "go on", reply on the Mac or the Echo per David's setting.
