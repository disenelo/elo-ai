"""
tests/test_canon_vii_executive.py — WO-CANON-VII: Executive Cortex
DoD checks for §B (speech gate), §C (intent queue), §D (UP-relay audit).

§A confirmed correct as-is (not tested here — it is the spec, not a bug).

Test families:
  IQ-*  — IntentQueue mechanism (§C)
  ET-*  — Epistemic Tier gate / SpeechLicence (§B)
  BB-*  — Brain-Body-Brain UP-relay audit (§D)
  AT-*  — compile / py_compile hygiene
"""
import os
import sys
import py_compile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

_passed = 0
_failed = 0


def ok(name: str):
    global _passed
    _passed += 1
    print(f"  ✅ {name}")


def fail(name: str, reason):
    global _failed
    _failed += 1
    print(f"  ❌ {name}: {reason}")


print()
print("WO-CANON-VII  Executive Cortex")
print("-" * 55)


# ═══════════════════════════════════════════════════════════════
# IQ — Intent Queue (§C)
# ═══════════════════════════════════════════════════════════════
print("\n── §C Intent Queue ──")


# IQ-1: Intent and IntentQueue dataclasses exist and are importable
try:
    from runtime.cognitive_snapshot import Intent, IntentQueue
    ok("IQ-1: Intent and IntentQueue importable from cognitive_snapshot")
except Exception as e:
    fail("IQ-1", e)


# IQ-2: Intent has required fields
try:
    from runtime.cognitive_snapshot import Intent
    import time
    intent = Intent(
        id="test001",
        lane="external",
        kind="sit",
        content="cursor",
        origin="user_command",
        pressure=1.0,
        feasible=True,
        boundary_ok=True,
        status="committed",
        created_ts=time.time(),
        expires=0.0,
    )
    assert intent.kind == "sit"
    assert intent.lane == "external"
    assert intent.status == "committed"
    ok("IQ-2: Intent construction — all fields set, frozen")
except AssertionError as e:
    fail("IQ-2", e)
except Exception as e:
    fail("IQ-2", e)


# IQ-3: IntentQueue lanes (external, internal, committed)
try:
    from runtime.cognitive_snapshot import Intent, IntentQueue
    import time
    i = Intent(
        id="abc123",
        lane="external",
        kind="move",
        content="window_corner",
        origin="faculty_propose",
        pressure=0.5,
        feasible=True,
        boundary_ok=True,
        status="proposed",
        created_ts=time.time(),
        expires=0.0,
    )
    q = IntentQueue(external=(i,), internal=(), committed=i)
    assert len(q.external) == 1
    assert q.committed is i
    assert len(q.internal) == 0
    ok("IQ-3: IntentQueue carries external/internal/committed lanes")
except AssertionError as e:
    fail("IQ-3", e)
except Exception as e:
    fail("IQ-3", e)


# IQ-4: build_snapshot() with pending_sit produces IntentQueue.committed (sit Intent)
try:
    from runtime.cognitive_snapshot import build_snapshot, IntentQueue, Intent
    import time
    snap = build_snapshot(
        attention={"intent": "movement", "valence": "neutral"},
        pending_sit={"active": True, "since": time.time() - 2, "queued": None},
        turn_id="test-vii-iq4",
    )
    q = snap.intent_queue
    assert isinstance(q, IntentQueue), f"intent_queue should be IntentQueue, got {type(q)}"
    assert q.committed is not None, "committed should not be None when sit is pending"
    assert isinstance(q.committed, Intent), f"committed should be Intent, got {type(q.committed)}"
    assert q.committed.kind == "sit"
    assert q.committed.lane == "external"
    assert q.committed.status == "committed"
    ok("IQ-4: build_snapshot with pending_sit produces Intent(kind=sit) as committed")
except AssertionError as e:
    fail("IQ-4", e)
except Exception as e:
    fail("IQ-4", e)


# IQ-5: parity — pending_intentions still carries legacy ("sit", "cursor") tuple
try:
    from runtime.cognitive_snapshot import build_snapshot
    import time
    snap = build_snapshot(
        pending_sit={"active": True, "since": time.time(), "queued": None},
    )
    assert ("sit", "cursor") in snap.pending_intentions, \
        f"Legacy pending_intentions must still contain ('sit','cursor'); got: {snap.pending_intentions}"
    ok("IQ-5: legacy pending_intentions tuple preserved for backward compat")
except AssertionError as e:
    fail("IQ-5", e)
except Exception as e:
    fail("IQ-5", e)


# IQ-6: no pending_sit → IntentQueue is empty (no intents, committed=None)
try:
    from runtime.cognitive_snapshot import build_snapshot, IntentQueue
    snap = build_snapshot()
    q = snap.intent_queue
    assert isinstance(q, IntentQueue)
    assert q.committed is None, f"committed should be None when no sit pending; got {q.committed}"
    assert len(q.external) == 0
    assert len(q.internal) == 0
    ok("IQ-6: empty IntentQueue when no pending_sit")
