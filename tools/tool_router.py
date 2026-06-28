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
    from tools.spotify_agent    import agent as _agent_spotify
    from tools.github_agent     import agent as _agent_github
    from tools.calendar_agent   import agent as _agent_calendar
    from tools.vision_agent     import agent as _agent_vision
    from tools.draft_agent      import agent as _agent_draft, is_draft_intent
    from tools.file_reader_agent import agent as _agent_file_reader, is_file_read_intent
    from tools.vault_writer     import agent as _agent_vault_writer, is_save_intent
except ImportError:
    _agent_spotify = _agent_github = _agent_calendar = _agent_vision = None
    _agent_draft = _agent_file_reader = _agent_vault_writer = None
    def is_draft_intent(t): return False
    def is_file_read_intent(t): return False
    def is_save_intent(t): return False

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
        r"\bplay\s+(?:music|spotify|something)\b",
        r"\bwhat\s+(?:song|track|music)\b",
        r"\bwho(?:'s| is)\s+(?:this|playing)\b",
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
    ("translate", [
        r"\btranslate\s+.+\s+(?:to|into)\b",
        r"\bhow\s+(?:do\s+you|to)\s+say\b",
        r"\bsay\s+['\"].+['\"]\s+in\s+\w+",
        r"\bwhat(?:'s| is)\s+['\"].+['\"]\s+in\s+\w+",
        r"\bin\s+(?:spanish|french|german|italian|japanese|chinese|korean|arabic|portuguese|russian|hindi|dutch|swedish|polish|turkish|greek|hebrew|thai|vietnamese|malay|indonesian)\b",
    ]),
    ("news", [
        r"\bnews\b",
        r"\bheadlines\b",
        r"\bwhat(?:['']s?|\s+is)?\s+(?:happening|going\s+on)\b",
        r"\blatest\b.*\b(?:news|stories|events)\b",
        r"\btoday'?s?\s+(?:news|stories)\b",
        r"\btop\s+stories\b",
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
        return f"From {data.get('AbstractSource', 'DuckDuckGo')} — {heading}: {abstract[:400]}"
    # Try related topics
    for topic in data.get("RelatedTopics", [])[:3]:
        if isinstance(topic, dict) and topic.get("Text"):
            return f"From DuckDuckGo — {topic['Text'][:300]}"
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


def _agent_news(query: str) -> str:
    """Pull headlines from RSS — BBC News, BBC Science, or Hacker News. No key needed."""
    import httpx

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
    "calendar":    _agent_calendar,
    "vision":      _agent_vision,
    "draft":       _agent_draft,
    "file_read":   _agent_file_reader,
    "vault_write": _agent_vault_writer,
}

# agents that accept a direct subject string for follow-up re-runs
_SUBJECT_AGENTS = {"weather", "search", "news"}


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
