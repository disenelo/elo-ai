"""
core/memory_engine.py — eLo AI memory system.

Five memory categories — each shapes behaviour, not just stores data:

    Identity Memory   — who the user says they are, their stated goals
    Project Memory    — what's being built, project trajectory and context
    Creative Memory   — aesthetic preferences, imaginative patterns, style
    World Memory      — eLo universe entity references, symbolic language
    User Memory       — behavioral patterns, emotional arc, recurring states

Every category produces three outputs:
    style_hint    — how eLo should adapt its tone for this response
    reference     — specific content to echo or acknowledge if relevant
    association   — a conceptual connection this memory makes available

A synthesis layer collapses all five into:
    response_style   — overall tone instruction
    key_reference    — the most important thing to surface
    key_association  — the most important connection to make
    future_idea      — a direction this work is pointing toward

Public API:
    load_registry()
    resolve_project(text, registry)
    store_interaction(user_input, response, mode, project_tag)
    retrieve(query, top_k)
    retrieve_by_project(project_tag, top_k)
    retrieve_structured(query, project_hint)     — legacy 4-block format
    build_memory_influence(query, project_hint)  — full influence dict
    export_memory()
    load_long_term_memory()
    load_session()
"""

import json
import os
import re
from collections import Counter
from datetime import datetime


# ── paths ──────────────────────────────────────────────────────────────────────

_DIR           = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
_STORE_PATH    = os.path.join(_DIR, "memory", "interactions.json")
_REGISTRY_PATH = os.path.join(_DIR, "memory", "project_registry.json")
_EXPORT_PATH   = os.path.join(_DIR, "memory", "export_memory.md")
_SESSION_PATH  = os.path.join(_DIR, "memory", "session.json")


# ── concept groups ─────────────────────────────────────────────────────────────
# Each group is a cluster of related ideas. Interactions are tagged at write time
# so retrieval can match on meaning rather than exact words.

_CONCEPT_GROUPS: dict = {
    "creation":    [r"\bbuild\b", r"\bmake\b", r"\bcreate\b", r"\bdesign\b",
                    r"\bstructure\b", r"\bsystem\b", r"\btool\b", r"\bchunk\b"],
    "narrative":   [r"\bstory\b", r"\bworld\b", r"\bmyth\b", r"\bcharacter\b",
                    r"\bnarrative\b", r"\blore\b", r"\bjourney\b", r"\buniverse\b"],
    "identity":    [r"\bi am\b", r"\bi want\b", r"\bwho am\b", r"\bpurpose\b",
                    r"\bmeaning\b", r"\bmy project\b", r"\bmy work\b"],
    "emotion":     [r"\bfeel\b", r"\bsense\b", r"\bwrong\b", r"\bstuck\b",
                    r"\bsugarcore\b", r"\boverwhelm\b", r"\bchaos\b", r"\bdistort\b"],
    "imagination": [r"\bwhat if\b", r"\bimagine\b", r"\bwonder\b",
                    r"\bexplore\b", r"\bbecome\b", r"\bpossible\b"],
    "technical":   [r"\bcode\b", r"\bmodule\b", r"\bfunction\b",
                    r"\bengine\b", r"\bapi\b", r"\bmemory\b", r"\btest\b"],
}

# eLo universe entities — tracked as symbolic themes in export
_UNIVERSE_ENTITIES = ["eLo", "Chunk", "K-7", "Core", "Sugarcore"]

# Stopwords excluded from keyword scoring to reduce noise
_STOPWORDS = {
    "the", "a", "an", "is", "it", "in", "on", "at", "to", "of", "and",
    "or", "but", "i", "my", "me", "this", "that", "for", "with", "be",
    "so", "do", "not", "what", "how", "why", "was", "are", "have",
}


# ── memory category signals ────────────────────────────────────────────────────
# Used at write time to tag each interaction with its memory categories.
# An interaction can belong to multiple categories.

_CATEGORY_SIGNALS: dict = {
    "identity": [
        r"\bi am\b", r"\bi want\b", r"\bi need\b", r"\bi believe\b",
        r"\bmy goal\b", r"\bmy project\b", r"\bmy work\b",
        r"\bwho am\b", r"\bpurpose\b", r"\bmeaning\b", r"\bi'?m building\b",
    ],
    "project": [
        r"\bbuilding\b", r"\bworking on\b", r"\bproject\b", r"\bsystem\b",
        r"\bversion\b", r"\bfeature\b", r"\bmodule\b", r"\bimplementation\b",
        r"\bshipping\b", r"\bdeploying\b", r"\bintegrat\b", r"\barchitecture\b",
    ],
    "creative": [
        r"\bdesign\b", r"\baesthetic\b", r"\bstyle\b", r"\bvisual\b",
        r"\bfeel\s+like\b", r"\blook\s+like\b", r"\bcolou?r\b", r"\btexture\b",
        r"\bsound\b", r"\bmusic\b", r"\bartistic\b", r"\bcreative\b",
        r"\bimagine\b", r"\bwhat\s+if\b", r"\bnarrative\b", r"\bstory\b",
    ],
    "world": [
        r"\beLo\b", r"\bChunk\b", r"\bK-7\b", r"\bCore\b", r"\bSugarcore\b",
        r"\buniverse\b", r"\bworld\b", r"\bmyth\b", r"\bsymbolic\b",
        r"\bcharacter\b", r"\blore\b", r"\bcanon\b",
    ],
    "user": [
        r"\bfeel\b", r"\bstuck\b", r"\bwrong\b", r"\bchaos\b",
        r"\boverwhelm\b", r"\bexhausted\b", r"\bconfused\b",
        r"\bbut\b.*\b(don'?t|not|hate|resist)\b",  # contradictions
        r"\bi\s+don'?t\s+know\b", r"\bnot\s+sure\b", r"\bscattered\b",
    ],
}


