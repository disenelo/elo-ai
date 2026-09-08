"""
runtime/router/intent_engine.py — Stage 04: Intent Classification

Determine what the user wants, not just what they said.
Intent categories map to agent routing priorities.

Output: {intent, confidence, chain, category, reason}
  category — Vol V Ch.8 five-category system:
    Build | Explore | Reflect | Decide | Connect
  reason   — one-phrase explanation of the category assignment
"""
from __future__ import annotations
import re

# ── Intent taxonomy ───────────────────────────────────────────────────────────
# Ordered by specificity — first match wins.

_INTENT_PATTERNS: list[tuple[str, list[str]]] = [
    ("file_ops", [
        r"\b(?:move|copy|rename|delete|trash)\s+\b",
        r"\borganise\s+(?:my\s+)?(?:folder|files|desktop)\b",
        r"\bwhat(?:'s|\s+is)\s+in(?:side)?\s+(?:the\s+)?(?:output|desktop|downloads?|documents?)\s+folder\b",
        r"\b(?:output|desktop|downloads?|documents?)\s+folder\s+(?:what|list|contents?)\b",
    ]),
    ("memory", [
        r"\b(?:what|what's)\s+(?:did\s+i|i)\s+(?:say|tell|write|mention|talk)\b",
        r"\bwhat\s+(?:were\s+)?(?:we|i)\s+(?:working\s+on|talking\s+about|building)\b",
        r"\bremember\s+(?:when|what|that)\b",
        r"\bwhat\s+(?:was|were)\s+(?:i|we|the)\b.*\b(?:earlier|before|last\s+time|yesterday)\b",
        r"\bwhat\s+did\s+(?:i|we)\s+(?:say|write|build|make|work\s+on)\b",
        r"\bmy\s+(?:notes?|journal|vault|obsidian)\b",
        r"\bi\s+(?:wrote|noted|saved)\s+",
        r"\brecall\b",
        r"\bfrom\s+(?:before|earlier|last\s+(?:session|time))\b",
    ]),
    ("system", [
        r"\b(?:volume|brightness)\s*(?:up|down|to\s*\d+|mute|unmute)\b",
        r"\bturn\s+(?:the\s+)?(?:volume|brightness)\b",
        r"\b(?:set|put)\s+(?:the\s+)?(?:volume|brightness)\b",
        r"\b(?:open|launch|start)\s+\w+\s*(?:app|application)?\b",
        # WO-039b: require a real app/process TARGET — "close friends"/"exit strategy"
        # must NOT fire (no real target). Target = known app word OR explicit "app/window/tab/process".
        r"^(?:please\s+)?(?:quit|exit|close|kill|force.?quit)\s+(?:the\s+)?(?:app|window|tab|browser|finder|chrome|safari|terminal|vscode|code|spotify|script|process|task|programme|program|\w+\.(?:app|exe|py|sh))\b",
        r"\b(?:focus|bring)\s+\w+\s+(?:to\s+)?(?:the\s+)?front\b",
        r"\bdark\s+mode\b",
        r"\blight\s+mode\b",
        r"\bscreenshot\b",
        r"\bfullscreen\b",
        r"\bfull\s+screen\b",
        r"\b(?:turn\s+(?:on\s+)?|enable\s+|disable\s+|switch\s+(?:on|off)\s+)?bluetooth\s*(?:on|off)\b",
        r"\b(?:connect|disconnect|pair)\s+(?:(?:my\s+)?bluetooth|bt)\b",
        r"\bbluetooth\s+(?:connect|disconnect|list|paired|devices?|status|on|off)\b",
        r"\bconnect\s+(?:my\s+)?bluetooth\s+to\b",
        r"\bconnect\s+(?:to\s+)?(?:my\s+)?(?:studio\s+)?speaker\b",
        r"\bconnect\s+(?:to\s+)?(?:the\s+)?(?:echo\s+dot|studio|creation\s+station)\b",
        r"\bpair\s+(?:to\s+)?(?:my\s+)?(?:bluetooth\s+)?(?:speaker|headphones?|earbuds?|airpods?)\b",
        r"\b(?:is\s+)?bluetooth\s+(?:on|off|connected|status)\b",
        r"\bcheck\s+bluetooth\b",
    ]),
    ("utility_timer", [
        r"\b(?:set|start)\s+(?:a\s+)?timer\b",  # action word required — bare "timer" is not a timer command
        r"\b\d+\s*(?:min(?:ute)?s?|hour?s?|sec(?:ond)?s?)\s+timer\b",
        r"\bpomodoro\b",
        r"\bremind\s+me\s+in\b",
    ]),
    ("utility_reminder", [
        r"\bremind\s+me\s+to\b",
        r"\badd\s+(?:a\s+)?reminder\b",
        r"\bmy\s+reminders?\b",
        r"\bto.?do\b",
        r"\bremind\s+me\b",   # "remind me" without "to" — bare intent still routes here
    ]),
    ("utility_weather", [
        r"\bweather\b",
        r"\bforecast\b",
        r"\btemperature\b",
        r"\b(?:rain|sunny|cloudy|snow|cold|hot)\s+(?:outside|today|tomorrow)\b",
    ]),
    ("utility_time", [
        r"\bwhat(?:'s|\s+is)\s+the\s+(?:time|date|day)\b",
        r"\bwhat\s+time\s+is\s+it\b",
        r"\btoday(?:'s)?\s+date\b",
    ]),
    ("utility_calendar", [
        r"\b(?:my\s+)?calendar\b",
        r"\bwhat(?:'s|\s+have\s+i\s+got)\s+(?:on\s+)?(?:today|tomorrow|this\s+week)\b",
        r"\bschedule\b",
        r"\bany\s+meetings?\b",
        r"\bcoming\s+up\b",
    ]),
    ("utility_spotify", [
        r"\bplay\s+(?:some\s+|a\s+)?(?:music|song|songs|track|tracks|something)\b",
        r"\bplay\s+.{2,}\s+by\s+\w",             # "play X by Y"
        r"\b(?:play|put\s+on)\s+.+\b(?:podcast|episode)\b",  # "play the Joe Budden Podcast"
        r"\b(?:open|launch|start)\s+spotify\b",
        r"\bspotify\s+(?:play|pause|skip|next|back|stop)\b",
        r"\b(?:skip|next)\s+(?:this|the\s+)?(?:song|track)\b",
        r"\bskip\b",                              # bare skip is almost always music
        r"\bpause\s+(?:the\s+)?(?:song|music|track|this)\b",
        r"\bwhat(?:'s|\s+is)\s+(?:playing|on)\b",
        r"\bnow\s+playing\b",
        r"\bcurrent\s+(?:song|track)\b",
        # volume — music-specific (system volume patterns are in "system" intent above)
        r"\b(?:turn\s+(?:up|down)|lower|raise|increase|decrease)\s+(?:the\s+)?music\b",
        r"\bmusic\s+(?:volume|louder|quieter|softer)\b",
        r"\bspotify\s+volume\b",
        r"\bvolume\s+(?:up|down)\s+(?:a\s+(?:bit|lot)|on\s+spotify)\b",
        # like / save
        r"\b(?:like|love|save|heart)\s+(?:this|the\s+)?(?:song|track|music)\b",
        r"\badd\s+(?:this|the)\s+(?:song|track)\s+to\s+(?:my\s+)?(?:library|liked|favourites?)\b",
        r"\bun(?:like|save|heart)\s+(?:this|the\s+)?(?:song|track)\b",
        # shuffle / repeat
        r"\b(?:turn\s+(?:on|off)|toggle|enable|disable)\s+shuffle\b",
        r"\bshuffle\s+(?:on|off|mode|this)\b",
        r"\b(?:turn\s+(?:on|off)|toggle|enable|disable|set)\s+repeat\b",
        r"\brepeat\s+(?:on|off|this|song|track|album|playlist)\b",
        r"\bloop\s+(?:this|the\s+)?(?:song|track|album)\b",
        # Widget show / hide / toggle
        r"\b(?:show|hide|open|close|toggle)\s+(?:the\s+)?spotify(?:\s+widget)?\b",
        r"\bspotify\s+(?:widget\s+)?(?:show|hide|open|close|toggle)\b",
        r"\b(?:show|hide|open|close)\s+(?:the\s+)?(?:music\s+)?widget\b",
        # Spotify Connect — transfer playback
        r"\bplay\s+(?:this\s+)?(?:on|through|from)\s+(?:my\s+)?(?:iphone|phone|mac|macbook|laptop|computer|tv|speaker|airplay)\b",
        r"\bswitch\s+(?:to|playback\s+to)\s+(?:my\s+)?(?:iphone|phone|mac|macbook|laptop|computer|tv|speaker)\b",
        r"\btransfer\s+(?:playback|music|spotify)\s+to\b",
        r"\bspotify\s+(?:connect|transfer|switch)\b",
        r"\bmove\s+(?:spotify|music|playback)\s+to\b",
    ]),
    ("utility_messages", [
        r"\b(?:send|text)\s+\w",                       # "send [person]", "text [person]"
        r"\bmessage\s+(?:to\s+)?\w{2,}\s+(?:that|saying|to\s+say)\b",  # "message [person] that"
        r"\btell\s+\w+\s+that\b",
        r"\bimessage\b",
    ]),
    ("utility_clipboard", [
        r"\bclipboard\b",
        r"\bwhat\s+(?:did\s+i|have\s+i)\s+cop(?:y|ied)\b",
        r"\bwhat(?:'s|\s+is)\s+copied\b",
    ]),
    ("utility_notes", [
        r"\b(?:make|create|new|add)\s+(?:a\s+)?note\b",
        r"\bapple\s+notes?\b",
    ]),
    ("utility_news", [
        r"\b(?:get|show|give|pull|want|tell\s+me)\s+(?:the\s+)?(?:news|headlines)\b",
        r"\bwhat(?:'s|\s+is)\s+(?:in\s+the\s+)?news\b",
        r"\btoday'?s?\s+(?:news|stories)\b",
        r"\btop\s+(?:stories|headlines)\b",
        r"\bcheck\s+(?:the\s+)?news\b",
    ]),
    ("utility_translate", [
        r"\btranslate\b",
        r"\bhow\s+(?:do\s+you\s+)?say\b",
        r"\bin\s+(?:spanish|french|german|japanese|arabic|portuguese|italian|korean|mandarin|hindi)\b",
    ]),
    ("utility_calculator", [
        r"\b\d[\d\s\+\-\*\/\.\^%]+\d\b",
        r"\bcalculate\b",
        r"\bhow\s+much\s+is\s+[\d(]",
        r"\bwhat(?:'s|\s+is)\s+[\d(]",
    ]),
    ("utility_github", [
        r"\bgithub\b",
        r"\brepo\b",
        r"\bpull\s+request\b",
        r"\blast\s+commit\b",
    ]),
    ("utility_vision", [
        r"\bwhat(?:'s|\s+is)\s+on\s+(?:my\s+)?screen\b",
        r"\bwhat\s+(?:do\s+you\s+see|can\s+you\s+see)\b",
        r"\blook\s+at\s+(?:my\s+)?screen\b",
    ]),
    ("file_read", [
        r"\bread\b.*[~/][\w/.\-]+\.\w+",
        r"\bopen\b.*[~/][\w/.\-]+\.\w+",
        r"\bwhat(?:'s|\s+is)\s+in\s+[~/][\w/.\-]+",
        r"\bread\s+(?:my\s+)?(?:tracker|notes?|brief|script)\b",
    ]),
    ("vault_write", [
        r"\bremember\s+(?:this|that)\b",
        r"\bsave\s+(?:this|that)\b",
        r"\bnote\s+(?:this|that|it|down)\b",
        r"\badd\s+(?:this|that)\s+to\s+(?:my\s+)?(?:vault|memory|notes?)\b",
        r"\bwrite\s+(?:this|that)\s+down\b",
    ]),
    ("draft", [
        r"\b(?:write|draft|compose)\s+(?:a\s+|an\s+)?(?:pitch|email|scene|brief|bio|outline|post|story)\b",
        r"\bbrainstorm\b",
        r"\bhelp\s+me\s+(?:write|draft)\b",
    ]),
    # planning before lookup — otherwise lookup's generic "what is" catches "what's the plan"
    ("planning", [
        r"\bwhat(?:'s|\s+is)\s+(?:the\s+)?(?:plan|next\s+step|first\s+step|move)\b",
        r"\bwhere\s+do\s+(?:i|we)\s+start\b",
        r"\bwhat\s+do\s+(?:i|we)\s+do\s+(?:first|next)\b",
        r"\baction\s+plan\b",
        r"\bhelp\s+me\s+(?:plan|figure\s+out|map\s+out|work\s+out|think\s+through)\b",
        r"\blet(?:'s|\s+us)\s+(?:plan|map\s+out|figure\s+out|think\s+through|work\s+out)\b",
        r"\bplan\s+(?:out|the|this|it)\b",
        r"\bwhat\s+(?:should|do)\s+(?:i|we)\s+(?:do|focus\s+on|build|prioritise|work\s+on)\s+(?:first|next|now)\b",
    ]),
    ("lookup", [
        r"\bwhat(?:'s|\s+is)\s+(?:a\s+|an\s+|the\s+)?\w",
        r"\bwho(?:'s|\s+is)\b",
        r"\btell\s+me\s+about\b",
        r"\bexplain\b",
        r"\bdefine\b",
        r"\blook\s+up\b",
        r"\bsearch\s+(?:for\s+)?\b",
        # WO-INTENT-ACCURACY-001: can-you-explain / walk-me-through phrasings
        r"\bcan\s+you\s+(?:explain|walk\s+me\s+through|break\s+(?:it|that|this)\s+down|help\s+me\s+understand)\b",
        r"\bwalk\s+me\s+through\b",
        r"\bhelp\s+me\s+understand\b",
        r"\bhow\s+does\s+.+\s+work\b",
        r"\bbreak\s+(?:it|that|this)\s+down\b",
    ]),
    ("social", [
        r"^(?:yo|hey|hi|hello|wagwan|wah\s+gwaan|safe|aight|what(?:'s|\s+is)\s+(?:good|the\s+vibe)|you\s+(?:calm|good|alright))[\s\w,!?]*$",
        r"^(?:chilling|just\s+chilling|just\s+vibing|about\s+to\s+\w+|just\s+(?:woke|got|finished))\b",
    ]),
    ("creation", [
        r"\blet(?:'s|\s+us)\s+(?:build|make|create|design)\b",
        r"\bi\s+(?:want|need)\s+to\s+(?:build|make|create|design)\b",
        r"\btime\s+to\s+(?:build|make|ship|launch)\b",
        # WO-INTENT-ACCURACY-001: let's explore / work on / dig into phrasings
        r"\blet(?:'s|\s+us)\s+(?:explore|work\s+on|dig\s+into|look\s+at|get\s+into|start\s+on)\b",
        r"\bi\s+(?:want|need)\s+to\s+(?:explore|work\s+on|dig\s+into|start\s+on)\b",
    ]),
    # WO-INTENT-ACCURACY-001: grounding intent — BEFORE catch-all
    ("ground", [
        r"\bground\s+(?:my)?self\b",
        r"\bi\s+need\s+to\s+(?:ground|breathe|slow\s+down|calm\s+down|settle)\b",
        r"\bfeeling\s+(?:overwhelmed|scattered|anxious|off|lost|stuck)\b",
        r"\bhelp\s+me\s+(?:breathe|ground|settle|calm\s+down|slow\s+down)\b",
        r"\btake\s+a\s+(?:breath|minute|moment|step\s+back)\b",
        r"\bi(?:'m|\s+am)\s+(?:overwhelmed|scattered|anxious|spiralling|spinning)\b",
    ]),
    # SP-16 (WO-NAV-003): spatial navigation intent — BEFORE catch-all
    ("navigation", [
        r"\b(?:go|head|move)\s+to\s+(?:that|the|this)\b",
        r"\bjump\s+to\b",
        r"\bnavigate\s+to\b",
        r"\btake\s+me\s+to\b",
        r"\bgo\s+(?:over\s+)?there\b",
    ]),
    ("conversation", [
        r".*",  # catch-all — always matches
    ]),
]

