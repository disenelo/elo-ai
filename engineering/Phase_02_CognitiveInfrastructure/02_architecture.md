# Phase 02 — Architecture (As-Built)

**Phase:** Cognitive Infrastructure
**Date:** 2026-07-10

---

## What Was Built

Phase 2 delivers the Connection Surface — a subsystem of the Attention Faculty. It observes registered cognitive streams, detects concept resonance between them, and produces a structured `AttentionSnapshot` injected into the Executive's context.

This is not a chatbot feature. It is cognitive infrastructure. eLo does not reference the snapshot directly — the Executive reads it as ambient context alongside the conversation.

---

## Core Components

### AttentionSnapshot (was: AttentionObservation)

The structured output of the Connection Surface.

```python
@dataclass
class AttentionSnapshot:
    source_streams:   list[str]        # which streams resonated
    shared_concept:   str              # the concept cluster that connected them
    confidence:       float            # 0.0–1.0 aggregate confidence
    importance:       str              # "low" | "medium" | "high"
    suggested_context: str             # human-readable summary → injected into g_ctx
    timestamp:        float            # time.time() of observation
    attention_shift:  str              # SUSTAINED | SHIFT | RETURN | TRANSIENT | NONE
    momentum:         float            # sustained attention duration (seconds)
    source_evidence:  dict[str,list]   # {stream_name: [tokens that fired]}
    session_reference: str | None      # "YYYY-MM-DD" from journal filename
    memory_reference:  str | None      # reserved for Phase 3
    novelty:          float            # 1.0 = first time, 0.0 = seen many times
    concept_path:     list[str] | None # reserved for Phase 3 graph traversal

AttentionObservation = AttentionSnapshot  # backward-compat alias
```

`__str__` → `[ATTENTION: {suggested_context}]` — the format the Executive reads. Unchanged from Phase 1.

### StreamDefinition

Self-describing stream object. New streams plug in via `register_stream()` without modifying the engine.

```python
@dataclass
class StreamDefinition:
    name:             str
    fn:               Callable[[], set[str]]   # returns tokens to observe
    description:      str = ""
    faculty_owner:    str = "attention"
    priority:         int = 10
    update_frequency: float = 5.0
    ttl:              float = 5.0
    confidence_weight: float = 1.0
    runtime_cost:     str = "low"
    enabled:          bool = True
    dependencies:     list[str] = field(default_factory=list)
    realtime:         bool = False
    embodiment_scope: list[str] = field(default_factory=lambda: ["all"])
    _health:          str = "unknown"
    _error_count:     int = 0
    _last_token_count: int = 0
```

### Attention History Ring Buffer

Tracks stream observations over time. Used for pattern detection.

```python
@dataclass
class _AttentionFrame:
    ts:           float       # time.monotonic()
    stream_name:  str
    top_concepts: frozenset   # concept clusters active at this moment
```

- Max 20 frames
- 3600s window (older frames discarded)
- `_detect_pattern()` → `(SUSTAINED|SHIFT|RETURN|TRANSIENT|NONE, momentum_float)`

### Multi-Signal Confidence

Aggregate confidence from 4 weighted signals:

| Signal | Weight | What It Measures |
|---|---|---|
| concept_agreement | 0.40 | How many streams share the concept |
| temporal_proximity | 0.25 | How recently each stream updated |
| novelty | 0.20 | How fresh this concept is (decay over repeated observations) |
| attention_level | 0.15 | Vision stream attention value |

Phase 3 adds: `memory_importance` (how significant this concept is in memory), `relationship_strength` (how connected this concept is in the Semantic World Model).

### Hybrid Cooldown

Both conditions must be true before a new observation fires:

```
calls_ok = (_call_count - _last_fired) >= ELO_CS_COOLDOWN     # default: 5 calls
time_ok  = (now_mono - _last_fired_ts) >= ELO_CS_COOLDOWN_SEC # default: 30.0 seconds
```

Environment variables: `ELO_CS_COOLDOWN`, `ELO_CS_COOLDOWN_SEC`, `ELO_CS_MIN_SHARED`, `ELO_CS_MIN_CONF`, `ELO_CS_MEMORY_TTL`

### Session Reference

Parses journal filenames to produce a dateable reference:

```python
def _parse_session_ref(filename: str) -> str | None:
    m = re.match(r"^(\d{4})(\d{2})(\d{2})", filename)
    if not m: return None
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
```

When present: `"This connects to a journal entry from 2026-07-10."` in `suggested_context`. Closes the Exhibit A gap — eLo can cite a specific journal date.

---

## Data Flow

```
stream_fn() → set[str] tokens
    ↓
_to_concepts(tokens) → set[str] cluster names  [keyword → cluster lookup]
    ↓
_score_pair(stream_A_concepts, stream_B_concepts) → (shared_concept, raw_score) | None
    ↓
_calc_confidence(raw_score, ...) → float  [multi-signal weighted aggregate]
    ↓
_detect_pattern(history) → (shift_type, momentum)
    ↓
_find_session_ref() → str | None  [scan obsidian_vault/Journal/]
    ↓
AttentionSnapshot(...)  [assembled]
    ↓
str(snapshot) → "[ATTENTION: ...]"
    ↓
g_ctx += "\n" + str(snapshot)  [server.py injection]
    ↓
Executive reads g_ctx  [frozen — no change]
```

---

## Registered Default Streams

| Stream | Source | Tokens |
|---|---|---|
| `conversation` | Last 3 g_ctx user messages | Words, deduplicated |
| `vision` | `blender_state.json["vision"]` | app + description (Phase 2) |
| `memory` | `blender_state.json["memory"]` | Last recall topics |
| `system` | `blender_state.json["state"]` | mode + activity |

All use `StreamDefinition` with `embodiment_scope: ["all"]`.

---

## Concept Clusters

Loaded from `config/concept_clusters.json`. 83 keywords → 6 clusters:
`embodiment`, `creation`, `recall`, `synthesis`, `presence`, `universe`

Inline fallback in `connection_surface.py` if file is absent.

Phase 3 replaces the flat lookup with traversable concept families.

---

## server.py Integration

```python
# server.py ~line 800, inside g_ctx assembly:
try:
    from tools.connection_surface import get_observation as _cs_observe
    _cs_obs = _cs_observe()
    if _cs_obs:
        g_ctx = f"{g_ctx}\n{_cs_obs}" if g_ctx else str(_cs_obs)
except Exception:
    pass
```

Silent fail — if Connection Surface raises anything, g_ctx is unchanged.

---

## vision_loop.py Addition

`_VISION_PROMPT` now requests `"description": "<5 words max>"` — primary screen activity in plain language (e.g. "rigging robot arm mesh").

`blender_state.json["vision"]` now contains:
```json
{
  "active": true,
  "attention": 0.73,
  "focus": {"x": 0.4, "y": 0.6},
  "app": "Blender",
  "description": "rigging robot arm mesh"
}
```

The vision stream's `_vision_tokens()` reads both `app` and `description` for richer vocabulary.
