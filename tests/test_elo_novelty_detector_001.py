"""
tests/test_elo_novelty_detector_001.py — Novelty and prediction-error detector

AT-1  score_novelty() with common edge_hint → score below threshold (familiar)
AT-2  score_novelty() with rare edge_hint → score above threshold (novel)
AT-3  score_novelty() with unseen edge_hint → maximum score contribution
AT-4  score_novelty() with unseen context_tag → score boost
AT-5  score is capped at 1.0 (no overflow)
AT-6  NoveltyScore.is_novel property correct at/above threshold
AT-7  novelty_prompt_block() returns "" for familiar turn
AT-8  novelty_prompt_block() returns non-empty for novel turn
AT-9  novelty_prompt_block() block mentions the rare edge_hint
AT-10 novelty_prompt_block() block mentions unseen context_tag
AT-11 novelty_prompt_block() never raises (resilient)
AT-12 score_novelty() with real signals file — common hints score low
AT-13 Server.py wiring: novelty_prompt_block import present
AT-14 py_compile clean on novelty_detector.py and server.py
"""
from __future__ import annotations

import json
import os
import sys
import py_compile
import tempfile
from pathlib import Path

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from memory.novelty_detector import (
    score_novelty,
    novelty_prompt_block,
    NoveltyScore,
    _NOVELTY_THRESHOLD,
    _MODEL,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_signals_file(tmp_path: Path, signals: list[dict]) -> Path:
    p = tmp_path / "spg_signals.jsonl"
    with open(p, "w") as f:
        for s in signals:
            f.write(json.dumps(s) + "\n")
    return p


def _synthetic_signals(common: int = 1000, rare: int = 5) -> list[dict]:
    """Build a synthetic signals file: 'close' common, 'challenge' rare."""
    signals = []
    for _ in range(common):
        signals.append({"edge_hint": "close", "context_tags": ["work"], "signal_type": "relationship_shift"})
    for _ in range(rare):
        signals.append({"edge_hint": "challenge", "context_tags": [], "signal_type": "relationship_shift"})
    return signals


# ── AT-1 — familiar edge_hint scores low ─────────────────────────────────────

def test_at1_common_edge_hint_scores_low(tmp_path):
    signals_path = _make_signals_file(tmp_path, _synthetic_signals(common=1000, rare=5))
    # Reset model for isolated test
    from memory import novelty_detector as nd_mod
    nd_mod._MODEL = nd_mod._FrequencyModel()
    ns = score_novelty("close", context_tags=[], signals_path=signals_path)
    assert ns.score < _NOVELTY_THRESHOLD, (
        f"AT-1 FAIL: common edge_hint 'close' scored {ns.score:.3f} >= threshold "
        f"{_NOVELTY_THRESHOLD} — baseline model is miscalibrated"
    )
    nd_mod._MODEL = nd_mod._FrequencyModel()  # reset after


# ── AT-2 — rare edge_hint scores above threshold ──────────────────────────────

def test_at2_rare_edge_hint_scores_high(tmp_path):
    signals_path = _make_signals_file(tmp_path, _synthetic_signals(common=1000, rare=5))
    from memory import novelty_detector as nd_mod
    nd_mod._MODEL = nd_mod._FrequencyModel()
    ns = score_novelty("challenge", context_tags=[], signals_path=signals_path)
    assert ns.score >= _NOVELTY_THRESHOLD, (
        f"AT-2 FAIL: rare edge_hint 'challenge' scored {ns.score:.3f} — "
        f"expected >= {_NOVELTY_THRESHOLD}. Challenge appears <1% of signals."
    )
    nd_mod._MODEL = nd_mod._FrequencyModel()


# ── AT-3 — unseen edge_hint scores maximum contribution ───────────────────────

def test_at3_unseen_edge_hint_maximum_contribution(tmp_path):
    signals_path = _make_signals_file(tmp_path, _synthetic_signals(common=500))
    from memory import novelty_detector as nd_mod
    nd_mod._MODEL = nd_mod._FrequencyModel()
    ns = score_novelty("totally_new_signal", context_tags=[], signals_path=signals_path)
    # Unseen hint → _W_EDGE_UNSEEN = 0.90 contribution
    assert ns.score >= 0.80, (
        f"AT-3 FAIL: unseen edge_hint scored only {ns.score:.3f} — "
        "expected large contribution from unseen signal type"
    )
    nd_mod._MODEL = nd_mod._FrequencyModel()


# ── AT-4 — unseen context_tag boosts score ────────────────────────────────────

def test_at4_unseen_context_tag_boosts_score(tmp_path):
    signals_path = _make_signals_file(tmp_path, _synthetic_signals(common=200))
    from memory import novelty_detector as nd_mod
    nd_mod._MODEL = nd_mod._FrequencyModel()
    # 'close' is common so edge_hint alone wouldn't trigger; unseen tag should add boost
    ns_no_tag  = score_novelty("close", context_tags=[],        signals_path=signals_path)
    ns_new_tag = score_novelty("close", context_tags=["new_domain_xyz"], signals_path=signals_path)
    assert ns_new_tag.score > ns_no_tag.score, (
        "AT-4 FAIL: unseen context_tag did not boost novelty score"
    )
    assert "new_domain_xyz" in ns_new_tag.unseen_tags
    nd_mod._MODEL = nd_mod._FrequencyModel()


# ── AT-5 — score capped at 1.0 ───────────────────────────────────────────────

def test_at5_score_capped_at_one(tmp_path):
    # Many unseen tags + unseen hint → would overflow without cap
    signals_path = _make_signals_file(tmp_path, [{"edge_hint": "known", "context_tags": []}])
    from memory import novelty_detector as nd_mod
    nd_mod._MODEL = nd_mod._FrequencyModel()
    ns = score_novelty(
        "never_seen_hint",
        context_tags=["tag_a", "tag_b", "tag_c", "tag_d", "tag_e"],
        signals_path=signals_path,
    )
    assert ns.score <= 1.0, f"AT-5 FAIL: score {ns.score} exceeds 1.0"
    nd_mod._MODEL = nd_mod._FrequencyModel()


# ── AT-6 — is_novel property correct ─────────────────────────────────────────

def test_at6_is_novel_property():
    ns_low  = NoveltyScore(score=0.10, edge_hint="close",     edge_rate=0.50)
    ns_high = NoveltyScore(score=0.80, edge_hint="challenge", edge_rate=0.005)
    assert not ns_low.is_novel,  "AT-6 FAIL: score 0.10 should not be novel"
    assert ns_high.is_novel,     "AT-6 FAIL: score 0.80 should be novel"


# ── AT-7 — prompt block empty for familiar turn ───────────────────────────────

def test_at7_prompt_block_empty_for_familiar(tmp_path):
    signals_path = _make_signals_file(tmp_path, _synthetic_signals(common=500))
    from memory import novelty_detector as nd_mod
    nd_mod._MODEL = nd_mod._FrequencyModel()
    block = novelty_prompt_block("close", context_tags=[], signals_path=signals_path)
    assert block == "", (
        f"AT-7 FAIL: familiar turn produced non-empty block: '{block[:100]}'"
    )
    nd_mod._MODEL = nd_mod._FrequencyModel()


# ── AT-8 — prompt block non-empty for novel turn ─────────────────────────────

def test_at8_prompt_block_non_empty_for_novel(tmp_path):
    signals_path = _make_signals_file(tmp_path, _synthetic_signals(common=500, rare=2))
    from memory import novelty_detector as nd_mod
    nd_mod._MODEL = nd_mod._FrequencyModel()
    block = novelty_prompt_block("totally_new_signal", context_tags=[], signals_path=signals_path)
    assert block, "AT-8 FAIL: unseen edge_hint produced empty prompt block"
    assert "NOVELTY DETECTION" in block, "AT-8 FAIL: missing NOVELTY DETECTION header"
    nd_mod._MODEL = nd_mod._FrequencyModel()


# ── AT-9 — block mentions the rare edge_hint ─────────────────────────────────

def test_at9_block_mentions_rare_edge_hint(tmp_path):
    signals_path = _make_signals_file(tmp_path, _synthetic_signals(common=500, rare=2))
    from memory import novelty_detector as nd_mod
    nd_mod._MODEL = nd_mod._FrequencyModel()
    block = novelty_prompt_block("challenge", context_tags=[], signals_path=signals_path)
    if block:
        assert "challenge" in block, (
            "AT-9 FAIL: block does not mention the rare edge_hint 'challenge'"
        )
    nd_mod._MODEL = nd_mod._FrequencyModel()


# ── AT-10 — block mentions unseen context_tag ────────────────────────────────

def test_at10_block_mentions_unseen_tag(tmp_path):
    signals_path = _make_signals_file(tmp_path, _synthetic_signals(common=100))
    from memory import novelty_detector as nd_mod
    nd_mod._MODEL = nd_mod._FrequencyModel()
    block = novelty_prompt_block(
        "totally_new_signal",
        context_tags=["quantum_entanglement_topic"],
        signals_path=signals_path,
    )
    assert block, "AT-10 FAIL: novel turn produced empty block"
    assert "quantum_entanglement_topic" in block, (
        "AT-10 FAIL: block does not mention the unseen context_tag"
    )
    nd_mod._MODEL = nd_mod._FrequencyModel()


# ── AT-11 — prompt block resilient (never raises) ────────────────────────────

def test_at11_prompt_block_resilient():
    from unittest.mock import patch
    import memory.novelty_detector as nd_mod

    def _boom(*a, **kw):
        raise RuntimeError("simulated scoring failure")

    with patch.object(nd_mod, "score_novelty", _boom):
        try:
            result = nd_mod.novelty_prompt_block("any_hint")
            assert isinstance(result, str), "AT-11 FAIL: should return str on error"
        except Exception as exc:
            pytest.fail(f"AT-11 FAIL: novelty_prompt_block raised: {exc}")


# ── AT-12 — common hints in real signals file score low ───────────────────────

def test_at12_real_signals_common_hints_score_low():
    real_signals = Path(ROOT) / "data" / "spg_signals.jsonl"
    if not real_signals.exists():
        pytest.skip("No real spg_signals.jsonl found — skipping real-data test")
    from memory import novelty_detector as nd_mod
    nd_mod._MODEL = nd_mod._FrequencyModel()
    # 'close' is the most common edge_hint (~50% of 12k signals)
    ns = score_novelty("close", context_tags=[], signals_path=real_signals)
    assert ns.score < _NOVELTY_THRESHOLD, (
        f"AT-12 FAIL: 'close' edge_hint (most common ~50%) scored {ns.score:.3f} "
        f">= threshold {_NOVELTY_THRESHOLD} on real signal data"
    )
    nd_mod._MODEL = nd_mod._FrequencyModel()


# ── AT-13 — server.py wiring ─────────────────────────────────────────────────

def test_at13_server_wiring():
    server_path = os.path.join(ROOT, "server.py")
    with open(server_path, encoding="utf-8") as f:
        source = f.read()
    assert "novelty_prompt_block" in source, (
        "AT-13 FAIL: novelty_prompt_block not in server.py"
    )
    assert "memory.novelty_detector" in source, (
        "AT-13 FAIL: memory.novelty_detector import missing from server.py"
    )


# ── AT-14 — py_compile clean ─────────────────────────────────────────────────

def test_at14_py_compile_clean():
    files = [
        os.path.join(ROOT, "memory", "novelty_detector.py"),
        os.path.join(ROOT, "server.py"),
    ]
    for path in files:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"AT-14: {os.path.basename(path)} compile error: {exc}")
