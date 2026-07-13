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

# User's preferred location — loaded from ELO_LOCATION env var, overridable
# at runtime by saying "I'm in London" / "set my location to London".
_user_location: Optional[str] = os.environ.get("ELO_LOCATION", "").strip() or None

# follow-up patterns — short phrases that reference a new subject but imply
# the same agent type as the previous turn
_FOLLOWUP_PATTERNS = [
    r"^(?:what|how)?\s*about\s+(?:in\s+)?([\w][\w\s\-]{1,30}?)[\?\.]*$",
    r"^(?:and\s+)?in\s+([\w][\w\s\-]{1,30}?)[\?\.]*$",
    r"^how about\s+(?:in\s+)?([\w][\w\s\-]{1,30}?)[\?\.]*$",
    r"^(?:what(?:'s| is) it like\s+)?in\s+([\w][\w\s\-]{1,30}?)[\?\.]*$",
    r"^(?:and\s+)?(?:what about|how about)\s+([\w][\w\s\-]{1,30}?)[\?\.]*$",
]

# location-setting phrases: "I'm in London" / "set my location to London"
_LOCATION_SET_PATTERNS = [
    r"(?:i'?m|i am)\s+(?:in|based in|located in)\s+([A-Za-z][A-Za-z\s\-]{0,25}?)(?:[,\.\?!]|$)",
    r"(?:set|change|update)\s+(?:my\s+)?location\s+to\s+([\w][\w\s\-]{1,30}?)[\.\?!]*$",
    r"(?:my\s+)?(?:city|location|home)\s+is\s+([\w][\w\s\-]{1,30}?)[\.\?!]*$",
    r"(?:we'?re|we are)\s+(?:in|based in|at)\s+([A-Za-z][A-Za-z\s\-]{0,25}?)(?:[,\.\?!]|$)",
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
    """Save user's preferred location for this session (and optionally to .env)."""
    global _user_location
    _user_location = city.strip()


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
        r"\btime\s+is\s+it\b",
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
    # extract expression from query
    match = re.search(r"[\d\(\)\+\-\*\/\.\^ ]+", query)
    if not match:
        raise ValueError("no expression found")
    expr = match.group(0).strip().replace("^", "**")
    tree = ast.parse(expr, mode="eval")
    result = _safe_eval(tree.body)
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return f"{expr.replace('**', '^')} = {result}"


def _agent_weather(query: str) -> str:
    import httpx

    # Location priority:
    #   1. Explicit city in this query ("weather in London")
    #   2. Session location set by user ("I'm in London")
    #   3. ELO_LOCATION env var (persistent default)
    #   4. Auto-detect (last resort)

    city_match = re.search(
        r"(?:in|at|for)\s+([A-Za-z][A-Za-z\s\-]{1,30}?)(?:\?|$|\s+today|\s+now|\s+like|\s+forecast)",
        query, re.IGNORECASE
    )
    city = (city_match.group(1).strip() if city_match else None) or _user_location

    # ── AccuWeather (primary) ─────────────────────────────────────────────────
    try:
        from tools.accuweather_agent import agent as _accu_agent, is_available as _accu_ok
        if _accu_ok():
            result = _accu_agent(query, city=city)
            if result:
                return result
    except Exception as _ae:
        _logger.warning("AccuWeather failed (%s), falling back to wttr.in", _ae)

    # ── wttr.in (fallback) ────────────────────────────────────────────────────
    target     = city.replace(" ", "+") if city else "auto"
    using_auto = not city

    resp = httpx.get(
        f"https://wttr.in/{target}",
        params={"format": "j1"},
        headers={"Accept": "application/json"},
        timeout=8.0,
        follow_redirects=True,
    )
    resp.raise_for_status()
    data = resp.json()
    area   = data["nearest_area"][0]
    loc    = f"{area['areaName'][0]['value']}, {area['country'][0]['value']}"
    cur    = data["current_condition"][0]
    desc   = cur["weatherDesc"][0]["value"]
    temp_c = cur["temp_C"]
    feels  = cur["FeelsLikeC"]
    humid  = cur["humidity"]

    result = f"Weather in {loc}: {desc}, {temp_c}°C, feels like {feels}°C, humidity {humid}%."
    if using_auto:
        result += f" (Detected as {loc} — say 'I'm in [city]' to set a default.)"
    return result


def _agent_wikipedia(query: str) -> str:
    import httpx
    topic = re.sub(
        r"^(?:what(?:'s| is)\s+(?:a\s+|an\s+|the\s+)?|who(?:'s| is)\s+|"
        r"tell me about\s+|explain\s+|define\s+|wiki\s+|search\s+(?:for\s+)?)",
        "", query.strip(), flags=re.IGNORECASE
    ).strip().rstrip("?")
    if not topic:
        raise ValueError("no topic extracted")
    resp = httpx.get(
        "https://en.wikipedia.org/api/rest_v1/page/summary/" + httpx.URL(topic).path,
        timeout=8.0,
        follow_redirects=True,
        headers={"User-Agent": "eLo-OS/1.0"},
        params={"redirect": "true"},
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("type") == "disambiguation":
        raise ValueError("disambiguation page")
    extract = data.get("extract", "")
    sentences = re.split(r'(?<=[.!?])\s+', extract)
    summary   = " ".join(sentences[:2])
    title     = data.get("title", topic)
    return f"From Wikipedia — {title}: {summary}"


def _agent_duckduckgo(query: str) -> str:
    """DuckDuckGo Instant Answers — free, no key. Best for entity lookups and quick facts."""
    import httpx
    resp = httpx.get(
        "https://api.duckduckgo.com/",
        params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
        timeout=8.0,
        follow_redirects=True,
        headers={"User-Agent": "eLo-OS/1.0"},
    )
    resp.raise_for_status()
    data = resp.json()
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
    import httpx, os as _os

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
        resp = httpx.post(url, json=payload, params={"key": api_key}, timeout=10.0)
        if resp.status_code == 200:
            translated = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip().strip('"')
            return f'"{text}" in {lang}: {translated}'

    # Fall back to OpenAI
    openai_key = _os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a translator. Output ONLY the translation, no explanation."},
                    {"role": "user",   "content": f'Translate "{text}" to {lang}'},
                ],
                "max_tokens": 150, "temperature": 0.1,
            },
            timeout=10.0,
        )
        if resp.status_code == 200:
            translated = resp.json()["choices"][0]["message"]["content"].strip().strip('"')
            return f'"{text}" in {lang}: {translated}'

    raise ValueError("no translation backend available")


