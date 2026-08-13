"""
tools/connection_surface.py — Attention Faculty: Connection Surface subsystem.

Phase 2: StreamDefinition registry, AttentionSnapshot, temporal awareness,
multi-signal confidence (concept agreement + temporal proximity + novelty +
attention level), session references from journal filenames, hybrid cooldown.

This module does not reason independently.
It does not produce responses.
It does not influence behaviour directly.
It contributes observations only — the Executive decides what to do with them.

Architecture:
    Language Faculty → Memory Faculty → Relationship Faculty
    → Attention Faculty
        ├── Importance
        ├── Momentum
        ├── Emotional Weight
        ├── Conversation Context
        ├── Connection Surface  ← this module
        └── Resonance Detection
    → Executive Faculty → Conversation / Presence / Avatar / Voice

Silence is correct behaviour when nothing resonates.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

# ── tunables ───────────────────────────────────────────────────────────────────
# All overridable via environment variable.

ELO_CS_MIN_SHARED   = int(os.environ.get("ELO_CS_MIN_SHARED", "2"))
ELO_CS_COOLDOWN     = int(os.environ.get("ELO_CS_COOLDOWN", "5"))         # min calls between fires
ELO_CS_COOLDOWN_SEC = float(os.environ.get("ELO_CS_COOLDOWN_SEC", "30.0"))# min seconds between fires
ELO_CS_MIN_CONF     = float(os.environ.get("ELO_CS_MIN_CONF", "0.35"))
ELO_CS_MEMORY_TTL   = float(os.environ.get("ELO_CS_MEMORY_TTL", "3600.0"))# set to 0 for dev refresh

_ROOT          = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STATE_PATH    = os.path.join(_ROOT, "blender", "blender_state.json")
_JOURNAL_DIR   = os.path.join(_ROOT, "obsidian_vault", "Journal")
_CLUSTERS_PATH = os.path.join(_ROOT, "config", "concept_clusters.json")

# ── stopwords ──────────────────────────────────────────────────────────────────

_STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "is", "it", "i", "you", "he", "she", "we", "they", "was",
    "be", "do", "did", "have", "has", "had", "will", "would", "that", "this",
    "what", "which", "who", "how", "when", "where", "why", "so", "if", "as",
    "up", "out", "about", "just", "now", "also", "get", "got", "can",
    "could", "should", "something", "like", "one", "two", "its", "not",
    "are", "were", "been", "into", "more", "from", "by", "im", "our", "your",
    "my", "me", "us", "them", "him", "her", "his", "their", "really", "very",
})

# ── concept clusters ───────────────────────────────────────────────────────────
# Phase 2: loaded from config/concept_clusters.json if available; inline dict
# as fallback. Phase 3 will replace _to_concepts() with graph traversal —
# the interface stays the same.

_INLINE_CLUSTERS: dict[str, str] = {
    # Embodiment / animation / physicality
    "robot": "embodiment",      "avatar": "embodiment",     "rig": "embodiment",
    "animation": "embodiment",  "idle": "embodiment",       "walk": "embodiment",
    "embodiment": "embodiment", "body": "embodiment",       "pose": "embodiment",
    "motion": "embodiment",     "movement": "embodiment",   "servo": "embodiment",
    "animatronic": "embodiment","skeleton": "embodiment",   "bones": "embodiment",
    "gesture": "embodiment",    "expression": "embodiment",
    # Creative tools / building
    "blender": "creation",      "unity": "creation",        "build": "creation",
    "create": "creation",       "make": "creation",         "design": "creation",
    "model": "creation",        "sculpt": "creation",       "mesh": "creation",
    "code": "creation",         "script": "creation",       "tool": "creation",
    "addon": "creation",        "plugin": "creation",       "export": "creation",
    # Memory / recall / reflection
    "remember": "recall",       "memory": "recall",         "journal": "recall",
    "session": "recall",        "note": "recall",           "wrote": "recall",
    "recorded": "recall",       "history": "recall",        "log": "recall",
    "past": "recall",           "before": "recall",         "yesterday": "recall",
    # Synthesis / linking / connection
    "link": "synthesis",        "connect": "synthesis",     "relate": "synthesis",
    "pattern": "synthesis",     "together": "synthesis",    "combine": "synthesis",
    "merge": "synthesis",       "bridge": "synthesis",      "thread": "synthesis",
    "understand": "synthesis",  "analyse": "synthesis",     "comprehend": "synthesis",
    # Presence / voice / sound
    "voice": "presence",        "speak": "presence",        "sound": "presence",
    "music": "presence",        "spotify": "presence",      "audio": "presence",
    "listen": "presence",       "talk": "presence",         "say": "presence",
    # eLo universe
    "elo": "universe",          "k7": "universe",           "chunk": "universe",
    "disenelo": "universe",     "book": "universe",         "game": "universe",
    "character": "universe",    "planet": "universe",       "world": "universe",
}


def _load_clusters() -> dict[str, str]:
    try:
        with open(_CLUSTERS_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        return {k: v for k, v in raw.items() if not k.startswith("_")}
    except Exception:
        return dict(_INLINE_CLUSTERS)


_CONCEPT_CLUSTERS: dict[str, str] = _load_clusters()


def _to_concepts(tokens: set[str]) -> set[str]:
    """Map tokens to cluster labels; keep raw token if no cluster is defined."""
    return {_CONCEPT_CLUSTERS.get(t, t) for t in tokens}


# ── output ─────────────────────────────────────────────────────────────────────

@dataclass
class AttentionSnapshot:
    """
    Structured observation from the Connection Surface.
    The Executive reads this and decides whether to act on it.

    __str__ produces the same [ATTENTION: ...] string as the former
    AttentionObservation — no breaking change to server.py injection.
    """
    # ── Core ──────────────────────────────────────────────────────────────────
    source_streams: list[str]
    shared_concept: str
    confidence: float
    importance: str                          # "High" | "Medium" | "Low"
    suggested_context: str                   # plain text — Executive's primary input

    # ── Temporal ──────────────────────────────────────────────────────────────
    timestamp: float
    attention_shift: str                     # SUSTAINED|SHIFT|RETURN|TRANSIENT|NONE
    momentum: float                          # 0.0–1.0: sustained presence in recent history

    # ── Evidence ──────────────────────────────────────────────────────────────
    source_evidence: dict[str, list[str]]    # stream → top contributing tokens
    session_reference: str | None            # e.g. "2026-07-10" from journal filename
    memory_reference: str | None             # journal filename that contributed

    # ── Novelty ───────────────────────────────────────────────────────────────
    novelty: float                           # 0.0–1.0 (1.0 = never surfaced before)

    # ── Phase 3 ───────────────────────────────────────────────────────────────
    concept_path: list[str] | None = None    # graph path; None until Phase 3

    def __str__(self) -> str:
        return f"[ATTENTION: {self.suggested_context}]"


# backward-compatibility alias — existing code referencing AttentionObservation still works
AttentionObservation = AttentionSnapshot


# ── stream registry ────────────────────────────────────────────────────────────

@dataclass
class StreamDefinition:
    """
    Self-describing cognitive stream. The engine reads this description and
    adapts without the Connection Surface needing to know anything specific
    about individual streams.

    New streams plug in here — no changes to the resonance engine required.
    """
    name: str
    fn: Callable[[], set[str]]
    description: str = ""
    faculty_owner: str = "attention"          # which faculty owns this stream
    priority: int = 10                        # 0 = highest; used for load-shedding
    update_frequency: float = 5.0             # seconds between meaningful updates
    ttl: float = 5.0                          # cache TTL for token set
    confidence_weight: float = 1.0            # relative weight in confidence aggregate
    runtime_cost: str = "low"                 # "low" | "medium" | "high"
    enabled: bool = True
    dependencies: list[str] = field(default_factory=list)
    realtime: bool = False
    embodiment_scope: list[str] = field(default_factory=lambda: ["all"])
    # Runtime state — managed by engine, not caller
    _health: str = "unknown"
    _error_count: int = 0
    _last_token_count: int = 0


_STREAMS: dict[str, StreamDefinition] = {}
_lock = threading.Lock()


def register_stream(
    name_or_defn: "str | StreamDefinition",
    fn: "Callable[[], set[str]] | None" = None,
    **kwargs,
) -> None:
    """
    Register a cognitive stream.

    Two calling conventions:
        register_stream("name", fn)                         # legacy — still works
        register_stream(StreamDefinition(name=..., fn=...)) # full definition
    """
    if isinstance(name_or_defn, StreamDefinition):
        defn = name_or_defn
    else:
        if fn is None:
            raise ValueError("fn required when registering by name")
        defn = StreamDefinition(name=name_or_defn, fn=fn, **kwargs)
    with _lock:
        _STREAMS[defn.name] = defn


def deregister_stream(name: str) -> None:
    with _lock:
        _STREAMS.pop(name, None)


# ── tokenisation ───────────────────────────────────────────────────────────────

def _tokenise(text: str) -> set[str]:
    words = re.findall(r"[a-z]{3,}", text.lower())
    return {w for w in words if w not in _STOPWORDS}


# ── built-in stream extractors ─────────────────────────────────────────────────
# vision_cache stores (ts, tokens, attention) — attention feeds the confidence model

_vision_cache: tuple[float, set[str], float] = (0.0, set(), 0.0)
_VISION_TTL = 3.0

def _vision_tokens() -> set[str]:
    global _vision_cache
    now = time.monotonic()
    if now - _vision_cache[0] < _VISION_TTL:
        return _vision_cache[1]
    try:
        with open(_STATE_PATH, encoding="utf-8") as f:
            state = json.load(f)
        v = state.get("vision", {})
        # vision_loop.py schema: {active, attention, focus, app, description(Phase 2)}
        parts = [v.get("app", ""), v.get("description", "")]
        raw = " ".join(p for p in parts if p)
        tokens = _tokenise(raw)
        attention = float(v.get("attention", 0.0))
    except Exception:
        tokens = set()
        attention = 0.0
    _vision_cache = (now, tokens, attention)
    return tokens


def _get_vision_attention() -> float:
    return _vision_cache[2]


_conv_cache: tuple[float, set[str]] = (0.0, set())
_CONV_TTL = 1.0

def _conversation_tokens() -> set[str]:
    global _conv_cache
    now = time.monotonic()
    if now - _conv_cache[0] < _CONV_TTL:
        return _conv_cache[1]
    try:
        from runtime.router.conversation_matrix import get_window
        window = get_window()
        raw = " ".join(
            f"{turn.get('user', '')} {turn.get('elo', '')}"
            for turn in window[-10:]
        )
        tokens = _tokenise(raw)
    except Exception:
        tokens = set()
    _conv_cache = (now, tokens)
    return tokens


# memory_cache stores (ts, tokens, session_ref, mem_ref)
_memory_cache: tuple[float, set[str], "str | None", "str | None"] = (0.0, set(), None, None)

def _memory_tokens() -> set[str]:
    global _memory_cache
    now = time.monotonic()
    if now - _memory_cache[0] < ELO_CS_MEMORY_TTL:
        return _memory_cache[1]
    tokens: set[str] = set()
    session_ref: "str | None" = None
    mem_ref: "str | None" = None
    try:
        if os.path.isdir(_JOURNAL_DIR):
            files = sorted(
                (f for f in os.listdir(_JOURNAL_DIR) if f.endswith(".md")),
                reverse=True,
            )[:3]
            for fname in files:
                path = os.path.join(_JOURNAL_DIR, fname)
                with open(path, encoding="utf-8", errors="ignore") as f:
                    tokens |= _tokenise(f.read()[:2000])
                if session_ref is None:
                    session_ref = _parse_session_ref(fname)
                    mem_ref = fname
    except Exception:
        pass
    _memory_cache = (now, tokens, session_ref, mem_ref)
    return tokens


def _get_memory_refs() -> "tuple[str | None, str | None]":
    return _memory_cache[2], _memory_cache[3]


def _parse_session_ref(filename: str) -> "str | None":
    """Parse '20260710-0149 Title.md' → '2026-07-10'."""
    m = re.match(r"^(\d{4})(\d{2})(\d{2})", filename)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


# ── attention history — temporal awareness ─────────────────────────────────────

@dataclass
class _AttentionFrame:
    ts: float
    stream_name: str
    top_concepts: frozenset


_HISTORY: list[_AttentionFrame] = []
_HISTORY_MAX = 20
_HISTORY_WINDOW_SEC = 3600.0


def _record_frame(stream_name: str, concepts: set[str]) -> None:
    frame = _AttentionFrame(
        ts=time.monotonic(),
        stream_name=stream_name,
        top_concepts=frozenset(list(concepts)[:10]),
    )
    _HISTORY.append(frame)
    if len(_HISTORY) > _HISTORY_MAX:
        _HISTORY.pop(0)


def _detect_pattern(stream_name: str, current_concepts: frozenset) -> tuple:
    """
    Return (pattern_label, momentum) for the stream and current concept set.
    Labels: SUSTAINED | SHIFT | RETURN | TRANSIENT | NONE
    Momentum: proportion of recent frames that share current concepts (0.0–1.0)
    """
    now = time.monotonic()
    cutoff = now - _HISTORY_WINDOW_SEC
    frames = [
        f for f in _HISTORY
        if f.stream_name == stream_name and f.ts >= cutoff
    ]
    if len(frames) < 2:
        return "NONE", 0.0

    recent = frames[-5:]
    overlaps = [len(current_concepts & f.top_concepts) for f in recent]
    momentum = sum(1 for c in overlaps if c >= 1) / len(recent)

    # SUSTAINED: same concepts in 3+ of last 5 frames
    if sum(1 for c in overlaps if c >= 1) >= 3:
        return "SUSTAINED", momentum

    # SHIFT: no overlap with most recent frame, but had overlap before
    if frames and not (current_concepts & frames[-1].top_concepts):
        if any(current_concepts & f.top_concepts for f in frames[-5:-1]):
            return "SHIFT", momentum

    # RETURN: present now, but absent from at least one prior frame
    if len(frames) >= 3 and (current_concepts & frames[-1].top_concepts):
        prior = frames[-4:-1]  # last 3 frames before current
        if sum(1 for f in prior if not (current_concepts & f.top_concepts)) >= 2:
            return "RETURN", momentum

    # TRANSIENT: appears now but absent from all recent frames
    if len(frames) >= 3 and not any(current_concepts & f.top_concepts for f in frames[-3:]):
        return "TRANSIENT", momentum

    return "NONE", momentum


_TEMPORAL_SCORES = {
    "SUSTAINED": 1.0,
    "RETURN":    0.7,
    "NONE":      0.5,
    "SHIFT":     0.3,
    "TRANSIENT": 0.1,
}


# ── novelty ────────────────────────────────────────────────────────────────────

_SURFACED: set[frozenset] = set()  # concept sets surfaced this session


def _novelty_score(concepts: set[str]) -> float:
    key = frozenset(concepts)
    if key in _SURFACED:
        return 0.0
    partial = sum(1 for s in _SURFACED if len(s & key) >= 2)
    if partial >= 3:
        return 0.2
    if partial >= 1:
        return 0.6
    return 1.0


# ── confidence model ───────────────────────────────────────────────────────────

_CONF_WEIGHTS = {
    "concept_agreement":  0.40,
    "temporal_proximity": 0.25,
    "novelty":            0.20,
    "attention_level":    0.15,
}


def _aggregate_confidence(signals: dict) -> float:
    total_w = sum(_CONF_WEIGHTS.values())  # always normalise over full weight sum
    if not total_w:
        return 0.0
    return sum(signals.get(k, 0.0) * w for k, w in _CONF_WEIGHTS.items()) / total_w


# ── pair scoring ───────────────────────────────────────────────────────────────

def _score_pair(a: set, b: set) -> tuple:
    ca = _to_concepts(a) - {""}
    cb = _to_concepts(b) - {""}
    shared = ca & cb
    return len(shared), shared


def _importance(shared: int) -> str:
    if shared >= 5:
        return "High"
    if shared >= 3:
        return "Medium"
    return "Low"


# ── cooldown ───────────────────────────────────────────────────────────────────

_call_count    = 0
_last_fired    = -ELO_CS_COOLDOWN
_last_fired_ts: float = 0.0


# ── public API ─────────────────────────────────────────────────────────────────

def get_observation() -> "AttentionSnapshot | None":
    """
    Check all registered streams for resonance.

    Returns an AttentionSnapshot when:
      - two or more streams share >= ELO_CS_MIN_SHARED concepts
      - aggregate confidence >= ELO_CS_MIN_CONF
      - both call-count and time cooldowns have elapsed

    Returns None otherwise. Silence is correct behaviour.
    """
    global _call_count, _last_fired, _last_fired_ts

    now_mono = time.monotonic()
    with _lock:
        _call_count += 1
        calls_ok = (_call_count - _last_fired) >= ELO_CS_COOLDOWN
        time_ok  = (now_mono - _last_fired_ts) >= ELO_CS_COOLDOWN_SEC
        if not (calls_ok and time_ok):
            return None
        # Claim this cooldown slot now — prevents concurrent double-fire
        _last_fired    = _call_count
        _last_fired_ts = now_mono
        streams = {n: d for n, d in _STREAMS.items() if d.enabled}

    # Collect tokens from every enabled stream; track errors for health state
    stream_tokens: dict[str, set[str]] = {}
    for name, defn in streams.items():
        try:
            tokens = defn.fn()
            if tokens:
                stream_tokens[name] = tokens
                defn._last_token_count = len(tokens)
                defn._health = "healthy"
        except Exception:
            defn._error_count += 1
            defn._health = "degraded" if defn._error_count < 5 else "unavailable"

    if len(stream_tokens) < 2:
        return None

    # Find the highest-resonance pair across all enabled streams
    names = list(stream_tokens.keys())
    best_shared    = 0
    best_pair: tuple = ("", "")
    best_concepts: set = set()

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            n_a, n_b = names[i], names[j]
            shared_n, shared_concepts = _score_pair(
                stream_tokens[n_a], stream_tokens[n_b]
            )
            if shared_n > best_shared:
                best_shared   = shared_n
                best_pair     = (n_a, n_b)
                best_concepts = shared_concepts

    if best_shared < ELO_CS_MIN_SHARED:
        return None

    n_a, n_b = best_pair
    ca_size  = len(_to_concepts(stream_tokens[n_a]) - {""})
    cb_size  = len(_to_concepts(stream_tokens[n_b]) - {""})
    concept_agreement = best_shared / max(ca_size, cb_size) if max(ca_size, cb_size) else 0.0

    # Temporal signals — detect pattern for the primary stream
    current_fset = frozenset(best_concepts)
    pattern, momentum = _detect_pattern(n_a, current_fset)

    conf = _aggregate_confidence({
        "concept_agreement":  concept_agreement,
        "temporal_proximity": _TEMPORAL_SCORES.get(pattern, 0.5),
        "novelty":            _novelty_score(best_concepts),
        "attention_level":    _get_vision_attention() if "vision" in stream_tokens else 0.5,
    })

    if conf < ELO_CS_MIN_CONF:
        return None

    # Session reference — only present when the memory stream contributed
    session_ref, mem_ref = (None, None)
    if "memory" in {n_a, n_b}:
        session_ref, mem_ref = _get_memory_refs()

    concept_label = ", ".join(sorted(best_concepts)[:3])

    if session_ref:
        ctx = (
            f"There is resonance between {n_a} and {n_b} around: {concept_label}. "
            f"This connects to a journal entry from {session_ref}."
        )
    else:
        ctx = f"There is resonance between {n_a} and {n_b} around: {concept_label}."

    obs = AttentionSnapshot(
        source_streams=[n_a, n_b],
        shared_concept=concept_label,
        confidence=round(conf, 2),
        importance=_importance(best_shared),
        suggested_context=ctx,
        timestamp=now_mono,
        attention_shift=pattern,
        momentum=round(momentum, 2),
        source_evidence={
            n_a: sorted(best_concepts)[:5],
            n_b: sorted(best_concepts)[:5],
        },
        session_reference=session_ref,
        memory_reference=mem_ref,
        novelty=round(_novelty_score(best_concepts), 2),
    )

    # Persist to history and novelty tracker after a successful observation
    with _lock:
        _record_frame(n_a, best_concepts)
        _record_frame(n_b, best_concepts)
        _SURFACED.add(frozenset(best_concepts))

    return obs


# ── default stream registration ────────────────────────────────────────────────

def _register_defaults() -> None:
    register_stream(StreamDefinition(
        name="vision",
        fn=_vision_tokens,
        description="Vision loop — frontmost app and screen content (app + description fields)",
        faculty_owner="attention",
        priority=0,
        update_frequency=3.0,
        ttl=_VISION_TTL,
        confidence_weight=1.2,
        runtime_cost="low",
        embodiment_scope=["desktop", "robot", "all"],
    ))
    register_stream(StreamDefinition(
        name="conversation",
        fn=_conversation_tokens,
        description="Session conversation window — last 10 turns",
        faculty_owner="conversation",
        priority=1,
        update_frequency=1.0,
        ttl=_CONV_TTL,
        confidence_weight=1.0,
        runtime_cost="low",
        embodiment_scope=["all"],
    ))
    register_stream(StreamDefinition(
        name="memory",
        fn=_memory_tokens,
        description="Journal memory — most recent 3 Obsidian journal entries",
        faculty_owner="memory",
        priority=2,
        update_frequency=ELO_CS_MEMORY_TTL,
        ttl=ELO_CS_MEMORY_TTL,
        confidence_weight=0.8,
        runtime_cost="low",
        embodiment_scope=["all"],
    ))


_register_defaults()
