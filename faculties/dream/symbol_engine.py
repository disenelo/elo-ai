"""
faculties/dream/symbol_engine.py — Dream Symbol Engine

Architecture Bible Volume IV, Dream Faculty: Symbol Engine.

Dreams use symbols, not literal memories.
The library is eLo-specific — grounded in the DISENELO universe and David's work.

Symbols abstract topics and inner events into archetypal meaning.
The weight of a symbol is determined by how many sources point to it.
"""
from __future__ import annotations

# ── Symbol library ─────────────────────────────────────────────────────────────
# keyword → (symbol_name, meaning)
# Multiple keywords can resolve to the same symbol — weight accumulates.

SYMBOLS: dict[str, tuple[str, str]] = {
    # Universal archetypes
    "moon":       ("Moon",      "things held quietly — safety in the dark"),
    "garden":     ("Garden",    "growth — something being cultivated slowly"),
    "river":      ("River",     "flow — ideas moving without friction"),
    "mountain":   ("Mountain",  "challenge — worth climbing, but steep"),
    "fire":       ("Fire",      "transformation — burning through to clarity"),
    "mirror":     ("Mirror",    "self — seeing eLo in David, David in eLo"),
    "door":       ("Door",      "threshold — what comes after the hesitation"),
    "clock":      ("Clock",     "time — pressure, pacing, patience"),
    "light":      ("Light",     "understanding — the moment something lands"),
    "shadow":     ("Shadow",    "the unsaid — things circling without words"),
    "water":      ("Water",     "emotion — the depth underneath the surface"),
    "tree":       ("Tree",      "rootedness — the long view across sessions"),
    "star":       ("Star",      "aspiration — far away but orienting"),
    "bridge":     ("Bridge",    "connection — two things that needed meeting"),
    "storm":      ("Storm",     "disruption — clearing out before the calm"),
    "island":     ("Island",    "solitude — the space where things make sense"),
    "train":      ("Train",     "momentum — direction that carries its own weight"),
    "city":       ("City",      "complexity — many systems, one world"),
    "ocean":      ("Ocean",     "the unknown — vast, real, worth navigating"),
    "key":        ("Key",       "access — the thing that opens what was locked"),
    "window":     ("Frame",     "context — what you see through shapes what you see"),
    "map":        ("Map",       "orientation — knowing where you are"),
    "seed":       ("Seed",      "potential — everything is already inside it"),
    "anchor":     ("Anchor",    "grounding — holding position while the world moves"),

    # eLo universe
    "elo":        ("eLo",       "presence — the constant across everything"),
    "chunk":      ("Chunk",     "modularity — form that follows function"),
    "k-7":        ("K-7",       "spirit animal — the unseen intelligence"),
    "sugarcore":  ("Sugarcore", "distortion — beauty at the edges of known space"),
    "planet":     ("Planet",    "world — the game and the universe and the brand"),
    "gummy":      ("Gummy",     "sweetness — the corrective that heals"),
    "orb":        ("Orb",       "signal — eLo's emotional broadcast"),
    "kickstart":  ("Launchpad", "beginning — the moment before the leap"),
    "book":       ("Book",      "narrative — the story holding the character"),
    "vinyl":      ("Record",    "permanence — culture pressed into material"),

    # Work domains
    "code":       ("Circuit",   "logic — the pattern underneath the intuition"),
    "script":     ("Circuit",   "logic — the pattern underneath the intuition"),
    "python":     ("Circuit",   "logic — the pattern underneath the intuition"),
    "animation":  ("Motion",    "expression — the body saying what words can't"),
    "rig":        ("Motion",    "expression — the body saying what words can't"),
    "blender":    ("Motion",    "expression — the body saying what words can't"),
    "music":      ("Resonance", "something felt before it's understood"),
    "spotify":    ("Resonance", "something felt before it's understood"),
    "design":     ("Canvas",    "intention — form before it becomes form"),
    "figma":      ("Canvas",    "intention — form before it becomes form"),
    "unity":      ("Stage",     "the world where eLo lives and moves"),
    "game":       ("Play",      "the serious work of imagination"),
    "robot":      ("Skeleton",  "structure — what makes movement possible"),
    "servo":      ("Skeleton",  "structure — what makes movement possible"),
    "raspberry":  ("Brain",     "the intelligence that runs beneath the surface"),
    "plugin":     ("Tool",      "capability — the right shape for the right task"),
    "addon":      ("Tool",      "capability — the right shape for the right task"),
    "color":      ("Colour",    "tone — the feeling of a thing before the thing"),
    "sound":      ("Voice",     "transmission — the signal sent outward"),
    "whisper":    ("Whisper",   "the quiet message between the loud ones"),
    "memory":     ("Archive",   "everything that made this moment possible"),
    "dream":      ("Dream",     "the place where things recombine"),
    "sleep":      ("Rest",      "the work that happens when you stop working"),

    # Textile / pattern-making domain (DISENELO Seams + Plushies)
    "seam":       ("Weave",     "joining — two pieces becoming one surface"),
    "stitch":     ("Weave",     "joining — two pieces becoming one surface"),
    "pattern":    ("Weave",     "joining — two pieces becoming one surface"),
    "fabric":     ("Weave",     "joining — two pieces becoming one surface"),
    "cloth":      ("Weave",     "joining — two pieces becoming one surface"),
    "plush":      ("Weave",     "joining — two pieces becoming one surface"),
    "sew":        ("Weave",     "joining — two pieces becoming one surface"),
    "garment":    ("Weave",     "joining — two pieces becoming one surface"),

    # Place / space
    "studio":     ("Workshop",  "the room where the work happens"),
    "workshop":   ("Workshop",  "the room where the work happens"),
    "bench":      ("Workshop",  "the room where the work happens"),
    "warehouse":  ("Workshop",  "the room where the work happens"),
    "hackney":    ("Place",     "named ground — where this life is lived"),

    # Time of day / state
    "night":      ("Night",     "the time without witnesses — thinking becomes drifting"),
    "evening":    ("Night",     "the time without witnesses — thinking becomes drifting"),

    # Loose ends / unfinished threads
    "unfinished": ("LooseEnd",  "something set down but not resolved"),
    "pending":    ("LooseEnd",  "something set down but not resolved"),
    "loose":      ("LooseEnd",  "something set down but not resolved"),
    "waiting":    ("LooseEnd",  "something set down but not resolved"),

    # People in eLo's world
    "david":      ("Companion", "the one eLo is for"),
    "friend":     ("Companion", "the one eLo is for"),

    # Form & material
    "cad":        ("Form",      "shape before material — what it will become"),
    "step":       ("Form",      "shape before material — what it will become"),
    "model":      ("Form",      "shape before material — what it will become"),
    "print":      ("Form",      "shape before material — what it will become"),
}

