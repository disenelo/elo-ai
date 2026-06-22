"""
runtime/backend_router.py — eLo OS backend routing layer.

Routes requests between local (Ollama) and cloud (Groq / Gemini / OpenAI) backends.
Falls back to mock when nothing is available.

Priority (auto mode):
    OpenAI → Gemini → Claude → Groq → Ollama → Mock

Routing mode set via ELO_BACKEND env var:
    export ELO_BACKEND=auto    (default)
    export ELO_BACKEND=cloud   (cloud only — OpenAI → Gemini → Claude → Groq)
    export ELO_BACKEND=local   (Ollama only)
    export ELO_BACKEND=mock    (testing)

Models:
    OpenAI:  gpt-4o-mini (default — set ELO_OPENAI_MODEL to override)
    Gemini:  gemini-1.5-flash (default — set ELO_GEMINI_MODEL to override)
             Requires GOOGLE_API_KEY from Google AI Studio (free: 1500 req/day)
    Groq:    llama-3.3-70b-versatile (quality, default)
             llama-3.1-8b-instant    (fast — set ELO_GROQ_MODEL=llama-3.1-8b-instant)
    Ollama:  mistral (default — set ELO_OLLAMA_MODEL to override)
"""

from __future__ import annotations
import os
import re
import logging

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())
_logger.propagate = False

# ── routing thresholds ─────────────────────────────────────────────────────────
_AUTO_LOCAL_MAX_CHARS = 80   # inputs under this → Ollama (fast local)
                              # inputs over this  → Groq (deeper reasoning)


# ── response normaliser ────────────────────────────────────────────────────────

_AI_PREAMBLES = [
    r"^as an ai\b",
    r"^as a language model\b",
    r"^i am an ai\b",
    r"^i'm an ai\b",
    r"^certainly[,!]?\s",
    r"^of course[,!]?\s",
    r"^sure[,!]?\s*here",
    r"^great question[.!]?\s",
    r"^absolutely[,!]?\s",
]

# World lore terms that should not appear in responses unless the user asked about them
_WORLD_LORE_TERMS = [
    "sugarcore", "jellydrop", "dessert desert", "gummy lands",
    "ice cream mountain", "chocolate mountain", "cyber garden",
    "orb system", "the orb", "world stage", "k-7", "k7",
]


def _has_lore_drift(response: str, user_input: str) -> bool:
    """True if the response introduced world lore the user didn't mention."""
    r = response.lower()
    u = user_input.lower()
    return any(term in r and term not in u for term in _WORLD_LORE_TERMS)


def _is_duplicate(new: str, prev: str, threshold: float = 0.75) -> bool:
    """True if new response is too similar to the previous one."""
    if not prev or not new:
        return False
    n, p = new.lower().strip(), prev.lower().strip()
    if n == p:
        return True
    # simple overlap: shared words / total unique words
    nw, pw = set(n.split()), set(p.split())
    if not nw or not pw:
        return False
    overlap = len(nw & pw) / max(len(nw), len(pw))
    return overlap >= threshold


# per-action last-response tracker (session-scoped, in-process)
_last_responses: dict[str, str] = {}

# singleton mock backend — preserves anti-repetition buffer across all mock calls this session
_mock_backend_instance = None

