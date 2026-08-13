# Unity Agent Handover — Exit Return Timing + Run Pace

## File to edit

`Assets/Scripts/DesktopBuddy.cs`

## The problem

When eLo runs off-screen (`ExitSequence`), `ReturnFromRunoff` fires on mouse-move after a `1.4s` delay. That delay was meant to feel "slow and dramatic" but reads as broken or frozen — he's gone, nothing happens, then he eventually runs back.

Additionally: the comment on `ambientReturnSpeedPx` says "(was 130 = looked like a walk)" and was bumped to 240. The exit run uses hard-coded `220f` — inconsistent with the return.

---

## Change 1 — Tighten the return delay

**Find** the serialized field (around line 991):
```csharp
[SerializeField] float ambientReturnDelay = 1.4f;      // "slow delayed" — wait after the mouse returns before running back
```

**Replace with:**
```csharp
[SerializeField] float ambientReturnDelay = 0.4f;      // tight — just enough to feel intentional, not frozen
```

This is a `[SerializeField]` — if the Inspector value was manually set to 1.4f it will not update automatically. Also update the Inspector value on the DesktopBuddy GameObject: `Ambient Return Delay` → `0.4`.

---

## Change 2 — Unify exit and return run speed

`ExitSequence` uses a hard-coded `220f` (line ~1035):
```csharp
float speedVp = 220f / sw;
```

`ReturnFromRunoff` uses `ambientReturnSpeedPx` (line ~1085):
```csharp
float speedVp = ambientReturnSpeedPx / sw;
```

The exit should use the same serialized value for consistency. In `ExitSequence`:

**Find:**
```csharp
float speedVp = 220f / sw;
```

**Replace with:**
```csharp
float speedVp = ambientReturnSpeedPx / sw;
```

Now both exit and return use the same speed value. Set `Ambient Return Speed Px` in Inspector to `260` (a clear, confident run — not slow, not frantic).

---

## Change 3 — Safety timeout on return

The 20s safety timeout in `TickAmbientReturn` (line ~1073) is too long — if eLo runs off and the mouse never moves, he's frozen off-screen for 20s.

**Find:**
```csharp
bool safety = Time.time - _dormantSince > 20f;                                       // never stuck off-screen
```

**Replace with:**
```csharp
bool safety = Time.time - _dormantSince > 8f;                                        // never stuck off-screen
```

8 seconds: long enough to feel intentional, short enough that a frozen off-screen eLo always recovers within one interaction cycle.

---

## Summary of Inspector values to set on DesktopBuddy GameObject

| Field | New value |
|---|---|
| Ambient Return Delay | 0.4 |
| Ambient Return Speed Px | 260 |

---

## What NOT to touch

- `ExitSequence()` logic (gun-check, speech wait, direction) — no changes
- `ReturnFromRunoff()` logic (start position, stop position, wrNeedsAttach) — no changes
- `EloIdleBehaviour.cs` — no changes
- Any other file

Three field value changes. One line change. One Inspector update.

---
Diagnosed: 2026-07-05
