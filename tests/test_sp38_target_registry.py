"""
tests/test_sp38_target_registry.py — SP-38 acceptance tests.

WO-SP38: multi-target embodiment publisher dispatcher (target registry fan-out).
Simultaneity policy: one _ts-stamped state, all targets, fail-independent.
"""
import os
import sys
import threading
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import blender_bridge.state_writer as sw


def _reset_registry():
    """Restore registry to default state after each test."""
    with sw._TARGET_REGISTRY_LOCK:
        sw._TARGET_REGISTRY.clear()
        sw._TARGET_REGISTRY.append("desktop_primary")
    sw._TARGET_HANDLERS.clear()


class TestSP38TargetRegistry(unittest.TestCase):

    def setUp(self):
        _reset_registry()

    def tearDown(self):
        _reset_registry()

    # AT-1: default registry contains exactly desktop_primary
    def test_at1_default_registry_desktop_primary(self):
        with sw._TARGET_REGISTRY_LOCK:
            registry = list(sw._TARGET_REGISTRY)
        self.assertEqual(registry, ["desktop_primary"])

    # AT-2: register_target() adds a new target
    def test_at2_register_target_adds(self):
        sw.register_target("robot_orb")
        with sw._TARGET_REGISTRY_LOCK:
            registry = list(sw._TARGET_REGISTRY)
        self.assertIn("robot_orb", registry)
        self.assertIn("desktop_primary", registry)

    # AT-3: register_target() is idempotent — no duplicates
    def test_at3_register_target_idempotent(self):
        sw.register_target("robot_orb")
        sw.register_target("robot_orb")
        with sw._TARGET_REGISTRY_LOCK:
            count = sw._TARGET_REGISTRY.count("robot_orb")
        self.assertEqual(count, 1)

    # AT-4: unregister_target() removes a target
    def test_at4_unregister_target_removes(self):
        sw.register_target("robot_orb")
        sw.unregister_target("robot_orb")
        with sw._TARGET_REGISTRY_LOCK:
            registry = list(sw._TARGET_REGISTRY)
        self.assertNotIn("robot_orb", registry)

    # AT-5: unregister_target() is fail-quiet for absent target
    def test_at5_unregister_absent_no_exception(self):
        try:
            sw.unregister_target("nonexistent_surface")
        except Exception as exc:
            self.fail(f"unregister raised exception: {exc}")

    # AT-6: _dispatch_to_targets() calls handler for non-desktop target
    def test_at6_dispatch_calls_handler(self):
        called_with = []
        sw.register_target("robot_orb")
        sw._TARGET_HANDLERS["robot_orb"] = lambda state: called_with.append(state)

        payload = {"state": {"mode": "idle"}, "_ts": 1234.0}
        sw._dispatch_to_targets(payload)

        self.assertEqual(len(called_with), 1)
        self.assertEqual(called_with[0]["_ts"], 1234.0)

    # AT-7: _dispatch_to_targets() does NOT push to desktop_primary (file poll handles it)
    def test_at7_dispatch_skips_desktop_primary(self):
        called = []
        sw._TARGET_HANDLERS["desktop_primary"] = lambda s: called.append(s)

        sw._dispatch_to_targets({"state": {"mode": "idle"}})
        # desktop_primary is skipped even if a handler is registered
        self.assertEqual(len(called), 0)

    # AT-8: handler exception does not propagate (fail-independent)
    def test_at8_handler_exception_does_not_propagate(self):
        sw.register_target("bad_target")
        sw._TARGET_HANDLERS["bad_target"] = lambda s: 1 / 0  # always raises

        try:
            sw._dispatch_to_targets({"state": {"mode": "idle"}})
        except ZeroDivisionError:
            self.fail("handler exception propagated — should be fail-independent")

    # AT-9: multiple targets dispatched — all called, all independent
    def test_at9_multiple_targets_all_called(self):
        results: dict[str, list] = {"a": [], "b": []}
        sw.register_target("surface_a")
        sw.register_target("surface_b")
        sw._TARGET_HANDLERS["surface_a"] = lambda s: results["a"].append(s["_ts"])
        sw._TARGET_HANDLERS["surface_b"] = lambda s: results["b"].append(s["_ts"])

        payload = {"_ts": 9999.0, "state": {"mode": "curious"}}
        sw._dispatch_to_targets(payload)

        self.assertEqual(results["a"], [9999.0])
        self.assertEqual(results["b"], [9999.0])

    # AT-10: registry is thread-safe — concurrent register/unregister does not corrupt
    def test_at10_registry_thread_safe(self):
        errors = []

        def _add():
            try:
                for i in range(50):
                    sw.register_target(f"surface_{i}")
            except Exception as e:
                errors.append(e)

        def _remove():
            try:
                for i in range(50):
                    sw.unregister_target(f"surface_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=_add), threading.Thread(target=_remove)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
