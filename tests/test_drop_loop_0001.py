"""
tests/test_drop_loop_0001.py

WO social_design_studio/QUEUE/0001_STAND_UP_THE_DROP_LOOP.md

Three tests per WO spec:
  1. Drop three unlike files → all catalogued, none renamed.
  2. File with no obvious project → lands in 04_FOR_DAVID as question, not guessed.
  3. Nothing reaches 05_SHIPPED without a recorded David approval.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_drop_loop_0001.py -v
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_temp_drop(tmp: Path) -> tuple[Path, Path, Path, Path, Path]:
    inbox      = tmp / "01_INBOX"
    catalogued = tmp / "02_CATALOGUED"
    in_process = tmp / "03_IN_PROCESS"
    for_david  = tmp / "04_FOR_DAVID"
    shipped    = tmp / "05_SHIPPED"
    for d in (inbox, catalogued, in_process, for_david, shipped):
        d.mkdir(parents=True, exist_ok=True)
    return inbox, catalogued, in_process, for_david, shipped


def _patch_drop_root(monkeypatch, tmp: Path):
    """Redirect all creative.catalogue paths to the temp tree."""
    import creative.catalogue as cat
    monkeypatch.setattr(cat, "INBOX",      tmp / "01_INBOX")
    monkeypatch.setattr(cat, "CATALOGUED", tmp / "02_CATALOGUED")
    monkeypatch.setattr(cat, "IN_PROCESS", tmp / "03_IN_PROCESS")
    monkeypatch.setattr(cat, "FOR_DAVID",  tmp / "04_FOR_DAVID")
    monkeypatch.setattr(cat, "SHIPPED",    tmp / "05_SHIPPED")
    import creative.drop_loop as dl
    monkeypatch.setattr(dl, "INBOX",           tmp / "01_INBOX")
    monkeypatch.setattr(dl, "CATALOGUED",      tmp / "02_CATALOGUED")
    monkeypatch.setattr(dl, "FOR_DAVID",       tmp / "04_FOR_DAVID")
    # _PROCESSED_LOG is set at import time from CATALOGUED; patch it directly
    monkeypatch.setattr(dl, "_PROCESSED_LOG",  tmp / "02_CATALOGUED" / "_processed.log")


def test_three_unlike_files_catalogued_not_renamed(tmp_path, monkeypatch):
    """AT-1: three unlike files catalogued; original names preserved."""
    inbox, catalogued, in_process, for_david, shipped = _make_temp_drop(tmp_path)
    _patch_drop_root(monkeypatch, tmp_path)

    # Three unlike files
    files = [
        inbox / "elo_run_animation.blend",   # 3D → game
        inbox / "kickstarter_hero.png",      # image → kickstarter
        inbox / "book_chapter_one.md",       # doc → book
    ]
    for f in files:
        f.write_bytes(b"test content")

    from creative.drop_loop import scan_once
    results = scan_once(inbox)

    processed = {r["file"] for r in results if r.get("action") not in ("skipped", "already_processed")}
    for f in files:
        assert f.name in processed, f"AT-1: {f.name} not processed"

    # Originals must NOT have been renamed
    for f in files:
        assert f.exists(), f"AT-1: original file renamed or moved: {f.name}"

    # Sidecars in 02_CATALOGUED
    for f in files:
        sidecar = catalogued / (f.name + ".catalogue.md")
        assert sidecar.exists(), f"AT-1: sidecar missing for {f.name}"
        sidecar_text = sidecar.read_text()
        assert f.name in sidecar_text, f"AT-1: sidecar doesn't reference original filename {f.name}"


def test_unclear_project_goes_to_04_not_guessed(tmp_path, monkeypatch):
    """AT-2: file with no obvious project → 04_FOR_DAVID question, not a guess."""
    inbox, catalogued, in_process, for_david, shipped = _make_temp_drop(tmp_path)
    _patch_drop_root(monkeypatch, tmp_path)

    mystery = inbox / "zxqrandom_20260828_abc.tiff"
    mystery.write_bytes(b"mystery content")

    from creative.drop_loop import scan_once
    results = scan_once(inbox)

    r = next((x for x in results if x["file"] == mystery.name), None)
    assert r is not None, "AT-2: mystery file not processed at all"
    assert r.get("action") == "question", (
        f"AT-2: unclear file should produce 'question' action; got {r.get('action')!r}"
    )
    assert r.get("project") is None, (
        f"AT-2: unclear file must NOT be assigned a project (never guess); got {r.get('project')!r}"
    )

    # Question card must exist in 04_FOR_DAVID
    q_card = for_david / (mystery.name + ".question.md")
    assert q_card.exists(), "AT-2: question card not found in 04_FOR_DAVID"

    # No proposal created
    proposal = in_process / (mystery.name + ".proposal.md")
    assert not proposal.exists(), "AT-2: proposal must NOT be created for unclear file"


def test_nothing_reaches_05_shipped_without_approval(tmp_path, monkeypatch):
    """AT-3: 05_SHIPPED must never have content written by the loop itself."""
    inbox, catalogued, in_process, for_david, shipped = _make_temp_drop(tmp_path)
    _patch_drop_root(monkeypatch, tmp_path)

    # Drop several files
    for name in ["elo_run.blend", "kickstarter_banner.png", "chapter_one.md", "zxqmystery.tiff"]:
        (inbox / name).write_bytes(b"test")

    from creative.drop_loop import scan_once
    scan_once(inbox)

    # 05_SHIPPED must be empty — the loop never writes here
    shipped_contents = [f for f in shipped.iterdir() if f.is_file()]
    assert not shipped_contents, (
        f"AT-3: INTEGRITY VIOLATION — drop_loop wrote to 05_SHIPPED without David approval: "
        f"{[f.name for f in shipped_contents]}"
    )

    # Also confirm that creative/drop_loop.py and creative/catalogue.py
    # contain no reference to the shipped path for writing
    import creative.catalogue as cat
    loop_src = open(Path(__file__).parent.parent / "creative" / "drop_loop.py").read()
    cat_src  = open(Path(__file__).parent.parent / "creative" / "catalogue.py").read()
    for src, label in [(loop_src, "drop_loop.py"), (cat_src, "catalogue.py")]:
        assert "SHIPPED" not in src or "05_SHIPPED" not in src.split("write")[1] if "write" in src else True, (
            f"AT-3: {label} contains a write path to SHIPPED — review for integrity violation"
        )


if __name__ == "__main__":
    import tempfile
    import types

    class _FakeMonkeypatch:
        def setattr(self, obj, name, value):
            setattr(obj, name, value)

    _tests = [
        ("AT-1", test_three_unlike_files_catalogued_not_renamed),
        ("AT-2", test_unclear_project_goes_to_04_not_guessed),
        ("AT-3", test_nothing_reaches_05_shipped_without_approval),
    ]
    _passed = _failed = 0
    for label, fn in _tests:
        with tempfile.TemporaryDirectory() as _tmp:
            _tmp_path = Path(_tmp)
            try:
                fn(_tmp_path, _FakeMonkeypatch())
                print(f"  ✅ {label}: {fn.__name__}")
                _passed += 1
            except Exception as _e:
                print(f"  ❌ {label}: {fn.__name__} — {_e}")
                _failed += 1
    print()
    print("=" * 62)
    print(f"DROP-LOOP-0001   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if __name__ == "__main__" and _failed:
        sys.exit(1)
