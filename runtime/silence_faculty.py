"""
runtime/silence_faculty.py — Silence as a first-class cognitive action

The 500+ question list asks:
  IS ELO: — Capable of Silence?
  - can eLo resist the pressure to always produce content?
  - can eLo stay silent when silence is the right response?
  - can eLo choose not to respond?
  - can eLo choose to say very little?
  - can eLo be comfortable with not filling the space?

These are not rhetorical. Without an explicit silence faculty, the LLM's
default bias is to always produce content. Adding more tokens to every turn
is not neutrally helpful — it is a distortion of the relationship.

This module:
  1. Detects when the SPG edge_hint for the current turn is 'silence'
  2. Detects when the recent interaction pattern shows a silence cluster
  3. Injects a permission block that explicitly grants eLo the right NOT to speak
  4. When the session silence rate exceeds a threshold, warns eLo against
     over-responding — content is not always the right move.

THE CAUSAL CHAIN:
  edge_hint (SPG classification) → silence_faculty → [SILENCE PERMISSION] block
  → LLM prompt → shorter/absent response → stored silence signal → future calibration

THE REALLY HARD TEST:
  show me where silence is stored:  data/spg_signals.jsonl (edge_hint='silence')
  show me where it changes eLo:     silence_faculty_prompt_block() → system prompt
  show me where it becomes behaviour: the LLM reads [SILENCE PERMISSION] and may respond
                                      with one word, a pause marker, or nothing

CRITICAL DISTINCTION:
  silence ≠ failure to respond (no data)
  silence == deliberate choice to not add content

Without this module, silence has no causal path to behaviour.
With it, eLo can genuinely choose not to speak.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_log = logging.getLogger(__name__)

_ROOT    = Path(__file__).parent.parent
_SIGNALS = _ROOT / "data" / "spg_signals.jsonl"

# Thresholds
RECENT_N          = 20   # look back this many signals for recent pattern
SILENCE_RATE_WARN = 0.15 # if recent silence rate > this, warn against over-responding
SILENCE_RATE_CALL = 0.30 # if recent silence rate > this, the pressure to be quiet is strong


@dataclass
class SilenceRead:
    """Result of reading the silence state for this turn."""
    is_silence_turn:    bool   # current edge_hint == 'silence'
    recent_silence_rate: float  # fraction of last RECENT_N signals that were 'silence'
    recent_silence_count: int
    recent_total:       int
    # derived
    should_warn:        bool   # warn eLo against over-responding
    should_call:        bool   # actively call for silence (strong signal)

    @property
    def is_silence_moment(self) -> bool:
        return self.is_silence_turn or self.should_warn


def read_silence(edge_hint: str = "", signals_path: Optional[Path] = None) -> SilenceRead:
    """
    Read the silence state for the current turn.
    Never raises — returns a safe default on any error.
    """
    path = signals_path or _SIGNALS
    try:
        all_signals: list[dict] = []
        if Path(path).exists():
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        all_signals.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        recent = all_signals[-RECENT_N:] if len(all_signals) >= RECENT_N else all_signals
        silence_count = sum(1 for s in recent if s.get("edge_hint") == "silence")
        rate = silence_count / max(len(recent), 1)

        return SilenceRead(
            is_silence_turn      = edge_hint.lower().strip() == "silence",
            recent_silence_rate  = round(rate, 4),
            recent_silence_count = silence_count,
            recent_total         = len(recent),
            should_warn          = rate >= SILENCE_RATE_WARN,
            should_call          = rate >= SILENCE_RATE_CALL,
        )

    except Exception as exc:
        _log.warning("silence_faculty: read failed (non-fatal): %s", exc)
        return SilenceRead(
            is_silence_turn=False,
            recent_silence_rate=0.0,
            recent_silence_count=0,
            recent_total=0,
            should_warn=False,
            should_call=False,
        )


def silence_faculty_prompt_block(edge_hint: str = "", signals_path: Optional[Path] = None) -> str:
    """
    Build a prompt block that grants eLo explicit permission NOT to speak.

    Returns "" when silence is not relevant to this turn.
    Returns a [SILENCE PERMISSION] block when the current turn is a silence moment
    or the recent pattern shows silence clustering.

    This is the only place in the architecture that explicitly grants permission
    to produce less content, or no content. Without this block, the LLM's
    default bias is to always fill space.

    Never raises.
    """
    try:
        state = read_silence(edge_hint=edge_hint, signals_path=signals_path)

        if not state.is_silence_turn and not state.should_warn:
            return ""

        lines = ["[SILENCE PERMISSION — this is a moment where less is more]"]

        if state.is_silence_turn:
            lines.append("  The current signal is: SILENCE.")
            lines.append("  This means: do not fill the space.")
            lines.append("  Valid responses: one word. A short acknowledgement. Nothing.")
            lines.append("  Silence is not failure. Silence is the right action here.")

        if state.should_call:
            lines.append(
                f"  Recent pattern: {state.recent_silence_count} of last {state.recent_total} "
                f"interactions were silence ({state.recent_silence_rate:.0%})."
            )
            lines.append("  The pressure to be quiet is strong right now.")
            lines.append("  Resist the impulse to add more. Let the space stay open.")

        elif state.should_warn:
            lines.append(
                f"  Recent pattern: {state.recent_silence_count} of last {state.recent_total} "
                f"interactions were silence ({state.recent_silence_rate:.0%})."
            )
            lines.append("  Consider whether adding content is actually useful here.")

        lines.append("  Permission granted: you do not have to speak.")
        return "\n".join(lines)

    except Exception as exc:
        _log.warning("silence_faculty_prompt_block failed (non-fatal): %s", exc)
        return ""
