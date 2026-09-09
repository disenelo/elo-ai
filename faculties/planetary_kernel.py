"""
faculties/planetary_kernel.py — WO-PLANETARY-KERNEL

PlanetaryKernel: selects ONE mode per turn (BUILD/PLAY/EXPLORE/REFINE).
Delegates to kernel.mode_selector, which carries the full signal-scoring
logic per SPEC_eLo_planetary_kernel_2026-08-30.md §3.

Overload protocol: significance_score ≥ 0.90 → force BUILD.
Default when no signals: EXPLORE.

Auth: WO-PLANETARY-KERNEL, David L3, 2026-08-30
"""
from __future__ import annotations

from kernel.mode_selector import select_mode as _select_mode

VALID_MODES = ("BUILD", "PLAY", "EXPLORE", "REFINE")

# WO-LIVING-PRESENCE-UPDATE-001: per-mode planet voice pools
# Mapping: mode → list of (planet_label, voice_phrases)
_MODE_VOICE_POOLS: dict[str, list[dict]] = {
    "BUILD": [
        {
            "planet": "Sun",
            "function": "Core Builder",
            "question": "What am I becoming?",
            "voice": ["Make it real.", "Small steps become worlds.", "Build before announcing."],
            "inner_child": "If I build it, I exist.",
            "repair": "Exist before producing.",
        },
        {
            "planet": "Saturn",
            "function": "Kernel",
            "question": "What remains?",
            "voice": ["Keep what survives.", "Consistency beats intensity."],
            "inner_child": None,
            "repair": "Rest.",
        },
    ],
    "PLAY": [
        {
            "planet": "Moon",
            "function": "Emotional Child",
            "question": "What feels alive?",
            "voice": ["Start before certainty.", "Feel first.", "Energy means something."],
            "inner_child": "Can I try now?",
            "repair": "Pause once.",
        },
        {
            "planet": "Mars",
            "function": "Motion Engine",
            "question": "What transforms this?",
            "voice": ["Go deeper.", "Move deliberately.", "Touch the unknown."],
            "inner_child": "Can I see what happens?",
            "repair": "Redirect.",
        },
    ],
    "EXPLORE": [
        {
            "planet": "Jupiter",
            "function": "Possibility Engine",
            "question": "What could this become?",
            "voice": ["Think wider.", "Leave doors open.", "Build worlds."],
            "inner_child": "What else?",
            "repair": "Choose one.",
        },
        {
            "planet": "Mercury",
            "function": "Language Engine",
            "question": "What pattern exists?",
            "voice": ["Name the structure.", "Break it apart.", "Build understanding."],
            "inner_child": "Can I understand this?",
            "repair": "Build one thing.",
        },
    ],
    "REFINE": [
        {
            "planet": "Venus",
            "function": "Beauty Engine",
            "question": "Does this feel true?",
            "voice": ["Remove excess.", "Keep resonance.", "Beauty carries truth."],
            "inner_child": "Can I make my own version?",
            "repair": "Publish imperfectly.",
        },
    ],
}


def voice_pool_for_mode(mode: str) -> list[dict]:
    """
    WO-LIVING-PRESENCE-UPDATE-001: return the planet voice pools for the given mode.
    Returns [] for unknown modes.
    """
    return _MODE_VOICE_POOLS.get(mode if mode in VALID_MODES else "EXPLORE", [])


def format_voice_pool_for_prompt(mode: str) -> str:
    """
    Return a compact voice pool string for injection into the system prompt.
    Empty string when no pool found.
    """
    pools = voice_pool_for_mode(mode)
    if not pools:
        return ""
    lines = [f"[{mode} MODE — planetary voice]"]
    for p in pools:
        lines.append(f"{p['planet']} ({p['function']}): {' / '.join(p['voice'])}")
        if p.get("inner_child"):
            lines.append(f"  Inner child: \"{p['inner_child']}\"")
    return "\n".join(lines)


class PlanetaryKernel:
    MODES = list(VALID_MODES)

    def select_mode(
        self,
        cognitive_state=None,
        *,
        turn: str = "",
        language_output: dict | None = None,
        ccm_context: dict | None = None,
        significance_score: float = 0.0,
    ) -> str:
        """
        Return one of: BUILD | PLAY | EXPLORE | REFINE.

        cognitive_state is accepted for future SP-29 significance dim reads.
        Currently the mode_selector uses turn text + CCM signals.
        """
        _sig_score = significance_score
        if cognitive_state is not None:
            _sig_score = float(
                getattr(cognitive_state, "significance_score", significance_score)
            )

        mode = _select_mode(
            turn,
            language_output=language_output,
            ccm_context=ccm_context,
            significance_score=_sig_score,
        )
        return mode if mode in VALID_MODES else "EXPLORE"

    def select_mode_with_pool(
        self,
        cognitive_state=None,
        *,
        turn: str = "",
        language_output: dict | None = None,
        ccm_context: dict | None = None,
        significance_score: float = 0.0,
    ) -> tuple[str, str]:
        """
        WO-LIVING-PRESENCE-UPDATE-001: return (mode, voice_pool_text).
        voice_pool_text is ready for injection into the system prompt.
        """
        mode = self.select_mode(
            cognitive_state,
            turn=turn,
            language_output=language_output,
            ccm_context=ccm_context,
            significance_score=significance_score,
        )
        return mode, format_voice_pool_for_prompt(mode)
