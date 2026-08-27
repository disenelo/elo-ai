"""
tests/test_sp31_sp32_self_initiation.py — SP-31 + SP-32 acceptance tests.

WO-SP31-SP32: self-initiation gate (ATTENDING + HARD-QUIET + significance threshold).
"""
import os
import sys
import time
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import runtime.self_initiation as si


def _setup(
    presence: dict | None = None,
    presence_state: dict | None = None,
    env_si: str = "0",
    last_conversing: float = 0.0,
    last_interact:   float = 0.0,
    last_self_init:  float = 0.0,
    last_dismiss:    float = 0.0,
):
    """
    Reset module timestamps, patch file reads, and set env var.
    Returns an undo callable that restores the original _read_json and clears env.
    """
    si._last_conversing_ts = last_conversing
    si._last_interact_ts   = last_interact
    si._last_self_init_ts  = last_self_init
    si._last_dismiss_ts    = last_dismiss

    _p  = presence        if presence        is not None else {}
    _ps = presence_state  if presence_state  is not None else {}

    _orig_read = si._read_json

    def _patched_read(path: str) -> dict:
        if "presence_state" in path:
            return _ps
        if "presence.json" in path:
            return _p
        return {}

    si._read_json = _patched_read

    orig_env = os.environ.get("ELO_SELF_INITIATION")
    if env_si == "0":
        os.environ.pop("ELO_SELF_INITIATION", None)
    else:
        os.environ["ELO_SELF_INITIATION"] = env_si

    def _undo():
        si._read_json = _orig_read
        if orig_env is None:
            os.environ.pop("ELO_SELF_INITIATION", None)
        else:
            os.environ["ELO_SELF_INITIATION"] = orig_env

    return _undo


