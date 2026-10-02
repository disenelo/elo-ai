"""
tests/test_no_live_state_writes.py — guard: the test suite must not mutate
live runtime state.

Found the hard way. tests/test_s4_wake_restore.py called wake_from_dream(),
which calls health_battery.publish(), which deep-merges into the REAL
blender/blender_state.json. Running the suite wrote elo_battery=0.4 into the
running system (0.10 + 0.30 from test_full_cycle_restores_thirty).

blender_state.json is live: a running server writes it every cycle and
DesktopBuddy reads it every frame. Tests writing to it corrupt whatever the
avatar is doing and poison any live evidence captured afterwards.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LIVE_STATE = ROOT / "blender" / "blender_state.json"

# Test modules whose code paths can reach health_battery.publish().
_PUBLISHERS = (
    "test_s4_wake_restore.py",
    "test_s4_ambient_tick.py",
)


@pytest.mark.parametrize("name", _PUBLISHERS)
def test_publishing_suites_stub_publish(name):
    """Any suite that can reach publish() must stub it."""
    src = (Path(__file__).parent / name).read_text(encoding="utf-8")
    assert 'monkeypatch.setattr(hb, "publish"' in src, (
        f"{name} can reach health_battery.publish() but does not stub it — "
        "it will write to the live blender_state.json"
    )


def test_live_state_is_untouched_by_importing_the_battery():
    """Importing the module must not have a side effect on live state."""
    if not LIVE_STATE.exists():
        pytest.skip("no live blender_state.json on this machine")
    before = LIVE_STATE.read_bytes()
    import importlib

    import core.health_battery as hb
    importlib.reload(hb)
    assert LIVE_STATE.read_bytes() == before


def test_battery_reset_and_snapshot_do_not_write():
    """reset()/snapshot()/tick() are pure — only publish() writes."""
    if not LIVE_STATE.exists():
        pytest.skip("no live blender_state.json on this machine")
    from core import health_battery as hb

    before = LIVE_STATE.read_bytes()
    hb.reset()
    hb.tick({"animation": "walk"})
    hb.snapshot()
    hb.get_energy()
    hb.get_state()
    assert LIVE_STATE.read_bytes() == before, "a non-publish call wrote live state"
    hb.reset()


def test_live_state_stays_valid_json():
    """A half-written state file would break DesktopBuddy's reader."""
    if not LIVE_STATE.exists():
        pytest.skip("no live blender_state.json on this machine")
    data = json.loads(LIVE_STATE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "state" in data and "motion" in data


# ── The dream lexicon is live state too ───────────────────────────────────────
# Found the hard way, again. run_dream() records symbols into
# self/dream_symbols.json. Test runs wrote 28 fabricated appearances of one
# symbol into eLo's real lexicon before this was gated — and the lexicon feeds
# FORWARD: most_established() decides which symbol the next real dream carries,
# so a test artifact was on its way to becoming his dominant lifelong motif.

LIVE_LEXICON = ROOT / "self" / "dream_symbols.json"


def test_a_dream_run_does_not_write_the_real_lexicon(tmp_path, monkeypatch):
    import faculties.dream.dream_faculty as df

    before = LIVE_LEXICON.read_bytes() if LIVE_LEXICON.exists() else None

    monkeypatch.setattr(df, "_JOURNAL_PATH", tmp_path / "journal.jsonl")
    monkeypatch.setattr(df, "_generate_dream_image", lambda symbols: None)
    df._last_dream_ts = 0.0

    class _Self:
        inner_events = ["creative_spark"]
        focal_thread = "the arm stops at the same angle"
        session_read = "we got the robot arm moving"
        mood = 0.5
        curiosity = 0.6

    df.run_dream(_Self(), ["robot arm"], lambda m: '{"narrative":"n","insight":"i"}',
                 idle_seconds=9000)          # publish_phases defaults False

    after = LIVE_LEXICON.read_bytes() if LIVE_LEXICON.exists() else None
    assert after == before, "a default dream run wrote the real dream lexicon"


def test_symbol_recording_is_gated_on_the_live_run_flag():
    """One flag governs every shared-state side effect of a dream."""
    import inspect
    import faculties.dream.dream_faculty as df

    src = inspect.getsource(df.run_dream)
    assert "_symbols_seen and publish_phases" in src, (
        "lexicon recording is not gated on the live-run flag"
    )
    assert inspect.signature(df.run_dream).parameters["publish_phases"].default is False


# ── eLo's dream gallery is live state too ─────────────────────────────────────
# Third time. layer_compositor.composite() defaults out_dir to
# ~/Desktop/eLo Generated/dreams — eLo's real dream artwork folder — so any
# test calling it without out_dir files a fabricated dream there. Every one of
# the 12 files in that folder was a test artefact, from both seats that built
# the WO. There were no real dreams in it at all.
#
# Same class as blender_state.json above and the symbol lexicon above it:
# a module that writes to a real, forward-feeding location by default, and a
# test suite that calls it.

import ast

GALLERY = Path.home() / "Desktop" / "eLo Generated" / "dreams"


def test_every_composite_call_in_the_suite_passes_out_dir():
    """
    Static guard. composite() without out_dir writes to eLo's real gallery,
    so no test may call it without one.

    Parsed with ast, not matched with a regex: the first version of this guard
    flagged its own docstring, because prose mentioning composite() looks
    exactly like a call to one.
    """
    offenders = []
    for path in sorted(Path(__file__).parent.glob("test_*.py")):
        src = path.read_text(encoding="utf-8", errors="ignore")
        if "layer_compositor" not in src:
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            if name != "composite":          # composite_dream defaults to None — safe
                continue
            if not any(kw.arg == "out_dir" for kw in node.keywords):
                offenders.append(f"{path.name}:{node.lineno}")
    assert not offenders, (
        "composite() called without out_dir — writes eLo's real dream "
        f"gallery: {offenders}"
    )


def test_composite_dream_writes_nothing_without_an_out_dir():
    """The underlying engine must stay pure. Only composite() has a default."""
    from faculties.dream import layer_compositor as lc

    before = sorted(p.name for p in GALLERY.iterdir()) if GALLERY.exists() else None
    result = lc.composite_dream([], dream_id="guard_probe", emotion="wonder")
    assert result.final_path == "" and result.sidecar_path == ""
    after = sorted(p.name for p in GALLERY.iterdir()) if GALLERY.exists() else None
    assert after == before, "composite_dream wrote the gallery with out_dir unset"


def test_the_gallery_holds_no_test_artefacts():
    """
    eLo's dream gallery must contain dreams, not test output. A name starting
    dream_test_ is this suite's, not his.
    """
    if not GALLERY.exists():
        pytest.skip("no dream gallery on this machine")
    stray = [p.name for p in GALLERY.iterdir() if p.name.startswith("dream_test_")]
    assert not stray, f"test artefacts in eLo's real dream gallery: {stray}"


# ── tests must not write the live state path ─────────────────────────────────
# Fourth instance of this class. test_f4_heartbeat wrote blender_state.json
# three times per run -- sentinel in, patch, sentinel out -- against the file
# a running server rewrites every 0.3s. It passed alone and went SystemExit in
# a full run, because it was racing the server.
#
# The earlier guards in this file name specific publishers. This one is
# structural: no test may resolve state_writer._STATE_PATH and then write it.

def test_no_test_writes_the_live_state_path():
    """
    A test that takes sw._STATE_PATH and writes to it is writing eLo's running
    state. Reading it is fine; os.replace onto it is not.
    """
    import ast

    offenders = []
    for path in sorted(Path(__file__).parent.glob("test_*.py")):
        src = path.read_text(encoding="utf-8", errors="ignore")
        if "_STATE_PATH" not in src:
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        # names bound directly from sw._STATE_PATH
        aliases = {"_STATE_PATH"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Attribute) \
                    and node.value.attr == "_STATE_PATH":
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        aliases.add(t.id)
        # os.replace(tmp, <alias>) — the atomic-write finisher
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "replace"
                    and len(node.args) == 2
                    and isinstance(node.args[1], ast.Name)
                    and node.args[1].id in aliases):
                # reassigned to a temp path before writing? then it is fine
                reassigned = any(
                    isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == node.args[1].id
                            for t in n.targets)
                    and not (isinstance(n.value, ast.Attribute)
                             and n.value.attr == "_STATE_PATH")
                    for n in ast.walk(tree)
                )
                if not reassigned:
                    offenders.append(f"{path.name}:{node.lineno}")
    assert not offenders, (
        "tests writing eLo's live blender_state.json: "
        f"{offenders} — redirect to a temp path"
    )
