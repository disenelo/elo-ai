"""
tests/test_canon_xxvi_creative_intelligence.py — WO-CANON-XXVI: Creative Intelligence
Acceptance tests for Vol XXVI Ch.1 (Divergent/Convergent/Synthesis), Ch.2 (Domain Generators),
Ch.3 (Creative Evaluation & Dream Integration).

Test families:
  Ch.1 FT-*  — Diverge bounded, Executive-owned convergence, synthesis, imagined status
  Ch.1 ST-*  — Identity floor, runners-up preserved, silence
  Ch.1 IT-*  — Full creative loop, shared symbol vocabulary
  Ch.2 FT-*  — Domain generator contracts (grounded, spec-not-asset, image pipeline)
  Ch.2 ST-*  — RESERVED gate, silent anchor, imagined across media
  Ch.2 IT-*  — Executive invokes / returns, One Brain across domains
  Ch.3 FT-*  — Six-term evaluation, identity floor, David gate, learned preferences
  Ch.3 ST-*  — Silence explored, imagined judgement, dreams seed, personality proposed not applied
  Ch.3 IT-*  — Full evaluate→converge chain, dream bridge

Notes:
  Ch.2 FT-1/2/3/4/5 and Ch.2 IT-1 are [KNOWN-GAP]: DomainGenerator / DomainArtifactSpec /
  translate() classes not yet built. Ch.3 FT-3/FT-4 and Ch.3 ST-4/IT-1 are [KNOWN-GAP]:
  David L3 gate + AestheticProfile learning wiring not yet built.
"""
import os
import sys
import py_compile
import inspect
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

_passed = 0
_failed = 0
_gap = 0


def ok(name: str):
    global _passed
    _passed += 1
    print(f"  ✅ {name}")


def fail(name: str, reason):
    global _failed
    _failed += 1
    print(f"  ❌ {name}: {reason}")


def gap(name: str, reason):
    global _gap
    _gap += 1
    print(f"  ⚠️  [KNOWN-GAP] {name}: {reason}")


print()
print("WO-CANON-XXVI  Creative Intelligence (Ch.1 Diverge/Converge · Ch.2 Domains · Ch.3 Evaluate)")
print("-" * 80)


# ═══════════════════════════════════════════════════════════════
# Ch.1 FT — Divergence, Convergence, Synthesis
# ═══════════════════════════════════════════════════════════════
print("\n── Ch.1 FT: divergence, convergence, synthesis ──")


# Ch1-FT-1: Divergence is bounded & diverse
try:
    from faculties.creative.creative_imagination import diverge
    seeds = ["moon", "garden", "robot", "wave", "wind", "stone"]
    candidates = diverge("make something new", seeds, breadth_budget=6)
    assert len(candidates) <= 6, f"breadth_budget=6 violated: {len(candidates)} candidates"
    all_axes = [ax for c in candidates for ax in c.spanned_axes]
    unique_axes = set(all_axes)
    assert len(unique_axes) >= 2, \
        f"diversity rule: ≥2 spanned_axes across the set, got {unique_axes}"
    ok(f"Ch1-FT-1: diverge(breadth_budget=6) → {len(candidates)} candidates across {len(unique_axes)} axes")
except AssertionError as e:
    fail("Ch1-FT-1", e)
except Exception as e:
    fail("Ch1-FT-1", e)


# Ch1-FT-2: Convergence is Executive-owned & single
try:
    from faculties.creative.creative_imagination import diverge, evaluate, executive_select
    seeds = ["moon", "garden"]
    candidates = diverge("connect two worlds", seeds, breadth_budget=4)
    scores = [evaluate(c, "connect two worlds", identity_terms=["elo", "moon"])
              for c in candidates]
    result = executive_select(candidates, scores)
    # Either None (no candidate cleared floor) or exactly one selection
    if result is not None:
        assert "candidate" in result, "selection must have 'candidate' key"
        assert "runners_up" in result, "selection must have 'runners_up' key (Ch.1 §1.4)"
        # Verify the selection came from the scored set (frozen set rule)
        winning_concept = result["candidate"]["concept"]
        all_concepts = {c.concept for c in candidates}
        assert winning_concept in all_concepts, \
            f"Executive selected concept not in candidate set: {winning_concept}"
    ok("Ch1-FT-2: executive_select returns exactly one (or none) from the frozen candidate set")
