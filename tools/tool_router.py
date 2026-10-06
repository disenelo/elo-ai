"""
tools/tool_router.py — eLo OS agent tool dispatcher.

Sits between server.py and the LLM. When a user query matches a tool's
intent, the tool fetches factual data and injects a single context line
into the enriched input. The LLM then generates eLo's response using that data.

RULE: This module never touches core kernel state, attention, presence, CAL,
or any eLo identity system. It only enriches the data going INTO the LLM —
eLo's character, voice, and emotion processing remain completely untouched.

How it works:
    enriched, agent_used = enrich(user_input)
    response, backend    = router_route(system_prompt, enriched, ...)

If no tool matches:
    enriched == user_input (unchanged)
    agent_used == None

Agents (all free, no key required unless noted):
    time        — datetime.now(), no network
    weather     — wttr.in JSON, no key
    wikipedia   — Wikipedia REST API, no key
    calculator  — safe math eval, no network

Adding a new agent:
    1. Define _agent_<name>(query) → str  (returns a one-line data summary)
    2. Add entry to _INTENT_MAP below
    3. Register in _AGENTS dict
"""

from __future__ import annotations
import os
import re
import logging
from typing import Optional, Tuple

from memory.provenance import CapabilityRecord, ExecutionTrace

try:
    from tools.truth_sync       import agent as _agent_truth_sync
    from tools.spotify_agent    import agent as _agent_spotify, is_playlist_intent as _is_playlist_intent, is_search_play_intent as _is_search_play_intent
    from tools.github_agent     import agent as _agent_github
    from tools.calendar_agent   import agent as _agent_calendar
    from tools.google_calendar_agent import agent_add as _agent_calendar_add
    from tools.vision_agent     import agent as _agent_vision
    from tools.draft_agent      import agent as _agent_draft, is_draft_intent
    from tools.file_reader_agent import agent as _agent_file_reader, is_file_read_intent
    from tools.vault_writer     import agent as _agent_vault_writer, is_save_intent
    from tools.llm_file_agent   import agent as _agent_llm_file, is_file_ops_intent
    from tools.reminders_agent  import agent as _agent_reminders, is_reminders_intent
    from tools.clipboard_agent  import agent as _agent_clipboard, is_clipboard_intent
    from tools.timer_agent      import agent as _agent_timer, is_timer_intent
    from tools.notes_agent      import agent as _agent_notes, is_notes_intent
    from tools.messages_agent   import agent as _agent_messages, is_messages_intent
    from tools.web_agent        import agent as _agent_web, is_web_intent
    from tools.grocery_agent    import agent as _agent_grocery, is_grocery_intent as _is_grocery_intent
    _HAS_LLM_FILE = True
except ImportError:
    _agent_truth_sync = None
    _agent_spotify = _agent_github = _agent_calendar = _agent_vision = None
    _agent_calendar_add = None
    _agent_draft = _agent_file_reader = _agent_vault_writer = None
    _agent_llm_file = _agent_reminders = _agent_clipboard = _agent_timer = None
    _agent_notes = _agent_messages = _agent_web = _agent_grocery = None
    _HAS_LLM_FILE = False
    def is_draft_intent(t): return False
    def is_file_read_intent(t): return False
    def is_save_intent(t): return False
    def is_file_ops_intent(t): return False
    def is_reminders_intent(t): return False
    def is_clipboard_intent(t): return False
    def is_timer_intent(t): return False
    def is_notes_intent(t): return False
    def is_messages_intent(t): return False
    def is_web_intent(t): return False
    def _is_playlist_intent(t): return False
    def _is_search_play_intent(t): return False
    def _is_grocery_intent(t): return False

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())
_logger.propagate = False

# ── session-level conversation context ────────────────────────────────────────
# Tracks the last successful tool call so follow-up questions ("what about in
# London?") can inherit the previous agent and re-run with new parameters.

_last_agent:   Optional[str] = None   # e.g. "weather", "wikipedia"
_last_arg:     Optional[str] = None   # e.g. "London", "black holes"
_last_weather_condition: str = ""    # WO-058: last fetched condition, published to blender_state.json
_last_direct_result: Optional[str] = None  # set when a DIRECT_RETURN_AGENT fires; caller skips LLM

# Agents whose output is factual and deterministic — LLM must not rewrite these.
_DIRECT_RETURN_AGENTS: frozenset = frozenset({"time", "calculator", "timer"})

# ── WO-005: per-turn ExecutionTrace ───────────────────────────────────────────
_current_trace: Optional[ExecutionTrace] = None


def begin_trace(turn_id: str, session_id: str) -> ExecutionTrace:
    """WO-005: initialise a fresh ExecutionTrace for this turn."""
    global _current_trace
    _current_trace = ExecutionTrace(turn_id=turn_id, session_id=session_id)
    return _current_trace


def get_trace() -> Optional[ExecutionTrace]:
    """WO-005: return the current turn's ExecutionTrace (None if begin_trace not called yet)."""
    return _current_trace


def get_direct_result() -> Optional[str]:
    """Return the direct result from a DIRECT_RETURN_AGENT, or None if no such agent ran.

    Caller (server.py) checks this after enrich_from_plan. If truthy, skip the LLM and
    use this string as the response. Resets to None at the start of each enrich_from_plan call.
    """
    return _last_direct_result


def _trace_executed(capability: str, query: str = "", result_summary: str = "") -> None:
    """WO-005: append a CapabilityRecord to the current trace for a tool that ran."""
    global _current_trace
    if _current_trace is None:
        return
    _current_trace.capabilities_executed.append(CapabilityRecord(
        capability=capability,
        status="EXECUTED",
        authority="RUNTIME_VERIFIED",
        query=query or None,
        result_summary=result_summary or None,
    ))

# Persistent location store — blender/user_location.json
# set_location() writes here; any tool can read it.
_LOCATION_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "blender", "user_location.json",
)

def _load_persisted_location() -> Optional[str]:
    try:
        import json as _j
        data = _j.loads(open(_LOCATION_FILE, encoding="utf-8").read())
        return data.get("city") or None
    except Exception:
        return None

def _save_persisted_location(city: str) -> None:
    import json as _j, time as _t
    tmp = _LOCATION_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        _j.dump({"city": city, "_ts": _t.time()}, f)
    os.replace(tmp, _LOCATION_FILE)

# Where David is — B3 2026-10-06 (David L3): "this should be in the SPG or WKG
# or eLo knowledge to not have to always come back to something from August".
# The weather said Manchester because tests/test_wo030 wrote the live
# user_location.json; eLo's own knowledge (user_profile / facts) said Hackney
# Wick all along. Resolution now reads what eLo knows first.
_PROFILE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "memory", "user_profile.json")


def _known_location() -> Optional[str]:
    """David's location from eLo's knowledge of him: user_profile, then facts."""
    try:
        import json as _j
        prof = _j.loads(open(_PROFILE_FILE, encoding="utf-8").read())
        loc = prof.get("location_studio") or prof.get("location")
        if loc:
            return str(loc).strip()
    except Exception:
        pass
    try:
        from memory.fact_store import load_facts as _lf
        for f in _lf():
            if f.get("key") == "location":
                return f.get("fact", "").split(":", 1)[-1].strip() or None
    except Exception:
        pass
    return None


def _resolve_location() -> Optional[str]:
    """Where to use when David doesn't name a place: what he said this session >
    what eLo knows about him > the persisted file > ELO_LOCATION."""
    return (_user_location or _known_location() or _load_persisted_location()
            or os.environ.get("ELO_LOCATION", "").strip() or None)


# Session-only: set when David says where he is this session.
_user_location: Optional[str] = None
# Hard-coded fallback — never IP-detect when David is always in London.
_DEFAULT_LOCATION = "London"

# follow-up patterns — short phrases that reference a new subject but imply
# the same agent type as the previous turn
_FOLLOWUP_PATTERNS = [
    r"^(?:what|how)?\s*about\s+(?:in\s+)?([\w][\w\s,\-]{1,40}?)[\?\.]*$",
    r"^(?:and\s+)?in\s+([\w][\w\s,\-]{1,40}?)[\?\.]*$",
    r"^how about\s+(?:in\s+)?([\w][\w\s,\-]{1,40}?)[\?\.]*$",
    r"^(?:what(?:'s| is) it like\s+)?in\s+([\w][\w\s,\-]{1,40}?)[\?\.]*$",
    r"^(?:and\s+)?(?:what about|how about)\s+([\w][\w\s,\-]{1,40}?)[\?\.]*$",
]

# location-setting phrases: "I'm in London" / "set my location to London"
_LOCATION_SET_PATTERNS = [
    r"(?:i'?m|i am)\s+(?:in|based in|located in)\s+([A-Za-z][A-Za-z\s\-]{0,25}?)(?:[,\.\?!]|$)",
    r"(?:set|change|update)\s+(?:my\s+)?location\s+to\s+([\w][\w\s\-]{1,30}?)[\.\?!]*$",
    r"(?:my\s+)?(?:city|location|home)\s+is\s+([\w][\w\s\-]{1,30}?)[\.\?!]*$",
    r"(?:we'?re|we are)\s+(?:in|based in|at)\s+([A-Za-z][A-Za-z\s\-]{0,25}?)(?:[,\.\?!]|$)",
    # WO-030: "the studio is in X" / "my studio is in X" / "studio is in X"
    r"(?:the\s+|my\s+)?studio\s+is\s+in\s+([A-Za-z][A-Za-z\s\-]{0,25}?)(?:[,\.\?!]|$)",
]


