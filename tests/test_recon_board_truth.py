"""
tests/test_recon_board_truth.py — WO-RECON / card 0064

Four disconnection-falsifiable tests for the board reconciler.

1. A WO with commit + test + .cs reference is NEVER reported not-started.
2. A WO with no evidence anywhere is NEVER reported DONE.
3. INT7 identifiers resolve via .cs source specifically.
   Remove the .cs sweep → this test goes RED.
4. A row marked BLOCKED with no reason string is reported BLOCKED-UNEXPLAINED.
"""
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from tools.board_reconciler import classify, _KNOWN_BLOCKED, CS_DIR


class TestBoardReconcilerTruth(unittest.TestCase):

    # ── 1: evidence → never not-started ──────────────────────────────────────

    def test_1_all_evidence_sources_never_reports_not_started(self):
        """A WO with commit + test file + .cs file must NOT be reported not-started.

        Disconnection: remove any of the three evidence sources from classify() →
        if the resulting status is 'not-started', the test fails.
        """
        ident = "INT7-CORE"

        # Stub all three evidence sources to return non-empty results
        with patch("tools.board_reconciler._git_commits_for", return_value=["abc1234"]), \
             patch("tools.board_reconciler._test_files_for", return_value=[pathlib.Path("tests/test_int7.py")]), \
             patch("tools.board_reconciler._done_cards_for", return_value=[]), \
             patch("tools.board_reconciler._cs_files_for", return_value=[pathlib.Path("EloBrainCluster.cs")]):

            result = classify(ident)

        self.assertNotEqual(
            result["status"], "not-started",
            f"{ident} has commit + test + .cs but reconciler reports 'not-started'. "
            "Check the evidence aggregation in classify()."
        )
        self.assertIn(
            result["status"], ("DONE-proven", "DONE-evidenced", "partial"),
            f"Expected a positive status, got '{result['status']}'"
        )

    # ── 2: no evidence → never DONE ──────────────────────────────────────────

    def test_2_no_evidence_never_reports_done(self):
        """A WO with absolutely no evidence must not be reported as DONE (any form).

        Disconnection: if classify() defaults to DONE on empty evidence, this goes RED.
        """
        ident = "WO-PRIN-1"  # listed as not-started in register, no known evidence

        with patch("tools.board_reconciler._git_commits_for", return_value=[]), \
             patch("tools.board_reconciler._test_files_for", return_value=[]), \
             patch("tools.board_reconciler._done_cards_for", return_value=[]), \
             patch("tools.board_reconciler._cs_files_for", return_value=[]):

            result = classify(ident)

        self.assertNotIn(
            "DONE", result["status"],
            f"{ident} has zero evidence but reconciler reports '{result['status']}'. "
            "The reconciler is fabricating DONE status."
        )

    # ── 3: INT7 IDs resolve via .cs specifically ──────────────────────────────

    def test_3_int7_resolves_via_cs_source(self):
        """INT7 identifiers are verified by .cs files in the Unity project.
        With the .cs sweep disabled, these IDs must NOT reach DONE-proven.

        Disconnection: remove CS_DIR search from _cs_files_for() → this goes RED.
        """
        # First: with .cs sweep live, INT7-CORE must have CS evidence
        if CS_DIR.exists():
            from tools.board_reconciler import _cs_files_for
            cs_hits = _cs_files_for("INT7-CORE")
            self.assertTrue(
                cs_hits,
                f"INT7-CORE not found in any .cs file under {CS_DIR}. "
                "Either the file moved or the .cs sweep is broken."
            )

        # Second: without .cs sweep, INT7-CORE cannot reach DONE-proven
        with patch("tools.board_reconciler._git_commits_for", return_value=["abc1234"]), \
             patch("tools.board_reconciler._test_files_for", return_value=[]), \
             patch("tools.board_reconciler._done_cards_for", return_value=[]), \
             patch("tools.board_reconciler._cs_files_for", return_value=[]):  # cs sweep disabled

            result_no_cs = classify("INT7-CORE")

        self.assertNotEqual(
            result_no_cs["status"], "DONE-proven",
            "INT7-CORE reaches DONE-proven even without .cs sweep — "
            "the .cs sweep is not the deciding factor. Review classify() source count logic."
        )

    # ── 4: BLOCKED with no reason → BLOCKED-UNEXPLAINED ─────────────────────

    def test_4_blocked_with_no_reason_is_unexplained(self):
        """WO-116 and WO-117 are marked BLOCKED in the register.
        Neither has a reason string in any DONE card.
        The reconciler must report them as BLOCKED-UNEXPLAINED, not BLOCKED.

        Disconnection: if classify() always returns BLOCKED (not UNEXPLAINED) for
        these IDs, the distinction is lost and David's audit question goes unanswered.
        """
        for ident in ("WO-116", "WO-117"):
            with patch("tools.board_reconciler._git_commits_for", return_value=[]), \
                 patch("tools.board_reconciler._test_files_for", return_value=[]), \
                 patch("tools.board_reconciler._done_cards_for", return_value=[]), \
                 patch("tools.board_reconciler._cs_files_for", return_value=[]):

                result = classify(ident)

            self.assertEqual(
                result["status"], "BLOCKED-UNEXPLAINED",
                f"{ident} is marked BLOCKED in the register but has no reason recorded. "
                f"reconciler reports '{result['status']}' — must be 'BLOCKED-UNEXPLAINED'. "
                "David asked: 'How do we get this done or unblocked if blocked for no real reason?'"
            )


if __name__ == "__main__":
    unittest.main()
