"""
tools/truth_sync.py — Truth Arbitration + Synchronization Protocol for eLo OS.

Three domains. One truth. No drift.

  Runtime  → source of truth for CURRENT STATE
  GitHub   → source of truth for STRUCTURE (versioned code, agent definitions)
  Obsidian → source of truth for MEANING (narrative, reasoning, memory compression)

If conflicts:
  - Runtime wins for state
  - GitHub wins for structure
  - Obsidian wins for meaning

Sync flows implemented here:
  A. Runtime → Obsidian  (auto-compress on turn threshold or significant CAL action)
  B. Runtime → GitHub    (commit message generation — never auto-commits, user approves)
  C. Obsidian → Runtime  (already handled by obsidian_loader — this validates freshness)
  D. GitHub → Runtime    (local structure validation on request)

Drift detection:
  Structural  — expected Python modules present?
  Semantic    — Obsidian vault has notes for active projects?
  Behavioural — CAL action pools non-empty and reachable?

Entry points:
  maybe_compress(raw, response, action, state)  → called after every turn (server.py)
  detect_drift()                                → on-demand, user-triggered
  generate_commit_draft(scope, desc, context)   → on-demand, returns text only
"""
from __future__ import annotations

import os
import subprocess
from datetime import datetime

# ── Constants ─────────────────────────────────────────────────────────────────

# Compress to Obsidian every N turns, or on significant CAL actions
_COMPRESS_EVERY_N_TURNS = 15
_COMPRESS_ON_ACTIONS    = frozenset(["build", "connect", "reflect"])

# Key modules that must be present for structural integrity
_REQUIRED_MODULES = [
    "runtime/spine/spine.py",
    "runtime/spine/plan.py",
    "runtime/spine/control_plane.py",
    "runtime/prompt_builder.py",
    "runtime/backend_router.py",
    "memory/obsidian_loader.py",
    "memory/vault_layer.py",
    "memory/vault_codec.py",
    "memory/state_manager.py",
    "tools/tool_router.py",
    "tools/truth_sync.py",
    "voice/voice_engine.py",
    "ambient/ambient_engine.py",
    "blender_bridge/state_writer.py",
    "blender_bridge/exit_state.py",
    "server.py",
]

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Turn counter (module-level, resets when server restarts) ─────────────────

_turn_count: int       = 0
_last_compress_turn: int = 0


def _increment_turn() -> int:
    global _turn_count
    _turn_count += 1
    return _turn_count


def _should_compress(action: str) -> bool:
    """Return True if auto-compression threshold reached."""
    global _last_compress_turn
    turns_since = _turn_count - _last_compress_turn
    return (
        turns_since >= _COMPRESS_EVERY_N_TURNS
        or action.lower() in _COMPRESS_ON_ACTIONS
    )


# ── Flow A — Runtime → Obsidian ───────────────────────────────────────────────

def compress_to_obsidian(
    raw:              str,
    response:         str,
    action:           str,
    state:            dict,
    weight:           int | None = None,
    execution_report: object = None,
) -> str | None:
    """
    Integrate the current turn context into durable memory (Obsidian vault).

    Calls integrate_session() (Reflection Faculty) — replaces the old
    vault_layer.compress_session() path. Integration grows; compression stores.

    WO-004 (S8): accepts ExecutionReport and passes it to integrate_session()
    so the Reflection Faculty can measure the intention↔reality gap.

    Called when threshold is met — not every turn.
    Returns the spot code of the written record, or None on failure.
    """
    try:
        from runtime.reflection_faculty import integrate_session

        project = _infer_project(state)
        session_summary = _build_session_summary(raw, response, action, state)

        if weight is None:
            weight = 7 if action.lower() in ("build", "connect") else 5

        tags = [action.lower(), project]

        result = integrate_session(
            session_summary,
            project=project,
            weight=weight,
            tags=tags,
            action=action,
            execution_report=execution_report,
        )

        global _last_compress_turn
        _last_compress_turn = _turn_count

        if result.get("skipped"):
            return None

        spot = result.get("spot")
        if result.get("error"):
            print(f"[truth-sync] integrate_session vault error: {result['error']}")
        if spot:
            print(f"[truth-sync] integrated turn {_turn_count} → {spot}")

        # WO-115: reflection reaches the self-model — lesson written to EloSelfState.
        # 0037/WO-ONEBRAIN-015: through the single-authority mutator (load→mutate→save
        # atomically) so a concurrent server write cannot clobber this lesson.
        if result.get("lesson"):
            try:
                from self.elo_self_model import (
                    update as _sm_update, apply_lesson as _sm_apply,
                )
                _lesson = result["lesson"]
                _sm_update(lambda s: _sm_apply(s, _lesson))
            except Exception:
                pass

        return spot
    except Exception as e:
        print(f"[truth-sync] compress_to_obsidian failed: {e}")
        return None


