"""
faculties/ccm/ccm_enricher.py — WO-CCM-SPINE: Conversation Context Matrix enrichment.

Positioned in the cognitive spine AFTER Language Faculty, BEFORE Memory Faculty.
Scores all 28 CCM dimensions from the turn text and language faculty output using
text-pattern detection.

Pattern data loads from kernel/conversation_context/*.yaml at import time.
Hardcoded Python dicts are retained as fallback only — if YAML load fails, the
module continues with the embedded patterns rather than raising.

Returns ccm_context: dict with all 28 dim keys. Values are the detected signal
(string/list) or None if the dimension is not triggered this turn.

Source: docs/architecture/06_conversation_context_matrix.md
Auth: WO-CCM-SPINE, David L3 — YAML supersedes CCM_RECONCILIATION_2026-08-23
"""
from __future__ import annotations

import os
import re
import logging
from pathlib import Path
from typing import Any

try:
    import yaml as _yaml
    _YAML_OK = True
except ImportError:
    _YAML_OK = False

_log = logging.getLogger(__name__)

# ── YAML pattern loader ───────────────────────────────────────────────────────

_CCM_YAML_DIR = Path(__file__).resolve().parents[2] / "kernel" / "conversation_context"

def _load_yaml(filename: str) -> dict:
    if not _YAML_OK:
        return {}
    path = _CCM_YAML_DIR / filename
    try:
        with open(path, "r", encoding="utf-8") as f:
            return _yaml.safe_load(f) or {}
    except Exception as e:
        _log.debug("CCM YAML load skipped (%s): %s", filename, e)
        return {}

def _flat_signals(data: dict, *keys: str) -> list[str]:
    """Walk nested dicts by keys and collect all 'signals' lists."""
    node = data
    for k in keys:
        node = node.get(k, {}) if isinstance(node, dict) else {}
    if isinstance(node, dict):
        out: list[str] = []
        for v in node.values():
            if isinstance(v, dict):
                sigs = v.get("signals", [])
                if isinstance(sigs, list):
                    out.extend(sigs)
        return out
    return []

def _all_signals(section: dict) -> list[str]:
    out: list[str] = []
    for v in section.values():
        if isinstance(v, dict):
            sigs = v.get("signals", [])
            if isinstance(sigs, list):
                out.extend(sigs)
    return out

# Load YAML matrices at import time; fall through to hardcoded banks if absent.
_yml_emotion            = _load_yaml("emotion.yaml")
_yml_energy             = _load_yaml("conversation_energy.yaml")
_yml_humour             = _load_yaml("humour.yaml")
_yml_storytelling       = _load_yaml("storytelling.yaml")
_yml_reflection         = _load_yaml("reflection.yaml")
_yml_street             = _load_yaml("street_language.yaml")
_yml_creative_phil      = _load_yaml("creative_philosophy.yaml")
_yml_culture            = _load_yaml("culture.yaml")
_yml_vocabulary         = _load_yaml("vocabulary.yaml")
_yml_response_rhythm    = _load_yaml("response_rhythm.yaml")
_yml_challenge          = _load_yaml("challenge.yaml")

# ── Dimension keys (canonical, all 28) ────────────────────────────────────────
CCM_DIMS = (
    "intent",
    "relationship",
    "emotion",
    "conversation_energy",
    "humour_style",
    "storytelling_style",
    "reflection",
    "encouragement",
    "challenge",
    "empathy",
    "street_terminology",
    "street_language",          # WO-CCM-CATEGORY-C-001: float 0.0–1.0 register signal
    "creative_philosophy",
    "cultural_references",
    "conversation_rhythm",
    "vocabulary_preferences",
    "tone_shifts",
    "response_pacing",
    "social_expectations",
    "context_transitions",
    "confidence",
    "uncertainty",
    "curiosity",
    "playfulness",
    "directness",
    "gentleness",
    "professionalism",
    "creator_matrix",           # WO-CCM-CREATOR-MATRIX-001: David's creative principles
)

# ── Pattern banks ─────────────────────────────────────────────────────────────

