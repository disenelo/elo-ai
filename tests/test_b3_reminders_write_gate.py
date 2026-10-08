"""
B3 — reminders_agent writes ONLY on an explicit add; everything else reads.
Offline: osascript and the Reminders store read are stubbed. Not live evidence.
"""
import pytest
from tools import reminders_agent as ra


@pytest.fixture
def _no_world(monkeypatch):
    runs = []
    monkeypatch.setattr(ra, "_run", lambda script: runs.append(script) or "")
    monkeypatch.setattr(ra, "spoken_open_reminders", lambda limit=5: "READ")
    return runs


@pytest.mark.parametrize("q", ["Yeah need to do some debugging", "due",
    "No it's just asking you to do something for me so I don't have to do it.",
    "[todo_vault] nothing find in vault for to-do.\nuser asked: what's the architecture remind h",
    "remind me to", "I should remind myself to stretch"])
def test_non_add_never_writes(_no_world, q):
    assert ra.agent(q) == "READ"
    assert not any("make new reminder" in s for s in _no_world)


@pytest.mark.parametrize("q,title", [("remind me to call mum", "call mum"),
    ("Can you add a reminder to pay rent", "pay rent"), ("Add a reminder: water plants", "water plants"),
    ("[reminder_set] reminder set — in an your 'call mum'\nuser asked: remind me to call mum", "call mum")])
def test_explicit_add_writes_clean_title(_no_world, q, title):
    out = ra.agent(q)
    assert out.startswith(f"Added reminder: '{title}'")
    assert len(_no_world) == 1 and f'name:"{title}"' in _no_world[0]