def _infer_project(state: dict) -> str:
    """Infer Obsidian project domain from session state."""
    topics = state.get("last_topics", [])
    topic_str = " ".join(t.lower() for t in topics)
    if any(k in topic_str for k in ("game", "elo-planet", "unity", "weapon", "enemy")):
        return "elo-game"
    if any(k in topic_str for k in ("robot", "servo", "neopixel", "raspberry")):
        return "elo-robot"
    if any(k in topic_str for k in ("book", "story", "narrative", "k-7", "chunk")):
        return "elo-book"
    if any(k in topic_str for k in ("os", "spine", "server", "backend", "memory", "vault", "sync")):
        return "elo-os"
    return "general"


def _build_session_summary(raw: str, response: str, action: str, state: dict) -> str:
    """Assemble a compact session summary for vault compression."""
    topics    = state.get("last_topics", [])
    session_n = state.get("session_count", 0)
    emotion   = state.get("emotion", "neutral")
    loops     = state.get("session_anchor", {}).get("open_loops", [])

    lines = [
        f"Session {session_n} — turn {_turn_count} — action: {action.upper()}",
        f"User: {raw[:200]}",
        f"eLo: {response[:200]}",
    ]
    if topics:
        lines.append(f"Active topics: {', '.join(topics[:5])}")
    if loops:
        lines.append(f"Open loops: {', '.join(str(l) for l in loops[:3])}")
    lines.append(f"Emotional tone: {emotion}")
    return "\n".join(lines)


# ── Flow A — Public trigger ───────────────────────────────────────────────────

def maybe_compress(raw: str, response: str, action: str, state: dict) -> None:
    """
    Called after every turn from server.py.
    Fires compression only when threshold is met — lightweight guard on all other turns.
    """
    _increment_turn()
    if _should_compress(action):
        compress_to_obsidian(raw, response, action, state)


# ── Flow B — Runtime → GitHub (commit draft, user-approved only) ──────────────

def generate_commit_draft(
    scope:           str,
    change_desc:     str,
    runtime_context: str = "",
    risk_level:      str = "low",
) -> str:
    """
    Generate a structured commit message for a code change.
    NEVER commits automatically. Returns formatted text for user review.

    Args:
        scope           — module scope e.g. "spine", "voice", "tools/truth_sync"
        change_desc     — concise description of the change
        runtime_context — what triggered this change (eLo OS context)
        risk_level      — "low" | "medium" | "high"

    Returns:
        Formatted commit message string.
    """
    # Classify type from description keywords
    lower = change_desc.lower()
    if any(k in lower for k in ("add", "new", "create", "introduce")):
        commit_type = "feat"
    elif any(k in lower for k in ("fix", "repair", "correct", "resolve")):
        commit_type = "fix"
    elif any(k in lower for k in ("refactor", "restructure", "reorganise", "move")):
        commit_type = "refactor"
    else:
        commit_type = "chore"

    # Detect changed files using git (non-destructive read)
    changed_files = _list_changed_files()
    files_str = "\n".join(f"  {f}" for f in changed_files[:10]) if changed_files else "  (run git status to confirm)"

    draft = f"""{commit_type}({scope}): {change_desc}

runtime-context:
  trigger: {runtime_context or 'manual'}
  affected-modules: {scope}
  risk-level: {risk_level}

changed-files:
{files_str}

Co-Authored-By: eLo OS Truth Sync <noreply@disenelo.com>"""
    return draft


def _list_changed_files() -> list[str]:
    """List currently modified tracked files via git status (read-only)."""
    try:
        result = subprocess.run(
            ["git", "-C", _ROOT, "status", "--short"],
            capture_output=True, text=True, timeout=5.0,
        )
        if result.returncode == 0:
            lines = [ln.strip() for ln in result.stdout.strip().split("\n") if ln.strip()]
            return [ln[3:].strip() for ln in lines if len(ln) > 3]
    except Exception:
        pass
    return []


# ── Flow C — Obsidian → Runtime validation ────────────────────────────────────