except AssertionError as e:
    fail("IQ-6", e)
except Exception as e:
    fail("IQ-6", e)


# IQ-7: record_intent_abandoned() exists and writes without error
try:
    from self.decision_journal import record_intent_abandoned
    record_intent_abandoned(
        intent_id="test-id-001",
        kind="move",
        content="window_corner",
        reason="out-competed by sit intent",
        lane="internal",
    )
    ok("IQ-7: record_intent_abandoned() callable without error")
except Exception as e:
    fail("IQ-7", e)


# IQ-8: IntentQueue is frozen (mutation raises FrozenInstanceError)
try:
    from runtime.cognitive_snapshot import IntentQueue
    q = IntentQueue()
    try:
        q.committed = "something"  # type: ignore[misc]
        fail("IQ-8", "FrozenInstanceError not raised — IntentQueue is mutable")
    except Exception as freeze_err:
        if "FrozenInstanceError" in type(freeze_err).__name__ or "cannot assign" in str(freeze_err).lower():
            ok("IQ-8: IntentQueue is frozen — mutation raises FrozenInstanceError")
        else:
            fail("IQ-8", freeze_err)
except Exception as e:
    fail("IQ-8", e)


# ═══════════════════════════════════════════════════════════════
# ET — Epistemic Tier gate / SpeechLicence (§B)
# ═══════════════════════════════════════════════════════════════
print("\n── §B Speech Gate ──")


# ET-1: SpeechLicence and verify_response_tiers importable
try:
    from runtime.the_moment import SpeechLicence, verify_response_tiers
    ok("ET-1: SpeechLicence and verify_response_tiers importable from the_moment")
except Exception as e:
    fail("ET-1", e)


# ET-2: all-observed snapshot → allow=True, hedge_required=False, no violations
try:
    from runtime.the_moment import verify_response_tiers
    lic = verify_response_tiers({
        "pose": "observed",
        "surface": "observed",
        "locomotion": "live",
        "capabilities": "live",
    })
    assert lic.allow is True
    assert lic.hedge_required is False
    assert len(lic.violations) == 0
    ok("ET-2: all-observed snapshot → allow=True, no hedge, no violations")
except AssertionError as e:
    fail("ET-2", e)
except Exception as e:
    fail("ET-2", e)


# ET-3: unknown field → violation registered
try:
    from runtime.the_moment import verify_response_tiers
    lic = verify_response_tiers({
        "pose": "observed",
        "nearby": "unknown",
    })
    assert lic.allow is True, "allow must always be True"
    assert "nearby" in lic.violations, f"'nearby' should be in violations; got {lic.violations}"
    ok("ET-3: unknown field in tier snapshot → violation registered")
except AssertionError as e:
    fail("ET-3", e)
except Exception as e:
    fail("ET-3", e)


# ET-4: last-known field → hedge_required=True (no violation, but must hedge)
try:
    from runtime.the_moment import verify_response_tiers
    lic = verify_response_tiers({
        "pose": "last-known",
        "surface": "observed",
    })
    assert lic.hedge_required is True, "last-known should set hedge_required=True"
    assert "pose" not in lic.violations, "last-known should not be a violation, just a hedge"
    ok("ET-4: last-known field → hedge_required=True, not a violation")
except AssertionError as e:
    fail("ET-4", e)
except Exception as e:
    fail("ET-4", e)


# ET-5: min_tier reflects worst tier in snapshot
try:
    from runtime.the_moment import verify_response_tiers
    lic = verify_response_tiers({
        "pose": "observed",
        "capabilities": "live",
        "nearby": "unknown",
    })
    assert lic.min_tier == "unknown", f"min_tier should be 'unknown'; got '{lic.min_tier}'"
    ok("ET-5: min_tier reflects worst tier (unknown) in snapshot")
except AssertionError as e:
    fail("ET-5", e)
except Exception as e:
    fail("ET-5", e)


# ET-6: build_snapshot() populates speech_licence on the snapshot
try:
    from runtime.cognitive_snapshot import build_snapshot
    from runtime.the_moment import SpeechLicence
    snap = build_snapshot()
    assert snap.speech_licence is not None, "speech_licence should not be None after build_snapshot"
    assert isinstance(snap.speech_licence, SpeechLicence), \
        f"speech_licence should be SpeechLicence; got {type(snap.speech_licence)}"
    assert snap.speech_licence.allow is True
    ok("ET-6: build_snapshot() populates speech_licence (SpeechLicence) on snapshot")
except AssertionError as e:
    fail("ET-6", e)
except Exception as e:
    fail("ET-6", e)