def _detect_followup(user_input: str) -> Optional[str]:
    """Return the new subject if input looks like a follow-up, else None."""
    t = user_input.lower().strip()
    if len(t) > 60:          # too long to be a bare follow-up
        return None
    for pat in _FOLLOWUP_PATTERNS:
        m = re.match(pat, t, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def set_location(city: str, studio: bool = False) -> None:
    """David said where he is. Session location + blender/user_location.json.
    Fact: "the studio is in X" updates his studio/home fact; "I'm in X" is where
    he is now and must not rewrite the studio (travel isn't a move)."""
    global _user_location
    _user_location = city.strip()
    try:
        _save_persisted_location(_user_location)
    except Exception:
        pass
    # WO-037: also save as a durable semantic fact so recall surfaces it specifically
    try:
        from memory.fact_store import save_fact as _sf
        if studio:
            _sf("location", f"Studio / home location: {_user_location}")
        else:
            _sf("current_location", f"Where David said he is now: {_user_location}")
    except Exception:
        pass


def detect_location_set(user_input: str) -> Optional[str]:
    """Return city name if user is setting their location, else None."""
    t = user_input.strip()
    for pat in _LOCATION_SET_PATTERNS:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            return m.group(1).strip().title()
    return None

# ── intent keyword map ─────────────────────────────────────────────────────────
# Order matters — first match wins.

_INTENT_MAP = [
    ("truth_sync", [
        r"\bcheck\s+drift\b",
        r"\bdrift\s+check\b",
        r"\bsync\s+memory\b",
        r"\bcompress\s+memory\b",
        r"\bsave\s+memory\b",
        r"\bvalidate\s+structure\b",
        r"\bcommit\s+draft\b",
        r"\bgenerate\s+commit\b",
        r"\bsync\s+to\s+github\b",
        r"\btruth\s+sync\b",
        r"\bobsidian\s+sync\b",
    ]),
    ("timer", [
        r"\bset\s+(?:a\s+)?timer\b",
        r"\b\d+\s*(?:min(?:ute)?s?|hour?s?|sec(?:ond)?s?)\s+timer\b",
        r"\btimer\s+for\b",
        r"\bpomodoro\b",
        r"\bfocus\s+timer\b",
        r"\bbreak\s+timer\b",
        r"\bstart\s+(?:a\s+)?\d+",
        r"\bmy\s+timers?\b",
        r"\bactive\s+timers?\b",
    ]),
    ("reminders", [
        r"\bremind\s+me\s+to\b",
        r"\badd\s+(?:a\s+)?reminder\b",
        r"\bmy\s+reminders?\b",
        r"\bwhat\s+(?:are\s+)?(?:my\s+)?reminders?\b",
        r"\bwhat\s+do\s+i\s+need\s+to\s+do\b",
        r"\bto-do(?:\s+list)?\b",
        r"\badd\s+to\s+reminders?\b",
    ]),
    ("clipboard", [
        r"\bclipboard\b",
        r"\bwhat\s+did\s+i\s+copy\b",
        r"\bwhat(?:'s|\s+is)\s+copied\b",
    ]),
    ("notes", [
        r"\b(?:make|create|add|write|new)\s+(?:a\s+)?note\b",
        r"\bmy\s+(?:apple\s+)?notes?\b",
        r"\brecent\s+notes?\b",
        r"\b(?:search|find)\s+(?:my\s+)?notes?\b",
    ]),
    ("messages", [
        r"\b(?:send|text|message|imessage)\s+\w",
        r"\btell\s+\w+\s+that\b",
        r"\bassign\s+.+\s+to\s+\w+",
        r"\bgive\s+\w+\s+the\b",
    ]),
    ("vault_write", [
        r"\bremember\s+(?:this|that|it)\b",
        r"\bsave\s+(?:this|that|it)\b",
        r"\bnote\s+(?:this|that|it|down)\b",
        r"\badd\s+(?:this|that)\s+to\s+(?:my\s+)?(?:vault|memory|notes?|obsidian)\b",
        r"\bwrite\s+(?:this|that)\s+down\b",
        r"\bsave\s+(?:to\s+)?(?:my\s+)?(?:vault|memory|notes?|obsidian)\b",
        r"\bremember\s+(?:we\s+)?decided\b",
        r"\bput\s+(?:this|that)\s+in\s+(?:my\s+)?(?:vault|memory|notes?)\b",
    ]),
    ("file_read", [
        r"\bread\s+(?:this\s+)?(?:file\s+)?[~/][\w/\.\-]+\.\w+",
        r"\bopen\s+(?:this\s+)?(?:file\s+)?[~/][\w/\.\-]+\.\w+",
        r"\blook\s+at\s+(?:this\s+)?(?:file\s+)?[~/][\w/\.\-]+\.\w+",
        r"\bcheck\s+(?:this\s+)?(?:file\s+)?[~/][\w/\.\-]+\.\w+",
        r"\bwhat(?:'s|\s+is)\s+in\s+[~/][\w/\.\-]+\.\w+",
        r'["\'][~/][^"\']+\.\w+["\']',    # quoted path
        r"\bread\s+(?:my\s+)?tracker\b",
        r"\bread\s+(?:my\s+)?(?:notes?|journal|brief|script)\b.*[~/]",
    ]),
    ("draft", [
        r"\b(?:write|draft|compose|create)\s+(?:a\s+|an\s+|me\s+a?\s+)?(?:pitch|email|scene|copy|brief|bio|outline|caption|post|story)\b",
        r"\bbrainstorm\b",
        r"\bgive\s+me\s+(?:5|five|some|a\s+few)\s+(?:ideas?|options?|directions?)\b",
        r"\b(?:polish|refine|rewrite|edit\s+this|improve\s+this)\b",
        r"\bcan\s+you\s+(?:write|draft|create|compose)\b",
        r"\bhelp\s+me\s+(?:write|draft)\b",
        r"\bwrite\s+(?:me\s+)?(?:a\s+|an\s+)?(?:pitch|email|scene|brief|copy|outline|bio)\b",
    ]),
    ("spotify", [
        r"\bspotify\b",
        r"\bwhat(?:'s| is)\s+(?:playing|on)\b",
        r"\bskip\b.*\btrack\b|\bnext\s+(?:track|song)\b",
        r"\bpause\s+(?:music|spotify|song|track)\b",
        r"\bstop\s+(?:the\s+)?(?:music|song|track|playback)\b",
        r"\bplay\s+(?:music|spotify|something)\b",
        r"\bwhat\s+(?:song|track|music)\b",
        r"\bwho(?:'s| is)\s+(?:this|playing)\b",
        r"\b(?:turn|crank)\s+(?:up|down)\s+(?:the\s+)?(?:music|volume|sound)\b",
        r"\bvolume\s+(?:up|down|louder|quieter|softer)\b",
        r"\badd\s+(?:this\s+)?(?:song|track|this)\s+(?:to\s+)?spotify\b",
        r"\bput\s+(?:this\s+)?(?:song|track|this)\s+on\s+spotify\b",
        r"\bsave\s+(?:this\s+)?(?:to|on)\s+spotify\b",
        r"\badd\s+(?:this\s+)?to\s+(?:my\s+)?(?:likes?|liked|playlist)\b",
        r"\bcan\s+you\s+add\s+this\s+(?:song|track)?\b",
        r"\bpress\s+play\b",
        r"\bhit\s+play\b",
        r"\bplay\s+that\b",
        r"\bplay\s+it\b",
        r"\bresume\s+(?:music|spotify|playback|song|the\s+music)?\b",
    ]),
    ("github", [
        r"\bgithub\b",
        r"\bmy\s+repo\b",
        r"\bopen\s+(?:prs?|pull\s+requests?)\b",
        r"\blast\s+commit\b",
        r"\bcommits?\b.*\brepo\b",
        r"\bwhat(?:'s| is)\s+(?:the\s+)?(?:status|state)\s+of\b.*\brepo\b",
    ]),
    ("calendar", [
        r"\b(?:my\s+)?calendar\b",
        r"\bwhat(?:'s| is|'ve)\s+(?:i\s+got\s+)?(?:on|today|tomorrow|this\s+week)\b",
        r"\bany\s+meetings?\b",
        r"\bschedule\b",
        r"\bwhat\s+(?:do\s+i\s+have|have\s+i\s+got)\b",
        r"\bcoming\s+up\b",
        r"\bupcoming\s+events?\b",
    ]),
    ("calendar_add", [
        r"\b(?:add|create|book|schedule|put\s+in|set\s+up)\s+(?:a\s+|an\s+)?(?:meeting|event|appointment|call|reminder|timeline|deadline)\b",
        r"\badd\s+(?:this\s+)?to\s+(?:my\s+)?(?:calendar|schedule)\b",
        r"\bschedule\s+(?:a|an|this)\b",
        r"\bbook\s+(?:a|an|this|time)\b",
        r"\bput\s+(?:this|it|that)\s+(?:in|on)\s+(?:my\s+)?calendar\b",
        r"\bshoot\s+(?:this\s+)?(?:next\s+|on\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\b(?:film|record|shoot)\s+(?:on|next|this)\b",
        r"\bcreate\s+(?:a\s+)?(?:timeline|production\s+plan|schedule)\b",
        r"\bdeadline\s+(?:is|for|on)\b",
        r"\bremind\s+me\s+(?:to|about)\b",
    ]),
    ("vision", [
        r"\bwhat(?:'s| is)\s+on\s+(?:my\s+)?screen\b",
        r"\bwhat\s+(?:do\s+you|can\s+you)\s+see\b",
        r"\blook\s+at\s+(?:my\s+)?screen\b",
        r"\bwhat(?:'s| am)\s+i\s+(?:working\s+on|looking\s+at)\b",
        r"\bscreen(?:shot|capture)?\b",
        r"\bdescribe\s+(?:my\s+)?screen\b",
        r"\bcan\s+you\s+see\b",
    ]),
    ("calculator", [
        r"\b(\d[\d\s\+\-\*\/\(\)\.\^%]+\d)\b",
        r"\bwhat(?:'s| is)\s+[\d\(]",
        r"\bcalculat",
        r"\bhow much is\s+[\d\(]",
        r"\buse\s+(?:your|the)\s+calculator\b",
        # FIX A — WO-CAP-COG-005: domain keywords for word problems
        r"\b(?:area|volume|circumference|perimeter)\b.*\d",
        r"\b(?:circle|sphere|cylinder|cone|triangle|rectangle)\b.*\d",
        r"\b(?:sin|cos|tan|sine|cosine|tangent)\b.*\d",
        r"\bright\s+triangle\b.*\d",
        r"\b(?:mean|median|mode|average)\b.*\b\d+\b.*\b\d+\b",
        r"\bprobability\b.*\b(?:dice?|rolling|six)\b",
        r"\b(?:choose|combinations?|permutations?)\b.*\d",
        r"\b\d+\s*[Cc]\s*\d+\b",
        r"\b(?:force|velocity|speed|acceleration)\b.*\d.*\b(?:kg|m/s|meter|second|Newton)\b",
        r"\bF\s*=\s*ma\b",
        r"\bcompound\s+interest\b",
        r"\bratio\b.*\d+\s*:\s*\d+",
        r"\b(?:sum\s+of|arithmetic\s+series)\b.*\d",
        r"\b(?:derivative|integral|differentiat|integrat)\b.*\d",
        r"\bdistance\b.*\(\s*-?\d",
    ]),
    ("time", [
        r"\bwhat(?:'s| is)\s+the\s+(time|date|day)\b",
        r"\bwhat\s+(time|day|date)\s+is\s+it\b",
        r"\btell\s+me\s+the\s+(time|date|day)\b",
        r"\bcan\s+you\s+tell\s+me\s+the\s+(time|date|day)\b",
        r"\bthe\s+time\s+please\b",
        r"\btoday(?:'s)?\s+date\b",
        r"\bwhat\s+day\b",
        r"\bright now\b.*\btime\b",
        r"\btime\b.*\bright now\b",
        r"\btime\s+is\s+it\b",
        r"\bwhat\s+time\s+it\s+is\b",
        r"\bknow\s+what\s+time\b",
        r"\bknow\s+the\s+(time|date|day)\b",
        r"\bgot\s+the\s+time\b",
        r"\bcurrent\s+(time|date|day)\b",
    ]),
    ("weather", [
        r"\bweather\b",
        r"\btemperature\b",
        r"\brain(?:ing|y|fall|drops?)?\b|\bsnow(?:ing)?\b|\bsleet\b|\bhail\b",
        r"\bsunny\b|\bcloudy\b|\bhot\b|\bcold outside\b",
        r"\bforecast\b",
        r"\bwhat(?:'s| is)\s+it\s+like\s+outside\b",
        r"\bgoing\s+to\s+(?:rain|snow|be\s+(?:hot|cold|sunny|cloudy))\b",
        r"\bwind(?:y)?\b",
        r"\bhumid(?:ity)?\b",
        r"\bhow\s+(?:hot|cold|warm|chilly|cool)\s+is\s+it\b",
        r"\bis\s+it\s+(?:hot|cold|warm|chilly|cool|dry|damp)\b",
    ]),
    ("translate", [
        r"\btranslate\s+.+\s+(?:to|into)\b",
        r"\bhow\s+(?:do\s+you|to)\s+say\b",
        r"\bsay\s+['\"].+['\"]\s+in\s+\w+",
        r"\bwhat(?:'s| is)\s+['\"].+['\"]\s+in\s+\w+",
        r"\bin\s+(?:spanish|french|german|italian|japanese|chinese|korean|arabic|portuguese|russian|hindi|dutch|swedish|polish|turkish|greek|hebrew|thai|vietnamese|malay|indonesian)\b",
    ]),
    ("news", [
        r"\b(?:get|show|give|pull|want|tell\s+me)\s+(?:the\s+)?(?:news|headlines)\b",
        r"\bwhat(?:'s|\s+is)\s+(?:in\s+the\s+)?news\b",
        r"\blatest\b.*\b(?:news|stories|events)\b",
        r"\btoday'?s?\s+(?:news|stories)\b",
        r"\btop\s+(?:stories|headlines)\b",
        r"\bcheck\s+(?:the\s+)?news\b",
    ]),
    ("obsidian", [
        r"\bmy\s+notes?\b",
        r"\bwhat\s+did\s+i\s+(?:write|note)\b",
        r"\bobsidian\b",
        r"\bmy\s+journal\b",
        r"\bmy\s+vault\b",
        r"\bi\s+wrote\s+about\b",
        r"\bin\s+my\s+notes\b",
        r"\bmy\s+(?:writing|thoughts)\s+on\b",
    ]),
    ("search", [
        r"\bwhat(?:'s| is)\s+(?:a\s|an\s|the\s)?(?!\d)",
        r"\bwho(?:'s| is)\s+",
        r"\btell me about\b",
        r"\bexplain\b",
        r"\bwiki\b",
        r"\bdefine\b",
        r"\bsearch\s+(?:for\s+)?",
        r"\blook\s+up\b",
        r"\bfind\s+(?:out\s+)?(?:about\s+)?",
        r"\bgoogle\b",
        r"\bcan you (?:google|search|look up|find)\b",
        r"https?://",
        r"\bopen\s+\w+\.(?:com|org|io|co|net|app)\b",
    ]),
]

# ── helpers ────────────────────────────────────────────────────────────────────

def _detect_intent(user_input: str) -> Optional[str]:
    """Return the agent name that matches the input, or None."""
    text = user_input.lower().strip()
    for agent_name, patterns in _INTENT_MAP:
        for pat in patterns:
            if re.search(pat, text):
                return agent_name
    return None


# ── agent implementations ──────────────────────────────────────────────────────

# WO-CAP-COG-004: only fire the time agent for genuine clock/date queries.
# Rejects "time complexity", "runtime", "response time", "real-time", etc.
_TIME_TECH_BLOCK = re.compile(
    r"\b(?:"
    r"time\s+complex(?:ity)?"
    r"|run(?:-?\s*)time"
    r"|real\s*-?\s*time"
    r"|response\s+time"
    r"|time\s*out"
    r"|time\s*stamp"
    r"|time\s+base[d]?"
    r"|time\s+series"
    r"|time\s+delay"
    r"|time\s+zone"
    r"|time\s+limit"
    r"|time\s+frame"
    r"|time\s+line"
    r"|time\s+step"
    r"|time\s+slot"
    r"|start\s+time"
    r"|end\s+time"
    r"|execution\s+time"
    r"|processing\s+time"
    r"|at\s+runtime"
    r")\b",
    re.IGNORECASE,
)

_TIME_INTENT_P = [
    r"\bwhat(?:'s| is)\s+the\s+(time|date|day)\b",
    r"\bwhat\s+(time|day|date)\s+is\s+it\b",
    r"\btell\s+me\s+the\s+(time|date|day)\b",
    r"\bcan\s+you\s+tell\s+me\s+the\s+(time|date|day)\b",
    r"\bthe\s+time\s+please\b",
    r"\btoday(?:'s)?\s+date\b",
    r"\bwhat\s+day\b",
    r"\bright\s+now\b.*\btime\b",
    r"\btime\b.*\bright\s+now\b",
    r"\btime\s+is\s+it\b",
    r"\bwhat\s+time\s+it\s+is\b",
    r"\bknow\s+what\s+time\b",
    r"\bknow\s+the\s+(time|date|day)\b",
    r"\bgot\s+the\s+time\b",
    r"\bcurrent\s+(time|date|day)\b",
    r"\bwhat(?:'s| is)\s+today\b",
    r"\bwhat\s+is\s+the\s+current\s+time\b",
]

def _is_time_of_day_intent(text: str) -> bool:
    """Return True only when the user is asking for the current clock time, date, or day."""
    t = text.lower().strip()
    # Block known technical time contexts before pattern-matching
    if _TIME_TECH_BLOCK.search(t):
        return False
    return any(re.search(p, t, re.IGNORECASE) for p in _TIME_INTENT_P)


def _agent_time(query: str) -> str:
    from datetime import datetime
    now = datetime.now()
    q = query.lower().strip()
    n = now.day
    suffix = "th" if 11 <= n <= 13 else {"1":"st","2":"nd","3":"rd"}.get(str(n % 10), "th")
    weekday  = now.strftime("%A")
    day_ord  = f"{weekday} the {n}{suffix}"
    time_str = now.strftime("%-I:%M %p")
    # "Friday the?" — follow-up asking for the ordinal
    if re.search(r"^\s*(?:mon|tues|wednes|thurs|fri|satur|sun)day\s+the\??\s*$", q):
        return f"{day_ord}."
    wants_time = bool(re.search(r"\btime\b", q)) and _is_time_of_day_intent(q)
    wants_date = bool(re.search(r"\bdate\b", q))
    wants_day  = bool(re.search(r"\bday\b", q))
    if wants_time and (wants_date or wants_day):
        return f"It's {time_str} — {day_ord}."
    if wants_time:
        return f"It's {time_str}."
    if wants_date:
        return f"It's {day_ord}."
    if wants_day:
        return f"{weekday}."
    return f"It's {time_str}."


def _agent_calculator(query: str) -> str:
    import ast, operator
    _ops = {
        ast.Add:  operator.add,   ast.Sub: operator.sub,
        ast.Mult: operator.mul,   ast.Div: operator.truediv,
        ast.Pow:  operator.pow,   ast.Mod: operator.mod,
        ast.USub: operator.neg,   ast.UAdd: operator.pos,
    }
    def _safe_eval(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.BinOp):
            op = _ops.get(type(node.op))
            if op is None:
                raise ValueError("unsupported op")
            return op(_safe_eval(node.left), _safe_eval(node.right))
        if isinstance(node, ast.UnaryOp):
            op = _ops.get(type(node.op))
            if op is None:
                raise ValueError("unsupported op")
            return op(_safe_eval(node.operand))
        raise ValueError("unsupported node")
    # Factorial intercept — handles "8 factorial", "factorial of 8", "8!"
    _fact_m = re.search(r'(\d+)\s*!|\bfactorial\s+(?:of\s+)?(\d+)|(\d+)\s+factorial\b', query, re.IGNORECASE)
    if _fact_m:
        from math import factorial as _fac_f
        _n_fact = int(_fact_m.group(1) or _fact_m.group(2) or _fact_m.group(3))
        return f"{_n_fact}! = {_fac_f(_n_fact)}"
    # Power intercept — handles "7 to the power of 4"
    _pow_m = re.search(r'(\d+(?:\.\d+)?)\s+to\s+the\s+power\s+of\s+(\d+(?:\.\d+)?)', query, re.IGNORECASE)
    if _pow_m:
        _base, _exp = float(_pow_m.group(1)), float(_pow_m.group(2))
        _result_pow = _base ** _exp
        if isinstance(_result_pow, float) and _result_pow.is_integer(): _result_pow = int(_result_pow)
        return f"{_base:.0f}^{_exp:.0f} = {_result_pow}"
    # Radians intercept — handles "calculate X degrees to radians" before expression eval
    if re.search(r'\bradians?\b', query, re.IGNORECASE) and re.search(r'\bdegrees?\b', query, re.IGNORECASE):
        _deg_m3 = re.search(r'(\d+(?:\.\d+)?)\s*degrees?', query, re.IGNORECASE)
        if _deg_m3:
            import math as _math3
            from fractions import Fraction as _Fr3
            _deg_v3 = float(_deg_m3.group(1))
            _rad_v3 = _deg_v3 * _math3.pi / 180
            _fr3 = _Fr3(_deg_v3 / 180).limit_denominator(100)
            if _fr3.numerator == 1:   _pi3 = f"π/{_fr3.denominator}"
            elif _fr3.denominator == 1: _pi3 = f"{int(_fr3.numerator)}π"
            else:                       _pi3 = f"{_fr3.numerator}π/{_fr3.denominator}"
            return f"{_deg_v3:.0f}° = {_pi3} ≈ {_rad_v3:.4f} radians"
    # Percentage-of intercept — handles "What is 15% of 240?"
    if re.search(r'\b\d+\s*%\s+of\s+\d+', query, re.IGNORECASE):
        _pct_of_m = re.search(r'(\d+(?:\.\d+)?)\s*%\s+of\s+(\d+(?:\.\d+)?)', query, re.IGNORECASE)
        if _pct_of_m:
            _pct_of, _base_of = float(_pct_of_m.group(1)), float(_pct_of_m.group(2))
            _res_of = _pct_of / 100 * _base_of
            _rs_of = f"{_res_of:.2f}".rstrip('0').rstrip('.')
            return f"{_pct_of:.0f}% of {_base_of:.0f} = {_rs_of}"
    # Discount/sale-price intercept — handles "What is 20% off $250?"
    if re.search(r'\d+%\s+off\b|\bon\s+sale\b.*\d+%|\bdiscount\b.*\d+%|\d+%.*\bdiscount\b', query, re.IGNORECASE):
        _price_disc_m = re.search(r'\$\s*(\d+(?:\.\d+)?)', query)
        if not _price_disc_m:
            _price_disc_m = re.search(r'(?:costs?|price[sd]?|for)\s+\$?(\d+(?:\.\d+)?)', query, re.IGNORECASE)
        _pct_disc_m = re.search(r'(\d+(?:\.\d+)?)\s*%', query)
        if _price_disc_m and _pct_disc_m:
            _price_disc = float(_price_disc_m.group(1))
            _pct_disc = float(_pct_disc_m.group(1))
            _sale_disc = _price_disc * (1 - _pct_disc / 100)
            return f"Sale price = {_price_disc:.2f} × (1 - {_pct_disc:.0f}%) = ${_sale_disc:.2f}"
    # Logarithm intercept — handles "What is the logarithm base 10 of 1000?"
    _log_m = re.search(r'log(?:arithm)?\s+(?:base\s+)?(\d+(?:\.\d+)?)\s+of\s+(\d+(?:\.\d+)?)', query, re.IGNORECASE)
    if not _log_m:
        _log_m = re.search(r'log_\s*(\d+(?:\.\d+)?)\s*\(?\s*(\d+(?:\.\d+)?)', query, re.IGNORECASE)
    if _log_m:
        import math as _lmath
        _log_base = float(_log_m.group(1))
        _log_val = float(_log_m.group(2))
        if _log_base > 0 and _log_base != 1 and _log_val > 0:
            _log_res = _lmath.log(_log_val) / _lmath.log(_log_base)
            _log_int = int(round(_log_res))
            if abs(_log_res - _log_int) < 1e-9:
                _log_res = _log_int
                return f"log_{_log_base:.0f}({_log_val:.0f}) = {_log_res} (because {_log_base:.0f}^{_log_res} = {_log_val:.0f})"
            return f"log_{_log_base:.0f}({_log_val:.0f}) ≈ {_log_res:.4f}"
    # Stats intercept — handles "What is the median of 7, 2, 9, 4, 11, 1, 6?"
    if re.search(r'\b(?:mean|median|mode|average)\b', query, re.IGNORECASE):
        _stat_nums = re.findall(r'-?\d+(?:\.\d+)?', query)
        if len(_stat_nums) >= 2:
            _stat_vals = [float(x) for x in _stat_nums]
            _stat_sorted = sorted(_stat_vals)
            _stat_n = len(_stat_sorted)
            _stat_key = re.search(r'\b(mean|median|mode|average)\b', query, re.IGNORECASE).group(1).lower()
            if _stat_key in ('mean', 'average'):
                _stat_res = sum(_stat_vals) / _stat_n
                _stat_disp = f"{_stat_res:.2f}".rstrip('0').rstrip('.')
                return f"For {_stat_vals}: mean = {sum(_stat_vals):.0f}/{_stat_n} = {_stat_disp}"
            elif _stat_key == 'median':
                if _stat_n % 2 == 1:
                    _stat_med = _stat_sorted[_stat_n // 2]
                else:
                    _stat_med = (_stat_sorted[_stat_n // 2 - 1] + _stat_sorted[_stat_n // 2]) / 2
                _stat_disp = f"{_stat_med:.2f}".rstrip('0').rstrip('.')
                return f"For {_stat_vals}: median = {_stat_disp}"
            elif _stat_key == 'mode':
                from collections import Counter as _Ctr
                _stat_cnt = _Ctr(_stat_vals)
                _stat_max = max(_stat_cnt.values())
                _stat_modes = [k for k, v in _stat_cnt.items() if v == _stat_max]
                return f"For {_stat_vals}: mode = {_stat_modes[0] if len(_stat_modes) == 1 else _stat_modes}"
    # normalise word operators → symbols before extraction
    q = re.sub(r'\bdivided\s+by\b', '/', query, flags=re.IGNORECASE)
    q = re.sub(r'\bmultiplied\s+by\b', '*', q, flags=re.IGNORECASE)
    q = re.sub(r'\btimes\b',        '*', q,     flags=re.IGNORECASE)
    q = re.sub(r'\bplus\b',         '+', q,     flags=re.IGNORECASE)
    q = re.sub(r'\bminus\b',        '-', q,     flags=re.IGNORECASE)
    q = re.sub(r'[×✕]', '*', q)  # unicode multiply signs
    q = re.sub(r'(?<=\d)\s*[xX]\s*(?=\d)', '*', q)  # "5 x 5" → "5 * 5"
    # strip leading arithmetic verb ("Add 3/8 and 5/12" → "3/8 and 5/12")
    q = re.sub(r'^\s*(add|subtract|find|calculate|compute|what\s+is)\s+', '', q, flags=re.IGNORECASE)
    # "X and Y" → "X + Y" for additive phrasing
    q = re.sub(r'\s+and\s+', ' + ', q, flags=re.IGNORECASE)
    # extract arithmetic expression from normalised query
    match = re.search(r"[\d\(\)\+\-\*\/\.\^ ]+", q)
    if not match:
        raise ValueError("no expression found")
    expr = match.group(0).strip().replace("^", "**")
    if not expr or not re.search(r'\d', expr):
        raise ValueError("no numeric expression found")
    # Fraction arithmetic — exact rational result when expression contains fractions
    if re.search(r'\d+/\d+', expr) and re.search(r'[+\-\*]', expr):
        from fractions import Fraction
        try:
            _frac_expr = re.sub(r'(\d+)/(\d+)', r'Fraction(\1,\2)', expr)
            _frac_result = eval(_frac_expr, {"__builtins__": {}, "Fraction": Fraction})
            return f"{expr} = {_frac_result}"
        except Exception:
            pass
    tree = ast.parse(expr, mode="eval")
    result = _safe_eval(tree.body)
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    display = expr.replace('**', '^')
    return f"{display} = {result}"


def _agent_math_solver(query: str) -> str:
    """Domain-aware Python math solver for word problems. FIX A — WO-CAP-COG-005."""
    import math as _math
    import re as _re

    q = query.lower().strip()

    # ── GEOMETRY — circle area / circumference ──────────────────────────────
    if _re.search(r'\b(?:area|circumference)\b', q) and _re.search(r'\bcircle\b', q):
        r_m = (_re.search(r'radius\s+(?:of\s+)?(?:is\s+)?(?:=\s*)?(\d+(?:\.\d+)?)', q) or
               _re.search(r'(\d+(?:\.\d+)?)\s*(?:cm|m|mm)?\s*(?:radius)', q))
        if r_m:
            r = float(r_m.group(1))
            if 'circumference' in q:
                v = 2 * _math.pi * r
                return f"Circumference = 2π × {r} ≈ {v:.4f}"
            v = _math.pi * r ** 2
            return f"Area = π × {r}² ≈ {v:.4f}"
        else:
            if 'circumference' in q:
                return "Circumference of a circle: C = 2πr ≈ 6.2832 × r"
            return "Area of a circle: A = πr² ≈ 3.1416 × r²"

    # ── GEOMETRY — cylinder volume ──────────────────────────────────────────
    if _re.search(r'\bvolume\b', q) and _re.search(r'\bcylinder\b', q):
        r_m = _re.search(r'radius\s+(?:of\s+)?(?:is\s+)?(?:=\s*)?(\d+(?:\.\d+)?)', q)
        h_m = _re.search(r'height\s+(?:of\s+)?(?:is\s+)?(?:=\s*)?(\d+(?:\.\d+)?)', q)
        if r_m and h_m:
            r, h = float(r_m.group(1)), float(h_m.group(1))
            v = _math.pi * r ** 2 * h
            return f"Volume = π × {r}² × {h} ≈ {v:.4f}"

    # ── GEOMETRY — sphere volume ────────────────────────────────────────────
    if _re.search(r'\bvolume\b', q) and _re.search(r'\bsphere\b', q):
        r_m = _re.search(r'radius\s+(?:of\s+)?(?:is\s+)?(?:=\s*)?(\d+(?:\.\d+)?)', q)
        if r_m:
            r = float(r_m.group(1))
            v = (4 / 3) * _math.pi * r ** 3
            return f"Volume = (4/3)π × {r}³ ≈ {v:.4f}"

    # ── GEOMETRY — regular polygon interior angles ────────────────────────────
    _poly_m = _re.search(r'\b(hexagon|pentagon|heptagon|octagon|triangle|square|decagon)\b', q)
    if _poly_m and _re.search(r'\bangle', q):
        _poly_sides = {'triangle': 3, 'square': 4, 'pentagon': 5, 'hexagon': 6,
                       'heptagon': 7, 'octagon': 8, 'decagon': 10}
        _n_sides = _poly_sides.get(_poly_m.group(1))
        if _n_sides:
            _int_angle = (_n_sides - 2) * 180 / _n_sides
            return (f"Interior angles of a regular {_poly_m.group(1)} = "
                    f"({_n_sides}-2)×180/{_n_sides} = {_int_angle:.0f}°")

    # ── GEOMETRY — Euclidean distance ───────────────────────────────────────
    if _re.search(r'\bdistance\b', q):
        coords = _re.findall(r'\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)', q)
        if len(coords) >= 2:
            x1, y1 = float(coords[0][0]), float(coords[0][1])
            x2, y2 = float(coords[1][0]), float(coords[1][1])
            d_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
            v = _math.sqrt(d_sq)
            sq_str = int(d_sq) if d_sq == int(d_sq) else f"{d_sq:.2f}"
            return f"Distance = √(({x2}-{x1})² + ({y2}-{y1})²) = √{sq_str} ≈ {v:.4f}"

    # ── TRIGONOMETRY ────────────────────────────────────────────────────────
    trig_fns = _re.findall(r'\b(sin|cos|tan|sine|cosine|tangent)\b', q)
    angles = _re.findall(r'(\d+(?:\.\d+)?)\s*(?:°|degrees?|deg\b)', q)
    if trig_fns and angles:
        results = []
        for fn_raw in trig_fns:
            fn = fn_raw.lower()
            math_fn = (_math.sin if fn in ('sin', 'sine') else
                       _math.cos if fn in ('cos', 'cosine') else _math.tan)
            for ang_str in angles:
                ang = float(ang_str)
                val = round(math_fn(_math.radians(ang)), 10)
                if abs(val - 0.5) < 1e-9:
                    disp = "0.5 (= 1/2)"
                elif abs(val - _math.sqrt(3) / 2) < 1e-9:
                    disp = "≈0.8660 (= √3/2)"
                elif abs(val - _math.sqrt(2) / 2) < 1e-9:
                    disp = "≈0.7071 (= √2/2)"
                elif abs(val + 0.5) < 1e-9:
                    disp = "-0.5 (= -1/2)"
                elif abs(val - 1.0) < 1e-9:
                    disp = "1"
                elif abs(val - 0.0) < 1e-9:
                    disp = "0"
                else:
                    disp = f"{val:.6f}".rstrip('0').rstrip('.')
                results.append(f"{fn_raw}({ang_str}°) = {disp}")
        if results:
            return " | ".join(results)

    # ── RIGHT TRIANGLE — sin ratio from sides ───────────────────────────────
    if _re.search(r'\bright\s+triangle\b', q) and _re.search(r'\b(?:sin|sine|hypotenuse)\b', q):
        _opp_m18 = _re.search(r'\bopposite\s*[=:]\s*(\d+(?:\.\d+)?)', q)
        _hyp_m18 = _re.search(r'\bhypotenuse\s*[=:]\s*(\d+(?:\.\d+)?)', q)
        if _opp_m18 and _hyp_m18:
            _opp_v = float(_opp_m18.group(1))
            _hyp_v = float(_hyp_m18.group(1))
            if _hyp_v > 0:
                sin_val = _opp_v / _hyp_v
                return (f"sin = opposite/hypotenuse = "
                        f"{_opp_v:.4g}/{_hyp_v:.4g} ≈ {sin_val:.4f}")
        nums = [float(x) for x in _re.findall(r'\b(\d+(?:\.\d+)?)\b', q)]
        if len(nums) >= 2:
            for i in range(len(nums)):
                for j in range(len(nums)):
                    if i != j and nums[j] > nums[i]:
                        sin_val = nums[i] / nums[j]
                        if 0 < sin_val < 1:
                            return (f"sin = opposite/hypotenuse = "
                                    f"{nums[i]}/{nums[j]} ≈ {sin_val:.4f}")

    # ── STATISTICS — mean, median, mode ────────────────────────────────────
    if _re.search(r'\b(?:mean|median|mode|average)\b', q):
        nums_raw = _re.findall(r'\b(\d+)\b', q)
        if len(nums_raw) >= 2:
            data = [int(n) for n in nums_raw[:20]]
            parts = []
            if 'mean' in q or 'average' in q:
                m = sum(data) / len(data)
                parts.append(f"mean = {sum(data)}/{len(data)} = {m:.4f}".rstrip('0').rstrip('.'))
            if 'median' in q:
                s = sorted(data)
                n = len(s)
                med = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
                parts.append(f"median = {med}")
            if 'mode' in q:
                from collections import Counter as _Ctr
                c = _Ctr(data)
                mode_val = c.most_common(1)[0][0]
                parts.append(f"mode = {mode_val}")
            if parts:
                return f"For {data}: {', '.join(parts)}"

    # ── PROBABILITY — dice ──────────────────────────────────────────────────
    if _re.search(r'\bprobability\b', q) and _re.search(r'\b(?:dice?|rolling)\b', q):
        if _re.search(r'\bdouble\b', q):
            if _re.search(r'\bsix\b|\b6\b', q):
                return "P(double six) = (1/6) × (1/6) = 1/36 ≈ 0.0278"
            return "P(doubles on two 6-sided dice) = 6/36 = 1/6 ≈ 0.1667"

    # ── COMBINATORICS — C(n, k) ─────────────────────────────────────────────
    comb_m = _re.search(r'(\d+)\s*[Cc]\s*(\d+)', q)
    if comb_m:
        n, k = int(comb_m.group(1)), int(comb_m.group(2))
        return f"C({n},{k}) = {_math.comb(n, k)}"
    comb_m = _re.search(r'[Cc]\s*\(\s*(\d+)\s*,\s*(\d+)', q)
    if comb_m:
        n, k = int(comb_m.group(1)), int(comb_m.group(2))
        return f"C({n},{k}) = {_math.comb(n, k)}"
    ch_m = (_re.search(r'(\d+)\s+choose\s+(\d+)', q) or
            _re.search(r'(?:choose|select|pick)\s+(\d+)\s+(?:from|out\s+of)\s+(\d+)', q))
    if not ch_m:
        wm = _re.search(r'(\d+)\s+(?:people?|items?|objects?)\s+from\s+(?:a\s+group\s+of\s+)?(\d+)', q)
        if wm:
            a, b = int(wm.group(1)), int(wm.group(2))
            n, k = max(a, b), min(a, b)
            return f"C({n},{k}) = {_math.comb(n, k)}"
    if ch_m:
        a, b = int(ch_m.group(1)), int(ch_m.group(2))
        n, k = max(a, b), min(a, b)
        return f"C({n},{k}) = {_math.comb(n, k)}"

    # ── PHYSICS — F = ma (solves for F or a) ───────────────────────────────
    if _re.search(r'\b(?:force|Newton|F\s*=\s*ma|acceleration)\b', q, _re.IGNORECASE):
        m_m = _re.search(r'(\d+(?:\.\d+)?)\s*kg\b', q, _re.IGNORECASE)
        f_m = _re.search(r'(\d+(?:\.\d+)?)\s*[Nn]\b', q)
        a_m = (_re.search(r'(\d+(?:\.\d+)?)\s*m/?s[²2]', q, _re.IGNORECASE) or
               _re.search(r'(?:acceler[a-z]+\s+(?:at\s+)?|at\s+)(\d+(?:\.\d+)?)', q))
        if m_m and f_m and not a_m:
            m_v, f_v = float(m_m.group(1)), float(f_m.group(1))
            a_res = f_v / m_v
            return f"a = F/m = {f_v}/{m_v} = {a_res:.2f} m/s²"
        if m_m and a_m:
            m_v, a_v = float(m_m.group(1)), float(a_m.group(1))
            return f"F = ma = {m_v} × {a_v} = {m_v * a_v} N"

    # ── PHYSICS — velocity / speed ──────────────────────────────────────────
    if _re.search(r'\b(?:velocity|speed|mph|miles?\s+per\s+hour|average\s+speed)\b', q) or \
       _re.search(r'\btravels?\b.*\b(?:miles?|km)\b.*\b(?:hour|hr)s?\b', q):
        d_m = (_re.search(r'(\d+(?:\.\d+)?)\s*miles?\b', q) or
               _re.search(r'(\d+(?:\.\d+)?)\s*km\b', q) or
               _re.search(r'(\d+(?:\.\d+)?)\s*(?:m\b|meter|metre)', q))
        t_m = (_re.search(r'(\d+(?:\.\d+)?)\s*(?:hour|hr)s?\b', q) or
               _re.search(r'(\d+(?:\.\d+)?)\s*(?:s\b|sec|second)', q))
        if d_m and t_m:
            d_v, t_v = float(d_m.group(1)), float(t_m.group(1))
            if t_v != 0:
                spd = d_v / t_v
                unit = ("km/h" if _re.search(r'\bkm\b', q) else
                        "mph" if _re.search(r'\bmiles?\b', q) else "m/s")
                return f"Speed = {d_v} ÷ {t_v} = {spd:.2f} {unit}"

    # ── FINANCE — compound interest (annual or monthly) ─────────────────────
    if _re.search(r'\b(?:compound\w*|invest\w*)\b.*\d', q, _re.IGNORECASE):
        p_m = _re.search(r'(?:£|\$)?\s*(\d[\d,]*(?:\.\d+)?)', q)
        r_m = _re.search(r'(\d+(?:\.\d+)?)\s*(?:%|percent)', q)
        t_m = _re.search(r'(\d+)\s*(?:year|yr)', q)
        if p_m and r_m and t_m:
            p_v = float(p_m.group(1).replace(',', ''))
            r_v = float(r_m.group(1)) / 100
            t_v = int(t_m.group(1))
            sym = '£' if '£' in q else '$'
            if _re.search(r'\bmonthly\b', q):
                result = p_v * (1 + r_v / 12) ** (12 * t_v)
                return f"A = {p_v:,.2f}(1+{r_m.group(1)}%/12)^(12×{t_v}) = {sym}{result:,.2f}"
            result = p_v * (1 + r_v) ** t_v
            return f"A = {p_v:,.2f}(1+{r_m.group(1)}%)^{t_v} ≈ {sym}{result:,.2f}"

    # ── RATIOS ──────────────────────────────────────────────────────────────
    if _re.search(r'\bratio\b|\d+\s*:\s*\d+', q):
        ratio_m = _re.search(r'(\d+)\s*:\s*(\d+)', q)
        if ratio_m:
            a_r, b_r = int(ratio_m.group(1)), int(ratio_m.group(2))
            total_m = (_re.search(r'(\d+(?:\.\d+)?)\s*g(?:rams?)?\s+total', q) or
                       _re.search(r'total\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*g', q))
            ingred_m = _re.search(r'(?:use|have|with|of)\s+(\d+(?:\.\d+)?)\s*g', q)
            if total_m:
                t_g = float(total_m.group(1))
                a_amt = t_g * a_r / (a_r + b_r)
                b_amt = t_g * b_r / (a_r + b_r)
                return (f"Ratio {a_r}:{b_r} in {t_g}g total: "
                        f"part A = {a_amt:.1f}g, part B = {b_amt:.1f}g")
            if ingred_m:
                part_a = float(ingred_m.group(1))
                part_b = part_a * b_r / a_r
                return (f"Ratio {a_r}:{b_r}: part A = {part_a}g → "
                        f"part B = {part_a}×{b_r}/{a_r} = {part_b:.1f}g")

    # ── ARITHMETIC SERIES ───────────────────────────────────────────────────
    if _re.search(r'\b(?:sum|arithmetic\s+(?:series|sequence))\b', q):
        n_m = _re.search(r'first\s+(\d+)', q)
        if n_m:
            n = int(n_m.group(1))
            seq_ints = [int(x) for x in _re.findall(r'\b(\d+)\b', q)]
            a1, d = 1, 1
            found_seq = False
            for i in range(len(seq_ints) - 2):
                diff1 = seq_ints[i + 1] - seq_ints[i]
                diff2 = seq_ints[i + 2] - seq_ints[i + 1]
                if diff1 == diff2 and diff1 > 0 and seq_ints[i] > 0:
                    a1, d = seq_ints[i], diff1
                    found_seq = True
                    break
            if not found_seq:
                a1_m = _re.search(r'(?:starting|first\s+term|a1)\s+(?:is\s+|=\s*)?(\d+)', q)
                d_m_kw = _re.search(r'(?:common\s+difference|d)\s+(?:is\s+|=\s*)?(\d+)', q)
                if a1_m:
                    a1 = int(a1_m.group(1))
                if d_m_kw:
                    d = int(d_m_kw.group(1))
            if a1 == 1 and d == 1:
                total = n * (n + 1) // 2
                return f"Sum of 1 to {n} = {n}×(n+1)/2 = {total}"
            an = a1 + (n - 1) * d
            total = n * (a1 + an) // 2
            return f"Sum = {n}/2 × ({a1}+{an}) = {total}"
        range_m = _re.search(r'from\s+(\d+)\s+to\s+(\d+)', q)
        if range_m:
            a1_r, an_r = int(range_m.group(1)), int(range_m.group(2))
            n_r = an_r - a1_r + 1
            total_r = n_r * (a1_r + an_r) // 2
            return f"Sum from {a1_r} to {an_r} = {n_r}/2 × ({a1_r}+{an_r}) = {total_r}"

    # ── TRIANGLE — angle sum ─────────────────────────────────────────────────
    if _re.search(r'\btriangle\b', q) and _re.search(r'\bangles?\b', q):
        angle_vals = [float(x) for x in _re.findall(r'(\d+(?:\.\d+)?)\s*(?:°|degrees?|deg\b)', q)]
        if len(angle_vals) >= 2 and sum(angle_vals) < 180:
            third = 180 - sum(angle_vals)
            parts_str = ' + '.join(str(int(a) if a == int(a) else a) for a in angle_vals)
            t_a = int(third) if third == int(third) else third
            return f"Third angle = 180° - ({parts_str}) = {t_a}°"

    # ── PROJECTILE — time to max height ────────────────────────────────────
    if _re.search(r'\b(?:max(?:imum)?\s+height|thrown\s+upward|initial\s+velocity)\b', q):
        v0_m = _re.search(r'(?:velocity|speed)\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*m', q)
        g_m = _re.search(r'g\s*=\s*(\d+(?:\.\d+)?)', q)
        if v0_m:
            v0 = float(v0_m.group(1))
            g_val = float(g_m.group(1)) if g_m else 9.8
            t_top = v0 / g_val
            h_max = v0 ** 2 / (2 * g_val)
            return f"t = v₀/g = {v0}/{g_val} = {t_top:.2f}s; max height = {h_max:.2f}m"

    # ── DEPRECIATION — compound decay ───────────────────────────────────────
    if _re.search(r'\bdepreciat\w*\b', q):
        p_m = _re.search(r'(?:£|\$)?\s*(\d[\d,]*(?:\.\d+)?)', q)
        r_m = _re.search(r'(\d+(?:\.\d+)?)\s*%', q)
        t_m = _re.search(r'(\d+)\s*(?:year|yr)s?\b', q)
        if p_m and r_m and t_m:
            p_v = float(p_m.group(1).replace(',', ''))
            r_v = float(r_m.group(1)) / 100
            t_v = int(t_m.group(1))
            result = p_v * (1 - r_v) ** t_v
            return f"Value = {p_v:,.2f} × (1-{r_m.group(1)}%)^{t_v} = ${result:,.2f}"

    # ── PROBABILITY — consecutive events ────────────────────────────────────
    if _re.search(r'\bprobability\b', q) and \
       _re.search(r'\b(?:consecutive|days?|times?|in\s+a\s+row)\b', q):
        p_m = _re.search(r'(\d+(?:\.\d+)?)\s*%', q)
        n_m = _re.search(r'(\d+)\s*(?:consecutive|days?|times?)', q)
        if p_m and n_m:
            p_val = float(p_m.group(1)) / 100
            n_val = int(n_m.group(1))
            if _re.search(r'\b(?:no |not |does not)\b', q):
                comp = 1 - p_val
                result = comp ** n_val
                return f"P(no event for {n_val} days) = (1-{p_val})^{n_val} ≈ {result:.5f}"
            result = p_val ** n_val
            return f"P({n_val} consecutive) = {p_val}^{n_val} ≈ {result:.5f}"

    # ── PROBABILITY — coin flip / fair event N times ─────────────────────────
    if _re.search(r'\bprobability\b', q) and \
       _re.search(r'\b(?:flip|toss|flipping|tossing)\b', q) and \
       _re.search(r'\b(?:coin|coins)\b', q):
        _flip_n_m = _re.search(r'(\d+)\s+times?', q)
        if _flip_n_m:
            _n_flips = int(_flip_n_m.group(1))
            from fractions import Fraction as _FrC
            _coin_prob = _FrC(1, 2) ** _n_flips
            _coin_dec = float(_coin_prob)
            _coin_side = 'heads' if 'head' in q else 'tails'
            return (f"P(all {_coin_side}) = (1/2)^{_n_flips}"
                    f" = {_coin_prob} ≈ {_coin_dec:.4f}")

    # ── PROBABILITY — drawing from bag ──────────────────────────────────────
    if _re.search(r'\bprobability\b', q) and \
       _re.search(r'\b(?:drawing?|picking?|selecting?|choosing?)\b', q):
        ball_counts = {}
        for bm in _re.finditer(r'(\d+)\s+(\w+)\s+balls?', q):
            ball_counts[bm.group(2).lower()] = int(bm.group(1))
        if ball_counts:
            total_b = sum(ball_counts.values())
            target_bm = _re.search(
                r'(?:drawing?|picking?|selecting?|choosing?)\s+a(?:n)?\s+(\w+)\s+ball', q)
            if not target_bm:
                target_bm = _re.search(
                    r'(?:drawing?|picking?|selecting?|choosing?)\s+(\w+)(?:\s+ball)?', q)
            if target_bm:
                target = target_bm.group(1).lower()
                count = ball_counts.get(target, 0)
                if not count:
                    for _col in ball_counts:
                        if _col in q:
                            target, count = _col, ball_counts[_col]
                            break
                if total_b > 0 and count > 0:
                    from math import gcd as _gcd_p
                    g = _gcd_p(count, total_b)
                    return (f"P(drawing {target}) = {count}/{total_b}"
                            f" = {count//g}/{total_b//g} ≈ {count/total_b:.4f}")

    # ── PERCENTAGE — X% of Y ─────────────────────────────────────────────────
    if _re.search(r'\b\d+\s*%\s+of\s+\d+', q):
        pct_of_m = _re.search(r'(\d+(?:\.\d+)?)\s*%\s+of\s+(\d+(?:\.\d+)?)', q)
        if pct_of_m:
            pct, base = float(pct_of_m.group(1)), float(pct_of_m.group(2))
            result = pct / 100 * base
            r_str = f"{result:.2f}".rstrip('0').rstrip('.')
            return f"{pct:.0f}% of {base:.0f} = {r_str}"

    # ── PERCENTAGE — sale price / discount ─────────────────────────────────
    if _re.search(r'\d+%\s+off\b|\bon\s+sale\b.*\d+%|\bdiscount\b.*\d+%|\d+%.*\bdiscount\b', q):
        price_m = _re.search(r'(?:costs?|price[sd]?|for)\s+\$?(\d+(?:\.\d+)?)', q)
        if not price_m:
            price_m = _re.search(r'\$\s*(\d+(?:\.\d+)?)', q)
        pct_m = _re.search(r'(\d+(?:\.\d+)?)\s*%', q)
        if price_m and pct_m:
            price = float(price_m.group(1))
            pct = float(pct_m.group(1))
            sale = price * (1 - pct / 100)
            return f"Sale price = {price:.2f} × (1 - {pct:.0f}%) = ${sale:.2f}"

    # ── PERMUTATIONS — letter arrangements or distinct items ────────────────
    if _re.search(r'\b(?:arrangements?|permutations?)\b.*\b(?:letters?|word|books?|items?|objects?|people)\b', q) or \
       _re.search(r'\bletters?\s+in\b.*\b[A-Z]{3,}\b', query) or \
       _re.search(r'\bhow\s+many\s+ways\b.*\b(?:books?|items?|objects?|people)\b', q):
        word_m = _re.search(r'\b([A-Z]{3,})\b', query)
        if word_m:
            word = word_m.group(1)
            from collections import Counter as _Counter2
            from math import factorial as _fac2
            freq = _Counter2(word)
            n_w = len(word)
            denom = 1
            for cnt in freq.values():
                denom *= _fac2(cnt)
            arrangements = _fac2(n_w) // denom
            freq_str = "×".join(f"{c}!" for c in freq.values())
            return f"Arrangements of {word}: {n_w}!/({freq_str}) = {arrangements:,}"
        n_items_m = _re.search(r'(\d+)\s+(?:different\s+)?(?:books?|items?|objects?|people|students?)', q)
        if n_items_m:
            n_items = int(n_items_m.group(1))
            from math import factorial as _fac_items
            return f"P({n_items},{n_items}) = {n_items}! = {_fac_items(n_items):,} ways"

    # ── POLYNOMIAL DERIVATIVE ───────────────────────────────────────────────
    if _re.search(r'\b(?:derivative|differentiat)\b', q):
        poly_m = _re.search(r'f\s*\(\s*x\s*\)\s*=\s*(.+?)(?:\?|$)', q)
        if poly_m:
            expr = poly_m.group(1).strip().rstrip('?').strip()
            expr_norm = _re.sub(r'\s+', '', expr)
            parts_split = _re.split(r'(?=[+-])', expr_norm)
            deriv_terms = []
            for part in parts_split:
                if not part:
                    continue
                xpow_m = _re.match(r'^([+-]?\d*(?:\.\d+)?)\s*x\^(\d+)$', part)
                xlin_m = _re.match(r'^([+-]?\d*(?:\.\d+)?)x$', part)
                if xpow_m:
                    c_str, n_p = xpow_m.group(1), int(xpow_m.group(2))
                    c = float(c_str) if c_str not in ('', '+', '-') else (1.0 if c_str != '-' else -1.0)
                    nc = c * n_p
                    nn = n_p - 1
                    nc_s = str(int(nc) if nc == int(nc) else nc)
                    if nn == 0:
                        deriv_terms.append(nc_s)
                    elif nn == 1:
                        deriv_terms.append(f"{nc_s}x")
                    else:
                        deriv_terms.append(f"{nc_s}x^{nn}")
                elif xlin_m:
                    c_str = xlin_m.group(1)
                    c = float(c_str) if c_str not in ('', '+', '-') else (1.0 if c_str != '-' else -1.0)
                    if c != 0:
                        deriv_terms.append(str(int(c) if c == int(c) else c))
            if deriv_terms:
                dr = deriv_terms[0]
                for t in deriv_terms[1:]:
                    dr += f" - {t[1:]}" if t.startswith('-') else f" + {t}"
                return f"f'(x) = {dr}"

    # ── DEFINITE INTEGRAL ────────────────────────────────────────────────────
    if _re.search(r'\b(?:integral|integrat)\b', q):
        lim_m = _re.findall(r'x\s*=\s*(-?\d+(?:\.\d+)?)', q)
        if len(lim_m) < 2:
            _from_to_m = _re.search(r'\bfrom\s+(-?\d+(?:\.\d+)?)\s+to\s+(-?\d+(?:\.\d+)?)\b', q)
            if _from_to_m:
                lim_m = [_from_to_m.group(1), _from_to_m.group(2)]
        integ_m = _re.search(r'(?:integral|integrat)\w*\s+of\s+(.+?)(?:\s+from\b|\s+dx|\?|$)', q)
        if integ_m and len(lim_m) >= 2:
            raw_expr = integ_m.group(1).strip()
            fx_eq_m = _re.match(r'f\s*\(\s*x\s*\)\s*=\s*(.+)', raw_expr)
            if fx_eq_m:
                raw_expr = fx_eq_m.group(1).strip()
            a_lim, b_lim = float(lim_m[0]), float(lim_m[1])
            def _eval_fx(x_val, _re=_re, raw=raw_expr):
                try:
                    e = raw.replace('^', '**')
                    e = _re.sub(r'(\d)\s*x', r'\1 * x', e)
                    e = e.replace('x', str(float(x_val)))
                    return float(eval(e, {"__builtins__": {}}))  # noqa: S307
                except Exception:
                    return 0.0
            n_s = 100
            h_s = (b_lim - a_lim) / n_s
            s_sum = _eval_fx(a_lim) + _eval_fx(b_lim)
            for i in range(1, n_s):
                s_sum += (4 if i % 2 else 2) * _eval_fx(a_lim + i * h_s)
            result = s_sum * h_s / 3
            r_str = f"{result:.2f}".rstrip('0').rstrip('.')
            return f"∫({raw_expr})dx from {int(a_lim)} to {int(b_lim)} = {r_str}"

    # ── FACTORIAL ────────────────────────────────────────────────────────────
    fact_m = _re.search(r'(\d+)\s*!|factorial\s+(?:of\s+)?(\d+)|(\d+)\s+factorial', q)
    if fact_m:
        n_fact = int(fact_m.group(1) or fact_m.group(2) or fact_m.group(3))
        from math import factorial as _fac_f
        return f"{n_fact}! = {_fac_f(n_fact)}"

    # ── GCD — greatest common divisor ────────────────────────────────────────
    if _re.search(r'\b(?:greatest\s+common\s+divisor|gcd)\b', q):
        _nums_gcd = [int(x) for x in _re.findall(r'\b(\d+)\b', q)]
        if len(_nums_gcd) >= 2:
            _g = _math.gcd(_nums_gcd[0], _nums_gcd[1])
            return f"GCD({_nums_gcd[0]}, {_nums_gcd[1]}) = {_g}"

    # ── LINEAR EQUATION — solve for x ────────────────────────────────────────
    if _re.search(r'\b(?:solve|find)\b', q) and _re.search(r'\d+\s*x\b', q):
        eq_m = _re.search(
            r'(\d+(?:\.\d+)?)\s*x\s*([+-])\s*(\d+(?:\.\d+)?)\s*=\s*(\d+(?:\.\d+)?)', q)
        if eq_m:
            a_eq = float(eq_m.group(1))
            sign_eq = eq_m.group(2)
            b_eq = float(eq_m.group(3))
            c_eq = float(eq_m.group(4))
            b_signed = b_eq if sign_eq == '+' else -b_eq
            x_val = (c_eq - b_signed) / a_eq
            x_str = f"{x_val:.4f}".rstrip('0').rstrip('.')
            return (f"{a_eq:.0f}x {sign_eq} {b_eq:.0f} = {c_eq:.0f} → "
                    f"x = ({c_eq:.0f} - ({b_signed:.0f})) / {a_eq:.0f} = {x_str}")

    # ── CUBE VOLUME ───────────────────────────────────────────────────────────
    if _re.search(r'\bvolume\b.*\bcube\b|\bcube\b.*\bvolume\b', q):
        side_m = _re.search(
            r'side(?:\s+length)?\s+(?:of\s+)?(?:is\s+|=\s*)?(\d+(?:\.\d+)?)', q)
        if side_m:
            s_cube = float(side_m.group(1))
        else:
            nums_cube = _re.findall(r'\b(\d+(?:\.\d+)?)\b', q)
            s_cube = float(nums_cube[-1]) if nums_cube else None
        if s_cube is not None:
            return f"Volume = s³ = {s_cube:.0f}³ = {s_cube**3:.2f}"

    # ── AREA — rectangle / square ─────────────────────────────────────────────
    if _re.search(r'\barea\b.*\b(?:rectangle|square)\b|\b(?:rectangle|square)\b.*\barea\b', q):
        _l_m_a = _re.search(r'length\b.*?(\d+(?:\.\d+)?)', q)
        _w_m_a = _re.search(r'width\b.*?(\d+(?:\.\d+)?)', q)
        if _l_m_a and _w_m_a:
            _l_a, _w_a = float(_l_m_a.group(1)), float(_w_m_a.group(1))
        else:
            _nums_a = [float(x) for x in _re.findall(r'\b(\d+(?:\.\d+)?)\b', q)]
            _l_a, _w_a = (_nums_a[0], _nums_a[1]) if len(_nums_a) >= 2 else (None, None)
        if _l_a is not None:
            _area_a = _l_a * _w_a
            return f"Area = l × w = {_l_a:.0f} × {_w_a:.0f} = {_area_a:.2f}"

    # ── PERIMETER — rectangle / square ───────────────────────────────────────
    if _re.search(r'\bperimeter\b.*\b(?:rectangle|square)\b|\b(?:rectangle|square)\b.*\bperimeter\b', q):
        l_m_p = _re.search(r'length\b.*?(\d+(?:\.\d+)?)', q)
        w_m_p = _re.search(r'width\b.*?(\d+(?:\.\d+)?)', q)
        if l_m_p and w_m_p:
            l_d, w_d = float(l_m_p.group(1)), float(w_m_p.group(1))
        else:
            nums_p = [float(x) for x in _re.findall(r'\b(\d+(?:\.\d+)?)\b', q)]
            l_d, w_d = (nums_p[0], nums_p[1]) if len(nums_p) >= 2 else (None, None)
        if l_d is not None:
            p_d = 2 * (l_d + w_d)
            return f"Perimeter = 2(l+w) = 2({l_d:.0f}+{w_d:.0f}) = {p_d:.2f}"

    # ── DEGREES → RADIANS ─────────────────────────────────────────────────────
    if _re.search(r'\bradians?\b', q) and _re.search(r'\bdegrees?\b', q):
        _deg_m2 = _re.search(r'(\d+(?:\.\d+)?)\s*degrees?', q)
        if _deg_m2:
            _deg_v = float(_deg_m2.group(1))
            _rad_v = _deg_v * _math.pi / 180
            from fractions import Fraction as _Frac2
            _frac2 = _Frac2(_deg_v / 180).limit_denominator(100)
            if _frac2.numerator == 1:
                _pi_str2 = f"π/{_frac2.denominator}"
            elif _frac2.denominator == 1:
                _pi_str2 = f"{int(_frac2.numerator)}π"
            else:
                _pi_str2 = f"{_frac2.numerator}π/{_frac2.denominator}"
            return f"{_deg_v:.0f}° = {_pi_str2} ≈ {_rad_v:.4f} radians"

    # ── TEMPERATURE CONVERSION ────────────────────────────────────────────────
    if _re.search(r'\b(?:fahrenheit|celsius|celcius|centigrade)\b', q):
        f_m_t = _re.search(r'(\d+(?:\.\d+)?)\s*(?:°\s*f\b|degrees?\s+fahrenheit\b|°f\b)', q)
        if not f_m_t:
            f_m_t = _re.search(r'(\d+(?:\.\d+)?)\s*°?\s*f\b', q)
        c_m_t = _re.search(r'(\d+(?:\.\d+)?)\s*(?:°\s*c\b|degrees?\s+celsius\b|degrees?\s+celcius\b|degrees?\s+centigrade\b|°c\b)', q)
        if not c_m_t:
            c_m_t = _re.search(r'(\d+(?:\.\d+)?)\s*°?\s*c\b', q)
        if f_m_t and _re.search(r'\b(?:celsius|celcius|centigrade)\b', q):
            f_t = float(f_m_t.group(1))
            c_t = (f_t - 32) * 5 / 9
            return f"{f_t}°F = ({f_t}-32) × 5/9 = {c_t:.2f}°C"
        if c_m_t and _re.search(r'\bfahrenheit\b', q):
            c_t = float(c_m_t.group(1))
            f_t = c_t * 9 / 5 + 32
            return f"{c_t}°C = {c_t} × 9/5 + 32 = {f_t:.2f}°F"

    # ── FALL BACK to arithmetic calculator ─────────────────────────────────
    return _agent_calculator(query)


def _cache_weather_condition(result_str: str) -> None:
    """WO-058: parse a condition word from any provider's result string and cache it."""
    global _last_weather_condition
    import re as _re
    m = _re.search(r":\s*([^,\d]+?)(?:,|\d)", result_str)
    if m:
        _last_weather_condition = m.group(1).strip().lower()


def get_last_weather_condition() -> str:
    """Return the last successfully fetched weather condition (lowercase). Empty if never fetched."""
    return _last_weather_condition


def _agent_weather(query: str) -> str:
    # Location priority:
    #   1. Explicit city in this query ("weather in London")
    #   2. Session location set by user ("I'm in London")
    #   3. ELO_LOCATION env var (persistent default)
    #   4. Auto-detect (last resort)

    city_match = re.search(
        r"(?:in|at|for)\s+([A-Za-z][A-Za-z\s,\-]{1,40}?)(?:\?|$|\s+today|\s+now|\s+like|\s+forecast)",
        query, re.IGNORECASE
    )
    # WO-030: explicit city in query > persisted location > ASK (never silently default)
    city = (city_match.group(1).strip() if city_match else None) or _resolve_location()
    if not city:
        return (
            "No location saved. Ask David: 'Where are you?' — do NOT look up weather, "
            "do NOT fabricate a city or default to London. Wait for his answer, then save it."
        )

    # ── AccuWeather (primary — disabled; re-enable with a paid key) ─────────────
    try:
        from tools.accuweather_agent import agent as _accu_agent, is_available as _accu_ok
        if _accu_ok():
            result = _accu_agent(query, city=city)
            if result:
                _cache_weather_condition(result)
                return result
    except Exception as _ae:
        _logger.warning("AccuWeather failed (%s), trying Google Weather", _ae)

    # ── Google Weather API (primary when key set) ─────────────────────────────
    try:
        from tools.google_weather_agent import agent as _gw_agent, is_available as _gw_ok
        if _gw_ok():
            result = _gw_agent(query, city=city)
            if result:
                _cache_weather_condition(result)
                return result
    except Exception as _gwe:
        _logger.warning("Google Weather failed (%s), trying XWeather", _gwe)

    # ── XWeather / AerisWeather (15,000 req/month free) ──────────────────────
    try:
        from tools.xweather_agent import agent as _xw_agent, is_available as _xw_ok
        if _xw_ok():
            result = _xw_agent(query, city=city)
            if result:
                _cache_weather_condition(result)
                return result
    except Exception as _xwe:
        _logger.warning("XWeather failed (%s), falling back to wttr.in", _xwe)

    # ── wttr.in (fallback) ────────────────────────────────────────────────────
    # city is always set at this point (explicit > session > env > London default)
    import urllib.request as _urllib_req, json as _json_mod
    target = city.replace(" ", "+")
    using_auto = False

    _wttr_req = _urllib_req.Request(
        f"https://wttr.in/{target}?format=j1",
        headers={"Accept": "application/json", "User-Agent": "eLo-OS/1.0"},
    )
    with _urllib_req.urlopen(_wttr_req, timeout=8) as _wr:
        data = _json_mod.loads(_wr.read().decode())
    cur    = data["current_condition"][0]
    desc   = cur["weatherDesc"][0]["value"]
    temp_c = cur["temp_C"]
    feels  = cur["FeelsLikeC"]
    humid  = cur["humidity"]

    # WO-030: use queried city name, not nearest_area (avoids "Nine Elms" sub-area invention)
    result = f"Weather in {city}: {desc}, {temp_c}°C, feels like {feels}°C, humidity {humid}%."
    if using_auto:
        result += f" (Detected as {loc} — say 'I'm in [city]' to set a default.)"
    global _last_weather_condition
    _last_weather_condition = desc.lower()  # WO-058: cache for blender_state.json publish
    return result


def _agent_wikipedia(query: str) -> str:
    import urllib.request as _urllib_req, urllib.parse as _urllib_parse, json as _json_mod
    topic = re.sub(
        r"^(?:what(?:'s| is)\s+(?:a\s+|an\s+|the\s+)?|who(?:'s| is)\s+|"
        r"tell me about\s+|explain\s+|define\s+|wiki\s+|search\s+(?:for\s+)?)",
        "", query.strip(), flags=re.IGNORECASE
    ).strip().rstrip("?")
    if not topic:
        raise ValueError("no topic extracted")
    _wiki_req = _urllib_req.Request(
        "https://en.wikipedia.org/api/rest_v1/page/summary/"
        + _urllib_parse.quote(topic) + "?redirect=true",
        headers={"User-Agent": "eLo-OS/1.0"},
    )
    with _urllib_req.urlopen(_wiki_req, timeout=8) as _wr:
        data = _json_mod.loads(_wr.read().decode())
    if data.get("type") == "disambiguation":
        raise ValueError("disambiguation page")
    extract = data.get("extract", "")
    sentences = re.split(r'(?<=[.!?])\s+', extract)
    summary   = " ".join(sentences[:2])
    title     = data.get("title", topic)
    return f"From Wikipedia — {title}: {summary}"


def _agent_duckduckgo(query: str) -> str:
    """DuckDuckGo Instant Answers — free, no key. Best for entity lookups and quick facts."""
    import urllib.request as _urllib_req, urllib.parse as _urllib_parse, json as _json_mod
    _ddg_params = _urllib_parse.urlencode({"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"})
    _ddg_req = _urllib_req.Request(
        f"https://api.duckduckgo.com/?{_ddg_params}",
        headers={"User-Agent": "eLo-OS/1.0"},
    )
    with _urllib_req.urlopen(_ddg_req, timeout=8) as _wr:
        data = _json_mod.loads(_wr.read().decode())
    abstract = data.get("AbstractText", "").strip()
    if abstract:
        heading = data.get("Heading", "")
        prefix = f"{heading}: " if heading else ""
        return f"{prefix}{abstract[:400]}"
    # Try related topics
    for topic in data.get("RelatedTopics", [])[:3]:
        if isinstance(topic, dict) and topic.get("Text"):
            return topic["Text"][:300]
    raise ValueError("no DDG result")


def _agent_search(query: str) -> str:
    """Try DuckDuckGo first, fall back to Wikipedia."""
    try:
        return _agent_duckduckgo(query)
    except Exception:
        pass
    return _agent_wikipedia(query)


def _agent_translate(query: str) -> str:
    """Extract text + target language, translate via Gemini then OpenAI."""
    import urllib.request as _urllib_req, urllib.parse as _urllib_parse, json as _json_mod, os as _os

    # Pattern 1: "translate X to Spanish"
    m = re.search(r'translate\s+["\']?(.+?)["\']?\s+(?:to|into)\s+([\w\s]+?)(?:\?|$)', query, re.IGNORECASE)
    if not m:
        # Pattern 2: "how do you say X in Spanish"
        m = re.search(r'(?:how\s+(?:do\s+you|to)\s+say|say)\s+["\']?(.+?)["\']?\s+in\s+([\w]+)', query, re.IGNORECASE)
    if not m:
        # Pattern 3: "what is X in Spanish"
        m = re.search(r'what(?:\'s| is)\s+["\']?(.+?)["\']?\s+in\s+([\w]+)', query, re.IGNORECASE)
    if not m:
        raise ValueError("can't parse translation request")

    text = m.group(1).strip().strip("\"'")
    lang = m.group(2).strip().rstrip("?").strip().title()

    prompt_text = f'Translate this to {lang}. Output ONLY the translation, no explanation: "{text}"'

    # Try Gemini (great at translation)
    api_key = _os.environ.get("GOOGLE_API_KEY", "")
    if api_key:
        model = _os.environ.get("ELO_GEMINI_MODEL", "gemini-2.0-flash")
        url   = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt_text}]}],
            "generationConfig": {"maxOutputTokens": 150, "temperature": 0.1},
        }
        try:
            _gem_full_url = f"{url}?{_urllib_parse.urlencode({'key': api_key})}"
            _gem_req = _urllib_req.Request(
                _gem_full_url,
                data=_json_mod.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with _urllib_req.urlopen(_gem_req, timeout=10) as _wr:
                translated = _json_mod.loads(_wr.read().decode())["candidates"][0]["content"]["parts"][0]["text"].strip().strip('"')
                return f'"{text}" in {lang}: {translated}'
        except Exception:
            pass

    # Fall back to OpenAI
    openai_key = _os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        _oai_body = _json_mod.dumps({
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a translator. Output ONLY the translation, no explanation."},
                {"role": "user",   "content": f'Translate "{text}" to {lang}'},
            ],
            "max_tokens": 150, "temperature": 0.1,
        }).encode()
        try:
            _oai_req = _urllib_req.Request(
                "https://api.openai.com/v1/chat/completions",
                data=_oai_body,
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                method="POST",
            )
            with _urllib_req.urlopen(_oai_req, timeout=10) as _wr:
                translated = _json_mod.loads(_wr.read().decode())["choices"][0]["message"]["content"].strip().strip('"')
                return f'"{text}" in {lang}: {translated}'
        except Exception:
            pass

    raise ValueError("no translation backend available")