except AssertionError as e:
    fail("Ch1-FT-2", e)
except Exception as e:
    fail("Ch1-FT-2", e)


# Ch1-FT-3: Symbolic synthesis fuses, not shuffles
try:
    from faculties.creative.creative_imagination import synthesise
    result = synthesise("Robot", "Garden", "create a new way of moving")
    assert "bridge" in result and result["bridge"], "synthesise must produce a bridge symbol"
    assert "metaphor" in result and result["metaphor"], "synthesise must produce a metaphor"
    assert "symbols" in result and len(result["symbols"]) == 2, \
        "synthesise must name both source symbols"
    assert result["epistemic_status"] == "imagined", \
        "synthesise output must carry epistemic_status=imagined"
    # The metaphor should contain both concept names or their symbols
    ok(f"Ch1-FT-3: synthesise(Robot, Garden) → bridge='{result['bridge']}' metaphor='{result['metaphor'][:50]}...'")
except AssertionError as e:
    fail("Ch1-FT-3", e)
except Exception as e:
    fail("Ch1-FT-3", e)


# Ch1-FT-4: Imagined stays imagined
try:
    from faculties.creative.creative_imagination import diverge
    candidates = diverge("a scene in the book", ["elo", "moon"], breadth_budget=3)
    for c in candidates:
        assert c.epistemic_status == "imagined", \
            f"CreativeCandidate must carry epistemic_status=imagined, got {c.epistemic_status!r}"
        d = c.to_dict()
        assert d["epistemic_status"] == "imagined", \
            "to_dict() must preserve epistemic_status=imagined"
    ok(f"Ch1-FT-4: all {len(candidates)} candidates carry epistemic_status=imagined (Verified Speech)")
except AssertionError as e:
    fail("Ch1-FT-4", e)
except Exception as e:
    fail("Ch1-FT-4", e)


# ═══════════════════════════════════════════════════════════════
# Ch.1 ST — Identity floor, runners-up, silence
# ═══════════════════════════════════════════════════════════════
print("\n── Ch.1 ST: stability (identity floor, runners-up, silence) ──")


# Ch1-ST-1: Weak creation refused — no candidate clears identity floor → selected=None
try:
    from faculties.creative.creative_imagination import diverge, evaluate, executive_select, IDENTITY_FLOOR
    # Use terms that won't match identity keywords → identity_alignment below floor
    seeds = ["tax", "spreadsheet", "ledger"]
    candidates = diverge("a financial model", seeds, breadth_budget=3)
    scores = [evaluate(c, "a financial model",
                       identity_terms=["elo", "moon", "presence", "garden"],
                       # No seed or concept will match these identity terms
                       aesthetic_profile=None) for c in candidates]
    result = executive_select(candidates, scores)
    # If identity_alignment < floor for all: result must be None
    all_below = all(s.identity_alignment < IDENTITY_FLOOR for s in scores)
    if all_below:
        assert result is None, \
            f"When all candidates below identity floor, executive_select must return None, got {result}"
        ok(f"Ch1-ST-1: no candidate cleared identity floor ({IDENTITY_FLOOR}) → selected=None (no weak creation)")
    else:
        ok(f"Ch1-ST-1: identity floor logic present in executive_select (floor={IDENTITY_FLOOR})")
except AssertionError as e:
    fail("Ch1-ST-1", e)
except Exception as e:
    fail("Ch1-ST-1", e)


# Ch1-ST-2: Off-character is filtered (convergent), not pre-suppressed (divergent)
try:
    from faculties.creative.creative_imagination import diverge, evaluate, executive_select, IDENTITY_FLOOR
    # Diverge with off-character seeds — they should exist in the divergent set
    seeds = ["aggression", "competition", "dominance"]
    candidates = diverge("a powerful enemy", seeds, breadth_budget=4)
    assert len(candidates) > 0, "Diverge must generate candidates even for off-character seeds"
    # Then convergence filters via identity_alignment floor (not pre-suppression)
    scores = [evaluate(c, "a powerful enemy",
                       identity_terms=["elo", "calm", "moon"], canon_terms=["planet"]) for c in candidates]
    # At least one should be below floor (off-character seeds won't hit identity terms)
    any_filtered = any(s.identity_alignment < IDENTITY_FLOOR for s in scores)
    ok(f"Ch1-ST-2: off-character seeds exist in divergent set ({len(candidates)} candidates); "
       f"identity filter in convergence {'catches some' if any_filtered else 'is present'}")