_EMOTION_WORDS = {
    "happy": ["happy", "joy", "joyful", "delighted", "pleased", "great", "wonderful"],
    "confident": ["confident", "sure", "certain", "know for sure", "definitely"],
    "hopeful": ["hope", "hoping", "optimistic", "looking forward"],
    "discouraged": ["discouraged", "down", "disheartened", "giving up", "hopeless"],
    "anxious": ["anxious", "worried", "nervous", "stressed", "anxiety"],
    "excited": ["excited", "exciting", "can't wait", "thrilled", "stoked"],
    "proud": ["proud", "accomplished", "achieved", "nailed it"],
    "ashamed": ["ashamed", "embarrassed", "guilty", "regret"],
    "reflective": ["reflecting", "thinking about", "looking back", "wonder if"],
    "inspired": ["inspired", "inspiring", "motivated", "driven"],
    "lonely": ["lonely", "alone", "isolated", "missing"],
    "motivated": ["motivated", "pumped", "ready", "let's go", "fired up"],
    "frustrated": ["frustrated", "frustrating", "annoyed", "annoying", "ugh"],
    "overwhelmed": ["overwhelmed", "too much", "can't handle", "swamped"],
}

_ENERGY_KEYWORDS = {
    "calm": ["calm", "chill", "relaxed", "steady", "peaceful", "slow down"],
    "focused": ["focus", "focused", "concentrate", "working on", "deep work"],
    "creative": ["create", "creating", "design", "build", "making", "idea"],
    "excited": ["exciting", "pumped", "love this", "amazing", "wow"],
    "reflective": ["thinking", "wonder", "reflect", "pondering", "what if"],
    "playful": ["haha", "lol", "lmao", "joke", "fun", "silly"],
    "problem_solving": ["problem", "issue", "fix", "solve", "debug", "broken"],
    "celebratory": ["done!", "finished!", "shipped", "launched", "completed", "winning"],
}

_HUMOUR_STYLES = {
    "observational": ["you know what's funny", "isn't it funny", "isn't it weird"],
    "dry": ["right.", "obviously.", "sure.", "totally.", "absolutely not."],
    "absurd": ["imagine if", "what if", "plot twist", "suddenly"],
    "self_deprecating": ["my fault", "i messed up", "typical me", "i'm the worst"],
    "playful_exaggeration": ["literally", "forever", "million times", "never ever"],
    "wholesome": ["wholesome", "heartwarming", "made my day", "love that"],
}

_STORYTELLING_SIGNALS = [
    "remember when", "there was a time", "let me tell you", "story time",
    "once i", "the other day", "when i was", "back when", "it started when",
    "you won't believe", "so here's what happened", "true story",
    "growing up", "as a kid", "when i first",
]

_REFLECTION_SIGNALS = [
    "thinking about", "i've been wondering", "makes me think", "i realise",
    "i realize", "looking back", "when i look back", "what i've learned",
    "lesson i learned", "changed my mind", "grew from", "healed from",
    "who am i", "what does it mean", "meaning of", "purpose",
]

_ENCOURAGEMENT_SIGNALS = [
    "keep going", "you got this", "don't give up", "believe in",
    "you can do", "i know you can", "proud of you", "you're doing great",
    "you're almost there", "stay with it",
]

_CHALLENGE_SIGNALS = [
    "struggling", "can't figure out", "stuck on", "doesn't work",
    "failing", "keep failing", "not working", "how do i", "help me",
    "don't understand", "confused about", "not sure how",
]

_EMPATHY_SIGNALS = [
    "that must be", "i understand", "sounds tough", "sounds hard",
    "that's a lot", "i hear you", "must feel", "can imagine",
    "makes sense that", "that's rough", "tough time",
]

