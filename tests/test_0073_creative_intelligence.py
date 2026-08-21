"""
tests/test_0073_creative_intelligence.py — Vol XXVI IT-1 + disconnection check.

Card 0073 test contract (self-contained, no David):
  1. IT-1 full loop: spark → candidates → Executive selects → Ch.5 scores →
     high significance → memory. Selection MUST be non-None; sig MUST score; ref MAY populate.
  2. Cut the Executive-selection step → this test goes RED (proves the wire is the Executive).
  3. Exercised on a real drop artefact end-to-end (Output/DROP/<campaign>/00_inbox → 03_ready/).

Run: python3 tests/test_0073_creative_intelligence.py
"""
from __future__ import annotations

import sys, tempfile, shutil, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PASS = 0; FAIL = 0
def ok(name):
    global PASS; PASS += 1; print(f"  ✅ {name}")
def fail(name, reason):
    global FAIL; FAIL += 1; print(f"  ❌ {name}: {reason}")


from faculties.creative.creative_imagination import (
    diverge, evaluate, synthesise, executive_select, run_creative_loop,
)
from tools.creative_drop_runner import process_drop, scan_campaign


# ── IT-1: spark → diverge → evaluate → Executive selects → Ch.5 → memory ─────
SPARK   = "a plushie for the moon phase of the book — comfort at bedtime"
GOAL    = "kickstarter build in public — hero moment plushie"
SEEDS   = ["moon", "garden", "seed", "book"]
IDENTITY = ["elo", "moon", "garden", "presence"]
CANON    = ["elo", "book", "planet"]

result_wired = run_creative_loop(
    spark=SPARK, goal=GOAL, seeds=SEEDS,
    executive_select_fn=executive_select,
    identity_terms=IDENTITY, canon_terms=CANON,
)

try:
    assert result_wired["selected"] is not None, "Executive returned no selection on the wired path"
    assert result_wired["selected"]["candidate"]["epistemic_status"] == "imagined"
    assert result_wired["selected"]["candidate"]["metaphor"], "empty metaphor"
    assert result_wired["significance"] is not None, "Ch.5 sig missing"
    assert "overall" in result_wired["significance"], "sig has no overall"
    assert result_wired["reason"] == "selected_and_scored"
    ok(f"IT-1 wired: metaphor='{result_wired['selected']['candidate']['metaphor']}' · "
       f"sig.overall={result_wired['significance']['overall']:.3f} · "
       f"memory_ref={result_wired.get('memory_ref')}")
except AssertionError as e:
    fail("IT-1 wired", e)


# ── Disconnection check: cut Executive-selection → this test goes RED ─────────
result_cut = run_creative_loop(
    spark=SPARK, goal=GOAL, seeds=SEEDS,
    executive_select_fn=None,   # THE WIRE, CUT
    identity_terms=IDENTITY, canon_terms=CANON,
)
try:
    assert result_cut["selected"] is None, "wire cut but selection came through"
    assert result_cut["significance"] is None, "sig scored without Executive"
    assert result_cut["memory_ref"] is None, "memory routed without Executive"
    assert result_cut["reason"] == "executive_disconnected"
    assert len(result_cut["candidates"]) > 0, "no candidates generated pre-cut"
    ok("Disconnection: cut Executive-select → no selection, no sig, no memory (RED-proving)")
except AssertionError as e:
    fail("Disconnection check", e)


# Extra: prove the same IT-1 assertion goes RED under the same cut — the wire IS the selector.
try:
    # These are the IT-1 assertions applied to the cut result. All must fail.
    would_pass = (result_cut["selected"] is not None
                  and result_cut["significance"] is not None)
    assert not would_pass, "IT-1 assertions still pass with wire cut — Executive is not the wire!"
    ok("Falsifiability: IT-1 assertions FAIL when executive_select_fn=None (wire proven)")
except AssertionError as e:
    fail("Falsifiability", e)