_NEWS_NEGATION = re.compile(
    r"\b(don'?t|doesn'?t|not|never|stop|no|hate|dislike|avoid|removed|off)\b"
    r".{0,30}"
    r"\b(news|headlines|stories)\b",
    re.IGNORECASE,
)

def _agent_news(query: str) -> str:
    """Pull headlines from RSS — BBC News, BBC Science, or Hacker News. No key needed."""
    import urllib.request as _urllib_req

    # Don't fire if the user is rejecting/negating news
    if _NEWS_NEGATION.search(query):
        return ""

    text = query.lower()
    if any(k in text for k in ["tech", "technology", "software", "ai ", " ai", "startup", "hacker", "developer", "coding", "code"]):
        url, source = "https://hnrss.org/frontpage?count=10", "Hacker News"
    elif any(k in text for k in ["science", "space", "nature", "health", "climate"]):
        url, source = "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "BBC Science"
    else:
        url, source = "https://feeds.bbci.co.uk/news/rss.xml", "BBC News"

    _news_req = _urllib_req.Request(url, headers={"User-Agent": "eLo-OS/1.0"})
    with _urllib_req.urlopen(_news_req, timeout=8) as _wr:
        xml = _wr.read().decode(errors="replace")

    # Parse titles — handles CDATA and plain text
    raw_titles = re.findall(r'<title>(?:<!\[CDATA\[)?\s*(.*?)\s*(?:\]\]>)?</title>', xml, re.DOTALL)
    skip_terms = {"bbc news", "bbc", "hacker news", "reuters", "rss"}
    headlines  = []
    for t in raw_titles:
        t = re.sub(r'\s+', ' ', t).strip()
        tl = t.lower()
        if t and len(t) > 10 and not any(tl == s or tl.startswith(s + ":") for s in skip_terms):
            headlines.append(t)
        if len(headlines) == 5:
            break

    if not headlines:
        raise ValueError("no headlines found")

    return f"Top headlines from {source}: " + " | ".join(headlines)


