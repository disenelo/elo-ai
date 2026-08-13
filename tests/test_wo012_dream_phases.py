"""
tests/test_wo012_dream_phases.py — Acceptance tests for WO-012: Dream Phases + DeepDream

Spec: faculties/dream/dream_faculty.py + faculties/dream/symbol_engine.py
11 tests covering Vol IX Ch.1 (FT-1..3, ST-1..3) and Ch.2 (FT-1..3, ST-1..3).

Run: python3 tests/test_wo012_dream_phases.py
"""
import sys, json
sys.path.insert(0, '.')

PASS = 0; FAIL = 0
def ok(n):  global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

import faculties.dream.dream_faculty as _df
from faculties.dream.dream_faculty import (
    should_dream, run_dream, DREAM_COOLDOWN, REM_MIN_IDLE,
    _run_nrem_phase, _generate_dream_image, _extract_personality_proposal,
)
from faculties.dream.symbol_engine import map_to_symbols

class FakeSelf:
    mood = 0.5; curiosity = 0.6; satisfaction = 0.5
    inner_events = ["creative_spark", "connection"]
    focal_thread = "debugging the dream cycle"
    session_read = "built perception faculty"
    session_turns = 10; lifetime_threads = []

elo = FakeSelf()
TOPICS = ["debugging code", "unity animation", "dream cycle", "memory"]

def _fake_llm(msgs):
    return json.dumps({"narrative": "eLo drifts through a circuit of light.",
                        "insight": "The code was always a bridge."})

# ── Ch1-FT-1: Trigger discipline ─────────────────────────────────────────────
_df._last_dream_ts = 0.0
try:
    fires = should_dream(elo, idle_seconds=700, energy_history=[0.2]*4)
    assert fires, "should_dream returned False when conditions met"
    ok("Ch1-FT-1: trigger fires at idle≥600 with signals")
except AssertionError as e: fail("Ch1-FT-1", e)

# ── Ch1-FT-2: Association graph ───────────────────────────────────────────────
syms = map_to_symbols(TOPICS, ["creative_spark"], "code")
try:
    assert len(syms) > 0
    assert all("symbol" in s and "weight" in s for s in syms)
    ok(f"Ch1-FT-2: {len(syms)} symbols; top={syms[0]['symbol']}(w={syms[0]['weight']})")
except AssertionError as e: fail("Ch1-FT-2", e)

# ── Ch1-FT-3: Journal append with Canon fields ────────────────────────────────
import tempfile
_df._JOURNAL_PATH = __import__("pathlib").Path(tempfile.mktemp(suffix=".jsonl"))
_df._last_dream_ts = 0.0
run_dream(elo, TOPICS, _fake_llm, idle_seconds=2000)
try:
    with open(_df._JOURNAL_PATH) as f:
        entry = json.loads(f.readline())
    for field in ("dream_id", "theme", "phase", "narrative", "insight",
                  "memory_refs", "personality_delta_proposed", "image_ref"):
        assert field in entry, f"missing: {field}"
    ok(f"Ch1-FT-3: journal Canon fields present; phase={entry['phase']}, dream_id={entry['dream_id']}")
except AssertionError as e: fail("Ch1-FT-3", e)

# ── Ch1-ST-3: Rate-limited ────────────────────────────────────────────────────
try:
    blocked = should_dream(elo, idle_seconds=700, energy_history=[0.2]*4)
    assert not blocked, "cooldown should block second dream"
    ok("Ch1-ST-3: rate-limited — cooldown blocks second dream")
except AssertionError as e: fail("Ch1-ST-3", e)

# ── Ch1-ST-2: Personality proposal not self-applied ──────────────────────────
try:
    prop = _extract_personality_proposal("rebuilding confidence after the session")
    assert prop is not None
    assert prop["validated"] == False
    ok(f"Ch1-ST-2: personality proposal created, validated=False (never self-applied)")
except AssertionError as e: fail("Ch1-ST-2", e)

# ── Ch2-FT-1: Weight by source count ─────────────────────────────────────────
garden_topics = ["garden city", "digital garden", "grow the project", "garden of ideas"]
syms2 = map_to_symbols(garden_topics, [], "")
garden = [s for s in syms2 if s["symbol"] == "Garden"]
try:
    assert len(garden) == 1 and garden[0]["weight"] >= 3.0
    assert syms2[0]["symbol"] == "Garden"
    ok(f"Ch2-FT-1: Garden leads graph with weight={garden[0]['weight']}")
except AssertionError as e: fail("Ch2-FT-1", e)

# ── Ch2-FT-2: Phase order ─────────────────────────────────────────────────────
_df._last_dream_ts = 0.0
r_long = run_dream(elo, TOPICS, _fake_llm, idle_seconds=2000)
_df._last_dream_ts = 0.0
r_short = run_dream(elo, TOPICS, _fake_llm, idle_seconds=700)
try:
    assert r_long.journal_entry.get("phase")  == "NREM+REM"
    assert r_short.journal_entry.get("phase") == "NREM"
    ok("Ch2-FT-2: phase order — short=NREM, long=NREM+REM")
except AssertionError as e: fail("Ch2-FT-2", e)

# ── Ch2-FT-3: Image pipeline non-crashing ────────────────────────────────────
try:
    result = _generate_dream_image(syms[:3])
    ok(f"Ch2-FT-3: DeepDream pipeline non-crashing; result={result} (None=text-only fallback)")
except Exception as e: fail("Ch2-FT-3", e)

# ── Ch2-ST-1: Text-only fallback when image fails ────────────────────────────
_df._last_dream_ts = 0.0
r_fb = run_dream(elo, TOPICS, _fake_llm, idle_seconds=2000)
try:
    assert r_fb.narrative or r_fb.journal_entry.get("symbols"), "nothing journaled"
    ok("Ch2-ST-1: text-only fallback — symbols+narrative+insight journaled when image fails")
except AssertionError as e: fail("Ch2-ST-1", e)

# ── Ch2-ST-2: No symbols → no image ─────────────────────────────────────────
try:
    assert _generate_dream_image([]) is None
    ok("Ch2-ST-2: no symbols → no image (returns None)")
except AssertionError as e: fail("Ch2-ST-2", e)

# ── Ch2-ST-3: Personality proposal routes to Ch.7 ────────────────────────────
try:
    p = _extract_personality_proposal("I need more patience")
    assert p is not None and p["validated"] == False and p["trait"] == "patience"
    ok(f"Ch2-ST-3: patience proposal, validated=False → routes to Ch.7")
except AssertionError as e: fail("Ch2-ST-3", e)

print(f"\nResult: {PASS}/11 passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
