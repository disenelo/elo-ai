"""
INT7-HEAT Builder acceptance tests — brain_state.json cognitive heat-map signals.

AT-1  All 9 systems have 'rate' field (0–1 float)
AT-2  All 9 systems have 'confidence' field (0–1 float)
AT-3  rate values are clamped [0, 1] across all systems
AT-4  confidence values are clamped [0, 1] across all systems
AT-5  high-intensity call produces higher mean rate than low-intensity call
AT-6  voice-active system has non-trivially higher rate than voice-silent
AT-7  intent-present raises intent.confidence above intent-absent baseline
AT-8  schema: existing fields (energy, valence, active, label, detail) unchanged
AT-9  publish() still returns True (writes successfully, no crash)
AT-10 Frozen kernel untouched (executive.py + prompts/ unchanged)
"""
import importlib.util
import json
import os
import sys
import tempfile

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_WRITER_PATH = os.path.join(_ROOT, "blender_bridge", "brain_state_writer.py")

_spec = importlib.util.spec_from_file_location("brain_state_writer_test", _WRITER_PATH)
_mod  = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

_SYSTEMS = ("intent", "attention", "emotion", "memory", "motion", "body", "vision", "expression", "voice")


def _call(tmp_path, **kwargs):
    """Call publish() with a writable temp path; return the systems dict."""
    defaults = dict(
        emotion="neutral", intensity=0.5, energy=0.5, mode="idle",
        motion_speed=0.55, motion_intensity=0.5,
        vision_active=False, vision_attention=0.0, vision_app="",
        expression_intensity=0.5, expression_pacing="steady",
        intent="", memory_energy=-1.0, voice_active=False,
        self_mood=0.5, self_curiosity=0.5, show_one_brain=True,
    )
    defaults.update(kwargs)
    # Redirect write to temp file
    orig = _mod._STATE_PATH
    _mod._STATE_PATH = tmp_path
    try:
        ok = _mod.publish(**defaults)
    finally:
        _mod._STATE_PATH = orig
    with open(tmp_path, encoding="utf-8") as f:
        return json.load(f), ok


def _tmp():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    return path


# ── AT-1 ─────────────────────────────────────────────────────────────────────

def test_at1_rate_present():
    path = _tmp()
    try:
        data, _ = _call(path)
        for s in _SYSTEMS:
            assert "rate" in data["systems"][s], f"AT-1 FAIL: {s} missing 'rate'"
    finally:
        os.unlink(path)
    print("AT-1 PASS — all 9 systems have 'rate'")


# ── AT-2 ─────────────────────────────────────────────────────────────────────

def test_at2_confidence_present():
    path = _tmp()
    try:
        data, _ = _call(path)
        for s in _SYSTEMS:
            assert "confidence" in data["systems"][s], f"AT-2 FAIL: {s} missing 'confidence'"
    finally:
        os.unlink(path)
    print("AT-2 PASS — all 9 systems have 'confidence'")


# ── AT-3 ─────────────────────────────────────────────────────────────────────

def test_at3_rate_clamped():
    path = _tmp()
    try:
        data, _ = _call(path, intensity=1.0, motion_speed=1.5, vision_active=True, vision_attention=1.0)
        for s in _SYSTEMS:
            r = data["systems"][s]["rate"]
            assert 0.0 <= r <= 1.0, f"AT-3 FAIL: {s}.rate={r} out of [0, 1]"
    finally:
        os.unlink(path)
    print("AT-3 PASS — all rate values clamped [0, 1]")


# ── AT-4 ─────────────────────────────────────────────────────────────────────

def test_at4_confidence_clamped():
    path = _tmp()
    try:
        data, _ = _call(path, intensity=1.0, vision_active=True, vision_attention=1.0)
        for s in _SYSTEMS:
            c = data["systems"][s]["confidence"]
            assert 0.0 <= c <= 1.0, f"AT-4 FAIL: {s}.confidence={c} out of [0, 1]"
    finally:
        os.unlink(path)
    print("AT-4 PASS — all confidence values clamped [0, 1]")


# ── AT-5 ─────────────────────────────────────────────────────────────────────

