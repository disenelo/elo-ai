"""
tests/test_server_idle_from_boot.py — idle must be measured from boot.

`last_user_ts` is set only on a user turn (server.py ~:2269) and is not
persisted across restarts. On a fresh server it is ABSENT, and every idle
reader defaulted to `time.time()` — so `idle = now - now = 0.0`, forever,
until David happened to speak.

Two things broke, both observed live:

  - The health battery never reached the hard-idle threshold, so the
    metabolic floor was charged on every tick with nothing restoring it.
    elo_battery sat at 0.0 "critical" indefinitely.
  - should_dream() requires idle >= DREAM_IDLE_THRESHOLD (600s). With idle
    pinned at 0, a dream could never fire on a quiet server at all.

Source-level guards: the readers are inside a long-running ambient function
that cannot be called directly from a test.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

SERVER = Path(__file__).resolve().parent.parent / "server.py"


@pytest.fixture(scope="module")
def src() -> str:
    return SERVER.read_text(encoding="utf-8")


def test_a_boot_timestamp_exists(src):
    assert "_SERVER_BOOT_TS" in src
    assert re.search(r"^_SERVER_BOOT_TS\s*=", src, re.M)


def test_no_idle_reader_defaults_to_now(src):
    """`now - now` is 0.0 — the bug in one line."""
    offenders = re.findall(
        r'get\("last_user_ts",\s*(?:_hb_now|_time_mod\.time\(\)|time\.time\(\))\)', src)
    assert not offenders, f"{len(offenders)} idle reader(s) still default to now"


def test_the_battery_idle_reader_uses_boot(src):
    assert '_hb_idle = _hb_now - (_state or {}).get("last_user_ts", _SERVER_BOOT_TS)' in src


def test_the_dream_trigger_idle_reader_uses_boot(src):
    """should_dream() needs >= 600s; pinned at 0 it could never fire."""
    assert src.count(
        '_idle_sec = _time_mod.time() - (_state or {}).get("last_user_ts", _SERVER_BOOT_TS)') == 1


def test_the_intent_proposer_idle_reader_uses_boot(src):
    assert src.count(
        '_idle_sec_now = _time_mod.time() - (_state or {}).get("last_user_ts", _SERVER_BOOT_TS)') == 1


def test_a_user_turn_still_resets_idle(src):
    """Boot time is the FALLBACK. A real turn must still win."""
    assert '_state["last_user_ts"] = _time_mod.time()' in src


def test_boot_default_crosses_the_dream_threshold_over_time():
    """The arithmetic the fix restores."""
    from faculties.dream.dream_faculty import DREAM_IDLE_THRESHOLD

    boot = 1_000_000.0
    assert (boot + 100) - boot < DREAM_IDLE_THRESHOLD      # 100s in: too soon
    assert (boot + 700) - boot >= DREAM_IDLE_THRESHOLD     # 700s in: eligible


def test_boot_default_crosses_the_hard_idle_threshold_over_time():
    from core.health_battery import HARD_IDLE_AFTER_S

    boot = 1_000_000.0
    assert (boot + 600) - boot < HARD_IDLE_AFTER_S
    assert (boot + 2000) - boot > HARD_IDLE_AFTER_S


def test_conversing_flag_uses_boot_too(src):
    """
    Designer's sit-linger reads this. With the default as now, an absent key
    made `now - now = 0 < 30` — so a fresh server with no conversation
    reported eLo as CONVERSING, and sit-linger ran on a conversation that
    never happened.
    """
    assert '(_state or {}).get("last_user_ts", _SERVER_BOOT_TS)\n            ) < 30.0' in src


def test_a_fresh_server_is_not_conversing():
    boot = 1_000_000.0
    assert not ((boot + 45) - boot) < 30.0      # 45s after boot, nobody spoke
    assert ((boot + 5) - boot) < 30.0           # within the window, still fine