# ── Multi-agent intent — inputs that explicitly chain two actions ─────────────
_CHAIN_PATTERNS = [
    # "read X then Y", "X and help me Y", "check X and do Y"
    (r"\bread\s+\w.*\bthen\b", ["file_read_or_obsidian", "draft"]),
    (r"\bcheck\s+\w.*\bthen\b", ["file_read_or_obsidian", "draft"]),
    (r"\bnotes?\b.*\bthen\b.*\bhelp\b", ["memory", "draft"]),
]


# ── Vol V Ch.8: five-category system ─────────────────────────────────────────
# Maps specific intents → (Build|Explore|Reflect|Decide|Connect, reason)

_CATEGORY_MAP: dict[str, tuple[str, str]] = {
    "file_ops":           ("Build",   "managing or creating files"),
    "memory":             ("Reflect", "recalling past moments"),
    "system":             ("Decide",  "choosing system settings"),
    "utility_timer":      ("Decide",  "controlling time or task"),
    "utility_reminder":   ("Decide",  "organising what needs doing"),
    "utility_weather":    ("Explore", "seeking information about conditions"),
    "utility_time":       ("Explore", "seeking the current time or date"),
    "utility_calendar":   ("Explore", "checking schedule"),
    "utility_spotify":    ("Connect", "enjoying music together"),
    "utility_messages":   ("Connect", "communicating with others"),
    "utility_clipboard":  ("Build",   "working with content"),
    "utility_notes":      ("Build",   "capturing thoughts"),
    "utility_news":       ("Explore", "staying informed"),
    "utility_translate":  ("Connect", "crossing language barriers"),
    "utility_calculator": ("Decide",  "working out a result"),
    "utility_github":     ("Build",   "working with code projects"),
    "utility_vision":     ("Explore", "seeing and interpreting"),
    "file_read":          ("Explore", "reading and understanding files"),
    "vault_write":        ("Build",   "building knowledge"),
    "draft":              ("Build",   "creating content"),
    "lookup":             ("Explore", "finding information"),
    "social":             ("Connect", "sharing a moment"),
    "planning":           ("Decide",  "charting a path forward"),
    "creation":           ("Build",   "making something new"),
    "ground":             ("Reflect", "grounding and steadying"),
    "navigation":         ("Decide",  "navigating to a destination"),
    "conversation":       ("Connect", "being present together"),
}