# ── FT-1: bounded & diverse divergence (Ch.1 §1.3) ────────────────────────────
cands = diverge(GOAL, SEEDS, breadth_budget=6)
try:
    assert 0 < len(cands) <= 6
    axes = {tuple(c.spanned_axes) for c in cands}
    assert len(axes) >= 2, f"divergence not diverse: axes={axes}"
    ok(f"FT-1 bounded & diverse: {len(cands)} candidates spanning {len(axes)} axes")
except AssertionError as e:
    fail("FT-1", e)


# ── FT-3: symbolic synthesis fuses through the shared Symbol Engine (Ch.1 §1.5)
syn = synthesise("robot", "garden", "a scene for the book")
try:
    assert "metaphor" in syn and syn["metaphor"]
    assert syn["epistemic_status"] == "imagined"
    ok(f"FT-3 synthesis: '{syn['metaphor']}' (bridge={syn['bridge']})")
except AssertionError as e:
    fail("FT-3", e)


# ── FT-4: Imagined stays imagined all the way through (Ch.1 §1.1.2) ───────────
try:
    for c in cands:
        assert c.epistemic_status == "imagined", f"candidate leaked: {c}"
    if result_wired["selected"]:
        assert result_wired["selected"]["candidate"]["epistemic_status"] == "imagined"
    ok("FT-4 imagined stays imagined across diverge → converge")
except AssertionError as e:
    fail("FT-4", e)


# ── ST-4: no spark → silence (contributes nothing) ────────────────────────────
try:
    empty = diverge(GOAL, [])
    assert empty == [], "divergence produced output with no seeds"
    ok("ST-4 no spark → silence")
except AssertionError as e:
    fail("ST-4", e)


# ── FT-2: Executive-only convergence (single, from one frozen set) ────────────
scores = [evaluate(c, GOAL, identity_terms=IDENTITY, canon_terms=CANON) for c in cands]
sel = executive_select(cands, scores)
try:
    assert sel is not None, "Executive rejected all candidates"
    assert "runners_up" in sel, "runners-up must be retained (Ch.1 §1.4)"
    ok(f"FT-2 Executive selects once + retains runners_up ({len(sel['runners_up'])})")
except AssertionError as e:
    fail("FT-2", e)


# ── EXERCISED: real folder-drop artefact end-to-end ───────────────────────────
tmpdir = Path(tempfile.mkdtemp(prefix="creative_drop_it1_"))
try:
    campaign = tmpdir / "kickstarter_build_in_public"
    inbox = campaign / "00_inbox"
    inbox.mkdir(parents=True)
    drop = inbox / "hero_plushie_moon_phase.md"
    drop.write_text(
        "goal: kickstarter hero — plushie of the moon phase\n"
        "seeds: moon, garden, book, seed\n"
        "\n"
        "David dropped this in the inbox to spark hero art for the campaign.\n",
        encoding="utf-8",
    )

    results = scan_campaign(campaign)
    assert len(results) == 1, f"expected 1 drop processed, got {len(results)}"
    r = results[0]
    assert r["selected"] is not None, "Executive returned nothing on the real drop"
    ready = campaign / "03_ready"
    ready_files = list(ready.glob("*.md"))
    assert len(ready_files) == 1, f"expected 1 file in 03_ready/, got {len(ready_files)}"
    body = ready_files[0].read_text(encoding="utf-8")
    assert "epistemic_status: imagined" in body, "observable missing epistemic tag"
    assert "Metaphor (Executive-selected)" in body, "observable missing selected metaphor section"
    print(f"    ▸ observable: {ready_files[0]}")
    print(f"    ▸ metaphor:   {r['selected']['candidate']['metaphor']}")
    ok("Exercised: real drop → 03_ready/ observable exists with Executive-selected metaphor")
finally:
    shutil.rmtree(tmpdir, ignore_errors=True)


print(f"\nResult: {PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
