"""
company_runtime/approval_faculty.py — EA2-5: the L3 approval gate as a clean faculty.

Formalizes the approval logic that previously lived scattered inside
company_state_writer.process_action / handle_company_approve into one cohesive,
testable DECISION layer.

ADDITIVE ONLY — this module never edits the dispatch board, the frozen kernel, or
server.py. It DECIDES whether an approval is allowed and RECORDS the decision to an
append-only ledger. The writer (company_state_writer._flip_wo_status) still performs
the actual board flip; keeping the two concerns separate makes each independently
testable.

David's rule (2026-08-01), enforced here:
  • only an L3 actor may approve                          → L3 gate
  • money / legal / safety (RESERVED) needs a human       → reserved/safety gate
  • AUTO / CONFIRM / DAVID follow their importance tiers  → tier gate

Classification is delegated to company_runtime.wo_policy.classify — ONE source of
truth. This faculty does not duplicate the importance logic.

Public surface
──────────────
  ApprovalFaculty(ledger_path=...).request(wo_id, actor, human_flag=False, title="", status="")
      → {ok, reason, decision}
  request(...)  — module-level convenience wrapping a default-ledger faculty.

Ledger: append-only JSONL at blender/approval_ledger.jsonl — one JSON object per
decision: {ts, wo, actor, importance, decision, reason}.
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import time

from company_runtime import wo_policy

_logger = logging.getLogger(__name__)

# L3 actors who may approve — money / legal / safety are their non-negotiable call.
L3_ACTORS: frozenset[str] = frozenset({"david", "disenelo", "founder"})

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_LEDGER = os.path.join(_ROOT, "blender", "approval_ledger.jsonl")

# Decision vocabulary
_ALLOWED = "allowed"
_REFUSED = "refused"


def _is_l3(actor: str) -> bool:
    return (actor or "").strip().lower() in L3_ACTORS


class ApprovalFaculty:
    """
    A cohesive decision + record layer for company approvals.

    Construct with a ledger_path (defaults to blender/approval_ledger.jsonl). Tests
    should point this at a temp path so the real ledger is never touched.
    """

    def __init__(self, ledger_path: str = _DEFAULT_LEDGER):
        self.ledger_path = ledger_path

    # ── Decision ──────────────────────────────────────────────────────────────

    def decide(
        self,
        wo_id: str,
        actor: str,
        human_flag: bool = False,
        title: str = "",
        status: str = "",
    ) -> dict:
        """
        Pure decision — no side effects, no ledger write.

        Returns {ok, reason, decision, importance, needs_david}.
        Never raises; malformed input yields a graceful refusal.
        """
        wo = (wo_id or "").strip()
        act = (actor or "").strip()

        # Malformed input → graceful refusal (no crash).
        if not wo or not act:
            return {
                "ok": False,
                "reason": "malformed: missing work_order or actor",
                "decision": _REFUSED,
                "importance": None,
                "needs_david": None,
            }

        # Classify via the single source of truth.
        try:
            pol = wo_policy.classify(wo, title, status)
        except Exception as exc:  # defensive — classification must never crash the gate
            _logger.error("approval_faculty: classify failed for %s: %s", wo, exc)
            return {
                "ok": False,
                "reason": f"internal error classifying {wo}: {exc}",
                "decision": _REFUSED,
                "importance": None,
                "needs_david": None,
            }

        importance = pol.get("importance", "AUTO")
        needs_david = pol.get("needs_david", False)

        # L3 gate — only L3 actors may approve, full stop.
        if not _is_l3(act):
            return {
                "ok": False,
                "reason": f"actor '{act}' is not L3 — refused",
                "decision": _REFUSED,
                "importance": importance,
                "needs_david": needs_david,
            }

        # Reserved / safety gate — money / legal / safety needs an explicit human.
        if importance == "RESERVED" and not human_flag:
            return {
                "ok": False,
                "reason": f"{wo} is RESERVED (money/legal/safety) — human_flag required, refused",
                "decision": _REFUSED,
                "importance": importance,
                "needs_david": needs_david,
            }

        # AUTO / CONFIRM / DAVID (and RESERVED with human_flag) — allowed for an L3 actor.
        return {
            "ok": True,
            "reason": f"{wo} approved by L3 actor '{act}' ({importance})",
            "decision": _ALLOWED,
            "importance": importance,
            "needs_david": needs_david,
        }

    # ── Decision + record ─────────────────────────────────────────────────────

    def request(
        self,
        wo_id: str,
        actor: str,
        human_flag: bool = False,
        title: str = "",
        status: str = "",
    ) -> dict:
        """
        Decide whether an approval is allowed AND record it to the append-only ledger.

        Returns {ok, reason, decision}. Every call — allowed or refused — writes one
        ledger line (unless the input is so malformed there is no WO/actor to log,
        which is still recorded with best-effort empties). Never raises.
        """
        result = self.decide(wo_id, actor, human_flag=human_flag, title=title, status=status)
        self._record(
            wo=(wo_id or "").strip(),
            actor=(actor or "").strip(),
            importance=result.get("importance"),
            decision=result.get("decision", _REFUSED),
            reason=result.get("reason", ""),
        )
        # Public contract is {ok, reason, decision}; keep it clean.
        return {
            "ok": result["ok"],
            "reason": result["reason"],
            "decision": result["decision"],
        }

    # ── Append-only ledger ────────────────────────────────────────────────────

    def _record(self, wo: str, actor: str, importance, decision: str, reason: str) -> bool:
        """
        Append one decision to the JSONL ledger. Atomic-ish append (open 'a' + flush +
        fsync). Best-effort — a ledger failure never blocks a decision.
        """
        entry = {
            "ts": datetime.datetime.utcnow().isoformat() + "Z",
            "_ts": round(time.time(), 3),
            "wo": wo,
            "actor": actor,
            "importance": importance,
            "decision": decision,
            "reason": reason,
        }
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.ledger_path)), exist_ok=True)
            line = json.dumps(entry, ensure_ascii=False)
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                f.flush()
                os.fsync(f.fileno())
            return True
        except Exception as exc:
            _logger.error("approval_faculty: ledger append failed: %s", exc)
            return False

    def read_ledger(self) -> list[dict]:
        """Parse the whole ledger into a list of decision dicts. Empty if none yet."""
        out: list[dict] = []
        if not os.path.exists(self.ledger_path):
            return out
        try:
            with open(self.ledger_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        out.append(json.loads(line))
        except Exception as exc:
            _logger.error("approval_faculty: ledger read failed: %s", exc)
        return out


# ── Module-level convenience (default ledger) ─────────────────────────────────

_default_faculty = ApprovalFaculty()


def request(
    wo_id: str,
    actor: str,
    human_flag: bool = False,
    title: str = "",
    status: str = "",
    ledger_path: str | None = None,
) -> dict:
    """
    Convenience wrapper — decide + record against the default (or supplied) ledger.

    Returns {ok, reason, decision}.
    """
    fac = _default_faculty if ledger_path is None else ApprovalFaculty(ledger_path)
    return fac.request(wo_id, actor, human_flag=human_flag, title=title, status=status)


# ── CLI smoke ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    import tempfile

    tmp = os.path.join(tempfile.gettempdir(), "approval_ledger_smoke.jsonl")
    if os.path.exists(tmp):
        os.remove(tmp)
    fac = ApprovalFaculty(tmp)
    for wo, actor, hf, title in [
        ("WO-123", "david", False, "some engineering fix"),
        ("WO-123", "intern", False, "some engineering fix"),
        ("BO-2", "david", False, "funding model"),
        ("BO-2", "david", True, "funding model"),
        ("WO-999", "david", False, "cleanup dead code"),
        ("", "", False, ""),
    ]:
        r = fac.request(wo, actor, human_flag=hf, title=title)
        print(f"{wo or '(none)':10} {actor or '(none)':8} human={hf!s:5} → {r['decision']:8} {r['reason']}")
    print(f"\nledger lines: {len(fac.read_ledger())} → {tmp}")