def _categorise(intent: str) -> tuple[str, str]:
    """Return (category, reason) for the given intent string."""
    return _CATEGORY_MAP.get(intent, ("Explore", "general curiosity"))


def detect(cleaned: str, session: dict | None = None) -> dict:
    """
    Stage 04 — classify intent from normalised, repaired input.

    Returns:
        intent      — primary intent string
        confidence  — 0.0–1.0
        chain       — optional list of intents for multi-agent (max 2)
        category    — Vol V Ch.8: Build | Explore | Reflect | Decide | Connect
        reason      — one-phrase explanation of the category assignment
    """
    t = cleaned.lower().strip()

    # Multi-agent chain detection
    for pattern, chain in _CHAIN_PATTERNS:
        if re.search(pattern, t):
            cat, reason = _categorise(chain[0])
            return {"intent": chain[0], "confidence": 0.8, "chain": chain,
                    "category": cat, "reason": reason}

    # Single intent — first match wins
    for intent, patterns in _INTENT_PATTERNS:
        for p in patterns:
            if re.search(p, t, re.IGNORECASE):
                confidence = 0.9 if intent != "conversation" else 0.5
                cat, reason = _categorise(intent)
                return {"intent": intent, "confidence": confidence, "chain": [],
                        "category": cat, "reason": reason}

    # WO-LOCAL-LLM-001: ollama fallback for low-confidence classification
    _ollama_result = _ollama_intent_classify(cleaned)
    if _ollama_result:
        cat, reason = _categorise(_ollama_result)
        return {"intent": _ollama_result, "confidence": 0.7, "chain": [],
                "category": cat, "reason": reason}

    cat, reason = _categorise("conversation")
    return {"intent": "conversation", "confidence": 0.5, "chain": [],
            "category": cat, "reason": reason}


