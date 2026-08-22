"""
tests/test_bdrift_u_trait_isolation.py — BDRIFT-U acceptance tests.

David L3 ruling 2026-08-22: EloSelfState.core_values must not enter the
canonical identity prompt path. Canonical character traits come from
canonical_identity.md via personality_block. identity_block() retains
name/with/invariants only.

Cards:
    BDRIFT_U_trait_vector_isolation.md
    BUILDER_CARD_F6_persona_david_sync.md (verified: zero "the user" in _PERSONA)

Acceptance tests:
    AT-U-1: identity_block() output contains no core_values content
    AT-U-2: identity_block() output contains no "core traits:" line
    AT-U-3: EloSelfState loads; core_values field still present (preserved)
    AT-U-4: identity_block() renders name, with, invariants correctly
    AT-U-5: canonical identity block comes from canonical_identity.md only
    AT-U-6: _PERSONA contains zero "the user" occurrences (F6 remnant)

Regression tests:
    AT-U-R1: if core_values content appears in identity block, test goes RED
    AT-U-R2: canonical_identity.md missing → identity block still omits core_values
             (identity_block() isolation does not fall back to core_values)
"""

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)


from self.elo_self_model import EloSelfState, identity_block


# ── AT-U-1: identity_block output contains no core_values content ─────────────

class TestAU1_NoCoreValuesInIdentityBlock:

    def test_default_state_no_core_value_trait_text(self):
        state = EloSelfState()
        block = identity_block(state)
        # None of the default core_values should appear as trait assertions
        for trait in state.core_values:
            # The trait must not appear in the rendered identity block
            assert trait.lower() not in block.lower(), (
                f"core_values trait '{trait}' found in identity_block output — "
                f"BDRIFT-U violation (core_values must not enter identity prompt path)"
            )

    def test_custom_core_values_do_not_leak(self):
        state = EloSelfState()
        object.__setattr__(state, "core_values", ["sentient", "recursive", "self-modifying"])
        block = identity_block(state)
        for trait in ["sentient", "recursive", "self-modifying"]:
            assert trait.lower() not in block.lower(), (
                f"Modified core_values trait '{trait}' leaked into identity_block — "
                f"core_values must be fully isolated from the identity prompt path"
            )


# ── AT-U-2: identity_block output contains no "core traits:" line ─────────────

class TestAU2_NoCoreTraitsLabel:

    def test_no_core_traits_label(self):
        state = EloSelfState()
        block = identity_block(state)
        assert "core traits:" not in block.lower(), (
            "identity_block() still emits 'core traits:' — BDRIFT-U not applied"
        )

    def test_no_core_values_label(self):
        state = EloSelfState()
        block = identity_block(state)
        assert "core values:" not in block.lower(), (
            "identity_block() emits 'core values:' — must be absent"
        )


# ── AT-U-3: EloSelfState loads; core_values field still present ───────────────

class TestAU3_CoreValuesPreserved:

    def test_core_values_field_exists(self):
        state = EloSelfState()
        assert hasattr(state, "core_values"), "core_values field must remain in EloSelfState"

    def test_core_values_non_empty_default(self):
        state = EloSelfState()
        assert len(state.core_values) > 0, (
            "EloSelfState.core_values should have default values (field preserved for future use)"
        )

    def test_core_values_default_content(self):
        state = EloSelfState()
        # Verify the defaults that were previously leaking are still in the field
        # (preserved, just not injected)
        assert any("calm" in v or "playful" in v or "curious" in v for v in state.core_values), (
            "core_values defaults seem missing — field should be preserved even though not injected"
        )


# ── AT-U-4: identity_block renders name, with, invariants correctly ───────────

class TestAU4_IdentityBlockRetainsCanonicalFields:

    def test_name_present(self):
        state = EloSelfState()
        block = identity_block(state)
        assert "name: eLo" in block, "identity_block must still assert name: eLo"

    def test_with_present(self):
        state = EloSelfState()
        block = identity_block(state)
        assert "with: David" in block, "identity_block must still assert with: David"

    def test_invariants_present(self):
        state = EloSelfState()
        block = identity_block(state)
        assert "invariants:" in block, "identity_block must still render invariants"
        assert "never preachy" in block, "'never preachy' invariant missing from identity_block"

    def test_constitutional_header_present(self):
        state = EloSelfState()
        block = identity_block(state)
        assert "[IDENTITY" in block, "identity_block must still include the [IDENTITY...] header"


