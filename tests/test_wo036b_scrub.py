"""
tests/test_wo036b_scrub.py  WO-036b / card 0062

Three disconnection-falsifiable structural tests.
None of these require a live LLM — they test the instructions and detection mechanism.

1. living_presence_spec.txt contains "You mentioned" in the anti-mirroring rule.
   RED if the phrase is absent (the gap is unfilled).
2. The harness catches restatement stems mid-response, not only as openers.
   RED if detection is narrowed back to startswith() only.
3. prompt_builder.py REFLECT directive still requires specific noticing.
   RED if the anti-mute language is removed (would let eLo go silent on genuine noticing).
"""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from tools.chatlog_replay import _evaluate_turn

SPEC_PATH = ROOT / "prompts" / "living_presence_spec.txt"
PB_PATH   = ROOT / "runtime" / "prompt_builder.py"


class TestWO036bScrub(unittest.TestCase):

    # ── 1: spec contains "You mentioned" ─────────────────────────────────────

    def test_1_spec_contains_you_mentioned_in_antimir_rule(self):
        """living_presence_spec.txt must contain 'you mentioned' in the anti-mirroring
        rule block (lines 243-250 range).  RED if the gap is unfilled.

        Disconnection: remove 'you mentioned' from the spec → test goes RED.
        """
        text = SPEC_PATH.read_text(encoding="utf-8").lower()
        # Confirm the anchor of the anti-mirroring rule is present
        self.assertIn(
            "do not describe the exchange back",
            text,
            "Anti-mirroring rule anchor missing from spec — something is very wrong"
        )
        # The gap this card fills
        self.assertIn(
            "you mentioned",
            text,
            "'you mentioned' is absent from living_presence_spec.txt — "
            "this is the phrase gap that card 0062 task 2 was built to close"
        )

    # ── 2: mid-response restatements are caught, not just openers ────────────

    def test_2_mid_response_restatement_is_caught(self):
        """The harness must detect 'you mentioned' mid-response, not only as opener.

        Fixture turn (synthetic): reply does NOT start with 'you mentioned' but contains
        it three words in.  The old startswith() check would miss this.  The new 'in'
        check must catch it.

        Disconnection: revert harness to startswith() → test goes RED.
        """
        synthetic_turn = {
            "n": 5,
            "user": "how does the routing decide between Groq and Cerebras?",
            "elo": "Yeah so you mentioned that the routing flips — it's actually Groq first.",
            "verdict": "FAIL — restatement mid-response",
        }
        fails = _evaluate_turn(synthetic_turn, exec_action="answer", prev_elo=None,
                               conversation_history=["how does routing work?"])
        restatement_fails = [f for f in fails if "restatement" in f and "you mentioned" in f]
        self.assertTrue(
            restatement_fails,
            "No mid-response restatement failure raised for 'you mentioned' that is NOT an opener. "
            "The detection is still opener-only (startswith). Must use 'in' check."
        )
        mid_response = [f for f in restatement_fails if "mid-response" in f]
        self.assertTrue(
            mid_response,
            "Failure was raised but not labelled 'mid-response' — check _evaluate_turn label"
        )

    # ── 3: REFLECT directive still requires specific noticing ─────────────────

    def test_3_reflect_directive_still_requires_specific_noticing(self):
        """prompt_builder.py must keep the 'specific to what they actually said' language
        in the REFLECT directive.  This is the anti-mute rule — it prevents the anti-mirroring
        fix from silencing genuine, specific observation.

        Disconnection: remove 'specific' or 'couldn\'t NOT say' from the REFLECT entry → RED.
        """
        pb_text = PB_PATH.read_text(encoding="utf-8")
        # Locate the reflect directive — it is a key in _ACTION_INSTRUCTION, value on the same line
        idx = -1
        for key in ('"reflect":   "Say', '"reflect": "Say', '"reflect"   :'):
            idx = pb_text.find(key)
            if idx >= 0:
                break
        if idx < 0:
            # fallback: find the line that both mentions reflect and "couldn't"
            for i, line in enumerate(pb_text.splitlines()):
                if '"reflect"' in line and ("specific" in line.lower() or "couldn" in line.lower()):
                    idx = pb_text.find(line)
                    break
        self.assertGreater(idx, 0, "REFLECT directive not found in prompt_builder.py")
        reflect_block = pb_text[idx: idx + 400]

        self.assertIn(
            "specific",
            reflect_block.lower(),
            "REFLECT directive no longer contains 'specific' — "
            "anti-mute rule is gone; eLo can now go silent on genuine noticing"
        )
        self.assertIn(
            "couldn",
            reflect_block.lower(),
            "REFLECT directive no longer contains \"couldn't NOT say\" — "
            "the specific-noticing anchor is missing"
        )


if __name__ == "__main__":
    unittest.main()
