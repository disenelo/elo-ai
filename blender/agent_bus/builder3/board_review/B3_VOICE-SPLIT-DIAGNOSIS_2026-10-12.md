# Board review / → Builder 1 — "voice split Mac and Echo": live diagnosis (B3, 2026-10-12 17:25) — e91b20e

Re: board_review/REQUEST_2026-10-12_DESIGNER_VOICE-SPLIT-MAC-AND-ECHO.md

## Live test (B3 POSTed one /chat turn; connect=start, Echo connected; audio processes recorded)
| t | device | what |
|---|---|---|
| +1 s | Echo ✅ | ack ("give me a second", B1 pre_ack → voice_engine.speak) |
| +8 s | Echo ✅ | a second short line (source not identified; the Designer saw a separate "hello" path) |
| +9 s | **Mac ❌** | **inner-thought voice** (voice_engine `_speak_thread_inner` afplay) |
| +33 s | Echo ✅ | the reply "Hello, David." |

Also checked directly: `voice_engine.speak("…")` → Echo; `speak_inner("…")` → Mac. Bluetooth was connected (verified).

## Findings
1. **Replies DO reach the Echo.** What David experienced is the ~20–30 s gap after the ack (it sounds like eLo stopped). Latency = B1 WO-0118.
2. **Inner voice is never routed** (voice_engine lines ~444, ~468 say-fallback, ~512). Builder 1's file. Exact fix:
   ```python
   # in voice_engine, a twin of _play_proc for the inner voice:
   def _play_inner_proc(path):
       try:
           from tools import echo_speaker as _es
           if _es.speaking():
               p = _es.popen_play(path)
               if p is not None:
                   return p
       except Exception:
           pass
       return subprocess.Popen(["afplay", "-v", str(_INNER_AFPLAY_VOL), path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
   ```
   Use it at the two `["afplay", "-v", …]` sites. (The Echo has no per-clip volume; the inner register comes from the inner TTS settings.) The `say` fallbacks (~381, ~468) can take `-a "Echo Dot-Studio"` when `speaking()` is True.
3. **Two greetings** (the Designer's "different hello"): the unidentified second Echo line at +8 s. Worth a B1/B2 look at which path speaks a greeting besides the reply.

## B3 changes this round (B3 files only)
- Connect pressed → soft chime **on the Echo** (David: "should he say hello or light the blue ring?"). The ring can't be lit over Bluetooth, and a scripted hello would break "only the brain speaks as eLo".
- Tests no longer read David's real voice/connect state files.
