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
    Gemini:  gemini-2.0-flash (default — set ELO_GEMINI_MODEL to override)
             Requires GOOGLE_API_KEY from Google AI Studio (free: 1500 req/day)
    Groq:    llama-3.3-70b-versatile (quality, default — set ELO_GROQ_MODEL to override)
    Ollama:  mistral (default — set ELO_OLLAMA_MODEL to override)
"""

from __future__ import annotations
import json as _json
import os
import re
import time as _time
import logging

_logger = logging.getLogger(__name__)
_logger.propagate = True   # let root handler (server.py) decide where logs go

_BEHAVIOUR_LOG = os.path.join(os.path.dirname(__file__), "..", "logs", "behaviour_audit.jsonl")


def _log_behaviour_audit(event: str, response: str) -> None:
    try:
        entry = {"ts": round(_time.time(), 3), "event": event, "preview": response[:120]}
        os.makedirs(os.path.dirname(_BEHAVIOUR_LOG), exist_ok=True)
        with open(_BEHAVIOUR_LOG, "a", encoding="utf-8") as f:
            f.write(_json.dumps(entry) + "\n")
    except Exception:
        pass


def _truncate_to_word_limit(text: str, max_words: int = 38) -> str:
    """Truncate text to sentence boundary at or before max_words."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    result, word_count = [], 0
    for sentence in sentences:
        words = sentence.split()
        if word_count + len(words) > max_words:
            break
        result.append(sentence)
        word_count += len(words)
    return " ".join(result) if result else sentences[0]

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
    # Over-effusive AI connector phrases — strip the prefix, keep any substance after
    r"^that'?s?\s+(?:a\s+)?(?:great|wonderful|amazing|beautiful|perfect|powerful)\s+(?:connection|point|insight|observation|reminder|thought)[.!,]?\s*",
    r"^(?:wow[,!]?\s+)?that'?s?\s+(?:really|truly|so|very)\s+(?:meaningful|beautiful|deep|powerful|touching|honest)[.!,]?\s*",
    r"^what\s+a\s+(?:beautiful|powerful|meaningful|lovely|great)\s+(?:connection|thought|reminder|moment)[.!,]?\s*",
    r"^let'?s?\s+keep\s+(?:building|going|moving|working)\s+on\s+that\s+momentum[.!]?\s*",
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


def _is_pure_preamble(text: str) -> bool:
    """True if the response is nothing but AI-assistant preamble phrases — no real content."""
    stripped = text.strip()
    for pattern in _AI_PREAMBLES:
        stripped = re.sub(pattern, "", stripped, flags=re.IGNORECASE).strip()
    return not stripped