def validate_obsidian_sync() -> dict:
    """
    Check that the Obsidian vault has notes for active runtime projects.
    Returns: {status, active_projects_found, missing_projects, note_count}
    """
    try:
        from memory.obsidian_loader import load
        pack = load(force=False)
        context = pack.context_block if pack else ""
        note_count = context.count("##") if context else 0

        active = ["elo-os", "elo-game", "elo-robot"]
        found, missing = [], []
        low = context.lower() if context else ""
        for proj in active:
            (found if any(k in low for k in [proj, proj.replace("-", " ")]) else missing).append(proj)

        return {
            "status":                "ok" if not missing else "partial",
            "active_projects_found": found,
            "missing_projects":      missing,
            "note_count":            note_count,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Flow D — GitHub → Runtime structure validation ────────────────────────────

def validate_structure() -> dict:
    """
    Check that all required runtime modules are present on disk.
    Returns: {status, present, missing, drift_detected}
    """
    present, missing = [], []
    for rel_path in _REQUIRED_MODULES:
        full = os.path.join(_ROOT, rel_path)
        (present if os.path.exists(full) else missing).append(rel_path)

    return {
        "status":         "ok" if not missing else "drift",
        "present":        present,
        "missing":        missing,
        "drift_detected": bool(missing),
    }


# ── Drift detection — unified ─────────────────────────────────────────────────

def detect_drift(state: dict | None = None) -> dict:
    """
    Run all three drift checks. Returns a unified drift report.

    Drift types:
      structural  — required Python modules missing from disk
      semantic    — Obsidian vault missing notes for active projects
      behavioural — CAL action pool check (direct response pools reachable)
    """
    report: dict = {
        "timestamp":         datetime.now().isoformat(),
        "structural_drift":  [],
        "semantic_drift":    [],
        "behavioural_drift": [],
        "clean":             True,
    }

    # Structural
    struct = validate_structure()
    if struct["missing"]:
        report["structural_drift"] = struct["missing"]
        report["clean"] = False

    # Semantic
    obs = validate_obsidian_sync()
    if obs.get("missing_projects"):
        report["semantic_drift"] = obs["missing_projects"]
        report["clean"] = False

    # Behavioural — check direct response pools are importable and non-empty
    try:
        import server as _srv
        pool_checks = {
            "_PURE_GREETING_POOL":  getattr(_srv, "_PURE_GREETING_POOL", []),
            "_FAREWELL_POOL_SOUTH_LDN": getattr(_srv, "_FAREWELL_POOL_SOUTH_LDN", []),
            "_GUN_CHECK_POOL":      getattr(_srv, "_GUN_CHECK_POOL", []),
            "_EXISTENCE_POOL":      getattr(_srv, "_EXISTENCE_POOL", []),
        }
        empty_pools = [name for name, pool in pool_checks.items() if not pool]
        if empty_pools:
            report["behavioural_drift"] = empty_pools
            report["clean"] = False
    except Exception as e:
        report["behavioural_drift"] = [f"pool_check_failed: {e}"]
        report["clean"] = False

    return report


# ── Agent entry — called by tool_router ──────────────────────────────────────

def agent(query: str) -> str:
    """
    Tool agent entry. Handles truth sync commands from eLo OS tool routing.

    Recognised queries:
      "drift" / "check drift"     → detect_drift()
      "sync memory"               → compress_to_obsidian() (immediate, current state)
      "validate structure"        → validate_structure()
      "commit draft <desc>"       → generate_commit_draft()
      "obsidian sync"             → validate_obsidian_sync()
    """
    lower = query.lower().strip()

    if any(k in lower for k in ("drift", "check drift", "sync check")):
        try:
            from memory.state_manager import load as load_state
            state = load_state()
        except Exception:
            state = {}
        report = detect_drift(state)
        if report["clean"]:
            return "TRUTH SYNC: All three domains aligned. No drift detected."
        lines = ["TRUTH SYNC: Drift detected —"]
        if report["structural_drift"]:
            lines.append(f"  STRUCTURAL: missing {report['structural_drift']}")
        if report["semantic_drift"]:
            lines.append(f"  SEMANTIC: no Obsidian notes for {report['semantic_drift']}")
        if report["behavioural_drift"]:
            lines.append(f"  BEHAVIOURAL: {report['behavioural_drift']}")
        return "\n".join(lines)

    if any(k in lower for k in ("sync memory", "compress memory", "save memory")):
        try:
            from memory.state_manager import load as load_state
            state = load_state()
        except Exception:
            state = {}
        spot = compress_to_obsidian(query, "User-triggered sync.", "build", state)
        return f"TRUTH SYNC: Compressed to Obsidian → {spot}" if spot else "TRUTH SYNC: Compression failed — check vault path."

    if any(k in lower for k in ("validate structure", "check modules", "structure check")):
        result = validate_structure()
        if result["status"] == "ok":
            return f"TRUTH SYNC: Structure clean — {len(result['present'])} modules present."
        return f"TRUTH SYNC: Structural drift — missing: {result['missing']}"

    if any(k in lower for k in ("commit draft", "generate commit", "sync to github")):
        desc = lower.replace("commit draft", "").replace("generate commit", "").replace("sync to github", "").strip()
        draft = generate_commit_draft(scope="elo-os", change_desc=desc or "system update")
        return f"TRUTH SYNC: Commit draft —\n\n{draft}"

    if any(k in lower for k in ("obsidian sync", "obsidian check")):
        result = validate_obsidian_sync()
        return (
            f"TRUTH SYNC: Obsidian sync — {result['status']} "
            f"| found: {result.get('active_projects_found', [])} "
            f"| missing: {result.get('missing_projects', [])}"
        )

    return "TRUTH SYNC: Unknown command. Try: 'check drift', 'sync memory', 'validate structure', 'commit draft <desc>'"
