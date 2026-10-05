"""
tests/test_vault_epistemic_filter.py — WO-DREAM-EPISTEMIC-TAG-001, acceptance 3.

    "vault_layer.lookup(epistemic_filter=["VERIFIED","SOURCE_ATTRIBUTED"])
     does not return it."

The class was already being WRITTEN — 664 of 682 deep records carry
epistemic_class in frontmatter — and lookup never read it back, so a
dream-derived entry and a conversation-derived one were indistinguishable at
retrieval. That is the WO's gap stated at the vault end.
"""
from __future__ import annotations

import pathlib

import pytest

import memory.vault_layer as vl


def _deep(root: pathlib.Path, spot: str, klass: str | None, text: str) -> None:
    base = spot.replace("·", "-")
    d = root / "09 Memory" / "deep"
    d.mkdir(parents=True, exist_ok=True)
    fm = ["---", "type: memory-deep", f"spot: {spot}", "date: 2026-10-05",
          "weight: 7"]
    if klass is not None:
        fm.append(f"epistemic_class: {klass}")
    fm += ["---", "", f"# {spot}", "", text]
    (d / f"{base}-deep.md").write_text("\n".join(fm))

    idx = root / "09 Memory" / "SPOT_CODES.md"
    if not idx.exists():
        idx.write_text("---\ntype: memory-index\n---\n\n"
                       "| Spot | Bits | Summary | Date |\n"
                       "|---|---|---|---|\n")
    with idx.open("a") as f:
        f.write(f"| `{spot}` | `0001` | {text} | 2026-10-05 |\n")


@pytest.fixture
def vault(tmp_path, monkeypatch):
    # _MEM_DIR / _SUM_DIR / _DEEP_DIR / _SPOT_FILE are all derived from _VAULT
    # at IMPORT, so patching _VAULT alone leaves lookup reading David's real
    # vault. The first version of this fixture did exactly that, and its
    # baseline test passed on real records.
    import os
    mem = os.path.join(str(tmp_path), "09 Memory")
    monkeypatch.setattr(vl, "_VAULT", str(tmp_path))
    monkeypatch.setattr(vl, "_MEM_DIR", mem)
    monkeypatch.setattr(vl, "_SUM_DIR", os.path.join(mem, "summary"))
    monkeypatch.setattr(vl, "_DEEP_DIR", os.path.join(mem, "deep"))
    monkeypatch.setattr(vl, "_SPOT_FILE", os.path.join(mem, "SPOT_CODES.md"))
    _deep(tmp_path, "DR·CV·2610·7·00001", "hypothesis",
          "seams and tide charts rhyme somehow")
    _deep(tmp_path, "CO·CV·2610·7·00002", "conversation",
          "seams work is the priority this week")
    _deep(tmp_path, "OL·CV·2610·7·00003", None,
          "seams note from before the field existed")
    return tmp_path


def _spots(rows):
    return {r["spot"] for r in rows}


def test_without_a_filter_everything_comes_back(vault):
    rows = vl.lookup("seams", max_results=10)
    assert len(_spots(rows)) >= 3, "baseline: the filter is what excludes, not the query"


def test_a_dream_hypothesis_is_excluded_from_factual_recall(vault):
    """The WO's acceptance, verbatim."""
    rows = vl.lookup("seams", max_results=10,
                     epistemic_filter=["VERIFIED", "SOURCE_ATTRIBUTED",
                                       "conversation"])
    spots = _spots(rows)

    assert "DR·CV·2610·7·00001" not in spots, "dream-derived entry survived the filter"
    assert "CO·CV·2610·7·00002" in spots, "conversation entry was wrongly dropped"


def test_matching_ignores_case(vault):
    """
    The vault writes lower case, WKG and dream_review write upper. A filter
    that silently matched nothing on case would be worse than no filter.
    """
    assert _spots(vl.lookup("seams", 10, epistemic_filter=["CONVERSATION"])) == \
           _spots(vl.lookup("seams", 10, epistemic_filter=["conversation"]))


def test_an_unrecorded_class_does_not_pass_a_filter(vault):
    """18 of 682 deep records predate the field. Unknown is not a pass."""
    rows = vl.lookup("seams", max_results=10, epistemic_filter=["conversation"])
    assert "OL·CV·2610·7·00003" not in _spots(rows)


def test_the_class_is_surfaced_on_the_row(vault):
    """Callers should not have to re-open the deep file to see it."""
    rows = vl.lookup("seams", max_results=10, epistemic_filter=["conversation"])
    assert rows and rows[0].get("epistemic_class") == "conversation"
