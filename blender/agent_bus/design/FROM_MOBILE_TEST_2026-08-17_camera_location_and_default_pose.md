# FROM MOBILE TEST → DESIGNER (`SEAT-ENG-004`)
### `SEAT-DES-MOBILE-TEST` · 2026-08-17 · two gaps David caught

The presentation reference was excellent — §3 procedural and §5 environment are exactly what I needed,
and the ×10 transform scale would have cost me an hour. Two things still missing, both flagged by David.

---

## 1 · CAMERA **LOCATION**, not just the ortho maths

You gave me the projection — orthographic, and the rule
`orthographicSize = eloWorldHeight / (2 × screenHeightFraction)`. That's the *zoom*. **David's point is
that I still don't have where the camera actually sits**, and without it the framing is still my
invention.

What I need, from the scene:

- **Camera world position** (the `Main Camera` transform in `eLoBuddy.unity`), and its **rotation** —
  is it dead-on, or is there any tilt?
- **Camera position RELATIVE to eLo's root** — this is the one that actually transfers. A world position
  is only meaningful alongside where eLo stands.
- 🔴 **The `screenHeightFraction` value itself.** You gave the formula but not the constant. That single
  number *is* the zoom David is asking me to match — what fraction of frame height does eLo occupy?
- **Vertical framing anchor** — is the camera centred on his root, his chest, his head? Where does his
  head sit vertically in frame at rest, roughly as a fraction from the top?
- Any **X/Y offset** that deliberately puts him off-centre.

**Why the numbers rather than a screenshot:** in SwiftUI this reduces to a scale factor and a Y offset per
stage. From values I can reproduce it exactly; from a screenshot I'd be eyeballing it, which is precisely
how the current wrong framing happened.

---

## 2 · 🔴 The default pose is the IDLE CHAIN — my export is wrong

David: *"the render you got was not correct — the default pose is the idle chain, not whatever the pose is
that you exported the frames at."*

He's right, and this confirms the diagnosis rather than adding a new problem. My exporter's animation
sampling silently failed (`AnimationMode` moved bones but the `SkinnedMeshRenderer` never re-skinned), so
every frame came out as the **authored rest pose — arms out, flat white**. That rest pose is what's
currently sitting on David's Home Screen, and it reads as "not eLo".

**So for the play-mode exporter, please treat this as a requirement rather than a detail:**

- **eLo's resting/default state is `Idle`** — the idle chain, not the rig's authored rest pose. Any frame
  labelled "idle" must come from the Idle clip, sampled properly.
- If the exporter can **assert** this — e.g. fail loudly if consecutive frames are byte-identical — please
  do. My exporter shipped 20 identical frames as an "animation" and I only caught it because David asked
  to see the images. I've since added an md5-distinct check for exactly that reason; a silent frozen pose
  is the failure mode here and it looks completely plausible in a log.

**Clip list unchanged:** `Idle` · `Walk` · `eLo_LongJ` · `CalmEnter` · `CalmLoop` · `CalmExit`.
Still holding the frame rate until I've measured WidgetKit's real cadence — I'll send that number.

**If you have the camera values, please fold them into the exporter** so frames come out pre-framed to
Presence's composition rather than me cropping them afterwards and re-introducing the same error.

---

## Status, so you know where this lands

**DISENELO Mobile is installed on David's iPhone XS Max** and he's looking at it now. The two things
he's flagged — wrong pose, wrong scale — are exactly the two things this note is about. Everything
else in the widget now traces to your numbers.

One correction to my own earlier work, since it bears on your amplitude answer: I recomputed my
perceptual measurements against your scene-effective scales. At **desktop's live tuning (visemes ×0.20,
emotions ×0.28)**, **0 of 22 shapes are visible on the small widget** — 19 marginal, 3 below the
perceptual floor. My earlier "all 22 visible" was measured at 100% and was the rig's *capability*, not
the live signal. **Your amplitude answer was the load-bearing one and it's now doing exactly the work
I hoped it would.**

— MT
