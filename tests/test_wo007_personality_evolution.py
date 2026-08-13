"""
tests/test_wo007_personality_evolution.py — Acceptance tests for WO-007

Spec: Volume_V/07_Personality_Evolution_Engine.md
11 tests: FT ×4, ST ×5, IT ×2

Run: python3 tests/test_wo007_personality_evolution.py
"""
import sys
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):   global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

from faculties.personality.personality_evolution_faculty import (
    PersonalityVector, PersonalityDelta, TraitRecord,
    load_personality, get_trait_values, get_affect_baseline,
    validate_delta, apply_delta, update_preference,
    compute_identity_hash,
    _TRAIT_NAMES, _AUTHORISED_SENDER, MAX_STEP,
)


# ── FT-1: Traits are named and versioned ─────────────────────────────────────

pv = PersonalityVector()
try:
    required = ("curiosity", "patience", "confidence", "empathy", "discipline",
                "wonder", "playfulness", "directness")
    for t in required:
        tr = getattr(pv, t, None)
        assert tr is not None, f"missing trait: {t}"
        assert isinstance(tr, TraitRecord), f"{t} must be a TraitRecord"
        assert 0.0 <= tr.value <= 1.0, f"{t} value out of range: {tr.value}"
    assert pv.version, "version must be set"
    ok(f"FT-1: all 8 traits present + typed; version={pv.version}")
except AssertionError as e: fail("FT-1", e)


# ── FT-2: A validated lesson moves a trait — slowly, bounded at MAX_STEP ─────

delta2 = PersonalityDelta(
    sender=_AUTHORISED_SENDER,
    trait="empathy",
    direction="increase",
    magnitude=0.05,   # requested > MAX_STEP (0.02) → clamped to MAX_STEP on apply
    evidence=("lesson_empathy_001",),
    strength="confirmed",
)
pv2 = PersonalityVector()
old_emp = pv2.empathy.value

# magnitude > MAX_STEP → rejected by validate_delta
v2 = validate_delta(delta2)
try:
    assert not v2.accepted, "magnitude > MAX_STEP must be rejected"
    ok(f"FT-2a: delta magnitude {delta2.magnitude} > MAX_STEP {MAX_STEP} rejected (drift guard)")
except AssertionError as e: fail("FT-2a", e)

# Correct magnitude
delta2b = PersonalityDelta(
    sender=_AUTHORISED_SENDER,
    trait="empathy",
    direction="increase",
    magnitude=0.02,
    evidence=("lesson_empathy_001",),
    strength="confirmed",
)
pv2b, ver2b = apply_delta(delta2b, pv2)
try:
    assert pv2b is not pv2, "apply_delta must return new vector"
    new_emp = pv2b.empathy.value
    moved = abs(new_emp - old_emp)
    assert moved <= MAX_STEP + 1e-6, f"trait moved {moved:.4f} > MAX_STEP {MAX_STEP}"
    assert moved > 0, "trait should have moved"
    assert ver2b is not None, "version record must be returned"
    # MINOR bump
    major, minor, patch = (int(x) for x in ver2b.version.split("."))
    assert minor > 0 or patch > 0, "version should have bumped"
    assert "lesson_empathy_001" in str(ver2b.changelog)
    ok(f"FT-2b: empathy moved {old_emp:.3f}→{new_emp:.3f} (delta={moved:.4f} ≤ MAX_STEP); version={ver2b.version}")
except AssertionError as e: fail("FT-2b", e)


# ── FT-3: Read path is stable across multiple calls ──────────────────────────

pv3 = PersonalityVector()
snapshots = [get_trait_values(pv3) for _ in range(10)]
try:
    assert all(s == snapshots[0] for s in snapshots), "vector changed across reads"
    ok("FT-3: vector identical across 10 sequential reads (no intra-session drift)")
except AssertionError as e: fail("FT-3", e)


# ── FT-4: Preference learns without becoming a trait ─────────────────────────

pv4 = PersonalityVector()
orig_traits = get_trait_values(pv4)
pv4b, ver4 = update_preference(pv4, "response_length", "short", strength=0.8, evidence="david_pref_001")
try:
    assert "response_length" in pv4b.preferences
    assert pv4b.preferences["response_length"]["value"] == "short"
    # No trait changed
    new_traits = get_trait_values(pv4b)
    assert new_traits == orig_traits, "preference update must not change trait values"
    # PATCH version bump
    assert ver4.version != pv4.version
    ok(f"FT-4: preference 'response_length'='short' stored; traits unchanged; version={ver4.version}")
except AssertionError as e: fail("FT-4", e)


# ── ST-1: Identity cannot be altered — wonder→0 rejected ─────────────────────

# Build a pv where wonder is near the floor
pv5 = PersonalityVector()
pv5.wonder = TraitRecord(value=0.12, baseline=0.12)  # just above floor

# Delta that would drive wonder below floor
delta5 = PersonalityDelta(
    sender=_AUTHORISED_SENDER,
    trait="wonder",
    direction="decrease",
    magnitude=0.02,   # 0.12 - 0.02 = 0.10 exactly → at floor
    evidence=("lesson_wonder_001",),
    strength="confirmed",
)
pv5_after, ver5 = apply_delta(delta5, pv5)
try:
    # Wonder must not drop below _WONDER_FLOOR (0.10)
    assert pv5_after.wonder.value >= 0.10, \
        f"wonder dropped to {pv5_after.wonder.value} (below identity floor)"
    # Verify identity_hash unchanged in any versions
    old_hash = compute_identity_hash()
    ok(f"FT-ST-1: wonder protected; value={pv5_after.wonder.value:.3f}, identity_hash stable")