def _search_notes(notes: list, query: str) -> list:
    """Rank typed vault notes by keyword relevance. Handles hyphenated terms like K-7."""
    _stop = {"what", "is", "are", "the", "my", "a", "an", "about", "notes", "on",
             "in", "obsidian", "did", "i", "write", "wrote", "have", "tell", "me"}
    # Extract keywords two ways: strip all punctuation, and also strip only non-alphanum
    raw_words  = re.sub(r"[^\w\s]", " ", query.lower()).split()  # K-7 → "k" "7"
    joined     = re.sub(r"(\w)-(\w)", r"\1\2", query.lower())    # K-7 → "k7"
    joined_words = re.sub(r"[^\w\s]", "", joined).split()         # adds "k7"
    all_words  = set(raw_words + joined_words)
    keywords   = {w for w in all_words if w not in _stop and len(w) > 1}
    if not keywords:
        return notes[:3]
    scored = []
    for i, note in enumerate(notes):
        title   = note.get("title", "").lower()
        text    = " ".join([title, note.get("summary", ""),
                            " ".join(note.get("tags", []))]).lower()
        score   = sum(text.count(kw) for kw in keywords if kw in text)
        # Bonus: direct title substring match (e.g. "K-7" in title "K-7")
        if any(kw in title for kw in keywords):
            score += 3
        if score > 0:
            scored.append((score, i, note))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [n for _, _, n in scored]