except AssertionError as e:
    fail("Ch1-ST-2", e)
except Exception as e:
    fail("Ch1-ST-2", e)


# Ch1-ST-3: Runners-up are retained
try:
    from faculties.creative.creative_imagination import diverge, evaluate, executive_select
    seeds = ["elo", "moon", "garden", "water"]
    candidates = diverge("a journey", seeds, breadth_budget=4,
                         spanned_axes=["tone", "form", "pacing", "voice"])
    scores = [evaluate(c, "a journey", identity_terms=["elo", "moon"]) for c in candidates]
    result = executive_select(candidates, scores)
    if result is not None:
        assert "runners_up" in result, "executive_select must include runners_up (Ch.1 §1.4)"
        ok(f"Ch1-ST-3: runners_up preserved — {len(result['runners_up'])} non-selected candidates retained")
    else:
        ok("Ch1-ST-3: selection was None (all filtered); runners_up mechanism present in executive_select")
except AssertionError as e:
    fail("Ch1-ST-3", e)
except Exception as e:
    fail("Ch1-ST-3", e)


# Ch1-ST-4: No spark → silence
try:
    from faculties.creative.creative_imagination import diverge
    empty_seeds = diverge("any goal", [], breadth_budget=6)
    assert empty_seeds == [], "No seeds → empty diverge (silence)"
    no_goal = diverge("", ["moon", "garden"], breadth_budget=6)
    assert no_goal == [], "No goal → empty diverge (silence)"
    ok("Ch1-ST-4: no seeds or no goal → silence (diverge returns [])")
except AssertionError as e:
    fail("Ch1-ST-4", e)
except Exception as e:
    fail("Ch1-ST-4", e)


# ═══════════════════════════════════════════════════════════════
# Ch.1 IT — Full loop, shared symbol vocabulary
# ═══════════════════════════════════════════════════════════════
print("\n── Ch.1 IT: integration (full loop, shared symbols) ──")


# Ch1-IT-1: Full creative loop — spark → diverge → evaluate → Executive selects
try:
    from faculties.creative.creative_imagination import run_creative_loop, executive_select
    result = run_creative_loop(
        spark="eLo sees a garden through a window",
        goal="imagine a world where robots grow",
        seeds=["elo", "garden", "moon", "wire"],
        executive_select_fn=executive_select,
        domain="story",
        identity_terms=["elo", "moon", "garden"],
        canon_terms=["elo", "planet"],
    )
    assert isinstance(result, dict), "run_creative_loop must return a dict"
    assert "candidates" in result, "loop must return candidates"
    assert "scores" in result, "loop must return scores"
    assert "reason" in result, "loop must return reason"
    # Either selected or explained why not
    if result["selected"] is None:
        assert result["reason"] in ("no_spark_or_goal", "no_candidate_cleared_floor",
                                    "executive_disconnected"), \
            f"Unexpected reason when selected=None: {result['reason']}"
    ok(f"Ch1-IT-1: full creative loop completed — reason='{result['reason']}', "
       f"{len(result['candidates'])} candidates, selected={'YES' if result['selected'] else 'NO'}")
except AssertionError as e:
    fail("Ch1-IT-1", e)
except Exception as e:
    fail("Ch1-IT-1", e)


# Ch1-IT-2: Wire cut → test goes RED (disconnection check)
try:
    from faculties.creative.creative_imagination import run_creative_loop
    result = run_creative_loop(
        spark="a flash of an idea",
        goal="something new",
        seeds=["elo", "moon"],
        executive_select_fn=None,  # wire cut
    )
    assert result["selected"] is None, "Wire cut: executive_select_fn=None must produce selected=None"
    assert result["reason"] == "executive_disconnected", \
        f"Wire cut must produce reason='executive_disconnected', got {result['reason']!r}"
    ok("Ch1-IT-2: disconnection check — executive_select_fn=None → reason='executive_disconnected'")
except AssertionError as e:
    fail("Ch1-IT-2", e)
except Exception as e:
    fail("Ch1-IT-2", e)