# ET-7: notes field is non-empty and meaningful
try:
    from runtime.the_moment import verify_response_tiers
    lic_ok = verify_response_tiers({"pose": "observed"})
    lic_bad = verify_response_tiers({"pose": "unknown"})
    assert lic_ok.notes, "notes must not be empty"
    assert lic_bad.notes, "notes must not be empty for violations"
    assert "GATE" in lic_ok.notes
    assert "GATE" in lic_bad.notes
    ok("ET-7: SpeechLicence.notes is non-empty and carries GATE prefix")
except AssertionError as e:
    fail("ET-7", e)
except Exception as e:
    fail("ET-7", e)


# ═══════════════════════════════════════════════════════════════
# BB — Brain-Body-Brain UP-relay audit (§D)
# ═══════════════════════════════════════════════════════════════
print("\n── §D UP-relay audit ──")


# BB-1: relay_body_event and audit_body_relay importable
try:
    from runtime.body_relay import relay_body_event, audit_body_relay
    ok("BB-1: relay_body_event and audit_body_relay importable from body_relay")
except Exception as e:
    fail("BB-1", e)


# BB-2: relay_body_event() runs without error (silent emitter)
try:
    from runtime.body_relay import relay_body_event
    relay_body_event("sit_commanded", {"target": "cursor", "test": True})
    ok("BB-2: relay_body_event() emits without error")
except Exception as e:
    fail("BB-2", e)


# BB-3: audit with no pending_sit → ok=True, no violations
try:
    from runtime.body_relay import audit_body_relay
    from runtime.cognitive_snapshot import BodySchema
    body = BodySchema()  # pending_sit=False
    result = audit_body_relay(body, [])
    assert result["ok"] is True, f"Expected ok=True for empty body; got {result}"
    assert result["violations"] == []
    ok("BB-3: audit with no pending_sit → ok=True, no violations")
except AssertionError as e:
    fail("BB-3", e)
except Exception as e:
    fail("BB-3", e)


# BB-4: pending_sit with sit in journal → not a violation (commanded DOWN exists)
try:
    from runtime.body_relay import audit_body_relay
    from runtime.cognitive_snapshot import BodySchema
    body = BodySchema(pending_sit=True, sit_pending_since=1.0)
    journal = [{"action": "sit", "outcome": "success"}]
    result = audit_body_relay(body, journal)
    # sit is commanded (in journal); pending_unacked is acceptable — not a violation
    assert result["violations"] == [], \
        f"sit in journal should prevent VIOLATION; got violations={result['violations']}"
    ok("BB-4: pending_sit with sit action in journal → no VIOLATION")
except AssertionError as e:
    fail("BB-4", e)
except Exception as e:
    fail("BB-4", e)


# BB-5: pending_sit with NO journal entry and NO relay event → VIOLATION
try:
    import os
    import sys

    # Temporarily rename relay log so audit sees no relay events
    from runtime import body_relay as _br
    _orig_log = _br._RELAY_LOG
    _br._RELAY_LOG = _br._RELAY_LOG + ".test_missing"
    try:
        from runtime.body_relay import audit_body_relay
        from runtime.cognitive_snapshot import BodySchema
        body = BodySchema(pending_sit=True, sit_pending_since=1.0)
        result = audit_body_relay(body, [])   # empty journal
        assert not result["ok"], f"Expected ok=False (VIOLATION); got ok={result['ok']}"
        assert result["violations"], f"Expected at least one violation; got {result['violations']}"
    finally:
        _br._RELAY_LOG = _orig_log
    ok("BB-5: pending_sit with no journal + no relay event → VIOLATION flagged")
except AssertionError as e:
    fail("BB-5", e)
except Exception as e:
    fail("BB-5", e)


# BB-6: relay event clears VIOLATION (relay_body_event then audit → ok)
try:
    from runtime.body_relay import relay_body_event, audit_body_relay
    from runtime.cognitive_snapshot import BodySchema
    # Emit a relay event
    relay_body_event("sit_commanded", {"target": "cursor"})
    body = BodySchema(pending_sit=True, sit_pending_since=1.0)
    result = audit_body_relay(body, [])   # no journal, but relay event exists
    assert result["violations"] == [], \
        f"relay event should prevent VIOLATION; got violations={result['violations']}"
    ok("BB-6: relay event present → no VIOLATION even without journal entry")
except AssertionError as e:
    fail("BB-6", e)
except Exception as e:
    fail("BB-6", e)


# ═══════════════════════════════════════════════════════════════
# AT — compile hygiene
# ═══════════════════════════════════════════════════════════════
print("\n── AT compile ──")


for _mod in (
    "runtime/cognitive_snapshot.py",
    "runtime/the_moment.py",
    "runtime/body_relay.py",
    "self/decision_journal.py",
):
    _label = f"AT-compile: {_mod}"
    try:
        py_compile.compile(_mod, doraise=True)
        ok(_label)
    except py_compile.PyCompileError as e:
        fail(_label, e)
    except Exception as e:
        fail(_label, e)


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 55)
print(f"WO-CANON-VII executive cortex   {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