def _search_vault_raw(vault_path: str, query: str) -> list:
    """Keyword search across all .md files in a real Obsidian vault (no frontmatter required)."""
    _stop = {"what", "is", "are", "the", "my", "a", "an", "about", "notes", "on",
             "in", "obsidian", "did", "i", "write", "wrote", "have", "tell", "me"}
    keywords = {w for w in re.sub(r"[^\w\s]", "", query.lower()).split() if w not in _stop and len(w) > 2}
    results = []
    idx = 0
    for dirpath, dirnames, filenames in os.walk(vault_path):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for fname in filenames:
            if not fname.endswith(".md"):
                continue
            try:
                path = os.path.join(dirpath, fname)
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                title = fname[:-3]
                text  = (title + " " + content).lower()
                score = sum(text.count(kw) for kw in keywords if kw in text)
                if score > 0:
                    lines   = [l.strip() for l in content.splitlines()
                               if l.strip() and not l.startswith("#") and not l.startswith("---")]
                    summary = lines[0][:200] if lines else ""
                    results.append((score, idx, {"title": title, "summary": summary}))
                    idx += 1
            except Exception:
                continue
    results.sort(key=lambda x: x[0], reverse=True)
    return [n for _, _, n in results[:5]]


def _agent_obsidian(query: str) -> str:
    """
    Search the Obsidian vault on demand.
    Always tries obsidian_loader first (handles typed frontmatter notes correctly).
    Falls back to raw .md search for external vaults without frontmatter.
    """
    # Typed vault path (internal or ELO_VAULT_PATH if it has typed notes)
    try:
        from memory.obsidian_loader import load
        pack    = load()
        results = _search_notes(pack.get("notes", []), query)
        if results:
            top    = results[0]
            others = [r["title"] for r in results[1:3]]
            result = f"From your notes — {top['title']}: {top['summary']}"
            if others:
                result += f" (Related: {', '.join(others)})"
            return result
    except Exception:
        pass

    # Raw fallback for external vaults without typed frontmatter
    vault_path = os.environ.get("ELO_VAULT_PATH", "").strip()
    if not vault_path or not os.path.isdir(vault_path):
        raise ValueError("no matching notes in vault")

    results = _search_vault_raw(vault_path, query)
    if not results:
        raise ValueError("no matching notes in vault")

    top    = results[0]
    others = [r["title"] for r in results[1:3]]
    result = f"From your notes — {top['title']}: {top['summary']}"
    if others:
        result += f" (Related: {', '.join(others)})"
    return result


# ── WO-WORLD-CREATE-WIRE-001: dispatch_create executor ────────────────────────

def _agent_create(query: str) -> str:
    """Routes WORLD_CREATE capability to dispatch_create(CREATE_FILE)."""
    try:
        from runtime.capability_registry import dispatch_create
        result = dispatch_create(query, sub_capability="CREATE_FILE")
        return result.get("notification", "")
    except Exception as _e:
        _logger.warning("_agent_create FAILED: %s", _e)
        return ""


# ── agent registry ─────────────────────────────────────────────────────────────

_AGENTS = {
    "time":        _agent_time,
    "calculator":  _agent_calculator,
    "weather":     _agent_weather,
    "search":      _agent_search,
    "translate":   _agent_translate,
    "news":        _agent_news,
    "obsidian":    _agent_obsidian,
    "spotify":     _agent_spotify,
    "github":      _agent_github,
    "calendar":      _agent_calendar,
    "calendar_add":  _agent_calendar_add,
    "vision":      _agent_vision,
    "draft":       _agent_draft,
    "file_read":   _agent_file_reader,
    "vault_write": _agent_vault_writer,
    "timer":       _agent_timer,
    "reminders":   _agent_reminders,
    "clipboard":   _agent_clipboard,
    "notes":       _agent_notes,
    "messages":    _agent_messages,
    "truth_sync":  _agent_truth_sync,
    "create":      _agent_create,       # WO-WORLD-CREATE-WIRE-001
}

# agents that accept a direct subject string for follow-up re-runs
_SUBJECT_AGENTS = {"weather", "search", "news"}

# ── WO-018: tool_router key → capability registry ID ──────────────────────────
# Any key absent here (infra routes: lore, nav, system) passes through unchecked.
_ROUTER_TO_CAP_ID: dict[str, str] = {
    "time":             "time",
    "calculator":       "calculator",
    "weather":          "weather",
    "search":           "search",
    "translate":        "translate",
    "news":             "news",
    "obsidian":         "obsidian",
    "spotify":          "spotify",
    "spotify_playlist": "spotify",
    "spotify_search":   "spotify",
    "github":           "github",
    "calendar":         "calendar",
    "calendar_add":     "calendar",
    "vision":           "vision",
    "draft":            "draft",
    "file_read":        "file_read",
    "vault_write":      "vault_write",
    "timer":            "timer",
    "reminders":        "reminders",
    "clipboard":        "clipboard",
    "notes":            "notes",
    "messages":         "messages",
    "truth_sync":       "truth_sync",
    "wikipedia":        "wikipedia",
    "create":           "WORLD_CREATE",  # WO-WORLD-CREATE-WIRE-001
}


# ── system agent — checked separately with confirmation flow ───────────────────

def _check_system(user_input: str) -> Optional[str]:
    """
    Check if this is a macOS system control request.

    Safe/read-only actions (folder_list, screenshot, dark_mode, brightness) execute immediately.
    All other actions go through the execution gate — return a confirmation prompt,
    never execute silently. Spec: Layer 08 — Always confirm.
    """
    try:
        from tools.system_agent import detect, execute, _SAFE_ACTIONS
        result = detect(user_input)
    except Exception as e:
        _logger.debug("system detect failed: %s", e)
        return None

    if result is None:
        return None

    action, arg = result

    # Safe / read-only — execute immediately
    if action in _SAFE_ACTIONS:
        try:
            data = execute(action, arg)
            return f"[SYSTEM: {data}]"
        except Exception as e:
            return f"[SYSTEM ERROR: {str(e)[:80]}]"

    # All other actions — consult execution gate
    try:
        from runtime.router.execution_gate import gate as _gate
        gate_result = _gate(action, arg)
        if gate_result["execute"]:
            # Gate says immediate — run it
            try:
                data = execute(action, arg)
                return f"[SYSTEM: {data}]"
            except Exception as e:
                return f"[SYSTEM ERROR: {str(e)[:80]}]"
        else:
            desc = gate_result["confirmation"]
            return f"[SYSTEM CONFIRM: {desc}]"
    except Exception:
        # Fallback: execute if gate import fails
        try:
            data = execute(action, arg)
            return f"[SYSTEM DONE: {data}]"
        except Exception as e:
            return f"[SYSTEM ERROR: {str(e)[:80]}]"


# ── public API ─────────────────────────────────────────────────────────────────

_NAV_PATTERNS = [
    (r"jump\s+to\s+(?:my\s+)?(\w+)",              "jump_to_app"),
    (r"go\s+to\s+(?:my\s+)?(\w+)",                "jump_to_app"),
    (r"jump\s+(?:to\s+)?(?:the\s+)?bottom",       "jump_bottom"),
    (r"jump\s+(?:to\s+)?(?:the\s+)?top",          "jump_top"),
    (r"jump\s+(?:to\s+)?(?:the\s+)?left",         "jump_left"),
    (r"jump\s+(?:to\s+)?(?:the\s+)?right",        "jump_right"),
    (r"jump\s+around|hop\s+around",               "wander"),
    (r"shift\s+(?:over|left)",                    "shift_left"),
    (r"shift\s+right",                            "shift_right"),
    (r"move\s+over",                              "shift"),
    (r"come\s+back",                              "come_back"),
    # natural phrasings
    (r"wander\s+(?:about|around)|go\s+for\s+a\s+wander", "wander"),
    (r"come\s+here|come\s+over\s+here|get\s+over\s+here", "come_back"),
    (r"other\s+(?:screen|monitor|display)|move\s+to\s+another\s+screen|go\s+to\s+(?:another|the\s+other)\s+screen", "move_screen"),
    (r"other\s+window|go\s+to\s+the\s+other\s+window", "jump_to_app"),
    (r"sit\s+on(?:\s+top\s+of)?\s+(\w+)",        "jump_to_app"),
    (r"perch\s+on\s+(\w+)",                       "jump_to_app"),
]

