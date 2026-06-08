# eLo Core → Unity Connection

**Method**: Local JSON file bridge
**No networking required**. Python writes. Unity reads. Easy to debug.

---

## How it works

```
Python (eLo Core)           JSON file              Unity
─────────────────           ─────────────          ──────────────────────
state_engine          →     avatar/                →   EloSignalReceiver.cs
emotion_engine        →     avatar_signal.json     →   EloAnimationMapper.cs
identity_engine       →                            →   Animator Controller
avatar_bridge         →                            →   eLo Character + Orb
```

On every turn: `core_engine.turn()` calls `unity_bridge.export_from_core()` → writes signal to file.
Unity polls the file every N milliseconds → reads signal → applies to Animator.

---

## Python setup

Signal is written automatically by `core_engine.py` on every turn when `UNITY_BRIDGE_ENABLED=1`:

```bash
export UNITY_BRIDGE_ENABLED=1
export ELO_SIGNAL_PATH=/path/to/elo-ai/avatar/avatar_signal.json
python main.py
```

Or call manually from anywhere:
```python
from avatar.unity_bridge import export_from_core
export_from_core(state="exploring", emotion="curious", intent="expand_idea", energy=0.7)
```

---

## Signal format

```json
{
  "state":   "exploring",
  "emotion": "curious",
  "intent":  "show_curiosity",
  "energy":  0.7,
  "mode":    "adventure",

  "identity": {
    "perspective": "symbolic",
    "intent":      "expand_idea",
    "bias":        "lean_imaginative"
  },

  "animation_hints": {
    "head_tilt_deg":    9.6,
    "lean_amount":      0.32,
    "bounce_intensity": 0.16,
    "movement_speed":   0.7
  },

  "orb": {
    "intensity": 0.9,
    "mode":      "slow_pulse"
  }
}
```

Full schema: `avatar/signal_schema.json`

---

## Unity C# receiver

### EloSignalReceiver.cs

Place in `Assets/_Project/Scripts/eLo/` in Unity.

```csharp
using UnityEngine;
using System.IO;
using System.Collections;

[System.Serializable]
public class EloAnimationHints {
    public float head_tilt_deg;
    public float lean_amount;
    public float bounce_intensity;
    public float rotation_speed;
    public float movement_speed;
}

[System.Serializable]
public class EloOrb {
    public float intensity;
    public string mode;
}

[System.Serializable]
public class EloAvatarSignal {
    public string state;
    public string emotion;
    public string intent;
    public float  energy;
    public string mode;
    public EloAnimationHints animation_hints;
    public EloOrb orb;
    public string project;
    public string posture;
    public string pace;
}

public class EloSignalReceiver : MonoBehaviour
{
    [Header("Signal File")]
    public string signalFilePath = "avatar/avatar_signal.json";
    public float  pollIntervalSeconds = 0.1f;  // 10x per second

    [Header("References")]
    public EloAnimationMapper animationMapper;

    private EloAvatarSignal _lastSignal;
    private string          _lastRaw = "";

    void Start()
    {
        StartCoroutine(PollSignalFile());
    }

    IEnumerator PollSignalFile()
    {
        while (true)
        {
            yield return new WaitForSeconds(pollIntervalSeconds);
            ReadSignal();
        }
    }

    void ReadSignal()
    {
        if (!File.Exists(signalFilePath)) return;

        string raw = File.ReadAllText(signalFilePath);
        if (raw == _lastRaw) return;  // no change
        _lastRaw = raw;

        try {
            EloAvatarSignal signal = JsonUtility.FromJson<EloAvatarSignal>(raw);
            _lastSignal = signal;
            animationMapper?.ApplySignal(signal);
        }
        catch (System.Exception e) {
            Debug.LogWarning($"EloSignalReceiver: failed to parse signal — {e.Message}");
        }
    }

    public EloAvatarSignal CurrentSignal => _lastSignal;
}
```

---

### EloAnimationMapper.cs

```csharp
using UnityEngine;

public class EloAnimationMapper : MonoBehaviour
{
    [Header("Animator")]
    public Animator animator;

    [Header("Orb")]
    public Light orbLight;
    public ParticleSystem orbParticles;

    // Animator parameter names
    const string P_ENERGY  = "Energy";
    const string P_HEAD    = "HeadTilt";
    const string P_LEAN    = "Lean";
    const string P_BOUNCE  = "Bounce";
    const string P_SPEED   = "MovementSpeed";

    public void ApplySignal(EloAvatarSignal signal)
    {
        if (!animator) return;

        // State → trigger
        animator.SetTrigger(StateToTrigger(signal.state));

        // Continuous parameters
        animator.SetFloat(P_ENERGY,  signal.energy);
        animator.SetFloat(P_SPEED,   signal.animation_hints.movement_speed);
        animator.SetFloat(P_HEAD,    signal.animation_hints.head_tilt_deg);
        animator.SetFloat(P_LEAN,    signal.animation_hints.lean_amount);
        animator.SetFloat(P_BOUNCE,  signal.animation_hints.bounce_intensity);

        // Orb
        if (orbLight)
            orbLight.intensity = signal.orb.intensity * 2f;  // scale to Unity range
    }

    string StateToTrigger(string state)
    {
        switch (state) {
            case "exploring":  return "Explore";
            case "building":   return "Build";
            case "focused":    return "Focus";
            case "reflecting": return "Reflect";
            case "playful":    return "Play";
            case "resting":    return "Rest";
            default:           return "Explore";
        }
    }
}
```

---

## Animator controller setup

Create these parameters in the Unity Animator:

| Parameter | Type | Range | Driven by |
|---|---|---|---|
| `Energy` | Float | 0–1 | energy |
| `HeadTilt` | Float | -20 to 20 | animation_hints.head_tilt_deg |
| `Lean` | Float | -0.3 to 0.5 | animation_hints.lean_amount |
| `Bounce` | Float | 0–1 | animation_hints.bounce_intensity |
| `MovementSpeed` | Float | 0–1 | animation_hints.movement_speed |
| `Explore` | Trigger | — | state == exploring |
| `Build` | Trigger | — | state == building |
| `Reflect` | Trigger | — | state == reflecting |
| `Rest` | Trigger | — | state == resting |
| `Play` | Trigger | — | state == playful |
| `Focus` | Trigger | — | state == focused |

---

## Testing the connection

1. Start Python: `python main.py`
2. Say something in the conversation
3. Check `avatar/avatar_signal.json` — the file should update
4. In Unity: verify `EloSignalReceiver` reads the file path correctly
5. Enter play mode — character should respond to state changes

**Debug**: Open `avatar/avatar_signal.json` in any text editor while running — watch it update live.

---

## The long-term picture

```
Python eLo Core → avatar_signal.json → Unity eLo Character
                                     → Physical Robot (same signal)
```

Both Unity and the robot consume the same JSON schema.
Same brain. Different bodies. Same signal.