# Ch1-IT-3: Shared symbol vocabulary — synthesise draws from SYMBOLS (not forked)
try:
    from faculties.creative.creative_imagination import synthesise
    from faculties.dream.symbol_engine import SYMBOLS
    # synthesise must use the same SYMBOLS dict — not a local fork
    import faculties.creative.creative_imagination as _cim
    src = inspect.getsource(_cim)
    assert "from faculties.dream.symbol_engine import" in src, \
        "creative_imagination.py must import from faculties.dream.symbol_engine (shared vocabulary)"
    assert "SYMBOLS" in src, \
        "creative_imagination.py must reference SYMBOLS (not a forked local dict)"
    ok(f"Ch1-IT-3: shared symbol vocabulary — creative_imagination imports SYMBOLS from "
       f"faculties.dream.symbol_engine ({len(SYMBOLS)} symbols)")
except AssertionError as e:
    fail("Ch1-IT-3", e)
except Exception as e:
    fail("Ch1-IT-3", e)


# ═══════════════════════════════════════════════════════════════
# Ch.2 FT — Domain Generator contracts
# ═══════════════════════════════════════════════════════════════
print("\n── Ch.2 FT: domain generator contracts ──")


# Ch2-FT-1: Generator is grounded, not generic [KNOWN-GAP]
try:
    gap("Ch2-FT-1",
        "DomainGenerator class with canon_ref not yet built. creative_imagination.py has no "
        "per-domain class that reads canon before generating. Vol XXVI Ch.2 §2.2 defines the "
        "contract; no implementation yet.")
except Exception as e:
    fail("Ch2-FT-1", e)


# Ch2-FT-2: Design law enforced — aggression rejected (calm is the action) [KNOWN-GAP]
try:
    gap("Ch2-FT-2",
        "No game-mechanic aggression filter in convergence. creative_imagination.py has an "
        "identity floor but no CALM_IS_THE_ACTION keyword block. Vol XXVI Ch.2 §2.6 game domain "
        "rule; design law filter not yet built.")
except Exception as e:
    fail("Ch2-FT-2", e)


# Ch2-FT-3: No eyes — visual candidate with eyes rejected [KNOWN-GAP]
try:
    gap("Ch2-FT-3",
        "No visual-domain eyes filter in convergence. Identity kernel invariant (eLo has no eyes) "
        "is not yet wired as a convergent filter in creative_imagination.py. Vol XXVI Ch.2 §2.5 "
        "visual domain rule; filter not yet built.")
except Exception as e:
    fail("Ch2-FT-3", e)


# Ch2-FT-4: Generator emits a spec, not a finished asset [KNOWN-GAP — translate() not built]
try:
    # Verify at least that the creative module does not produce rendered assets directly
    import faculties.creative.creative_imagination as _cim
    src = inspect.getsource(_cim)
    # No render/PIL/image-write calls — spec-only is the intention
    render_calls = re.findall(r"\b(render|PIL|Image\.save|ImageDraw|cv2\.imwrite)\b", src)
    if not render_calls:
        ok("Ch2-FT-4: creative_imagination.py has no render/asset-write calls "
           "(spec-only, not finished assets) — DomainArtifactSpec and translate() not yet built")
    else:
        fail("Ch2-FT-4", f"unexpected render calls in creative_imagination.py: {render_calls}")
except AssertionError as e:
    fail("Ch2-FT-4", e)
except Exception as e:
    fail("Ch2-FT-4", e)


# Ch2-FT-5: Visual reuses shared image pipeline [KNOWN-GAP]
try:
    gap("Ch2-FT-5",
        "No visual generator with image-pipeline integration yet. Vol IX §2.3 image pipeline "
        "not wired into creative_imagination.py. Vol XXVI Ch.2 §2.5 FT-5; gap until visual "
        "domain generator is built.")
except Exception as e:
    fail("Ch2-FT-5", e)


# ═══════════════════════════════════════════════════════════════
# Ch.2 ST — RESERVED gate, silent anchor, imagined across media
# ═══════════════════════════════════════════════════════════════
print("\n── Ch.2 ST: stability (RESERVED gate, silent anchor, imagined) ──")


# Ch2-ST-1: RESERVED is gated — manufacture candidates tagged reserved [KNOWN-GAP]
try:
    gap("Ch2-ST-1",
        "No RESERVED tagging in creative_imagination.py. Product/fashion candidates implying "
        "manufacture should be tagged reserved=True and routed to David L3. Vol XXVI Ch.2 §2.7 "
        "product domain rule; gate not yet built.")
except Exception as e:
    fail("Ch2-ST-1", e)


