"""
tests/test_spg_significance.py — WO-SPG-PATTERN-001.

Board held the SPG backfill until a scoring function exists, with three
inputs in priority order: relationship type weight, recurrence,
confidence as tiebreaker only.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from memory.spg_significance import (
    RELATIONSHIP_WEIGHT, W_CONFIDENCE, score_all, score_claim, triple,
)

_VOCAB = json.loads(
    (pathlib.Path(__file__).resolve().parent.parent / "memory" / "wkg"
     / "relationship_types.json").read_text(encoding="utf-8"))


def _claim(rel="ASSOCIATED_WITH", conf=0.7, cid="c1", s="s", o="o"):
    return {"claim_id": cid, "relationship_type": rel, "confidence": conf,
            "subject_entity_id": s, "object_entity_id": o}


# ── The weights are over types that exist ──────────────────────────────────

def test_every_weighted_type_is_in_the_vocabulary():
    """
    The defect WO-SPG-LINK-002 found in the CCM map: 11 of 12 named types
    could not exist on a claim, so the filter silently selected nothing.
    """
    assert set(RELATIONSHIP_WEIGHT) <= set(_VOCAB), \
        set(RELATIONSHIP_WEIGHT) - set(_VOCAB)


def test_every_vocabulary_type_has_a_weight():
    """A real type with no weight would silently score as unknown."""
    assert set(_VOCAB) <= set(RELATIONSHIP_WEIGHT), \
        set(_VOCAB) - set(RELATIONSHIP_WEIGHT)


@pytest.mark.parametrize("phantom", ["DECIDED", "FACT", "BELIEF", "OBSERVATION"])
def test_the_names_in_the_ruling_are_not_real_types(phantom):
    """
    Documents the deviation rather than hiding it. The Board's ordering is
    "DECIDED > FACT > BELIEF > OBSERVATION > ASSOCIATED_WITH"; only the
    last exists. The ordering is honoured, the names are mapped.
    """
    assert phantom not in _VOCAB


def test_associated_with_is_last_as_ruled():
    assert RELATIONSHIP_WEIGHT["ASSOCIATED_WITH"] == min(RELATIONSHIP_WEIGHT.values())


def test_a_structural_relation_outranks_a_bare_association():
    assert score_claim(_claim("CAUSES")) > score_claim(_claim("ASSOCIATED_WITH"))
    assert score_claim(_claim("IS")) > score_claim(_claim("ASSOCIATED_WITH"))


def test_an_unknown_type_scores_as_the_weakest_not_as_zero():
    """A new legitimate relation must not become invisible."""
    assert score_claim(_claim("SOMETHING_NEW")) == score_claim(_claim("ASSOCIATED_WITH"))


# ── Recurrence ─────────────────────────────────────────────────────────────

def test_recurrence_raises_significance():
    once = score_claim(_claim(), recurrence=1)
    often = score_claim(_claim(), recurrence=40)
    assert often > once


def test_recurrence_is_log_scaled_not_linear():
    """
    Live counts span 1 to 1118. The step from 1 to 10 must matter more than
    1000 to 1100, or one runaway triple swamps everything.
    """
    # Equal ABSOLUTE steps at the low and high end. Log scaling makes the
    # low step worth more; linear makes them identical. Comparing 1-vs-10
    # against 1000-vs-1100 could not tell them apart, because both forms
    # saturate up there — a wire-cut to linear left this green and that is
    # how the weak version was found.
    low  = score_claim(_claim(), recurrence=4)  - score_claim(_claim(), recurrence=2)
    high = score_claim(_claim(), recurrence=40) - score_claim(_claim(), recurrence=38)
    assert low > high, (low, high)


def test_recurrence_saturates():
    assert score_claim(_claim(), recurrence=1000) == score_claim(_claim(), recurrence=100000)


def test_score_all_counts_recurrence_across_the_batch():
    claims = [_claim(cid=f"c{i}") for i in range(5)] + [_claim(cid="x", s="other")]
    out = score_all(claims)
    assert out["c0"] > out["x"], "a repeated triple must outscore a singleton"
    assert len(out) == 6


# ── Confidence is a tiebreaker and nothing more ────────────────────────────

def test_confidence_cannot_outrank_type():
    weak_but_certain = score_claim(_claim("ASSOCIATED_WITH", conf=1.0))
    strong_but_unsure = score_claim(_claim("CAUSES", conf=0.0))
    assert strong_but_unsure > weak_but_certain


def test_confidence_cannot_outrank_recurrence():
    assert score_claim(_claim(conf=0.0), recurrence=40) > score_claim(_claim(conf=1.0), recurrence=1)


def test_confidence_does_break_a_tie():
    assert score_claim(_claim(conf=0.9)) > score_claim(_claim(conf=0.5))


def test_its_whole_influence_is_bounded_by_its_weight():
    spread = score_claim(_claim(conf=1.0)) - score_claim(_claim(conf=0.0))
    assert spread == pytest.approx(W_CONFIDENCE, abs=1e-6)


# ── Shape ──────────────────────────────────────────────────────────────────

def test_scores_are_clamped_and_deterministic():
    c = _claim("CAUSES", conf=1.0)
    assert 0.0 <= score_claim(c, recurrence=10_000) <= 1.0
    assert score_claim(c) == score_claim(c)


def test_a_missing_confidence_does_not_crash():
    assert 0.0 <= score_claim({"relationship_type": "IS"}) <= 1.0
    assert 0.0 <= score_claim({"relationship_type": "IS", "confidence": None}) <= 1.0


def test_triple_identifies_a_claim_by_its_content_not_its_id():
    assert triple(_claim(cid="a")) == triple(_claim(cid="b"))


# ── Against the live store ─────────────────────────────────────────────────

def test_the_live_store_would_not_score_flat():
    """
    The reason the backfill was held. WO-SPG-LINK-004 added a FLAT warning
    for exactly this: nodes linked but every score identical, so the sort
    is a no-op that merely stops warning. If this ever collapses to one
    value, the backfill must stay held.
    """
    claims = json.loads(
        (pathlib.Path(__file__).resolve().parent.parent / "memory" / "wkg"
         / "claims.json").read_text(encoding="utf-8"))
    if not claims:
        pytest.skip("no live claims")
    distinct = set(score_all(claims).values())
    assert len(distinct) > 1, "scoring is flat — a backfill would be inert"
