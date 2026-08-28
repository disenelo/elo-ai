"""
tests/test_wo_fix_perception_0006.py — WO-FIX-PERCEPTION-0006

AT-1: truncated window_title → result.partial is True
AT-2: clean window_title → truncation path does NOT fire (clean title alone)
AT-3: truncated vision_text → result.partial is True
AT-4: no truncated inputs + confidence ≥ 0.7 → result.partial is False
AT-5: regression — tag_partial("cut off…") still returns "[PARTIAL: ...]"
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faculties.perception.perception_faculty import perceive, tag_partial


# ── AT-1: truncated window_title fires partial ────────────────────────────────

def test_at1_truncated_window_title_sets_partial():
    result = perceive(window_app="Chrome", window_title="A very long title that got cut…")
    assert result.partial is True, (
        f"expected partial=True for truncated window_title; got partial={result.partial}"
    )


# ── AT-2: clean title alone does not fire truncation path ────────────────────

def test_at2_clean_title_truncation_does_not_fire():
    result = perceive(window_app="Chrome", window_title="Full complete title")
    # The fix under test: a non-truncated raw input must NOT trigger _any_truncated.
    # Confidence is ~0.95 here so partial may still be False; the point is truncation alone
    # does not flip it. We verify _any_truncated would be False by checking the title is not
    # truncated — and that partial is not True due to truncation specifically.
    # (If partial were True it could only be from confidence < 0.7, which it isn't here.)
    # So: partial must be False.
    assert result.partial is False, (
        f"clean title must not trigger partial via truncation; got partial={result.partial}"
    )


# ── AT-3: truncated vision_text fires partial ─────────────────────────────────

def test_at3_truncated_vision_text_sets_partial():
    result = perceive(
        window_app="Chrome",
        window_title="Clean title",
        vision_text="Screen cut off…",
    )
    assert result.partial is True, (
        f"expected partial=True for truncated vision_text; got partial={result.partial}"
    )


# ── AT-4: no truncated inputs + confidence ≥ 0.7 → partial False ─────────────

def test_at4_no_truncation_high_confidence_not_partial():
    result = perceive(window_app="Chrome", window_title="Clean title")
    assert result.confidence >= 0.7, (
        f"expected confidence ≥ 0.7, got {result.confidence}"
    )
    assert result.partial is False, (
        f"expected partial=False with clean inputs and confidence ≥ 0.7; got {result.partial}"
    )


# ── AT-5: regression — tag_partial still works ───────────────────────────────

def test_at5_tag_partial_still_prefixes():
    result = tag_partial("cut off…")
    assert result.startswith("[PARTIAL:"), (
        f"tag_partial regression: expected '[PARTIAL:' prefix, got {result!r}"
    )
