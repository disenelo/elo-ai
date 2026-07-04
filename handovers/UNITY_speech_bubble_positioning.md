# Handover: Speech Bubble Positioning
**Target**: eLo DesktopBuddy — Unity Agent
**Scope**: Unity layout only — no eLo OS changes required

## Problem

The speech bubble arrow does not land flush with the mouth area. The offset is fixed and does not track head animation or jaw movement.

## Investigation Steps

1. **Locate the bubble anchor.** Find the speech bubble GameObject. Determine whether it is:
   - Parented to a World Space canvas, Screen Space canvas, or directly to the head bone transform
   - Positioned by a fixed Inspector offset or driven each frame in script

2. **Head bone world position.** The head bone is `c_head.x` (Auto-Rig Pro naming). Get its world position via `headBone.position` each frame — do not cache it, animations move it continuously.

3. **If parented to a Screen Space canvas:** Reposition each frame using `Camera.WorldToScreenPoint(headBone.position)` plus a viewport-relative vertical offset. A fixed `anchoredPosition` will not track the head.

4. **If parented to a World Space canvas or 3D object:** Verify the parent transform is the head bone itself, not the armature root. A local-space offset authored at rest pose is valid here.

## Jaw Offset

When the jaw drops during speech, the mouth position shifts downward. Read the current jaw-open value from `EloOSAvatarReceiver.jawNow` (0–1) each frame and apply a downward offset proportional to that value.

Target calculation every `LateUpdate`:

```csharp
Vector3 mouthWorld = headBone.position
                   + headBone.up * baseVerticalOffset       // negative = below head centre
                   + Vector3.down * (jawNow * jawDropScale); // tune jawDropScale to mesh

// Screen Space canvas:
Vector2 screenPos = Camera.main.WorldToScreenPoint(mouthWorld);
bubbleRect.position = screenPos + new Vector2(0, bubblePaddingPx);

// World Space:
bubbleTransform.position = mouthWorld + Vector3.up * bubblePaddingWorld;
```

The arrow tip must point to `mouthWorld`. If the bubble uses an anchored arrow sprite, ensure the arrow pivot is at the tip.

## Acceptance

- Idle animation plays — arrow stays on the mouth throughout the lean cycle.
- `jawNow` at 1.0 — arrow tip follows the dropped jaw position.
- Window resized (Screen Space) — bubble tracks correctly.
