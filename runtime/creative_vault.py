"""
runtime/creative_vault.py — WO-CREATIVE-VAULT-001

Persistent creative vault: captures creative moments (ideas, decisions,
aesthetic positions, concepts) during sessions and makes them retrievable
in future sessions. Unblocks COG-029 (creative insight retention).

Write path: record_creative() — called on build/expand turns when eLo
produces a substantive creative output.
Read path: get_creative_summary() — compact text for g_ctx injection so
eLo can reference prior creative work from the first turn of a session.
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid

_log = logging.getLogger(__name__)

_ROOT         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_VAULT_FILE   = os.path.join(_ROOT, "self", "journals", "creative_vault.jsonl")


def record_creative(
    content: str,
    type: str = "idea",
    tags: list[str] | None = None,
    significance: float = 0.7,
    source: str = "conversation",
    session_id: str | None = None,
) -> None:
    """Write a creative entry to the vault. Fire-and-forget — never raises."""
    try:
        if not content or not content.strip():
            return
        if significance < 0.6:
            return

        if session_id is None:
            try:
                from runtime.session_events import _session_id as _sid
                session_id = _sid
            except Exception:
                session_id = None

        entry = {
            "vault_id":   str(uuid.uuid4()),
            "ts":         time.time(),
            "session_id": session_id or "unknown",
            "type":       type,
            "content":    content.strip(),
            "tags":       tags or [],
            "significance": significance,
            "source":     source,
        }
        os.makedirs(os.path.dirname(_VAULT_FILE), exist_ok=True)
        with open(_VAULT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        _log.warning("creative_vault.record_creative failed: %s", e)


def get_recent_creative(n: int = 5) -> list[dict]:
    """Return the n most recent creative vault entries."""
    try:
        entries: list[dict] = []
        with open(_VAULT_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
        return entries[-n:]
    except FileNotFoundError:
        return []
    except Exception as e:
        _log.warning("creative_vault.get_recent_creative failed: %s", e)
        return []


def get_creative_summary(n: int = 5) -> str:
    """
    Return compact text of recent creative vault entries for g_ctx injection.
    Returns empty string when vault is empty.
    """
    try:
        entries = get_recent_creative(n)
        if not entries:
            return ""

        lines = []
        for e in entries:
            ts = e.get("ts", 0)
            age_h = int((time.time() - ts) / 3600)
            age_str = f"{age_h}h ago" if age_h < 48 else f"{age_h // 24}d ago"
            content = e.get("content", "")[:100]
            etype = e.get("type", "idea")
            lines.append(f"[{etype}, {age_str}] {content}")

        return "Creative vault (prior work): " + " | ".join(lines) + "."
    except Exception as e:
        _log.warning("creative_vault.get_creative_summary failed: %s", e)
        return ""
