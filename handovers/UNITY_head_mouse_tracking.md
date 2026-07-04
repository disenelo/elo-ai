# Handover: Head Roll Mapped to Mouse Position
**Target**: eLo DesktopBuddy — Unity Agent
**Scope**: Unity animation layer only — no eLo OS changes, no blender_state.json writes

## Context

The head bone is currently driven by `expression.head_lean` from `blender_state.json` (emotional lean). This task adds a secondary mouse-tracking offset on top — ambient awareness, not a stare.

## Implementation

Add to `LateUpdate`, after the emotional lean is applied, so the mouse offset always composes on top.

### Mouse Sampling

```csharp
Vector2 viewport = Camera.main.ScreenToViewportPoint(Input.mousePosition);
float xOffset = viewport.x - 0.5f;   // -0.5 left → +0.5 right
float yOffset = viewport.y - 0.5f;   // -0.5 bottom → +0.5 top
```

### Rotation Mapping

```csharp
float targetYaw   = xOffset * 12f;   // ±6° max
float targetPitch = yOffset *  8f;   // ±4° max
```

### Attention Timer — 30% active

eLo notices the mouse intermittently, not continuously.

```csharp
private bool  _trackingActive   = false;
private float _trackingTimer    = 0f;

void UpdateTrackingTimer()
{
    _trackingTimer -= Time.deltaTime;
    if (_trackingTimer <= 0f)
    {
        _trackingActive = !_trackingActive;
        float cycle     = Random.Range(8f, 20f);
        _trackingTimer  = _trackingActive ? cycle * 0.30f : cycle * 0.70f;
    }
}
```

### Smoothed Mouse Contribution

```csharp
private Quaternion _mouseContribution = Quaternion.identity;

void ApplyMouseOffset(Transform headBone)
{
    UpdateTrackingTimer();

    Quaternion target = _trackingActive
        ? Quaternion.Euler(-targetPitch, targetYaw, 0f)
        : Quaternion.identity;   // fade to neutral when not tracking

    _mouseContribution = Quaternion.Lerp(
        _mouseContribution, target, Time.deltaTime * 8f);

    // Apply after emotional lean
    headBone.rotation = headBone.rotation * _mouseContribution;
}
```

Call `ApplyMouseOffset` at the end of `LateUpdate`.

## Constraints

- Do not modify any eLo OS state files
- Do not replace the emotional lean — compose after it
- If head bone is Animator-driven, apply in `LateUpdate` (after Animator.Update)

## Acceptance

- Head still responds to `head_lean` from `blender_state.json`
- Moving mouse left/right causes subtle yaw; up/down causes subtle pitch
- Tracking goes inactive periodically — head smoothly returns to emotional lean baseline
- No twitching or frame-rate jumps
