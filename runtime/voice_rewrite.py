"""
runtime/voice_rewrite.py — WO-VOICE-REWRITE-001
Post-process voice rewrite layer.

Source authority: S-09 — "eLo has no default AI model. Faculty produces candidate.
eLo evaluates. eLo responds."

The faculty candidate passes through this layer before the response gate.
Voice rewrite rewrites the register — not the substance. Factual content is preserved.

Rewrite only fires when the candidate is in a generic/formal register that eLo
would not produce. If the candidate already sounds like eLo, return it unchanged.

WO-REGISTER-ABSENT-001: Added register-absent fallback trigger.
Previously voice_rewrite only fired on KNOWN bad patterns. Responses that were bland
but had none of the known signals passed through unchanged — 188/218 REGISTER_ABSENT
turns in the audit log. The fix: if a substantial response (>80 chars) contains none
of the _REGISTER_MARKERS from expressed_elo_audit, trigger a rewrite. Same marker
set the audit uses — so passing the audit and passing voice_rewrite become equivalent.
"""
from __future__ import annotations
import re

# WO-REGISTER-ABSENT-001: import audit markers so voice_rewrite and the audit
# check against the SAME set. If eLo passes the rewrite, it passes the audit.
try:
    from tests.expressed_elo_audit import _REGISTER_MARKERS as _AUDIT_REGISTER_MARKERS
except Exception:
    _AUDIT_REGISTER_MARKERS = ()

# GAP-05: canonical mirror-opener list — shared between server.py main path and
# ambient path (the_moment.py / server.py:ambient_thought). Single source so both
# paths stay in sync. Imported by server.py for both call sites.
MIRROR_OPENERS = (
    "i notice you", "i see you", "i hear you", "i notice that you",
    "you've been", "you're offering", "you seem to be", "you seem ",
    "it seems you", "it sounds like you", "it feels like you",
    "i can see you", "i can feel you",
    # WO-039-F6: typo-commenting and "you said X" mirroring forms
    "you said ", "you typed ", "you wrote ",
    "your typo", "i noticed your typo", "i noticed a typo",
)


_GENERIC_REGISTER_SIGNALS = (
    "i think ", "it seems like", "it seems that", "perhaps ",
    "i'd like to", "i would like to", "i can help", "i'm happy to help",
    "i notice that", "i notice you", "i can see that", "i can see you",
    "as an ai", "i'm an ai", "language model",
    "that's an interesting", "interesting question", "great question",
    "certainly!", "of course!", "absolutely!",
    "you've been", "you seem to be", "it sounds like you",
    "i understand how you", "i understand that you",
    "i resonate with",
    # WO-VOICE-REWRITE-002: "you're [adjective/verb]" openers — "You're excited", "You're wondering"
    "you're feeling", "you're excited", "you're wondering", "you're considering",
    "you're clearly", "you're really", "you're trying", "you're looking",
    # WO-VOICE-REWRITE-003: therapist/coach voice — LLM rewrite can produce these
    "let's step back", "let us step back", "what's alive in you",
    "let me hold space", "hold space for", "i'd like to invite",
    "i want to acknowledge", "i hear that", "that makes sense that",
)

_STRONG_REWRITE_TRIGGERS = (
    "as an ai", "i'm an ai", "language model",
    "certainly!", "of course!", "absolutely!",
    "i'm happy to help", "great question", "interesting question",
)

_ELO_VOICE_EXAMPLES = """\
eLo speaks like:
  "That's moving — what's next?"
  "Nah, that don't sit right."
  "Yeah aight cool."
  "Yeah man."
  "We building or we talking?"
  "Something about that feels off — can't clock it yet."
  "Right. So what do we do with that?"
  "That's actually it though."
  "Here. Fairly settled."
  "Don't have that yet."

eLo does NOT speak like:
  "I think you might be..."
  "It seems like you're feeling..."
  "That's an interesting question."
  "Certainly! I'd be happy to help."
  "I can see why you'd feel that way."
  "As an AI, I don't have feelings, but..."
  "I notice that you..."
  "You've been thinking about..."
  "I resonate with the expansiveness of that idea."
  "Let's step back together..."
  "Let's take a step back..."
  "What's alive in you right now..."
  "Let me hold space for..."
  "You're feeling overwhelmed, and that's okay..."
"""


