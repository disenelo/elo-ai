"""
tests/test_cognitive_journal.py

WP_F gap: core/cognitive_journal.py — eLo cognitive journal read/write.
Pure stdlib, no external dependencies. Tests use a temp file so no
production journal data is touched.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_cognitive_journal.py -q
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.cognitive_journal import (
    JournalEntry,
    append_entry,
    load_recent_entries,
    build_journal_context,
    find_by_project,
)


def _tmp_journal() -> str:
    fd, path = tempfile.mkstemp(suffix=".journal.txt", prefix="test_cj_")
    os.close(fd)
    return path


def _entry(title="Test Entry", project="elo_core", tags=None, body="This is the body."):
    return JournalEntry(
        date="2026-08-27",
        entry_type="insight",
        title=title,
        project=project,
        tags=tags or ["test"],
        body=body,
    )


def test_append_and_load_roundtrip():
    """AT-1: append_entry() writes a record; load_recent_entries() reads it back."""
    path = _tmp_journal()
    try:
        entry = _entry()
        result = append_entry(entry, path)
        assert isinstance(result, str), f"AT-1: append_entry must return a string; got {type(result)}"
        loaded = load_recent_entries(path, days=365)
        assert len(loaded) >= 1, f"AT-1: must load >=1 entry after append; got {len(loaded)}"
        titles = [e.title for e in loaded]
        assert "Test Entry" in titles, f"AT-1: appended entry title not found in loaded; got {titles}"
    finally:
        os.unlink(path)


def test_append_does_not_overwrite_existing():
    """AT-2: multiple appends accumulate entries."""
    path = _tmp_journal()
    try:
        for i in range(3):
            append_entry(_entry(title=f"Entry {i}"), path)
        loaded = load_recent_entries(path, days=365)
        assert len(loaded) >= 3, (
            f"AT-2: 3 appends must yield >=3 entries; got {len(loaded)}"
        )
    finally:
        os.unlink(path)


def test_find_by_project_filters_correctly():
    """AT-3: find_by_project() returns only entries matching the project."""
    path = _tmp_journal()
    try:
        append_entry(_entry(project="elo_core"), path)
        append_entry(_entry(project="other_project"), path)
        found = find_by_project(path, "elo_core")
        assert all(e.project == "elo_core" for e in found), (
            f"AT-3: find_by_project must only return 'elo_core' entries; got {[e.project for e in found]}"
        )
        not_found = find_by_project(path, "nonexistent_project")
        assert not_found == [], (
            f"AT-3: nonexistent project must return empty list; got {not_found!r}"
        )
    finally:
        os.unlink(path)


def test_build_journal_context_is_string_within_limit():
    """AT-4: build_journal_context() returns a string within max_chars."""
    entries = [_entry(title=f"E{i}", body="x" * 200) for i in range(10)]
    ctx = build_journal_context(entries, max_chars=1500)
    assert isinstance(ctx, str), f"AT-4: build_journal_context must return str; got {type(ctx)}"
    assert len(ctx) <= 1500, (
        f"AT-4: context must be <=1500 chars; got {len(ctx)}"
    )


def test_load_recent_entries_missing_file_returns_empty():
    """AT-5: load_recent_entries() on a missing file returns empty list (no crash)."""
    result = load_recent_entries("/nonexistent/path/journal.txt", days=7)
    assert result == [], (
        f"AT-5: missing journal file must return empty list; got {result!r}"
    )


def test_journal_entry_dataclass_defaults():
    """AT-6: JournalEntry has expected fields and list defaults."""
    entry = JournalEntry(date="2026-08-27", entry_type="decision", title="Ruling")
    assert entry.project == "", f"AT-6: default project must be ''; got {entry.project!r}"
    assert entry.characters == [], f"AT-6: default characters must be []; got {entry.characters!r}"
    assert entry.tags == [], f"AT-6: default tags must be []; got {entry.tags!r}"


if __name__ == "__main__":
    _tests = [
        ("AT-1", test_append_and_load_roundtrip),
        ("AT-2", test_append_does_not_overwrite_existing),
        ("AT-3", test_find_by_project_filters_correctly),
        ("AT-4", test_build_journal_context_is_string_within_limit),
        ("AT-5", test_load_recent_entries_missing_file_returns_empty),
        ("AT-6", test_journal_entry_dataclass_defaults),
    ]
    _passed = _failed = 0
    for label, fn in _tests:
        try:
            fn()
            print(f"  ✅ {label}: {fn.__name__}")
            _passed += 1
        except Exception as _e:
            print(f"  ❌ {label}: {fn.__name__} — {_e}")
            _failed += 1
    print()
    print("=" * 62)
    print(f"cognitive_journal   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
