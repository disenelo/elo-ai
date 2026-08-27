"""
conftest.py — skip script-style test files during pytest collection.

Script-style tests (no def test_ functions) use sys.exit() at module level
and are designed to be run directly: python3 tests/test_xxx.py
Importing them under pytest triggers SystemExit (INTERNALERROR).
This hook prevents pytest from importing those files.
"""


def pytest_ignore_collect(collection_path, config):
    name = collection_path.name
    if collection_path.suffix == ".py" and name.startswith("test_"):
        try:
            source = collection_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None
        if "def test_" not in source and "class Test" not in source:
            return True  # skip — script-style, not pytest-style
    return None