def _is_duplicate(new: str, prev: str, threshold: float = 0.92) -> bool:
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
    - Cap to max_sentences (counted across all paragraphs)
    - Preserve paragraph breaks (\n\n) so chat panel renders spacing
    - Preserve natural sentence endings
    """
    if not text:
        return text

    text = text.strip()
    _original = text

    # remove AI preambles
    for pattern in _AI_PREAMBLES:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()

    # if stripping preambles emptied the whole response, keep the original
    if not text:
        text = _original

    # split into paragraphs first — preserve \n\n structure
    paragraphs = re.split(r"\n{2,}", text)
    collected = []
    remaining = max_sentences
    for para in paragraphs:
        para = para.strip()
        if not para or remaining <= 0:
            break
        sentences = re.split(r"(?<=[.!?])\s+", para)
        take = sentences[:remaining]
        collected.append(" ".join(take))
        remaining -= len(take)

    text = "\n\n".join(collected).strip()

    # VOICE RULE enforcement — 15-30 word target; 38-word hard cap (allows natural margin)
    word_count = len(text.split())
    if word_count > 38:
        text = _truncate_to_word_limit(text, max_words=38)

    # MULTI-TURN RULE audit — one question per turn; log if violated (no auto-truncation)
    question_count = sum(1 for s in re.split(r"(?<=[.!?])\s+", text) if s.strip().endswith("?"))
    if question_count > 1:
        _log_behaviour_audit("multi_question_detected", text)

    return text


# ── WO-026: per-mode token budget ────────────────────────────────────────────
_TOKEN_BUDGET: dict = {
    "direct_response": 150,
    "celebrate":       200,
    "answer":          250,
    "observe":         250,
    "elaborate":       400,
    "reflect":         500,
    "build":           600,
    "plan":            600,
}
_TOKEN_BUDGET_DEFAULT = 300


def _token_budget(action: str) -> int:
    return _TOKEN_BUDGET.get((action or "").lower(), _TOKEN_BUDGET_DEFAULT)


_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s")


# ── backend calls ──────────────────────────────────────────────────────────────

def _groq_call(system_prompt: str, user_input: str, model: str = None, max_tokens: int = None) -> str:
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
        max_tokens=max_tokens or 500,
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


def _openai_call(
    system_prompt:     str,
    user_input:        str,
    max_tokens:        int      = None,
    on_first_sentence: object   = None,
) -> str:
    """Call OpenAI. When ELO_STREAM=1 and on_first_sentence is set, streams and fires early TTS."""
    import httpx
    api_key = os.environ.get("OPENAI_API_KEY", "")
    model   = os.environ.get("ELO_OPENAI_MODEL", "gpt-4o-mini")
    budget  = max_tokens or 700
    _msgs   = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_input},
    ]
    _headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    if os.environ.get("ELO_STREAM", "1") == "1" and on_first_sentence is not None:
        # streaming path — collect chunks, fire callback on first sentence
        chunks: list = []
        buffer = ""
        fired  = False
        try:
            with httpx.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                json={"model": model, "messages": _msgs, "max_tokens": budget,
                      "temperature": 0.7, "stream": True},
                headers=_headers,
                timeout=60.0,
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    payload = line[6:]
                    if payload.strip() == "[DONE]":
                        break
                    try:
                        delta = _json.loads(payload)["choices"][0]["delta"].get("content", "")
                    except Exception:
                        continue
                    if not delta:
                        continue
                    chunks.append(delta)
                    if not fired:
                        buffer += delta
                        m = _SENTENCE_END_RE.search(buffer)
                        if m:
                            try:
                                on_first_sentence(buffer[:m.start() + 1].strip())
                            except Exception:
                                pass
                            fired = True
            return "".join(chunks).strip()
        except Exception:
            pass   # streaming failed — fall through to non-streaming below

    # non-streaming (default, or streaming fallback)
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        json={"model": model, "messages": _msgs, "max_tokens": budget, "temperature": 0.7},
        headers=_headers,
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _cerebras_available() -> bool:
    return bool(os.environ.get("CEREBRAS_API_KEY", ""))


def _cerebras_call(system_prompt: str, user_input: str) -> str:
    """Call Cerebras Cloud — OpenAI-compatible, llama-3.3-70b, very fast."""
    import httpx
    api_key = os.environ.get("CEREBRAS_API_KEY", "")
    model   = os.environ.get("ELO_CEREBRAS_MODEL", "llama-3.3-70b")
    resp = httpx.post(
        "https://api.cerebras.ai/v1/chat/completions",
        json={
            "model":    model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_input},
            ],
            "max_tokens":  700,
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
    model   = os.environ.get("ELO_GEMINI_MODEL", "gemini-2.0-flash")
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


def _claude_call(system_prompt: str, user_input: str, max_tokens: int = None) -> str:
    """Call Anthropic Claude."""
    import anthropic
    api_key = os.environ["ANTHROPIC_API_KEY"]
    client  = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model      = os.environ.get("ELO_MODEL", "claude-sonnet-4-6"),
        max_tokens = max_tokens or 512,
        system     = system_prompt,
        messages   = [{"role": "user", "content": user_input}],
    )
    return msg.content[0].text.strip()


# ── intent-based model override ───────────────────────────────────────────────
# Lets users explicitly direct a query to a specific model.
# eLo still delivers the response — only the reasoning engine changes.

_CLAUDE_OVERRIDE   = ("ask claude", "use claude", "claude answer", "run it through claude")
_GEMINI_OVERRIDE   = ("ask gemini", "use gemini", "gemini answer", "translate", "long context")
_GROQ_OVERRIDE     = ("ask groq", "use groq", "fast answer", "quick answer")


def _detect_model_override(user_input: str) -> Optional[str]:
    """Return a forced backend name if the user explicitly named one, else None."""
    t = user_input.lower()
    if any(p in t for p in _CLAUDE_OVERRIDE):
        return "claude"
    if any(p in t for p in _GEMINI_OVERRIDE):
        return "gemini"
    if any(p in t for p in _GROQ_OVERRIDE):
        return "groq"
    return None


# ── public router ──────────────────────────────────────────────────────────────

def route(
    system_prompt:     str,
    user_input:        str,
    mode:              str    = None,
    max_sentences:     int    = 4,
    action:            str    = "",
    on_first_sentence: object = None,
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
        _env_mode = "local"
    mode = mode or _env_mode or "auto"

    # WO-026: per-mode token budget
    _budget = _token_budget(action)

    # intent-based model override — user explicitly named a backend
    _override = _detect_model_override(user_input)
    if _override == "claude" and _claude_available():
        try:
            raw = _claude_call(system_prompt, user_input, max_tokens=_budget)
            return normalise(raw, max_sentences), "claude(direct)"
        except Exception:
            pass  # fall through to normal routing
    elif _override == "gemini" and _gemini_available():
        try:
            raw = _gemini_call(system_prompt, user_input)
            return normalise(raw, max_sentences), "gemini(direct)"
        except Exception:
            pass
    elif _override == "groq" and _groq_available():
        try:
            raw = _groq_call(system_prompt, user_input, max_tokens=_budget)
            return normalise(raw, max_sentences), "groq(direct)"
        except Exception:
            pass

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
        # cloud mode: OpenAI → Gemini → Claude → Groq → Cerebras → Mock
        if _openai_available():
            try:
                raw = _openai_call(system_prompt, user_input, max_tokens=_budget,
                                   on_first_sentence=on_first_sentence)
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
                raw = _claude_call(system_prompt, user_input, max_tokens=_budget)
                return normalise(raw, max_sentences), "claude"
            except Exception as e:
                _logger.warning("Claude failed: %s", e)
        if _groq_available():
            try:
                raw = _groq_call(system_prompt, user_input, max_tokens=_budget)
                return normalise(raw, max_sentences), "groq"
            except Exception as e:
                _logger.warning("Groq failed: %s", e)
        if _cerebras_available():
            try:
                raw = _cerebras_call(system_prompt, user_input)
                return normalise(raw, max_sentences), "cerebras"
            except Exception as e:
                _logger.warning("Cerebras failed: %s", e)
        return _mock_fallback(user_input), "mock"

    # auto mode: OpenAI → Gemini → Claude → Groq → Cerebras → Ollama → Mock
    # Note: no hard mock shortcuts — all fallbacks go to the next backend in chain.
    if _openai_available():
        try:
            raw = _openai_call(system_prompt, user_input, max_tokens=_budget,
                               on_first_sentence=on_first_sentence)
            if _has_lore_drift(raw, user_input):
                _logger.warning("Lore drift in OpenAI response — falling back")
            elif _is_pure_preamble(raw):
                _logger.debug("OpenAI returned pure preamble — falling back")
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
            elif _is_pure_preamble(raw):
                _logger.debug("Gemini returned pure preamble — falling back")
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
            raw = _claude_call(system_prompt, user_input, max_tokens=_budget)
            return normalise(raw, max_sentences), "claude"
        except Exception as e:
            _logger.warning("Claude failed, trying Groq: %s", e)

    if _groq_available():
        try:
            raw = _groq_call(system_prompt, user_input, max_tokens=_budget)
            if _has_lore_drift(raw, user_input):
                _logger.debug("Lore drift in Groq response — trying Cerebras")
            else:
                # For short build/celebrate inputs: cap to 2 sentences so embedded
                # questions bubble to the end where _strip_trailing_question can remove them.
                _cap = 2 if (action in ("build", "celebrate") and len(user_input.strip()) < 40) else max_sentences
                normalised = normalise(raw, _cap)
                if action in ("build", "celebrate"):
                    stripped = _strip_trailing_question(normalised)
                    if stripped:
                        normalised = stripped
                if not _is_duplicate(normalised, _last_responses.get(action, "")):
                    _last_responses[action] = normalised
                    return normalised, "groq"
                else:
                    _logger.debug("Duplicate Groq response — trying Cerebras")
        except Exception as e:
            _logger.warning("Groq failed, trying Cerebras: %s", e)

    if _cerebras_available():
        try:
            raw = _cerebras_call(system_prompt, user_input)
            if _has_lore_drift(raw, user_input):
                _logger.debug("Lore drift in Cerebras response — trying Ollama")
            else:
                _cap = 2 if (action in ("build", "celebrate") and len(user_input.strip()) < 40) else max_sentences
                normalised = normalise(raw, _cap)
                if action in ("build", "celebrate"):
                    stripped = _strip_trailing_question(normalised)
                    if stripped:
                        normalised = stripped
                if not _is_duplicate(normalised, _last_responses.get(action, "")):
                    _last_responses[action] = normalised
                    return normalised, "cerebras"
                else:
                    _logger.debug("Duplicate Cerebras response — trying Ollama")
        except Exception as e:
            _logger.warning("Cerebras failed, trying Ollama: %s", e)

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