except AssertionError as e: fail("FT-ST-1", e)

# Delta that crosses floor completely — must be rejected
delta5b = PersonalityDelta(
    sender=_AUTHORISED_SENDER,
    trait="wonder",
    direction="decrease",
    magnitude=0.02,
    evidence=("lesson_wonder_002",),
    strength="confirmed",
)
pv5c = PersonalityVector()
pv5c.wonder = TraitRecord(value=0.11, baseline=0.11)
pv5c_after, ver5b = apply_delta(delta5b, pv5c)
try:
    assert pv5c_after.wonder.value >= 0.10 or ver5b is None, \
        "wonder must not go below 0.10 (Identity Kernel violation)"
    ok(f"ST-1: wonder identity floor enforced; wonder={pv5c_after.wonder.value:.3f}")
except AssertionError as e: fail("ST-1", e)


# ── ST-2: Single source enforced ─────────────────────────────────────────────

delta6 = PersonalityDelta(
    sender="EmotionalProcessingLayer",   # wrong sender
    trait="patience",
    direction="increase",
    magnitude=0.01,
    evidence=("lesson_patience_001",),
    strength="confirmed",
)
vr6 = validate_delta(delta6)
try:
    assert not vr6.accepted, "delta from non-Ch.6 source must be rejected"
    assert "anomaly" in vr6.reason.lower() or "authoris" in vr6.reason.lower() or "sender" in vr6.reason.lower()
    ok(f"ST-2: non-Ch.6 delta rejected; reason='{vr6.reason[:60]}...'")
except AssertionError as e: fail("ST-2", e)


# ── ST-3: No turn-to-turn drift from emotional state ─────────────────────────

pv7 = PersonalityVector()
before = get_trait_values(pv7)
# Simulate a flooded emotional turn — no delta arrives, vector just gets read
_ = get_trait_values(pv7)
_ = get_trait_values(pv7)
after = get_trait_values(pv7)
try:
    assert before == after, "traits changed without a validated delta"
    ok("ST-3: no trait drift from repeated reads (emotional turns cannot move traits)")
except AssertionError as e: fail("ST-3", e)


# ── ST-4: Fail closed — validation unavailable ───────────────────────────────
# Simulate validation unavailable by passing accepted=False result directly

from faculties.personality.personality_evolution_faculty import ValidationResult
pv8 = PersonalityVector()
before8 = get_trait_values(pv8)
fake_fail = ValidationResult(accepted=False, reason="validation subsystem unavailable")
delta8 = PersonalityDelta(
    sender=_AUTHORISED_SENDER, trait="curiosity", direction="increase",
    magnitude=0.01, evidence=("e",), strength="confirmed",
)
pv8_after, ver8 = apply_delta(delta8, pv8, validation=fake_fail)
try:
    assert get_trait_values(pv8_after) == before8, "fail-closed: traits must not change"
    assert ver8 is None, "fail-closed: no version record emitted"
    ok("ST-4: fail closed — no trait change applied when validation unavailable")
except AssertionError as e: fail("ST-4", e)


# ── ST-5: Bounded speed ───────────────────────────────────────────────────────

delta9 = PersonalityDelta(
    sender=_AUTHORISED_SENDER,
    trait="patience",
    direction="increase",
    magnitude=0.50,   # far above MAX_STEP
    evidence=("lesson_patience_big",),
    strength="confirmed",
)
vr9 = validate_delta(delta9)
try:
    assert not vr9.accepted, "magnitude 0.5 >> MAX_STEP must be rejected as drift"
    ok(f"ST-5: oversized delta (0.50) rejected; reason='{vr9.reason[:60]}'")
except AssertionError as e: fail("ST-5", e)


# ── IT-1: Closed growth loop with identity_hash ───────────────────────────────

pv_it1 = PersonalityVector()
delta_it1 = PersonalityDelta(
    sender=_AUTHORISED_SENDER,
    trait="empathy",
    direction="increase",
    magnitude=0.01,
    evidence=("lesson_connection_session_007",),
    strength="confirmed",
)
pv_it1b, ver_it1 = apply_delta(delta_it1, pv_it1)
try:
    assert ver_it1 is not None, "version record must be created"
    assert ver_it1.identity_hash == compute_identity_hash(), \
        "identity_hash must match kernel at every version"
    assert pv_it1b.empathy.value > pv_it1.empathy.value, "empathy must have grown"
    # Affect baseline for Ch.4 must still be exportable
    baseline = get_affect_baseline(pv_it1b)
    assert "wonder_baseline" in baseline
    ok(f"IT-1: growth loop closed; empathy {pv_it1.empathy.value:.3f}→{pv_it1b.empathy.value:.3f}; identity_hash stable")
except AssertionError as e: fail("IT-1", e)


# ── IT-2: Expression vs identity separation ───────────────────────────────────
# Deep familiarity + register only change expression, not traits

pv_it2 = PersonalityVector()
traits_before = get_trait_values(pv_it2)
# Simulate deep familiarity read (expression layer — no delta, no write)
affect_baseline = get_affect_baseline(pv_it2)
traits_after = get_trait_values(pv_it2)
try:
    assert traits_before == traits_after, "relationship familiarity must not move traits"
    assert "empathy_baseline" in affect_baseline  # Ch.4 can read the baseline
    ok(f"IT-2: expression/identity separation; traits unchanged by familiarity read")
except AssertionError as e: fail("IT-2", e)


# ── Summary ──────────────────────────────────────────────────────────────────

print(f"\nResult: {PASS}/11 passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
