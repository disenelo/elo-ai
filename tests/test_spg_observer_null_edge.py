"""
tests/test_spg_observer_null_edge.py — the same null that killed habit_tracker.

data/spg_signals.jsonl carries 43 rows with `edge_hint: null` out of 14707.
`.get("edge_hint", "")` returns None for those — the default only applies when
the key is ABSENT — and `.strip()` then raises.

That shape took habit_tracker out completely: it read the whole file, the
AttributeError escaped its JSONDecodeError-only handler, and 7070 observations
of one habit reported as zero.

spg_observer._action_patterns has the identical line and RAISES on the full
file — verified. It survives today only because the live caller reads a recent
window and all 43 nulls sit at indices 2386-3150, the newest 11556 rows from
the end. So this is a LATENT crash, not a live one, and it fires the moment a
null lands in the window.

Not inflating it: today the block works. It is one line, the class is proven,
and leaving a known landmine in because it has not gone off yet is how the
habit_tracker one survived.
"""
from __future__ import annotations

import pytest

from memory.spg_observer import _action_patterns


def _sig(hint, ts=0.0):
    return {"edge_hint": hint, "ts": ts}


def test_a_null_edge_hint_does_not_raise():
    rows = [_sig("close", i) for i in range(30)] + [_sig(None, 31)]
    _action_patterns(rows)          # must not raise


def test_a_missing_key_does_not_raise():
    rows = [_sig("reflect", i) for i in range(30)] + [{"ts": 31}]
    _action_patterns(rows)


def test_a_non_string_hint_does_not_raise():
    rows = [_sig("build", i) for i in range(30)] + [_sig(5, 31), _sig(["x"], 32)]
    _action_patterns(rows)


def test_the_good_rows_are_still_counted():
    """
    The point of the fix: one bad row skips that row, it does not cost the
    other thirty. That is exactly what habit_tracker got wrong.
    """
    rows = [_sig("close", i) for i in range(30)] + [_sig(None, 31)]
    obs = _action_patterns(rows)
    assert obs, "30 good signals produced no observation"
    assert any("close" in str(o.__dict__) for o in obs)


def test_it_survives_the_whole_live_file():
    """The file that raises today, read in full."""
    import json
    import pathlib
    p = pathlib.Path(__file__).resolve().parent.parent / "data" / "spg_signals.jsonl"
    if not p.exists():
        pytest.skip("no live signals")
    rows = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    assert any(r.get("edge_hint") is None for r in rows if isinstance(r, dict)), \
        "precondition: the live file still contains null edge_hints"
    _action_patterns(rows)          # must not raise