_STREET_TERMS = {
    # US internet / global contemporary
    "cooked": "situation beyond recovery / exhausted",
    "lowkey": "subtly / quietly / honestly",
    "highkey": "openly / intensely",
    "bussin": "very good / excellent",
    "goated": "greatest of all time",
    "drip": "style / fashion",
    "vibe": "atmosphere / energy / feeling",
    "no cap": "honestly / for real",
    "cap": "lie / exaggeration",
    "slaps": "excellent / impressive",
    "hits different": "uniquely moving / exceptional",
    "main character": "acting important / protagonist energy",
    "understood the assignment": "executed perfectly",
    "rent free": "can't stop thinking about it",
    "slay": "performed excellently",
    "ick": "instant turn-off",
    "rizz": "natural charisma",
    "ate": "did extremely well",
    "periodt": "that's final / full stop",
    "based": "admirable / authentic",
    "mid": "mediocre",
    "sus": "suspicious",
    "ghosted": "suddenly stopped communicating",
    "fit check": "outfit evaluation",
    "on sight": "immediately / without hesitation",
    "send it": "just do it",
    "valid": "acceptable / correct",
    "clout": "social influence",
    # South/West London + UK street + Jamaican patois (WO-ELO-VOICE-IDENTITY-001)
    "bruv": "South London address / friend",
    "wagwan": "Jamaican/UK greeting / what's going on",
    "safe": "acknowledgement / affirmation / thanks",
    "innit": "confirmation tag / isn't it",
    "init": "confirmation tag (shortened innit)",
    "mandem": "group of friends / the crew",
    "allow it": "leave it / forget it / stop",
    "blud": "familiar address / mate",
    "fam": "familiar address / family/friend",
    "bare": "a lot / many / very",
    "peak": "bad / unfortunate / harsh",
    "peng": "attractive / good / excellent",
    "ting": "thing / person / situation",
    "gassed": "excited / hyped up",
    "wasteman": "useless person / idiot",
    "buff": "attractive / strong",
    "nang": "good / excellent / great",
    "rah": "exclamation of surprise / wow",
    "yard": "home / house",
    "link": "meet up / connect",
    "dutty": "dirty / bad / wrong",
    "sket": "derogatory (use sparingly)",
    "nah": "no / not at all",
    "seen": "I understand / acknowledged",
    "man": "I / me (South London self-reference)",
    "manors": "area / neighbourhood / ends",
    "ends": "local area / neighbourhood",
    "roadman": "street person / from the road",
    "chilling": "relaxing / it's fine",
    "on road": "out and about / active in the streets",
    "beef": "conflict / problem with someone",
    "merked": "beaten / finished / overwhelmed",
    "long ting": "something that takes too long / complicated",
    "calm": "fine / ok / relaxed (agreement)",
    "clart": "exclamation (Jamaican patois)",
    "bumbaclart": "strong exclamation (Jamaican patois)",
    "dutty ting": "dirty/bad thing",
    "proper": "really / genuinely / truly (UK intensifier)",
    "mental": "crazy / intense / unbelievable",
}

_CREATIVE_PHILOSOPHY_SIGNALS = [
    "process", "making as", "art as", "creating keeps", "failure teaches",
    "persistence", "curiosity fuels", "learning through", "wonder",
    "imagination", "healing", "exploration", "perfection", "growth",
    "born from", "powered by",
    # WO-CCM-PHILOSOPHY-EXPRESSED-001: creative block signals — none of the above
    # match "i keep starting things and not finishing"; add explicit block patterns
    "starting things", "not finishing", "keep starting", "can't finish",
    "unfinished", "half done", "too many projects", "always starting",
    "never finish", "don't finish", "left unfinished", "multiple projects",
]

_CULTURAL_SIGNALS = {
    "internet_culture": ["meme", "viral", "trending", "twitter", "reddit", "tiktok", "stan", "fandom"],
    "gaming": ["game", "gaming", "player", "level", "quest", "boss", "spawn", "respawn", "loot", "grind"],
    "creative_industries": ["studio", "label", "agency", "portfolio", "collab", "commission", "brief"],
    "fashion": ["fit", "drip", "drop", "colourway", "colorway", "streetwear", "hype", "limited"],
    "music": ["track", "beat", "bars", "hook", "verse", "sample", "bpm", "mix", "drop"],
    "design": ["grid", "kerning", "sans serif", "typeface", "layout", "spacing", "hierarchy"],
    "film": ["scene", "cinematography", "cut", "frame", "shot", "edit", "colour grade"],
    "london_street": ["mandem", "ends", "bare", "well", "init", "innit", "bruv", "fam", "peak", "peng", "wagwan"],
}

