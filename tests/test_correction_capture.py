"""
tests/test_correction_capture.py — a correction has to leave a mark.

Builder 2 brief, three NO verdicts sharing one cause:

    changing future behaviour after correction?  NO
        "No mechanism writes a correction back to vault or WKG.
         'Got it' with no action demonstrates this."
    learning from self-correction?               NO
    learning from feedback?                      NO

Measured 2026-10-06: self/corrections_ledger.jsonl holds 47,238 rows, so the
brief is wrong that nothing stores them. None of it is a MEMORY — the ledger
is append-only and nothing retrieves from it, so a correction could never
change a later turn. That is what "Got it" with no action looks like.

And most of it must NOT be kept:

    45,976  verify-layer scrubs — the guard WORKING          97.3%
     1,262  real corrections                                  2.7%
"""
from __future__ import annotations

import json

import pytest

from faculties.metacognition import correction_capture as cc

SCRUB = {"id": "CX-1", "why": "scrub: raw generation differed from final output",
         "input": "x", "corrected_response": "y"}
DRIFT = {"id": "CX-2", "why": "identity drift: core value 'playful' absent from response",
         "input": "x", "corrected_response": "y"}
ARITH = {"id": "CX-3", "why": "arithmetic", "input": "2+2", "corrected_response": "4"}


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    """Never the live vault or the live cursor."""
    monkeypatch.setattr(cc, "_CURSOR_PATH", str(tmp_path / "cursor.json"))
    written = []
    import memory.vault_layer as vl
    monkeypatch.setattr(vl, "write_memory",
                        lambda **kw: written.append(kw) or "SPOT-TEST")
    cc._written = written


# ── what is worth keeping ───────────────────────────────────────────────────

def test_a_real_correction_is_kept():
    assert cc.capture(DRIFT) is not None
    assert len(cc._written) == 1


def test_the_guard_working_is_not_a_correction():
    """
    97.3% of the ledger is scrubs. Writing those to the vault would bury what
    eLo knows under his own telemetry, and he would learn that he frequently
    rephrases.
    """
    assert cc.capture(SCRUB) is None
    assert cc._written == []


def test_identity_drift_outweighs_a_clarification():
    drift = cc.capture(DRIFT, apply=False)
    # corrected_response is required now — a correction with nothing on the
    # other side of it is not learnable. The first version of this fixture
    # omitted it and the test went red the moment that guard landed.
    clar = cc.capture({"id": "c", "why": "character identity clarification",
                       "input": "who are you", "corrected_response": "I'm eLo."},
                      apply=False)
    assert drift["weight"] > clar["weight"]


# ── typed, so it is answerable ──────────────────────────────────────────────

def test_the_record_is_typed_as_a_correction():
    """"What have I been corrected on" must be a query, not a grep."""
    cc.capture(ARITH)
    kw = cc._written[0]
    assert kw["source_type"] == "CORRECTION"
    assert kw["content_type"] == "correction"
    assert "correction" in kw["tags"]
    assert "arithmetic" in kw["tags"]


def test_the_kind_travels_with_it():
    cc.capture(DRIFT)
    assert any("identity_drift" in t for t in cc._written[0]["tags"])


def test_both_sides_of_the_correction_are_kept():
    """Without what was said AND what it became, there is nothing to learn from."""
    cc.capture({"id": "c", "why": "arithmetic",
                "input": "two plus two is five", "corrected_response": "it is four"})
    deep = cc._written[0]["deep_text"]
    assert "two plus two is five" in deep and "it is four" in deep


def test_it_is_inferred_not_verified():
    """
    That a correction happened is certain. That eLo was wrong in the way the
    reason says is a judgement the verify layer made.
    """
    cc.capture(ARITH)
    assert cc._written[0]["epistemic_class"] == "inferred"


# ── the cursor ──────────────────────────────────────────────────────────────

def test_the_same_correction_is_not_written_twice(monkeypatch):
    rows = [DRIFT, ARITH]
    monkeypatch.setattr("memory.spg_failure.load_corrections", lambda *a, **k: rows)

    first = cc.capture_new()
    second = cc.capture_new()

    assert first["kept"] == 2
    assert second["seen"] == 0, (
        "every tick would rewrite the same corrections — 1,262 keepable rows "
        "becoming millions of duplicate memories"
    )


def test_a_pass_is_bounded(monkeypatch):
    """47,238 rows behind the cursor must not land in one ambient tick."""
    monkeypatch.setattr("memory.spg_failure.load_corrections",
                        lambda *a, **k: [DRIFT] * 5000)
    assert cc.capture_new()["seen"] == cc.MAX_PER_PASS


def test_a_rotated_ledger_resumes_from_the_end(monkeypatch):
    monkeypatch.setattr("memory.spg_failure.load_corrections",
                        lambda *a, **k: [DRIFT] * 100)
    cc.capture_new(max_rows=100)

    monkeypatch.setattr("memory.spg_failure.load_corrections",
                        lambda *a, **k: [ARITH] * 3)
    res = cc.capture_new()
    assert res["seen"] == 0, (
        "re-reading a truncated ledger from zero would duplicate everything "
        "already kept"
    )


# ── it never costs a turn ───────────────────────────────────────────────────

def test_a_failing_vault_write_is_absorbed(monkeypatch):
    import memory.vault_layer as vl

    def _boom(**kw):
        raise RuntimeError("vault unavailable")
    monkeypatch.setattr(vl, "write_memory", _boom)
    assert cc.capture(DRIFT) is None


def test_a_malformed_row_is_skipped():
    assert cc.capture(None) is None
    assert cc.capture({}) is None


def test_the_ambient_tick_runs_it():
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "ambient" / "ambient_engine.py").read_text()
    assert "correction_capture import capture_new" in src


# ── against the real ledger ─────────────────────────────────────────────────

def test_the_real_ledger_keeps_only_the_small_minority():
    from memory.spg_failure import load_corrections
    rows = load_corrections()
    if len(rows) < 1000:
        pytest.skip("ledger not present at full size")

    kept = sum(1 for r in rows if cc.should_keep(r))
    ratio = kept / len(rows)
    assert 0.0 < ratio < 0.15, (
        f"keeping {ratio:.1%} of the ledger — scrubs are leaking into memory"
    )