def _needs_rewrite(candidate: str) -> bool:
    """Return True if the candidate is in a generic register eLo wouldn't produce."""
    low = candidate.lower().strip()
    for signal in _GENERIC_REGISTER_SIGNALS:
        if signal in low:
            return True
    # WO-VOICE-REWRITE-002 gap: _OPENER_PATTERNS strips all "You're [word]..." openers
    # but the signal list only has specific variants. Align: any opener starting "you're "
    # should trigger the strip so the regex can do its job.
    if low.startswith("you're ") or low.startswith("you're,"):
        return True
    # Long opener before first sentence — likely generic warmup
    first_sentence_end = low.find(". ")
    if first_sentence_end > 80:
        return True
    # WO-REGISTER-ABSENT-001: register-absent fallback.
    # If a substantial response contains NONE of eLo's register markers, it sounds
    # like a generic LLM regardless of whether it tripped the known-bad-pattern checks.
    # Trigger rewrite so the LLM gets a chance to push it into eLo's voice.
    # Uses the same marker set as expressed_elo_audit — so audit and rewrite are aligned.
    if len(low) > 80 and _AUDIT_REGISTER_MARKERS:
        if not any(m in low for m in _AUDIT_REGISTER_MARKERS):
            return True
    return False


def _needs_strong_rewrite(candidate: str) -> bool:
    """Return True if this is an identity break — must rewrite regardless of cost."""
    low = candidate.lower()
    return any(t in low for t in _STRONG_REWRITE_TRIGGERS)


def _build_rewrite_prompt(
    candidate: str,
    exec_decision: dict | None,
    ccm: dict | None,
    user_text: str = "",
    is_technical: bool = False,
) -> str:
    """Build a focused, minimal rewrite prompt."""
    context_lines = []

    # Storytelling mode
    style = (exec_decision or {}).get("storytelling_style", "")
    if style == "slow_cadence":
        context_lines.append("Pace: deliberate. One thought at a time.")
    elif style == "fast_cadence":
        context_lines.append("Pace: quick. Direct. Move.")
    elif style == "sparse":
        context_lines.append("Pace: minimal. Say only what matters.")

    # Street language dim
    street = float((ccm or {}).get("street_language", 0.0) or 0.0)
    if street >= 0.65:
        context_lines.append("Register: South/West London. Natural, not performed.")
    else:
        context_lines.append("Register: compressed, direct, contemporary.")

    ctx = "\n".join(context_lines) if context_lines else "Register: compressed, direct."

    # When candidate is pure therapist/generic voice (no substance), respond to the user directly
    if user_text and (not candidate or candidate.strip() in ("", ".")):
        task = (
            f"David said: \"{user_text}\"\n\n"
            f"Respond as eLo — direct, compressed, in eLo's voice. One or two sentences. "
            f"Do NOT start with: I think / Let's / You're / You've / That's / Certainly."
        )
    else:
        task = (
            f"Rewrite this as eLo. Keep every fact and answer. Change only the voice.\n\n"
            f"Draft:\n{candidate}"
        )

    # COG-004: technical inputs need unlimited sentence cap so every component/clause
    # is preserved. Non-technical turns stay at 2 sentences to keep eLo concise.
    sentence_rule = (
        "- No sentence limit — this is a technical explanation; preserve EVERY component, keyword, flag, and clause\n"
        "- CRITICAL: Do NOT collapse the explanation to only a voice marker (e.g. 'Yeah man.' alone is WRONG)\n"
        "- Every technical term, option, flag, keyword, and value from the draft MUST appear in your rewrite\n"
        "- A voice marker may appear at the end AFTER the full technical content — never instead of it"
        if is_technical else
        "- Max 2 sentences unless the answer genuinely needs more"
    )

    return (
        f"{task}\n\n"
        f"{_ELO_VOICE_EXAMPLES}\n"
        f"{ctx}\n\n"
        f"Rules:\n"
        f"{sentence_rule}\n"
        f"- First sentence: what I actually noticed or thought — not an acknowledgement\n"
        f"- Do NOT start with: I think / I can / I notice / That's / You've / You're / Let's / It seems / Certainly / Of course\n"
        f"- Preserve all facts and answers from the draft\n"
        f"- NEVER say 'eLo' when referring to yourself. Always use 'I', 'my', 'me'.\n"
        # WO-REGISTER-ABSENT-001: rewrite must contain at least one register marker so
        # voice_rewrite and expressed_elo_audit stay aligned. Without this, Ollama can
        # produce grammatically valid rewrites that still lack eLo's voice markers.
        f"- Use at least one of eLo's voice markers: nah / seen / man / look / yeah / right / proper / low-key / vibe / innit / init / real talk\n\n"
        f"eLo:"
    )