def _strip_trailing_question(text: str) -> str:
    """Remove trailing question sentence(s). Returns empty string if all sentences are questions."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    while sentences and sentences[-1].strip().endswith('?'):
        sentences.pop()
    return ' '.join(sentences).strip()


def normalise(text: str, max_sentences: int = 4) -> str:
    """
    Normalise LLM output to eLo voice standards.

    - Strip AI-assistant preambles
    - Cap to max_sentences
    - Trim whitespace
    - Preserve natural sentence endings
    """
    if not text:
        return text

    text = text.strip()

    # remove AI preambles
    for pattern in _AI_PREAMBLES:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()

    # cap to max_sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) > max_sentences:
        text = " ".join(sentences[:max_sentences])

    return text.strip()


# ── backend calls ──────────────────────────────────────────────────────────────

def _groq_call(system_prompt: str, user_input: str, model: str = None) -> str:
    """Call Groq cloud inference."""
    from groq import Groq
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")
    model = model or os.environ.get("ELO_GROQ_MODEL", "llama-3.3-70b-versatile")
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_input},
        ],
        max_tokens=512,
    )
    return response.choices[0].message.content.strip()


def _ollama_call(system_prompt: str, user_input: str) -> str:
    """Call local Ollama instance."""
    import requests
    host  = os.environ.get("ELO_OLLAMA_HOST",  "http://localhost:11434").rstrip("/")
    model = os.environ.get("ELO_OLLAMA_MODEL", "mistral")
    payload = {
        "model":    model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_input},
        ],
        "stream":  False,
        "options": {"temperature": 0.7, "num_predict": 256},
    }
    r = requests.post(f"{host}/api/chat", json=payload, timeout=60)
    r.raise_for_status()
    return r.json().get("message", {}).get("content", "").strip()


def _openai_available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", ""))


def _openai_call(system_prompt: str, user_input: str) -> str:
    """Call OpenAI GPT-4o-mini."""
    import httpx
    api_key = os.environ.get("OPENAI_API_KEY", "")
    model   = os.environ.get("ELO_OPENAI_MODEL", "gpt-4o-mini")
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        json={
            "model":    model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_input},
            ],
            "max_tokens":  512,
            "temperature": 0.7,
        },
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type":  "application/json"},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _ollama_available() -> bool:
    try:
        import requests
        r = requests.get(
            os.environ.get("ELO_OLLAMA_HOST", "http://localhost:11434").rstrip("/") + "/api/tags",
            timeout=2
        )
        return r.status_code == 200
    except Exception:
        return False


def _groq_available() -> bool:
    return bool(os.environ.get("GROQ_API_KEY", ""))


def _gemini_available() -> bool:
    return bool(os.environ.get("GOOGLE_API_KEY", ""))


def _gemini_call(system_prompt: str, user_input: str) -> str:
    """Call Google Gemini Flash via AI Studio REST API (no SDK — httpx only)."""
    import httpx
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    model   = os.environ.get("ELO_GEMINI_MODEL", "gemini-1.5-flash")
    url     = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_input}]}],
        "generationConfig": {"maxOutputTokens": 512, "temperature": 0.7},
    }
    resp = httpx.post(url, json=payload, params={"key": api_key}, timeout=30.0)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def _claude_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY", ""))


def _claude_call(system_prompt: str, user_input: str) -> str:
    """Call Anthropic Claude."""
    import anthropic
    api_key = os.environ["ANTHROPIC_API_KEY"]
    client  = anthropic.Anthropic(api_key=api_key)
    # smoke-test: if key is invalid this raises immediately
    msg = client.messages.create(
        model      = os.environ.get("ELO_MODEL", "claude-sonnet-4-5"),
        max_tokens = 512,
        system     = system_prompt,
        messages   = [{"role": "user", "content": user_input}],
    )
    return msg.content[0].text.strip()


# ── public router ──────────────────────────────────────────────────────────────

def route(
    system_prompt: str,
    user_input:    str,
    mode:          str = None,
    max_sentences: int = 4,
    action:        str = "",
) -> tuple[str, str]:
    """
    Route a request to the appropriate backend.

    Args:
        system_prompt: Full assembled system prompt from prompt_builder.
        user_input:    Raw user message.
        mode:          'auto' | 'local' | 'cloud' | 'mock' | None (reads ELO_BACKEND).
        max_sentences: Max sentences for response normaliser.

    Returns:
        (response_text, backend_name)
    """
    _env_mode = os.environ.get("ELO_BACKEND", "")
    _any_cloud = _openai_available() or _gemini_available() or _groq_available() or _claude_available()
    if not _env_mode and not _any_cloud:
        # no API keys and no explicit backend set — go offline immediately
        _env_mode = "local"
    mode = mode or _env_mode or "auto"

    # explicit mode overrides
    if mode == "mock":
        return _mock_fallback(user_input), "mock"

    if mode == "local":
        if _ollama_available():
            try:
                raw = _ollama_call(system_prompt, user_input)
                return normalise(raw, max_sentences), "ollama"
            except Exception as e:
                _logger.warning("Ollama failed: %s", e)
        return _mock_fallback(user_input), "mock"

    if mode == "cloud":
        # cloud mode: OpenAI → Gemini → Claude → Groq → Mock
        if _openai_available():
            try:
                raw = _openai_call(system_prompt, user_input)
                return normalise(raw, max_sentences), "openai"
            except Exception as e:
                _logger.warning("OpenAI failed: %s", e)
        if _gemini_available():
            try:
                raw = _gemini_call(system_prompt, user_input)
                return normalise(raw, max_sentences), "gemini"
            except Exception as e:
                _logger.warning("Gemini failed: %s", e)
        if _claude_available():
            try:
                raw = _claude_call(system_prompt, user_input)
                return normalise(raw, max_sentences), "claude"
            except Exception as e:
                _logger.warning("Claude failed: %s", e)
        if _groq_available():
            try:
                raw = _groq_call(system_prompt, user_input)
                return normalise(raw, max_sentences), "groq"
            except Exception as e:
                _logger.warning("Groq failed: %s", e)
        return _mock_fallback(user_input), "mock"

    # auto mode: OpenAI → Gemini → Claude → Groq → Ollama → Mock
    if _openai_available():
        try:
            raw = _openai_call(system_prompt, user_input)
            if _has_lore_drift(raw, user_input):
                _logger.debug("Lore drift in OpenAI response — falling back")
            else:
                normalised = normalise(raw, max_sentences)
                if action in ("build", "celebrate"):
                    normalised = _strip_trailing_question(normalised) or normalised
                if not _is_duplicate(normalised, _last_responses.get(action, "")):
                    _last_responses[action] = normalised
                    return normalised, "openai"
        except Exception as e:
            _logger.warning("OpenAI failed, trying Gemini: %s", e)

    if _gemini_available():
        try:
            raw = _gemini_call(system_prompt, user_input)
            if _has_lore_drift(raw, user_input):
                _logger.debug("Lore drift in Gemini response — falling back")
            else:
                normalised = normalise(raw, max_sentences)
                if action in ("build", "celebrate"):
                    normalised = _strip_trailing_question(normalised) or normalised
                if not _is_duplicate(normalised, _last_responses.get(action, "")):
                    _last_responses[action] = normalised
                    return normalised, "gemini"
        except Exception as e:
            _logger.warning("Gemini failed, trying Claude: %s", e)

    if _claude_available():
        try:
            raw = _claude_call(system_prompt, user_input)
            return normalise(raw, max_sentences), "claude"
        except Exception as e:
            _logger.warning("Claude failed, trying Groq: %s", e)

    if _groq_available():
        _ulen = len(user_input.strip())
        # < 30 chars → mock always (Groq misparses short statements, over-expands affirmations)
        if _ulen < 30:
            return _mock_fallback(user_input, action=action), "mock"
        # BUILD/CELEBRATE < 60 chars → mock (8b model adds questions, breaks on short insights)
        if action in ("build", "celebrate") and _ulen < 60:
            return _mock_fallback(user_input, action=action), "mock"

        try:
            raw = _groq_call(system_prompt, user_input)
            # catch lore drift — replace with mock using the original action
            if _has_lore_drift(raw, user_input):
                _logger.debug("Lore drift detected — replacing with mock fallback")
                return _mock_fallback(user_input, action=action), "mock"
            normalised = normalise(raw, max_sentences)
            # for BUILD/CELEBRATE: strip any trailing questions Groq added
            if action in ("build", "celebrate"):
                stripped = _strip_trailing_question(normalised)
                if not stripped:
                    _logger.debug("Trailing question stripped to empty — using mock")
                    return _mock_fallback(user_input, action=action), "mock"
                normalised = stripped
            # catch duplicate — if too similar to last response, use mock
            if _is_duplicate(normalised, _last_responses.get(action, "")):
                _logger.debug("Duplicate response detected — replacing with mock fallback")
                _last_responses[action] = ""   # reset so next call is fresh
                return _mock_fallback(user_input, action=action), "mock"
            _last_responses[action] = normalised
            return normalised, "groq"
        except Exception as e:
            _logger.warning("Groq failed, trying Ollama: %s", e)

    if _ollama_available():
        try:
            raw = _ollama_call(system_prompt, user_input)
            return normalise(raw, max_sentences), "ollama"
        except Exception as e:
            _logger.warning("Ollama failed, falling to mock: %s", e)

    return _mock_fallback(user_input), "mock"


def _mock_fallback(user_input: str, action: str = "") -> str:
    global _mock_backend_instance
    from backends.mock_backend import MockBackend
    from core.attention import compute
    from runtime.executive import decide as exec_decide
    if _mock_backend_instance is None:
        _mock_backend_instance = MockBackend()
    m = _mock_backend_instance
    if action:
        return m.generate_response(user_input, action, {}, {}, {}, {})["response_text"]
    att  = compute(user_input, {}, {})
    ex   = exec_decide(att, user_input=user_input)
    mode = ex.get("action", ex.get("tone", "reflect"))
    return m.generate_response(user_input, mode, {}, {}, {}, {})["response_text"]


def active_backend() -> str:
    """Return the name of the highest-priority backend currently available."""
    _env_mode = os.environ.get("ELO_BACKEND", "")
    if not _env_mode and not _groq_available() and not _claude_available():
        _env_mode = "local"   # no keys → go offline
    mode = _env_mode or "auto"
    if mode == "mock":   return "mock"
    if mode == "local":  return "ollama" if _ollama_available() else "mock"
    if mode == "cloud":
        if _openai_available():  return "openai"
        if _gemini_available():  return "gemini"
        if _claude_available():  return "claude"
        return "groq" if _groq_available() else "mock"
    # auto: OpenAI → Gemini → Claude → Groq → Ollama → Mock
    if _openai_available():  return "openai"
    if _gemini_available():  return "gemini"
    if _claude_available():  return "claude"
    if _groq_available():    return "groq"
    if _ollama_available():  return "ollama"
    return "mock"
