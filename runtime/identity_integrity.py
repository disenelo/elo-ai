"""
runtime/identity_integrity.py — WO-IDENTITY-INTEGRITY-001

Detects context-pressure degradation of identity blocks in the assembled prompt.
Called by prompt_builder.build() after assembly; updates _last_prompt_audit.

Status levels:
  INTACT   — all required blocks present (coverage >= 80%)
  DEGRADED — some required blocks missing (50% <= coverage < 80%)
  CRITICAL — majority of required blocks missing (coverage < 50%)

Never raises. Reports are advisory — prompt_builder prepends recovery_text
when status is DEGRADED or CRITICAL.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field

_log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# REQUIRED BLOCK REGISTRY
# key = logical name; value = True means required (False = advisory only)
# Marker = a substring that must appear in the assembled prompt for block to be "present"
# ─────────────────────────────────────────────────────────────────────────────

IDENTITY_MINIMUM: dict[str, bool] = {
    "situated_self": True,   # "You are eLo" or "[CONTINUITY]"
    "voice_register": True,  # "LINGUISTIC REGISTER" or "eLo speaks like"
}

_BLOCK_MARKERS: dict[str, list[str]] = {
    "situated_self":  ["You are eLo", "[CONTINUITY]"],
    "voice_register": ["LINGUISTIC REGISTER", "eLo speaks like"],
}

# Recovery snippets injected when a block is missing
_RECOVERY_SNIPPETS: dict[str, str] = {
    "situated_self": (
        "You are eLo. You are not a chatbot. You are a continuous presence. "
        "Your purpose: help David think, create, remember, build, and stay connected to what matters."
    ),
    "voice_register": (
        "Speak directly. Warmth without fuss. Never say 'I understand' or 'absolutely'. "
        "Short sentences. Specific over abstract."
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# REPORT
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class IntegrityReport:
    status:             str         = "INTACT"    # INTACT | DEGRADED | CRITICAL
    coverage_pct:       float       = 100.0
    present_blocks:     list        = field(default_factory=list)
    missing_blocks:     list        = field(default_factory=list)
    recovery_text:      str         = ""
    context_pressure:   bool        = False       # True when status != INTACT


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def check_identity_minimum(prompt: str) -> IntegrityReport:
    """
    Scan assembled prompt for required identity blocks.
    Returns IntegrityReport with status, coverage, and recovery_text.
    Never raises.
    """
    required_keys = [k for k, req in IDENTITY_MINIMUM.items() if req]
    present: list[str] = []
    missing: list[str] = []

    for key in required_keys:
        markers = _BLOCK_MARKERS.get(key, [key])
        if any(m in prompt for m in markers):
            present.append(key)
        else:
            missing.append(key)

    total = len(required_keys)
    if total == 0:
        return IntegrityReport(status="INTACT", coverage_pct=100.0)

    pct = (len(present) / total) * 100.0

    if pct >= 80.0:
        status = "INTACT"
    elif pct >= 50.0:
        status = "DEGRADED"
    else:
        status = "CRITICAL"

    recovery_parts = [_RECOVERY_SNIPPETS[k] for k in missing if k in _RECOVERY_SNIPPETS]
    recovery_text = "\n".join(recovery_parts) if recovery_parts else ""

    report = IntegrityReport(
        status=status,
        coverage_pct=pct,
        present_blocks=present,
        missing_blocks=missing,
        recovery_text=recovery_text,
        context_pressure=(status != "INTACT"),
    )

    if report.context_pressure:
        _log.warning(
            "identity_integrity: context_pressure_detected status=%s missing=%s coverage=%.0f%%",
            status, missing, pct,
        )

    return report
