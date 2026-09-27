"""
tests/test_dream_scene_images.py — WO-DREAM-ENGINE-001 PHASE 5a/5b (DREAM-1).

DREAM-1 asks for three things:
  - openai installed
  - the actual exception surfaced, not swallowed
  - "[dream] image generation failed: <reason>" — never a silent None

The third was the real defect: the agent printed per-backend errors, but
generate() collapsed them to "All image generation backends failed." and
_generate_dream_image() then returned None with no log at all. The dream
path had nothing to say about why it had no image.

No test here makes a paid API call. The backends are stubbed.
"""
from __future__ import annotations

import pytest

import faculties.dream.dream_faculty as df
from tools import image_gen_agent as iga


def test_openai_is_installed():
    """DREAM-1 prerequisite."""
    import openai
    assert openai.__version__


# ── generate() surfaces real reasons ──────────────────────────────────────────

def test_generate_returns_per_backend_reasons_not_a_generic_string(monkeypatch):
    for name in ("_dalle3", "_dalle2", "_sd_local"):
        def fail(prompt, filename=None, _n=name):
            iga._LAST_ERRORS.append(f"{_n}: boom")
            return None
        monkeypatch.setattr(iga, name, fail)

    out = iga.generate("a prompt")
    assert out["ok"] is False
    assert len(out["errors"]) == 3
    assert "boom" in out["error"]
    assert out["error"] != "All image generation backends failed."


def test_errors_do_not_leak_between_calls(monkeypatch):
    def fail(prompt, filename=None):
        iga._LAST_ERRORS.append("one reason")
        return None
    monkeypatch.setattr(iga, "_dalle3", fail)
    monkeypatch.setattr(iga, "_dalle2", lambda p, f=None: None)
    monkeypatch.setattr(iga, "_sd_local", lambda p, f=None: None)

    first = iga.generate("a")
    second = iga.generate("b")
    assert len(first["errors"]) == len(second["errors"]) == 1


# ── Filenames and preview ─────────────────────────────────────────────────────

def test_named_output_is_used(tmp_path, monkeypatch):
    monkeypatch.setattr(iga, "_OUTPUT_DIR", tmp_path)
    assert iga._output_path("dream_abc_scene_01.png").name == "dream_abc_scene_01.png"
    assert iga._output_path("dream_abc_scene_02").name == "dream_abc_scene_02.png"


def test_unnamed_output_no_longer_collides(tmp_path, monkeypatch):
    """14 scenes generate inside one second; each must get its own file."""
    monkeypatch.setattr(iga, "_OUTPUT_DIR", tmp_path)
    names = set()
    for _ in range(5):
        p = iga._output_path()
        p.write_bytes(b"x")
        names.add(p.name)
    assert len(names) == 5


def test_filename_is_sanitised(tmp_path, monkeypatch):
    monkeypatch.setattr(iga, "_OUTPUT_DIR", tmp_path)
    out = iga._output_path("../../etc/passwd")
    assert out.parent == tmp_path
    assert "/" not in out.name


def test_preview_can_be_suppressed(tmp_path, monkeypatch):
    opened: list = []
    monkeypatch.setattr(iga, "_open_preview", lambda p: opened.append(p))
    monkeypatch.setattr(iga, "_write_hud", lambda p: None)
    img = tmp_path / "x.png"
    img.write_bytes(b"x")
    monkeypatch.setattr(iga, "_dalle3", lambda p, f=None: img)

    iga.generate("a", preview=False)
    assert opened == [], "a multi-scene dream would open a window per scene"
    iga.generate("a", preview=True)
    assert len(opened) == 1


# ── Scene generation ──────────────────────────────────────────────────────────

_CYCLES = [{
    "cycle": 1,
    "prompts": ["grounded prompt", "abstract prompt"],
    "scenes": [
        {"stage": "grounded", "intensity": 0.2},
        {"stage": "abstraction", "intensity": 0.9},
    ],
}]


