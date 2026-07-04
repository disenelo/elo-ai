# Handover: Polling Optimisation — File Event Watcher
**Target**: eLo DesktopBuddy — Unity Agent
**File**: `EloOSAvatarReceiver.cs`
**Scope**: Replace fixed 250ms poll with event-driven file watching; keep poll as fallback heartbeat

## Problem

250ms poll means state transitions are visible up to 250ms late. During LLM thinking → speaking transitions this is perceptible. Lipsync phoneme updates at ~50ms intervals are also clipping the poll window.

## Architecture

Two watched files:
- `blender_state.json` — changes per cognitive turn (~1–3s). Drives mode, expression, head lean.
- `lipsync_state.json` — changes per phoneme (~50ms during speech). Drives mouth shapes / IsSpeaking.

**Important note:** Both files are written via atomic rename (`write to .tmp → os.replace()`). On macOS this may not fire a `Changed` event. Also watch `Created`.

## Dirty-Flag Pattern

File watcher callbacks fire on a background thread. Unity APIs are not thread-safe. Set a `volatile bool` flag in the callback; do the JSON parse in `Update`/`LateUpdate`.

```csharp
private volatile bool _blenderStateDirty = false;
private volatile bool _lipsyncStateDirty = false;
```

Watcher callbacks:

```csharp
void OnBlenderStateChanged(object s, FileSystemEventArgs e) => _blenderStateDirty = true;
void OnLipsyncStateChanged(object s, FileSystemEventArgs e) => _lipsyncStateDirty = true;
```

`Update` (main thread):

```csharp
void Update()
{
    if (_blenderStateDirty) { _blenderStateDirty = false; ReadBlenderState(); }
    if (_lipsyncStateDirty) { _lipsyncStateDirty = false; ReadLipsyncState(); }
}
```

## FSW Setup

```csharp
private FileSystemWatcher _blenderWatcher;
private FileSystemWatcher _lipsyncWatcher;

void InitWatchers()
{
    _blenderWatcher = new FileSystemWatcher(
        Path.GetDirectoryName(resolvedBlender),
        Path.GetFileName(resolvedBlender));
    _blenderWatcher.NotifyFilter        = NotifyFilters.LastWrite;
    _blenderWatcher.Changed            += OnBlenderStateChanged;
    _blenderWatcher.Created            += OnBlenderStateChanged; // atomic rename
    _blenderWatcher.EnableRaisingEvents = true;

    _lipsyncWatcher = new FileSystemWatcher(
        Path.GetDirectoryName(resolvedLipsync),
        Path.GetFileName(resolvedLipsync));
    _lipsyncWatcher.NotifyFilter        = NotifyFilters.LastWrite;
    _lipsyncWatcher.Changed            += OnLipsyncStateChanged;
    _lipsyncWatcher.Created            += OnLipsyncStateChanged;
    _lipsyncWatcher.EnableRaisingEvents = true;
}
```

Call `InitWatchers()` from `Start()`. Dispose both in `OnDestroy()`.

## Fallback Heartbeat

Keep the existing 250ms InvokeRepeating timer. On each tick, set both dirty flags — covers any FSW events missed on unusual volume/mount configurations.

```csharp
void HeartbeatTick()
{
    _blenderStateDirty = true;
    _lipsyncStateDirty = true;
}
```

## Acceptance

- Change `state.mode` in `blender_state.json` manually → avatar reacts within one frame, not up to 250ms.
- Play speech → phoneme updates fire without poll-lag stutter.
- Kill eLo OS process (no writes for 30s) → heartbeat continues, no exceptions.
- App quit → `OnDestroy` disposes watchers cleanly.