def _ollama_intent_classify(user_input: str) -> str | None:
    """
    WO-LOCAL-LLM-001: Ollama fallback for intent classification when regex
    confidence is low. Asks local LLM for a single intent keyword from the
    taxonomy. Returns None on any failure — never raises.
    """
    try:
        import os
        import json
        import urllib.request

        host = os.environ.get("ELO_OLLAMA_HOST", "http://localhost:11434")
        model = os.environ.get("ELO_OLLAMA_MODEL", "llama3.1:8b")

        _known_intents = ", ".join(
            "conversation, question, calculation, reminder, weather, "
            "music, search, code, debug, write, summarise, translate, "
            "image_gen, utility_vision, file_read, vault_write, draft, "
            "lookup, social, planning, creation, navigation".split(", ")
        )

        prompt = (
            f"Classify the user's intent as ONE word from this list: {_known_intents}.\n"
            f"User: {user_input[:200]}\n"
            f"Intent (one word only):"
        )

        body = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 8},
        }).encode()

        req = urllib.request.Request(
            f"{host}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            raw = data.get("response", "").strip().lower().split()[0].rstrip(".,;:")
            # Validate against known intents
            _known = {
                "conversation", "question", "calculation", "reminder", "weather",
                "music", "search", "code", "debug", "write", "summarise", "translate",
                "image_gen", "utility_vision", "file_read", "vault_write", "draft",
                "lookup", "social", "planning", "creation", "navigation",
            }
            return raw if raw in _known else None
    except Exception:
        return None