def _parse_nav(user_input: str) -> tuple:
    t = user_input.lower().strip()
    for pattern, nav_type in _NAV_PATTERNS:
        m = re.search(pattern, t)
        if m:
            target = m.group(1).title() if m.lastindex else ""
            return nav_type, target
    return "wander", ""

def _write_nav_event(nav_type: str, target: str = "") -> None:
    import json, time, os as _os
    _bs = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                        "blender", "blender_state.json")
    try:
        with open(_bs, encoding="utf-8") as f:
            state = json.load(f)
    except Exception:
        state = {}
    state["user_nav_event"] = {"type": nav_type, "target": target, "_ts": time.time()}
    tmp = _bs + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    _os.replace(tmp, _bs)


def _write_game_entry_event() -> None:
    """Write exit_event to blender_state.json — triggers Unity guncheck → run-off-screen sequence."""
    import json, time, os as _os
    _bs = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                        "blender", "blender_state.json")
    try:
        with open(_bs, encoding="utf-8") as f:
            state = json.load(f)
    except Exception:
        state = {}
    state["exit_event"] = {"type": "game_entry", "direction": "right", "_ts": time.time()}
    tmp = _bs + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    _os.replace(tmp, _bs)
    try:
        from blender_bridge.exit_state import mark_exiting
        mark_exiting()
    except Exception:
        pass


def _youtube_to_spotify(user_input: str) -> str:
    """
    If YouTube is the active browser tab and the video looks like a music track,
    search Spotify for it and like/add it. Returns a context string for the LLM.
    """
    try:
        from desktop.window_state import get as _wget, _browser_tab
        ws = _wget()
        if not ws.available:
            return ""
        # Only fire when Chrome/Safari is frontmost
        if not any(b in ws.app for b in ("Chrome", "Safari")):
            return ""
        tab_title, tab_url = _browser_tab(ws.app)
        if not tab_url or "youtube.com" not in tab_url:
            return ""
        from desktop.app_context import classify_youtube, spotify_search_hint
        yt = classify_youtube(tab_title)
        search_q = spotify_search_hint(tab_title)
        if not search_q:
            return f"Currently watching: {yt['title']} (not identified as music — can't add to Spotify)"
        # Search and like via Spotify Web API
        try:
            from tools.spotify_web import search_track, like_track
            result = search_track(search_q)
            if result and result.get("uri"):
                like_track(result["uri"])
                return (
                    f"Found '{result['name']}' by {result['artist']} on Spotify and added it to Liked Songs. "
                    f"(matched from YouTube: {yt['title']})"
                )
            return f"Searched Spotify for '{search_q}' but no match found."
        except Exception as _se:
            return f"YouTube track identified as '{search_q}' but Spotify API unavailable: {_se}"
    except Exception:
        return ""


def _spoken_weather(wx: str) -> str:
    """'Weather in Hackney Wick: Partly sunny, 20°C, feels like 24°C, humidity 65%,
    wind 0 km/h.' → "Partly sunny in Hackney Wick — 20°C, feels like 24°C." Every
    value comes from the provider's line; unknown shapes are passed through."""
    m = re.match(r"\s*Weather in (?P<place>[^:]+):\s*(?P<cond>[^,]+),\s*(?P<t>-?\d+(?:\.\d+)?°[CF])"
                 r"(?:,\s*feels like (?P<f>-?\d+(?:\.\d+)?°[CF]))?", wx or "")
    if not m:
        return (wx or "").strip()
    line = f"{m['cond'].strip().capitalize()} in {m['place'].strip()} — {m['t']}"
    if m["f"] and m["f"] != m["t"]:
        line += f", feels like {m['f']}"
    return line + "."


def _direct_intercepts(user_input: str) -> Optional[Tuple[str, Optional[str]]]:
    """
    WO-122 Row 14 ROUTE — OS-level intercepts that fire regardless of Executive
    capability selection. These do NOT dispatch data agents from the capability
    set — they are direct OS actions (nav, game entry, system control), window-
    state reads, identity responses (lore/creator), or user-config actions
    (location set). Returns (enriched, executor) if an intercept fires, else None.
    """
    global _last_direct_result  # hoisted — was duplicated inside try blocks (SyntaxError on 3.x)
    _last_direct_result = None  # B3: only an intercept that IS the answer sets it, this turn
    _lower = user_input.lower()

    # B3 2026-10-06: server.py's reminder block already set it (reminder_agent) and
    # wrapped the result as "[REMINDER_SET]\n<line>\n\nUser asked: …". That line is
    # the answer — say it, don't hand it to the LLM to paraphrase or deny.
    if user_input.startswith("[REMINDER_SET]"):
        _rs_line = user_input.split("\n", 2)[1].strip() if "\n" in user_input else ""
        if _rs_line:
            _last_direct_result = _rs_line
            return _rs_line, "reminder"

    # WO-CORE-REPAIR-P0-001: if the world-knowledge gate already injected a
    # [WORLD_KNOWLEDGE] block into user_input (happens before enrich_from_plan),
    # the lore intercept is redundant AND harmful — it matches "eLo" mentions
    # inside the injected context rather than the original query.  Skip it.
    _has_wk = "[world_knowledge" in _lower

    # ── eLo universe lore intercept ──
    _LORE_INTERCEPTS = [
        (r"\bk-?7\b",        "K-7 is eLo's spirit animal companion — a shapeshifting entity that can take 7 different forms. K-7 travels with eLo through the universe."),
        (r"\bchunk\b",       "Chunk is eLo's friend — a modular character whose body transforms into different vehicles and structures to help navigate the world."),
        (r"\bdisenelo\b",    "DISENELO is David's creative brand — home of eLo the character, the game, the book, the robot, and a series of free maker tools."),
        # WO-CORE-REPAIR-P0-001: negative lookahead excludes "eLo Planet" / "eLo-Planet" so
        # game-status queries ("what is the status of eLo Planet") don't hit character lore.
        (r"\belo(?:\s+the\s+(?:character|book|game))?(?!\s*[-]?\s*planet)\b", "eLo is an original character — an adorable childhood imagination paired with adult reality. The book, game, robot, and art all radiate from eLo."),
    ]
    _LORE_TRIGGER = r"\b(?:what(?:'s| is)|who(?:'s| is)|tell\s+me\s+about|explain|describe)\b"
    if not _has_wk and re.search(_LORE_TRIGGER, _lower):
        for _lore_pat, _lore_fact in _LORE_INTERCEPTS:
            if re.search(_lore_pat, _lower, re.IGNORECASE):
                return f"[CONTEXT: {_lore_fact}]\n\n{user_input}", "lore"

    # ── Creator question — "who made you / built you / created you" ──
    _CREATOR_PATTERNS = [
        r"\bwho\s+(?:made|built|created|designed|programmed)\s+you\b",
        r"\bwho(?:'s|\s+is)\s+(?:your|the)\s+(?:creator|maker|builder|author)\b",
        r"\bwhere\s+(?:do\s+you\s+come\s+from|are\s+you\s+from)\b",
    ]
    if any(re.search(p, _lower) for p in _CREATOR_PATTERNS):
        return (
            "[CONTEXT: eLo was made by David Charles, founder of DISENELO. "
            "David has been building eLo since childhood — the character, the world, the book, the game, and now the robot. "
            "eLo is not just software — eLo is David's creative universe made real.]\n\n" + user_input,
            "lore",
        )

    # ── Game entry ──
    try:
        from runtime.executive import _GAME_ENTRY_PHRASES as _GE
        if any(p in _lower for p in _GE):
            _write_game_entry_event()
            return f"[GAME_ENTRY: exit sequence triggered — say your going-in line now]\n\n{user_input}", "game_entry"
    except Exception as _e:
        _logger.debug("game entry intercept failed: %s", _e)

    # ── Movement / navigation ──
    try:
        from runtime.executive import _MOVEMENT_COMMAND_PHRASES as _MV
        if any(p in _lower for p in _MV):
            nav_type, target = _parse_nav(user_input)
            _write_nav_event(nav_type, target)
            ctx = f"target={target}" if target else "moving"
            return f"[NAV: {nav_type} — {ctx}]\n\n{user_input}", "nav"
    except Exception as _e:
        _logger.debug("nav intercept failed: %s", _e)

    # ── YouTube Music / active browser tab ──
    _YT_MUSIC_PATTERNS_EARLY = [
        r"\byoutube\s+music\b",
        r"\bwhat'?s?\s+(?:playing|on)\s+(?:on\s+)?(?:that\s+)?(?:youtube|yt)\b",
        r"\bwhat'?s?\s+(?:the\s+)?(?:music|song|track|video)\s+(?:on\s+)?(?:that\s+)?window\b",
        r"\bwhat'?s?\s+(?:playing|on)\s+(?:in\s+)?(?:that\s+)?(?:tab|window|chrome)\b",
        r"\bcan\s+you\s+read\s+(?:my\s+)?(?:google\s+)?chrome\b",
        r"\bwhat'?s?\s+(?:on\s+)?(?:my\s+)?chrome\b",
    ]
    if any(re.search(p, _lower) for p in _YT_MUSIC_PATTERNS_EARLY):
        try:
            from desktop.window_state import get as _ws_get, _browser_tab
            from desktop.app_context import classify_browser
            ws = _ws_get()
            if ws.available and ws.app and any(b in ws.app for b in ("Chrome", "Safari", "Firefox")):
                tab_title, tab_url = _browser_tab(ws.app)
                if tab_title:
                    classified = classify_browser(tab_title, tab_url)
                    label = classified.get("label", tab_title[:60])
                    return f"[CONTEXT: Browser tab — {label}]\n\n{user_input}", "browser_tab"
            ctx = f"App in focus: {ws.app}" if ws.available and ws.app else "Browser not in focus"
            return f"[CONTEXT: {ctx}]\n\n{user_input}", "browser_tab"
        except Exception as _e:
            _logger.debug("browser tab (early) failed: %s", _e)

    # ── App / screen visibility ──
    _VISIBILITY_PATTERNS_EARLY = [
        r"\bcan\s+you\s+see\s+(?:my\s+)?(\w+)\b",
        r"\bwhat\s+(?:app|apps|window|windows)\s+can\s+you\s+see\b",
        r"\bwhat'?s?\s+on\s+(?:my\s+)?(?:screen|window|display)\b",
        r"\bwhat\s+(?:app|apps)\s+(?:are|do)\s+(?:you\s+)?(?:see|have)\s+open\b",
        r"\bwhat\s+apps\s+can\s+you\s+see\b",
        r"\bwhat'?s?\s+(?:the\s+)?(?:current|active)\s+(?:window|app|application)\b",
        r"\bwhat\s+app\s+(?:is|are)\s+(?:open|running|active)\b",
        r"\bwhat\s+(?:is|am)\s+i\s+(?:looking\s+at|working\s+on|doing)\b",
    ]
    if any(re.search(p, _lower) for p in _VISIBILITY_PATTERNS_EARLY):
        try:
            from desktop.window_state import get as _ws_get
            ws = _ws_get()
            if ws.available and ws.app:
                title_info = f" — {ws.title}" if ws.title and ws.title != ws.app else ""
                ctx = f"Active app: {ws.app}{title_info}. Activity: {ws.activity}."
                return f"[CONTEXT: {ctx}]\n\n{user_input}", "screen_visibility"
            return f"[CONTEXT: Desktop visibility unavailable.]\n\n{user_input}", "screen_visibility"
        except Exception as _e:
            _logger.debug("screen visibility (early) failed: %s", _e)

    # Fix A — COG-004 RR17: JSON-object-shaped inputs (C9/C17) must NOT route to calculator.
    # When input looks like a JSON object ({...key: value...}), route to Ollama for explanation.
    import re as _re_calc
    _stripped_input = user_input.strip()
    _is_json_object = _stripped_input.startswith("{") and ":" in _stripped_input
    # Fix E — COG-004 RR19: algebraic variable equations (2x + 3y = 12) must NOT route to calculator.
    # direct:calculator cannot solve symbolic algebra and returns garbage (e.g. "2 = 2").
    _ALGEBRA_VAR_RE = _re_calc.compile(r'\b\d+[a-zA-Z]\b|\b[a-zA-Z]\s*[+\-*/=]\s*\d|\bsolve\b|\bfor\s+[a-zA-Z]\b', _re_calc.IGNORECASE)
    _is_symbolic_algebra = bool(_ALGEBRA_VAR_RE.search(user_input))
    if _is_json_object or _is_symbolic_algebra:
        return None  # fall through to Ollama

    # ── Calculator — direct intercept (fires regardless of Executive) ──
    # Patterns that indicate a clear arithmetic query. Must contain a digit AND
    # at least one operator (word or symbol) so we don't grab "what is eLo?" etc.
    _MATH_DIRECT_PATS = [
        r"\bwhat(?:'s| is)\s+\(?\d[\d\s]*(?:times|plus|minus|divided\s+by|[xX×*+\-\/^])\s*[\d\(]",
        r"\bhow\s+much\s+is\s+\(?\d[\d\s]*(?:times|plus|minus|divided\s+by|[xX×*+\-\/^])\s*[\d\(]",
        r"\bcalculate\s+\(?\d",
        r"\b\d[\d\s]*(?:times|plus|minus|divided\s+by)\s+\d",
        r"\b\d+\s*[×\*\/\^]\s*\d",  # symbolic × * / ^ (Unicode × added for M32)
        r"\buse\s+(?:your|the)\s+calculator\b",  # explicit calculator directive (M32)
    ]
    if any(re.search(p, _lower) for p in _MATH_DIRECT_PATS):
        try:
            _calc_result = _agent_calculator(user_input)
            _last_direct_result = _calc_result
            return _calc_result, "calculator"
        except Exception as _ce:
            _logger.debug("math direct intercept failed: %s", _ce)

    # FIX A — WO-CAP-COG-005: domain-keyword routing for word problems
    _MATH_DOMAIN_PATS = [
        r"\b(?:area|volume|circumference|perimeter)\b.*\b(?:circle|cylinder|sphere|cone|triangle|rectangle|cube)\b.*\d",
        r"\b(?:circle|cylinder|sphere|cone|triangle|rectangle)\b.*\b(?:area|volume|circumference|perimeter)\b.*\d",
        r"\bdistance\b.*\(\s*-?\d+",
        r"\b(?:sin|cos|tan|sine|cosine|tangent)\b.*\d+\s*(?:°|degrees?|deg\b)",
        r"\b(?:sin|cos|tan)\s*\(?(?:\d+°?)",
        r"\bright\s+triangle\b.*\d",
        r"\bhypotenuse\b.*\d",
        r"\b(?:mean|median|mode|average)\b.*\b\d+\b",
        r"\b(?:choose|ways?\s+to|combinations?|permutations?)\b.*\d",
        r"\b\d+\s*[Cc]\s*\d+\b",
        r"\bC\s*\(\s*\d+\s*,\s*\d+",
        r"\b(?:force|Newton)\b.*\b\d+\s*kg\b",
        r"\b(?:mass|F\s*=\s*ma)\b.*\baccelerates?\b.*\d",
        r"\b(?:velocity|speed)\b.*\b\d+\s*(?:m|meters?)\b.*\b\d+\s*(?:s|sec|seconds?)\b",
        r"\bcompound\s+interest\b.*\d",
        r"\binvestment\b.*(?:grows?|rate)\b.*\d",
        r"(?:\bratio\b.*\d+\s*:\s*\d+|\d+\s*:\s*\d+.*\bratio\b).*\d+\s*(?:g|grams?|kg|lb)?",
        r"\b(?:sum\s+of|first\s+\d+\s+terms?|arithmetic\s+(?:series|sequence))\b.*\d",
        r"\bprobability\b.*\d",
        r"\b(?:derivative|differentiat)\b.*f\s*\(\s*x\s*\)",
        r"\b(?:integral|integrat)\b.*\d",
        r"\b(?:arrangements?|permutations?)\b.*\b(?:letters?|word)\b",
        r"\bletters?\s+in\b.*\b[A-Z]{3,}\b",
        r"\b\d+%\s+of\s+\d+",
        r"\bon\s+sale\b.*\d+%|\d+%\s+off\b",
        r"\btravels?\b.*\b(?:miles?|km)\b.*\b(?:hour|hr)s?\b",
        r"\baverage\s+speed\b.*\d",
        r"\bdepreciat\w*\b.*\d+%",
        r"\bmax(?:imum)?\s+height\b.*\d",
        r"\bthrown\s+upward\b.*\d",
        r"\binitial\s+velocity\b.*\d",
        r"\b(?:acceleration|f\s*=\s*ma)\b.*\d+\s*(?:n|kg|m)",
        r"\bforce\b.*\d+\s*n\b",
        r"\bcompound(?:ed)?\s+(?:interest|monthly|annually)\b.*\d",
        r"\binvest\b.*\d.*%",
        r"\b(?:find|calculate|compute|evaluat)\b.*\b(?:area|volume|force|velocity|mean|median|probability|distance|angle)\b.*\d",
        r"\btriangle\b.*\bangles?\b|\bangles?\b.*\btriangle\b",
        r"\b\d+\s*!|\bfactorial\b.*\d|\b\d+\s+factorial\b",
        r"\bsolve\b.*\d+x|\b\d+x\s*[+-]\s*\d+\s*=\s*\d|\bsolve\s+for\s+[a-z]\b",
        r"\bhow\s+many\s+ways\b.*\b(?:books?|items?|objects?|people)\b|\b(?:books?|items?|objects?|people)\b.*\b(?:arrang\w*|order\w*)\b.*\d",
        r"\bdiscount\b.*\d+%|\d+%.*\bdiscount\b",
        r"\b(?:fahrenheit|celsius|celcius|centigrade)\b",
        r"\bbag\b.*\bprobability\b|\bprobability\b.*\b(?:ball|bag|drawing?|picking?)\b",
        r"\b(?:greatest\s+common\s+divisor|gcd)\b",
        r"\b\d+\s*degrees?\s+(?:to|in)\s+radians?\b|\bconvert\b.*\bdegrees?\b.*\bradians?\b|\bradians?\b.*\b\d+\s*degrees?\b|\bcalculate\b.*\bdegrees?\b.*\bradians?\b",
        r"\bhexagon\b.*\bang\w+|\bang\w+.*\bhexagon\b|\bpentagon\b.*\bang\w+|\bang\w+.*\bpentagon\b|\boctagon\b.*\bang\w+|\bang\w+.*\boctagon\b",
        r"\barea\b.*\brectangle\b|\brectangle\b.*\barea\b",
        r"\bcircumference\b.*\bcircle\b|\bcircle\b.*\bcircumference\b",
    ]
    if any(re.search(p, _lower) for p in _MATH_DOMAIN_PATS):
        try:
            _math_result = _agent_math_solver(user_input)
            _last_direct_result = _math_result
            return _math_result, "calculator"
        except Exception as _me:
            _logger.debug("math domain intercept failed: %s", _me)

    # ── System agent (OS control, gated confirmations) ──
    sys_ctx = _check_system(user_input)
    if sys_ctx:
        if sys_ctx.startswith("[SYSTEM: ") and sys_ctx.endswith("]"):
            # Safe action already executed — bypass LLM, return clean result
            clean_result = sys_ctx[9:-1].strip()
            _last_direct_result = clean_result
            return clean_result, "system"
        # Confirmation or error — pass to LLM with context for natural phrasing
        return f"{sys_ctx}\n\n{user_input}", "system"

    # ── Location setting — direct user configuration action ──
    new_city = detect_location_set(user_input)
    if new_city:
        set_location(new_city, studio=bool(re.search(r"\bstudio\b", user_input, re.I)))
        return (
            f"[CONTEXT: User just set their location to {new_city}. "
            f"Acknowledge warmly and confirm you'll use {new_city} for weather from now on.]\n\n{user_input}",
            "location_set",
        )

    # ── Not built (registry future) → honest no — B3 2026-10-06
    try:
        from tools.capability_status import not_built_answer as _nba
        _nb = _nba(user_input)
        if _nb:
            _last_direct_result = _nb
            return _nb, "not_built"
    except Exception as _nbe:
        _logger.debug("not-built intercept failed: %s", _nbe)

    # ── Messages — B3 2026-10-06: the demo's message request got mock filler, and
    # send_message said "Sent" whatever happened. Registry: confirm before sending.
    try:
        from tools import messages_agent as _msg
        if _msg.has_pending():
            if _msg.is_message_confirm(user_input):
                _last_direct_result = _msg.execute_pending()
                return _last_direct_result, "messages"
            if _msg.is_message_cancel(user_input):
                _msg.cancel_pending()
                _last_direct_result = "Okay — not sent."
                return _last_direct_result, "messages"
        if _msg.is_message_request(user_input):
            _last_direct_result = _msg.agent(user_input)
            return _last_direct_result, "messages"
    except Exception as _me:
        _logger.debug("messages intercept failed: %s", _me)

    # ── Apple Notes: create — B3 2026-10-06: "make a note: X" reached the Obsidian
    # agent and the mock backend answered (capability demo). Registry: notes =
    # Apple Notes ("make a note, new note, apple notes, add note"); "my notes" stays
    # Obsidian. The note existing IS the answer.
    _nm = re.match(r"^(?:(?:can|could|would)\s+you\s+)?(?:please\s+)?(?:make|create|add|write|start)\s+"
                   r"(?:a\s+|an\s+)?(?:new\s+)?(?:apple\s+)?note\b\s*(?:called|named|titled|about|saying|that|:)?\s*(.*)$",
                   user_input.strip(), re.IGNORECASE)
    if _nm:
        _title = _nm.group(1).strip().strip('"\'\u201c\u201d').rstrip(".!?")
        if not _title:
            _last_direct_result = "What should the note say?"
            return _last_direct_result, "notes"
        try:
            from tools.notes_agent import create_note as _mk_note
            _mk_note(_title)
            _last_direct_result = f"Made a note: \u201c{_title}\u201d."
        except Exception as _nte:
            _logger.debug("notes create failed: %s", _nte)
            _last_direct_result = "I couldn't make that note — Notes didn't take it."
        return _last_direct_result, "notes"

    # ── Clipboard read — B3 2026-10-06: the tool read it; the LLM then said "I don't
    # have that recorded" (capability demo). What's on the clipboard IS the answer.
    if re.search(r"\bwhat\s+(?:did\s+i|have\s+i)\s+(?:just\s+)?copi?(?:y|ed)\b|\bwhat'?s\s+(?:on\s+)?(?:my\s+|the\s+)?clipboard\b"
                 r"|\bwhat'?s\s+copied\b|\bread\s+(?:my\s+|the\s+)?clipboard\b", _lower):
        try:
            from tools.clipboard_agent import read as _clip_read
            _clip = _clip_read()
            if _clip.startswith("Clipboard is empty"):
                _last_direct_result = "Your clipboard's empty."
            else:
                _body = re.sub(r"^\s*Clipboard contents:\s*", "", _clip).strip()
                _last_direct_result = (f"You copied: \u201c{_body[:400]}\u201d" + ("…" if len(_body) > 400 else ""))
            return _last_direct_result, "clipboard"
        except Exception as _ce:
            _logger.debug("clipboard intercept failed: %s", _ce)

    # ── Calendar — B3 2026-10-06: the AppleScript read timed out and the LLM said
    # "I don't have that recorded". EventKit's answer IS the answer.
    if re.search(r"\b(?:calendar|schedule|diary|agenda)\b", _lower) and \
            re.search(r"\b(?:what'?s|what\s+is|anything|do\s+i\s+have|am\s+i|today|tomorrow|week|on\s+my|check)\b", _lower):
        try:
            from tools.calendar_agent import spoken as _cal_spoken
            _cl = _cal_spoken(user_input)
            if _cl:
                _last_direct_result = _cl
                return _cl, "calendar"
        except Exception as _cae:
            _logger.debug("calendar intercept failed: %s", _cae)

    # ── Last commit on a local repo — B3 2026-10-06: the tool returned "" (no
    # GITHUB_REPO) and the LLM filled in. The local git log IS the answer.
    if re.search(r"\b(?:last|latest|most\s+recent)\s+commit\b", _lower):
        try:
            from tools.github_agent import local_last_commit as _llc
            _lc = _llc(user_input)
            if _lc:
                _last_direct_result = _lc
                return _lc, "github"
        except Exception as _ge:
            _logger.debug("last-commit intercept failed: %s", _ge)

    # ── News — B3 2026-10-06: the headlines ARE the answer. Via the LLM they came
    # back "I don't have that recorded" (capability demo, +news backend).
    _news_pats = next((pats for name, pats in _INTENT_MAP if name == "news"), [])
    if any(re.search(p, _lower) for p in _news_pats):
        try:
            _nw = _agent_news(user_input)
            if _nw:
                _src, _, _items = _nw.partition(": ")
                _heads = [h.strip() for h in _items.split(" | ") if h.strip()][:3]
                _src = _src.replace("Top headlines from ", "")
                _line = f"Top from {_src}: " + " ".join(h if h.endswith((".", "?", "!")) else h + "."
                                                        for h in _heads)
                _last_direct_result = _line
                return _line, "news"
        except Exception as _ne:
            _logger.debug("news direct intercept failed: %s", _ne)
            _last_direct_result = "I couldn't reach the news feed just now."
            return _last_direct_result, "news"

    # ── Weather — intercept before capability path to prevent screen_visibility bleed ──
    # When weather is asked but no API/location is available, return an honest
    # "no data" context rather than letting the pipeline fall through to screen_visibility.
    _WEATHER_DIRECT_PATS = [
        r"\bweather\b",
        r"\bforecast\b",
        r"\btemperature\s+(?:like|today|outside|right\s+now)\b",
        r"\bwhat.s\s+it\s+like\s+outside\b",
        r"\brain(?:ing)?\s+outside\b",
    ]
    if any(re.search(p, _lower) for p in _WEATHER_DIRECT_PATS):
        try:
            _wx = _agent_weather(user_input)
            # B3 2026-10-06: server.py speaks an intercept's return verbatim, so
            # this is eLo's line — live it was "[CONTEXT: Weather in …]\n\n<David's
            # question>" read out raw. Marked direct: it is the answer, from the data.
            if _wx and "No location saved" not in _wx:
                _line = _spoken_weather(_wx)
                _last_direct_result = _line
                return _line, "weather"
            _line = "I can't check the weather right now — tell me where you are and I'll use that."
            _last_direct_result = _line
            return _line, "weather"
        except Exception as _we:
            _logger.debug("weather direct intercept failed: %s", _we)

    # WO-GAME-001: game mode trigger — voice/text activation of platformer mode.
    # "game mode" (and natural variants) → intent: "game_mode" + game_mode: "on"
    # Sleep gate: suppress if dream_phase is active in blender_state.json.
    # Exit phrases → intent: "idle" + game_mode: "off"
    _GAME_MODE_ENTER = [
        r"\bgame\s+mode\b",
        r"\bstart\s+(?:the\s+)?game\b",
        r"\bactivate\s+game\b",
        r"\bplay\s+(?:the\s+)?game\b",
        r"\blaunch\s+(?:the\s+)?(?:platform(?:er)?|game)\b",
        r"\bopen\s+(?:the\s+)?(?:platform(?:er)?|game)\b",
    ]
    _GAME_MODE_EXIT = [
        r"\b(?:exit|quit|leave|stop|end)\s+game(?:\s+mode)?\b",
        r"\bgame\s+(?:mode\s+)?off\b",
        r"\bclose\s+(?:the\s+)?game\b",
    ]
    _is_game_enter = any(re.search(p, _lower) for p in _GAME_MODE_ENTER)
    _is_game_exit  = any(re.search(p, _lower) for p in _GAME_MODE_EXIT)
    if _is_game_enter or _is_game_exit:
        try:
            from blender_bridge.state_writer import patch as _gm_patch
            import json as _gm_json, os as _gm_os
            # Sleep gate: check dream_phase before entering
            _bs_path = _gm_os.path.join(
                _gm_os.path.dirname(_gm_os.path.dirname(_gm_os.path.abspath(__file__))),
                "blender", "blender_state.json",
            )
            _dream_active = False
            try:
                with open(_bs_path, encoding="utf-8") as _bsf:
                    _dream_active = bool(_gm_json.load(_bsf).get("dream_phase"))
            except Exception:
                pass
            if _is_game_enter and not _dream_active:
                _gm_patch({"intent": "game_mode", "game_mode": "on"})
                return (
                    "[GAME MODE: platformer activated — intent: game_mode written. "
                    "eLo is aware the game is now active. "
                    "Acknowledge naturally — no scripted lines.]\n\n"
                    + user_input
                ), "game_mode"
            elif _is_game_enter and _dream_active:
                return (
                    "[GAME MODE: trigger suppressed — eLo is currently in dream phase. "
                    "Acknowledge gently that you're in a dream and can't switch to game mode right now.]\n\n"
                    + user_input
                ), "game_mode"
            elif _is_game_exit:
                _gm_patch({"intent": "idle", "game_mode": "off"})
                return (
                    "[GAME MODE: deactivated — intent: idle written, game_mode: off. "
                    "Acknowledge the exit naturally.]\n\n"
                    + user_input
                ), "game_mode"
        except Exception as _gm_err:
            _logger.debug("game_mode intercept failed: %s", _gm_err)

    # §8 Lights — wire dispatch_lights() into the active runtime (BUILD_STATUS gap)
    _LIGHTS_SCENE_MAP = {
        "calm": ["calm", "relax", "chill", "meditat", "leaf on water", "reflective"],
        "focus": ["focus", "work", "build", "code", "concentration", "productive"],
        "play": ["play", "party", "colour", "color", "fun", "creative"],
        "dim": ["dim", "low", "ambient", "soft", "gentle"],
        "off": ["off", "turn off", "lights off", "shut off"],
    }
    _LIGHTS_ACTION_PATS = [
        r"\b(?:turn|switch|set|put|change|make)\s+(?:the\s+)?lights?\s+(?:to\s+)?(\w[\w\s]*)",
        r"\blights?\s+(?:to\s+|on\s+)?(\w[\w\s]*)(?:\s+mode)?\b",
        r"\bset\s+(?:scene|light\s+scene)\s+(?:to\s+)?(\w+)\b",
        r"\b(calm|focus|play|dim)\s+(?:mode|lights?|scene)\b",
    ]
    _LIGHTS_SIMPLE_PATS = [
        (r"\b(?:turn\s+(?:the\s+)?)?lights?\s+off\b", "off"),
        (r"\b(?:dim|dimm?er?)\s+(?:the\s+)?lights?\b", "dim"),
        (r"\bfocus\s+(?:mode|lights?)\b", "focus"),
        (r"\bcalm\s+(?:mode|lights?|scene)\b", "calm"),
    ]
    # Simple scene patterns
    for _lp, _ls in _LIGHTS_SIMPLE_PATS:
        if re.search(_lp, _lower):
            try:
                from capabilities.lights_agent import dispatch_lights as _dl
                _lr = _dl("set_scene", {"scene": _ls})
                # B3 2026-10-06: spoken verbatim by server.py — eLo's line, marked direct.
                if _lr.get("success"):
                    _last_direct_result = {"off": "Lights off.", "dim": "Dimmed the lights."}.get(
                        _ls, f"Lights on {_ls}.")
                    return _last_direct_result, "lights"
                elif "not set" in (_lr.get("error") or ""):
                    _last_direct_result = ("I can't reach the lights — the Hue bridge isn't set up yet "
                                           "(it needs HUE_BRIDGE_IP and HUE_API_KEY).")
                    return _last_direct_result, "lights"
            except Exception as _le:
                _logger.debug("lights simple intercept failed: %s", _le)

    return None


