"""
runtime/backend_router.py — eLo OS backend routing layer.

Routes requests between local (Ollama) and cloud (Groq / Gemini / OpenAI) backends.
Falls back to mock when nothing is available.

Priority (auto mode):
    OpenAI → Gemini → Claude → Groq → Cerebras → Ollama → Mock

Routing mode set via ELO_BACKEND env var:
    export ELO_BACKEND=auto    (default)
    export ELO_BACKEND=groq    (pinned Groq — voice-consistent, WO-032)
    export ELO_BACKEND=cloud   (cloud only — OpenAI → Gemini → Claude → Groq)
    export ELO_BACKEND=local   (Ollama only)
    export ELO_BACKEND=mock    (testing)

Models:
    OpenAI:  gpt-4o-mini (default — set ELO_OPENAI_MODEL to override)
    Gemini:  gemini-2.0-flash (default — set ELO_GEMINI_MODEL to override)
             Requires GOOGLE_API_KEY from Google AI Studio (free: 1500 req/day)
    Groq:    llama-3.3-70b-versatile (quality, default)
             llama-3.1-8b-instant    (fast — set ELO_GROQ_MODEL=llama-3.1-8b-instant)
    Ollama:  mistral (default — set ELO_OLLAMA_MODEL to override)
"""

from __future__ import annotations
import json as _json
import os
import re
import time
import logging
import urllib.request as _urllib_req
import urllib.error as _urllib_err

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())
_logger.propagate = False


def _cloud_timeout_s() -> float:
    """Per-attempt cloud timeout. 2026-08-20: was a hardcoded 30.0, and the pinned chain tries Groq THEN
    Cerebras THEN Ollama sequentially — so a stalled cloud leg could cost 60s of silence before the local
    brain was even asked. David's rule: "if it is taking longer than 4s it should figure out a quicker
    route." Env-tunable; the default now fits inside a single turn budget."""
    try:
        return max(1.0, float(os.environ.get("ELO_CLOUD_TIMEOUT_MS", "8000")) / 1000.0)
    except Exception:
        return 8.0


def _json_post(url: str, payload: dict, headers: dict, timeout: float = None) -> dict:
    """POST JSON to url, return parsed response dict. Raises urllib.error.HTTPError on 4xx/5xx."""
    data = _json.dumps(payload).encode()
    req = _urllib_req.Request(url, data=data, headers=headers, method="POST")
    with _urllib_req.urlopen(req, timeout=(timeout if timeout is not None else _cloud_timeout_s())) as resp:
        return _json.loads(resp.read().decode())

# ── routing thresholds ─────────────────────────────────────────────────────────
_AUTO_LOCAL_MAX_CHARS = 80   # inputs under this → Ollama (fast local)
                              # inputs over this  → Groq (deeper reasoning)
                              # David L3: retire-or-wire decision pending (WO-CANON-XX OQ)

# ── Cognitive tier constants (Vol XX — WO-CANON-XX) ───────────────────────────
_TIER_REFLEX         = 0   # handled before router — Tier 0 must never reach route()
_TIER_CONVERSATIONAL = 1   # cheapest capable (social, ambient, short answers)
_TIER_REASONING      = 2   # capable cloud (build, plan, challenge, reflect)
_TIER_DEEP           = 3   # premium (diagnose, deep, long analysis)

# ── CT0031: Ollama timing telemetry — populated by _ollama_call each turn ─────
_last_ollama_metrics: dict = {}

# Provider cost classes — used for escalation comparison
_COST_FREE_LOCAL    = "free-local"
_COST_CHEAP_CLOUD   = "cheap-cloud"
_COST_PREMIUM_CLOUD = "premium-cloud"

_PROVIDER_COST_CLASS: dict[str, str] = {
    "ollama":   _COST_FREE_LOCAL,
    "mock":     _COST_FREE_LOCAL,
    "groq":     _COST_CHEAP_CLOUD,
    "cerebras": _COST_CHEAP_CLOUD,
    "gemini":   _COST_CHEAP_CLOUD,
    "openai":   _COST_PREMIUM_CLOUD,
    "claude":   _COST_PREMIUM_CLOUD,
}

# Tier→cheapest-first provider order (absent a tier Executive always provides, route
# falls back to the live auto mode chain — the escalation-gate HOME is a CA open question)
_TIER_PROVIDER_ORDER: dict[int, list[str]] = {
    _TIER_CONVERSATIONAL: ["ollama", "groq", "cerebras", "gemini", "openai", "claude"],
    _TIER_REASONING:      ["groq", "cerebras", "openai", "gemini", "claude", "ollama"],
    _TIER_DEEP:           ["openai", "claude", "gemini", "groq", "cerebras", "ollama"],
}

# Tier→token budget (Vol XX M-3 — tier is primary key, action secondary)
_TIER_BUDGET: dict[int, int] = {
    _TIER_CONVERSATIONAL: 180,
    _TIER_REASONING:      400,
    _TIER_DEEP:           600,
}

# Priority order under scarcity (Vol XX §1.3)
# 0 = highest priority (never yields); 9 = yields first
_ACTION_PRIORITY: dict[str, int] = {
    "safety":     0,
    "answer":     1,
    "celebrate":  1,
    "connect":    1,
    "build":      2,
    "plan":       2,
    "challenge":  2,
    "reflect":    3,
    "ground":     3,
    "witness":    4,
    "navigate":   4,
    "silence":    4,
    "deep":       5,
    "diagnose":   5,
    "dream":      9,
    "optimise":   9,
}