class TestSP31SP32SelfInitiation(unittest.TestCase):

    # AT-1: disabled by default — ELO_SELF_INITIATION not set → blocked
    def test_at1_disabled_by_default(self):
        undo = _setup(
            presence={"state": "active"},
            presence_state={"eloOnFront": True, "mode": "ACTIVE", "engagement": "ACTIVE"},
            env_si="0",
            last_conversing=time.time(),
        )
        try:
            result = si.may_self_initiate(0.95)
            self.assertFalse(result.allowed)
            self.assertEqual(result.tier, "blocked")
            self.assertIn("disabled", result.reason)
        finally:
            undo()

    # AT-2: HARD-QUIET Q1 — user away → blocked even when enabled and attending
    def test_at2_hard_quiet_user_away(self):
        undo = _setup(
            presence={"state": "away"},
            presence_state={"eloOnFront": True, "mode": "ACTIVE", "engagement": "ACTIVE"},
            env_si="1",
            last_conversing=time.time(),
        )
        try:
            result = si.may_self_initiate(0.90)
            self.assertFalse(result.allowed)
            self.assertEqual(result.tier, "blocked")
            self.assertEqual(result.reason, "hard_quiet")
        finally:
            undo()

    # AT-3: HARD-QUIET Q4a — cooldown active (60s elapsed, cooldown=180s) → blocked
    def test_at3_hard_quiet_cooldown(self):
        undo = _setup(
            presence={"state": "active"},
            presence_state={"eloOnFront": True, "mode": "ACTIVE", "engagement": "ACTIVE"},
            env_si="1",
            last_conversing=time.time(),
            last_self_init=time.time() - 60,  # 60s ago; cooldown=180s → still active
        )
        try:
            result = si.may_self_initiate(0.85)
            self.assertFalse(result.allowed)
            self.assertEqual(result.reason, "hard_quiet")
        finally:
            undo()

    # AT-4: HARD-QUIET Q4b — dismiss quiet window (100s elapsed, window=300s) → blocked
    def test_at4_hard_quiet_dismiss_window(self):
        undo = _setup(
            presence={"state": "active"},
            presence_state={"eloOnFront": True, "mode": "ACTIVE", "engagement": "ACTIVE"},
            env_si="1",
            last_conversing=time.time(),
            last_dismiss=time.time() - 100,  # 100s ago; window=300s → still active
        )
        try:
            result = si.may_self_initiate(0.95)
            self.assertFalse(result.allowed)
            self.assertEqual(result.reason, "hard_quiet")
        finally:
            undo()

    # AT-5: ATTENDING via A1 (conversing pulse ≤ 45s) + score ≥ 0.72 → verbal allowed
    def test_at5_attending_a1_verbal_allowed(self):
        undo = _setup(
            presence={"state": "active"},
            presence_state={"eloOnFront": False, "mode": "ACTIVE", "engagement": "ACTIVE"},
            env_si="1",
            last_conversing=time.time() - 10,  # 10s ago — within 45s
        )
        try:
            result = si.may_self_initiate(0.72)
            self.assertTrue(result.allowed)
            self.assertEqual(result.tier, "verbal")
            self.assertIn("attending", result.reason)
        finally:
            undo()

    # AT-6: ATTENDING via A2 (eloOnFront=True) + score ≥ 0.72 → verbal allowed
    def test_at6_attending_a2_elo_on_front(self):
        undo = _setup(
            presence={"state": "active"},
            presence_state={"eloOnFront": True, "mode": "ACTIVE", "engagement": "ACTIVE"},
            env_si="1",
            # No conversing pulse, no interaction — only A2 (eloOnFront)
        )
        try:
            result = si.may_self_initiate(0.80)
            self.assertTrue(result.allowed)
            self.assertEqual(result.tier, "verbal")
        finally:
            undo()

    # AT-7: NOT attending + exceptional score ≥ 0.90 → allowed (exceptional tier)
    def test_at7_exceptional_score_not_attending(self):
        undo = _setup(
            presence={"state": "active"},
            presence_state={"eloOnFront": False, "mode": "ACTIVE", "engagement": "ACTIVE"},
            env_si="1",
            # No signals — not attending
        )
        try:
            result = si.may_self_initiate(0.95)
            self.assertTrue(result.allowed)
            self.assertEqual(result.tier, "verbal")
            self.assertIn("exceptional", result.reason)
        finally:
            undo()

    # AT-8: score < 0.72 → ambient_only, no spine call
    def test_at8_below_threshold_ambient_only(self):
        undo = _setup(
            presence={"state": "active"},
            presence_state={"eloOnFront": True, "mode": "ACTIVE", "engagement": "ACTIVE"},
            env_si="1",
            last_conversing=time.time(),
        )
        try:
            result = si.may_self_initiate(0.50)
            self.assertFalse(result.allowed)
            self.assertEqual(result.tier, "ambient_only")
            self.assertIn("threshold", result.reason)
        finally:
            undo()

    # AT-9: not attending + score in [0.72, 0.90) → ambient_only (not exceptional enough)
    def test_at9_not_attending_midrange_ambient_only(self):
        undo = _setup(
            presence={"state": "active"},
            presence_state={"eloOnFront": False, "mode": "ACTIVE", "engagement": "ACTIVE"},
            env_si="1",
            # No signals → not attending
        )
        try:
            result = si.may_self_initiate(0.80)
            self.assertFalse(result.allowed)
            self.assertEqual(result.tier, "ambient_only")
            self.assertIn("not_attending", result.reason)
        finally:
            undo()

    # AT-10: record_conversation_pulse() advances _last_conversing_ts
    def test_at10_record_conversation_pulse(self):
        si._last_conversing_ts = 0.0
        before = time.time()
        si.record_conversation_pulse()
        self.assertGreaterEqual(si._last_conversing_ts, before)

    # AT-11: cooldown expired (200s > 180s cooldown) → allowed
    def test_at11_cooldown_expired_allowed(self):
        undo = _setup(
            presence={"state": "active"},
            presence_state={"eloOnFront": True, "mode": "ACTIVE", "engagement": "ACTIVE"},
            env_si="1",
            last_self_init=time.time() - 200,  # 200s ago; cooldown=180s → expired
        )
        try:
            result = si.may_self_initiate(0.80)
            self.assertTrue(result.allowed)
        finally:
            undo()

    # AT-12: is_enabled() False when env not set
    def test_at12_is_enabled_false(self):
        os.environ.pop("ELO_SELF_INITIATION", None)
        self.assertFalse(si.is_enabled())

    # AT-13: is_enabled() True when ELO_SELF_INITIATION=1
    def test_at13_is_enabled_true(self):
        os.environ["ELO_SELF_INITIATION"] = "1"
        result = si.is_enabled()
        os.environ.pop("ELO_SELF_INITIATION", None)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
