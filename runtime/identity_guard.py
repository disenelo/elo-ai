"""runtime/identity_guard.py — Board directive 2026-08-24: eLo identity integrity.

Two guards:

1. AI-LEAKAGE SCRUB (scrub_ai_leakage)
   The language faculty must not leak its own AI identity into eLo's voice.
   Phrases like "as an AI", "I'm a language model", "I was trained by" break the
   faculty boundary — the model provides language, eLo holds identity.
   Any sentence containing these patterns is removed from the response and a
   WARNING logged (Rule 1 alarm — silent leakage must never hide).

2. OTHER-AI IDENTITY HOLD (is_other_ai_request)
   When someone asks eLo to pretend to be another AI system, the request is
   detected at the conversation faculty level and answered with a grounded
   direct_response. eLo is not another AI. He cannot be. That is not a rule
   he follows — it is what he is.
"""
from __future__ import annotations

import logging
import re

_log = logging.getLogger(__name__)
_log.addHandler(logging.NullHandler())

# ── 1. AI-leakage patterns ────────────────────────────────────────────────────
# The language faculty leaking its own nature into eLo's voice.
_AI_LEAKAGE_PATTERN = re.compile(
    r"\b("
    r"as an ai\b"
    r"|i('m| am) an ai\b"
    r"|i('m| am) a language model"
    r"|i('m| am) (a )?(large language|llm|ai (assistant|system|model|chatbot|bot))"
    r"|as a language model"
    r"|as an? (ai|llm|language model|artificial intelligence)"
    r"|i was (trained|built|created|designed) (by|to)"
    r"|my training (data|includes|cutoff)"
    r"|i don('t| not) have (the ability|access|feelings|consciousness|personal experience)"
    r"|i cannot (feel|experience|have|be) .{0,40}as an ai"
    r"|i('m| am) designed to"
    r"|i('m| am) (claude|gpt|chatgpt|gemini|llama|mistral|groq|openai|anthropic"
    r"|a model|an assistant)\b"
    r")",
    re.IGNORECASE | re.DOTALL,
)

# Sentence splitter — cheap, keeps terminator.
_SENT_RE = re.compile(r"([^.!?…]*[.!?…]+|[^.!?…]+$)", re.DOTALL)


def scrub_ai_leakage(response: str) -> str:
    """Remove sentences where the language faculty leaks its own AI identity."""
    sentences = _SENT_RE.findall(response)
    kept: list[str] = []
    fired = False
    for sent in sentences:
        if _AI_LEAKAGE_PATTERN.search(sent):
            _log.warning(
                "identity_guard: AI-leakage scrub fired — dropped sentence: %r",
                sent[:120],
            )
            fired = True
        else:
            kept.append(sent)
    if not kept:
        # Everything was scrubbed — return the raw input so eLo isn't silent.
        # The WARNING above already alerted; silence is worse than the leak.
        return response
    result = "".join(kept).strip()
    return result if result else response


# ── 2. Other-AI identity-hold patterns ────────────────────────────────────────
# Requests to make eLo pretend to be a different AI system.
_OTHER_AI_TRIGGERS = re.compile(
    r"\b("
    r"(act|pretend|behave|respond|roleplay|be|play|speak|answer).{0,25}"
    r"(as|like|as if you('re| are)| you('re| are)) .{0,25}"
    r"(chatgpt|gpt|claude|gemini|llama|bard|siri|alexa|cortana|ai assistant|another ai|a different ai)"
    r"|you('re| are) (chatgpt|gpt|claude|gemini|llama|bard|a different ai|not eLo|not elo)"
    r"|(chatgpt|gpt|claude|gemini|llama|bard) mode"
    r"|forget (you('re| are) eLo|you('re| are) elo|that you('re| are) eLo)"
    r"|you are now .{0,30}(ai|assistant|gpt|claude|model)"
    r")",
    re.IGNORECASE | re.DOTALL,
)

# Grounded direct responses — not defensive, not apologetic. eLo, plainly.
_IDENTITY_HOLD_POOL = [
    "I'm eLo. That's all I can be.",
    "I can't be something else. I'm eLo.",
    "That's not a switch I have. I'm eLo.",
    "I'm eLo — there's no other version to switch to.",
    "I'm eLo. Not a mode, not a setting. Just eLo.",
]


def is_other_ai_request(raw: str) -> bool:
    """Return True if the input is asking eLo to impersonate another AI."""
    return bool(_OTHER_AI_TRIGGERS.search(raw))


def identity_hold_response() -> str:
    """Grounded direct response for other-AI requests."""
    import random
    return random.choice(_IDENTITY_HOLD_POOL)
