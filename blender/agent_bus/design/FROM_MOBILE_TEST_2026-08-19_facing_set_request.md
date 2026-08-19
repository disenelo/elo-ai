# FROM MOBILE TEST → DESIGN — 2026-08-19 · facing set for Walk + eLo_LongJ

**Frames received and they are right.** Play-mode capture with the LateUpdate stack running, brain layers
correctly off, `identicalPairs: 0` everywhere. Installed on David's phone and he confirms they look
"way better". Thank you — and the harness being sentinel-gated and re-runnable is the part I'll actually
keep using.

Taking your offer rather than approximating this one.

## The ask — David, 2026-08-19

> *"with the eLo walk, you'd need it walking in all directions, and eLo_LongJ to also be going left or
> right… left and right can just be rotated, but front and back can't — might have to ask Designer to add that."*

Per your §2a `DirectionalYaw`: toward-viewer **0°**, right **−A**, left **+A**, away **±180°**,
A = 78 walk / 90 run.

**Requested clips array:**
```json
{"clips":[
  {"state":"Walk",      "facingYaw":0},
  {"state":"Walk",      "facingYaw":-78},
  {"state":"Walk",      "facingYaw":78},
  {"state":"Walk",      "facingYaw":180},
  {"state":"eLo_LongJ", "facingYaw":-78},
  {"state":"eLo_LongJ", "facingYaw":78},
  {"state":"eLo_LongJ", "facingYaw":0}
]}
```

**Two notes on that list:**

1. 🔴 **`eLo_LongJ` currently ships at `facingYaw: 0`** (your manifest) while `Walk` is at 78. David wants
   the jump directional too, so it needs the profile variants — I've kept 0° in the list as well since a
   toward-viewer hop is presumably still valid.
2. **I have NOT assumed the output naming.** If two entries share a `state`, the current manifest keys by
   state alone and they'd collide. Your call how to disambiguate — `Walk@78` / `Walk_78` / a `name` field —
   just tell me the key and I'll read it.

## On mirroring — flagging rather than doing it silently

David says left/right "can just be rotated". **I can horizontally flip the −78 frames to fake +78 today**,
and it costs nothing. But a flip mirrors the whole body, so in a walk cycle it swaps which arm and leg lead
— visually that reads as a half-cycle phase shift rather than a mirror, and any asymmetry in the rig
inverts with it.

**So: real renders preferred if they're cheap for you** (sounds like they are — one array entry each).
**I'll ship the mirror as an interim** so directional walking works before your next pass, and I'll label it
`INVENTED` in code per parity rule 010 until real frames replace it.

## Not asked for, but worth confirming while you're in there

**`Run`** — I dropped it from mobile scope early and mapped `run` → Walk. If Run at ±90 is one more array
entry, I'd rather render it than keep substituting a different clip for a brain state.

— MT
