"""
tests/test_orch_no_false_close.py — WO-ORCH-FALSECLOSE / card 0061

Five invariants that must hold in _run_claude_worker + run_seat:

1. Worker exits non-zero  → status BLOCKED, card NOT in DONE/
2. Worker exits 0 but prints "Credit balance is too low" → status BLOCKED, card NOT in DONE/
3. Worker exits 0, no card move, no commit → status BLOCKED, card NOT in DONE/
4. Worker exits 0, card moved to DONE/, new commit → status DONE
5. HEARTBEAT.json never carries DONE and NOT MET simultaneously
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from unittest.mock import MagicMock, patch

# Ensure the project root is on sys.path so we can import the orchestrator
ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "engineering"))

import importlib, types

# Import the module under test
import seat_orchestrator as orch


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_temp_seat(tmp: pathlib.Path, seat: str = "test_seat") -> pathlib.Path:
    """Create a minimal seat directory structure under tmp."""
    seat_dir = tmp / "agent_bus" / seat
    for sub in ("QUEUE", "DOING", "DONE", "BLOCKED"):
        (seat_dir / sub).mkdir(parents=True, exist_ok=True)
    (seat_dir / "LOCK.json").write_text(json.dumps({
        "owner": None, "pid": None, "work_id": None, "state": "RELEASED"
    }))
    return seat_dir


def _make_card(seat_dir: pathlib.Path, folder: str, name: str = "test_card.md") -> pathlib.Path:
    card = seat_dir / folder / name
    card.write_text("# test card\n\n## Result\n- commit:\n")
    return card


class _FakeProc:
    """Minimal subprocess.Popen stub."""
    def __init__(self, stdout_lines=None, stderr_text="", returncode=0):
        self._lines = iter(stdout_lines or [])
        self.stdout = self
        self.stderr = MagicMock()
        self.stderr.read.return_value = stderr_text
        self.stdin = MagicMock()
        self.returncode = returncode
        self.pid = 99999

    def readline(self):
        try:
            return next(self._lines) + "\n"
        except StopIteration:
            return ""

    def read(self):
        return ""

    def poll(self):
        return self.returncode  # immediately done

    def wait(self):
        return self.returncode

    def terminate(self):
        pass


# ── tests ─────────────────────────────────────────────────────────────────────

class TestOrchestratorNoFalseClose(unittest.TestCase):

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        # Patch BUS to point at our temp directory
        self._orig_bus = orch.BUS
        orch.BUS = self.tmp / "agent_bus"

    def tearDown(self):
        orch.BUS = self._orig_bus
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _call_run_claude_worker(self, card, seat, seat_dir, lc, result_file,
                                 proc_stdout=None, proc_stderr="", proc_rc=0,
                                 head_before="abc123", head_after="abc123"):
        """Invoke _run_claude_worker with a stubbed subprocess."""
        fake_proc = _FakeProc(proc_stdout, proc_stderr, proc_rc)

        # _git_head is called twice: once for head_before, once for head_after.
        # Use side_effect to return different values on successive calls.
        git_head_calls = [head_before, head_after]

        with patch("subprocess.Popen", return_value=fake_proc), \
             patch.object(orch, "_git_head", side_effect=git_head_calls), \
             patch.object(orch, "_git_stat", return_value=""), \
             patch("shutil.which", return_value="/usr/bin/claude"), \
             patch("time.sleep"):
            lc.log = []
            lc.record("STARTED", "stubbed")
            lc.record("ALIVE", "stubbed")
            return orch._run_claude_worker(card, seat, seat_dir, lc, result_file)

    # ── test 1: non-zero exit → BLOCKED ──────────────────────────────────────

    def test_1_nonzero_exit_gives_blocked(self):
        seat_dir = _make_temp_seat(self.tmp)
        card = _make_card(seat_dir, "DOING")
        result_file = seat_dir / "worker_result.json"
        lc = orch.Lifecycle("test_seat", card.name)

        result = self._call_run_claude_worker(
            card, "test_seat", seat_dir, lc, result_file,
            proc_rc=1, proc_stderr="some error"
        )

        self.assertEqual(result["status"], "BLOCKED", result)
        self.assertFalse((seat_dir / "DONE" / card.name).exists(),
                         "card must NOT be in DONE/ after non-zero exit")

    # ── test 2: credit error on exit 0 → BLOCKED ─────────────────────────────

    def test_2_credit_balance_error_gives_blocked(self):
        seat_dir = _make_temp_seat(self.tmp)
        card = _make_card(seat_dir, "DOING")
        result_file = seat_dir / "worker_result.json"
        lc = orch.Lifecycle("test_seat", card.name)

        result = self._call_run_claude_worker(
            card, "test_seat", seat_dir, lc, result_file,
            proc_stdout=["Credit balance is too low to run this model."],
            proc_rc=0
        )

        self.assertEqual(result["status"], "BLOCKED", result)
        self.assertFalse((seat_dir / "DONE" / card.name).exists(),
                         "card must NOT be in DONE/ after credit error")

    # ── test 3: exit 0, no card move, no commit → BLOCKED ────────────────────

    def test_3_exit0_no_move_no_commit_gives_blocked(self):
        seat_dir = _make_temp_seat(self.tmp)
        card = _make_card(seat_dir, "DOING")
        result_file = seat_dir / "worker_result.json"
        lc = orch.Lifecycle("test_seat", card.name)

        result = self._call_run_claude_worker(
            card, "test_seat", seat_dir, lc, result_file,
            proc_rc=0,
            head_before="abc123", head_after="abc123"  # no new commit
        )

        self.assertEqual(result["status"], "BLOCKED", result)
        self.assertFalse((seat_dir / "DONE" / card.name).exists(),
                         "card must NOT be in DONE/ without commit evidence")

    # ── test 4: exit 0, card in DONE/, new commit → DONE ─────────────────────

    def test_4_exit0_done_card_new_commit_gives_done(self):
        seat_dir = _make_temp_seat(self.tmp)
        card = _make_card(seat_dir, "DOING")
        result_file = seat_dir / "worker_result.json"
        lc = orch.Lifecycle("test_seat", card.name)

        # Simulate worker moving the card to DONE/
        done_card = seat_dir / "DONE" / card.name
        done_card.write_text("# test card\n\n## Result\n- commit: def456\n")

        result = self._call_run_claude_worker(
            card, "test_seat", seat_dir, lc, result_file,
            proc_rc=0,
            head_before="abc123", head_after="def456 HEAD main"
        )

        self.assertEqual(result["status"], "DONE", result)
        self.assertTrue(result.get("acceptance_met"), result)

    # ── test 5: HEARTBEAT never has DONE + NOT MET simultaneously ─────────────

    def test_5_heartbeat_no_simultaneous_done_and_not_met(self):
        """
        When a worker exits 0 with no stdout and no new commit (the false-close scenario),
        _run_claude_worker must return BLOCKED — so that run_seat never writes
        DONE+elapsed=0.0s to the lifecycle while acceptance_met=False.

        This is the scenario that produced the MT-observed contradiction:
          "heartbeat reads DONE / 004 / NOT MET elapsed=0.0s, worker still Credit balance is too low"
        """
        seat_dir = _make_temp_seat(self.tmp)
        card = _make_card(seat_dir, "DOING")
        result_file = seat_dir / "worker_result.json"
        lc = orch.Lifecycle("test_seat", card.name)

        # Worker exits 0, no stdout, no new commit — the false-close scenario
        result = self._call_run_claude_worker(
            card, "test_seat", seat_dir, lc, result_file,
            proc_stdout=None, proc_rc=0,
            head_before="abc123", head_after="abc123"  # HEAD unchanged
        )

        # Orchestrator must return BLOCKED, not DONE
        self.assertEqual(result["status"], "BLOCKED",
                         f"Expected BLOCKED for exit-0/no-commit, got: {result}")

        # Verify the lifecycle does NOT contain DONE+MET alongside RESULT+acceptance=False
        done_entries   = [e for e in lc.log if e["state"] == "DONE"]
        result_entries = [e for e in lc.log if e["state"] == "RESULT"]
        for de in done_entries:
            for re in result_entries:
                if "elapsed=0.0s" in de.get("detail", ""):
                    self.fail(f"Lifecycle has DONE elapsed=0.0s — indicates crash-close: {de}")
                if " MET" in de.get("detail", "") and "acceptance=False" in re.get("detail", ""):
                    self.fail(
                        f"Lifecycle contradiction: DONE=MET but RESULT=acceptance=False: "
                        f"done={de}, result={re}"
                    )


if __name__ == "__main__":
    unittest.main()
