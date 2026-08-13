"""
memory/consolidation_faculty.py — Memory Consolidation Faculty (WO-011)

Timed faculty (integration window only — never response path).
Implements hippocampal replay: what lasts, what fades, what patterns emerge.

Spec: docs/architecture/Volume_VIII/01_Memory_Architecture.md §1.3–1.4
      docs/architecture/17_memory_update.md §6 (integrate_session)
      docs/architecture/Volume_V/06 (Reflection faculty companion)

Rules (MUST):
  - Never runs in the response path. Call at session close or idle only.
  - Atomic: a failed run preserves prior vault intact.
  - Identity (weight=9) and pinned records NEVER decay.
  - Personality-affecting outputs are proposals to Ch.7, never self-applied.
  - Memory Faculty is the only permanent-memory writer (D-F).
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone, timedelta
from typing import Any

_ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_VAULT    = os.environ.get("ELO_VAULT_PATH", os.path.join(_ROOT, "obsidian_vault"))
_MEM_DIR  = os.path.join(_VAULT, "09 Memory")
_SUM_DIR  = os.path.join(_MEM_DIR, "summary")

# ── Forgetting curve parameters ───────────────────────────────────────────────

_IDENTITY_FLOOR     = 8    # weight >= this: never decays (identity + pinned)
_DECAY_THRESHOLD    = 6    # weight < this: eligible for decay
_DECAY_AGE_DAYS     = 14   # minimum age before decay can apply
_DECAY_STEP         = 1    # weight decrease per consolidation pass
_REINFORCE_STEP     = 1    # weight increase per reinforcement event
_WEIGHT_CAP         = 9    # maximum allowed weight

# ── Weight label (mirrors vault_codec) ───────────────────────────────────────

def _weight_label(weight: int) -> str:
    labels = {9: "core identity", 8: "important", 7: "important", 6: "useful",
              5: "useful", 4: "useful", 3: "peripheral", 2: "peripheral",
              1: "fading", 0: "archived"}
    return labels.get(weight, "unknown")


# ── Frontmatter parsing ───────────────────────────────────────────────────────

def _parse_fm(content: str) -> dict:
    meta: dict = {}
    if not content.startswith("---"):
        return meta
    end = content.find("\n---", 3)
    if end == -1:
        return meta
    for line in content[3:end].splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip().strip("\"'")
    return meta


def _update_weight_in_content(content: str, new_weight: int) -> str:
    """Update the weight field in YAML frontmatter and body weight line."""
    label = _weight_label(new_weight)

    # Update frontmatter weight: field
    content = re.sub(
        r"(^weight:\s*)\d+",
        lambda m: f"{m.group(1)}{new_weight}",
        content,
        count=1,
        flags=re.MULTILINE,
    )

    # Update body display: **Weight:** N/9 (label)
    content = re.sub(
        r"\*\*Weight:\*\*\s*\d+/9\s*\([^)]*\)",
        f"**Weight:** {new_weight}/9 ({label})",
        content,
    )

    return content


# ── Forgetting curve ──────────────────────────────────────────────────────────

def apply_forgetting_curve(dry_run: bool = False) -> dict:
    """
    Scan vault summary notes and decay weak, old records.

    Rules:
      - weight >= _IDENTITY_FLOOR → protected, no decay.
      - weight < _DECAY_THRESHOLD AND note older than _DECAY_AGE_DAYS → decay by _DECAY_STEP.
      - Minimum weight after decay = 1 (never deleted, just faded).
      - Atomic: skips any file that fails to parse or write.

    Args:
        dry_run — if True, reports what WOULD be decayed without writing.

    Returns:
        {"decayed": [spot_codes], "protected": int, "errors": [str]}
    """
    decayed: list[str] = []
    protected: int = 0
    errors: list[str] = []

    if not os.path.isdir(_SUM_DIR):
        return {"decayed": decayed, "protected": protected, "errors": errors}

    cutoff = datetime.now(timezone.utc) - timedelta(days=_DECAY_AGE_DAYS)

    for fname in os.listdir(_SUM_DIR):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(_SUM_DIR, fname)
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()

            meta = _parse_fm(content)
            weight = int(meta.get("weight", 5))
            date_str = meta.get("date", "")
            spot = meta.get("spot", fname)

            # Identity floor — never decay
            if weight >= _IDENTITY_FLOOR:
                protected += 1
                continue

            # Weight above decay threshold — skip
            if weight >= _DECAY_THRESHOLD:
                continue

            # Age check — must be old enough
            if date_str:
                try:
                    record_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if record_date > cutoff:
                        continue
                except ValueError:
                    pass

            # Apply decay
            new_weight = max(1, weight - _DECAY_STEP)
            if not dry_run and new_weight != weight:
                new_content = _update_weight_in_content(content, new_weight)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)

            decayed.append(spot)

        except Exception as exc:
            errors.append(f"{fname}: {exc}")

    return {"decayed": decayed, "protected": protected, "errors": errors}


# ── Reinforcement ─────────────────────────────────────────────────────────────

def reinforce(spot_code: str, steps: int = 1) -> bool:
    """
    Strengthen a memory record by raising its weight (capped at _WEIGHT_CAP).
    Called when a memory is retrieved and used in a turn (referenced = relevant).

    Returns True if weight was changed, False if already at cap or not found.
    """
    fname = spot_code.replace("·", "-") + ".md"
    path = os.path.join(_SUM_DIR, fname)
    if not os.path.exists(path):
        return False
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        meta = _parse_fm(content)
        weight = int(meta.get("weight", 5))
        new_weight = min(_WEIGHT_CAP, weight + steps)
        if new_weight == weight:
            return False
        new_content = _update_weight_in_content(content, new_weight)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    except Exception:
        return False


# ── Consolidation faculty (main entry) ───────────────────────────────────────

def consolidate(
    session_summaries: list[dict],
    execution_reports: list[Any] | None = None,
    project: str = "general",
) -> dict:
    """
    Hippocampal replay — timed consolidation of the session.

    CRITICAL: Must only be called at session close or idle.
    Never call from the response path.

    Steps:
      1. Apply forgetting curve (decay old/weak memories).
      2. Integrate significant session episodes via integrate_session().
      3. Extract patterns (repeated themes → semantic elevation).
      4. Return consolidation report.

    Args:
        session_summaries:  List of {user, elo, action, ...} turn dicts from state.
        execution_reports:  Optional list of ExecutionReport objects from the session.
        project:            Domain for vault records.

    Returns:
        {
          "forgetting": decay result dict,
          "integrated": list of spot codes written,
          "patterns":   list of pattern strings detected,
          "errors":     list of error strings,
        }
    """
    integrated: list[str] = []
    patterns: list[str] = []
    errors: list[str] = []

    # ── 1. Forgetting curve ────────────────────────────────────────────────────
    forgetting_result: dict = {}
    try:
        forgetting_result = apply_forgetting_curve()
    except Exception as exc:
        errors.append(f"forgetting_curve: {exc}")

    # ── 2. Session integration ─────────────────────────────────────────────────
    if session_summaries:
        try:
            from runtime.reflection_faculty import integrate_session
            from memory.summariser import compress_session

            # Build a unified session summary from all turns
            session_text = compress_session(session_summaries)

            if session_text:
                # Find the most significant action in this session
                actions = [s.get("action", "") for s in session_summaries if s.get("action")]
                primary_action = max(set(actions), key=actions.count) if actions else ""

                exec_report = execution_reports[-1] if execution_reports else None

                result = integrate_session(
                    session_text,
                    project=project,
                    weight=7,    # session-level consolidation = important (7+)
                    tags=["consolidated", "session-close"],
                    action=primary_action,
                    execution_report=exec_report,
                )

                if result.get("spot"):
                    integrated.append(result["spot"])
                if result.get("error"):
                    errors.append(f"integrate_session: {result['error']}")

        except Exception as exc:
            errors.append(f"session_integration: {exc}")

    # ── 3. Pattern extraction (semantic elevation) ─────────────────────────────
    try:
        patterns = _extract_patterns(session_summaries)
    except Exception:
        pass

    return {
        "forgetting":  forgetting_result,
        "integrated":  integrated,
        "patterns":    patterns,
        "errors":      errors,
    }


def _extract_patterns(session_summaries: list[dict]) -> list[str]:
    """
    Detect repeated themes across the session that warrant semantic elevation.
    A theme repeated ≥3 times in different turns = a pattern worth noting.
    """
    from memory.summariser import _detect_themes
    theme_counts: dict[str, int] = {}
    for turn in session_summaries:
        text = (turn.get("user", "") + " " + turn.get("elo", "")).strip()
        for theme in _detect_themes(text):
            theme_counts[theme] = theme_counts.get(theme, 0) + 1

    return [theme for theme, count in theme_counts.items() if count >= 3]
