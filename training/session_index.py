"""
training/session_index.py — per-session statistics aggregator.

Accumulates turn counts, energy, action and tone distribution.
Produces the summary dict written to summary_<session_id>.json at close.
"""
from collections import Counter


class SessionIndex:
    def __init__(self, session_id: str):
        self._session_id = session_id
        self._turns      = 0
        self._energies: list = []
        self._actions    = Counter()
        self._tones      = Counter()

    def track(self, action: str, tone: str, energy: float) -> None:
        self._turns += 1
        self._energies.append(energy)
        if action:
            self._actions[action] += 1
        if tone:
            self._tones[tone] += 1

    def summary(self) -> dict:
        avg_e = round(sum(self._energies) / len(self._energies), 3) if self._energies else 0.0
        return {
            "session_id":   self._session_id,
            "turns":        self._turns,
            "avg_energy":   avg_e,
            "actions_used": dict(self._actions),
            "tones_used":   dict(self._tones),
        }