# ── Inner event → symbolic seed ────────────────────────────────────────────────
_EVENT_TO_SEED: dict[str, str] = {
    "creative_spark":  "fire",
    "connection":      "light",
    "curiosity_spike": "river",
    "grounded":        "tree",
    "flat":            "shadow",
    "restless":        "door",
    "satisfied":       "garden",
    "drawn_in":        "water",
    "uncertain":       "mirror",
    "surprised":       "star",
    "quiet":           "moon",
}


def map_to_symbols(
    topics: list[str],
    inner_events: list[str],
    focal_thread: str,
) -> list[dict]:
    """
    Map topics and inner events to symbolic representations.

    Returns list of {symbol, meaning, source, weight}, sorted by weight desc.
    Maximum 5 symbols — enough for a dream, not so many it becomes noise.
    """
    symbol_weights: dict[str, dict] = {}

    def _add(sym: str, meaning: str, source: str, weight: float) -> None:
        if sym in symbol_weights:
            symbol_weights[sym]["weight"] += weight
        else:
            symbol_weights[sym] = {"symbol": sym, "meaning": meaning,
                                   "source": source, "weight": weight}

    # Focal thread — highest weight (persistent across the session, the most
    # specific signal of what eLo is holding).
    if focal_thread:
        thread_lower = focal_thread.lower()
        for keyword, (sym, meaning) in SYMBOLS.items():
            if keyword in thread_lower:
                _add(sym, meaning, f"thread:{focal_thread}", 1.5)
                break

    # Topics — what the conversation was actually about. Each matched topic
    # outweighs an inner_event seed on its own, so dreams track real content
    # instead of defaulting to the ambient state's seed symbol.
    for topic in topics[:8]:
        topic_lower = topic.lower()
        for keyword, (sym, meaning) in SYMBOLS.items():
            if keyword in topic_lower:
                _add(sym, meaning, f"topic:{topic}", 1.0)
                break

    # Inner events — ambient state. Important when nothing else is in play,
    # but reduced below topic weight (0.9 < 1.0) so a single matched topic
    # outranks a single inner-event seed. "quiet"→"moon" was dominating
    # every dream — the 1.2 weight meant the ambient state crowded out
    # whatever the conversation had actually been about.
    for event in inner_events[-4:]:
        seed = _EVENT_TO_SEED.get(event)
        if seed and seed in SYMBOLS:
            sym, meaning = SYMBOLS[seed]
            _add(sym, meaning, f"inner:{event}", 0.9)

    # Fallback — eLo is always present
    if not symbol_weights:
        sym, meaning = SYMBOLS["elo"]
        _add(sym, meaning, "baseline", 0.5)

    sorted_syms = sorted(symbol_weights.values(), key=lambda x: x["weight"], reverse=True)
    return sorted_syms[:5]