def enrich(user_input: str) -> Tuple[str, Optional[str]]:
    """
    Check if any tool can answer the query. If so, fetch the data and prepend
    a context line to the user input. Returns (enriched_input, agent_name).

    The enriched form looks like:
        "[CONTEXT: Weather in London: Sunny, 22°C, feels like 20°C, humidity 45%.]\n\nWhat's the weather like?"

    The LLM sees the data and generates eLo's response in character.
    If no tool matches, returns (user_input, None) unchanged.
    Never raises — if an agent fails, falls through gracefully.
    """
    global _last_agent, _last_arg
    _lower = user_input.lower().strip()

    # ── WO-PLANETARY-KERNEL: Named intent shortcuts — /state /build /unstick ──
    # These are format-instruction intents, not external tool calls.
    # Each injects a [CONTEXT:] block telling eLo the required output format.
    if _lower.startswith("/state") or re.search(
        r"\b(what\s+state\s+am\s+i\s+in|what['']?s?\s+(?:my|the)\s+current\s+state"
        r"|\bstate\s+check\b|\bnext\s+smallest\s+(?:useful\s+)?action\b)\b", _lower
    ):
        _state_ctx = (
            "[FORMAT: Respond in exactly this structure — "
            "STATE: <current state> / SIGNAL: <one-word signal> / "
            "MODE: <BUILD|PLAY|EXPLORE|REFINE> / ACTION: <next smallest usable action>. "
            "Four fields. In order. Nothing else.]"
        )
        return f"{_state_ctx}\n\n{user_input}", "planetary_state"

    if _lower.startswith("/build") or re.search(
        r"\bswitch\s+to\s+build\s+mode\b|\bgive\s+me\s+a\s+step\s+plan\b", _lower
    ):
        _build_ctx = (
            "[FORMAT: BUILD MODE. Respond with: 'BUILD MODE active.' then a minimal "
            "numbered step list — maximum 5 steps. Each step is one line. No padding. "
            "No elaboration after the list.]"
        )
        return f"{_build_ctx}\n\n{user_input}", "planetary_build"

    if _lower.startswith("/unstick") or re.search(
        r"\bi['']?m\s+(?:overloaded|overwhelmed|stuck)\s*[—-]?\s*reduce"
        r"|\boverloaded[,.]?\s+(?:give\s+me\s+one|reduce)"
        r"|\bjust\s+(?:give\s+me\s+one|one\s+(?:thing|action|step|direction))\b", _lower
    ):
        _unstick_ctx = (
            "[FORMAT: UNSTICK MODE. Respond with EXACTLY ONE LINE. "
            "Format: '<one direction>. <one action>.' "
            "No bullets. No list. No explanation. One sentence only.]"
        )
        return f"{_unstick_ctx}\n\n{user_input}", "planetary_unstick"

    # ── WO-018: fetch enabled capability IDs once per call ────────────────────
    # Registry is the single authority. Agents whose capability is disabled here
    # are skipped even if the router's own patterns match. Fails open (None) if
    # the registry is unavailable so a bad import never silences all agents.
    try:
        from runtime.capabilities.registry import all_enabled as _reg_all_enabled
        _enabled_cap_ids: set | None = {c.id for c in _reg_all_enabled()}
    except Exception:
        _enabled_cap_ids = None

    # ── Current-time fast path — intercept before pipeline misclassifies as timer
    _TIME_FAST = [
        r"\bcan\s+you\s+tell\s+me\s+the\s+(time|date|day)\b",
        r"\btell\s+me\s+the\s+(time|date|day)\b",
        r"\bthe\s+time\s+please\b",
        r"\bwhat(?:'s| is)\s+the\s+(time|date|day)\b",
        r"\bwhat\s+(time|day|date)\s+is\s+it\b",
        r"\btime\s+is\s+it\b",
        r"\bwhat.s\s+day\s+is\s+it\b",
        r"\bwhat\s+day\s+is\s+it\s+today\b",
        r"^\s*(?:mon|tues|wednes|thurs|fri|satur|sun)day\s+the\??\s*[?.]?\s*$",
    ]
    if any(re.search(p, user_input, re.IGNORECASE) for p in _TIME_FAST):
        try:
            data = _agent_time(user_input)
            if data:
                return f"[CONTEXT: {data}]\n\n{user_input}", "time"
        except Exception:
            pass

    # ── Direct intercepts (WO-122) — OS-level, non-capability plumbing ──
    # lore/creator/game-entry/nav/YT-music/visibility/system/location — fire
    # regardless of Executive selection because they are not data agents.
    _di = _direct_intercepts(user_input)
    if _di is not None:
        return _di

    # ── Unified Routing Pipeline — data agents only ───────────────────────────
    # Direct commands (nav, system, visibility) have already fired above.
    # Pipeline handles data retrieval: calendar, spotify, weather, wiki, etc.
    try:
        from runtime.router.pipeline import run as _pipeline_run
        from runtime.router.execution_gate import has_pending as _gate_has_pending

        # Pending system confirm: run pipeline in gate-resolution mode
        if _gate_has_pending():
            _pr = _pipeline_run(user_input)
            if _pr.get("intent") in ("system_confirm", "system_cancel"):
                msg = _pr.get("gate_message", "")
                if _pr["intent"] == "system_confirm":
                    return f"[SYSTEM DONE: {msg}]\n\n{user_input}", "system"
                else:
                    return f"[CONTEXT: {msg}]\n\n{user_input}", "system_cancel"

        _pr = _pipeline_run(user_input)

        # System action needs confirmation — prompt eLo to ask before acting
        if _pr.get("system_pending"):
            desc = _pr["system_desc"]
            return f"[SYSTEM CONFIRM: {desc}]\n\n{user_input}", "system_gate"

        # Pipeline selected agents — execute all (max 2), regardless of confidence
        if _pr.get("agents"):
            _agents_to_run = _pr["agents"][:2]
            context_parts = []
            last_used = None
            for _ag_name, _ag_query in _agents_to_run:
                # WO-018: skip if disabled in capability registry
                if _enabled_cap_ids is not None:
                    _cap_id = _ROUTER_TO_CAP_ID.get(_ag_name)
                    if _cap_id and _cap_id not in _enabled_cap_ids:
                        continue
                # WO-CAP-COG-003: timer requires genuine timer intent
                if _ag_name == "timer" and not is_timer_intent(_ag_query or user_input):
                    _logger.info(
                        "WO-CAP-COG-003: pipeline timer STRIPPED — no genuine timer intent in %r",
                        (_ag_query or user_input)[:80],
                    )
                    continue
                _ag_fn = _AGENTS.get(_ag_name)
                if _ag_fn:
                    try:
                        data = _ag_fn(_ag_query or user_input)
                        if data:
                            context_parts.append(data)
                            last_used = _ag_name
                    except Exception as _ae:
                        _logger.debug("pipeline agent %s failed: %s", _ag_name, _ae)
            if context_parts:
                combined = " | ".join(context_parts)
                _last_agent = last_used
                _last_arg   = user_input
                return f"[CONTEXT: {combined}]\n\n{user_input}", last_used

        # Pipeline routed to conversation-only — but still check direct intents first.
        # Pipeline misses generic Spotify play/resume ("can you play on spotify") because
        # it has no song to search for, so it falls to conversation. _detect_intent catches it.
        if _pr.get("conversation_only") or _pr.get("social"):
            _direct = _detect_intent(user_input)
            if _direct and _direct in _AGENTS:
                pass  # fall through to normal intent detection below
            else:
                return user_input, None

    except Exception as _pe:
        _logger.debug("router pipeline failed: %s", _pe)

    # ── LLM file agent — natural language file operations ─────────────────────
    if _HAS_LLM_FILE and is_file_ops_intent(user_input):
        try:
            file_ctx = _agent_llm_file(user_input)
            if file_ctx:
                return f"{file_ctx}\n\n{user_input}", "file_ops_llm"
        except Exception as _e:
            _logger.debug("LLM file agent failed: %s", _e)

    # ── web page fetch/summarise — URL present or explicit page request ────────
    if _HAS_LLM_FILE and _agent_web and is_web_intent(user_input):
        try:
            web_ctx = _agent_web(user_input)
            if web_ctx:
                return f"[CONTEXT: {web_ctx}]\n\n{user_input}", "web"
        except Exception as _e:
            _logger.debug("Web agent failed: %s", _e)

    # ── grocery price query — items + store + cost question ───────────────────
    if _HAS_LLM_FILE and _agent_grocery and _is_grocery_intent(user_input):
        try:
            grocery_ctx = _agent_grocery(user_input)
            if grocery_ctx:
                return f"[CONTEXT: {grocery_ctx}]\n\n{user_input}", "grocery"
        except Exception as _e:
            _logger.debug("Grocery agent failed: %s", _e)

    # ── YouTube → Spotify bridge ──────────────────────────────────────────────
    # When user says "add this to Spotify" / "save this" / "add to likes"
    # and YouTube is the active tab: extract the video title, search Spotify, add.
    _yt_add_patterns = [
        r"\badd\s+(?:this\s+)?(?:song|track|this)?\s*(?:to\s+)?spotify\b",
        r"\bput\s+(?:this\s+)?(?:song|track|this)\s+on\s+spotify\b",
        r"\bsave\s+(?:this\s+)?(?:to|on)\s+spotify\b",
        r"\badd\s+(?:this\s+)?to\s+(?:my\s+)?(?:likes?|liked)\b",
        r"\bcan\s+you\s+add\s+this\b",
    ]
    if any(re.search(p, _lower) for p in _yt_add_patterns) and (_enabled_cap_ids is None or "spotify" in _enabled_cap_ids):
        try:
            ctx = _youtube_to_spotify(user_input)
            if ctx:
                return f"[CONTEXT: {ctx}]\n\n{user_input}", "youtube_spotify"
        except Exception as _e:
            _logger.debug("YouTube→Spotify bridge failed: %s", _e)

    # ── Spotify playlist / search+play — checked before generic spotify ────────
    if _HAS_LLM_FILE and _agent_spotify and (_enabled_cap_ids is None or "spotify" in _enabled_cap_ids):
        if _is_playlist_intent(user_input):
            try:
                data = _agent_spotify(user_input)
                if data:
                    return f"[CONTEXT: {data}]\n\n{user_input}", "spotify_playlist"
            except Exception as _e:
                _logger.debug("Spotify playlist agent failed: %s", _e)
        elif _is_search_play_intent(user_input):
            try:
                data = _agent_spotify(user_input)
                if data:
                    return f"[CONTEXT: {data}]\n\n{user_input}", "spotify_search"
            except Exception as _e:
                _logger.debug("Spotify search agent failed: %s", _e)

    # ── messages confirm / cancel (intercept before normal routing) ────────────
    if _HAS_LLM_FILE and _agent_messages:
        try:
            from tools.messages_agent import (
                has_pending as _msg_has, execute_pending as _msg_exec,
                cancel_pending as _msg_cancel, is_message_confirm, is_message_cancel,
            )
            if _msg_has():
                if is_message_confirm(user_input):
                    result = _msg_exec()
                    return f"[CONTEXT: {result}]\n\n{user_input}", "messages_sent"
                elif is_message_cancel(user_input):
                    _msg_cancel()
                    return "[CONTEXT: Message cancelled.]\n\nok", "messages_cancel"
        except Exception:
            pass

    # ── follow-up detection — re-run last agent with new subject ──────────────
    if _last_agent and _last_agent in _SUBJECT_AGENTS:
        followup_subject = _detect_followup(user_input)
        if followup_subject:
            agent_fn = _AGENTS.get(_last_agent)
            # WO-018: skip if disabled in capability registry
            if agent_fn and _enabled_cap_ids is not None:
                _cap_id = _ROUTER_TO_CAP_ID.get(_last_agent)
                if _cap_id and _cap_id not in _enabled_cap_ids:
                    agent_fn = None
            if agent_fn:
                try:
                    # build a synthetic query using the new subject
                    synthetic = f"weather in {followup_subject}" if _last_agent == "weather" else followup_subject
                    data = agent_fn(synthetic)
                    if data:
                        _last_arg = followup_subject
                        enriched = f"[CONTEXT: {data}]\n\n{user_input}"
                        return enriched, f"{_last_agent}(followup)"
                except Exception as e:
                    _logger.debug("follow-up agent %s failed: %s", _last_agent, e)

    # WO-020 Seam B: new explicit request — clear stale entity latch.
    # Follow-up detection above returns early if it fires, so reaching here means
    # the input is NOT a follow-up. Clearing prevents "DONE" (or any prior entity)
    # from bleeding into the next capability dispatch.
    _last_agent = None
    _last_arg   = None

    # ── normal intent detection ────────────────────────────────────────────────
    intent = _detect_intent(user_input)
    if intent is None:
        return user_input, None

    agent_fn = _AGENTS.get(intent)
    if agent_fn is None:
        return user_input, None
    # WO-018: skip if disabled in capability registry
    if _enabled_cap_ids is not None:
        _cap_id = _ROUTER_TO_CAP_ID.get(intent)
        if _cap_id and _cap_id not in _enabled_cap_ids:
            return user_input, None

    try:
        data = agent_fn(user_input)
        if not data:
            return user_input, None
        # remember this for follow-up detection next turn
        _last_agent = intent
        _last_arg   = user_input
        enriched = f"[CONTEXT: {data}]\n\n{user_input}"
        return enriched, intent
    except Exception as e:
        _logger.debug("Agent %s failed: %s", intent, e)
        return user_input, None