def test_at5_high_intensity_higher_rate():
    path = _tmp()
    try:
        hi, _ = _call(path, intensity=0.9, motion_speed=1.2)
        lo, _ = _call(path, intensity=0.1, motion_speed=0.2)
        hi_rates = [hi["systems"][s]["rate"] for s in _SYSTEMS]
        lo_rates = [lo["systems"][s]["rate"] for s in _SYSTEMS]
        assert sum(hi_rates) > sum(lo_rates), \
            f"AT-5 FAIL: high intensity mean rate {sum(hi_rates)/9:.3f} not > low {sum(lo_rates)/9:.3f}"
    finally:
        os.unlink(path)
    print(f"AT-5 PASS — high-intensity mean rate > low-intensity")


# ── AT-6 ─────────────────────────────────────────────────────────────────────

def test_at6_voice_active_higher_rate():
    path = _tmp()
    try:
        on, _  = _call(path, voice_active=True,  expression_intensity=0.8, expression_pacing="quick")
        off, _ = _call(path, voice_active=False, expression_intensity=0.8, expression_pacing="quick")
        r_on  = on["systems"]["voice"]["rate"]
        r_off = off["systems"]["voice"]["rate"]
        assert r_on > r_off, f"AT-6 FAIL: voice.rate active={r_on} not > silent={r_off}"
    finally:
        os.unlink(path)
    print(f"AT-6 PASS — voice.rate active > silent")


# ── AT-7 ─────────────────────────────────────────────────────────────────────

def test_at7_intent_confidence():
    path = _tmp()
    try:
        with_intent, _    = _call(path, intent="build a game level")
        without_intent, _ = _call(path, intent="")
        c_on  = with_intent["systems"]["intent"]["confidence"]
        c_off = without_intent["systems"]["intent"]["confidence"]
        assert c_on > c_off, \
            f"AT-7 FAIL: intent.confidence with_intent={c_on} not > without={c_off}"
    finally:
        os.unlink(path)
    print(f"AT-7 PASS — intent.confidence higher when intent is set ({c_on:.3f} > {c_off:.3f})")


# ── AT-8 ─────────────────────────────────────────────────────────────────────

def test_at8_existing_fields_unchanged():
    path = _tmp()
    try:
        data, _ = _call(path)
        for s in _SYSTEMS:
            sys_data = data["systems"][s]
            for field in ("energy", "valence", "active", "label", "detail"):
                assert field in sys_data, f"AT-8 FAIL: {s} lost existing field '{field}'"
    finally:
        os.unlink(path)
    print("AT-8 PASS — existing fields (energy, valence, active, label, detail) intact")


# ── AT-9 ─────────────────────────────────────────────────────────────────────

def test_at9_publish_returns_true():
    path = _tmp()
    try:
        _, ok = _call(path)
        assert ok is True, f"AT-9 FAIL: publish() returned {ok}"
    finally:
        os.unlink(path)
    print("AT-9 PASS — publish() returns True")


# ── AT-10 ────────────────────────────────────────────────────────────────────

def test_at10_frozen_kernel():
    for path in [os.path.join(_ROOT, "runtime", "executive.py")]:
        if not os.path.exists(path):
            continue
        with open(path, "rb") as f:
            content = f.read()
        for token in (b"brain_state_writer", b"_intent_rate", b"_voice_conf"):
            assert token not in content, \
                f"AT-10 FAIL: frozen file {path} contains INT7-HEAT token '{token.decode()}'"
    prompts_dir = os.path.join(_ROOT, "prompts")
    if os.path.isdir(prompts_dir):
        for fname in os.listdir(prompts_dir):
            with open(os.path.join(prompts_dir, fname), "rb") as f:
                content = f.read()
            assert b"brain_state_writer" not in content, \
                f"AT-10 FAIL: prompts/{fname} modified — FREEZE_V1_LOCK violated"
    print("AT-10 PASS — frozen kernel untouched")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_at1_rate_present,
        test_at2_confidence_present,
        test_at3_rate_clamped,
        test_at4_confidence_clamped,
        test_at5_high_intensity_higher_rate,
        test_at6_voice_active_higher_rate,
        test_at7_intent_confidence,
        test_at8_existing_fields_unchanged,
        test_at9_publish_returns_true,
        test_at10_frozen_kernel,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
    print(f"\n{'ALL PASS' if not failed else f'{failed} FAILED'} — INT7-HEAT ({len(tests)-failed}/{len(tests)})")
    sys.exit(failed)
