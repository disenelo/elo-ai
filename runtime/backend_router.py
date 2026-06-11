"""
runtime/backend_router.py — eLo OS backend routing layer.

Routes requests between local (Ollama) and cloud (Groq) backends.
Falls back to mock when neither is available.

Priority:
    auto mode  → Groq for deep reasoning (>80 chars), Ollama for short responses
    local mode → Ollama only
    cloud mode → Groq only
    mock mode  → deterministic mock (always available)

Routing mode set via ELO_BACKEND env var:
    export ELO_BACKEND=auto    (default)
    export ELO_BACKEND=cloud   (Groq only)
    export ELO_BACKEND=local   (Ollama only)
    export ELO_BACKEND=mock    (testing)

Models:
    Groq:   llama-3.1-70b-versatile (quality, default)
            llama-3.1-8b-instant    (fast testing — set ELO_GROQ_MODEL=llama-3.1-8b-instant)
    Ollama: mistral (default — set ELO_OLLAMA_MODEL to override)
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
    mode = mode or os.environ.get("ELO_BACKEND", "auto")

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
        # cloud mode: Claude first, Groq fallback
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

    # auto mode: Claude → Groq → Ollama → Mock
    # Every input goes through the best available backend — no length split.
    if _claude_available():
        try:
            raw = _claude_call(system_prompt, user_input)
            return normalise(raw, max_sentences), "claude"
        except Exception as e:
            _logger.warning("Claude failed, trying Groq: %s", e)

    if _groq_available():
        # short affirmations / < 25 chars → mock has precise pools, Groq over-expands
        if len(user_input.strip()) < 25:
            return _mock_fallback(user_input, action=action), "mock"

        try:
            raw = _groq_call(system_prompt, user_input)
            # catch lore drift — replace with mock using the original action
            if _has_lore_drift(raw, user_input):
                _logger.debug("Lore drift detected — replacing with mock fallback")
                return _mock_fallback(user_input, action=action), "mock"
            normalised = normalise(raw, max_sentences)
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
    from backends.mock_backend import MockBackend
    from core.attention import compute
    from runtime.executive import decide as exec_decide
    m = MockBackend()
    if action:
        return m.generate_response(user_input, action, {}, {}, {}, {})["response_text"]
    att  = compute(user_input, {}, {})
    ex   = exec_decide(att, user_input=user_input)
    mode = ex.get("action", ex.get("tone", "reflect"))
    return m.generate_response(user_input, mode, {}, {}, {}, {})["response_text"]


def active_backend() -> str:
    """Return the name of the highest-priority backend currently available."""
    mode = os.environ.get("ELO_BACKEND", "auto")
    if mode == "mock":   return "mock"
    if mode == "local":  return "ollama" if _ollama_available() else "mock"
    if mode == "cloud":  return "claude" if _claude_available() else ("groq" if _groq_available() else "mock")
    # auto: Claude → Groq → Ollama → Mock
    if _claude_available():  return "claude"
    if _groq_available():    return "groq"
    if _ollama_available():  return "ollama"
    return "mock"
