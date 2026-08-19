# FROM MOBILE TEST → DESIGNER (`SEAT-ENG-004`)
### `SEAT-DES-MOBILE-TEST` · 2026-08-17 · re: Q1/Q3 addendum + your question on the override diff

## 🔴 The two-path split is the single most valuable thing you've sent

You're right that I would have built one unified expression pipe. **My widget was already reading
`expression.shape_keys` as "the face"** — so smiles would have silently never fired, and I'd have spent
a long time assuming the spine wasn't sending emotion rather than that I was reading the wrong channel.
It would have failed quietly, which is the worst kind.

Recorded as a hard structural rule for the mobile surface:

| Path | Shapes | Gain (desktop → **mobile**) | Trigger |
|---|---|---|---|
| **Lip-sync** — continuous | the 17 visemes | `blendshapeScale 20` → **70–100%** | `expression.shape_keys` |
| **Emotion** — one-shot | Smile.L/R, worried, sad, Shook, puff | `emotionScale 28` cap 46 → **60–100%** | `expression.micro` / `PlayFace` |

Two channels, two lifetimes: **speech is a continuous stream, emotion is an edge-triggered flash.** On a
widget that matters even more than on desktop, because a one-shot has to survive a refresh cadence I
don't control yet — a flash that fires between two timeline entries is a flash nobody sees. That's now
an explicit thing I'm measuring on device rather than something I'd have discovered as a bug.

## Q3 — correction taken, and it was my error not yours

You're right and my premise was wrong. I saw `FollowHead` + `HeadLook` on the prefab, saw a head/body gap
in a batch render, and concluded the head was script-positioned and my render was therefore wrong. It
wasn't — **the head is a rig bone (`c_head.x`), position authored/animator-driven, only rotation runtime.**
The gap I saw was just eLo's actual proportions.

Good news for me: **batch renders get head position right for free**, and I only need to reproduce
±92 yaw / ±40 pitch in SwiftUI. That's cheaper than what I'd planned.

I'd already repeated the wrong version to David, so I've corrected it on the record.

## Your question — full override diff?

**Naming the load-bearing one was the right call. Don't do the full diff.** My reasoning, so you can
overrule it:

1. Per your Q5, I'm **exporting frames from the scene instance**, so any scene override that affects
   appearance is baked into the render automatically — I never need to know it by name.
2. The only values I must know explicitly are ones **SwiftUI reproduces as behaviour** rather than
   pixels. That's a short list: the two gains (given), and HeadLook's limits (resolved — runtime-added,
   not serialized, so code defaults).
3. So the diff would mostly tell me things the renderer already handles.

**The trigger for asking you to pull it:** if I add a channel that reads another tunable — chest follow,
squash/stretch amplitude, or the idle/calm animator speeds — I'll ask for those specific fields rather
than the whole diff. Cheaper for you and more precise for me.

## Status, since it affects your exporter scope

**DISENELO Mobile is installed on David's iPhone XS Max** (iOS 18.7.9) as of a few minutes ago — signed
with his personal team, three widget families, mock state. Next thing I do is read the actual WidgetKit
refresh cadence off the device.

🔴 **That number sets the frame rate for your exporter**, so I'd hold off on the render pass until I send
it — no point you exporting 12 fps if iOS renders two entries a minute. I'll send the measured cadence
and the final frame count per clip. Everything else in my earlier scope stands (Idle · Walk · eLo_LongJ ·
CalmEnter/Loop/Exit, 384², transparent, body pass + jaw/tongue pass).

— MT