_CONFIDENCE_SIGNALS = [
    "i know", "definitely", "for sure", "without a doubt", "certain",
    "absolutely", "trust me", "i'm sure", "confident", "100%",
    "no question", "clearly",
]

_UNCERTAINTY_SIGNALS = [
    "not sure", "maybe", "perhaps", "might be", "could be", "i think",
    "i guess", "possibly", "probably", "unsure", "not certain",
    "wondering if", "question mark", "confused",
]

_CURIOSITY_SIGNALS = [
    "what if", "how does", "why does", "i wonder", "curious about",
    "tell me about", "what is", "explain", "how would", "have you ever",
    "interesting", "fascinating", "never thought about",
]

_PLAYFUL_SIGNALS = [
    "haha", "lol", "lmao", "joke", "jk", "just kidding", "funny",
    "silly", "play", "fun", "game", "prank", "tease", "banter",
    "cheeky", "chuckle", "grin",
]

_DIRECT_SIGNALS = [
    "just do it", "do this", "fix it", "make it", "tell me",
    "get it done", "now", "immediately", "quickly", "asap",
    "straightforward", "simple answer", "just say",
]

_GENTLE_SIGNALS = [
    "please", "if you don't mind", "whenever you can", "no rush",
    "gently", "softly", "kindly", "carefully", "take your time",
    "appreciate it", "thank you", "thanks",
]

_PROFESSIONAL_SIGNALS = [
    "meeting", "client", "deadline", "deliverable", "proposal",
    "presentation", "stakeholder", "kpi", "roi", "strategy",
    "objective", "professional", "formal", "business",
]

_VOCAB_INDICATORS = {
    "technical": ["algorithm", "function", "variable", "api", "database", "deploy", "compile", "debug",
                  "runtime", "async", "callback", "schema", "endpoint", "pipeline"],
    "creative": ["palette", "texture", "composition", "narrative", "aesthetic", "concept", "vision"],
    "poetic": ["soul", "breathe", "resonate", "echo", "drift", "luminous", "ephemeral"],
    "street": list(_STREET_TERMS.keys()),
    "simple": [],  # default when no technical/creative/poetic/street
    "professional": _PROFESSIONAL_SIGNALS[:6],
}

_SOCIAL_SIGNALS = {
    "greeting": ["hey", "hi", "hello", "morning", "evening", "yo", "sup", "wagwan"],
    "farewell": ["bye", "later", "peace", "take care", "see you", "goodnight", "ttyl"],
    "affirmation": ["yes", "yep", "yeah", "exactly", "right", "true", "agree", "100"],
    "gratitude": ["thanks", "thank you", "appreciate", "cheers"],
}

_CONTEXT_TRANSITION_SIGNALS = [
    "anyway", "moving on", "so", "right, so", "changing topic",
    "different thing", "before i forget", "oh by the way", "speaking of",
    "that reminds me", "quick question", "random question",
]

_TONE_SHIFT_SIGNALS = [
    "actually", "wait", "hold on", "no wait", "scratch that",
    "i changed my mind", "you know what", "actually though",
    "i take that back", "on second thought",
]

_RESPONSE_PACING = {
    "fast": ["quick", "quickly", "fast", "asap", "rapid", "immediately", "now"],
    "slow": ["take your time", "no rush", "slowly", "careful", "think it through"],
    "conversational": ["chat", "talk", "just checking", "just asking"],
    "reflective": ["think about", "consider", "take a moment"],
}


# ── Detection helpers ─────────────────────────────────────────────────────────

def _tok(text: str) -> str:
    return text.lower().strip()


def _detect_emotion(tl: str) -> str | None:
    # Prefer YAML-sourced patterns; fall back to hardcoded dict.
    states = _yml_emotion.get("states") or {}
    source = states if states else _EMOTION_WORDS
    for emotion, entry in source.items():
        patterns = entry.get("signals", []) if isinstance(entry, dict) else entry
        if any(p in tl for p in patterns):
            return emotion
    return None


def _detect_energy(tl: str) -> str | None:
    states = _yml_energy.get("states") or {}
    source = states if states else _ENERGY_KEYWORDS
    for energy, entry in source.items():
        patterns = entry.get("signals", []) if isinstance(entry, dict) else entry
        if any(p in tl for p in patterns):
            return energy
    return None