def _classify_memory_categories(text: str) -> list:
    """Return all memory categories that match the given text."""
    text_lower = text.lower()
    matched = []
    for category, patterns in _CATEGORY_SIGNALS.items():
        if any(re.search(p, text_lower) for p in patterns):
            matched.append(category)
    return matched


# ── concept detection ──────────────────────────────────────────────────────────

def _detect_concepts(text: str) -> list:
    """Return list of concept group names matched in text."""
    text_lower = text.lower()
    matched = []
    for concept, patterns in _CONCEPT_GROUPS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                matched.append(concept)
                break
    return matched


def _query_words(text: str) -> set:
    """Tokenise text, strip stopwords, return meaningful word set."""
    return {w for w in re.findall(r"\w+", text.lower()) if w not in _STOPWORDS}


# ── project registry ───────────────────────────────────────────────────────────

def load_registry() -> dict:
    if os.path.exists(_REGISTRY_PATH):
        with open(_REGISTRY_PATH) as f:
            return json.load(f)
    return {"project_namespace": "elo_core", "active_projects": {}}


def resolve_project(text: str, registry: dict) -> str:
    """Return the project namespace most relevant to the input text, or elo_core."""
    text_lower = text.lower()
    for project_id, info in registry.get("active_projects", {}).items():
        # match on project id or any linked system name
        candidates = [project_id, project_id.replace("_", " ")]
        candidates += info.get("linked_systems", [])
        if any(c in text_lower for c in candidates):
            return project_id
    return registry.get("project_namespace", "elo_core")


# ── interaction store ──────────────────────────────────────────────────────────

def _load_store() -> list:
    if os.path.exists(_STORE_PATH):
        with open(_STORE_PATH) as f:
            return json.load(f)
    return []


def _save_store(interactions: list):
    os.makedirs(os.path.dirname(_STORE_PATH), exist_ok=True)
    with open(_STORE_PATH, "w") as f:
        json.dump(interactions, f, indent=2)


def store_interaction(
    user_input: str,
    response: str,
    mode: str,
    project_tag: str = "elo_core",
):
    """Append one interaction record to the persistent store."""
    combined = user_input + " " + response
    record = {
        "timestamp":         datetime.utcnow().isoformat() + "Z",
        "project_tag":       project_tag,
        "mode":              mode,
        "user":              user_input,
        "response":          response,
        "concepts":          _detect_concepts(combined),
        "memory_categories": _classify_memory_categories(user_input),
    }
    interactions = _load_store()
    interactions.append(record)
    _save_store(interactions)
    _update_session(record)


# ── session state ──────────────────────────────────────────────────────────────

def _update_session(record: dict):
    session = {"last_interaction": record}
    with open(_SESSION_PATH, "w") as f:
        json.dump(session, f, indent=2)


def load_session() -> dict:
    if os.path.exists(_SESSION_PATH):
        with open(_SESSION_PATH) as f:
            return json.load(f)
    return {}


# ── retrieval ─────────────────────────────────────────────────────────────────

def _score_record(
    record: dict,
    query_words: set,
    query_concepts: set,
    project_hint: str,
    recency_index: int,
    total: int,
) -> float:
    """
    Composite relevance score for one record.

    Components:
        keyword_score   — normalised word overlap (stopwords removed)
        concept_score   — bonus for matching concept groups
        project_boost   — multiplier when record shares the active project
        recency_weight  — linear decay: newest = 1.0, oldest ≈ 0.1
    """
    text = (record.get("user", "") + " " + record.get("response", "")).lower()
    record_words = _query_words(text)

    overlap = len(query_words & record_words)
    if not query_words:
        keyword_score = 0.0
    else:
        keyword_score = overlap / len(query_words)

    record_concepts = set(record.get("concepts", []))
    concept_score = 0.4 * len(query_concepts & record_concepts)

    project_boost = 1.5 if record.get("project_tag") == project_hint else 1.0

    # recency_index 0 = oldest, total-1 = newest
    recency = 0.1 + 0.9 * (recency_index / max(total - 1, 1))

    return (keyword_score + concept_score) * project_boost * (0.4 + 0.6 * recency)


def retrieve(query: str, top_k: int = 5, project_hint: str = "elo_core") -> list:
    """
    Return up to top_k past interactions scored by:
        keyword overlap + concept match + project alignment + recency.

    project_hint biases results toward the active project namespace.
    """
    interactions = _load_store()
    if not interactions:
        return []

    q_words    = _query_words(query)
    q_concepts = set(_detect_concepts(query))
    total      = len(interactions)

    scored = []
    for i, record in enumerate(interactions):
        score = _score_record(record, q_words, q_concepts, project_hint, i, total)
        if score > 0:
            scored.append((score, record))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:top_k]]


