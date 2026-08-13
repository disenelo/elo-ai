"""
tests/test_wo110_epistemic_tiers.py — WO-110: epistemic tiers beyond the body.

AT-110-1: tier_fact() returns OBSERVED for sensor facts confirmed this turn
AT-110-2: tier_fact() returns REMEMBERED for vault/lesson facts
AT-110-3: tier_fact() returns UNKNOWN when value is absent
AT-110-4: tier_fact() returns INFERRED for inferred-source facts
AT-110-5: tier changes when source changes (computed, not constant)
AT-110-6: nearby_tier is UNKNOWN when nearby_surfaces empty (was hardcoded "inferred")
AT-110-7: compile() includes non-body epistemic fields (recent_behaviour, lessons)
AT-109-R8: vault_layer.lookup() returns experience_id, event, outcome in each hit
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ── AT-110-1..5: tier_fact() general purpose ─────────────────────────────────

def test_tier_fact_observed_sensor():
    from runtime.the_moment import tier_fact
    assert tier_fact("desktop", source="sensor", confirmed=True) == "observed"


def test_tier_fact_observed_tool():
    from runtime.the_moment import tier_fact
    assert tier_fact("result_data", source="tool") == "observed"


def test_tier_fact_remembered_vault():
    from runtime.the_moment import tier_fact
    assert tier_fact("some vault entry", source="vault") == "remembered"


def test_tier_fact_remembered_lesson():
    from runtime.the_moment import tier_fact
    assert tier_fact({"lesson": "test"}, source="lesson") == "remembered"


def test_tier_fact_unknown_when_absent():
    from runtime.the_moment import tier_fact
    assert tier_fact(None,   source="sensor") == "unknown"
    assert tier_fact("",     source="vault")  == "unknown"
    assert tier_fact([],     source="tool")   == "unknown"
    assert tier_fact({},     source="lesson") == "unknown"


def test_tier_fact_inferred():
    from runtime.the_moment import tier_fact
    assert tier_fact("nearby surfaces", source="inferred") == "inferred"


def test_tier_changes_when_source_changes():
    from runtime.the_moment import tier_fact
    # Same value — different source → different tier (proves it's computed, not constant)
    t_sensor = tier_fact("Chrome", source="sensor", confirmed=True)
    t_vault  = tier_fact("Chrome", source="vault")
    t_absent = tier_fact(None,     source="sensor")
    assert t_sensor != t_vault,  f"sensor and vault should differ: {t_sensor} vs {t_vault}"
    assert t_sensor != t_absent, f"present and absent should differ: {t_sensor} vs {t_absent}"
    assert t_vault  != t_absent, f"remembered and unknown should differ: {t_vault} vs {t_absent}"


# ── AT-110-6: nearby_tier is UNKNOWN when no nearby surfaces ─────────────────

def test_nearby_tier_unknown_when_empty():
    from runtime.the_moment import compile
    from unittest.mock import MagicMock
    state = MagicMock()
    state.embodiment = "desktop"
    state.pose = "perched"
    state.surface = "Chrome"
    state.location = ""
    state.balance = "stable"
    state.size = {"height_cm": 30, "reach_cm": 20, "jump_cm": 40}
    state.available_actions = []
    state.current_action = "idle"
    state.locomotion_faculty_health = "ok"
    state.nearby_surfaces = []   # empty — tier must be unknown, not "inferred"
    state.mood = 0.5
    state.curiosity = 0.5
    state.goal = ""
    state.last_updated = 0.0
    state.recent_behavior = {}
    m = compile(state)
    assert m["nearby_tier"] == "unknown", (
        f"nearby_tier should be 'unknown' when nearby_surfaces is empty, got: {m['nearby_tier']}"
    )


def test_nearby_tier_inferred_when_populated():
    from runtime.the_moment import compile
    from unittest.mock import MagicMock
    state = MagicMock()
    state.embodiment = "desktop"
    state.pose = "perched"
    state.surface = "Chrome"
    state.location = ""
    state.balance = "stable"
    state.size = {"height_cm": 30, "reach_cm": 20, "jump_cm": 40}
    state.available_actions = []
    state.current_action = "idle"
    state.locomotion_faculty_health = "ok"
    state.nearby_surfaces = ["Finder", "Terminal"]
    state.mood = 0.5
    state.curiosity = 0.5
    state.goal = ""
    state.last_updated = 0.0
    state.recent_behavior = {}
    m = compile(state)
    assert m["nearby_tier"] == "inferred", (
        f"nearby_tier should be 'inferred' when surfaces present, got: {m['nearby_tier']}"
    )


# ── AT-110-7: compile() includes non-body epistemic fields ───────────────────

def test_compile_includes_non_body_fields():
    from runtime.the_moment import compile
    from unittest.mock import MagicMock
    state = MagicMock()
    state.embodiment = "desktop"
    state.pose = "perched"
    state.surface = "Terminal"
    state.location = ""
    state.balance = "stable"
    state.size = {"height_cm": 30, "reach_cm": 20, "jump_cm": 40}
    state.available_actions = ["sit"]
    state.current_action = "idle"
    state.locomotion_faculty_health = "ok"
    state.nearby_surfaces = []
    state.mood = 0.7
    state.curiosity = 0.6
    state.goal = "help"
    state.last_updated = 0.0
    state.recent_behavior = {"sit": 2, "move": 1}
    m = compile(state)
    assert "recent_behaviour" in m, "compile() missing recent_behaviour field (WO-110)"
    assert "recent_behaviour_tier" in m, "compile() missing recent_behaviour_tier field (WO-110)"
    assert "lessons" in m, "compile() missing lessons field (WO-110)"
    assert "lessons_tier" in m, "compile() missing lessons_tier field (WO-110)"
    # recent_behaviour should be OBSERVED (sensor, confirmed) since it's non-empty
    assert m["recent_behaviour_tier"] == "observed", (
        f"recent_behaviour_tier should be 'observed' when non-empty, got: {m['recent_behaviour_tier']}"
    )


# ── AT-109-R8: vault_layer.lookup() returns provenance fields ────────────────

def test_lookup_returns_experience_id_and_event(tmp_path, monkeypatch):
    import memory.vault_layer as vl

    mem_dir  = tmp_path / "09 Memory"
    sum_dir  = mem_dir / "summary"
    deep_dir = mem_dir / "deep"
    sum_dir.mkdir(parents=True)
    deep_dir.mkdir(parents=True)

    spot_file = mem_dir / "SPOT_CODES.md"
    spot_file.write_text(
        "---\ntype: memory-index\n---\n\n"
        "| Spot | Bits | Summary | Date |\n"
        "|------|------|---------|------|\n"
        "| `EO·RC·2608·1` | `EO-RC-26` | test recall provenance entry | 2026-08-13 |\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(vl, "_MEM_DIR",   str(mem_dir))
    monkeypatch.setattr(vl, "_SUM_DIR",   str(sum_dir))
    monkeypatch.setattr(vl, "_DEEP_DIR",  str(deep_dir))
    monkeypatch.setattr(vl, "_SPOT_FILE", str(spot_file))

    results = vl.lookup("test recall provenance")
    assert results, "lookup() returned no hits — test data not matched"
    hit = results[0]
    assert "experience_id" in hit, f"lookup() hit missing 'experience_id': {list(hit.keys())}"
    assert "event" in hit,         f"lookup() hit missing 'event': {list(hit.keys())}"
    assert "outcome" in hit,       f"lookup() hit missing 'outcome': {list(hit.keys())}"
    assert "confidence" in hit,    f"lookup() hit missing 'confidence'"
    assert "source" in hit,        f"lookup() hit missing 'source'"
    assert "timestamp" in hit,     f"lookup() hit missing 'timestamp'"
    # experience_id should be the spot code
    assert hit["experience_id"] == hit["spot"], (
        f"experience_id should match spot: {hit['experience_id']} vs {hit['spot']}"
    )