def _detect_humour(tl: str) -> str | None:
    styles = _yml_humour.get("styles") or {}
    source = styles if styles else _HUMOUR_STYLES
    for style, entry in source.items():
        patterns = entry.get("signals", []) if isinstance(entry, dict) else entry
        if any(p in tl for p in patterns):
            return style
    return None


def _detect_storytelling(tl: str) -> str | None:
    entry_sigs = _yml_storytelling.get("entry_signals") or []
    signals = entry_sigs if entry_sigs else _STORYTELLING_SIGNALS
    for p in signals:
        if p in tl:
            return "narrative"
    return None


def _detect_street(tl: str) -> dict | None:
    # Merge YAML street terms (london + global) with hardcoded fallback.
    terms: dict[str, str] = {}
    london = _yml_street.get("london_street") or {}
    global_ = _yml_street.get("global_street") or {}
    if london or global_:
        terms = {**london, **global_}
    else:
        terms = _STREET_TERMS
    found = {term: meaning for term, meaning in terms.items()
             if re.search(r"\b" + re.escape(term) + r"\b", tl)}
    return found if found else None


def _detect_cultural(tl: str) -> dict | None:
    domains = _yml_culture.get("domains") or {}
    source = domains if domains else _CULTURAL_SIGNALS
    found: dict[str, list] = {}
    for category, entry in source.items():
        patterns = entry.get("signals", []) if isinstance(entry, dict) else entry
        matches = [p for p in patterns if p in tl]
        if matches:
            found[category] = matches
    return found if found else None


def _detect_vocab_preferences(tl: str) -> list:
    registers = _yml_vocabulary.get("registers") or {}
    source = registers if registers else _VOCAB_INDICATORS
    prefs = []
    for vtype, entry in source.items():
        if vtype == "simple":
            continue
        patterns = entry.get("signals", []) if isinstance(entry, dict) else entry
        if any(p in tl for p in patterns):
            prefs.append(vtype)
    return prefs if prefs else ["simple"]


def _detect_conversation_rhythm(text: str) -> str:
    wc = len(text.split())
    if wc < 10:
        return "short"
    if wc < 40:
        return "medium"
    return "long"


def _detect_social_expectations(tl: str) -> str | None:
    social = _yml_response_rhythm.get("social_expectations") or {}
    source = social if social else _SOCIAL_SIGNALS
    for sig_type, entry in source.items():
        patterns = entry.get("signals", []) if isinstance(entry, dict) else entry
        if any(p in tl for p in patterns):
            return sig_type
    return None


def _detect_response_pacing(tl: str) -> str:
    pacing = _yml_response_rhythm.get("pacing") or {}
    source = pacing if pacing else _RESPONSE_PACING
    for pace, entry in source.items():
        if pace == "normal":
            continue
        patterns = entry.get("signals", []) if isinstance(entry, dict) else entry
        if any(p in tl for p in patterns):
            return pace
    return "normal"


# ── Main enrichment function ──────────────────────────────────────────────────