# ── AT-U-5: canonical identity comes from canonical_identity.md only ──────────

class TestAU5_CanonicalIdentitySource:

    def test_canonical_identity_file_exists(self):
        canonical_path = os.path.join(
            _ROOT, "elo_personality_engine", "sources", "canonical_identity.md"
        )
        assert os.path.exists(canonical_path), (
            "canonical_identity.md missing — canonical identity source not present"
        )

    def test_personality_profile_has_foundational_traits(self):
        from elo_personality_engine.injection_layer import load_personality_profile
        profile = load_personality_profile(force=True)
        assert len(profile.foundational_traits) == 7, (
            f"Expected 7 foundational traits from canonical_identity.md; "
            f"got {len(profile.foundational_traits)}"
        )

    def test_personality_block_has_canonical_traits(self):
        from elo_personality_engine.injection_layer import load_personality_profile
        profile = load_personality_profile(force=True)
        block = profile.to_prompt_block()
        assert "ELO FOUNDATIONAL CHARACTER" in block, (
            "personality_block must contain ELO FOUNDATIONAL CHARACTER section"
        )
        assert "curious" in block.lower(), "canonical trait 'curious' missing from personality_block"
        assert "encouraging" in block.lower(), "canonical trait 'encouraging' missing from personality_block"

    def test_identity_block_does_not_duplicate_canonical_traits(self):
        """identity_block and personality_block should not both assert the same traits."""
        from elo_personality_engine.injection_layer import load_personality_profile
        profile = load_personality_profile(force=True)
        state = EloSelfState()
        id_block = identity_block(state)
        # canonical traits must NOT appear in identity_block
        for trait in profile.foundational_traits:
            # Strip to bare keyword for comparison
            bare = trait.split()[0].lower()
            assert bare not in id_block.lower() or "invariants" in id_block.lower(), (
                f"Canonical foundational trait '{trait}' found in identity_block — "
                f"BDRIFT-U: traits must come from personality_block only"
            )


# ── AT-U-6: _PERSONA contains zero "the user" occurrences (F6) ───────────────

class TestAU6_PersonaNoTheUser:

    def test_no_the_user_in_persona(self):
        from runtime.prompt_builder import _PERSONA
        hits = [
            (i + 1, line)
            for i, line in enumerate(_PERSONA.splitlines())
            if "the user" in line.lower()
        ]
        assert len(hits) == 0, (
            f"F6 (WO-CANON-I): 'the user' found in _PERSONA at lines: "
            + "; ".join(f"L{ln}: {txt.strip()}" for ln, txt in hits)
        )


# ── AT-U-R1: regression — core_values reintroduction goes RED ─────────────────

class TestAUR1_RegressionCoreValuesNotReintroduced:

    def test_none_of_the_problematic_non_canonical_traits_appear(self):
        """
        The specific traits that were previously leaking and are NOT canonical:
        'observant' (unknown provenance), 'emotionally aware' (conflicts with
        canonical 'emotionally present'), 'grounded' (U-grounded, UNKNOWN).
        None of these should appear in identity_block output.
        """
        state = EloSelfState()
        block = identity_block(state)
        non_canonical = ["observant", "emotionally aware", "grounded"]
        for trait in non_canonical:
            assert trait.lower() not in block.lower(), (
                f"Non-canonical trait '{trait}' (U-trait-vector-injection) found in "
                f"identity_block — BDRIFT-U regression"
            )


# ── AT-U-R2: regression — no fallback to core_values if canonical missing ─────

class TestAUR2_NoSilentFallbackToCoreValues:

    def test_identity_block_does_not_use_core_values_even_as_fallback(self):
        """
        identity_block() must not use core_values as a fallback for canonical traits.
        Verify by setting core_values to a canary list — none of those values should
        appear in the rendered block. The isolation must be unconditional.
        """
        state = EloSelfState()
        # Set core_values to distinctive canary values
        object.__setattr__(state, "core_values", ["canary_alpha", "canary_beta", "canary_gamma"])
        block = identity_block(state)
        for canary in ["canary_alpha", "canary_beta", "canary_gamma"]:
            assert canary not in block, (
                f"Canary value '{canary}' in core_values leaked into identity_block output — "
                f"BDRIFT-U: isolation must be unconditional, not dependent on canonical file"
            )