# Tier each action defaults to when no Executive tier is provided
_ACTION_DEFAULT_TIER: dict[str, int] = {
    "build":     _TIER_REASONING,
    "challenge": _TIER_REASONING,
    "reflect":   _TIER_REASONING,
    "plan":      _TIER_REASONING,
    "deep":      _TIER_DEEP,
    "diagnose":  _TIER_DEEP,
}

# Factual request patterns — mock MUST NOT fabricate for these (Vol XX Ch.3 G-1)
_FACTUAL_PATTERNS = [
    r"\bwhat time\b", r"\bwhat date\b", r"\bwhat is\b", r"\bwhat are\b",
    r"\bhow do\b", r"\bhow does\b", r"\bwhy does\b", r"\bexplain\b",
    r"\bcan you check\b", r"\bcalculate\b", r"\bconvert\b",
    r"\bremind\b", r"\bschedule\b",
]

# Honest limitation message — degraded tier never fabricates factual content (G-1/G-4)
_HONEST_DEGRADATION_MSG = (
    "I can't reason through that right now — I'm running offline."
)


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
    "orb system", "the orb",
    # k-7, k7, "world stage" removed — canon characters/concepts, not hallucinated lore
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


# ── Vol XX helpers (WO-CANON-XX) ──────────────────────────────────────────────

def _action_priority(action: str) -> int:
    """Priority under scarcity (0=highest/never-yields, 9=yields-first)."""
    return _ACTION_PRIORITY.get(action, 5)


def _is_factual_request(user_input: str) -> bool:
    """True when the request is factual/technical/action — mock must not fabricate."""
    t = user_input.lower()
    return any(re.search(p, t) for p in _FACTUAL_PATTERNS)


def _action_default_tier(action: str) -> int:
    """Return the lowest sufficient tier for this action."""
    return _ACTION_DEFAULT_TIER.get(action, _TIER_CONVERSATIONAL)

# WO-032b: time-boxed Groq 429 cooldown — clears automatically after 60 s so one transient
# rate-limit doesn't pin the entire session to mock.  0.0 = not in cooldown.
_groq_quota_cooldown_until: float = 0.0

# singleton mock backend — preserves anti-repetition buffer across all mock calls this session
_mock_backend_instance = None

# card 0069: time-boxed OpenAI 429 cooldown — mirrors WO-032b's Groq pattern.
# Was _openai_quota_exceeded (bool) which permanently snubbed OpenAI after one 429.
# David 2026-08-21: "do not snub them out — use what is available to feel out failsafes."
_openai_quota_cooldown_until: float = 0.0

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

def _groq_call(system_prompt: str, user_input: str, model: str = None, max_tokens: int = None) -> str:
    """Call Groq cloud inference via stdlib urllib (OpenAI-compatible REST, no SDK required).
    WO-032b: switched from httpx to urllib — zero external dependencies."""
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")
    model = model or os.environ.get("ELO_GROQ_MODEL", "llama-3.3-70b-versatile")
    result = _json_post(
        "https://api.groq.com/openai/v1/chat/completions",
        payload={
            "model":       model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_input},
            ],
            "max_tokens":  max_tokens or 400,
            "temperature": 0.7,
        },
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type":  "application/json"},
    )
    return result["choices"][0]["message"]["content"].strip()


def _cerebras_available() -> bool:
    return bool(os.environ.get("CEREBRAS_API_KEY", ""))


def _cerebras_call(system_prompt: str, user_input: str, model: str = None, max_tokens: int = None) -> str:
    """Call Cerebras fast inference via stdlib urllib (OpenAI-compatible REST).
    WO-032b: switched from httpx to urllib — zero external dependencies."""
    api_key = os.environ.get("CEREBRAS_API_KEY", "")
    if not api_key:
        raise RuntimeError("CEREBRAS_API_KEY not set")
    model = model or os.environ.get("ELO_CEREBRAS_MODEL", "llama-3.3-70b")
    result = _json_post(
        "https://api.cerebras.ai/v1/chat/completions",
        payload={
            "model":       model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_input},
            ],
            "max_tokens":  max_tokens or 400,
            "temperature": 0.7,
        },
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type":  "application/json"},
    )
    return result["choices"][0]["message"]["content"].strip()