def retrieve_by_project(project_tag: str, top_k: int = 10) -> list:
    """Return the most recent interactions tagged to a specific project."""
    interactions = _load_store()
    matches = [r for r in interactions if r.get("project_tag") == project_tag]
    return matches[-top_k:]


# ── export ────────────────────────────────────────────────────────────────────

def _section_identity_evolution(interactions: list) -> list:
    """
    Section 1 — Identity evolution.
    Surfaces how the user's goals, self-description, and creative direction have shifted.
    """
    _IDENTITY_SIGNALS = [
        r"\bi am\b", r"\bi want\b", r"\bi need\b", r"\bmy project\b",
        r"\bmy work\b", r"\bi think\b", r"\bi realize\b", r"\bwho am\b",
        r"\bmy goal\b", r"\bi'm building\b",
    ]

    identity_records = []
    for record in interactions:
        text = record.get("user", "").lower()
        if any(re.search(p, text) for p in _IDENTITY_SIGNALS):
            identity_records.append(record)

    lines = ["## 1. Identity Evolution", ""]

    if not identity_records:
        lines.append("_No identity-signal interactions recorded yet._")
        return lines

    # show earliest, a midpoint if there are enough, and most recent
    checkpoints = [identity_records[0]]
    if len(identity_records) > 2:
        checkpoints.append(identity_records[len(identity_records) // 2])
    if len(identity_records) > 1:
        checkpoints.append(identity_records[-1])

    seen = set()
    for record in checkpoints:
        ts = record.get("timestamp", "")[:10]
        key = record["user"][:60]
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"**{ts}** — {record['user'][:120]}")
        lines.append("")

    # dominant mode across identity records
    mode_counts = Counter(r.get("mode", "?") for r in identity_records)
    dominant = mode_counts.most_common(1)[0][0] if mode_counts else "?"
    lines.append(f"_Identity conversations tend toward **{dominant}** mode._")

    return lines


def _section_project_evolution(interactions: list, registry: dict) -> list:
    """
    Section 2 — Project evolution.
    Shows trajectory for each active project: first touch, recent direction, volume.
    """
    lines = ["## 2. Project Evolution", ""]

    projects = registry.get("active_projects", {})
    if not projects:
        lines.append("_No active projects in registry._")
        return lines

    by_project: dict = {}
    for record in interactions:
        tag = record.get("project_tag", "elo_core")
        by_project.setdefault(tag, []).append(record)

    for project_id, info in projects.items():
        records = by_project.get(project_id, [])
        lines.append(f"### {project_id}")
        lines.append(f"Type: {info.get('type', '?')} · Status: {info.get('status', '?')}")
        lines.append(f"Interactions: {len(records)}")

        if records:
            first = records[0]
            last  = records[-1]
            lines.append(f"- First: *{first['user'][:80]}*")
            if len(records) > 1:
                lines.append(f"- Recent: *{last['user'][:80]}*")

            concepts = Counter(c for r in records for c in r.get("concepts", []))
            if concepts:
                top = ", ".join(f"{c} ({n})" for c, n in concepts.most_common(3))
                lines.append(f"- Dominant concepts: {top}")
        else:
            lines.append("- No interactions recorded yet.")

        lines.append("")

    return lines


def _section_emotional_patterns(interactions: list) -> list:
    """
    Section 3 — Emotional patterns.
    Mode distribution and recurring emotional states across all interactions.
    """
    lines = ["## 3. Emotional Patterns", ""]

    if not interactions:
        lines.append("_No interactions recorded yet._")
        return lines

    mode_counts   = Counter(r.get("mode", "?") for r in interactions)
    concept_counts = Counter(c for r in interactions for c in r.get("concepts", []))

    lines.append("**Mode distribution:**")
    total = sum(mode_counts.values())
    for mode, count in mode_counts.most_common():
        pct = int(100 * count / total)
        lines.append(f"- {mode}: {count} ({pct}%)")

    lines.append("")
    lines.append("**Concept distribution:**")
    for concept, count in concept_counts.most_common(6):
        lines.append(f"- {concept}: {count}")

    # emotional arc: compare first third vs last third
    if len(interactions) >= 6:
        third = len(interactions) // 3
        early_modes = Counter(r.get("mode") for r in interactions[:third])
        late_modes  = Counter(r.get("mode") for r in interactions[-third:])
        early_dom   = early_modes.most_common(1)[0][0] if early_modes else "?"
        late_dom    = late_modes.most_common(1)[0][0]  if late_modes  else "?"
        lines.append("")
        if early_dom == late_dom:
            lines.append(f"_Mode has been consistently **{early_dom}** across the session._")
        else:
            lines.append(f"_Arc: started in **{early_dom}** mode, shifted toward **{late_dom}**._")

    return lines


def _section_symbolic_themes(interactions: list) -> list:
    """
    Section 4 — Recurring symbolic themes.
    Tracks eLo universe entity mentions and other repeated symbolic language.
    """
    lines = ["## 4. Recurring Symbolic Themes", ""]

    if not interactions:
        lines.append("_No interactions recorded yet._")
        return lines

    entity_counts: dict = {e: 0 for e in _UNIVERSE_ENTITIES}
    all_text = ""

    for record in interactions:
        combined = record.get("user", "") + " " + record.get("response", "")
        all_text += combined + "\n"
        combined_lower = combined.lower()
        for entity in _UNIVERSE_ENTITIES:
            if entity.lower() in combined_lower:
                entity_counts[entity] += 1

    lines.append("**eLo Universe entity mentions:**")
    for entity, count in sorted(entity_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            lines.append(f"- {entity}: {count}")
    if all(v == 0 for v in entity_counts.values()):
        lines.append("_No universe entities mentioned yet._")

    # most repeated non-stopword content words
    all_words = [w for w in re.findall(r"\b[a-z]{4,}\b", all_text.lower()) if w not in _STOPWORDS]
    word_freq = Counter(all_words).most_common(12)
    if word_freq:
        lines.append("")
        lines.append("**Most repeated themes:**")
        for word, count in word_freq:
            lines.append(f"- `{word}` ({count}×)")

    return lines


def export_memory() -> str:
    """
    Write a human- and AI-readable snapshot of all memory to export_memory.md.

    Sections:
        1. Identity evolution
        2. Project evolution
        3. Emotional patterns
        4. Recurring symbolic themes
    """
    interactions = _load_store()
    registry     = load_registry()

    header = [
        "# eLo AI — Memory Export",
        f"> Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "> Human and AI readable. Injected as long-term context at session start.",
        f"> Total interactions: {len(interactions)}",
        "",
        "---",
        "",
    ]

    body = []
    body += _section_identity_evolution(interactions)
    body += ["", "---", ""]
    body += _section_project_evolution(interactions, registry)
    body += ["---", ""]
    body += _section_emotional_patterns(interactions)
    body += ["", "---", ""]
    body += _section_symbolic_themes(interactions)
    body += ["", "---", "", "_End of memory export._", ""]

    os.makedirs(os.path.dirname(_EXPORT_PATH), exist_ok=True)
    with open(_EXPORT_PATH, "w") as f:
        f.write("\n".join(header + body))

    return _EXPORT_PATH


# ── structured retrieval ──────────────────────────────────────────────────────

def retrieve_structured(query: str, project_hint: str = "elo_core") -> dict:
    """
    Return memory organised into four semantic blocks for offline response generation.

    Blocks:
        identity  — interactions with identity signals ("I am", "I want", "my project")
        project   — interactions tagged to project_hint, scored by relevance
        emotional — interactions in emotion/distortion concept space
        symbolic  — interactions mentioning eLo universe entities

    Each block is a list of record dicts, most relevant last.
    """
    interactions = _load_store()
    if not interactions:
        return {"identity": [], "project": [], "emotional": [], "symbolic": []}

    q_words    = _query_words(query)
    q_concepts = set(_detect_concepts(query))
    total      = len(interactions)

    _IDENTITY_SIGNALS  = [r"\bi am\b", r"\bi want\b", r"\bi need\b",
                          r"\bmy project\b", r"\bmy work\b", r"\bwho am\b"]
    _EMOTIONAL_SIGNALS = [r"\bfeel\b", r"\bstuck\b", r"\bwrong\b",
                          r"\bsugarcore\b", r"\boverwhelm\b", r"\bchaos\b"]
    _ENTITY_NAMES      = ["eLo", "Chunk", "K-7", "Core", "Sugarcore"]

    identity  = []
    project   = []
    emotional = []
    symbolic  = []

    for i, record in enumerate(interactions):
        user_text = record.get("user", "").lower()

        if any(re.search(p, user_text) for p in _IDENTITY_SIGNALS):
            identity.append(record)

        if record.get("project_tag") == project_hint:
            score = _score_record(record, q_words, q_concepts, project_hint, i, total)
            if score > 0:
                project.append((score, record))

        if any(re.search(p, user_text) for p in _EMOTIONAL_SIGNALS):
            emotional.append(record)

        if any(e.lower() in user_text for e in _ENTITY_NAMES):
            symbolic.append(record)

    # sort project by score, keep top 5; others keep chronological order, cap at 5
    project_sorted = [r for _, r in sorted(project, key=lambda x: x[0], reverse=True)[:5]]

    return {
        "identity":  identity[-5:],
        "project":   project_sorted,
        "emotional": emotional[-5:],
        "symbolic":  symbolic[-5:],
    }


# ── memory influence ──────────────────────────────────────────────────────────
#
# This is the layer that makes memory active rather than passive.
# Instead of returning raw records for the caller to re-derive,
# build_memory_influence() returns ready-to-use signals:
#
#   tone_signal       — dominant emotional pattern the user has been in recently
#   dominant_mode     — which mode has dominated recent turns
#   recurring_concepts — concepts appearing 2+ times in the last 8 interactions
#   entity_frequency  — universe entity mention counts across all history
#   concept_pairs     — concepts that cluster together for this specific user
#   returning_theme   — human-readable string when user keeps revisiting same ground
#   project_momentum  — which project is most active in recent interactions
#   symbolic_echo     — entity-specific note when an entity forms a pattern
#   raw_blocks        — the four typed blocks from retrieve_structured()

_TONE_CONCEPT_MAP = {
    "emotion":     "distorted",
    "identity":    "reflective",
    "imagination": "curious",
    "creation":    "focused",
    "narrative":   "curious",
    "technical":   "focused",
}

_RETURNING_THEME_PHRASES = {
    "creation":    "The building territory keeps coming up.",
    "narrative":   "The world-making territory keeps coming up.",
    "identity":    "The question of who this is for — or what it's really about — keeps surfacing.",
    "emotion":     "The emotional register of this work keeps returning.",
    "imagination": "The 'what if' layer keeps pulling at this.",
    "technical":   "The structural/technical layer keeps coming back.",
}

_ENTITY_ECHO_PHRASES = {
    "eLo":       "eLo has been the lens for several of these turns — explorer mode, moving before the map.",
    "Chunk":     "Chunk keeps appearing — there's a fragmentation-and-reassembly pattern in this work.",
    "K-7":       "K-7 keeps showing up — the emotional signal layer is active and persistent.",
    "Core":      "Core keeps appearing — navigation and orientation are real concerns right now.",
    "Sugarcore": "Sugarcore has been present across multiple turns — the overload state is a recurring condition.",
}


def _detect_tone_signal(recent: list) -> str:
    """Derive dominant tone from recent interactions' concept distribution."""
    if not recent:
        return "neutral"
    concept_counts = Counter(c for r in recent for c in r.get("concepts", []))
    if not concept_counts:
        return "neutral"
    dominant_concept = concept_counts.most_common(1)[0][0]
    return _TONE_CONCEPT_MAP.get(dominant_concept, "neutral")


# ── memory drift control ──────────────────────────────────────────────────────
#
# Problem: a single recent distorted interaction can dominate tone_signal
# even if 20 prior interactions show a stable neutral pattern.
#
# Fix: weight older consistent patterns higher than recent spikes.
# Recent interactions get lower weight. Long-term patterns get higher weight.
#
# This layer is purely informational — it does NOT affect routing or mode.
# It stabilises the tone/familiarity signals that the generation layer reads.


def _stability_weight(age_idx: int, total: int) -> float:
    """
    Compute stability weight for one memory record.

    age_idx = 0  → oldest record in the window → weight 1.0
    age_idx = N-1 → newest record            → weight 0.3

    Effect: a stable long-term pattern outweighs a recent spike.
    Recent interactions still contribute — they just carry less weight.

    Returns a float in [0.3, 1.0].
    """
    if total <= 1:
        return 1.0
    return round(1.0 - 0.7 * (age_idx / max(total - 1, 1)), 3)


def _detect_tone_stable(interactions: list, window: int = 15) -> str:
    """
    Stability-weighted tone detection.

    Unlike _detect_tone_signal() which weights all recents equally,
    this applies the stability weight so that:
        - a single recent distorted turn does not override a stable long-term neutral
        - a consistent long-term pattern resists short-term emotional spikes
        - the returned tone reflects the weighted history, not just the last 8 turns

    Does NOT change retrieval logic or concept detection.
    Only changes HOW the concepts are weighted before picking the dominant tone.
    """
    recent = interactions[-window:] if len(interactions) >= window else interactions
    n = len(recent)

    if not recent:
        return "neutral"

    weighted: dict = {}
    for age_idx, record in enumerate(recent):
        # age_idx 0 = oldest = high weight, age_idx n-1 = newest = low weight
        w = _stability_weight(age_idx, n)
        for concept in record.get("concepts", []):
            weighted[concept] = weighted.get(concept, 0.0) + w

    if not weighted:
        return "neutral"

    dominant = max(weighted, key=lambda c: weighted[c])
    return _TONE_CONCEPT_MAP.get(dominant, "neutral")


def _compute_pattern_confidence(interactions: list, window: int = 12) -> float:
    """
    Estimate how stable the memory pattern is (0.0 = unstable, 1.0 = very stable).

    Confidence is the consistency of the dominant concept across the window:
        high confidence → long-term consistent pattern (memory signals are reliable)
        low confidence  → recent divergence or insufficient history

    Used to expose pattern reliability — does not affect any decision.
    """
    if len(interactions) < 3:
        return 0.3   # insufficient data → low confidence

    recent = interactions[-window:] if len(interactions) >= window else interactions
    turn_dominants = []
    for record in recent:
        concepts = record.get("concepts", [])
        if concepts:
            turn_dominants.append(concepts[0])

    if not turn_dominants:
        return 0.3

    overall_dominant = Counter(turn_dominants).most_common(1)[0][0]
    consistency = turn_dominants.count(overall_dominant) / len(turn_dominants)
    return round(min(1.0, consistency), 2)


def _detect_tone_drift(interactions: list) -> bool:
    """
    Detect whether recent tone signal has drifted from long-term baseline.

    Returns True if the last 3 turns show a different dominant concept from
    the older half of history — indicating a temporary spike, not a real shift.

    Useful for suppressing spurious "distorted" tone signals from a single bad turn.
    """
    if len(interactions) < 6:
        return False

    midpoint   = len(interactions) // 2
    long_term  = interactions[:midpoint]
    recent_3   = interactions[-3:]

    lt_concepts = Counter(c for r in long_term for c in r.get("concepts", []))
    rc_concepts = Counter(c for r in recent_3  for c in r.get("concepts", []))

    lt_dom = lt_concepts.most_common(1)[0][0] if lt_concepts else None
    rc_dom = rc_concepts.most_common(1)[0][0] if rc_concepts else None

    return (lt_dom is not None and rc_dom is not None and lt_dom != rc_dom)


def _detect_returning_theme(recent: list, query_concepts: list) -> str:
    """
    Return a human-readable phrase if the user keeps returning to the same concept ground.
    Threshold: concept appears in 3+ of the last 8 interactions.
    """
    if len(recent) < 3:
        return ""
    concept_counts = Counter(c for r in recent for c in r.get("concepts", []))
    for concept, count in concept_counts.most_common():
        if count >= 3 and concept in _RETURNING_THEME_PHRASES:
            return _RETURNING_THEME_PHRASES[concept]
    return ""


def _build_concept_pairs(interactions: list) -> dict:
    """
    Find which concepts this specific user tends to think about together.
    Returns {concept: [co-occurring concept, ...]} for pairs that appear 2+ times.
    """
    pair_counts: Counter = Counter()
    for record in interactions:
        concepts = record.get("concepts", [])
        for i, c1 in enumerate(concepts):
            for c2 in concepts[i + 1:]:
                key = tuple(sorted([c1, c2]))
                pair_counts[key] += 1

    pairs: dict = {}
    for (c1, c2), count in pair_counts.items():
        if count >= 2:
            pairs.setdefault(c1, []).append(c2)
            pairs.setdefault(c2, []).append(c1)
    return pairs


def _detect_symbolic_echo(interactions: list) -> str:
    """
    Return an entity-specific echo phrase if a universe entity appears in 3+ of the
    last 10 interactions. The most frequent entity wins.
    """
    recent = interactions[-10:] if len(interactions) >= 10 else interactions
    entity_counts: Counter = Counter()
    for record in recent:
        combined = (record.get("user", "") + " " + record.get("response", "")).lower()
        for entity in _UNIVERSE_ENTITIES:
            if entity.lower() in combined:
                entity_counts[entity] += 1

    for entity, count in entity_counts.most_common():
        if count >= 3:
            return _ENTITY_ECHO_PHRASES.get(entity, "")
    return ""


def _detect_project_momentum(interactions: list) -> str:
    """Return the project tag most active in the last 10 interactions."""
    recent = interactions[-10:] if len(interactions) >= 10 else interactions
    if not recent:
        return "elo_core"
    counts = Counter(r.get("project_tag", "elo_core") for r in recent)
    return counts.most_common(1)[0][0]


# ── five memory category extractors ───────────────────────────────────────────
# Each returns a dict with: style_hint, reference, association.
# Empty strings mean "nothing strong enough to surface."

def _extract_identity_memory(interactions: list) -> dict:
    """
    Identity Memory — who the user says they are, their goals and direction.

    Shapes: response directness, how much eLo leads vs follows, vocabulary register.
    """
    records = [r for r in interactions if "identity" in r.get("memory_categories", [])]
    if not records:
        return {"style_hint": "", "reference": "", "association": ""}

    recent = records[-3:]
    # detect dominant self-description vocabulary
    all_text = " ".join(r.get("user", "") for r in recent).lower()

    style_hint  = ""
    reference   = ""
    association = ""

    if any(w in all_text for w in ["build", "create", "make", "ship"]):
        style_hint  = "User identifies as a maker/builder. Lead with concrete, not abstract."
        association = "building and making"
    elif any(w in all_text for w in ["explore", "discover", "understand", "learn"]):
        style_hint  = "User identifies as an explorer. Match the open-ended energy."
        association = "exploration and discovery"
    elif any(w in all_text for w in ["feel", "sense", "mean", "purpose"]):
        style_hint  = "User is in meaning-seeking mode. Don't rush to practical."
        association = "meaning and purpose"

    if recent:
        reference = recent[-1].get("user", "")[:80]

    return {"style_hint": style_hint, "reference": reference, "association": association}


def _extract_project_memory(interactions: list, project_hint: str) -> dict:
    """
    Project Memory — what's being built, project momentum, recent direction.

    Shapes: what eLo references, how it grounds abstract ideas in specific work.
    """
    records = [
        r for r in interactions
        if r.get("project_tag") == project_hint
        or "project" in r.get("memory_categories", [])
    ]
    if not records:
        return {"style_hint": "", "reference": "", "association": ""}

    recent = records[-5:]
    concepts = Counter(c for r in recent for c in r.get("concepts", []))
    dominant = concepts.most_common(1)[0][0] if concepts else ""

    style_hint  = f"Active project context: {project_hint}. Ground ideas here first." if recent else ""
    reference   = recent[-1].get("user", "")[:80] if recent else ""
    association = dominant if dominant else ""

    return {"style_hint": style_hint, "reference": reference, "association": association}


def _extract_creative_memory(interactions: list) -> dict:
    """
    Creative Memory — aesthetic preferences, imaginative patterns, stylistic tendencies.

    Shapes: metaphor choices, which creative frames eLo reaches for, vocabulary texture.
    """
    records = [r for r in interactions if "creative" in r.get("memory_categories", [])]
    if not records:
        return {"style_hint": "", "reference": "", "association": ""}

    recent = records[-5:]
    all_text = " ".join(r.get("user", "") for r in recent).lower()

    style_hint  = ""
    association = ""

    # detect creative orientation
    if any(w in all_text for w in ["world", "universe", "myth", "lore", "story"]):
        style_hint  = "User thinks in worlds and narratives. Expand symbolically."
        association = "world-building and narrative logic"
    elif any(w in all_text for w in ["visual", "design", "aesthetic", "colour", "look"]):
        style_hint  = "User has visual/aesthetic orientation. Use image-based language."
        association = "visual language and aesthetic coherence"
    elif any(w in all_text for w in ["system", "structure", "pattern", "logic"]):
        style_hint  = "User thinks in systems and patterns. Use structural metaphors."
        association = "systems and structural thinking"
    else:
        style_hint  = "User is in creative mode. Follow their lead before offering direction."

    reference = recent[-1].get("user", "")[:80] if recent else ""

    return {"style_hint": style_hint, "reference": reference, "association": association}


def _extract_world_memory(interactions: list) -> dict:
    """
    World Memory — eLo universe entity references, symbolic language patterns.

    Shapes: which entities to invoke, symbolic register, mythic/world-logic framing.
    """
    records = [r for r in interactions if "world" in r.get("memory_categories", [])]
    if not records:
        return {"style_hint": "", "reference": "", "association": ""}

    recent = records[-8:]
    entity_counts: Counter = Counter()
    for record in recent:
        combined = (record.get("user", "") + " " + record.get("response", "")).lower()
        for entity in _UNIVERSE_ENTITIES:
            if entity.lower() in combined:
                entity_counts[entity] += 1

    dominant_entity = entity_counts.most_common(1)[0][0] if entity_counts else ""

    _ENTITY_FRAMES = {
        "eLo":       "Explorer lens active. Move through unknowns with curiosity, not certainty.",
        "Chunk":     "Reconstruction lens active. Think in fragments becoming new shapes.",
        "K-7":       "Emotional signal lens active. Respond to what behaviour reveals, not words.",
        "Core":      "Navigation lens active. Help find the thread that orients everything.",
        "Sugarcore": "Distortion lens active. Name the overload state before offering movement.",
    }

    style_hint  = _ENTITY_FRAMES.get(dominant_entity, "Universe symbolic vocabulary is in use.")
    reference   = dominant_entity
    association = f"{dominant_entity} logic" if dominant_entity else "eLo universe symbolic frame"

    return {"style_hint": style_hint, "reference": reference, "association": association}


def _extract_user_memory(interactions: list) -> dict:
    """
    User Memory — behavioral patterns, emotional arc, recurring states and contradictions.

    Shapes: emotional calibration, contradiction tolerance, how much to slow down or push.
    """
    records = [r for r in interactions if "user" in r.get("memory_categories", [])]
    if not records:
        return {"style_hint": "", "reference": "", "association": ""}

    recent = records[-5:]
    all_text = " ".join(r.get("user", "") for r in recent).lower()

    style_hint  = ""
    association = ""

    # detect recurring behavioral pattern
    if any(w in all_text for w in ["stuck", "overwhelm", "chaos", "scattered"]):
        style_hint  = "User has been in overload/Sugarcore territory. Name state, go slow."
        association = "naming the state before moving"
    elif any(re.search(p, all_text) for p in [r"\bbut\b.*\bnot\b", r"\bwant\b.*\bbut\b"]):
        style_hint  = "User holds contradictions. Don't resolve — stay in tension."
        association = "holding contradictions as information"
    elif any(w in all_text for w in ["don't know", "not sure", "confused"]):
        style_hint  = "User is in uncertain territory. Reflect before redirecting."
        association = "navigating uncertainty"
    elif any(w in all_text for w in ["excited", "amazing", "finally", "yes"]):
        style_hint  = "User has momentum. Match the energy, then give it shape."
        association = "channeling momentum into structure"

    reference = recent[-1].get("user", "")[:60] if recent else ""

    return {"style_hint": style_hint, "reference": reference, "association": association}


def _synthesize_behavioral_guidance(
    identity: dict,
    project: dict,
    creative: dict,
    world: dict,
    user: dict,
    query: str,
) -> dict:
    """
    Collapse five memory categories into four response-ready behavioral directives.

    Priority:
        1. User memory (emotional/behavioral state) — most immediate
        2. World memory (symbolic frame) — if entities are in play
        3. Identity memory (who they are) — shapes register
        4. Creative memory (aesthetic) — shapes vocabulary
        5. Project memory (grounding) — shapes references
    """
    # response_style: the highest-priority style hint
    style = (
        user.get("style_hint")
        or world.get("style_hint")
        or identity.get("style_hint")
        or creative.get("style_hint")
        or project.get("style_hint")
        or ""
    )

    # key_reference: the most specific thing to echo back
    reference = (
        world.get("reference")
        or identity.get("reference")
        or project.get("reference")
        or creative.get("reference")
        or user.get("reference")
        or ""
    )

    # key_association: the most useful conceptual bridge
    association = (
        world.get("association")
        or creative.get("association")
        or identity.get("association")
        or user.get("association")
        or project.get("association")
        or ""
    )

    # future_idea: what direction this memory suggests the work is heading
    future_idea = ""
    if project.get("association") and creative.get("association"):
        future_idea = f"{project['association']} expressed through {creative['association']}"
    elif world.get("association") and identity.get("association"):
        future_idea = f"{world['association']} applied to {identity['association']}"
    elif creative.get("association"):
        future_idea = creative["association"]

    return {
        "response_style":  style,
        "key_reference":   reference,
        "key_association": association,
        "future_idea":     future_idea,
    }


def build_memory_influence(query: str, project_hint: str = "elo_core") -> dict:
    """
    Build actionable memory signals that directly shape response tone,
    associations, and symbolic framing.

    The offline engine consumes this dict in Phase 2 — memory becomes
    part of reasoning, not just logged context.

    Returns:
        tone_signal        — dominant emotional pattern in recent turns
        dominant_mode      — most frequent mode in recent turns
        recurring_concepts — concepts appearing 2+ times in last 8 interactions
        entity_frequency   — universe entity counts across full history
        concept_pairs      — user-specific concept co-occurrence map
        returning_theme    — human-readable string when user revisits same ground
        project_momentum   — most active project in recent turns
        symbolic_echo      — entity echo phrase when pattern detected
        raw_blocks         — four typed blocks from retrieve_structured()
    """
    interactions = _load_store()
    recent8      = interactions[-8:]  if len(interactions) >= 8  else interactions
    recent10     = interactions[-10:] if len(interactions) >= 10 else interactions

    q_concepts = _detect_concepts(query)

    # tone — use stability-weighted version so long-term patterns resist short-term spikes
    # _detect_tone_signal (raw recent) kept for comparison; stable version is authoritative
    tone_signal     = _detect_tone_stable(interactions)
    tone_confidence = _compute_pattern_confidence(interactions)
    tone_drift      = _detect_tone_drift(interactions)

    # dominant mode
    mode_counts  = Counter(r.get("mode", "companion") for r in recent10)
    dominant_mode = mode_counts.most_common(1)[0][0] if mode_counts else "companion"

    # recurring concepts
    concept_counts = Counter(c for r in recent8 for c in r.get("concepts", []))
    recurring_concepts = [c for c, n in concept_counts.items() if n >= 2]

    # entity frequency across full history
    entity_frequency: dict = {e: 0 for e in _UNIVERSE_ENTITIES}
    for record in interactions:
        combined = (record.get("user", "") + " " + record.get("response", "")).lower()
        for entity in _UNIVERSE_ENTITIES:
            if entity.lower() in combined:
                entity_frequency[entity] += 1

    # concept co-occurrence pairs (user-specific)
    concept_pairs = _build_concept_pairs(interactions)

    # returning theme
    returning_theme = _detect_returning_theme(recent8, q_concepts)

    # project momentum
    project_momentum = _detect_project_momentum(interactions)

    # symbolic echo
    symbolic_echo = _detect_symbolic_echo(interactions)

    # ── five memory categories ──
    identity_mem = _extract_identity_memory(interactions)
    project_mem  = _extract_project_memory(interactions, project_hint)
    creative_mem = _extract_creative_memory(interactions)
    world_mem    = _extract_world_memory(interactions)
    user_mem     = _extract_user_memory(interactions)

    # ── behavioral synthesis ──
    guidance = _synthesize_behavioral_guidance(
        identity_mem, project_mem, creative_mem, world_mem, user_mem, query
    )

    # raw blocks (backward compat)
    raw_blocks = retrieve_structured(query, project_hint)

    return {
        # existing signals (backward compat — behavior_engine / kernel reads these)
        # tone_signal is now stability-weighted: long-term patterns resist short-term spikes
        "tone_signal":        tone_signal,
        "dominant_mode":      dominant_mode,
        "recurring_concepts": recurring_concepts,
        "entity_frequency":   entity_frequency,
        "concept_pairs":      concept_pairs,
        "returning_theme":    returning_theme,
        "project_momentum":   project_momentum,
        "symbolic_echo":      symbolic_echo,
        "raw_blocks":         raw_blocks,

        # memory drift control signals (informational — do NOT affect routing/mode)
        # these may influence: tone, familiarity, contextual relevance ONLY
        "tone_confidence":    tone_confidence,  # 0.0-1.0: how stable the tone pattern is
        "tone_drift":         tone_drift,       # True if recent tone diverges from long-term baseline

        # five typed memory categories
        "memory_categories": {
            "identity": identity_mem,
            "project":  project_mem,
            "creative": creative_mem,
            "world":    world_mem,
            "user":     user_mem,
        },

        # behavioral synthesis — ready to use directly in response generation
        "response_style":  guidance["response_style"],
        "key_reference":   guidance["key_reference"],
        "key_association": guidance["key_association"],
        "future_idea":     guidance["future_idea"],
    }


# ── long-term memory loader ────────────────────────────────────────────────────

def load_long_term_memory() -> str:
    """Read export_memory.md for injection into system prompt. Returns empty string if absent."""
    if os.path.exists(_EXPORT_PATH):
        with open(_EXPORT_PATH) as f:
            return f.read().strip()
    return ""
