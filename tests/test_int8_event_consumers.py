"""
tests/test_int8_event_consumers.py — INT-8 / FROM_DESIGN_2026-08-21

Two disconnection-falsifiable tests.

1. ack-poller does NOT truncate unity_events.json after reading.
   RED if server.py still opens the file with mode "w" inside _poll_unity_events.

2. file_drop_handler reads payload.path from NDJSON, not top-level path via json.load.
   RED if file_drop_handler still uses json.load or reads event.get("path") directly.
"""
import inspect
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


class TestInt8EventConsumers(unittest.TestCase):

    # ── 1: ack-poller must not truncate ──────────────────────────────────────

    def test_1_ack_poller_does_not_truncate(self):
        """_poll_unity_events must not open unity_events.json in write mode.

        Disconnection: revert Bug-2 fix → the open("w") line comes back → test RED.
        """
        server_path = ROOT / "server.py"
        self.assertTrue(server_path.exists(), f"server.py not found at {server_path}")
        source = server_path.read_text(encoding="utf-8")

        # Find the _poll_unity_events function body — everything between its def and the next
        # top-level def/class after the threading.Thread launch.
        start = source.find("def _poll_unity_events()")
        self.assertNotEqual(start, -1, "_poll_unity_events not found in server.py")

        # Grab 80 lines past the def — enough to cover the whole inner function
        func_region = source[start : start + 4000]

        # The truncation pattern: open(path, "w") inside this function
        truncation_patterns = [
            'open(_UNITY_EVENTS_PATH, "w"',
            "open(_UNITY_EVENTS_PATH, 'w'",
        ]
        for pattern in truncation_patterns:
            self.assertNotIn(
                pattern, func_region,
                f"Truncation pattern '{pattern}' found in _poll_unity_events — "
                "INT-8 Bug 2 is not fixed. The ack-poller must use a seq cursor, not truncation."
            )

        # The cursor must be present
        self.assertIn(
            "_ack_consumed_seq", func_region,
            "_ack_consumed_seq not found in _poll_unity_events — cursor is absent. "
            "INT-8 Bug 2 fix was not applied."
        )

    # ── 2: file_drop_handler reads NDJSON + payload.path ─────────────────────

    def test_2_file_drop_reads_ndjson_and_payload_path(self):
        """_poll_loop must read NDJSON line-by-line and pull path from payload.path.

        Disconnection: revert Bug-1 fix → json.load comes back → test RED.
        """
        import desktop.file_drop_handler as fdh

        source = inspect.getsource(fdh._poll_loop)

        # Must NOT use json.load (single-object parse)
        self.assertNotIn(
            "json.load(f)",
            source,
            "_poll_loop still calls json.load(f) — INT-8 Bug 1 not fixed. "
            "Must read NDJSON line-by-line with json.loads(line)."
        )

        # Must use json.loads (per-line)
        self.assertIn(
            "json.loads(line)",
            source,
            "_poll_loop does not call json.loads(line) — NDJSON reading not implemented."
        )

        # Must read path from payload
        self.assertIn(
            'payload',
            source,
            "_poll_loop does not reference 'payload' — path is not being read from payload.path."
        )

        # Must have seq cursor
        self.assertIn(
            "_last_seq",
            source,
            "_poll_loop does not reference _last_seq — seq cursor not implemented."
        )

        # _last_seq must be a module-level variable
        self.assertTrue(
            hasattr(fdh, "_last_seq"),
            "_last_seq not a module attribute in file_drop_handler — cursor not declared."
        )


if __name__ == "__main__":
    unittest.main()
