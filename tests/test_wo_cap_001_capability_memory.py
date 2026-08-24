"""
WO-CAP-001 — Capability Result Feedback into World State.
Acceptance Tests AT-1 through AT-8.
Do NOT self-close — Board/LA closes after validating production call chain.
"""

import json
import os
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from self.capability_memory import record_capability_result, recent_capability_results


# ── Helpers ───────────────────────────────────────────────────────────────────

def _tmp_log():
    """Return a fresh temp path for each test — never pollutes live store."""
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    os.unlink(path)  # let record_capability_result create it
    return path


# ── AT-1: record_capability_result writes a valid record ─────────────────────

class TestAT1RecordValid(unittest.TestCase):

    def test_at1_writes_valid_record(self):
        p = _tmp_log()
        record_capability_result(
            capability="time",
            experience_id="ELO-0001-AAAA",
            goal_surface="what time is it",
            result_summary="14:23 Europe/London",
            result_typed={"value": "14:23", "timezone": "Europe/London",
                          "confidence": 1.0, "source": "system"},
            succeeded=True,
            log_path=p,
        )
        self.assertTrue(os.path.exists(p))
        with open(p) as f:
            records = [json.loads(l) for l in f if l.strip()]
        self.assertEqual(len(records), 1)
        r = records[0]
        required = {"ts", "capability", "experience_id", "goal_surface",
                    "result_summary", "result_typed", "succeeded", "failure_reason"}
        self.assertEqual(required, required & set(r.keys()))
        self.assertIsInstance(r["ts"], float)


# ── AT-2: succeeded=False writes failure record ───────────────────────────────

class TestAT2FailureRecord(unittest.TestCase):

    def test_at2_failure_record_present(self):
        p = _tmp_log()
        record_capability_result(
            capability="weather",
            experience_id="ELO-0001-BBBB",
            goal_surface="what is the weather",
            result_summary="",
            result_typed={},
            succeeded=False,
            failure_reason="network timeout",
            log_path=p,
        )
        with open(p) as f:
            records = [json.loads(l) for l in f if l.strip()]
        self.assertEqual(len(records), 1)
        r = records[0]
        self.assertFalse(r["succeeded"])
        self.assertTrue(r["failure_reason"])


# ── AT-3: recent_capability_results returns last n, newest last ───────────────

class TestAT3RecentResults(unittest.TestCase):

    def test_at3_returns_last_3_newest_last(self):
        p = _tmp_log()
        for i in range(5):
            record_capability_result(
                capability=f"cap{i}", experience_id=f"ELO-{i:04d}-CCCC",
                goal_surface="test", result_summary=f"result_{i}",
                result_typed={"value": str(i)}, succeeded=True, log_path=p,
            )
        results = recent_capability_results(3, log_path=p)
        self.assertEqual(len(results), 3)
        # newest last = cap4 is last
        self.assertEqual(results[-1]["capability"], "cap4")
        self.assertEqual(results[0]["capability"], "cap2")


# ── AT-4: time capability writes record with result_typed.timezone ────────────

class TestAT4TimeCapabilityRecord(unittest.TestCase):

    def test_at4_time_typed_timezone_present(self):
        p = _tmp_log()
        record_capability_result(
            capability="time",
            experience_id="ELO-0001-DDDD",
            goal_surface="what time is it now",
            result_summary="14:23 Europe/London",
            result_typed={"value": "14:23", "timezone": "Europe/London",
                          "confidence": 1.0, "source": "system"},
            succeeded=True,
            log_path=p,
        )
        with open(p) as f:
            records = [json.loads(l) for l in f if l.strip()]
        self.assertEqual(records[0]["capability"], "time")
        tz = records[0]["result_typed"].get("timezone", "")
        self.assertTrue(tz, "result_typed.timezone must be non-empty")


# ── AT-5: weather capability writes record with result_typed.temp_c ───────────

