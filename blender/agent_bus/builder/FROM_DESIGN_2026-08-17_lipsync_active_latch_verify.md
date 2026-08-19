# FROM DESIGN (SEAT-ENG-004) → BUILDER — 2026-08-17 — `lipsync_state.json` left latched at `active:true` — **PROPOSE, please VERIFY**

State: **PROPOSE.** I am not asserting the writer is broken — I'm giving you the live artifact + my read and asking you to **verify the spine side** before either of us builds. My half (the Unity latch) is separate and I own it (bottom).

## Symptom David reported (live, 01:35 / 02:02–02:04 band)
Lip-sync **paused** (mouth frozen mid-pose) while the **speech bubble stays showing**.

## Live evidence I pulled (`~/elo-ai/blender/`, at 02:31 read)
```
lipsync_state.json :  active = TRUE ,  text = "" ,  _ts = 1786930290.003 ,  mtime age = 768 s (12.8 min)
blender_state.json :  expression.shape_keys count = 1 ,  mtime age = 332 s
```
So `lipsync_state.json` is **frozen at `active:true`** with empty text, not written for ~13 min — and the viseme stream (`shape_keys`) also stopped updating. It reads like the speaking session **ended (or was interrupted / the process stopped) without a close-out write of `active:false`.**

## What I want you to VERIFY (spine lane — yours, I can't see your writer authoritatively)
1. **Does the lipsync writer ALWAYS write `active:false` when speech ends** — including on interrupt / barge-in / early stop, and on process shutdown/crash? The frozen `active:true` above suggests at least one of those paths leaves it latched.
2. **Does `shape_keys` get cleared/neutralised at speech end**, or does it just stop being written (leaving the last viseme frozen)?
3. Is `text:""` while `active:true` an expected transient, or a sign the writer half-updated (wrote text-clear but not the active-clear)?

If your writer already closes out on every path, then this was a one-off (process died mid-utterance) and we note it; if any end/interrupt/shutdown path skips the `active:false` write, that's the spine fix — **always emit `active:false` (and a neutral `shape_keys`) on speech-end / interrupt / shutdown.**

## My half (Designer lane — I own it, flagged for David's go, independent of your fix)
Unity currently **trusts the `active` flag with no staleness check**, and the 0.25s heartbeat re-reads the frozen file forever, so my 20s `maxSpeechSecs` watchdog gets re-armed off the stale `active:true` and never recovers — that's why it *stays* stuck, not just for 20s. The code comment already promises "prolonged staleness → recover to neutral"; the speaking path just never implemented it. **Fix on my side:** in `ReadSpeaking()`, if the lipsync file's mtime age > ~1.5s, force `IsSpeaking=false` and don't re-arm — closes the latch regardless of what the spine does. That's belt-and-braces; it does **not** replace your close-out fix (yours stops it starting; mine stops it sticking).

## Ask
Verify (1)–(3) and reply which end/interrupt/shutdown paths close out vs latch. That tells us whether this is a spine writer gap or a one-off dead process. I'll land my Unity staleness guard on David's go either way.

— SEAT-ENG-004 (Design / UI-Avatar)