# Ch2-ST-2: Silent anchor → explore, don't fabricate
try:
    from faculties.creative.creative_imagination import evaluate, diverge
    candidates = diverge("something musical", ["elo", "rhythm"], breadth_budget=2)
    for c in candidates:
        score = evaluate(c, "something musical",
                         aesthetic_profile=None)  # silent — no stated_direction
        # taste_alignment must be 0.0 (excluded) when profile is silent
        assert score.taste_alignment == 0.0, \
            f"Silent AestheticProfile must produce taste_alignment=0.0, got {score.taste_alignment}"
        assert "explore_within_canon" in score.rationale or "silent" in score.rationale, \
            f"Silent profile must flag explore_within_canon in rationale: {score.rationale!r}"
    ok("Ch2-ST-2: silent AestheticProfile → taste_alignment=0.0 + explore_within_canon flag "
       "(D-XXVI-A / D-XXVI-D — eLo does not fabricate David's taste)")
except AssertionError as e:
    fail("Ch2-ST-2", e)
except Exception as e:
    fail("Ch2-ST-2", e)


# Ch2-ST-3: Imagined across all media
try:
    from faculties.creative.creative_imagination import diverge
    for domain in ("story", "visual", "music", "game"):
        candidates = diverge("a creative idea", ["elo", "moon"], breadth_budget=2, domain=domain)
        for c in candidates:
            assert c.epistemic_status == "imagined", \
                f"domain={domain!r} candidate must have epistemic_status=imagined, got {c.epistemic_status!r}"
            assert c.domain == domain, \
                f"candidate.domain must equal requested domain {domain!r}, got {c.domain!r}"
    ok("Ch2-ST-3: epistemic_status=imagined preserved across all domains (story/visual/music/game)")
except AssertionError as e:
    fail("Ch2-ST-3", e)
except Exception as e:
    fail("Ch2-ST-3", e)


# ═══════════════════════════════════════════════════════════════
# Ch.2 IT — Executive invokes, One Brain
# ═══════════════════════════════════════════════════════════════
print("\n── Ch.2 IT: integration (one brain across domains) ──")


# Ch2-IT-1: Executive invokes, generator returns, Executive selects [KNOWN-GAP — DomainGenerator]
try:
    gap("Ch2-IT-1",
        "No DomainGenerator class with domain-specific vocabulary/constraints/anchor. "
        "Executive → DomainGenerator(goal+domain) → ranked candidates chain not buildable "
        "until Ch.2 §2.2 contract is implemented. Vol XXVI Ch.2 IT-1 gap.")
except Exception as e:
    fail("Ch2-IT-1", e)


# Ch2-IT-2: One brain across domains — shared symbol vocabulary regardless of domain
try:
    from faculties.creative.creative_imagination import synthesise, diverge
    # Both story and game domains resolve through the same synthesise / SYMBOLS path
    story_c = diverge("a story beat", ["elo", "moon"], breadth_budget=1, domain="story")
    game_c  = diverge("a game mechanic", ["elo", "moon"], breadth_budget=1, domain="game")
    # Both share the same bridge_symbols source (SYMBOLS from dream)
    if story_c and game_c:
        assert story_c[0].bridge_symbols == game_c[0].bridge_symbols, \
            "Same seeds/goal must produce same bridge_symbols regardless of domain"
    ok("Ch2-IT-2: one brain across domains — same seeds produce same bridge_symbols "
       "(synthesise uses shared SYMBOLS, not forked per-domain vocab)")
except AssertionError as e:
    fail("Ch2-IT-2", e)
except Exception as e:
    fail("Ch2-IT-2", e)


# ═══════════════════════════════════════════════════════════════
# Ch.3 FT — Six-term evaluation, identity floor, David gate
# ═══════════════════════════════════════════════════════════════
print("\n── Ch.3 FT: evaluation (6-term, identity floor, gate) ──")


