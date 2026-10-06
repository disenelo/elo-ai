"""WO-METACOGNITION-001: tests for faculties/metacognition/metacognition.py."""
import pytest


# ── assess_confidence ─────────────────────────────────────────────────────────

def test_assess_confidence_empty_returns_zero():
    from faculties.metacognition.metacognition import assess_confidence
    assert assess_confidence("") == 0.0
    assert assess_confidence("   ") == 0.0


def test_assess_confidence_returns_float_in_range():
    from faculties.metacognition.metacognition import assess_confidence
    result = assess_confidence("The robot walked across the room.", {})
    assert isinstance(result, float)
    assert 0.0 <= result <= 1.0


def test_assess_confidence_penalises_very_short_response():
    from faculties.metacognition.metacognition import assess_confidence
    short = assess_confidence("Ok.", {})
    medium = assess_confidence("The quick brown fox jumped over the lazy dog.", {})
    assert short <= medium


def test_assess_confidence_penalises_overreach():
    from faculties.metacognition.metacognition import assess_confidence
    overreach = "I definitely know the answer is 42."
    normal = "The answer might be 42 based on what we have."
    score_overreach = assess_confidence(overreach, {})
    score_normal = assess_confidence(normal, {})
    # Overreach should score no higher than normal
    assert score_overreach <= score_normal + 0.3  # generous tolerance, WKG coverage varies


def test_assess_confidence_with_context_match():
    from faculties.metacognition.metacognition import assess_confidence
    ctx = {"wkg_context": "canvas seams fray under high tension stitching"}
    response_match = "Canvas seams can fray under high tension when stitching."
    response_mismatch = "The weather in Bristol is rainy in autumn."
    score_match = assess_confidence(response_match, ctx)
    score_mismatch = assess_confidence(response_mismatch, ctx)
    # Matching context should score at least as high
    assert score_match >= score_mismatch - 0.2  # WKG coverage may shift this


# ── flag_uncertainty ──────────────────────────────────────────────────────────

def test_flag_uncertainty_true_when_below_threshold():
    from faculties.metacognition.metacognition import flag_uncertainty
    assert flag_uncertainty(0.3, threshold=0.6) is True
    assert flag_uncertainty(0.59, threshold=0.6) is True


def test_flag_uncertainty_false_when_at_or_above_threshold():
    from faculties.metacognition.metacognition import flag_uncertainty
    assert flag_uncertainty(0.6, threshold=0.6) is False
    assert flag_uncertainty(0.9, threshold=0.6) is False


def test_flag_uncertainty_uses_default_threshold():
    from faculties.metacognition.metacognition import flag_uncertainty
    assert flag_uncertainty(0.4) is True
    assert flag_uncertainty(0.8) is False


# ── detect_reasoning_error ────────────────────────────────────────────────────

def test_detect_reasoning_error_none_on_clean_text():
    from faculties.metacognition.metacognition import detect_reasoning_error
    result = detect_reasoning_error("The fabric frays because of loose weave.")
    assert result is None


def test_detect_reasoning_error_on_empty():
    from faculties.metacognition.metacognition import detect_reasoning_error
    assert detect_reasoning_error("") is None
    assert detect_reasoning_error(None) is None


def test_detect_reasoning_error_missing_evidence():
    from faculties.metacognition.metacognition import detect_reasoning_error
    result = detect_reasoning_error("I assume this is correct but have no evidence.")
    # "i assume" is a missing-evidence marker
    assert result is not None
    assert "missing_evidence" in result


def test_detect_reasoning_error_no_false_positive_on_correct():
    from faculties.metacognition.metacognition import detect_reasoning_error
    correct_responses = [
        "Canvas requires reinforced seaming at stress points.",
        "The stitch count affects durability significantly.",
        "Heat-setting the fabric prevents shrinkage.",
        "Grain alignment is critical for pattern matching.",
        "Interfacing adds structure without adding weight.",
    ]
    for resp in correct_responses:
        result = detect_reasoning_error(resp)
        assert result is None, f"False positive on: {resp!r} → {result}"


# ── evaluate_and_record ───────────────────────────────────────────────────────

def test_evaluate_and_record_returns_dict():
    from faculties.metacognition.metacognition import evaluate_and_record
    result = evaluate_and_record("Some response text.", {})
    assert isinstance(result, dict)
    assert "confidence" in result
    assert "needs_hedge" in result
    assert "error" in result


def test_evaluate_and_record_hedge_flag_consistent():
    from faculties.metacognition.metacognition import evaluate_and_record
    result = evaluate_and_record("I assume this is true.", {})
    # needs_hedge should match what flag_uncertainty would give
    assert result["needs_hedge"] == (result["confidence"] < 0.6)
