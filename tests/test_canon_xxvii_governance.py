"""
tests/test_canon_xxvii_governance.py — WO-CANON-XXVII §B

Seven disconnection-falsifiable tests.

GT-1  G1_links returns zero broken for the governed index; planted broken link → exactly one.
GT-2  G2_drift flags a volume whose 00_Metadata.md disagrees with 00_CANON_INDEX.md (fixture).
GT-3  G3_wo_shape fails a post-cutoff WO missing required sections; passes a complete one;
      reports pre-cutoff backlog as a number without failing.
GT-4  G4_done_ownership flags a board line DONE ✅ with no COMPLETION_LOG.md entry (fixture).
GT-5  check_secrets.py rejects a diff with an API-key literal; accepts a clean diff.
GT-6  No verbatim paragraph ≥ 25 words in the governed index is copied from engineering/standards/.
GT-7  DECISION_LOG.md IDs are unique and append-only (no existing ID's text was modified per git diff).
"""
import pathlib
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from governance_check import G1_links, G2_drift, G3_wo_shape, G4_done_ownership
from check_secrets import check_diff, check_tracked_files


class TestCanonXXVIIGovernance(unittest.TestCase):

    # ── GT-1: G1 link integrity ───────────────────────────────────────────────

    def test_1_g1_links_governed_index(self):
        """G1_links returns zero broken links for the real governed index.
        A fixture with a deliberately broken link returns exactly one broken entry.

        Disconnection: remove 04_Governed_Index.md → G1_links returns error (not zero).
        """
        # Clean check on real governed index
        governed_index = ROOT / "docs" / "architecture" / "Volume_XXVII" / "04_Governed_Index.md"
        self.assertTrue(governed_index.exists(), f"Governed index not found: {governed_index}")

        broken = G1_links(governed_index)
        self.assertEqual(
            broken, [],
            f"G1_links found broken links in the governed index: {broken}. "
            "Fix the governed index to point at files that exist."
        )

        # Fixture with a broken link
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Fixture\n\n[Bad link](../nonexistent/file_that_does_not_exist.md)\n")
            fixture_path = pathlib.Path(f.name)

        try:
            broken_fixture = G1_links(fixture_path)
            self.assertEqual(
                len(broken_fixture), 1,
                f"Expected exactly 1 broken link in fixture, got {len(broken_fixture)}: {broken_fixture}"
            )
            self.assertIn(
                "nonexistent/file_that_does_not_exist.md",
                broken_fixture[0]["link"],
                "Broken link not found in the reported finding."
            )
        finally:
            fixture_path.unlink(missing_ok=True)

    # ── GT-2: G2 drift detection ──────────────────────────────────────────────

    def test_2_g2_drift_detects_planted_mismatch(self):
        """G2_drift flags a volume whose 00_Metadata.md implementation disagrees with canon index.

        Uses a fixture pair: one metadata file says COMPLETE while the fixture index says PENDING.

        Disconnection: change the comparison logic to always return [] → test RED.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = pathlib.Path(tmp)

            # Fixture canon index saying Volume_TEST is PENDING
            index_dir = tmp_root / "docs" / "architecture"
            index_dir.mkdir(parents=True)
            (index_dir / "00_CANON_INDEX.md").write_text(
                "# Canon Index\n\nVolume TEST — 📝 PENDING some note\n",
                encoding="utf-8",
            )

            # Fixture metadata saying COMPLETE
            vol_dir = index_dir / "Volume_TEST"
            vol_dir.mkdir()
            (vol_dir / "00_Metadata.md").write_text(
                "volume: TEST\nimplementation: COMPLETE\n",
                encoding="utf-8",
            )

            drift = G2_drift(
                volumes_dir=index_dir,
                canon_index=index_dir / "00_CANON_INDEX.md",
            )

        self.assertTrue(
            len(drift) >= 1,
            f"G2_drift found no disagreements in the fixture. "
            f"Expected 'Volume_TEST' (metadata=COMPLETE vs index=PENDING) to be flagged. Got: {drift}"
        )
        vol_names = [d.get("volume", "") for d in drift]
        self.assertIn(
            "Volume_TEST", vol_names,
            f"G2_drift did not flag 'Volume_TEST'. Findings: {drift}"
        )

    # ── GT-3: G3 WO shape lint ────────────────────────────────────────────────

    def test_3_g3_wo_shape_lint(self):
        """G3_wo_shape fails a post-cutoff WO missing required sections;
        passes a complete post-cutoff WO; pre-cutoff WO contributes to backlog count only.

        Disconnection: remove any required section check → complete WO still passes (but incomplete WO
        no longer fails) → test RED on the incomplete-WO assertion.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)

            # Post-cutoff WO WITHOUT required sections
            (tmp_dir / "WO-TEST-INCOMPLETE.md").write_text(
                "# WO-TEST-INCOMPLETE\n\n**Status:** OPEN — raised 2026-08-15\n\nSome description.\n",
                encoding="utf-8",
            )

            # Post-cutoff WO WITH all required sections
            (tmp_dir / "WO-TEST-COMPLETE.md").write_text(
                textwrap.dedent("""\
                    # WO-TEST-COMPLETE
                    **Status:** OPEN — raised 2026-08-15

                    ## Files to TOUCH
                    - `some/file.py`

                    ## Files MUST-NOT-TOUCH
                    - `runtime/executive.py`

                    ## Definition of Done
                    - Tests pass, committed.
                """),
                encoding="utf-8",
            )

            # Pre-cutoff WO (no sections, old date — should NOT fail)
            (tmp_dir / "WO-OLD.md").write_text(
                "# WO-OLD\n\n**Status:** OPEN — raised 2026-07-01\n\nOld WO.\n",
                encoding="utf-8",
            )

            result = G3_wo_shape(wo_dir=tmp_dir, cutoff="2026-08-13")

        # Incomplete post-cutoff WO must be a failure
        failure_names = [f["file"] for f in result["post_cutoff_failures"]]
        self.assertIn(
            "WO-TEST-INCOMPLETE.md", failure_names,
            f"G3 did not flag the post-cutoff WO missing required sections. Failures: {failure_names}"
        )

        # Complete post-cutoff WO must NOT be a failure
        self.assertNotIn(
            "WO-TEST-COMPLETE.md", failure_names,
            f"G3 flagged the complete WO — it should not. Failures: {failure_names}"
        )

        # Pre-cutoff WO must contribute to backlog, not failures
        self.assertNotIn(
            "WO-OLD.md", failure_names,
            f"G3 flagged the pre-cutoff WO — it must only go to backlog."
        )
        self.assertGreaterEqual(
            result["pre_cutoff_backlog"], 1,
            f"Pre-cutoff backlog count should be >= 1 (WO-OLD.md). Got {result['pre_cutoff_backlog']}."
        )

    # ── GT-4: G4 DONE ownership ───────────────────────────────────────────────

    def test_4_g4_done_ownership(self):
        """G4_done_ownership flags a board DONE ✅ line with no COMPLETION_LOG.md entry.

        Fixture: a board line with WO-XXXX DONE ✅, and a log with no [WO-XXXX] entry.

        Disconnection: remove the ownership check → unowned WO silently passes → test RED.

        Also verifies real data: G-4 is documented as expected to fail on the current board.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)

            board = tmp_dir / "DISPATCH_BOARD.md"
            log   = tmp_dir / "COMPLETION_LOG.md"

            board.write_text(
                "| WO-XXXX | Some task | DONE ✅ |\n",
                encoding="utf-8",
            )
            log.write_text(
                "# Completion Log\n\n### [WO-OTHER] — Some other task\n",
                encoding="utf-8",
            )

            unowned = G4_done_ownership(board_path=board, log_path=log)

        self.assertTrue(
            len(unowned) >= 1,
            f"G4 returned no unowned DONE entries in fixture — expected WO-XXXX to be flagged. Got: {unowned}"
        )
        self.assertTrue(
            any(u.get("id") == "WO-XXXX" for u in unowned),
            f"WO-XXXX not in unowned list: {unowned}"
        )

        # Verify that G4 is expected to fire on the real board (not testing its count — testing the check works)
        real_unowned = G4_done_ownership()
        self.assertIsInstance(real_unowned, list,
                              "G4_done_ownership on real data returned non-list")
        # Documented expectation: G-4 flags real board lines (not asserting count — count is Architect's fix)
        # Just assert the check ran without error
        if real_unowned and "error" not in real_unowned[0]:
            print(f"\n  [GT-4] Real board: {len(real_unowned)} DONE ✅ line(s) without COMPLETION_LOG.md entry "
                  "(expected — Architect corrects these)")

    # ── GT-5: check_secrets.py ────────────────────────────────────────────────

    def test_5_check_secrets_rejects_api_key_accepts_clean(self):
        """check_secrets.check_diff rejects a diff containing an API-key literal.
        check_secrets.check_tracked_files rejects a tracked .env file.

        Disconnection: remove any pattern from _SECRET_PATTERNS → the planted key passes → test RED.
        """
        # OpenAI-shaped key on an added diff line
        dirty_diff = "+OPENAI_API_KEY=sk-" + "A" * 50 + "\n"
        findings = check_diff(dirty_diff)
        self.assertTrue(
            findings,
            f"check_diff did not detect the planted API key in diff. "
            "The pattern may be missing from _SECRET_PATTERNS."
        )

        # Clean diff with no secrets
        clean_diff = "+# this is a comment\n+some_var = 42\n"
        findings_clean = check_diff(clean_diff)
        self.assertEqual(
            findings_clean, [],
            f"check_diff flagged a clean diff: {findings_clean}. Review _SECRET_PATTERNS for false positives."
        )

        # Tracked .env file
        blocked = check_tracked_files([".env"])
        self.assertTrue(
            blocked,
            "check_tracked_files did not flag '.env' as a blocked file."
        )
        self.assertNotIn(".env", check_tracked_files(["main.py", "README.md"]),
                         "check_tracked_files incorrectly blocked a safe file.")

    # ── GT-6: no duplication in governed index ─────────────────────────────────

    def test_6_governed_index_no_verbatim_duplication(self):
        """The governed index must not contain a verbatim paragraph ≥ 25 words
        copied from engineering/standards/*.

        Disconnection: paste a paragraph from coding.md into the index → test RED.
        """
        governed_index = ROOT / "docs" / "architecture" / "Volume_XXVII" / "04_Governed_Index.md"
        if not governed_index.exists():
            self.skipTest("Governed index not yet created — create it first (WO-CANON-XXVII §A)")

        index_text = governed_index.read_text(encoding="utf-8")
        standards_dir = ROOT / "engineering" / "standards"

        if not standards_dir.exists():
            self.skipTest(f"engineering/standards/ not found at {standards_dir}")

        for std_file in sorted(standards_dir.glob("*.md")):
            std_text = std_file.read_text(encoding="utf-8", errors="replace")
            # Build 25-word sliding windows from standards text
            words = std_text.split()
            for i in range(len(words) - 25):
                phrase = " ".join(words[i : i + 25]).lower().strip()
                # Skip very short or boilerplate fragments
                if len(phrase) < 100:
                    continue
                if phrase in index_text.lower():
                    self.fail(
                        f"Verbatim 25-word phrase from {std_file.name} found in governed index. "
                        "The index must cite, not copy, standards content.\n"
                        f"Phrase: '{phrase[:80]}…'"
                    )

    # ── GT-7: DECISION_LOG.md IDs are unique and append-only ─────────────────

    def test_7_decision_log_ids_unique_append_only(self):
        """DECISION_LOG.md IDs must be unique (no duplicate D-X or ADR-NNN IDs).

        Disconnect: introduce a duplicate ID → test RED.
        The git-diff append-only check is also run but skipped if not in a git repo.
        """
        log_path = ROOT / "docs" / "architecture" / "DECISION_LOG.md"
        if not log_path.exists():
            self.skipTest(f"DECISION_LOG.md not found at {log_path}")

        text = log_path.read_text(encoding="utf-8")

        # IDs appear in cross-references in heading text — only extract the PRIMARY id:
        # the id immediately following the ## markers (the defining entry, not mentions).
        primary_id_pattern = re.compile(
            r'^#+\s+(D-[A-Z]+(?:\d+)?|ADR-\d+|FC-\d+|LAW-\d+)'
        )
        heading_ids: list[str] = []
        for line in text.splitlines():
            m = primary_id_pattern.match(line.strip())
            if m:
                heading_ids.append(m.group(1))

        seen: dict[str, int] = {}
        duplicates: list[str] = []
        for ident in heading_ids:
            if ident in seen:
                if ident not in duplicates:
                    duplicates.append(ident)
            seen[ident] = seen.get(ident, 0) + 1

        self.assertEqual(
            duplicates, [],
            f"Duplicate decision entry headings found in DECISION_LOG.md: {duplicates}. "
            "Each decision ID may have only one defining heading — cross-references are fine, "
            "but two ## headings with the same ID are a governance violation."
        )

        # git-diff append-only check (best-effort — skipped outside a git repo)
        try:
            diff = subprocess.check_output(
                ["git", "diff", "HEAD", "--", str(log_path.relative_to(ROOT))],
                cwd=ROOT, text=True, stderr=subprocess.DEVNULL
            )
            removed_ids = [
                line[1:] for line in diff.splitlines()
                if line.startswith("-") and not line.startswith("---")
                and id_pattern.search(line)
            ]
            self.assertEqual(
                removed_ids, [],
                f"Unstaged diff shows lines removed from DECISION_LOG.md that contain IDs: {removed_ids[:5]}. "
                "Decision IDs are immutable — they may never be deleted or replaced."
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass  # not in a git repo or git not available


if __name__ == "__main__":
    unittest.main()
