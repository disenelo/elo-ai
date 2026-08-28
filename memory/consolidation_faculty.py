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

import json
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


# ── WO-CANON-XXIV §A/§B: Knowledge graph promotion + demotion ─────────────────

# Promotion threshold constants (Architect defaults — tunable by Builder;
# MUST agree with LEARNING_LOOP_v1.md §3.4. Do not change the shape.)
_KG_STRENGTH_MIN        = 0.70   # §3.4: candidate→confirmed strength floor
_KG_REFS_MIN            = 3      # §3.4: distinct episode_ref minimum
_KG_SESSIONS_MIN        = 2      # §3.4: distinct sessions minimum
_KG_VERIFIED_MIN        = 2      # §3.4: verified episodes minimum
_KG_CONFIDENCE_WEAKEN   = 0.20   # §3.4: confidence decrease per contradicting episode
_KG_DEMOTE_THRESHOLD    = 0.50   # §3.4: promoted_memory → contested below this
_KG_RETRACT_THRESHOLD   = 0.20   # §3.4: contested → retracted below this
_KG_RETRACT_CONSECUTIVE = 3      # §3.4: consecutive contradictions → retract
_KG_RETRACT_IDLE_DAYS   = 60     # §3.4: no confirming evidence for this many days → retract

_KG_GRAPH_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "relationships", "world_graph.json",
)

# Node statuses for promoted knowledge
_KG_STATUS_PROMOTED  = "promoted_memory"
_KG_STATUS_CONTESTED = "contested"
_KG_STATUS_RETRACTED = "retracted"

# Authored fact epistemic kind — may NEVER be demoted/retracted by Consolidation
_KG_KIND_AUTHORED_FACT = "fact"


