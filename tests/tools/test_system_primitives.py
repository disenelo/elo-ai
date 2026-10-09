"""
WO-B3-0007 — tools/system_primitives: deterministic macOS facts, no LLM.
Headless: real macOS shell calls only (no socket, server or model). Side-effect
primitives (speak, notify, open) are not executed here.
"""
import re
import pytest
from tools.system_primitives import system, CAPABILITIES, COMMAND_VOCAB

SHAPE = {"value", "source", "authority", "confidence", "freshness"}


def _v(r):
    assert SHAPE <= set(r) and r["source"] == "macOS" and r["authority"] == "definitive", r
    assert r["confidence"] == 1.0, r
    return r["value"]


def test_time_now_returns_string():
    assert re.fullmatch(r"\d\d:\d\d:\d\d", _v(system.time.now()))


def test_math_calculate_integer():
    assert _v(system.math.calculate("25 * 17")) == "425"
    assert _v(system.math.calculate("28 × 74")) == "2072"
    assert _v(system.run("CALC", "what's 6 times 7?")) == "42"


def test_math_calculate_float():
    assert _v(system.math.calculate("10 / 3")) == "3.3333"
    assert _v(system.math.calculate("2 ^ 10")) == "1024"
    assert _v(system.math.calculate("0.5 + 0.25")) == "0.75"


@pytest.mark.parametrize("bad", ["__import__('os').system('ls')", "open('/etc/passwd')", "2+2; ls", "abc"])
def test_math_refuses_anything_but_arithmetic(bad):
    r = system.math.calculate(bad)
    assert r["value"] is None and r["confidence"] == 0.0 and "not arithmetic" in r["error"]


def test_calendar_today_returns_string():
    today = _v(system.calendar.today())
    assert re.fullmatch(r"[A-Z][a-z]+day \d{1,2} [A-Z][a-z]+ \d{4}", today)
    assert _v(system.calendar.day_of_week()) in today
    assert _v(system.calendar.tomorrow()) != today


def test_computer_battery_returns_dict():
    b = _v(system.computer.battery())
    assert set(b) >= {"percent", "charging", "power_source", "has_battery"}


def test_computer_disk_returns_dict():
    assert set(_v(system.computer.disk())) >= {"total", "free", "used"}


def test_files_search_returns_list():
    assert isinstance(_v(system.files.search("system_primitives", scope="~/elo-ai/tools")), list)
    assert _v(system.files.exists("~")) is True


def test_capabilities_dict_exists():
    assert CAPABILITIES["math.calculate"]["deterministic"] is True
    assert all(c["reasoning_required"] is False for c in CAPABILITIES.values())


def test_command_vocab_dict_exists():
    assert COMMAND_VOCAB["TIME"] == "time.now"
    assert all(v in CAPABILITIES for v in COMMAND_VOCAB.values())
    assert system.run("NOPE")["value"] is None


def test_percent_of_and_spoken_sums():
    assert _v(system.math.calculate("15% of 80")) == "12"
    assert _v(system.math.calculate("what is 15 percent of 80")) == "12"


def test_uptime_is_readable():
    up = _v(system.computer.uptime())
    assert up.startswith("up ") and "load average" not in up
