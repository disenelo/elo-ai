"""
tests/test_file_lock.py — WO-B1-0107 file lock protocol tests
"""

import os
import pytest
import tempfile
from tools.file_lock import acquire, release, check


@pytest.fixture()
def tmp_target(tmp_path):
    f = tmp_path / "server.py"
    f.write_text("# placeholder")
    yield str(f)
    # clean up any leftover lock
    lock = str(f) + ".lock"
    if os.path.exists(lock):
        os.remove(lock)


def test_acquire_creates_lockfile(tmp_target):
    result = acquire(tmp_target, seat="Builder1", purpose="test acquire")
    assert result is True
    assert os.path.exists(tmp_target + ".lock")
    release(tmp_target)


def test_acquire_returns_false_if_already_locked(tmp_target):
    acquire(tmp_target, seat="Builder1", purpose="first lock")
    result = acquire(tmp_target, seat="Builder2", purpose="second lock")
    assert result is False
    release(tmp_target)


def test_release_deletes_lockfile(tmp_target):
    acquire(tmp_target, seat="Builder1", purpose="test release")
    release(tmp_target)
    assert not os.path.exists(tmp_target + ".lock")


def test_check_returns_none_when_free(tmp_target):
    assert check(tmp_target) is None


def test_check_returns_dict_when_held(tmp_target):
    acquire(tmp_target, seat="Builder1", purpose="test check")
    info = check(tmp_target)
    assert isinstance(info, dict)
    assert info["seat"] == "Builder1"
    assert info["purpose"] == "test check"
    assert info["file"] == tmp_target
    assert "timestamp" in info
    release(tmp_target)