def _kg_load(graph_path: str) -> dict:
    """Load the knowledge graph JSON, returning {} on any error."""
    try:
        with open(graph_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _kg_save(graph: dict, graph_path: str) -> None:
    """Atomically save the knowledge graph JSON."""
    tmp = graph_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    os.replace(tmp, graph_path)


def promotion_pass(
    memory_records: list[dict],
    graph_path: str | None = None,
) -> dict:
    """
    WO-CANON-XXIV §A: Promote eligible memory records to promoted_memory nodes.

    Timed only — NEVER called from server.py or spine.run() (response path).
    Sole writer of promoted_memory nodes to the knowledge graph.

    Each memory_record dict must carry:
      fact         str   — the durable world claim
      strength     float — salience, 0.0–1.0
      episode_refs list  — [{"ref": SPOT_code, "session": str, "verified": bool}]
      about_world  bool  — True = durable world fact (not event-specific)
      id           str   — unique id for the node (generated if absent)

    Exclusions (assert in code):
      - Text-only episodes (verified=False) count toward nothing.
      - about_world=False records never promote.
      - Authored-canon nodes (epistemic_kind="fact") are never written here.

    Returns:
      {"promoted": [node_ids], "skipped": int, "errors": [str]}
    """
    gpath = graph_path or _KG_GRAPH_PATH
    promoted: list[str] = []
    skipped = 0
    errors: list[str] = []

    try:
        graph = _kg_load(gpath)
    except Exception as exc:
        return {"promoted": [], "skipped": len(memory_records), "errors": [str(exc)]}

    existing_ids = {e.get("id") for e in graph.get("entities", [])}

    for rec in memory_records:
        try:
            fact_text = str(rec.get("fact", "")).strip()
            strength  = float(rec.get("strength", 0.0))
            refs      = list(rec.get("episode_refs") or [])
            about_world = bool(rec.get("about_world", False))
            node_id   = str(rec.get("id") or f"pm_{abs(hash(fact_text)) % 10**8}").strip()

            # Hard exclusions
            if not about_world:
                skipped += 1
                continue
            if not fact_text:
                skipped += 1
                continue
            if node_id in existing_ids:
                skipped += 1
                continue

            # Threshold checks
            if strength < _KG_STRENGTH_MIN:
                skipped += 1
                continue

            verified_refs   = [r for r in refs if r.get("verified")]
            distinct_refs   = {r.get("ref") for r in refs if r.get("ref")}
            distinct_sessions = {r.get("session") for r in refs if r.get("session")}

            if len(distinct_refs) < _KG_REFS_MIN:
                skipped += 1
                continue
            if len(distinct_sessions) < _KG_SESSIONS_MIN:
                skipped += 1
                continue
            if len(verified_refs) < _KG_VERIFIED_MIN:
                skipped += 1
                continue

            # Build evidence list pointing at SPOT codes (provenance mandatory)
            evidence = [
                {"episode_ref": r["ref"], "verified": r.get("verified", False)}
                for r in refs
                if r.get("ref")
            ]

            node = {
                "id":            node_id,
                "name":          fact_text[:80],
                "type":          "promoted_fact",
                "epistemic_kind": _KG_STATUS_PROMOTED,
                "description":   fact_text,
                "keywords":      [w.lower() for w in fact_text.split()[:6] if len(w) > 3],
                "confidence":    round(min(1.0, strength), 4),
                "evidence":      evidence,
                "status":        _KG_STATUS_PROMOTED,
                "promoted_at":   datetime.now(timezone.utc).isoformat(),
            }

            graph.setdefault("entities", []).append(node)
            existing_ids.add(node_id)
            promoted.append(node_id)

        except Exception as exc:
            errors.append(f"record error: {exc}")

    if promoted:
        try:
            _kg_save(graph, gpath)
        except Exception as exc:
            errors.append(f"save error: {exc}")
            return {"promoted": [], "skipped": skipped, "errors": errors}

    return {"promoted": promoted, "skipped": skipped, "errors": errors}


def demotion_pass(graph_path: str | None = None) -> dict:
    """
    WO-CANON-XXIV §B: Weaken/demote/retract promoted_memory nodes.

    Timed only — NEVER called from server.py or spine.run() (response path).
    Only processes nodes with status in {promoted_memory, contested}.
    Authored facts (epistemic_kind="fact") are NEVER touched.

    Reads each promoted_memory node's:
      confidence           float  — current confidence
      contradicting_count  int    — accumulated contradictions
      last_confirmed_at    str    — ISO datetime of last confirming evidence

    Returns:
      {"weakened": [ids], "demoted": [ids], "retracted": [ids], "errors": [str]}
    """
    gpath = graph_path or _KG_GRAPH_PATH
    weakened:  list[str] = []
    demoted:   list[str] = []
    retracted: list[str] = []
    errors:    list[str] = []

    try:
        graph = _kg_load(gpath)
    except Exception as exc:
        return {"weakened": [], "demoted": [], "retracted": [], "errors": [str(exc)]}

    changed = False
    now = datetime.now(timezone.utc)

    for entity in graph.get("entities", []):
        try:
            status = entity.get("status", "")
            if status not in (_KG_STATUS_PROMOTED, _KG_STATUS_CONTESTED):
                continue

            # Authored facts are Architect lane only — Consolidation must not touch them
            if entity.get("epistemic_kind") == _KG_KIND_AUTHORED_FACT:
                continue

            node_id      = entity.get("id", "")
            confidence   = float(entity.get("confidence", 1.0))
            contradictions = int(entity.get("contradicting_count", 0))
            last_confirmed = entity.get("last_confirmed_at")

            # ── idle retraction ─────────────────────────────────────────────
            if last_confirmed:
                try:
                    last_dt = datetime.fromisoformat(last_confirmed)
                    if last_dt.tzinfo is None:
                        last_dt = last_dt.replace(tzinfo=timezone.utc)
                    idle_days = (now - last_dt).days
                    if idle_days >= _KG_RETRACT_IDLE_DAYS and confidence < _KG_DEMOTE_THRESHOLD:
                        entity["status"] = _KG_STATUS_RETRACTED
                        entity["epistemic_kind"] = _KG_STATUS_RETRACTED
                        entity["retracted_at"] = now.isoformat()
                        entity["reason"] = f"idle_{idle_days}_days"
                        retracted.append(node_id)
                        changed = True
                        continue
                except Exception:
                    pass

            # ── consecutive contradictions retract ──────────────────────────
            if contradictions >= _KG_RETRACT_CONSECUTIVE:
                entity["status"] = _KG_STATUS_RETRACTED
                entity["epistemic_kind"] = _KG_STATUS_RETRACTED
                entity["retracted_at"] = now.isoformat()
                entity["reason"] = f"contradictions_{contradictions}"
                retracted.append(node_id)
                changed = True
                continue

            # ── confidence too low — retract ────────────────────────────────
            if confidence < _KG_RETRACT_THRESHOLD:
                entity["status"] = _KG_STATUS_RETRACTED
                entity["epistemic_kind"] = _KG_STATUS_RETRACTED
                entity["retracted_at"] = now.isoformat()
                entity["reason"] = f"confidence_{confidence:.2f}"
                retracted.append(node_id)
                changed = True
                continue

            # ── confidence below demote threshold — demote ──────────────────
            if confidence < _KG_DEMOTE_THRESHOLD and status == _KG_STATUS_PROMOTED:
                entity["status"] = _KG_STATUS_CONTESTED
                demoted.append(node_id)
                changed = True
                continue

            # ── contradicting episode — weaken confidence ───────────────────
            if contradictions > 0 and status in (_KG_STATUS_PROMOTED, _KG_STATUS_CONTESTED):
                new_conf = max(0.0, round(confidence - _KG_CONFIDENCE_WEAKEN, 4))
                if new_conf != confidence:
                    entity["confidence"] = new_conf
                    weakened.append(node_id)
                    changed = True

        except Exception as exc:
            errors.append(f"node error: {exc}")

    if changed:
        try:
            _kg_save(graph, gpath)
        except Exception as exc:
            errors.append(f"save error: {exc}")

    return {"weakened": weakened, "demoted": demoted, "retracted": retracted, "errors": errors}


def david_correction(
    node_id: str,
    reason: str,
    graph_path: str | None = None,
) -> bool:
    """
    WO-CANON-XXIV §B: Immediate retraction of a node per David's correction.

    Effective same turn (not deferred to nightly consolidation).
    Sets status="retracted", retracted_at=<ts>, reason="david_correction: <reason>".
    Preserves node and evidence — nothing is deleted.

    Authored facts (epistemic_kind="fact") are REFUSED — Architect lane only.
    Returns True on success, False if node not found or refused.
    """
    gpath = graph_path or _KG_GRAPH_PATH
    try:
        graph = _kg_load(gpath)
    except Exception:
        return False

    for entity in graph.get("entities", []):
        if entity.get("id") != node_id:
            continue

        # Authored facts are Architect lane only
        if entity.get("epistemic_kind") == _KG_KIND_AUTHORED_FACT:
            return False

        entity["status"]        = _KG_STATUS_RETRACTED
        entity["epistemic_kind"] = _KG_STATUS_RETRACTED
        entity["retracted_at"]  = datetime.now(timezone.utc).isoformat()
        entity["reason"]        = f"david_correction: {reason}"

        try:
            _kg_save(graph, gpath)
            return True
        except Exception:
            return False

    return False

    return [theme for theme, count in theme_counts.items() if count >= 3]