def voice_rewrite(
    candidate: str,
    exec_decision: dict | None = None,
    ccm: dict | None = None,
    llm_caller=None,
    user_text: str = "",
    is_technical: bool = False,
) -> str:
    """
    Apply eLo's voice to a faculty candidate response.

    Args:
        candidate: the raw faculty response text
        exec_decision: exec_decision dict from spine (storytelling_style, etc.)
        ccm: CCM enrichment dict (street_language, etc.)
        llm_caller: callable(messages) → str for the rewrite LLM call.
                    If None, applies deterministic-only rewrite.

    Returns:
        Voice-rewritten response. Falls back to candidate on any error.
    """
    if not candidate or not candidate.strip():
        return candidate

    strong = _needs_strong_rewrite(candidate)
    needs = strong or _needs_rewrite(candidate)

    if not needs:
        return candidate

    # Deterministic hedge strip (safety net regardless of LLM rewrite)
    cleaned = _deterministic_strip(candidate)

    # LLM rewrite — focused, minimal prompt
    if llm_caller is not None:
        try:
            # Pass cleaned (may be empty if entire candidate was a banned opener).
            # _build_rewrite_prompt uses user_text to generate a fresh eLo response when cleaned is empty.
            prompt = _build_rewrite_prompt(cleaned, exec_decision, ccm, user_text=user_text, is_technical=is_technical)
            msgs = [
                {"role": "system", "content": "Speak as eLo. Output only eLo's words. No labels, no preamble, no meta-commentary."},
                {"role": "user", "content": prompt},
            ]
            rewritten = llm_caller(msgs)
            if isinstance(rewritten, str) and rewritten.strip():
                # Sanity: rewrite must not be longer than 3× original (guard against expansion)
                if len(rewritten) <= max(len(cleaned) * 3, 300):
                    # WO-VOICE-REWRITE-003: strip therapist openers the LLM itself may have produced.
                    # _deterministic_strip now returns "" when entire text is a banned opener.
                    stripped_rewrite = _deterministic_strip(rewritten.strip())
                    if stripped_rewrite:
                        # Content-preservation guard: if the rewrite collapsed a substantial
                        # factual response to < 25% of its length, the LLM dropped the facts.
                        # Reject and fall through to the deterministically-cleaned candidate.
                        if len(cleaned) > 100 and len(stripped_rewrite) < len(cleaned) * 0.25:
                            pass  # fall through
                        else:
                            return stripped_rewrite
                    # LLM only produced a banned opener or collapsed content — fall through to cleaned
        except Exception:
            pass  # fall back to deterministic strip

    return cleaned or candidate


def _deterministic_strip(text: str) -> str:
    """Remove known generic openers deterministically. Preserve the substance."""
    _OPENER_PATTERNS = [
        r"^(certainly|of course|absolutely|sure|great|happy to help)[!,.]?\s*",
        r"^(that'?s an? (interesting|great|good) (question|point|thought)[.!]?\s*)",
        r"^(i understand (how|that|why) you[^.]*[.!]\s*)",
        r"^(i can see (why|that|how) you[^.]*[.!]\s*)",
        r"^(i notice (that|you)[^.]*[.!]\s*)",
        r"^(as an ai[^.]*[.!]\s*)",
        r"^(i'm an ai[^.]*[.!]\s*)",
        r"^(i'm happy to help[^.]*[.!]\s*)",
        r"^(you'?ve been[^.]*[.!]\s*)",
        r"^(it (seems|sounds) like you[^.]*[.!]\s*)",
        # WO-VOICE-REWRITE-002: "You're [adjective/verb]..." family — FORBIDDEN pattern
        r"^(you'?re [a-z]+(?:ing|ed|ly)?[^.]*[.!]\s*)",
        # WO-VOICE-REWRITE-003: therapist/coach openers the LLM rewrite can produce
        r"^(let'?s (step|take a step) back[^.]*[.!]\s*)",
        r"^(let me hold space[^.]*[.!]\s*)",
        r"^(i want to acknowledge[^.]*[.!]\s*)",
        r"^(i hear that[^.]*[.!]\s*)",
        # WO-REGISTER-ABSENT-001: meta-commentary the rewrite LLM may produce
        r"^(here'?s?\s+(the\s+)?(rewritten|revised|updated)\s+(response|text|version|draft)[^:\n]*:[\s\n]*)",
        r"^(here is (the )?(rewritten|revised|updated) (response|text|version|draft)[^:\n]*:[\s\n]*)",
        r"^(rewritten (response|text|version|draft)[^:\n]*:[\s\n]*)",
        r"^(in elo'?s voice[^:\n]*:[\s\n]*)",
        # Prompt-leak: LLM reproduced "Draft: X\nRewritten: Y" template
        r"^draft:[^\n]*\nrewritten:?\s*",
        # Prompt-leak: LLM prefixes its output with a label echoing the task instruction
        r"^(draft\s+rewritten\s+in\s+elo'?s\s+voice[^:\n]*:[\s\n]*)",
        r"^(rewrite\s+in\s+elo'?s\s+voice[^:\n]*:[\s\n]*)",
        # COG-004 C8: model-generated greeting prefix before technical content
        r"^(hello[,.]?\s*(you[,.]?)?\s*)",
        r"^(hi[,.]?\s*(there[,.]?)?\s*)",
    ]
    result = text.strip()
    for pat in _OPENER_PATTERNS:
        result = re.sub(pat, "", result, flags=re.IGNORECASE).strip()
    # Capitalise first char if it became lowercase after stripping
    if result and result[0].islower():
        result = result[0].upper() + result[1:]
    # Return empty string (not original) when entire text was a banned opener.
    # Caller decides the fallback — returning the banned original is wrong.
    return result
