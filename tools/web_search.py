"""
tools/web_search.py — Web search for eLo OS via SerpAPI.

One key, multiple engines. eLo picks the right engine automatically
based on what's being asked:

  "find that video"       → YouTube
  "latest news on X"      → Google News
  "find an image of X"    → Google Images
  "look up X"             → Google Web (default)
  "find X on Amazon"      → Amazon
  "where is X"            → Google Maps

Falls back to DuckDuckGo if no key is set.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional

_SERPAPI_KEY = lambda: os.environ.get("SERPAPI_KEY", "")

# WO-051: track which provider last served results so callers can surface fallback.
last_source: str = ""  # "serpapi" | "ddg" | ""

# B3-SEARCH-001: Google's own reading of the last query — knowledge-graph card
# ({"title", "description"}) and spelling fix ("Pinkie" → "Pinky and the Brain").
last_kg: dict = {}
last_spelling_fix: str = ""
# WO-RESEARCH-001: Google's direct answer to a question ("when did …", "how tall …").
last_answer_box: dict = {}


@dataclass
class SearchResult:
    title:   str
    url:     str
    snippet: str


# ── Engine routing ────────────────────────────────────────────────────────────

_ENGINE_TRIGGERS: dict[str, list[str]] = {
    "youtube": [
        "youtube", "find that video", "search youtube", "that video",
        "watch", "find a video", "video of", "video about", "clip of",
        "show me the video", "find the video",
    ],
    "google_news": [
        "latest news", "news on", "news about", "what's happening",
        "recent news", "in the news", "latest on", "breaking",
        "what happened with", "update on",
    ],
    "google_images": [
        "image of", "images of", "picture of", "pictures of",
        "what does it look like", "show me what", "find a photo",
        "find an image", "photo of",
    ],
    "amazon": [
        "amazon", "buy", "how much is", "price of", "find on amazon",
        "where to buy", "purchase",
    ],
    "google_maps": [
        "where is", "directions to", "find near", "near me",
        "address of", "location of", "how far is",
    ],
}


def _detect_engine(text: str) -> str:
    """Return the best SerpAPI engine for this query."""
    t = text.lower()
    for engine, triggers in _ENGINE_TRIGGERS.items():
        if any(tr in t for tr in triggers):
            return engine
    return "google"


def search(query: str, max_results: int = 5, engine: str = "") -> list[SearchResult]:
    """
    Search using the appropriate engine for this query.
    Auto-detects engine from query intent if not specified.
    Falls back to DuckDuckGo if no key or SerpAPI fails.
    Sets last_source to "serpapi" or "ddg" so callers can surface the fallback.
    """
    global last_source, last_kg, last_spelling_fix, last_answer_box
    last_kg, last_spelling_fix, last_answer_box = {}, "", {}
    key = _SERPAPI_KEY()
    if key:
        chosen = engine or _detect_engine(query)
        results = _serp_search(query, key, max_results, engine=chosen)
        if results:
            last_source = "serpapi"
            return results
    last_source = "ddg"
    return _ddg_search(query, max_results)


def _serp_search(query: str, key: str, max_results: int, engine: str = "google") -> list[SearchResult]:
    try:
        import httpx
        params: dict = {
            "q":       query,
            "api_key": key,
            "engine":  engine,
            "hl":      "en",
            "gl":      "gb",
        }
        if engine == "google":
            params["num"] = max_results
        elif engine == "youtube":
            params["search_query"] = query
            del params["q"]
        elif engine == "amazon":
            params["amazon_domain"] = "amazon.co.uk"

        resp = httpx.get("https://serpapi.com/search.json", params=params, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()

        global last_kg, last_spelling_fix, last_answer_box
        _ab = data.get("answer_box") or {}
        last_answer_box = {
            "answer":  str(_ab.get("answer") or _ab.get("result") or ""),
            "snippet": str(_ab.get("snippet") or ""),
            "title":   str(_ab.get("title") or ""),
            "link":    str(_ab.get("link") or ""),
        } if _ab else {}
        _kg = data.get("knowledge_graph") or {}
        last_kg = {"title": _kg.get("title", ""), "description": _kg.get("description", "")} if _kg else {}
        _si = data.get("search_information") or {}
        last_spelling_fix = (_si.get("spelling_fix") or _si.get("showing_results_for") or "").strip('"')

        # Each engine returns results under a different key
        items = (
            data.get("organic_results")          # google
            or data.get("video_results")         # youtube
            or data.get("news_results")          # google_news
            or data.get("images_results")        # google_images
            or data.get("organic_results", [])   # amazon, maps
        ) or []

        results: list[SearchResult] = []
        for r in items[:max_results]:
            title   = r.get("title", "") or r.get("name", "")
            url     = r.get("link", "") or r.get("url", "") or r.get("thumbnail", "")
            snippet = (
                r.get("snippet", "")
                or r.get("description", "")
                or r.get("published_date", "")
                or r.get("duration", "")
            )
            if title:
                results.append(SearchResult(title=title, url=url, snippet=snippet))
        return results

    except Exception as e:
        import sys
        print(f"[web_search] SerpAPI ({engine}) failed: {e}", file=sys.stderr)
        return []


def _ddg_search(query: str, max_results: int) -> list[SearchResult]:
    """DuckDuckGo instant answers — no API key, limited but always available."""
    try:
        import httpx
        resp = httpx.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=8.0,
        )
        resp.raise_for_status()
        data    = resp.json()
        results: list[SearchResult] = []

        # Abstract (main answer)
        if data.get("AbstractText"):
            results.append(SearchResult(
                title=   data.get("Heading", query),
                url=     data.get("AbstractURL", ""),
                snippet= data["AbstractText"][:300],
            ))

        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(SearchResult(
                    title=   topic.get("Text", "")[:60],
                    url=     topic.get("FirstURL", ""),
                    snippet= topic.get("Text", "")[:200],
                ))
            if len(results) >= max_results:
                break

        return results
    except Exception as e:
        import sys
        print(f"[web_search] DDG failed: {e}", file=sys.stderr)
        return []


def format_for_context(results: list[SearchResult], max_chars: int = 800) -> str:
    """Format results as a compact context block for injection into system prompt."""
    if not results:
        return ""
    lines = ["[WEB_SEARCH_RESULTS]"]
    total = 0
    for r in results:
        entry = f"• {r.title}: {r.snippet}"
        if total + len(entry) > max_chars:
            break
        lines.append(entry)
        total += len(entry)
    return "\n".join(lines)


# ── Intent detection ──────────────────────────────────────────────────────────

_SEARCH_TRIGGERS = (
    "search for",
    "look that up",
    "look up",
    "find out",
    "what is ",
    "who is ",
    "when did ",
    "how does ",
    "can you search",
    "google that",
    "research that",
    "research ",
    "find me info",
    "find info",
    "what's the latest",
    "latest on ",
    "news on ",
    "find out about",
    "find that video",
    "search youtube",
    "find a video",
    "latest news",
    "find an image",
    "find a photo",
    "where to buy",
    "how much is",
    "where is ",
    # P0-WEBSEARCH: explicit search instructions David uses that were missing
    "websearch",
    "web search",
    "do a search",
    "do a websearch",
    "read up about",
    "get a summary",
    "look it up",
    "search it up",
    "search that up",
    "look that up about",
    "find out more about",
    "find out more",
    "summarise that",
    "summarize that",
    "get info on",
    "look into that",
    "look into ",
)


def is_search_intent(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in _SEARCH_TRIGGERS)


def extract_query(text: str) -> str:
    """Pull the search term out of a natural language request."""
    t = text.strip()
    for trigger in sorted(_SEARCH_TRIGGERS, key=len, reverse=True):
        if trigger in t.lower():
            idx = t.lower().index(trigger) + len(trigger)
            q = t[idx:].strip().strip("?.,!")
            if q:
                return q
    return t


# ── B3-SEARCH-001: SEARCH_INTENT — David tells eLo to look something up ─────────
#
# Source: docs/architecture/_intake/SOURCE_2026-10-05_DAVID_pinkie_brain_chat_log.md
# "You'd have to do a websearch to read up about it" matched none of the
# _SEARCH_TRIGGERS above, and "it" pointed at the previous turn. An explicit
# instruction is a command, not a question: eLo searches, then says what he
# found — built from the source text, so every detail is the source's.

_SEARCH_COMMAND_RE = re.compile(
    r"\b(?:"
    r"do\s+(?:a|an)\s+(?:quick\s+)?(?:web\s*|internet\s+|online\s+|google\s+)?search"
    r"|web\s*search(?:ed|ing)?"
    r"|search\s+(?:the\s+web|online|the\s+internet|for|it|that|this)"
    r"|look\s+(?:it|that|this|them|him|her)\s+up"
    r"|look\s+up"
    r"|google\s+(?:it|that|this)"
    r"|read\s+up\s+(?:on|about)"
    r"|find\s+out\s+(?:about|what)"
    r"|get\s+(?:a|me\s+a)\s+summary"
    r"|check\s+online"
    r")\b",
    re.IGNORECASE,
)

# Words that never name a topic on their own — "read up about it", "a summary
# from somewhere to understand it more".
_VAGUE_WORDS = frozenset("""
it that this them him her there these those somewhere something anything
more about on for up of from to the a an and or understand learn know read
summary info information bit little maybe please me quick quickly some
what is was online web internet google search it's
""".split())

_LEADING_FILLER_RE = re.compile(r"^(?:(?:on|about|for|of|up|from|into)\s+)+", re.IGNORECASE)
_TRAILING_FILLER_RE = re.compile(
    r"\s+(?:for\s+me|please|from\s+somewhere|online|on\s+the\s+web|to\s+understand.*|so\s+.*)$",
    re.IGNORECASE,
)
_REFERENCE_RE = re.compile(
    r"\b(?:it'?s|that'?s|this\s+is|was)\s+(?:a|an|the)\s+(.+?)\s+(?:reference|joke|bit|quote|line)\b",
    re.IGNORECASE,
)
_CONNECTORS = r"(?:and|the|of|&|de|la|von|van|in|on)"
_PROPER_SPAN_RE = re.compile(
    r"\b([A-Z][\w'\-]*(?:\s+(?:" + _CONNECTORS + r"\s+)*[A-Z][\w'\-]*)*)"
)
_NOT_PROPER = frozenset({"i", "i'm", "i'd", "i'll", "eLo".lower(), "you", "you'd", "maybe", "same",
                         "it's", "it", "that", "this", "ok", "okay", "yeah", "yo", "so", "and"})


def is_search_command(text: str) -> bool:
    """True when David explicitly tells eLo to search / look something up."""
    return bool(_SEARCH_COMMAND_RE.search(text or ""))


def _is_vague(topic: str) -> bool:
    words = re.findall(r"[a-zA-Z0-9']+", topic.lower())
    return not any(w not in _VAGUE_WORDS for w in words)


def _topic_from_command(text: str) -> str:
    """Topic named in the command itself — text after the last trigger."""
    last = None
    for m in _SEARCH_COMMAND_RE.finditer(text):
        last = m
    if not last:
        return ""
    tail = text[last.end():]
    tail = re.split(r"[.?!\n]", tail, maxsplit=1)[0]
    tail = _LEADING_FILLER_RE.sub("", tail.strip())
    tail = _TRAILING_FILLER_RE.sub("", tail).strip(" ,;:'\"")
    return "" if _is_vague(tail) else tail


def _topic_from_text(text: str) -> str:
    """Best named topic in one utterance: "It's a X reference" first, then the
    longest capitalised span (sentence-initial single words don't count)."""
    m = _REFERENCE_RE.search(text)
    if m and not _is_vague(m.group(1)):
        return m.group(1).strip()
    best = ""
    for sm in _PROPER_SPAN_RE.finditer(text):
        span = sm.group(1).strip()
        words = span.split()
        if len(words) == 1:
            if span.lower() in _NOT_PROPER:
                continue
            before = text[:sm.start()].rstrip()
            if not before or before[-1] in ".?!\n":
                continue  # sentence-initial capital, not a name
        if len(span) > len(best):
            best = span
    return best


# Every turn's raw input, oldest first — fed by server.py at turn start, so
# early-return turns count and a few interleaved turns don't push the topic
# out of reach (tracker / _last_inputs only look back three).
_recent_inputs: list[str] = []
_RECENT_MAX = 8


def note_input(text: str) -> None:
    _recent_inputs.append(text or "")
    if len(_recent_inputs) > _RECENT_MAX:
        _recent_inputs.pop(0)


def resolve_search_topic(text: str, recent_user_turns: list[str] | None = None) -> str:
    """What David wants looked up. The command's own object if it names one;
    otherwise the topic of this message's other sentences, then of recent
    turns (most recent first). A bare name that a longer recent topic
    contains resolves to the longer one ("Pinkie" → "Pinkie and the Brain").
    "" when nothing names a topic."""
    topic = _topic_from_command(text)
    if topic:
        return topic
    candidates: list[str] = []
    for sentence in re.split(r"(?<=[.?!])\s+|\n+", text):
        if not is_search_command(sentence):
            t = _topic_from_text(sentence)
            if t:
                candidates.append(t)
    history = list(recent_user_turns or [])
    if _recent_inputs and _recent_inputs[-1] == text:
        history += _recent_inputs[:-1]
    else:
        history += _recent_inputs
    seen = set()
    for turn in reversed(history):
        if turn in seen or turn == text:
            continue
        seen.add(turn)
        t = _topic_from_text(turn or "")
        if t:
            candidates.append(t)
    if not candidates:
        return ""
    best = candidates[0]
    for c in candidates[1:]:
        if len(c) > len(best) and best.lower() in c.lower():
            best = c
    return best


_STOP = frozenset("the a an and of in on for to is are was what who how".split())


def _content_words(q: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", q.lower()) if w not in _STOP and len(w) > 2]


def _relevant(r: SearchResult, words: list[str]) -> bool:
    if not words:
        return True
    hay = f"{r.title} {r.snippet}".lower()
    need = max(1, -(-len(words) * 2 // 3))
    return sum(1 for w in words if w in hay) >= need


def wiki_summary(name: str) -> SearchResult | None:
    """Wikipedia's lead summary for a canonical name — the encyclopedic answer
    to "read up about it". Free, no key. None when there is no article."""
    try:
        import httpx, sys, time
        from urllib.parse import quote
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(name.replace(" ", "_"))
        for attempt in (1, 2):
            resp = httpx.get(
                url, headers={"User-Agent": "eLo-OS/1.0 (DISENELO; local companion)"},
                timeout=6.0, follow_redirects=True,
            )
            if resp.status_code == 429 or resp.status_code >= 500:
                print(f"[web_search] wikipedia {resp.status_code} for {name!r} (attempt {attempt})",
                      file=sys.stderr)
                time.sleep(1.0)
                continue
            break
        if resp.status_code != 200:
            if resp.status_code != 404:
                print(f"[web_search] wikipedia {resp.status_code} for {name!r}", file=sys.stderr)
            return None
        data = resp.json()
        if data.get("type") == "disambiguation" or not data.get("extract"):
            return None
        return SearchResult(
            title=data.get("title", name),
            url=(data.get("content_urls", {}).get("desktop", {}) or {}).get("page", ""),
            snippet=data["extract"],
        )
    except Exception as e:
        import sys
        print(f"[web_search] wikipedia failed: {e}", file=sys.stderr)
        return None


# Music asks ("Jitwam Radio playlist on Spotify") — live 2026-10-05 a generic
# Google hit about a ring with 540 likes was read out as the answer. A music
# topic only counts results that are about music.
_MUSIC_TOPIC_RE = re.compile(r"\b(?:spotify|playlist|album|song|track|artist|soundtrack|radio|ep|mixtape|dj)\b", re.I)
_MUSIC_RESULT_RE = re.compile(r"\b(?:spotify|playlist|music|artist|album|song|track|dj|soundcloud|bandcamp|apple\s+music|radio)\b", re.I)


def search_topic(topic: str, max_results: int = 5) -> tuple[str, list[SearchResult]]:
    """Search for a topic and return (canonical_name, relevant_results).
    Google's spelling fix names the topic; when no result is about it,
    retry once with the phrase quoted (gl=gb on an unquoted show title has
    returned brain-science pages — 2026-10-05)."""
    results = search(topic, max_results=max_results, engine="google")
    name = last_kg.get("title") or last_spelling_fix or topic
    words = _content_words(name)
    rel = [r for r in results if _relevant(r, words)]
    if not rel and not last_kg:
        results = search(f'"{name}"', max_results=max_results, engine="google")
        name = last_kg.get("title") or name
        words = _content_words(name)
        rel = [r for r in results if _relevant(r, words)]
    if _MUSIC_TOPIC_RE.search(topic):
        rel = [r for r in rel if _MUSIC_RESULT_RE.search(f"{r.title} {r.snippet} {r.url}")]
        return name, rel
    # Wikipedia under each name Google gave us; its title is the cleanest
    # display name ("Camberwell College of Arts", not the KG's
    # "University of the Arts London, Camberwell College of Arts").
    for cand in dict.fromkeys(n for n in (last_spelling_fix, topic, name,
                                          re.sub(r"^the\s+", "", topic, flags=re.I)) if n):
        wiki = wiki_summary(cand)
        if wiki:
            return wiki.title, [wiki] + rel
    return ((last_spelling_fix or topic) if "," in name else name), rel


_PROMO_START_RE = re.compile(
    r"^(?:listen|watch|stream|buy|shop|subscribe|download|sign\s+up|tune\s+in(?:to)?|follow|click|"
    r"read\s+more|learn\s+more|find\s+out|discover|get|order|see|check\s+out)\b",
    re.IGNORECASE,
)
_PROMO_ANY_RE = re.compile(r"\b(?:invites\s+you|learn\s+more|click\s+here|\d+\s+likes?|\d+\s+comments?|"
                           r"find\s+out\s+more|sign\s+up|subscribe|book\s+now|buy\s+now)\b",
                           re.IGNORECASE)

# What eLo has already told David per topic, so "tell me more" brings the next
# finding instead of a verbatim repeat (elo_response_gate suppresses repeats —
# live 2026-10-05 the second Pinky request came back as a lesson string / silence).
_said: dict[str, set[str]] = {}


_ABBR = frozenset("mr mrs ms dr st jr sr vs etc no co inc ltd mt ft approx est fig e.g i.e u.s u.k".split())
# Social / forum hosts: a post is somebody's opinion, not a finding.
_SOCIAL_HOSTS = ("facebook.com", "instagram.com", "tiktok.com", "twitter.com", "x.com",
                 "pinterest.", "threads.net", "linkedin.com", "quora.com")
_FIRST_PERSON_RE = re.compile(r"\b(?:I|I've|I'm|I'd|my|me|we've)\b")


def _sentences(snippet: str) -> list[str]:
    """Complete sentences from a snippet; a trailing "..." fragment is dropped.
    Initials and abbreviations don't end a sentence ("Rudolf E. Kálmán")."""
    s = re.sub(r"\s+", " ", snippet or "").strip()
    s = re.sub(r"^[A-Z][a-z]{2} \d{1,2}, \d{4}\s*[—–-]\s*", "", s)  # "Oct 5, 2026 — "
    out, start = [], 0
    for m in re.finditer(r"[.!?](?=\s|$)", s):
        before = s[start:m.start()].split()
        last = before[-1].lower().rstrip(".") if before else ""
        if m.group() == "." and (re.fullmatch(r"[a-z]", last) or last in _ABBR):
            continue
        sent = s[start:m.end()].strip()
        start = m.end()
        if sent.endswith("...") or len(sent) < 25 or not re.match(r"[A-Z0-9\"'“‘(]", sent):
            continue
        out.append(sent)
    return out


def _usable_source(url: str) -> bool:
    return not any(h in (url or "") for h in _SOCIAL_HOSTS)


def _key(sentence: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", sentence.lower()).strip()[:60]


# WO-RESEARCH-001: what the last compose_found said, sentence by sentence,
# with the source each came from — read by tools/research.py for the ledger.
last_picks: list[tuple[str, str]] = []   # (sentence, source url | "google:knowledge_graph")


def source_label(url: str) -> str:
    """How eLo names a source out loud: "Wikipedia", "Google", else the site."""
    if not url:
        return "the web"
    if url.startswith("google:"):
        return "Google"
    host = re.sub(r"^https?://(?:www\.|en\.|m\.)?", "", url).split("/")[0]
    named = {"wikipedia.org": "Wikipedia", "britannica.com": "Britannica", "imdb.com": "IMDb",
             "bbc.co.uk": "the BBC", "bbc.com": "the BBC", "nasa.gov": "NASA"}
    for k, v in named.items():
        if host.endswith(k):
            return v
    return host


def compose_found(name: str, results: list[SearchResult]) -> str:
    """eLo's spoken report of what he found. Every clause is lifted from the
    source text; only the lead-in is his, and it names where it came from
    (WO-RESEARCH-001: retrieved, never passed off as his own knowledge).
    Wikipedia's lead first, then "<name> is/are …" sentences, then Google's
    own description, then other on-topic sentences. Promo and social copy are
    skipped. A follow-up on the same topic gives the next findings, never a
    repeat."""
    global last_picks
    words = _content_words(name)
    said = _said.setdefault(name.lower(), set())
    first_time = not said

    encyclopedic, defining, other = [], [], []
    for r in results:
        if "wikipedia.org" in (r.url or ""):
            encyclopedic += [(s, r.url) for s in _sentences(r.snippet)]
            continue
        if not _usable_source(r.url):
            continue
        for sent in _sentences(r.snippet):
            low = sent.lower()
            if _PROMO_START_RE.match(sent) or _PROMO_ANY_RE.search(sent) or not any(w in low for w in words):
                continue
            if _FIRST_PERSON_RE.search(sent):
                continue
            if re.match(r"^(?:the\s+)?" + re.escape(name.lower()) + r"\s+(?:is|are|was|were)\b", low):
                defining.append((sent, r.url))
            else:
                other.append((sent, r.url))
    kg = (last_kg.get("description") or "").strip()
    if kg and not kg.endswith((".", "!", "?")):
        kg += "."
    ordered = encyclopedic + defining + ([(kg, "google:knowledge_graph")] if kg else []) + other

    picked, keys = [], set()
    for sent, src in ordered:
        k = _key(sent)
        if k in said or k in keys:
            continue
        picked.append((sent, src))
        keys.add(k)
        if len(picked) == 2:
            break

    last_picks = picked
    if not picked:
        if first_time:
            return ""
        return f"That's everything solid I found on {name} — nothing new past what I told you."
    said.update(keys)
    labels = list(dict.fromkeys(source_label(src) for _, src in picked))
    where = " and ".join(labels)
    lead = f"Looked it up on {where} —" if first_time else f"More on {name}, from {where} —"
    return " ".join([lead] + [sent for sent, _ in picked])


def lookup(topic: str) -> dict:
    """B3 result standard: {success, result: {name, line, sources, provider}, error}.
    One call for the explicit-search path; recorded for the execution gate."""
    from tools.capability_status import tool_result, record_result
    try:
        name, results = search_topic(topic, max_results=5)
        line = compose_found(name, results)
        ok = bool(line)
        return record_result("web_search", tool_result(ok, {
            "name": name, "line": line or f"Searched {name} — nothing solid came back.",
            "sources": [src for _, src in last_picks], "provider": last_source,
            "results": results,
        }, None if ok else "no relevant results"))
    except Exception as e:
        return record_result("web_search", tool_result(False, {
            "name": topic, "line": f"Searched {topic} — the search itself failed.", "sources": [],
            "provider": last_source, "results": [],
        }, f"{type(e).__name__}: {e}"))