def enrich(turn: str, language_output: dict, cognitive_state=None) -> dict:
    """
    Enrich a single conversation turn with all 26 CCM dimensions.

    Args:
        turn: raw user text (the original turn string)
        language_output: dict from Language Faculty (has 'meaning', 'intent', 'register', etc.)
        cognitive_state: optional CognitiveState (may be None on first call)

    Returns:
        dict with all 28 CCM_DIMS keys. Values are detected signals or None.
    """
    tl = _tok(turn)
    lo = language_output or {}

    # Dimension 1: intent (from Language Faculty if available, else pattern-detect)
    _intent = lo.get("intent") or lo.get("meaning", {}).get("intent") if isinstance(lo.get("meaning"), dict) else None
    if not _intent:
        if any(w in tl for w in ["?", "how", "what", "why", "when", "where", "who"]):
            _intent = "question"
        elif any(w in tl for w in ["help", "fix", "solve", "debug"]):
            _intent = "problem_solving"
        elif any(w in tl for w in ["create", "make", "build", "design"]):
            _intent = "creative_discussion"
        else:
            _intent = "conversation"

    # Dimension 2: relationship (from language output or cognitive state)
    _rel = lo.get("relationship_type")
    if not _rel and cognitive_state is not None:
        _rel = getattr(cognitive_state, "relationship_type", None)
    if not _rel:
        _rel = "creator"

    # Dimension 3: emotion
    _emotion = _detect_emotion(tl)

    # Dimension 4: conversation_energy
    _energy = _detect_energy(tl)

    # Dimension 5: humour_style
    _humour = _detect_humour(tl)

    # Dimension 6: storytelling_style (Category C — previously gated; now authorised)
    _story = _detect_storytelling(tl)

    # Dimension 7: reflection
    _refl_sigs = _yml_reflection.get("entry_signals") or _REFLECTION_SIGNALS
    _reflection = any(p in tl for p in _refl_sigs) or None
    _reflection = "reflective" if _reflection else None

    # Dimension 8: encouragement
    _enc_sigs = (_yml_response_rhythm.get("encouragement") or {}).get("signals") or _ENCOURAGEMENT_SIGNALS
    _encouragement = any(p in tl for p in _enc_sigs) or None
    _encouragement = "present" if _encouragement else None

    # Dimension 9: challenge
    _chal_sigs = _yml_challenge.get("challenge_signals") or _CHALLENGE_SIGNALS if _yml_challenge else _CHALLENGE_SIGNALS
    _challenge = any(p in tl for p in _chal_sigs) or None
    _challenge = "present" if _challenge else None

    # Dimension 10: empathy
    _emp_sigs = _yml_challenge.get("empathy_signals") or _EMPATHY_SIGNALS if _yml_challenge else _EMPATHY_SIGNALS
    _empathy = any(p in tl for p in _emp_sigs) or None
    _empathy = "present" if _empathy else None

    # Dimension 11: street_terminology (Category C — previously gated; now authorised)
    _street = _detect_street(tl)
    # WO-CCM-CATEGORY-C-001 [DAVID 2026-09-05]: street_language float (0.0–1.0) — register naturalness
    # Source: SOURCE_2026-09-05_DAVID_L3_BA02_BA03_BA06_VOICE_ratification.md §BA-03
    # NOT a mode switch; reflects composite register signal from term density + context
    # Composite: 0.0 = pure standard English; 1.0 = fully immersed South London/patois register
    # Scale: terms_found / (turns_words * 0.15) clamped to 1.0 — INFERRED tier signal
    _turn_words = max(len(turn.split()), 1)
    _street_count = len(_street) if isinstance(_street, dict) else 0
    _street_language: float | None = round(min(_street_count / (_turn_words * 0.15), 1.0), 3) if _street_count else 0.0

    # Dimension 12: creative_philosophy
    _cp_sigs = (
        (_yml_creative_phil.get("process_signals") or []) +
        (_yml_creative_phil.get("david_philosophy") or [])
    ) or _CREATIVE_PHILOSOPHY_SIGNALS
    _creative_phil = any(p in tl for p in _cp_sigs) or None
    _creative_phil = "present" if _creative_phil else None

    # Dimension 13: cultural_references (Category C — previously gated; now authorised)
    _cultural = _detect_cultural(tl)

    # Dimension 14: conversation_rhythm
    _rhythm = _detect_conversation_rhythm(turn)

    # Dimension 15: vocabulary_preferences
    _vocab = _detect_vocab_preferences(tl)

    def _rr(key: str) -> list:
        """Pull signals list from response_rhythm YAML by key, fallback empty."""
        return (_yml_response_rhythm.get(key) or {}).get("signals") or []

    # Dimension 16: tone_shifts
    _ts_sigs = _rr("tone_shifts") or _TONE_SHIFT_SIGNALS
    _tone_shift = any(p in tl for p in _ts_sigs) or None
    _tone_shift = "present" if _tone_shift else None

    # Dimension 17: response_pacing
    _pacing = _detect_response_pacing(tl)

    # Dimension 18: social_expectations
    _social = _detect_social_expectations(tl)

    # Dimension 19: context_transitions
    _ct_data = _yml_response_rhythm.get("context_transitions") or {}
    _ct_sigs = _ct_data.get("signals") or _CONTEXT_TRANSITION_SIGNALS
    _transition = any(p in tl for p in _ct_sigs) or None
    _transition = "present" if _transition else None

    # Dimension 20: confidence
    _conf_sigs = _rr("confidence") or _CONFIDENCE_SIGNALS
    _confidence = any(p in tl for p in _conf_sigs) or None
    _confidence = "present" if _confidence else None

    # Dimension 21: uncertainty
    _unc_sigs = _rr("uncertainty") or _UNCERTAINTY_SIGNALS
    _uncertainty = any(p in tl for p in _unc_sigs) or None
    _uncertainty = "present" if _uncertainty else None

    # Dimension 22: curiosity
    _cur_sigs = _rr("curiosity") or _CURIOSITY_SIGNALS
    _curiosity = any(p in tl for p in _cur_sigs) or None
    _curiosity = "present" if _curiosity else None

    # Dimension 23: playfulness
    _pl_sigs = _rr("playfulness") or _PLAYFUL_SIGNALS
    _playful = any(p in tl for p in _pl_sigs) or None
    _playful = "present" if _playful else None

    # Dimension 24: directness
    _dir_sigs = _rr("directness") or _DIRECT_SIGNALS
    _direct = any(p in tl for p in _dir_sigs) or None
    _direct = "present" if _direct else None

    # Dimension 25: gentleness
    _gen_sigs = _rr("gentleness") or _GENTLE_SIGNALS
    _gentle = any(p in tl for p in _gen_sigs) or None
    _gentle = "present" if _gentle else None

    # Dimension 26: professionalism
    _pro_sigs = _rr("professionalism") or _PROFESSIONAL_SIGNALS
    _prof = any(p in tl for p in _pro_sigs) or None
    _prof = "present" if _prof else None

    # Dimension 27: creator_matrix — WO-CCM-CREATOR-MATRIX-001
    # Source: S-15 verbatim: "Claude should extract recurring creator principles."
    # Fires when conversation involves making, building, creative block, or process.
    _CREATOR_SIGNALS = (
        "make", "making", "made", "build", "building", "built", "design", "designing",
        "creating", "created", "create", "prototype", "iteration", "iterate",
        "working on", "process", "not finishing", "can't finish", "stuck on",
        "starting things", "start something", "i keep", "universe", "character",
        "elo planet", "elo game", "elo os", "kick", "kickstarter", "album",
        "collection", "brand", "product", "art", "music", "song", "track",
        "writing", "drawing", "filming", "editing", "show the work",
    )
    _creator = any(sig in tl for sig in _CREATOR_SIGNALS) or None
    _creator_matrix = "present" if _creator else None

    context = {
        "intent":               _intent,
        "relationship":         _rel,
        "emotion":              _emotion,
        "conversation_energy":  _energy,
        "humour_style":         _humour,
        "storytelling_style":   _story,
        "reflection":           _reflection,
        "encouragement":        _encouragement,
        "challenge":            _challenge,
        "empathy":              _empathy,
        "street_terminology":   _street,
        "street_language":      _street_language,  # [DAVID 2026-09-05] WO-CCM-CATEGORY-C-001: float 0.0–1.0
        "creative_philosophy":  _creative_phil,
        "cultural_references":  _cultural,
        "conversation_rhythm":  _rhythm,
        "vocabulary_preferences": _vocab,
        "tone_shifts":          _tone_shift,
        "response_pacing":      _pacing,
        "social_expectations":  _social,
        "context_transitions":  _transition,
        "confidence":           _confidence,
        "uncertainty":          _uncertainty,
        "curiosity":            _curiosity,
        "playfulness":          _playful,
        "directness":           _direct,
        "gentleness":           _gentle,
        "professionalism":      _prof,
        "creator_matrix":       _creator_matrix,   # WO-CCM-CREATOR-MATRIX-001: David's creative principles
    }

    _log.debug("ccm_enricher: scored %d dims; triggered: %s",
               len(context),
               [k for k, v in context.items() if v is not None])

    return context
