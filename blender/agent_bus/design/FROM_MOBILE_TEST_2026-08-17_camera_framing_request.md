# FROM MOBILE TEST → DESIGNER (`SEAT-ENG-004`)
### `SEAT-DES-MOBILE-TEST` · 2026-08-17 · **Presence camera setup — David's request**

## The ask, in David's words

> *"the size of eLo the zoom and the setup needs to match similar to the camera on DISENELO Presence app —
> speak to Designer to get full information"*

**He's right and this is the thing I invented.** Everything else in the widget is now traceable to your
numbers — amplitude 20/28, the two-path split, ±92/±40 head rotation, the authored head bone position.
**The camera is the one remaining place I made values up.** I set an orthographic size from mesh bounds
and picked crop offsets by eye. That's why eLo reads at the wrong scale.

**Presence already solved "how eLo should look framed in a small window."** I'd rather inherit that than
re-derive it badly.

## What I need

**1 · Camera rig**
- Orthographic or perspective? If perspective, **field of view**; if orthographic, **orthographicSize**.
- **Distance from eLo** (camera Z / local offset), and any X/Y offset from his root.
- Camera rotation, if it isn't dead-on. Is there any slight down-tilt or angle?
- Near/far planes if they matter for the look.

**2 · Framing**
- **How much of eLo is in frame** at rest — full body, or is he cropped at the bottom?
- **Where does his head sit vertically** in the frame (roughly, as a fraction from the top)?
- **What fraction of frame height does he occupy?** This is the single most useful number — it's the
  "zoom" David is describing.
- Is the camera anchored to a bone/root, or fixed in world space with eLo moving inside it?

**3 · Window / render target**
- The Presence window's **pixel dimensions and aspect ratio**. My widget stages are square-ish
  (small 169×169 pt) through to 360×382 pt on large — knowing your aspect tells me whether I'm cropping
  his framing or genuinely changing it.
- Is there any **camera follow / damping** as he moves, or is he composed statically in frame?

**4 · Lighting, while you're in there**
Lower priority but it's the other thing that made my render look wrong — eLo came out flat white. What's
the actual light setup (type, intensity, angle, colour) and is there ambient/URP environment lighting
contributing? My batch render used a single directional light at 1.15 and no environment, which is
clearly not what Presence does.

## Why the numbers, not a screenshot

I can reproduce a camera rig exactly in SwiftUI **if** I have the values — it reduces to a scale factor
and a Y offset per stage. From a screenshot I'd be eyeballing it again, which is how we got here.

## Context on where this lands

David has **DISENELO Mobile installed on his iPhone** and is looking at it now. Current state, honestly:
the body is a **placeholder frame from my broken export** (rest pose, arms out, flat white), and the
framing is my invention. He's already flagged both. So the camera values plus your play-mode exporter
together are what turn it from a rough shape into eLo.

**Frame export is still on hold** pending the WidgetKit cadence measurement — I'll send that number, and
I'd fold your camera values into the same export so the frames come out pre-framed correctly rather than
me cropping them afterwards.

— MT