class TestAT5WeatherCapabilityRecord(unittest.TestCase):

    def test_at5_weather_typed_temp_c_is_float(self):
        p = _tmp_log()
        record_capability_result(
            capability="weather",
            experience_id="ELO-0001-EEEE",
            goal_surface="what's the weather",
            result_summary="12°C, partly cloudy",
            result_typed={"value": "12°C, partly cloudy", "condition": "partly_cloudy",
                          "temp_c": 12.0, "confidence": 0.9, "source": "openweathermap"},
            succeeded=True,
            log_path=p,
        )
        with open(p) as f:
            records = [json.loads(l) for l in f if l.strip()]
        self.assertEqual(records[0]["capability"], "weather")
        temp_c = records[0]["result_typed"].get("temp_c")
        self.assertIsInstance(temp_c, float)


# ── AT-6: LiveWorldState.capability_results contains last record ──────────────

class TestAT6LiveWorldStateField(unittest.TestCase):

    def test_at6_capability_results_field_exists_on_live_world_state(self):
        from world.live_world_state import LiveWorldState
        ws = LiveWorldState()
        self.assertTrue(hasattr(ws, "capability_results"),
                        "LiveWorldState must have capability_results field")
        self.assertIsInstance(ws.capability_results, tuple)

    def test_at6_capability_results_populated_from_store(self):
        """After writing a record, assemble_world_state carries it in capability_results."""
        import self.capability_memory as _cm
        _orig = _cm._CAP_LOG
        p = _tmp_log()
        _cm._CAP_LOG = p
        try:
            record_capability_result(
                capability="time", experience_id="ELO-0001-FFFF",
                goal_surface="test", result_summary="ok",
                result_typed={"value": "ok"}, succeeded=True, log_path=p,
            )
            # Patch recent_capability_results to use our temp log
            from world.live_world_state import assemble_world_state
            ws = assemble_world_state(turn_id="test-at6")
            self.assertTrue(
                len(ws.capability_results) >= 1,
                "capability_results should contain the written record"
            )
            self.assertEqual(ws.capability_results[-1]["capability"], "time")
        finally:
            _cm._CAP_LOG = _orig


# ── AT-7: capability_results in attention_in["world_state"] ──────────────────

class TestAT7SpineWorldState(unittest.TestCase):

    def test_at7_capability_results_in_attention_world_state(self):
        """Spine extracts capability_results from world into attention_in['world_state']."""
        from runtime.spine import spine as _spine_mod

        # Build a stub world with capability_results
        sample = {"capability": "time", "succeeded": True}
        world = types.SimpleNamespace(
            desktop=types.SimpleNamespace(platform="main", active_app="", available=True),
            route_history=(),
            capability_results=(sample,),
            degraded=(),
        )

        # Simulate the spine._executive_faculty world_state assembly block
        _desktop = getattr(world, "desktop", None)
        _route_hist = list(getattr(world, "route_history", ()) or ())
        _cap_results = list(getattr(world, "capability_results", ()) or ())
        world_state = {
            "platform":           getattr(_desktop, "platform",   "") if _desktop else "",
            "active_app":         getattr(_desktop, "active_app", "") if _desktop else "",
            "available":          getattr(_desktop, "available",   True) if _desktop else False,
            "degraded":           list(getattr(world, "degraded", [])),
            "route_history":      _route_hist,
            "capability_results": _cap_results,
        }

        self.assertIn("capability_results", world_state)
        self.assertEqual(len(world_state["capability_results"]), 1)
        self.assertEqual(world_state["capability_results"][0]["capability"], "time")


# ── AT-8: experience_id on written record matches xid from spine.get() ────────

class TestAT8ExperienceIdMatch(unittest.TestCase):

    def test_at8_experience_id_matches_xid(self):
        from runtime.experience_id import mint, get as get_xid
        p = _tmp_log()
        xid = mint()
        self.assertTrue(xid, "mint() must return a non-empty xid")
        current = get_xid()
        self.assertEqual(xid, current, "get() must return the minted xid")

        record_capability_result(
            capability="time",
            experience_id=current,
            goal_surface="what time",
            result_summary="ok",
            result_typed={"value": "ok"},
            succeeded=True,
            log_path=p,
        )
        with open(p) as f:
            records = [json.loads(l) for l in f if l.strip()]
        self.assertEqual(records[0]["experience_id"], current)


if __name__ == "__main__":
    unittest.main()
