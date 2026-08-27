"""
runtime/response_authority_guards.py — WO-GUARD-001: Response Authority Guard Chain
3 guards inserted after existing 4 guards, before publication.

D-1: Current-user-reality override
D-2: Tool provenance
D-3: Contradiction / resurrection

Authority: CA ruling 2026-08-27 + David L3 Convergence Directive
Each guard: wrap in try/except — failure must not block response.

# PROVENANCE CONTRACT — WO-GUARD-001
# D-2 and D-3 need: epistemic_class, authority_level, contradiction_flag
# memory/provenance.py defines EpistemicClass / AuthorityLevel — not yet wired.
# When wired, replace stub lookups here with provenance.py calls.
# This is the coordination boundary — do not block on it.
"""
from __future__ import annotations

import logging
import re

_log = logging.getLogger("response_authority_guards")

# ── D-1 helpers ───────────────────────────────────────────────────────────────

_CLAIM_ABOUT_USER = re.compile(
    r"\b(you\s+said|you\s+told\s+me|you\s+mentioned|you\s+asked\s+me|you\s+sent|"
    r"you\s+wrote|you\s+requested|you\s+confirmed)\b",
    re.IGNORECASE,
)

_USER_DENIAL = re.compile(
    r"\b(i\s+didn[''']?t|i\s+never|that[''']?s\s+not\s+what\s+i\s+said|"
    r"i\s+don[''']?t\s+remember\s+saying|i\s+haven[''']?t|i\s+didn[''']?t\s+say|"
    r"i\s+never\s+said|no\s+i\s+didn[''']?t|that[''']?s\s+not\s+right)\b",
    re.IGNORECASE,
)


def guard_d1_current_user_reality(response: str, session_summaries: list) -> str:
    """D-1: If response claims David said/did something he recently denied, qualify or suppress."""
    try:
        if not _CLAIM_ABOUT_USER.search(response):
            return response

        recent_user_inputs = [
            s.get("user", "")
            for s in session_summaries[-5:]
            if isinstance(s, dict)
        ]
        has_denial = any(_USER_DENIAL.search(u) for u in recent_user_inputs if u)
        if not has_denial:
            return response

        _log.warning(
            "D-1: candidate response makes a claim about David that conflicts with a recent denial — qualifying"
        )

        def _qualify_sentence(match_obj: re.Match) -> str:
            return match_obj.group(0).replace(
                match_obj.group(0),
                f"I thought {match_obj.group(0).lower()}",
            )

        qualified = _CLAIM_ABOUT_USER.sub(_qualify_sentence, response, count=1)
        return qualified
    except Exception as _e:
        _log.warning("D-1 guard exception (non-fatal): %s", _e)
        return response


# ── D-2 helpers ───────────────────────────────────────────────────────────────

_TOOL_ACTION_CLAIM = re.compile(
    r"\b(I\s+checked|I\s+confirmed|I\s+looked\s+up|I\s+searched|I\s+found|"
    r"I\s+fetched|I\s+retrieved|I\s+queried|I\s+pulled)\b",
    re.IGNORECASE,
)

_TOOL_ACTION_REWRITE: dict[str, str] = {
    "i checked":    "it shows",
    "i confirmed":  "it indicates",
    "i looked up":  "looking it up,",
    "i searched":   "the search shows",
    "i found":      "it shows",
    "i fetched":    "it returned",
    "i retrieved":  "it returned",
    "i queried":    "the result shows",
    "i pulled":     "it returned",
}


def guard_d2_tool_provenance(response: str, tool_agent: str) -> str:
    """D-2: When a tool ran, correct tool-action claims presented as personal eLo actions."""
    try:
        if not tool_agent:
            return response

        def _rewrite(m: re.Match) -> str:
            key = m.group(0).lower()
            for pattern, replacement in _TOOL_ACTION_REWRITE.items():
                if key.startswith(pattern):
                    return replacement
            return m.group(0)

        rewritten = _TOOL_ACTION_CLAIM.sub(_rewrite, response)
        if rewritten != response:
            _log.warning("D-2: tool provenance rewrite applied (tool_agent=%s)", tool_agent)
        return rewritten
    except Exception as _e:
        _log.warning("D-2 guard exception (non-fatal): %s", _e)
        return response


# ── D-3 helpers ───────────────────────────────────────────────────────────────

_MEMORY_CLAIM = re.compile(
    r"\b(I\s+remember|you\s+told\s+me|we\s+discussed|we\s+talked\s+about|"
    r"you\s+mentioned\s+before|last\s+time\s+you\s+said|earlier\s+you\s+said)\b",
    re.IGNORECASE,
)

_CORRECTION_SIGNAL = re.compile(
    r"\b(that[''']?s\s+not\s+right|that[''']?s\s+wrong|i\s+never\s+said|"
    r"no,?\s+that[''']?s|no,?\s+i\s+didn[''']?t|you[''']?re\s+wrong|"
    r"i\s+don[''']?t\s+think\s+that|that[''']?s\s+incorrect)\b",
    re.IGNORECASE,
)

_MEMORY_QUALIFIER = "I may be misremembering, but "


def guard_d3_contradiction_resurrection(response: str, session_summaries: list) -> str:
    """D-3: Prevent resurrecting claims already contradicted in session."""
    try:
        if not _MEMORY_CLAIM.search(response):
            return response

        recent_user_inputs = [
            s.get("user", "")
            for s in session_summaries[-4:]
            if isinstance(s, dict)
        ]
        has_correction = any(
            _CORRECTION_SIGNAL.search(u) for u in recent_user_inputs if u
        )
        if not has_correction:
            return response

        _log.warning(
            "D-3: candidate response resurrects a memory claim after user correction — qualifying"
        )

        def _qualify_memory(m: re.Match) -> str:
            return _MEMORY_QUALIFIER + m.group(0).lower()

        qualified = _MEMORY_CLAIM.sub(_qualify_memory, response, count=1)
        return qualified
    except Exception as _e:
        _log.warning("D-3 guard exception (non-fatal): %s", _e)
        return response


# ── Public interface ───────────────────────────────────────────────────────────

def apply_authority_guards(
    response: str,
    session_summaries: list,
    tool_agent: str = "",
) -> str:
    """Apply D-1, D-2, D-3 in sequence. Each guard is independently wrapped."""
    response = guard_d1_current_user_reality(response, session_summaries)
    response = guard_d2_tool_provenance(response, tool_agent)
    response = guard_d3_contradiction_resurrection(response, session_summaries)
    return response
