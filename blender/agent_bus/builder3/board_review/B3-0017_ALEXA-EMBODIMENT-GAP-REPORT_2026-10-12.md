# Board review — WO-B3-0017 Alexa as eLo's second embodiment: GAP REPORT (Builder 3, 2026-10-12)

The card asks for a gap report before building. What's wired vs missing:

## Wired and live-verified
| Piece | Status | Evidence |
|---|---|---|
| Ears: Alexa → eLo's brain | ✅ live | 2026-10-11 23:01, LaunchRequest accepted via the permanent Tailscale endpoint |
| Same brain: same turn pipeline as Mac chat (`_process_turn_queued`), inner thought, world knowledge, memory | ✅ | Same queue; reply "good to see you **again**" shows memory; `[WORLD_KNOWLEDGE …]` in the turn |
| Mouth: eLo's own ElevenLabs voice from the Echo | ✅ live | David heard it; log `voice on echo (Alexa input)` |
| Permanent endpoint, key expiry off | ✅ | card 0008 |
| Device choice: Alexa input → Echo; desk → Mac; idle → Echo | ✅ built | WO-0018 (e7e11fa), tests |

## Gaps
1. **eLo doesn't know he's in the Alexa body.** `runtime/memory_origin.current_embodiment()` reads `blender_state.json["embodiment"]`; Alexa turns never set it, so he answers as "desktop" and memories are tagged desktop. `runtime/embodiment_capabilities` already defines an `ALEXA` body. **Owner: Builder 1** (memory_origin / server per-turn state). Suggest: the per-turn model override path (f449819) also carries `embodiment="alexa"` for Alexa turns and restores it afterwards, without touching Presence's display.
2. **WKG updated from Alexa conversations:** same pipeline as chat, so it should, but it's **not verified on an Alexa turn specifically**. Needs Builder 2's live check (their WO-0010 WKG live growth) on one Alexa turn.
3. **Inner voice on the Mac only:** eLo's thoughts are generated on Alexa turns, but the inner-voice audio never plays on the Echo (voice_engine inner calls aren't routed). **Owner: Builder 1's file**; one-line change to use the same routing. David asked about it 2026-10-11.
4. **Reply latency ~20 s:** Builder 1 WO-0118. Also blocks gap 5.
5. **Free conversation without "Alexa" every sentence:** Alexa only keeps the mic open if the skill answers within 8 s. Once replies are under ~7 s, B3 switches the skill to keep the session open (≈ 10 lines in B3's alexa_ingress). **Blocked on gap 4.**
6. **"Hello you":** the address guard sometimes rewrites "David" (B1, filed).
7. **No instant "heard you" cue on Alexa:** the 20 s of silence feels broken. B3 can add a short non-verbal sound. Waiting on a Board/David call.

## B3 can do now (no other seat's files)
- Gap 7 (sound cue) on a yes.
- Gap 5 as soon as latency drops.
Everything else above belongs to B1/B2 and is listed for routing.

## Update (B3, 2026-10-12): gap 7 BUILT (d7df7d3)
- "Heard you" chime: 0.4 s two-note sound on the Echo the instant David's words reach eLo (no words, not eLo's voice). ALEXA_HEARD_CUE=off disables. Needs a Presence relaunch to load.
- Gap 5 (open conversation): no build needed. ALEXA_REPLY=skill already keeps Alexa listening after each reply; it becomes usable once B1's WO-0118 gets replies under ~7 s.
