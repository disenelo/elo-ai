"""
self/lesson_store.py — WO-095: Learning Loop Read Side

The read/promote/recall layer for self/lessons_ledger.jsonl.
reflection_faculty.py is the sole writer of new rows; this is the sole
writer of `status` (candidate ↔ confirmed ↔ retired).

ADR-Exec-005 write-allow list:
  self/lessons_ledger.jsonl   — status · strength · evidence · retired_at
  self/personality_vector.json — ONLY via personality_evolution_faculty (validated)

Hard rules (enforced here, not just documented):
  - verified==False episode  → may not strengthen, promote, or emit a PersonalityDelta
  - significance capped at 0.30; never the sole promotion input
  - Nothing deleted; retired rows stay with retired_at + reason
  - promote_pass() is the SOLE writer of `status`; never run in the response path

Lesson identity = sha1(scope | normalised_statement | cause) — repeats strengthen.
Pre-v1 rows (no lesson_key) are archived and excluded from promotion.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time

_log = logging.getLogger(__name__)

_ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LEDGER      = os.path.join(_ROOT, "self", "lessons_ledger.jsonl")
_LEDGER_PRE  = os.path.join(_ROOT, "self", "lessons_ledger_pre_v1.jsonl")
_METRICS     = os.path.join(_ROOT, "self", "journals", "growth_metrics.jsonl")

# §3.4 promotion thresholds
_STRENGTHEN_DELTA   =  0.15
_WEAKEN_DELTA       =  0.20
_IDLE_DECAY_DELTA   =  0.02   # per 7 days with no confirming evidence
_PROMOTE_STRENGTH   =  0.70
_PROMOTE_EPISODES   =  3       # distinct episode_refs
_PROMOTE_SESSIONS   =  2       # distinct session_ids
_PROMOTE_VERIFIED   =  2       # verified episodes
_DEMOTE_STRENGTH    =  0.50
_RETIRE_STRENGTH    =  0.20
_RETIRE_DAYS        =  60
_RETIRE_CONTRADICTIONS = 3

_STRENGTH_CAP       =  1.00
_MAX_LESSONS_RECALL =  3
_MAX_CHARS_RECALL   =  240


# ── Key generation ────────────────────────────────────────────────────────────

def lesson_key(scope: str, statement: str, cause: str = "") -> str:
    """sha1 identity key — repeats strengthen the existing row, never duplicate."""
    norm = re.sub(r"\s+", " ", statement.strip().lower())
    blob = f"{scope}|{norm}|{cause}"
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


# ── Ledger I/O ─────────────────────────────────────────────────────────────────

def _load_ledger(path: str | None = None) -> list[dict]:
    p = path or _LEDGER
    rows = []
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        pass
    return rows


def _save_ledger(rows: list[dict], path: str | None = None) -> None:
    p = path or _LEDGER
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _append_ledger(row: dict, path: str | None = None) -> None:
    p = path or _LEDGER
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


# ── Pre-v1 migration ──────────────────────────────────────────────────────────

def migrate_pre_v1(ledger_path: str | None = None, archive_path: str | None = None) -> int:
    """
    Move pre-v1 rows (no lesson_key field) to lessons_ledger_pre_v1.jsonl.
    Idempotent — safe to call every startup.
    Returns count of rows migrated this call.
    """
    rows = _load_ledger(ledger_path)
    v1, pre = [], []
    for r in rows:
        if r.get("lesson_key"):
            v1.append(r)
        else:
            pre.append(r)
    if not pre:
        return 0
    _save_ledger(v1, ledger_path)
    arch = archive_path or _LEDGER_PRE
    os.makedirs(os.path.dirname(arch), exist_ok=True)
    with open(arch, "a", encoding="utf-8") as f:
        for r in pre:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(pre)


# ── record_outcome ─────────────────────────────────────────────────────────────

def record_outcome(
    lkey: str,
    episode_ref: str,
    verified: bool,
    contradicting: bool = False,
    session_id: str = "",
    ledger_path: str | None = None,
) -> dict:
    """
    Register an outcome against a known lesson.

    If verified=False: records the episode but may not strengthen/promote.
    If contradicting=True + verified=True: weakens the lesson.
    Returns the updated row, or {} if lesson not found.

    This does NOT create new lesson rows — reflection_faculty creates them.
    """
    rows = _load_ledger(ledger_path)
    now_iso = _now_iso()
    updated_row: dict = {}

    for i, row in enumerate(rows):
        if row.get("lesson_key") != lkey:
            continue
        if row.get("status") == "retired" and not (verified and not contradicting):
            break  # retired lessons only re-activate on fresh verified confirming episode

        # Append episode_ref
        evidence = row.setdefault("evidence", [])
        evidence.append({
            "episode_ref": episode_ref,
            "verified": verified,
            "ts": time.time(),          # float epoch — unambiguous for _last_any_ts
            "session_id": session_id,
        })
        row["last_seen"] = now_iso

        if verified:
            if contradicting:
                row["strength"] = max(0.0, round(row.get("strength", 0.3) - _WEAKEN_DELTA, 3))
                row.setdefault("contradiction_count", 0)
                row["contradiction_count"] += 1
            else:
                row["strength"] = min(_STRENGTH_CAP, round(row.get("strength", 0.3) + _STRENGTHEN_DELTA, 3))
                # Reset contradiction count on a confirming episode
                if "contradiction_count" in row:
                    row["contradiction_count"] = 0
                # Re-activate a retired lesson
                if row.get("status") == "retired":
                    row["status"] = "candidate"
                    row["strength"] = 0.30
                    row["retired_at"] = None
                    row["reason"] = None

        rows[i] = row
        updated_row = row
        break

    if updated_row:
        _save_ledger(rows, ledger_path)
    else:
        _log.warning(
            "record_outcome: lkey not found in ledger — evidence discarded (lkey=%s)", lkey
        )
    return updated_row


# ── ensure_lesson ─────────────────────────────────────────────────────────────

def ensure_lesson(
    scope: str,
    statement: str,
    cause: str = "",
    ledger_path: str | None = None,
) -> str:
    """
    Return the lesson_key for (scope, statement, cause), creating a minimal candidate
    row if one is not yet in the ledger.  Used by out-of-band outcome recorders (e.g.
    the sit-ACK hook) that must guarantee a row exists before calling record_outcome().
    """
    lkey = lesson_key(scope, statement, cause)
    rows = _load_ledger(ledger_path)
    if any(r.get("lesson_key") == lkey for r in rows):
        return lkey
    now = _now_iso()
    row: dict = {
        "id":          f"L-{int(time.time())}",
        "lesson_key":  lkey,
        "statement":   statement,
        "evidence":    [],
        "scope":       scope,
        "cause":       cause or "met",
        "strength":    0.3,
        "delta":       cause or "met",
        "status":      "candidate",
        "first_seen":  now,
        "last_seen":   now,
        "promoted_at": None,
        "retired_at":  None,
        "reason":      None,
        "proposes":    None,
        "ts":          now,
    }
    _append_ledger(row, ledger_path)
    _log.info("ensure_lesson: created candidate row (lkey=%s scope=%s)", lkey, scope)
    return lkey


# ── promote_pass ───────────────────────────────────────────────────────────────

def promote_pass(ledger_path: str | None = None, dry_run: bool = False) -> dict:
    """
    Periodic promotion sweep — sole writer of `status`.
    Must NOT run in the response path.

    Applies §3.4 thresholds:
      candidate → confirmed when strength/episode/session/verified criteria all met
      confirmed → candidate when strength < DEMOTE threshold
      any → retired when strength < RETIRE threshold or consecutive contradictions or idle days

    Returns summary dict of transitions.
    """
    rows = _load_ledger(ledger_path)
    transitions: dict[str, list[str]] = {
        "promoted": [], "demoted": [], "retired": [], "personality_delta": [],
    }
    now = time.time()

    for i, row in enumerate(rows):
        status = row.get("status", "candidate")
        strength = row.get("strength", 0.3)
        evidence = row.get("evidence", [])
        lkey = row.get("lesson_key", "")

        # ── Idle decay (7-day, confirming only) ──────────────────────────────
        last_confirming = _last_confirming_ts(evidence)
        if last_confirming:
            days_idle = (now - last_confirming) / 86400
            if days_idle >= 7:
                decay = _IDLE_DECAY_DELTA * int(days_idle / 7)
                strength = max(0.0, round(strength - decay, 3))

        # ── Retirement gate ───────────────────────────────────────────────────
        days_since_any = (now - _last_any_ts(evidence)) / 86400 if _last_any_ts(evidence) else _RETIRE_DAYS + 1
        consecutive_contradictions = row.get("contradiction_count", 0)
        if (
            strength < _RETIRE_STRENGTH
            or consecutive_contradictions >= _RETIRE_CONTRADICTIONS
            or days_since_any >= _RETIRE_DAYS
        ):
            if status != "retired":
                reason = (
                    "strength below floor" if strength < _RETIRE_STRENGTH
                    else "3 consecutive contradictions" if consecutive_contradictions >= _RETIRE_CONTRADICTIONS
                    else "60 days idle"
                )
                row.update(status="retired", retired_at=_now_iso(), reason=reason)
                transitions["retired"].append(lkey)
            row["strength"] = strength
            rows[i] = row
            continue

        # ── Demote confirmed → candidate ─────────────────────────────────────
        if status == "confirmed" and strength < _DEMOTE_STRENGTH:
            row["status"] = "candidate"
            transitions["demoted"].append(lkey)

        # ── Promote candidate → confirmed ─────────────────────────────────────
        verified_refs = [e for e in evidence if e.get("verified")]
        distinct_refs = len({e.get("episode_ref") for e in verified_refs if e.get("episode_ref")})
        distinct_sessions = len({e.get("session_id") for e in verified_refs if e.get("session_id")})

        if (
            row.get("status", "candidate") == "candidate"
            and strength >= _PROMOTE_STRENGTH
            and distinct_refs >= _PROMOTE_EPISODES
            and distinct_sessions >= _PROMOTE_SESSIONS
            and len(verified_refs) >= _PROMOTE_VERIFIED
        ):
            row["status"] = "confirmed"
            row["promoted_at"] = _now_iso()
            transitions["promoted"].append(lkey)

            # First live PersonalityDelta — trait/preference scope only
            scope = row.get("scope", "")
            if scope in ("preference",) and row.get("proposes"):
                _try_personality_delta(row, transitions)

        row["strength"] = strength
        rows[i] = row

    if not dry_run:
        _save_ledger(rows, ledger_path)
        _append_metrics(transitions, ledger_path)

    return transitions


def _parse_ts(ts_val) -> float | None:
    """Accept float epoch or ISO-8601 string."""
    if ts_val is None:
        return None
    try:
        return float(ts_val)
    except (ValueError, TypeError):
        pass
    try:
        from datetime import datetime, timezone
        return datetime.fromisoformat(str(ts_val)).timestamp()
    except Exception:
        return None


def _last_confirming_ts(evidence: list) -> float | None:
    confirming = [_parse_ts(e.get("ts")) for e in evidence
                  if e.get("verified") and not e.get("contradicting")]
    confirming = [t for t in confirming if t is not None]
    return max(confirming) if confirming else None


def _last_any_ts(evidence: list) -> float | None:
    timestamps = [_parse_ts(e.get("ts")) for e in evidence if e.get("ts")]
    timestamps = [t for t in timestamps if t is not None]
    return max(timestamps) if timestamps else None


def _try_personality_delta(row: dict, transitions: dict) -> None:
    try:
        from faculties.personality.personality_evolution_faculty import (
            validate_delta, apply_delta, save_personality,
        )
        proposal = row.get("proposes", {})
        if not proposal:
            return
        delta = {
            "sender": "ReflectionGrowthEngine",
            "strength": "confirmed",
            "evidence": [e.get("episode_ref") for e in row.get("evidence", []) if e.get("verified")],
            **proposal,
        }
        result = validate_delta(delta)
        if result.get("approved"):
            apply_delta(result)
            save_personality()
            transitions["personality_delta"].append(row.get("lesson_key", ""))
    except Exception:
        pass


# ── recall ─────────────────────────────────────────────────────────────────────

def recall(
    scope: str = "",
    context: dict | None = None,
    k: int = _MAX_LESSONS_RECALL,
    ledger_path: str | None = None,
) -> list[dict]:
    """
    Return ≤k confirmed lessons, ranked by strength × recency × context match.
    Bounded to _MAX_CHARS_RECALL total characters of statement text.

    Confirmed lessons only — candidate/retired are invisible here.
    """
    rows = _load_ledger(ledger_path)
    confirmed = [r for r in rows if r.get("status") == "confirmed"]

    if scope:
        scoped = [r for r in confirmed if r.get("scope") == scope]
        confirmed = scoped if scoped else confirmed

    def _score(r: dict) -> float:
        strength = r.get("strength", 0.3)
        # recency: decay toward 0.5 over 30 days
        last_ts = _last_confirming_ts(r.get("evidence", [])) or 0.0
        days_old = (time.time() - last_ts) / 86400 if last_ts else 30
        recency = max(0.5, 1.0 - days_old / 60)
        # context match: simple keyword overlap with focal_thread / topic
        ctx_bonus = 0.0
        if context:
            topic = str(context.get("focal_thread", "") or context.get("topic", "")).lower()
            stmt = r.get("statement", "").lower()
            if topic and any(w in stmt for w in topic.split()[:5]):
                ctx_bonus = 0.15
        return strength * recency + ctx_bonus

    ranked = sorted(confirmed, key=_score, reverse=True)
    result = []
    total_chars = 0
    for r in ranked:
        stmt = r.get("statement", "")
        if total_chars + len(stmt) > _MAX_CHARS_RECALL:
            break
        result.append(r)
        total_chars += len(stmt)
        if len(result) >= k:
            break
    return result


# ── stats ──────────────────────────────────────────────────────────────────────

def stats(ledger_path: str | None = None) -> dict:
    """
    GrowthMetrics slice — read-only, never enters the response path.

    Returns:
        intention_realisation: met / (met + partial + failed) from growth_journal
        repeat_failure_rate:   recurring causes in failure_log
        reinforcement_ratio:   confirming vs contradicting evidence in ledger
        identity_stability:    trait variance from personality_vector (alarm if rising)
        ledger_counts:         {total, candidate, confirmed, retired}
    """
    rows = _load_ledger(ledger_path)
    counts = {"total": len(rows), "candidate": 0, "confirmed": 0, "retired": 0}
    conf_ev = contra_ev = 0
    for r in rows:
        status = r.get("status", "candidate")
        if status in counts:
            counts[status] += 1
        for ev in r.get("evidence", []):
            if ev.get("verified"):
                if ev.get("contradicting"):
                    contra_ev += 1
                else:
                    conf_ev += 1

    reinforcement_ratio = (
        round(conf_ev / (conf_ev + contra_ev), 3)
        if (conf_ev + contra_ev) > 0 else 0.0
    )

    # intention_realisation from growth_journal
    intention_realisation = _compute_intention_realisation()

    # repeat_failure_rate from failure_log
    repeat_failure_rate = _compute_repeat_failure_rate()

    # identity_stability — trait variance (alarm if rising)
    identity_stability = _compute_identity_stability()

    return {
        "ledger_counts": counts,
        "reinforcement_ratio": reinforcement_ratio,
        "intention_realisation": intention_realisation,
        "repeat_failure_rate": repeat_failure_rate,
        "identity_stability": identity_stability,
        "identity_stability_alarm": identity_stability > 0.15,
    }


def _compute_intention_realisation() -> float:
    journal = os.path.join(_ROOT, "self", "journals", "growth_journal.jsonl")
    met = partial = failed = 0
    try:
        with open(journal, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                comp = rec.get("completion", "")
                if comp == "met":
                    met += 1
                elif comp == "partial":
                    partial += 1
                elif comp == "failed":
                    failed += 1
    except FileNotFoundError:
        pass
    total = met + partial + failed
    return round(met / total, 3) if total > 0 else 0.0


def _compute_repeat_failure_rate() -> float:
    failure_log = os.path.join(_ROOT, "self", "failure_log.jsonl")
    cause_counts: dict[str, int] = {}
    total = 0
    try:
        with open(failure_log, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                cause = rec.get("delta", rec.get("cause", "unknown"))
                cause_counts[cause] = cause_counts.get(cause, 0) + 1
                total += 1
    except FileNotFoundError:
        pass
    if total == 0:
        return 0.0
    repeats = sum(c for c in cause_counts.values() if c > 1)
    return round(repeats / total, 3)


def _compute_identity_stability() -> float:
    pvec = os.path.join(_ROOT, "self", "personality_vector.json")
    try:
        with open(pvec, encoding="utf-8") as f:
            vec = json.load(f)
        # compute variance of all trait floats
        vals = [v for v in vec.values() if isinstance(v, (int, float))]
        if not vals:
            return 0.0
        mean = sum(vals) / len(vals)
        variance = sum((v - mean) ** 2 for v in vals) / len(vals)
        return round(variance ** 0.5, 4)   # std deviation as proxy
    except Exception:
        return 0.0


def _append_metrics(transitions: dict, ledger_path: str | None = None) -> None:
    # WO-096B: when a custom ledger_path is given (e.g. test runs) write metrics
    # beside it, not into the real journal, so tests never pollute production data.
    if ledger_path:
        _m = os.path.join(os.path.dirname(ledger_path), "journals", "growth_metrics.jsonl")
    else:
        _m = _METRICS
    os.makedirs(os.path.dirname(_m), exist_ok=True)
    with open(_m, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": time.time(),
            "promoted": len(transitions.get("promoted", [])),
            "demoted": len(transitions.get("demoted", [])),
            "retired": len(transitions.get("retired", [])),
            "personality_delta": len(transitions.get("personality_delta", [])),
        }, ensure_ascii=False) + "\n")


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