def test_scene_images_are_named_per_the_wo(monkeypatch):
    seen: list = []

    def fake(prompt, filename=None, preview=True, write_hud=True):
        seen.append(filename)
        return {"ok": True, "path": f"/tmp/{filename}", "source": "stub"}

    monkeypatch.setattr("tools.image_gen_agent.generate", fake)
    out = df.generate_scene_images(_CYCLES, "a3f7c2b1")
    assert all(n.startswith("dream_a3f7c2b1_scene_") for n in seen)
    assert all(r["ok"] for r in out)


def test_highest_intensity_scenes_are_kept_when_capped(monkeypatch):
    prompts: list = []

    def fake(prompt, filename=None, preview=True, write_hud=True):
        prompts.append(prompt)
        return {"ok": True, "path": "/tmp/x.png", "source": "stub"}

    monkeypatch.setattr("tools.image_gen_agent.generate", fake)
    df.generate_scene_images(_CYCLES, "d1", limit=1)
    assert prompts == ["abstract prompt"], "cap kept the least transformed scene"


def test_preview_is_off_for_every_scene(monkeypatch):
    previews: list = []

    def fake(prompt, filename=None, preview=True, write_hud=True):
        previews.append(preview)
        return {"ok": True, "path": "/tmp/x.png", "source": "stub"}

    monkeypatch.setattr("tools.image_gen_agent.generate", fake)
    df.generate_scene_images(_CYCLES, "d1")
    assert previews == [False, False]


def test_a_failed_scene_is_logged_with_its_reason_not_silent(capsys, monkeypatch):
    def fake(prompt, filename=None, preview=True, write_hud=True):
        return {"ok": False, "error": "DALL-E 3: insufficient_quota", "errors": ["..."]}

    monkeypatch.setattr("tools.image_gen_agent.generate", fake)
    out = df.generate_scene_images(_CYCLES, "d1")
    captured = capsys.readouterr().out
    assert "[dream] image generation failed: DALL-E 3: insufficient_quota" in captured
    assert all(r["ok"] is False for r in out)
    assert out[0]["error"] == "DALL-E 3: insufficient_quota"


def test_legacy_single_image_path_also_logs_its_reason(capsys, monkeypatch):
    def fake(prompt, preview=True, **kw):
        return {"ok": False, "error": "DALL-E 3: rate limited"}

    monkeypatch.setattr("tools.image_gen_agent.generate", fake)
    assert df._generate_dream_image([{"symbol": "Bird", "meaning": "freedom"}]) is None
    assert "[dream] image generation failed: DALL-E 3: rate limited" in capsys.readouterr().out


def test_unavailable_agent_does_not_raise(monkeypatch):
    import builtins
    real = builtins.__import__

    def boom(name, *a, **k):
        if name == "tools.image_gen_agent":
            raise ImportError("gone")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", boom)
    assert df.generate_scene_images(_CYCLES, "d1") == []


# ── Cost gate ─────────────────────────────────────────────────────────────────

def test_a_test_run_never_spends_money(monkeypatch):
    """Scene generation is gated on the live-run flag, like every side effect."""
    calls: list = []
    monkeypatch.setattr("tools.image_gen_agent.generate",
                        lambda *a, **k: calls.append(1) or {"ok": False, "error": "x"})
    monkeypatch.setattr(df, "_generate_dream_image", lambda s: None)
    df._last_dream_ts = 0.0

    class _Self:
        inner_events = ["creative_spark"]
        focal_thread = "x"
        session_read = "y"
        mood = 0.5
        curiosity = 0.5

    df.run_dream(_Self(), ["robot arm"], lambda m: '{"narrative":"n","insight":"i"}',
                 idle_seconds=9000)            # publish_phases defaults False
    assert calls == [], "a default dream run made paid image calls"


def test_scene_image_cap_is_bounded():
    assert 2 <= df.DREAM_MAX_SCENE_IMAGES <= 14