def _ollama_call(system_prompt: str, user_input: str) -> str:
    """Call local Ollama instance via stdlib urllib."""
    import urllib.request as _ureq, json as _json
    host  = os.environ.get("ELO_OLLAMA_HOST",  "http://localhost:11434").rstrip("/")
    model = os.environ.get("ELO_OLLAMA_MODEL", "mistral")
    payload = _json.dumps({
        "model":      model,
        "messages":   [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_input},
        ],
        "stream":     False,
        "keep_alive": "30m",   # CT0031 Fix A: keep model loaded between turns
        "options":    {"temperature": 0.7, "num_predict": 256, "num_ctx": 8192},
    }).encode()
    req = _ureq.Request(
        f"{host}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with _ureq.urlopen(req, timeout=60) as _r:
        body = _json.loads(_r.read())
    # CT0031 Step 1: extract Ollama timing telemetry — all durations are nanoseconds
    _ns = lambda ns: round(ns / 1_000_000, 1) if ns else 0.0  # noqa: E731
    _load_ms   = _ns(body.get("load_duration", 0))
    _pe_tok    = body.get("prompt_eval_count", 0)
    _pe_ms     = _ns(body.get("prompt_eval_duration", 0))
    _ev_tok    = body.get("eval_count", 0)
    _ev_ms     = _ns(body.get("eval_duration", 0))
    _logger.info(
        "CT0031 ollama: load=%.0fms prompt_eval=%dtok(%.0fms) gen=%dtok(%.0fms)",
        _load_ms, _pe_tok, _pe_ms, _ev_tok, _ev_ms,
    )
    _last_ollama_metrics.clear()
    _last_ollama_metrics.update({
        "load_ms":              _load_ms,
        "prompt_eval_tokens":   _pe_tok,
        "prompt_eval_ms":       _pe_ms,
        "gen_tokens":           _ev_tok,
        "gen_ms":               _ev_ms,
    })
    return body.get("message", {}).get("content", "").strip()


def _openai_available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", ""))


def _token_budget(action: str, tier: int = 0) -> int:
    """Return max_tokens for the given action. Tier is primary key (Vol XX M-3); action fallback."""
    if tier and tier in _TIER_BUDGET:
        return _TIER_BUDGET[tier]
    # action-based fallback (verbatim live budgets)
    if action in ("build", "challenge", "reflect", "plan", "deep", "diagnose"):
        return 600
    # celebrate, connect, ground, navigate, witness, silence, answer, ""
    return 280


def _openai_call(system_prompt: str, user_input: str, max_tokens: int = None) -> str:
    """Call OpenAI GPT-4o-mini via stdlib urllib. WO-032b: switched from httpx."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    model   = os.environ.get("ELO_OPENAI_MODEL", "gpt-4o-mini")
    result = _json_post(
        "https://api.openai.com/v1/chat/completions",
        payload={
            "model":    model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_input},
            ],
            "max_tokens":  max_tokens or 400,
            "temperature": 0.7,
        },
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type":  "application/json"},
    )
    return result["choices"][0]["message"]["content"].strip()


def _finish(raw: str, action: str, max_sentences: int, backend: str) -> str:
    """The voice guards, in ONE place, applied identically to EVERY backend.

    2026-08-20 — before this existed, the Groq branch ran normalise -> _strip_trailing_question ->
    _last_responses[action] = ..., while the Cerebras and Ollama fallback branches ran only normalise and
    returned. So `_is_duplicate` was never consulted and `_last_responses` was never updated on a
    fall-through, and eLo repeated himself verbatim on consecutive turns exactly when the weaker backend was
    answering. (David, live 2026-08-20: "Okay doubling up?")

    Guards and their ORDER are unchanged — they are eLo's voice, not performance code. This only makes them
    unskippable. Raises ValueError on a duplicate so the caller can try the next backend.
    """
    out = normalise(raw, max_sentences)
    if action in ("build", "celebrate"):
        out = _strip_trailing_question(out) or out
    if _is_duplicate(out, _last_responses.get(action, "")):
        raise ValueError(f"duplicate response from {backend}")
    _last_responses[action] = out
    _identity_assert(out, action)  # WO-BRAIN-AUTHORS: detection only, never blocks
    return out


# ── WO-BRAIN-AUTHORS: identity assertion (detection only) ────────────────────

# Patterns that indicate the model is narrating David's state instead of being eLo.
# This list mirrors the living_presence_spec anti-mirroring rule — update both together.
_IDENTITY_FAIL_PATTERNS: tuple[str, ...] = (
    "it feels like you",
    "i notice you",
    "i hear you",
    "i see you",
    "you mentioned",
    "you've been",
    "you seem to be",
    "it sounds like you",
    "you said ",
    "you typed ",
    "you were feeling",
    "you were thinking",
    "you feel ",           # "you feel overwhelmed" — space prevents "how do you feel"
    "you're still",        # "you're still feeling" — state narration
    "you're feeling",
    "you're checking",
)


def _identity_assert(text: str, action: str) -> list[str]:
    """Detection-only identity assertion.  Returns matched patterns (empty = clean).
    Logs at WARNING. Does NOT rewrite the response. Does NOT block.
    v1: pattern-based. Future: voice-state embedding similarity.

    RED when this function is removed: tests/test_brain_authors.py test 3 goes RED.
    """
    found = []
    text_lower = text.lower()
    for pattern in _IDENTITY_FAIL_PATTERNS:
        if pattern in text_lower:
            found.append(pattern)
    if found:
        _logger.warning(
            "identity-assert: action=%s patterns=%s",
            action, found,
        )
    return found


# ── WO-BRAIN-AUTHORS: tier-aware routing ─────────────────────────────────────

def _route_by_tier(
    system_prompt: str,
    user_input: str,
    tier: int,
    action: str,
    max_sentences: int,
) -> tuple[str, str] | None:
    """Try providers in _TIER_PROVIDER_ORDER[tier] order.
    Returns (text, backend) or None if tier is not mapped or all providers fail.

    ELO_BACKEND is an override — only call this when ELO_BACKEND is NOT set (mode == "auto").
    Conversational → local-first (Ollama); Reasoning → Groq-first; Deep → OpenAI-first.

    RED when _TIER_PROVIDER_ORDER is removed: tests/test_brain_authors.py test 2 goes RED.
    """
    if tier not in _TIER_PROVIDER_ORDER:
        return None
    _budget = _token_budget(action, tier)
    for provider in _TIER_PROVIDER_ORDER[tier]:
        try:
            if provider == "ollama" and _ollama_available():
                raw = _ollama_call(system_prompt, user_input)
                return _finish(raw, action, max_sentences, "ollama"), f"ollama(tier{tier})"
            elif provider == "groq" and _groq_available():
                raw = _groq_call(system_prompt, user_input, max_tokens=_budget)
                if _has_lore_drift(raw, user_input):
                    continue
                return _finish(raw, action, max_sentences, "groq"), f"groq(tier{tier})"
            elif provider == "openai" and _openai_available():
                raw = _openai_call(system_prompt, user_input, max_tokens=_budget)
                if _has_lore_drift(raw, user_input):
                    continue
                return _finish(raw, action, max_sentences, "openai"), f"openai(tier{tier})"
            elif provider == "claude" and _claude_available():
                raw = _claude_call(system_prompt, user_input, max_tokens=_budget)
                return _finish(raw, action, max_sentences, "claude"), f"claude(tier{tier})"
            elif provider == "cerebras" and _cerebras_available():
                raw = _cerebras_call(system_prompt, user_input, max_tokens=_budget)
                if _has_lore_drift(raw, user_input):
                    continue
                return _finish(raw, action, max_sentences, "cerebras"), f"cerebras(tier{tier})"
            elif provider == "gemini" and _gemini_available():
                raw = _gemini_call(system_prompt, user_input)
                if _has_lore_drift(raw, user_input):
                    continue
                return _finish(raw, action, max_sentences, "gemini"), f"gemini(tier{tier})"
        except ValueError:
            _logger.debug("Tier routing: duplicate from %s, trying next", provider)
        except Exception as e:
            _logger.debug("Tier routing: %s failed: %s", provider, e)
    return None


def _groq_stream(
    system_prompt: str,
    user_input: str,
    max_tokens: int = None,
    on_first_sentence=None,
) -> tuple[str, float]:
    """Stream Groq tokens. Mirrors _openai_stream exactly; same SSE shape (OpenAI-compatible endpoint).

    2026-08-20 — eLo runs ELO_BACKEND=groq, and route_streaming() gated streaming behind
    `mode in ("auto","cloud")`, so his everyday configuration NEVER streamed: he waited for the whole
    generation before speaking a word, and on_first_sentence early-TTS never fired.

    stdlib urllib, NOT httpx — WO-032b deliberately removed the SDK/httpx dependency from the Groq path
    ("zero external dependencies"). That decision is kept.

    Same model, same prompt, same temperature 0.7, same max_tokens as _groq_call. The assembled string is
    byte-identical to the non-streaming call; only ARRIVAL changes. Nothing of eLo is traded for speed.
    Returns (full_assembled_text, first_token_latency_ms).
    """
    import urllib.request as _ureq, json as _json, time as _t
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")
    model = os.environ.get("ELO_GROQ_MODEL", "llama-3.3-70b-versatile")
    payload = _json.dumps({
        "model":       model,
        "stream":      True,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_input},
        ],
        "max_tokens":  max_tokens or 400,
        "temperature": 0.7,
    }).encode()
    req = _ureq.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    t_start = _t.monotonic()
    first_token_ms = 0.0
    buffer, first_sent_fired = [], False
    # first-token deadline: David's rule — "if it is taking longer than 4s it should figure out a quicker
    # route". Connect/read timeout is the floor; the caller enforces the wall-clock budget.
    with _ureq.urlopen(req, timeout=_first_token_budget_s()) as resp:
        for raw_line in resp:
            line = raw_line.decode("utf-8", "replace").strip()
            if not line or not line.startswith("data: "):
                continue
            chunk_s = line[6:]
            if chunk_s.strip() == "[DONE]":
                break
            try:
                delta = _json.loads(chunk_s)["choices"][0]["delta"].get("content", "")
            except Exception:
                continue
            if not delta:
                continue
            if not buffer:
                first_token_ms = (_t.monotonic() - t_start) * 1000
            buffer.append(delta)
            if not first_sent_fired and on_first_sentence:
                assembled = "".join(buffer)
                m = _SENTENCE_END_RE.search(assembled)
                if m:
                    first_sent_fired = True
                    try:
                        on_first_sentence(assembled[:m.end()].strip())
                    except Exception:
                        pass
    return "".join(buffer).strip(), first_token_ms


def _first_token_budget_s() -> float:
    """Seconds to wait for a first token before handing off. Env-tunable, never hardcoded downstream."""
    try:
        return max(0.5, float(os.environ.get("ELO_FIRST_TOKEN_MS", "2500")) / 1000.0)
    except Exception:
        return 2.5


def _openai_stream(
    system_prompt: str,
    user_input: str,
    max_tokens: int = None,
    on_first_sentence=None,
) -> tuple[str, float]:
    """Stream OpenAI tokens. Fires on_first_sentence(sentence) when sentence 1 ends.
    Returns (full_assembled_text, first_token_latency_ms).
    """
    import httpx, time as _t
    api_key = os.environ.get("OPENAI_API_KEY", "")
    model   = os.environ.get("ELO_OPENAI_MODEL", "gpt-4o-mini")

    t_start = _t.monotonic()
    first_token_ms = 0.0
    buffer = []
    first_sent_fired = False

    with httpx.stream(
        "POST",
        "https://api.openai.com/v1/chat/completions",
        json={
            "model":    model,
            "stream":  True,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_input},
            ],
            "max_tokens":  max_tokens or 400,
            "temperature": 0.7,
        },
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type":  "application/json"},
        timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=5.0),
    ) as resp:
        resp.raise_for_status()
        import json as _json
        for line in resp.iter_lines():
            if not line or not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload.strip() == "[DONE]":
                break
            try:
                chunk = _json.loads(payload)
                delta = chunk["choices"][0]["delta"].get("content", "")
            except Exception:
                continue
            if delta:
                if not buffer:
                    first_token_ms = (_t.monotonic() - t_start) * 1000
                buffer.append(delta)
                # Fire on_first_sentence when we see end-of-sentence punctuation
                if not first_sent_fired and on_first_sentence:
                    assembled = "".join(buffer)
                    m = _SENTENCE_END_RE.search(assembled)
                    if m:
                        first_sent = assembled[:m.end()].strip()
                        first_sent_fired = True
                        try:
                            on_first_sentence(first_sent)
                        except Exception:
                            pass

    return "".join(buffer).strip(), first_token_ms


_SENTENCE_END_RE = __import__("re").compile(r"(?<=[.!?…])\s")


def _ollama_stream(
    system_prompt: str,
    user_input: str,
    max_tokens: int = None,
    on_first_sentence=None,
) -> "tuple[str, float]":
    """Stream Ollama tokens via NDJSON /api/chat. Mirrors _openai_stream signature.
    Updates _last_ollama_metrics from the final done=True chunk.
    Returns (full_assembled_text, first_token_latency_ms).
    """
    import urllib.request as _ureq, json as _json, time as _t
    host  = os.environ.get("ELO_OLLAMA_HOST",  "http://localhost:11434").rstrip("/")
    model = os.environ.get("ELO_OLLAMA_MODEL", "mistral")
    payload = _json.dumps({
        "model":      model,
        "messages":   [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_input},
        ],
        "stream":     True,
        "keep_alive": "30m",
        "options":    {"temperature": 0.7, "num_predict": max_tokens or 256, "num_ctx": 8192},
    }).encode()
    req = _ureq.Request(
        f"{host}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t_start = _t.monotonic()
    first_token_ms = 0.0
    buffer = []
    first_sent_fired = False
    _ns = lambda ns: round(ns / 1_000_000, 1) if ns else 0.0  # noqa: E731
    with _ureq.urlopen(req, timeout=120) as _resp:
        for _raw in _resp:
            line = _raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                chunk = _json.loads(line)
            except Exception:
                continue
            delta = chunk.get("message", {}).get("content", "")
            if delta:
                if not buffer:
                    first_token_ms = (_t.monotonic() - t_start) * 1000
                buffer.append(delta)
                if not first_sent_fired and on_first_sentence:
                    assembled = "".join(buffer)
                    _m = _SENTENCE_END_RE.search(assembled)
                    if _m:
                        first_sent_fired = True
                        try:
                            on_first_sentence(assembled[:_m.end()].strip())
                        except Exception:
                            pass
            if chunk.get("done"):
                _last_ollama_metrics.clear()
                _last_ollama_metrics.update({
                    "load_ms":            _ns(chunk.get("load_duration", 0)),
                    "prompt_eval_tokens": chunk.get("prompt_eval_count", 0),
                    "prompt_eval_ms":     _ns(chunk.get("prompt_eval_duration", 0)),
                    "gen_tokens":         chunk.get("eval_count", 0),
                    "gen_ms":             _ns(chunk.get("eval_duration", 0)),
                })
                _logger.info(
                    "CT0031 ollama stream: load=%.0fms prompt_eval=%dtok(%.0fms) gen=%dtok(%.0fms)",
                    _last_ollama_metrics["load_ms"],
                    _last_ollama_metrics["prompt_eval_tokens"],
                    _last_ollama_metrics["prompt_eval_ms"],
                    _last_ollama_metrics["gen_tokens"],
                    _last_ollama_metrics["gen_ms"],
                )
    return "".join(buffer).strip(), first_token_ms


def _ollama_available() -> bool:
    """True only when Ollama is up AND at least one model is installed (WO-073)."""
    try:
        import urllib.request as _ureq, json as _json
        host  = os.environ.get("ELO_OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        model = os.environ.get("ELO_OLLAMA_MODEL", "mistral")
        with _ureq.urlopen(f"{host}/api/tags", timeout=2) as _r:
            if _r.status != 200:
                return False
            models = [m.get("name", "") for m in _json.loads(_r.read()).get("models", [])]
        # Accept if the configured model is present, or any model at all as fallback
        return any(model in m for m in models) or len(models) > 0
    except Exception:
        return False


def _groq_available() -> bool:
    return bool(os.environ.get("GROQ_API_KEY", ""))


def _gemini_available() -> bool:
    return bool(os.environ.get("GOOGLE_API_KEY", ""))


def _gemini_call(system_prompt: str, user_input: str) -> str:
    """Call Google Gemini Flash via AI Studio REST API via stdlib urllib. WO-032b: switched from httpx."""
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    model   = os.environ.get("ELO_GEMINI_MODEL", "gemini-2.0-flash")
    url     = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    result = _json_post(url, payload={
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_input}]}],
        "generationConfig": {"maxOutputTokens": 512, "temperature": 0.7},
    }, headers={"Content-Type": "application/json"})
    return result["candidates"][0]["content"]["parts"][0]["text"].strip()


def _claude_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY", ""))


def _claude_call(system_prompt: str, user_input: str, max_tokens: int = None) -> str:
    """Call Anthropic Claude."""
    import anthropic
    api_key = os.environ["ANTHROPIC_API_KEY"]
    client  = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model      = os.environ.get("ELO_MODEL", "claude-sonnet-4-6"),
        max_tokens = max_tokens or 400,
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
    system_prompt: str,
    user_input:    str,
    mode:          str = None,
    max_sentences: int = 4,
    action:        str = "",
    tier:          int = 0,
) -> tuple[str, str]:
    """
    Route a request to the appropriate backend.

    Args:
        system_prompt: Full assembled system prompt from prompt_builder.
        user_input:    Raw user message.
        mode:          'auto' | 'local' | 'cloud' | 'mock' | None (reads ELO_BACKEND).
        max_sentences: Max sentences for response normaliser.
        tier:          Cognitive tier supplied by the Executive (Vol XX M-2).
                       0 = absent (use live auto mode); 1-3 = explicit tier.
                       Escalations above the action's default tier are logged.

    Returns:
        (response_text, backend_name)
    """
    # Vol XX M-2: escalation logging — record when Executive tier > action's cheapest default
    _default_tier = _action_default_tier(action)
    if tier and tier > _default_tier:
        _logger.info(
            "router: escalated tier %d→%d action=%s escalated=true",
            _default_tier, tier, action,
        )
    _budget = _token_budget(action, tier=tier)
    _env_mode = os.environ.get("ELO_BACKEND", "")
    _any_cloud = _openai_available() or _gemini_available() or _groq_available() or _claude_available() or _cerebras_available()
    if not _env_mode and not _any_cloud:
        # no API keys and no explicit backend set — go offline immediately
        _env_mode = "local"
    mode = mode or _env_mode or "auto"

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
            raw = _groq_call(system_prompt, user_input)
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
        # cloud mode: OpenAI → Gemini → Claude → Groq → Mock
        if _openai_available():
            try:
                raw = _openai_call(system_prompt, user_input, max_tokens=_budget)
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
                raw = _cerebras_call(system_prompt, user_input, max_tokens=_budget)
                return normalise(raw, max_sentences), "cerebras"
            except Exception as e:
                _logger.warning("Cerebras failed: %s", e)
        return _mock_fallback(user_input), "mock"

    if mode == "groq":
        # WO-032: pinned Groq mode — voice-consistent, no Claude/OpenAI drift.
        # Falls through to Cerebras → Mock only; never touches OpenAI, Gemini, or Claude.
        # WO-032b: _groq_quota_cooldown_until replaces the session-permanent bool — clears after 60 s.
        global _groq_quota_cooldown_until
        _groq_fell_through = False
        _in_cooldown = _groq_quota_cooldown_until and time.monotonic() < _groq_quota_cooldown_until
        if _groq_available() and not _in_cooldown:
            try:
                raw = _groq_call(system_prompt, user_input, max_tokens=_budget)
                if _has_lore_drift(raw, user_input):
                    # Lore drift: Cerebras may give a cleaner answer — don't go straight to mock
                    _logger.warning("Groq lore drift detected — trying Cerebras")
                    _groq_fell_through = True
                else:
                    normalised = normalise(raw, max_sentences)
                    if action in ("build", "celebrate"):
                        stripped = _strip_trailing_question(normalised)
                        if stripped:
                            normalised = stripped
                    _last_responses[action] = normalised
                    _groq_quota_cooldown_until = 0.0  # clear any stale cooldown on success
                    return normalised, "groq"
            except _urllib_err.HTTPError as e:
                if e.code == 429:
                    _groq_quota_cooldown_until = time.monotonic() + 60.0
                    _logger.warning("Groq 429 — 60 s cooldown, routing to Cerebras")
                elif e.code == 403:
                    _logger.error(
                        "GROQ API KEY SUSPENDED (403 Forbidden) — all turns falling to Ollama. "
                        "David: check console.groq.com and rotate the key in .env"
                    )
                else:
                    _logger.warning("Groq HTTP %s in pinned mode: %s", e.code, e)
            except Exception as e:
                _logger.warning("Groq failed in pinned mode: %s", e)
        if _cerebras_available():
            try:
                raw = _cerebras_call(system_prompt, user_input, max_tokens=_budget)
                # 2026-08-20: was `normalise(...)` then return — skipping _is_duplicate and never updating
                # _last_responses. _finish() applies the SAME guards the Groq branch already used.
                return _finish(raw, action, max_sentences, "cerebras"), "cerebras"
            except Exception as e:
                _logger.warning("Cerebras failed in pinned mode: %s", e)
        # WO-073: Ollama local floor — never drop to mute mock while a local brain is running
        if _ollama_available():
            try:
                raw = _ollama_call(system_prompt, user_input)
                # 2026-08-20: same omission as the Cerebras branch above. This is the path David was on when
                # eLo answered him twice with the same sentence.
                return _finish(raw, action, max_sentences, "ollama"), "ollama"
            except Exception as e:
                _logger.warning("Ollama failed in pinned mode: %s", e)
        return _mock_fallback(user_input), "mock"

    # WO-BRAIN-AUTHORS: tier-aware routing — Brain applies the model.
    # When ELO_BACKEND is NOT set (mode == "auto"), use the Executive's action tier
    # to choose the provider order from _TIER_PROVIDER_ORDER instead of the static chain.
    # ELO_BACKEND in .env is an explicit override and wins unconditionally.
    _derived_tier = tier or _action_default_tier(action)
    if _derived_tier and not os.environ.get("ELO_BACKEND", ""):
        _tier_result = _route_by_tier(system_prompt, user_input, _derived_tier, action, max_sentences)
        if _tier_result is not None:
            return _tier_result

    # auto mode: OpenAI → Gemini → Claude → Groq → Cerebras → Ollama → Mock
    # WO-032: skip OpenAI for the rest of the session once quota is confirmed exceeded
    # WO-042: import faculty health registry for reasoning faculty tracking
    try:
        from runtime.faculty_health import mark_degraded as _fh_degraded, mark_recovered as _fh_recovered
    except Exception:
        _fh_degraded = lambda *a, **k: None  # noqa: E731
        _fh_recovered = lambda *a, **k: None  # noqa: E731

    global _openai_quota_cooldown_until
    # card 0069: cooldown replaces the session-permanent bool — clears after 60 s so one transient
    # 429 doesn't permanently snub OpenAI. David: "feel out the failsafes."
    _openai_in_cooldown = (_openai_quota_cooldown_until
                          and time.monotonic() < _openai_quota_cooldown_until)
    if _openai_available() and not _openai_in_cooldown:
        try:
            raw = _openai_call(system_prompt, user_input, max_tokens=_budget)
            if _has_lore_drift(raw, user_input):
                _logger.debug("Lore drift in OpenAI response — falling back")
            else:
                normalised = normalise(raw, max_sentences)
                if action in ("build", "celebrate"):
                    normalised = _strip_trailing_question(normalised) or normalised
                if not _is_duplicate(normalised, _last_responses.get(action, "")):
                    _last_responses[action] = normalised
                    _openai_quota_cooldown_until = 0.0  # clear any stale cooldown on success
                    _fh_recovered("reasoning")
                    return normalised, "openai"
        except _urllib_err.HTTPError as e:
            if e.code == 429:
                # card 0069: 60 s cooldown, same as Groq (WO-032b). Reported, not removed.
                _openai_quota_cooldown_until = time.monotonic() + 60.0
                _fh_degraded("reasoning", "OpenAI quota exceeded (60s cooldown)")
                _logger.warning("OpenAI 429 — 60s cooldown, routing to Gemini/Groq/Claude")
            else:
                _logger.warning("OpenAI HTTP %s, trying Gemini: %s", e.code, e)
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
            raw = _claude_call(system_prompt, user_input, max_tokens=_budget)
            return normalise(raw, max_sentences), "claude"
        except Exception as e:
            _logger.warning("Claude failed, trying Groq: %s", e)

    if _groq_available():
        # NOTE (WO-032 Part C, 2026-08-03): reaching this block means OpenAI/Gemini/Claude all
        # failed or were unavailable — Groq is now the SOLE working engine, so it must handle ALL
        # inputs. The old "< 30 chars → mock" / "build < 60 → mock" gates forced short turns to the
        # canned mock even while Groq worked (backend_health showed backend:"mock" for every short
        # input). Those length gates are LIFTED — mock is a worse outcome than a Groq answer.
        # (Greetings are already handled by the greeting pool upstream, so pure "yo"/"hi" don't reach here.)
        try:
            raw = _groq_call(system_prompt, user_input, max_tokens=_budget)
            # catch lore drift — replace with mock using the original action
            if _has_lore_drift(raw, user_input):
                _logger.debug("Lore drift detected — replacing with mock fallback")
                return _mock_fallback(user_input, action=action), "mock"
            normalised = normalise(raw, max_sentences)
            # for BUILD/CELEBRATE: strip any trailing questions Groq added
            if action in ("build", "celebrate"):
                stripped = _strip_trailing_question(normalised)
                # WO-032: if stripping empties the response, keep original — real > mock
                if stripped:
                    normalised = stripped
            # WO-032: near-duplicate real response beats a canned mock — return it, reset cache
            if _is_duplicate(normalised, _last_responses.get(action, "")):
                _logger.debug("Duplicate Groq response — returning anyway (real > mock)")
                _last_responses[action] = ""   # reset so next call is fresh
            _last_responses[action] = normalised
            _fh_recovered("reasoning")  # WO-042: Groq working — mark reasoning healthy
            return normalised, "groq"
        except Exception as e:
            _logger.warning("Groq failed, trying Cerebras: %s", e)

    if _cerebras_available():
        try:
            raw = _cerebras_call(system_prompt, user_input, max_tokens=_budget)
            if _has_lore_drift(raw, user_input):
                _logger.debug("Lore drift in Cerebras — falling to mock")
                return _mock_fallback(user_input, action=action), "mock"
            normalised = normalise(raw, max_sentences)
            if action in ("build", "celebrate"):
                stripped = _strip_trailing_question(normalised)
                if stripped:
                    normalised = stripped
            # WO-032: near-duplicate real response beats a canned mock — return it, reset cache
            if _is_duplicate(normalised, _last_responses.get(action, "")):
                _logger.debug("Duplicate Cerebras response — returning anyway (real > mock)")
                _last_responses[action] = ""
            _last_responses[action] = normalised
            return normalised, "cerebras"
        except Exception as e:
            _logger.warning("Cerebras failed, trying Ollama: %s", e)

    if _ollama_available():
        try:
            raw = _ollama_call(system_prompt, user_input)
            return normalise(raw, max_sentences), "ollama"
        except Exception as e:
            _logger.warning("Ollama failed, falling to mock: %s", e)

    # WO-042: all providers exhausted → reasoning bucket is OFFLINE, not merely
    # degraded. mock_fallback is a stub, not a working reasoning path — the
    # Executive should treat this as no-reasoning-available for downstream gates.
    try:
        from runtime.faculty_health import mark_offline as _fh_offline
        _fh_offline("reasoning", "all providers failed — mock fallback only")
    except Exception:
        _fh_degraded("reasoning", "all providers failed — mock fallback")
    return _mock_fallback(user_input), "mock"


def route_streaming(
    system_prompt: str,
    user_input:    str,
    mode:          str = None,
    max_sentences: int = 4,
    action:        str = "",
    on_first_sentence=None,
    tier:          int = 0,
) -> tuple[str, str, float]:
    """
    Like route() but streams OpenAI tokens when available.

    Fires on_first_sentence(sentence) as soon as sentence 1 is complete —
    allowing TTS to start before the full response finishes.

    Returns (response_text, backend_name, first_token_latency_ms).
    Falls back to route() with 0.0 latency if streaming fails or OpenAI unavailable.
    """
    import time as _t
    global _groq_quota_cooldown_until
    _budget = _token_budget(action, tier=tier)
    _env_mode = os.environ.get("ELO_BACKEND", "")
    _env_mode = _env_mode or "auto"
    mode = mode or _env_mode

    # CT0031 Fix B: Ollama streaming for local/offline mode
    if mode == "local" and _ollama_available():
        try:
            t0 = _t.monotonic()
            raw, first_token_ms = _ollama_stream(
                system_prompt, user_input,
                max_tokens=_budget,
                on_first_sentence=on_first_sentence,
            )
            total_ms = (_t.monotonic() - t0) * 1000
            if not raw or _has_lore_drift(raw, user_input):
                raise ValueError("empty or lore-drifted stream response")
            normalised = normalise(raw, max_sentences)
            if action in ("build", "celebrate"):
                normalised = _strip_trailing_question(normalised) or normalised
            if _is_duplicate(normalised, _last_responses.get(action, "")):
                raise ValueError("duplicate stream response")
            _last_responses[action] = normalised
            _logger.debug("CT0031 ollama stream: first_token=%.0fms total=%.0fms", first_token_ms, total_ms)
            return normalised, "ollama(stream)", first_token_ms
        except Exception as _ose:
            _logger.warning("Ollama streaming failed (%s), falling back to route()", _ose)
            text, backend = route(system_prompt, user_input, mode=mode,
                                  max_sentences=max_sentences, action=action, tier=tier)
            return text, backend, 0.0

    # ── PINNED GROQ — stream it. 2026-08-20 ──────────────────────────────────────────────────
    # This branch did not exist. `"groq"` is not in ("auto","cloud"), so eLo's everyday configuration fell
    # straight through to the non-streaming route() below and returned 0.0 latency — which is why
    # routing_trace.json has always shown "llm_latency_ms": 0.0, and why early-TTS never fired.
    # Order is unchanged from route(): Groq -> Cerebras -> Ollama -> mock. Same prompts, same guards.
    if mode == "groq":
        _in_cd = _groq_quota_cooldown_until and _t.monotonic() < _groq_quota_cooldown_until
        if _groq_available() and not _in_cd:
            try:
                raw, first_ms = _groq_stream(system_prompt, user_input,
                                             max_tokens=_budget, on_first_sentence=on_first_sentence)
                if not raw:
                    raise ValueError("empty stream response")
                if _has_lore_drift(raw, user_input):
                    raise ValueError("lore drift")
                return _finish(raw, action, max_sentences, "groq"), "groq(stream)", first_ms
            except Exception as _ge:
                _logger.warning("Groq streaming failed (%s) — handing off", _ge)
        # Ollama can stream too; _ollama_stream already exists but was reachable only when mode=="local".
        if _ollama_available():
            try:
                raw, first_ms = _ollama_stream(system_prompt, user_input,
                                               max_tokens=_budget, on_first_sentence=on_first_sentence)
                if raw and not _has_lore_drift(raw, user_input):
                    return _finish(raw, action, max_sentences, "ollama"), "ollama(stream)", first_ms
            except Exception as _oe:
                _logger.warning("Ollama streaming failed in pinned mode (%s)", _oe)
        text, backend = route(system_prompt, user_input, mode=mode,
                              max_sentences=max_sentences, action=action, tier=tier)
        return text, backend, 0.0

    if mode not in ("auto", "cloud") or not _openai_available():
        # Non-streaming path — latency not measured
        text, backend = route(system_prompt, user_input, mode=mode,
                              max_sentences=max_sentences, action=action, tier=tier)
        return text, backend, 0.0

    try:
        t0 = _t.monotonic()
        raw, first_token_ms = _openai_stream(
            system_prompt, user_input,
            max_tokens=_budget,
            on_first_sentence=on_first_sentence,
        )
        total_ms = (_t.monotonic() - t0) * 1000
        if not raw or _has_lore_drift(raw, user_input):
            raise ValueError("empty or lore-drifted stream response")
        normalised = normalise(raw, max_sentences)
        if action in ("build", "celebrate"):
            normalised = _strip_trailing_question(normalised) or normalised
        if _is_duplicate(normalised, _last_responses.get(action, "")):
            raise ValueError("duplicate stream response")
        _last_responses[action] = normalised
        _logger.debug("WO-026 stream: first_token=%.0fms total=%.0fms", first_token_ms, total_ms)
        return normalised, "openai(stream)", first_token_ms
    except Exception as _se:
        _logger.warning("Streaming failed (%s), falling back to route()", _se)
        text, backend = route(system_prompt, user_input, mode=mode,
                              max_sentences=max_sentences, action=action, tier=tier)
        return text, backend, 0.0


def _mock_fallback(user_input: str, action: str = "") -> str:
    # Vol XX Ch.3 G-1: factual/technical/action requests must not fabricate.
    # Social/ambient turns may use a canned presence line.
    _social_actions = frozenset({"celebrate", "connect", "ground", "silence", "witness"})
    if _is_factual_request(user_input) and action not in _social_actions:
        return _HONEST_DEGRADATION_MSG
    global _mock_backend_instance
    from backends.mock_backend import MockBackend
    from core.memory_relevance_filter import compute
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
    if not _env_mode and not _groq_available() and not _claude_available() and not _cerebras_available():
        _env_mode = "local"   # no keys → go offline
    mode = _env_mode or "auto"
    if mode == "mock":   return "mock"
    if mode == "local":  return "ollama" if _ollama_available() else "mock"
    if mode == "groq":
        if _groq_available():      return "groq"
        if _cerebras_available():  return "cerebras"
        return "ollama" if _ollama_available() else "mock"  # WO-073
    if mode == "cloud":
        if _openai_available():    return "openai"
        if _gemini_available():    return "gemini"
        if _claude_available():    return "claude"
        if _groq_available():      return "groq"
        return "cerebras" if _cerebras_available() else "mock"
    # auto: OpenAI → Gemini → Claude → Groq → Cerebras → Ollama → Mock
    if _openai_available():    return "openai"
    if _gemini_available():    return "gemini"
    if _claude_available():    return "claude"
    if _groq_available():      return "groq"
    if _cerebras_available():  return "cerebras"
    if _ollama_available():    return "ollama"
    return "mock"