_NEWS_NEGATION = re.compile(
    r"\b(don'?t|doesn'?t|not|never|stop|no|hate|dislike|avoid|removed|off)\b"
    r".{0,30}"
    r"\b(news|headlines|stories)\b",
    re.IGNORECASE,
)

def _agent_news(query: str) -> str:
    """Pull headlines from RSS — BBC News, BBC Science, or Hacker News. No key needed."""
    import httpx

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

    resp = httpx.get(url, timeout=8.0, follow_redirects=True, headers={"User-Agent": "eLo-OS/1.0"})
    resp.raise_for_status()
    xml = resp.text

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
}

# agents that accept a direct subject string for follow-up re-runs
_SUBJECT_AGENTS = {"weather", "search", "news"}


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
    _lower = user_input.lower()

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

    # ── eLo universe lore intercept — block search from misidentifying eLo characters ──
    # K-7, Chunk, eLo, DISENELO are eLo-universe entities. "what is K-7" must NOT
    # trigger a Wikipedia/DuckDuckGo search (Kalinin K-7 aircraft, etc.)
    _LORE_INTERCEPTS = [
        (r"\bk-?7\b",        "K-7",        "K-7 is eLo's spirit animal companion — a shapeshifting entity that can take 7 different forms. K-7 travels with eLo through the universe."),
        (r"\bchunk\b",       "Chunk",      "Chunk is eLo's friend — a modular character whose body transforms into different vehicles and structures to help navigate the world."),
        (r"\bdisenelo\b",    "DISENELO",   "DISENELO is David's creative brand — home of eLo the character, the game, the book, the robot, and a series of free maker tools."),
        (r"\belo(?:\s+the\s+(?:character|book|game))?\b", "eLo", "eLo is an original character — an adorable childhood imagination paired with adult reality. The book, game, robot, and art all radiate from eLo."),
    ]
    _LORE_TRIGGER = r"\b(?:what(?:'s| is)|who(?:'s| is)|tell\s+me\s+about|explain|describe)\b"
    if re.search(_LORE_TRIGGER, _lower):
        for _lore_pat, _lore_name, _lore_fact in _LORE_INTERCEPTS:
            if re.search(_lore_pat, _lower, re.IGNORECASE):
                return f"[CONTEXT: {_lore_fact}]\n\n{user_input}", "lore"

    # Creator question — "who made you / built you / created you"
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

    # ── Direct command intercepts — always fire before pipeline ─────────────────
    # These control the avatar/system directly. Pipeline is for DATA agents only.
    # Nav, game-entry, screen-visibility, browser-tab, and system commands must
    # never be blocked by the pipeline's conversation_only early-return.

    # game entry
    try:
        from runtime.executive import _GAME_ENTRY_PHRASES as _GE
        if any(p in _lower for p in _GE):
            _write_game_entry_event()
            return f"[GAME_ENTRY: exit sequence triggered — say your going-in line now]\n\n{user_input}", "game_entry"
    except Exception as _e:
        _logger.debug("game entry intercept failed: %s", _e)

    # movement / navigation
    try:
        from runtime.executive import _MOVEMENT_COMMAND_PHRASES as _MV
        if any(p in _lower for p in _MV):
            nav_type, target = _parse_nav(user_input)
            _write_nav_event(nav_type, target)
            ctx = f"target={target}" if target else "moving"
            return f"[NAV: {nav_type} — {ctx}]\n\n{user_input}", "nav"
    except Exception as _e:
        _logger.debug("nav intercept failed: %s", _e)

    # YouTube Music / active browser tab
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

    # app / screen visibility
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

    # system agent
    sys_ctx = _check_system(user_input)
    if sys_ctx:
        return f"{sys_ctx}\n\n{user_input}", "system"

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

    # ── location-setting ──────────────────────────────────────────────────────
    new_city = detect_location_set(user_input)
    if new_city:
        set_location(new_city)
        return (
            f"[CONTEXT: User just set their location to {new_city}. "
            f"Acknowledge warmly and confirm you'll use {new_city} for weather from now on.]\n\n{user_input}",
            "location_set",
        )

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
    if any(re.search(p, _lower) for p in _yt_add_patterns):
        try:
            ctx = _youtube_to_spotify(user_input)
            if ctx:
                return f"[CONTEXT: {ctx}]\n\n{user_input}", "youtube_spotify"
        except Exception as _e:
            _logger.debug("YouTube→Spotify bridge failed: %s", _e)

    # ── Spotify playlist / search+play — checked before generic spotify ────────
    if _HAS_LLM_FILE and _agent_spotify:
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

    # ── normal intent detection ────────────────────────────────────────────────
    intent = _detect_intent(user_input)
    if intent is None:
        return user_input, None

    agent_fn = _AGENTS.get(intent)
    if agent_fn is None:
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
