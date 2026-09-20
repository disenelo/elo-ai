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

# Priority: persisted JSON > ELO_LOCATION env > code default
_user_location: Optional[str] = (
    _load_persisted_location()
    or os.environ.get("ELO_LOCATION", "").strip()
    or None
)
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


def set_location(city: str) -> None:
    """Save user's preferred location in memory + blender/user_location.json (survives restarts)."""
    global _user_location
    _user_location = city.strip()
    try:
        _save_persisted_location(_user_location)
    except Exception:
        pass
    # WO-037: also save as a durable semantic fact so recall surfaces it specifically
    try:
        from memory.fact_store import save_fact as _sf
        _sf("location", f"Studio / home location: {_user_location}")
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
        r"\bremind\s+me\s+in\s+\d+\b",
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
        r"\bmake\s+a\s+note\b",
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
    wants_time = bool(re.search(r"\btime\b", q))
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
    # normalise word operators → symbols before extraction
    q = re.sub(r'\bdivided\s+by\b', '/', query, flags=re.IGNORECASE)
    q = re.sub(r'\btimes\b',        '*', q,     flags=re.IGNORECASE)
    q = re.sub(r'\bplus\b',         '+', q,     flags=re.IGNORECASE)
    q = re.sub(r'\bminus\b',        '-', q,     flags=re.IGNORECASE)
    q = re.sub(r'(?<=\d)\s*[xX]\s*(?=\d)', '*', q)  # "5 x 5" → "5 * 5"
    # extract arithmetic expression from normalised query
    match = re.search(r"[\d\(\)\+\-\*\/\.\^ ]+", q)
    if not match:
        raise ValueError("no expression found")
    expr = match.group(0).strip().replace("^", "**")
    if not expr or not re.search(r'\d', expr):
        raise ValueError("no numeric expression found")
    tree = ast.parse(expr, mode="eval")
    result = _safe_eval(tree.body)
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    display = expr.replace('**', '^')
    return f"{display} = {result}"


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
    city = (city_match.group(1).strip() if city_match else None) or _user_location
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


def _direct_intercepts(user_input: str) -> Optional[Tuple[str, Optional[str]]]:
    """
    WO-122 Row 14 ROUTE — OS-level intercepts that fire regardless of Executive
    capability selection. These do NOT dispatch data agents from the capability
    set — they are direct OS actions (nav, game entry, system control), window-
    state reads, identity responses (lore/creator), or user-config actions
    (location set). Returns (enriched, executor) if an intercept fires, else None.
    """
    _lower = user_input.lower()

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

    # ── Calculator — direct intercept (fires regardless of Executive) ──
    # Patterns that indicate a clear arithmetic query. Must contain a digit AND
    # at least one operator (word or symbol) so we don't grab "what is eLo?" etc.
    _MATH_DIRECT_PATS = [
        r"\bwhat(?:'s| is)\s+\(?\d[\d\s]*(?:times|plus|minus|divided\s+by|[xX*+\-\/^])\s*[\d\(]",
        r"\bhow\s+much\s+is\s+\(?\d[\d\s]*(?:times|plus|minus|divided\s+by|[xX*+\-\/^])\s*[\d\(]",
        r"\bcalculate\s+\(?\d",
        r"\b\d[\d\s]*(?:times|plus|minus|divided\s+by)\s+\d",
        r"\b\d+\s*[\*\/\^]\s*\d",   # symbolic * / ^ (not + or - to avoid "I need 5 - 3 items")
    ]
    if any(re.search(p, _lower) for p in _MATH_DIRECT_PATS):
        try:
            global _last_direct_result
            _calc_result = _agent_calculator(user_input)
            _last_direct_result = _calc_result
            return _calc_result, "calculator"
        except Exception as _ce:
            _logger.debug("math direct intercept failed: %s", _ce)

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
        set_location(new_city)
        return (
            f"[CONTEXT: User just set their location to {new_city}. "
            f"Acknowledge warmly and confirm you'll use {new_city} for weather from now on.]\n\n{user_input}",
            "location_set",
        )

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
            if _wx and "No location saved" not in _wx:
                return f"[CONTEXT: {_wx}]\n\n{user_input}", "weather"
            # No location set or no weather API — honest fallback (D7-compliant)
            return (
                "[CONTEXT: No weather data available — no location saved and no weather API "
                "is connected. Tell the user honestly that you can't check the weather, and "
                "if they want to enable it they can tell you their city (e.g. 'I\\'m in London').]\n\n"
                + user_input
            ), "weather"
        except Exception as _we:
            _logger.debug("weather direct intercept failed: %s", _we)

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
    if any(re.search(p, user_input, re.IGNORECASE) for p in _TIME_FAST_P):
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
