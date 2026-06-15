"""
training/collector.py — passive turn capture for eLo OS.

Activated when ELO_COLLECT=true in .env.
No behaviour modification. No online learning. Capture only.

One record per completed turn, written to datasets/organic/.
Quality-filtered: mock/fallback responses discarded.
Duplicate-detected: identical (input, response) pairs dropped.
"""
import hashlib
import os
import uuid

from training.dataset_writer import DatasetWriter
from training.session_index  import SessionIndex

_SYSTEM_VERSION   = "2.1"
_DISCARD_BACKENDS = {"mock", "fallback"}


class Collector:
    def __init__(self, base_dir: str):
        for sub in ("organic", "synthetic", "review", "final"):
            os.makedirs(os.path.join(base_dir, sub), exist_ok=True)

        self._session_id = str(uuid.uuid4())[:12]
        organic_dir      = os.path.join(base_dir, "organic")
        self._writer     = DatasetWriter(organic_dir, self._session_id)
        self._index      = SessionIndex(self._session_id)
        self._seen: set  = set()

    def record(
        self,
        user_input:      str,
        response:        str,
        backend_name:    str,
        exec_decision:   dict,
        attention_model: dict,
        presence:        dict,
    ) -> bool:
        """
        Record one completed turn. Returns True if saved, False if discarded.
        Never raises — all errors are silent to preserve conversation behaviour.
        """
        # Quality filters
        if len(response.strip()) < 3:
            return False
        if backend_name in _DISCARD_BACKENDS:
            return False

        # Duplicate detection
        _hash = hashlib.md5(f"{user_input}|{response}".encode()).hexdigest()
        if _hash in self._seen:
            return False
        self._seen.add(_hash)

        emo    = attention_model.get("emotional_context", {})
        energy = emo.get("energy", 0.5)
        action = exec_decision.get("action", "")
        tone   = exec_decision.get("tone", "")

        record = {
            "timestamp":       _now_iso(),
            "session_id":      self._session_id,
            "backend":         backend_name,
            "system_version":  _SYSTEM_VERSION,
            "user_input":      user_input,
            "response":        response,
            "intent":          exec_decision.get("intent", ""),
            "action":          action,
            "tone":            tone,
            "presence_state":  _safe_presence(presence),
            "memory_used":     _memory_summary(attention_model),
            "collection_type": "organic",
        }

        self._writer.write(record)
        self._index.track(action, tone, energy)
        return True

    def close(self) -> dict:
        """Finalise session. Writes summary file. Returns summary dict."""
        summary = self._index.summary()
        self._writer.close(summary)
        return summary


# ── helpers ───────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _safe_presence(presence: dict) -> dict:
    """Public motion fields only — no raw embeddings or debug state."""
    if not presence:
        return {}
    keep = {"animation", "intensity", "energy", "duration", "mood"}
    return {k: v for k, v in presence.items() if k in keep}


def _memory_summary(attention_model: dict) -> list:
    """Memory tier counts only — no raw text content."""
    high = attention_model.get("high_priority_memory", [])
    med  = attention_model.get("medium_priority_memory", [])
    out  = []
    if high:
        out.append(f"high:{len(high)}")
    if med:
        out.append(f"med:{len(med)}")
    return out
