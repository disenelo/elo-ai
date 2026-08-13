#!/usr/bin/env python3
"""
wo_policy.py — ONE source of truth for a Work Order's IMPORTANCE and whether it
needs David's approval. Used by wo_test_runner (auto-close logic) AND by
company_state_writer (dashboard badges), so the board, the runner, and the
Presence dashboard all agree.

David's rule (2026-08-01):
  • a quick fix (a number change, a threshold, config, cleanup) → DON'T need me
  • something I asked for specifically → MY call
  • money / legal / safety → always MY call (L3)

Importance levels
─────────────────
  AUTO      🟢  trivial / mechanical, or green-tested engineering with no human
                judgement → closes itself, no approval.
  CONFIRM   🔵  live eLo behaviour you like to feel (voice / routing / memory /
                movement) → green tests = one-click confirm.
  DAVID     🟠  YOU asked for it by name (a feature/look you requested) → your call,
                even when small, because it's your vision.
  RESERVED  🔴  money / legal / safety → your L3, always, non-negotiable.
"""
from __future__ import annotations
import re

BADGE = {"AUTO": "🟢", "CONFIRM": "🔵", "DAVID": "🟠", "RESERVED": "🔴"}
LABEL = {
    "AUTO":     "auto — no approval needed",
    "CONFIRM":  "confirm — your one-click",
    "DAVID":    "your call — you asked for this",
    "RESERVED": "L3 gate — money / legal / safety",
}

# money / legal / safety — always David
_RESERVED_PREFIX = ("BO", "LG", "RD-CAD")
_RESERVED_WORDS  = ("money", "funding", "cost model", "legal", "compliance", "t&c",
                    "privacy", "safety", "force limit", "soft-stop", "soft stop",
                    "hazard", "liability", "kickstarter goal")

# live behaviours David feels before closing
_CONFIRM_WOS = {"WO-016", "WO-017", "WO-019", "WO-020", "WO-022"}

# David-REPORTED live behaviour bugs — a green SCAFFOLD test does NOT prove the behaviour
# is fixed (e.g. WO-035 has a passing scaffold but the say/do eval still FAILS). These must
# NEVER auto-close on a green test; David feels them fixed. Checked before TRIVIAL so a stray
# keyword can't downgrade them. (Guard added 2026-08-03 after an auto-close false-closed
# WO-035/036/037 while they were live + dispatched.)
_DAVID_WOS = {"WO-030", "WO-035", "WO-036", "WO-037", "WO-038", "WO-039",
              "WO-040", "WO-041", "WO-042", "WO-043", "WO-044", "WO-045"}

# "David specifically asked for this" signals in the board row
_DAVID_ASK = ("david asked", "david-directed", "david directed", "you asked",
              "david green-light", "david green light", "(david", "david 2026",
              "david re-review", "signed off direct")

# trivial / mechanical → safe to auto (a number, a value, a cleanup)
_TRIVIAL = ("number change", "threshold", "value change", "cap ", "default ",
            "raise default", "param", "config", "typo", "rename", "cleanup",
            "dead code", "delete dead", "one-line", "one line", "bump ", "tweak")

# design / visual / brand → David's eye (he requests these + approves the look/voice)
_VISUAL = ("INT7",)                    # One Brain visualiser look — David approves the look
_DAVID_PREFIX = ("MK", "CR", "SD", "FH")  # marketing / creative / social / fashion — his brand + content call


def classify(wo: str, title: str = "", status: str = "") -> dict:
    """Return {importance, needs_david, reason, badge, label} for a WO."""
    w = (wo or "").upper().strip()
    blob = f"{title} {status}".lower()

    # 1) reserved gates — money / legal / safety — override everything
    # Use word-boundary matching so "reliability" doesn't hit "liability",
    # "safety dims" (significance engine) doesn't hit "safety", etc.
    def _reserved_hit(b: str) -> bool:
        for k in _RESERVED_WORDS:
            pat = r"\b" + re.escape(k) + r"\b"
            if re.search(pat, b):
                return True
        return False
    if any(w.startswith(p) for p in _RESERVED_PREFIX) or _reserved_hit(blob):
        return _mk("RESERVED", True, "money / legal / safety — always your L3")

    # 1.5) David-reported live behaviour bugs — never auto-close on a green scaffold test.
    #      Checked before TRIVIAL so a stray keyword can't downgrade them to AUTO.
    if w in _DAVID_WOS:
        return _mk("DAVID", True, "David-reported live behaviour — you feel it fixed, not a scaffold test")

    # 2) trivial / mechanical → no approval (a number change, a cleanup) — beats "you asked",
    #    because you said quick fixes shouldn't need you even if you mentioned them.
    if any(k in blob for k in _TRIVIAL):
        return _mk("AUTO", False, "trivial/mechanical fix — no approval needed")

    # 3) things David asked for by name (features + the visualiser look + brand/creative)
    if (any(k in blob for k in _DAVID_ASK)
            or any(w.startswith(p) for p in _VISUAL)
            or any(w.startswith(p) for p in _DAVID_PREFIX)):
        return _mk("DAVID", True, "you requested this specifically — your call")

    # 4) live eLo behaviours you like to feel
    if w in _CONFIRM_WOS:
        return _mk("CONFIRM", True, "live behaviour — green tests, your one-click")

    # 5) default: engineering WO — auto if it's test-gated, else light
    return _mk("AUTO", False, "engineering — auto-close on green tests")


def _mk(imp: str, needs: bool, reason: str) -> dict:
    return {"importance": imp, "needs_david": needs, "reason": reason,
            "badge": BADGE[imp], "label": LABEL[imp]}


if __name__ == "__main__":
    for wo, t, s in [
        ("WO-019", "voice drops out", "DONE (Builder)"),
        ("BO-2", "funding model", "money → David L3"),
        ("INT7-WEB", "spider links", "David asked"),
        ("WO-023", "screen position", "READY (David 2026-08-01)"),
        ("INT7-RING-CLEANUP", "delete dead ring code", "cleanup-only"),
        ("EA2-4", "Scheduling Faculty", "QUEUED"),
    ]:
        c = classify(wo, t, s)
        print(f"{c['badge']} {wo:20} {c['importance']:8} needs_david={c['needs_david']}  {c['reason']}")
