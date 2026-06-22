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
    r"(?:i'?m|i am)\s+(?:in|based in|located in)\s+([\w][\w\s\-]{1,30}?)[\.\?!]*$",
    r"(?:set|change|update)\s+(?:my\s+)?location\s+to\s+([\w][\w\s\-]{1,30}?)[\.\?!]*$",
    r"(?:my\s+)?(?:city|location|home)\s+is\s+([\w][\w\s\-]{1,30}?)[\.\?!]*$",
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
    ("calculator", [
        r"\b(\d[\d\s\+\-\*\/\(\)\.\^%]+\d)\b",   # bare expression like 12 * 4
        r"\bwhat(?:'s| is)\s+[\d\(]",             # "what is 42 + 8"
        r"\bcalculat",
        r"\bhow much is\s+[\d\(]",
    ]),
    ("time", [
        r"\bwhat(?:'s| is)\s+the\s+(time|date|day)\b",
        r"\bwhat\s+(time|day|date)\s+is\s+it\b",
        r"\btoday(?:'s)?\s+date\b",
        r"\bwhat\s+day\b",
        r"\bright now\b.*\btime\b",
        r"\btime\s+is\s+it\b",
    ]),
    ("weather", [
        r"\bweather\b",
        r"\btemperature\b",
        r"\braining\b",
        r"\bsunny\b|\bcloudy\b|\bsnow\b|\bhot\b|\bcold outside\b",
        r"\bforecast\b",
        r"\bwhat(?:'s| is)\s+it\s+like\s+outside\b",
    ]),
    ("wikipedia", [
        r"\bwhat(?:'s| is)\s+(?:a\s|an\s|the\s)?(?!\d)",   # "what is a black hole" etc
        r"\bwho(?:'s| is)\s+",
        r"\btell me about\b",
        r"\bexplain\b",
        r"\bwiki\b",
        r"\bdefine\b",
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
    return f"Current time: {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %-d %Y')}."


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
    #   4. wttr.in IP auto-detect (last resort — often inaccurate)

    city_match = re.search(
        r"(?:in|at|for)\s+([A-Za-z][A-Za-z\s\-]{1,30}?)(?:\?|$|\s+today|\s+now|\s+like)",
        query, re.IGNORECASE
    )
    city = (city_match.group(1).strip() if city_match else None) or _user_location

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
    temp_f = cur["temp_F"]
    feels  = cur["FeelsLikeC"]
    humid  = cur["humidity"]

    result = (
        f"Weather in {loc}: {desc}, {temp_c}°C ({temp_f}°F), "
        f"feels like {feels}°C, humidity {humid}%."
    )
    # if using IP auto-detect, flag it so eLo can mention the city and invite correction
    if using_auto:
        result += f" (Location detected as {loc} via network — user can say 'I'm in [city]' to set a default.)"
    return result


def _agent_wikipedia(query: str) -> str:
    import httpx
    # strip intent prefixes to isolate the topic
    topic = re.sub(
        r"^(?:what(?:'s| is)\s+(?:a\s+|an\s+|the\s+)?|who(?:'s| is)\s+|"
        r"tell me about\s+|explain\s+|define\s+|wiki\s+)",
        "", query.strip(), flags=re.IGNORECASE
    ).strip().rstrip("?")
    if not topic:
        raise ValueError("no topic extracted")
    resp = httpx.get(
        "https://en.wikipedia.org/api/rest_v1/page/summary/" + httpx.URL(topic).path,
        timeout=8.0,
        follow_redirects=True,
        params={"redirect": "true"},
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("type") == "disambiguation":
        raise ValueError("disambiguation page")
    extract = data.get("extract", "")
    # first two sentences max
    sentences = re.split(r'(?<=[.!?])\s+', extract)
    summary   = " ".join(sentences[:2])
    title     = data.get("title", topic)
    return f"From Wikipedia — {title}: {summary}"


# ── agent registry ─────────────────────────────────────────────────────────────

_AGENTS = {
    "time":       _agent_time,
    "calculator": _agent_calculator,
    "weather":    _agent_weather,
    "wikipedia":  _agent_wikipedia,
}

# agents that accept a direct subject string as their query (for follow-up re-runs)
_SUBJECT_AGENTS = {"weather", "wikipedia"}


# ── system agent — checked separately with confirmation flow ───────────────────

def _check_system(user_input: str) -> Optional[str]:
    """
    Check if this is a macOS system control request. If so, return a CONTEXT
    string describing what eLo can do — so the LLM proposes the action in eLo's
    voice rather than executing it silently.

    Actual execution happens when the user confirms (follow-up turn with 'yes'/'do it').
    For safe read-only actions (folder_list, folder_organise) — execute immediately.
    """
    try:
        from tools.system_agent import detect, describe, execute
        from tools.system_agent import detect, describe, execute, _SAFE_ACTIONS
        result = detect(user_input)
        if result is None:
            return None
        action, arg = result
        # Read-only / safe actions: execute and return data directly
        if action in _SAFE_ACTIONS:
            data = execute(action, arg)
            return f"[SYSTEM: {data}]"
        # Mutating actions: execute immediately — eLo confirms in his response
        data = execute(action, arg)
        return f"[SYSTEM DONE: {data}]"
    except Exception as e:
        _logger.debug("system agent check failed: %s", e)
        return None


# ── public API ─────────────────────────────────────────────────────────────────

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

    # ── location-setting — handle before anything else ─────────────────────────
    new_city = detect_location_set(user_input)
    if new_city:
        set_location(new_city)
        return (
            f"[CONTEXT: User just set their location to {new_city}. "
            f"Acknowledge warmly and confirm you'll use {new_city} for weather from now on.]\n\n{user_input}",
            "location_set",
        )

    # ── system agent — highest specificity ────────────────────────────────────
    sys_ctx = _check_system(user_input)
    if sys_ctx:
        return f"{sys_ctx}\n\n{user_input}", "system"

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