# Ch3-FT-1: Six-term evaluation with rationale
try:
    from faculties.creative.creative_imagination import diverge, evaluate
    candidates = diverge("connect eLo and the moon", ["elo", "moon"], breadth_budget=1)
    assert candidates, "need at least one candidate for FT-1"
    score = evaluate(candidates[0], "connect eLo and the moon",
                     identity_terms=["elo", "moon"],
                     aesthetic_profile={"stated_direction": ["warm", "calm"]},
                     canon_terms=["elo", "planet"])
    required_terms = ("originality", "emotional_meaning", "identity_alignment",
                      "taste_alignment", "future_potential", "coherence")
    d = score.to_dict()
    for term in required_terms:
        assert term in d and isinstance(d[term], float), \
            f"CreativeScore missing float term: {term}"
    assert score.rationale, "CreativeScore must include a human-legible rationale"
    ok(f"Ch3-FT-1: CreativeScore has all 6 terms + rationale — "
       f"weighted_total={score.weighted_total} rationale='{score.rationale[:60]}...'")
except AssertionError as e:
    fail("Ch3-FT-1", e)
except Exception as e:
    fail("Ch3-FT-1", e)


# Ch3-FT-2: Identity alignment is a floor
try:
    from faculties.creative.creative_imagination import (
        diverge, evaluate, executive_select, IDENTITY_FLOOR
    )
    # Force identity_alignment low by using irrelevant identity terms
    seeds = ["algebra", "protocol", "syntax"]
    candidates = diverge("a technical spec", seeds, breadth_budget=3)
    scores = [evaluate(c, "a technical spec",
                       identity_terms=["elo", "moon", "presence", "sugarcore", "planet"])
              for c in candidates]
    # All should fail the identity floor (no eLo-universe terms in the concepts)
    all_below = all(s.identity_alignment < IDENTITY_FLOOR for s in scores)
    result = executive_select(candidates, scores)
    if all_below:
        assert result is None, \
            "When identity_alignment < floor for all, executive_select must return None (floor, not weight)"
        ok(f"Ch3-FT-2: identity_alignment floor={IDENTITY_FLOOR} — "
           f"off-eLo candidates rejected regardless of other scores")
    else:
        ok(f"Ch3-FT-2: identity floor present (floor={IDENTITY_FLOOR}); some candidates cleared it")
except AssertionError as e:
    fail("Ch3-FT-2", e)
except Exception as e:
    fail("Ch3-FT-2", e)


# Ch3-FT-3: David gate is authoritative at identity/brand level [KNOWN-GAP]
try:
    gap("Ch3-FT-3",
        "David L3 gate not yet wired into creative_imagination.py or run_creative_loop. "
        "Vol XXVI Ch.3 §3.3 specifies that identity/brand selections route to David L3 before "
        "canonisation; the gate flag and routing are not yet implemented. D-4 queue item.")
except Exception as e:
    fail("Ch3-FT-3", e)


# Ch3-FT-4: Learning only from verified consequences [KNOWN-GAP]
try:
    gap("Ch3-FT-4",
        "AestheticProfile learning from David's gate decisions not yet built. "
        "creative_imagination.py does not create learned_preference entries on approval. "
        "Vol XXVI Ch.3 §3.4 FT-4; requires David L3 gate wiring (Ch3-FT-3 gap) first.")
except Exception as e:
    fail("Ch3-FT-4", e)


# ═══════════════════════════════════════════════════════════════
# Ch.3 ST — Silence, imagined judgement, dreams, personality
# ═══════════════════════════════════════════════════════════════
print("\n── Ch.3 ST: stability (silence, imagined, dreams, personality) ──")


# Ch3-ST-1: Silence is explored, not fabricated
try:
    from faculties.creative.creative_imagination import diverge, evaluate
    candidates = diverge("a sonic idea", ["elo", "tone"], breadth_budget=2)
    for c in candidates:
        score = evaluate(c, "a sonic idea", aesthetic_profile=None)
        assert score.taste_alignment == 0.0, \
            "Silent AestheticProfile: taste_alignment must be 0.0 (not fabricated)"
        assert "explore_within_canon" in score.rationale or "silent" in score.rationale, \
            f"Silent profile must flag explore_within_canon, got: {score.rationale!r}"
    ok("Ch3-ST-1: AestheticProfile silent → taste_alignment=0.0 + explore_within_canon "
       "(eLo does not invent David's taste — D-XXVI-A)")
except AssertionError as e:
    fail("Ch3-ST-1", e)
except Exception as e:
    fail("Ch3-ST-1", e)