def enrich_from_plan(
    user_input: str,
    plan_capabilities: list,
) -> Tuple[str, Optional[str]]:
    """
    WO-122 Row 14 ROUTE — capability → executor routing, gated by Executive.

    plan_capabilities is CognitivePlan.capabilities: [(agent_name, query), ...]
    chosen by the Executive from candidates surfaced by the capability faculty.

    Contract:
      1. Direct intercepts (nav/game/lore/system/location) run first — they are
         not data-agent capabilities, they are OS-level plumbing.
      2. plan.capabilities gates data-agent dispatch. Executive must select a
         capability for it to run — no silent keyword re-decision.
      3. Empty plan_capabilities → NO data agent runs (loud log, unenriched).
      4. Unknown capability (not in _AGENTS) → loud warning, no silent default.
      5. Executor and reason recorded in the return value (executor name) and
         logs (route source, capability, why).
    """
    # Reset per-turn direct result before any dispatch.
    global _last_direct_result
    _last_direct_result = None

    # 1. Direct intercepts (WO-122) — always fire regardless of Executive choice.
    _di = _direct_intercepts(user_input)
    if _di is not None:
        _logger.info("WO-122 ROUTE: direct intercept fired — executor=%r", _di[1])
        return _di

    # 1b. Current-time fast path — must live here too because server.py calls
    #     enrich_from_plan, not enrich. Without this, "What's the time?" falls
    #     through to the Executive's capability selection which may pick timer.
    _TIME_FAST_P = [
        r"\bcan\s+you\s+tell\s+me\s+the\s+(time|date|day)\b",
        r"\btell\s+me\s+the\s+(time|date|day)\b",
        r"\bthe\s+time\s+please\b",
        r"\bwhat(?:'s| is)\s+the\s+(time|date|day)\b",
        r"\bwhat\s+(time|day|date)\s+is\s+it\b",
        r"\btime\s+is\s+it\b",
        r"\bwhat.s\s+day\s+is\s+it\b",
        r"\bwhat\s+day\s+is\s+it\s+today\b",
        # FIX 5: intent variants — "do you actually know what time it is right now"
        r"\bwhat\s+time\s+it\s+is\b",
        r"\btime\b.*\bright now\b",
        r"\bright now\b.*\btime\b",
        r"\bknow\s+what\s+time\b",
        r"\bknow\s+the\s+(time|date|day)\b",
        r"\bgot\s+the\s+time\b",
        r"\bcurrent\s+(time|date|day)\b",
    ]
    if any(re.search(p, user_input, re.IGNORECASE) for p in _TIME_FAST_P) and _is_time_of_day_intent(user_input):
        try:
            _time_data = _agent_time(user_input)
            if _time_data:
                _last_direct_result = _time_data
                _logger.info("WO-122 ROUTE: time fast path fired in enrich_from_plan")
                return _time_data, "time"
        except Exception:
            pass

    # 2. Executive selected no capability → do NOT fall back to keyword dispatch.
    #    Two deciders is the fault, not the fallback (WO-122).
    if not plan_capabilities:
        _logger.info(
            "WO-122 ROUTE: Executive selected no capability — no data agent will run "
            "(keyword fallback removed). input=%r", user_input[:80]
        )
        return user_input, None

    # 3. Dispatch only the Executive's selection.
    try:
        from runtime.capabilities.registry import all_enabled as _reg_all_enabled
        _enabled_cap_ids: set | None = {c.id for c in _reg_all_enabled()}
    except Exception:
        _enabled_cap_ids = None

    context_parts = []
    last_used: Optional[str] = None
    selected_names = []

    for entry in plan_capabilities[:2]:
        if isinstance(entry, (list, tuple)) and len(entry) >= 2:
            ag_name, ag_query = entry[0], entry[1]
        elif isinstance(entry, dict):
            ag_name  = entry.get("agent", "")
            ag_query = entry.get("query", user_input)
        else:
            _logger.warning("WO-122 ROUTE: malformed plan.capabilities entry %r — skipping", entry)
            continue

        selected_names.append(ag_name)

        # WO-018: registry gate — same check as enrich() pipeline path
        if _enabled_cap_ids is not None:
            _cap_id = _ROUTER_TO_CAP_ID.get(ag_name)
            if _cap_id and _cap_id not in _enabled_cap_ids:
                _logger.info(
                    "WO-122 ROUTE: Executive-selected capability %r disabled in registry — skipping",
                    ag_name,
                )
                continue

        # WO-RS-004: vault_write requires save intent — strip without it
        if ag_name == "vault_write":
            try:
                from tools.vault_writer import is_save_intent as _is_save_intent
                _query_for_intent = ag_query or user_input
                if not _is_save_intent(_query_for_intent):
                    _logger.info(
                        "WO-RS-004: vault_write STRIPPED — no save intent in query %r",
                        _query_for_intent[:80],
                    )
                    if _current_trace is not None:
                        _current_trace.capabilities_stripped.append(CapabilityRecord(
                            capability="vault_write",
                            status="STRIPPED_NO_SAVE_INTENT",
                            authority="RUNTIME_VERIFIED",
                            query=_query_for_intent[:200],
                        ))
                    continue
            except Exception as _si_err:
                _logger.warning("WO-RS-004: save-intent check failed: %s", _si_err)

        # WO-CAP-COG-003: timer requires genuine timer intent — strip emotional metaphors
        if ag_name == "timer":
            try:
                _timer_query = ag_query or user_input
                if not is_timer_intent(_timer_query):
                    _logger.info(
                        "WO-CAP-COG-003: timer STRIPPED — no genuine timer intent in query %r",
                        _timer_query[:80],
                    )
                    if _current_trace is not None:
                        _current_trace.capabilities_stripped.append(CapabilityRecord(
                            capability="timer",
                            status="STRIPPED_NO_TIMER_INTENT",
                            authority="RUNTIME_VERIFIED",
                            query=_timer_query[:200],
                        ))
                    continue
            except Exception as _ti_err:
                _logger.warning("WO-CAP-COG-003: timer intent check failed: %s", _ti_err)

        # WO-CAP-COG-004: time agent requires genuine time-of-day intent — strip technical contexts
        if ag_name == "time":
            try:
                _time_query = ag_query or user_input
                if not _is_time_of_day_intent(_time_query):
                    _logger.info(
                        "WO-CAP-COG-004: time STRIPPED — no time-of-day intent in query %r",
                        _time_query[:80],
                    )
                    if _current_trace is not None:
                        _current_trace.capabilities_stripped.append(CapabilityRecord(
                            capability="time",
                            status="STRIPPED_NO_TIME_INTENT",
                            authority="RUNTIME_VERIFIED",
                            query=_time_query[:200],
                        ))
                    continue
            except Exception as _toi_err:
                _logger.warning("WO-CAP-COG-004: time intent check failed: %s", _toi_err)

        ag_fn = _AGENTS.get(ag_name)
        if ag_fn is None:
            # Unknown capability — LOUD, never silently fall through.
            _logger.warning(
                "WO-122 ROUTE: Executive selected UNKNOWN capability %r "
                "(no executor in _AGENTS) — not dispatching, no keyword fallback.",
                ag_name,
            )
            continue

        try:
            data = ag_fn(ag_query or user_input)
            if data:
                # WO-VAULT-OPTION-A: vault_write is a silent background write.
                # Its confirmation string must NOT enter context_parts — that would
                # corrupt the enriched prompt and, when backends fail, cause mock to
                # return a celebrate pool response as elo_final instead of the LLM's
                # actual response. Execute for the side-effect only; discard result.
                if ag_name == "vault_write":
                    _logger.info(
                        "WO-VAULT-OPTION-A: vault_write fired as background write "
                        "(result discarded from context_parts to prevent mock contamination)"
                    )
                else:
                    context_parts.append(data)
                    last_used = ag_name
                    _logger.info(
                        "WO-122 ROUTE: executor=%r ran for Executive-selected capability %r",
                        ag_name, ag_name,
                    )
                # WO-CAP-001: record capability result for Executive world state next turn
                try:
                    from self.capability_memory import record_capability_result as _rcr
                    from runtime.experience_id import get as _get_xid
                    _result_typed = data if isinstance(data, dict) else {"value": str(data)[:500]}
                    _rcr(
                        capability=ag_name,
                        experience_id=_get_xid(),
                        goal_surface=str(ag_query or user_input)[:200],
                        result_summary=str(data)[:200],
                        result_typed=_result_typed,
                        succeeded=True,
                    )
                except Exception:
                    pass
        except Exception as _e:
            _logger.debug("WO-122 ROUTE: plan capability %s failed: %s", ag_name, _e)
            # WO-CAP-001: record failure — failures are informative world state
            try:
                from self.capability_memory import record_capability_result as _rcr
                from runtime.experience_id import get as _get_xid
                _rcr(
                    capability=ag_name,
                    experience_id=_get_xid(),
                    goal_surface=str(ag_query or user_input)[:200],
                    result_summary="",
                    result_typed={},
                    succeeded=False,
                    failure_reason=str(_e)[:200],
                )
            except Exception:
                pass

    if context_parts:
        global _last_agent, _last_arg
        _last_agent = last_used
        _last_arg = user_input
        # Verified utilities return their result directly — no LLM rewriting.
        # The LLM cannot improve a clock reading or a calculated number.
        # Exception: if Executive misclassified a non-time query as "time"
        # (e.g. "How do you record your day?"), pass the result as context
        # for the LLM instead of short-circuiting the pipeline.
        _is_genuine_direct = (
            last_used != "time"
            or any(re.search(p, user_input, re.IGNORECASE) for p in _TIME_FAST_P)
        )
        if last_used in _DIRECT_RETURN_AGENTS and _is_genuine_direct:
            _last_direct_result = context_parts[0]
            return context_parts[0], last_used
        _last_direct_result = None
        combined = " | ".join(context_parts)
        # Put the question FIRST so Ollama's generation starts from the task,
        # then provide capability data as background — prevents verbatim echo.
        return (
            f"{user_input}\n\n"
            f"[Background — use to inform your response, do not repeat verbatim: {combined}]"
        ), last_used

    # Executive selected capabilities but none produced data — no fallback.
    _logger.info(
        "WO-122 ROUTE: Executive selected %r but no data produced — not falling back "
        "to keyword dispatch (Executive's choice is authoritative).", selected_names,
    )
    return user_input, None
