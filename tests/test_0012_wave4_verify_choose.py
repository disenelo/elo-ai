"""
tests/test_0012_wave4_verify_choose.py — Wave 4: rows 13 VERIFY and 15 CHOOSE.

## Row 13 VERIFY (WO-111)
Executor silently fails ⇒ eLo says it didn't work.
anim_trigger.fire() returns ANIM_UNCONFIRMED — not True on file write.
Every capability with ack_required=True must declare an ack_executor.

## Row 15 CHOOSE (WO-112)
Decision confidence is populated in every journal entry.
alternatives_rejected: open design question — decide() does not form a candidate set.
  The field exists but is always [] because no candidate scoring happens.
  Raising as design question: adding candidate set to decide() requires Architect ruling
  (FREEZE_V1_LOCK covers decision logic; candidate formation = logic change, not additive input).

Tests:
    VR-1  anim_trigger.fire() returns ANIM_UNCONFIRMED (never True)
    VR-2  No capability has ack_required=True without an ack_executor (sentinel check)
    CH-1  decide() result has confidence key (not null)
    CH-2  decision_journal.jsonl latest entry has non-null confidence
    CH-3  alternatives_rejected field exists on journal entry (even if empty — design Q open)

Run: python3 tests/test_0012_wave4_verify_choose.py
"""
import json
import os
import sys
import tempfile
import unittest.mock as mock

sys.path.insert(0, ".")

import logging
logging.basicConfig(level=logging.CRITICAL)

PASS = 0; FAIL = 0

def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── VR-1: anim_trigger.fire() returns ANIM_UNCONFIRMED, never True ────────────

print("\nVR-1: anim_trigger.fire() returns ANIM_UNCONFIRMED (not True on file write)")
try:
    import blender_bridge.anim_trigger as _at
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir="/tmp") as _tf:
        _tmp = _tf.name
        json.dump({"motion": {"animation": "idle"}}, _tf)
    _orig = _at._STATE_PATH
    try:
        _at._STATE_PATH = _tmp
        result = _at.fire("wave")
        if result is True or result == True:
            fail("VR-1", "anim_trigger.fire() returned True — it lied about completion (WO-111 not applied)")
        elif result == _at.ANIM_UNCONFIRMED:
            ok(f"VR-1 — fire() returns ANIM_UNCONFIRMED={result!r} (no false success claim)")
        elif result is False:
            fail("VR-1", "fire() returned False — file write failed (check path)")
        else:
            ok(f"VR-1 — fire() returns non-True sentinel: {result!r}")
    finally:
        _at._STATE_PATH = _orig
        try: os.unlink(_tmp)
        except: pass
except Exception as e:
    fail("VR-1", repr(e))


# ── VR-2: ack_required=True capabilities must declare ack_executor ────────────

print("\nVR-2: capabilities with ack_required=True must have ack_executor declared")
try:
    from runtime.capabilities.registry import ALL_CAPABILITIES
    _violations = []
    for cap in ALL_CAPABILITIES:
        _ack_req  = getattr(cap, "ack_required",  False)
        _ack_exec = getattr(cap, "ack_executor",  "")
        if _ack_req and not _ack_exec:
            _violations.append(cap.id)
    if _violations:
        fail("VR-2", f"capabilities with ack_required=True but no ack_executor: {_violations}")
    else:
        _total_ack = sum(1 for c in ALL_CAPABILITIES if getattr(c, "ack_required", False))
        ok(f"VR-2 — no ack_required violations (currently {_total_ack} cap(s) have ack_required=True)")
except Exception as e:
    fail("VR-2", repr(e))


# ── CH-1: decide() result has non-null confidence ─────────────────────────────

print("\nCH-1: decide() result has confidence key (not null)")
try:
    from runtime.executive import decide
    r = decide({"intent": "creation", "valence": "positive", "momentum": "building"},
               loop_detected=False, user_input="let's build something")
    conf = r.get("confidence")
    if conf is None:
        fail("CH-1", "confidence is None in decide() result")
    elif isinstance(conf, (int, float)):
        ok(f"CH-1 — decide() returns confidence={conf!r}")
    else:
        fail("CH-1", f"unexpected confidence type: {type(conf).__name__} = {conf!r}")
except Exception as e:
    fail("CH-1", repr(e))


# ── CH-2: latest journal entry has non-null confidence ───────────────────────

print("\nCH-2: latest decision_journal.jsonl entry has non-null confidence")
_JOURNAL = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "self", "journals", "decision_journal.jsonl",
)
try:
    if not os.path.exists(_JOURNAL):
        fail("CH-2", "decision_journal.jsonl does not exist")
    else:
        _last = None
        with open(_JOURNAL) as _f:
            for _line in _f:
                _stripped = _line.strip()
                if _stripped:
                    try: _last = json.loads(_stripped)
                    except: pass
        if _last is None:
            fail("CH-2", "decision_journal.jsonl is empty or unparseable")
        elif _last.get("confidence") is None:
            fail("CH-2", f"latest entry has confidence=null; entry={list(_last.keys())}")
        else:
            ok(f"CH-2 — latest journal entry confidence={_last['confidence']!r}")
except Exception as e:
    fail("CH-2", repr(e))


# ── CH-3: alternatives_rejected field exists (design question: candidate set) ─

print("\nCH-3: alternatives_rejected field exists in journal (content open — design Q)")
print("      Note: field is always [] because decide() uses early-return, not candidate scoring.")
print("      Candidate set requires Architect ruling (FREEZE_V1_LOCK / logic change).")
try:
    if not os.path.exists(_JOURNAL):
        fail("CH-3", "decision_journal.jsonl does not exist")
    else:
        _has_field = False
        with open(_JOURNAL) as _f:
            for _line in _f:
                _stripped = _line.strip()
                if _stripped:
                    try:
                        _entry = json.loads(_stripped)
                        if "alternatives_rejected" in _entry:
                            _has_field = True
                            break
                    except: pass
        if _has_field:
            ok("CH-3 — alternatives_rejected field present in journal (always [] — design Q open)")
        else:
            fail("CH-3", "alternatives_rejected missing from journal entries entirely")
except Exception as e:
    fail("CH-3", repr(e))


# ── results ───────────────────────────────────────────────────────────────────

print(f"\n{'='*40}")
print(f"Wave 4 Verify+Choose: {PASS} passed, {FAIL} failed")
print()
print("Rows:")
print("  13 VERIFY — anim_trigger returns ANIM_UNCONFIRMED (not True); ack_required contract checked")
print("  15 CHOOSE — confidence populated; alternatives_rejected field present")
print()
print("OPEN DESIGN QUESTION (Row 15):")
print("  alternatives_rejected is always [] because decide() early-returns without candidate scoring.")
print("  Candidate set = decision logic change = FREEZE_V1_LOCK. Needs Architect ruling.")
if FAIL:
    sys.exit(1)