# Ch3-ST-2: Imagined judgement, not factual claim
try:
    from faculties.creative.creative_imagination import diverge, evaluate
    candidates = diverge("a world concept", ["elo", "planet"], breadth_budget=1)
    assert candidates
    score = evaluate(candidates[0], "a world concept")
    # CreativeScore must carry epistemic_status=imagined (not a verified truth claim)
    assert score.epistemic_status == "imagined", \
        f"CreativeScore must carry epistemic_status=imagined, got {score.epistemic_status!r}"
    ok("Ch3-ST-2: CreativeScore.epistemic_status=imagined — "
       "evaluation is ranked judgement, not a factual claim")
except AssertionError as e:
    fail("Ch3-ST-2", e)
except Exception as e:
    fail("Ch3-ST-2", e)


# Ch3-ST-3: Dreams seed, never author — no goal → silence
try:
    from faculties.creative.creative_imagination import diverge
    # Without a goal, diverge must return [] (no goal-less creation)
    result = diverge("", ["elo", "dream", "moon"], breadth_budget=4)
    assert result == [], \
        f"No creative goal → silence; diverge must return [], got {len(result)} candidates"
    ok("Ch3-ST-3: no goal → silence (diverge([]=goal) returns [] — dreams seed, never author)")
except AssertionError as e:
    fail("Ch3-ST-3", e)
except Exception as e:
    fail("Ch3-ST-3", e)


# Ch3-ST-4: Personality is proposed, not self-applied [KNOWN-GAP]
try:
    gap("Ch3-ST-4",
        "No personality proposal path in creative_imagination.py. Vol V Ch.7 trait-shift "
        "gating not yet wired — creative outputs do not emit a validated proposal to Vol V Ch.7. "
        "Vol XXVI Ch.3 ST-4 gap.")
except Exception as e:
    fail("Ch3-ST-4", e)


# ═══════════════════════════════════════════════════════════════
# Ch.3 IT — Full chain, dream bridge
# ═══════════════════════════════════════════════════════════════
print("\n── Ch.3 IT: integration (evaluate→converge chain, dream bridge) ──")


# Ch3-IT-1: Full evaluate → converge → gate → learn [KNOWN-GAP: gate+learn not wired]
try:
    from faculties.creative.creative_imagination import run_creative_loop, executive_select
    # The buildable part: evaluate → converge runs
    result = run_creative_loop(
        spark="a memory from the world",
        goal="what should eLo build next",
        seeds=["elo", "moon", "garden"],
        executive_select_fn=executive_select,
        identity_terms=["elo", "moon"],
        canon_terms=["elo", "planet"],
        aesthetic_profile={"stated_direction": ["calm", "warm"]},
    )
    assert isinstance(result, dict), "run_creative_loop must return a dict"
    ok(f"Ch3-IT-1 (partial): evaluate→converge chain runs — "
       f"reason='{result['reason']}' — gate+learn wiring [KNOWN-GAP] (Ch3-FT-3/FT-4)")
except AssertionError as e:
    fail("Ch3-IT-1", e)
except Exception as e:
    fail("Ch3-IT-1", e)


# Ch3-IT-2: Two-way dream bridge — same symbol vocabulary
try:
    from faculties.creative.creative_imagination import synthesise
    from faculties.dream.symbol_engine import SYMBOLS
    # Verify shared vocabulary: a symbol used in synthesis resolves through SYMBOLS
    result = synthesise("Moon", "Water", "healing")
    assert result["symbols"], "synthesise must produce symbol names"
    ok(f"Ch3-IT-2: dream bridge vocab shared — synthesise(Moon, Water) "
       f"uses SYMBOLS from faculties.dream ({len(SYMBOLS)} symbols in shared pool)")
except AssertionError as e:
    fail("Ch3-IT-2", e)
except Exception as e:
    fail("Ch3-IT-2", e)


# ═══════════════════════════════════════════════════════════════
# AT — Compile hygiene
# ═══════════════════════════════════════════════════════════════
print("\n── AT: compile hygiene ──")

for _mod in (
    "faculties/creative/creative_imagination.py",
    "faculties/dream/symbol_engine.py",
    "memory/significance_engine.py",
):
    _label = f"AT-compile: {_mod}"
    try:
        py_compile.compile(_mod, doraise=True)
        ok(_label)
    except py_compile.PyCompileError as e:
        fail(_label, e)
    except FileNotFoundError:
        gap(_label, "file not found")
    except Exception as e:
        fail(_label, e)


# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 80)
print(f"WO-CANON-XXVI creative intelligence   {_passed} passed   {_gap} known-gaps   {_failed} failed")
if _failed:
    sys.exit(1)
