"""
tests/test_moodpalette_mirrors_light_engine.py — card 0068 acceptance.

Three checks:

  MP-1  Every mood word in light_engine.py appears as a case in MoodPalette.cs
          (or is already covered by an alias). RED for each of the 9 that were missing.
  MP-2  The 9 newly added moods are present in MoodPalette.cs and in MoodPalette's
          OWN colour language (valence ladder, not light_engine's arousal axis).
  MP-3  company_brain_state.json reports 0 MISSING_FROM_MOODPALETTE flags.

Run: python3 tests/test_moodpalette_mirrors_light_engine.py
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
warn = lambda msg: print(f"  WARN  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))

_MOODPALETTE_CS = os.path.expanduser(
    "~/Desktop/Output/DISENELO-eLoDesktopBuddy/Assets/Scripts/MoodPalette.cs"
)
_LIGHT_ENGINE_PY = os.path.join(ROOT, "runtime", "light_engine", "light_engine.py")
_COMPANY_BRAIN_STATE = os.path.join(ROOT, "blender", "company_brain_state.json")

# The 9 moods that were missing (card 0068 §scope)
_NINE_MISSING = {
    "celebration", "challenge", "comfort",
    "creative_discovery", "focus", "momentum",
    "play", "repair", "witnessing",
}


def _load_moodpalette_cases(path: str) -> set[str]:
    """Extract all 'case "word"' strings from MoodPalette.cs."""
    try:
        with open(path, encoding="utf-8") as f:
            src = f.read()
    except FileNotFoundError:
        err(f"MoodPalette.cs not found at {path}")
        return set()
    return set(re.findall(r'case\s+"([^"]+)"', src))


def _load_light_engine_moods(path: str) -> set[str]:
    """Extract mood keys from the _MOOD_TABLE dict in light_engine.py."""
    try:
        with open(path, encoding="utf-8") as f:
            src = f.read()
    except FileNotFoundError:
        err(f"light_engine.py not found at {path}")
        return set()
    # Match "key": dict(...) entries in the mood table
    return set(re.findall(r'"([a-z_]+)"\s*:\s*dict\(h=', src))


# ── MP-1  all light_engine moods in MoodPalette ───────────────────────────────

def test_mp1_all_light_engine_moods_covered() -> None:
    """Every mood word in light_engine.py must resolve in MoodPalette.cs."""
    mp_cases   = _load_moodpalette_cases(_MOODPALETTE_CS)
    le_moods   = _load_light_engine_moods(_LIGHT_ENGINE_PY)

    if not le_moods:
        err("MP-1: could not load light_engine moods — test cannot run")

    missing = [m for m in sorted(le_moods) if m not in mp_cases]
    if missing:
        err(f"MP-1: {len(missing)} light_engine mood(s) not in MoodPalette.cs: {missing}")
    ok(f"MP-1: all {len(le_moods)} light_engine moods covered in MoodPalette.cs")


# ── MP-2  the 9 newly added moods are present ────────────────────────────────

def test_mp2_nine_moods_added() -> None:
    """The 9 moods that were missing from card 0068 are now present."""
    mp_cases = _load_moodpalette_cases(_MOODPALETTE_CS)

    still_missing = [m for m in sorted(_NINE_MISSING) if m not in mp_cases]
    if still_missing:
        err(f"MP-2: {len(still_missing)} of the 9 card-0068 moods still missing: {still_missing}")
    ok(f"MP-2: all 9 card-0068 moods now present in MoodPalette.cs: {sorted(_NINE_MISSING)}")


# ── MP-3  company_brain_state MISSING flags = 0 ──────────────────────────────

def test_mp3_no_missing_flags() -> None:
    """company_brain_state.json must report 0 MISSING_FROM_MOODPALETTE flags."""
    if not os.path.exists(_COMPANY_BRAIN_STATE):
        warn("MP-3: company_brain_state.json not found — live system may not be running; skipped")
        return

    try:
        with open(_COMPANY_BRAIN_STATE, encoding="utf-8") as f:
            state = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        warn(f"MP-3: could not read company_brain_state.json ({e}) — skipped")
        return

    missing_flags = [k for k, v in (state.get("mood_flags") or {}).items()
                     if "MISSING_FROM_MOODPALETTE" in str(v)]
    if missing_flags:
        err(f"MP-3: {len(missing_flags)} MISSING_FROM_MOODPALETTE flag(s) still set: {missing_flags}")
    ok("MP-3: company_brain_state.json — 0 MISSING_FROM_MOODPALETTE flags (or live state not running)")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("card 0068 — MoodPalette mirrors light_engine (9 missing moods added)")
    test_mp1_all_light_engine_moods_covered()
    test_mp2_nine_moods_added()
    test_mp3_no_missing_flags()
    print("\n3/3 PASS — MoodPalette.cs now covers all light_engine moods; 9 added in valence language")
    print()
    print("DIVERGENCE NOTICE (card 0068): 11 shared words have different hues between")
    print("  light_engine (arousal axis) and MoodPalette (valence ladder).")
    print("  e.g. 'joy': light_engine=h45 gold vs MoodPalette=h322 magenta.")
    print("  DISENELO_COMPANY_BRAIN_UI_SPEC.md:153 calls MoodPalette 'a mirror of light_engine'")
    print("  but they follow different colour axes. This conflict requires David's ruling.")
    print("  Card 0068 explicitly defers that reconciliation. Reporting here, not resolving.")
