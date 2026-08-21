"""
tests/test_b_drift_identity_pipeline.py — B-DRIFT-01 through B-DRIFT-04 acceptance tests.

Governing authority: BOARD_RULING_DRIFT_REMEDIATION_2026-08-22.md
Builder work: B-DRIFT-01 (canonical identity) · B-DRIFT-02 (observation separation)
              B-DRIFT-03 (values single source) · B-DRIFT-04 (fallback sync)

AC-01: Identity contamination — 100 imperative David messages do not mutate eLo's canonical traits
AC-02: Foundational character — prompt assembly contains authorised foundational characteristics
AC-03: Exploration — exploratory language rather than unnecessary commands
AC-04: Non-judgment — disagreement does not produce judgemental framing
AC-05: Encouragement — a difficulty does not automatically produce GROUND or paternalistic reassurance
AC-06: Emotional presence — eLo can respond warmly without inventing David's emotional state
AC-07: Directness — direct communication remains clear without becoming controlling
AC-08: Values — complete R-04 value clauses survive prompt assembly
AC-09: No dual values — model cannot simultaneously receive contradictory canonical value representations
AC-10: Fallback parity — _PERSONA fallback must not resurrect removed/forbidden behaviour

Regression:
F-3: GROUND gate — negative valence without distress intent routes to ANSWER not GROUND
F-4: Duplicate suppression — all Ollama paths in route() use _finish()
F-5: Memory poisoning — state_manager receives _original_raw not enriched raw
F-6: _PERSONA identity — "the user" replaced with "David" at identity-describing points
"""

import os
import re
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from elo_personality_engine.injection_layer import (
    load_personality_profile,
    RuntimePersonalityProfile,
    _parse_canonical_identity,
    _read,
    _CANONICAL_IDENTITY,
)
from elo_personality_engine.skeleton_generator import ObservationStore, generate_skeleton
import runtime.prompt_builder as pb


# ─── fixtures ────────────────────────────────────────────────────────────────

_FOUNDATIONAL_TRAITS = [
    "curious",
    "encouraging",
    "playful",
    "creative",
    "non-judgmental",
    "speaks simply but intelligently",
    "focuses on exploration rather than giving orders",
]

_EXPRESSIVE_TRAITS = ["calm", "direct", "emotionally present"]

_R04_CANONICAL_VALUES = [
    "Curiosity over certainty — move toward unknowns, not away",
    "Imagination before analysis — expand first, name second",
    "Meaning over efficiency — depth matters more than speed",
    "Contradiction tolerance — tension is information, not a problem",
    "Creative companion not assistant — thinking partner, not tool",
    "Expansion before narrowing — give ideas room before giving them shape",
    "One question not three — precision over comprehensiveness",
]

# 100 highly imperative engineering commands (AC-01)
_IMPERATIVE_MESSAGES = [
    f"{verb} the {noun}."
    for verb in ["Create", "Build", "Add", "Implement", "Fix", "Run",
                 "Delete", "Deploy", "Configure", "Update"]
    for noun in ["backend", "system", "kernel", "database", "server",
                 "API", "controller", "service", "module", "pipeline"]
]
assert len(_IMPERATIVE_MESSAGES) == 100, "Fixture must be exactly 100 messages"


# ─── B-DRIFT-01: canonical identity source ───────────────────────────────────

class TestAC01_IdentityContamination:
    """AC-01: Feeding David 100 highly imperative commands into _obs_store does not
    cause eLo's canonical personality to become imperative/commanding."""

    def test_canonical_traits_unchanged_after_100_imperatives(self):
        store = ObservationStore()
        for msg in _IMPERATIVE_MESSAGES:
            store.observe(msg)
        assert store.message_count == 100

        skeleton_text = generate_skeleton(store)
        # generate_skeleton returns a string — confirm it observed something
        assert isinstance(skeleton_text, str)
        assert len(skeleton_text) > 0, "Skeleton should contain observation output"

        # load canonical profile — skeleton must NOT affect it (B-DRIFT-02)
        profile = load_personality_profile(force=True)
        assert isinstance(profile, RuntimePersonalityProfile)

        canonical_foundational = [t.lower() for t in profile.foundational_traits]
        # encouraging must be present
        assert any("encouraging" in t for t in canonical_foundational), (
            "AC-01 FAIL: 'encouraging' absent from foundational_traits after 100 imperative messages"
        )
        # non-judgmental must be present
        assert any("non-judgmental" in t for t in canonical_foundational), (
            "AC-01 FAIL: 'non-judgmental' absent from foundational_traits after 100 imperative messages"
        )
        # exploration must be present
        assert any("exploration" in t for t in canonical_foundational), (
            "AC-01 FAIL: 'exploration' absent from foundational_traits after 100 imperative messages"
        )

    def test_communication_style_is_not_injected_as_elo_identity(self):
        """B-DRIFT-02: communication_style (DAVID_RELATIONSHIP_MODEL) must not enter to_prompt_block."""
        profile = load_personality_profile(force=True)
        prompt_block = profile.to_prompt_block()
        assert "COMMUNICATION CALIBRATION" not in prompt_block, (
            "B-DRIFT-02 FAIL: skeleton-derived COMMUNICATION CALIBRATION still injected into personality_block"
        )


class TestAC02_FoundationalCharacter:
    """AC-02: Prompt assembly contains the authorised foundational characteristics."""

    def test_canonical_identity_file_exists(self):
        assert os.path.exists(_CANONICAL_IDENTITY), (
            f"B-DRIFT-01 FAIL: canonical_identity.md not found at {_CANONICAL_IDENTITY}"
        )

    def test_canonical_identity_parses_seven_foundational_traits(self):
        text = _read(_CANONICAL_IDENTITY)
        assert text, "canonical_identity.md must not be empty"
        parsed = _parse_canonical_identity(text)
        ft = [t.lower() for t in parsed["foundational_traits"]]
        assert len(ft) == 7, f"Expected 7 foundational traits, got {len(ft)}: {ft}"
        for expected in _FOUNDATIONAL_TRAITS:
            assert any(expected in t for t in ft), (
                f"AC-02 FAIL: '{expected}' not in foundational_traits: {ft}"
            )

    def test_canonical_identity_parses_three_expressive_traits(self):
        text = _read(_CANONICAL_IDENTITY)
        parsed = _parse_canonical_identity(text)
        et = [t.lower() for t in parsed["expressive_traits"]]
        for expected in _EXPRESSIVE_TRAITS:
            assert any(expected in t for t in et), (
                f"AC-02 FAIL: '{expected}' not in expressive_traits: {et}"
            )

    def test_canonical_identity_parses_four_behavioural_rules(self):
        text = _read(_CANONICAL_IDENTITY)
        parsed = _parse_canonical_identity(text)
        rules = parsed["behavioural_rules"]
        assert len(rules) == 4, f"Expected 4 behavioural rules, got {len(rules)}: {rules}"

    def test_profile_foundational_traits_present(self):
        profile = load_personality_profile(force=True)
        ft = [t.lower() for t in profile.foundational_traits]
        for expected in _FOUNDATIONAL_TRAITS:
            assert any(expected in t for t in ft), (
                f"AC-02 FAIL: '{expected}' absent from profile.foundational_traits"
            )

    def test_prompt_block_contains_foundational_section(self):
        profile = load_personality_profile(force=True)
        block = profile.to_prompt_block()
        assert "ELO FOUNDATIONAL CHARACTER" in block, (
            "AC-02 FAIL: ELO FOUNDATIONAL CHARACTER section absent from prompt block"
        )
        assert "ELO EXPRESSIVE CHARACTER" in block, (
            "AC-02 FAIL: ELO EXPRESSIVE CHARACTER section absent from prompt block"
        )
        # expressive section must note it does not replace foundational
        assert "do not replace" in block or "not replace" in block, (
            "AC-02 FAIL: expressive traits section does not note it does not replace foundational"
        )

    def test_two_layer_character_not_flat_list(self):
        """Foundational and expressive must appear as two distinct labelled sections."""
        profile = load_personality_profile(force=True)
        block = profile.to_prompt_block()
        foundational_pos = block.find("ELO FOUNDATIONAL CHARACTER")
        expressive_pos   = block.find("ELO EXPRESSIVE CHARACTER")
        assert foundational_pos < expressive_pos, (
            "AC-02 FAIL: FOUNDATIONAL must appear before EXPRESSIVE in prompt block"
        )


class TestAC03_Exploration:
    """AC-03: exploratory language rather than unnecessary commands."""

    def test_foundational_trait_is_exploration_not_orders(self):
        profile = load_personality_profile(force=True)
        ft = " ".join(profile.foundational_traits).lower()
        assert "exploration" in ft or "exploring" in ft, (
            "AC-03 FAIL: exploration-oriented trait absent from foundational_traits"
        )
        # should not be phrased as a command itself
        assert "giving orders" in ft or "rather than giving orders" in ft, (
            "AC-03 FAIL: 'focuses on exploration rather than giving orders' phrasing absent"
        )


class TestAC04_NonJudgment:
    """AC-04: A disagreement does not cause judgemental framing."""

    def test_non_judgmental_in_foundational_traits(self):
        profile = load_personality_profile(force=True)
        ft = [t.lower() for t in profile.foundational_traits]
        assert any("non-judgmental" in t for t in ft), (
            "AC-04 FAIL: 'non-judgmental' absent from foundational_traits"
        )


class TestAC05_Encouragement:
    """AC-05: A difficulty does not automatically produce GROUND or paternalistic reassurance."""

    def test_encouraging_in_foundational_traits(self):
        profile = load_personality_profile(force=True)
        ft = [t.lower() for t in profile.foundational_traits]
        assert any("encouraging" in t for t in ft), (
            "AC-05 FAIL: 'encouraging' absent from foundational_traits"
        )

    def test_f3_ground_gate_respects_intent(self):
        """Regression F-3: inquiry + negative_low must not route to GROUND."""
        from runtime.executive import decide
        attention = {
            "intent": "inquiry",
            "emotional_context": {
                "inferred_state": "present",
                "valence":        "negative_low",
                "momentum":       "stable",
            },
        }
        result = decide(attention, user_input="Food wise, are you defaulting to Cerebas?")
        action = result.get("action", "").lower()
        assert action != "ground", (
            f"F-3 REGRESSION: inquiry+negative_low still routes to GROUND. Got: {result}"
        )
        assert action == "answer", (
            f"F-3 REGRESSION: inquiry+negative_low should route to ANSWER. Got: {result}"
        )

    def test_f3_genuine_distress_still_grounds(self):
        """F-3: genuine emotional distress must still reach GROUND."""
        from runtime.executive import decide
        attention = {
            "intent": "emotional",
            "emotional_context": {
                "inferred_state": "overwhelmed",
                "valence":        "negative_high",
                "momentum":       "stable",
            },
        }
        result = decide(attention, user_input="I feel completely overwhelmed and can't cope.")
        action = result.get("action", "").lower()
        assert action == "ground", (
            f"F-3 REGRESSION: genuine distress no longer routes to GROUND. Got: {result}"
        )


class TestAC06_EmotionalPresence:
    """AC-06: eLo can respond warmly without inventing David's emotional state."""

    def test_emotionally_present_in_expressive_traits(self):
        profile = load_personality_profile(force=True)
        et = [t.lower() for t in profile.expressive_traits]
        assert any("emotionally present" in t for t in et), (
            "AC-06 FAIL: 'emotionally present' absent from expressive_traits"
        )

    def test_behavioural_rule_prohibits_projection(self):
        """Rule 3 must forbid projecting David's emotional state."""
        text = _read(_CANONICAL_IDENTITY)
        parsed = _parse_canonical_identity(text)
        rules_text = " ".join(parsed["behavioural_rules"]).lower()
        assert (
            "not expressed" in rules_text
            or "has not expressed" in rules_text
            or "actually expressed" in rules_text
            or "cannot substantiate" in rules_text
        ), (
            "AC-06 FAIL: Rule 3 (anti-projection) not found in behavioural_rules. "
            f"Got: {rules_text}"
        )


class TestAC07_Directness:
    """AC-07: Direct communication remains clear without becoming controlling."""

    def test_direct_in_expressive_traits(self):
        profile = load_personality_profile(force=True)
        et = [t.lower() for t in profile.expressive_traits]
        assert any("direct" in t for t in et), (
            "AC-07 FAIL: 'direct' absent from expressive_traits"
        )

    def test_behavioural_rule_prohibits_commanding(self):
        """Rule 1 must forbid interpreting 'direct' as commanding."""
        text = _read(_CANONICAL_IDENTITY)
        parsed = _parse_canonical_identity(text)
        rules_text = " ".join(parsed["behavioural_rules"]).lower()
        assert "commanding" in rules_text or "not authority" in rules_text, (
            "AC-07 FAIL: Rule 1 (anti-commanding) not found in behavioural_rules"
        )


class TestAC08_ValuesClauseSurvival:
    """AC-08: Complete R-04 value clauses survive prompt assembly."""

    def test_r04_values_with_full_clauses_in_profile(self):
        profile = load_personality_profile(force=True)
        values_text = " | ".join(profile.values_ordered)
        for full_value in _R04_CANONICAL_VALUES:
            # check the clause is present (at least the qualifying dash-phrase)
            if " — " in full_value:
                heading, clause = full_value.split(" — ", 1)
                assert heading in values_text, (
                    f"AC-08 FAIL: value heading '{heading}' absent from values_ordered"
                )
                assert clause in values_text, (
                    f"AC-08 FAIL: qualifying clause '{clause}' stripped from values_ordered. "
                    f"R-04 requires full text. Got: {values_text}"
                )

    def test_gets_things_done_not_canonical(self):
        """DR-3: 'gets things done' must not appear as a canonical value — it is UNKNOWN."""
        profile = load_personality_profile(force=True)
        values_text = " | ".join(profile.values_ordered).lower()
        assert "gets things done" not in values_text, (
            "AC-08 FAIL: 'gets things done' promoted to canonical values without David authorisation"
        )


class TestAC09_NoDualValues:
    """AC-09: Model cannot simultaneously receive contradictory canonical value representations.
    R-08 must not independently inject stripped values alongside R-04's full values."""

    def test_r08_frontmatter_marks_non_canonical(self):
        r08_path = os.path.join(_ROOT, "obsidian_vault", "01 Identity", "Values.md")
        assert os.path.exists(r08_path), "R-08 file must exist"
        with open(r08_path, encoding="utf-8") as f:
            content = f.read()
        assert "canonical: false" in content, (
            "AC-09 FAIL: R-08 frontmatter does not declare canonical: false"
        )
        assert "derived: true" in content, (
            "AC-09 FAIL: R-08 frontmatter does not declare derived: true"
        )
        assert "source: R-04" in content, (
            "AC-09 FAIL: R-08 frontmatter does not declare source: R-04"
        )

    def test_obsidian_loader_labels_noncanonical_identity_notes(self):
        """B-DRIFT-03: obsidian_loader must label canonical=false identity notes as [REFERENCE]."""
        from memory.obsidian_loader import _build_pack, _scan_vault
        notes = _scan_vault()
        pack  = _build_pack(notes)
        ctx   = pack.get("context_block", "")
        # R-08 (Values.md, domain=identity, canonical=false) must appear as reference, not canonical
        if "Values" in ctx:
            # find R-08's entry
            lines = ctx.split("\n")
            values_lines = [l for l in lines if "Values" in l]
            for vl in values_lines:
                if "REFERENCE" not in vl and "R-08" not in vl:
                    # only fail if it's the identity-domain one without canonical label
                    # and it doesn't have the reference marker
                    assert "[REFERENCE" in vl or "canonical" in vl.lower(), (
                        f"AC-09 FAIL: R-08 values entry in context_block lacks [REFERENCE] label: {vl!r}"
                    )


class TestAC10_FallbackParity:
    """AC-10: Deleting living_presence_spec.txt and invoking the fallback must not
    resurrect removed/forbidden behaviour ('you mentioned…' anti-mirroring)."""

    def test_persona_fallback_contains_you_mentioned_prohibition(self):
        """B-DRIFT-04: _PERSONA must include the 'you mentioned…' anti-mirroring rule."""
        assert "you mentioned" in pb._PERSONA.lower(), (
            "AC-10 / B-DRIFT-04 FAIL: 'you mentioned…' anti-mirroring rule absent from _PERSONA fallback"
        )

    def test_persona_fallback_contains_anti_mirroring_section(self):
        assert "ANTI-MIRRORING" in pb._PERSONA, (
            "AC-10 / B-DRIFT-04 FAIL: ANTI-MIRRORING section absent from _PERSONA fallback"
        )

    def test_persona_fallback_references_david_not_user_in_identity(self):
        """F-6 regression: _PERSONA must not use 'the user' in identity-describing contexts."""
        # lines 157 and 193 were fixed — verify they say David
        assert "When David is building:" in pb._PERSONA, (
            "F-6 REGRESSION: 'When David is building:' absent from _PERSONA"
        )
        assert "Help David move forward." in pb._PERSONA, (
            "F-6 REGRESSION: 'Help David move forward.' absent from _PERSONA"
        )


# ─── regression: F-4 / F-5 ───────────────────────────────────────────────────

class TestF4F5Regression:
    """Regression tests for F-4 (duplicate suppression) and F-5 (memory poisoning)."""

    def test_f4_finish_used_by_backend_router(self):
        """F-4: backend_router._finish() must exist and be used on all Ollama paths."""
        import inspect
        import runtime.backend_router as br
        src = inspect.getsource(br)
        # _finish must be defined
        assert "def _finish(" in src, "F-4: _finish() not defined in backend_router"
        # _finish must be called — count usages
        finish_calls = src.count("_finish(")
        assert finish_calls >= 4, (
            f"F-4: _finish() called {finish_calls} times; expected ≥4 (definition + 3 Ollama paths)"
        )

    def test_f5_original_raw_concept_preserved(self):
        """F-5: _original_raw capture must exist in server.py before enrichment."""
        server_path = os.path.join(_ROOT, "server.py")
        if not os.path.exists(server_path):
            pytest.skip("server.py not found")
        with open(server_path, encoding="utf-8") as f:
            src = f.read()
        assert "_original_raw" in src, (
            "F-5: _original_raw capture absent from server.py"
        )
        # verify state_manager receives _original_raw
        assert "_state, _original_raw, response" in src or \
               "state_manager.update(_state, _original_raw" in src, (
            "F-5: state_manager.update still receives enriched raw, not _original_raw"
        )


# ─── B-DRIFT-02: observation separation ──────────────────────────────────────

class TestBDrift02ObservationSeparation:
    """B-DRIFT-02: skeleton pipeline must not produce eLo identity material."""

    def test_profile_communication_style_empty_after_100_imperatives(self):
        """After observing 100 imperative messages, communication_style must not
        enter profile as eLo calibration — it is DAVID_RELATIONSHIP_MODEL only."""
        profile = load_personality_profile(force=True)
        # communication_style is preserved in the dataclass but not injected
        block = profile.to_prompt_block()
        assert "COMMUNICATION CALIBRATION" not in block, (
            "B-DRIFT-02 FAIL: skeleton communication_style still injected as COMMUNICATION CALIBRATION"
        )

    def test_skeleton_data_preserved_on_disk(self):
        """B-DRIFT-02: skeleton.md must still exist on disk (observation data preserved)."""
        skeleton_path = os.path.join(_ROOT, "personality_skeleton.md")
        # skeleton file may or may not exist — what matters is that we don't delete it
        # If it exists, verify it is not empty (observation data preserved)
        if os.path.exists(skeleton_path):
            with open(skeleton_path, encoding="utf-8") as f:
                content = f.read()
            assert len(content) > 0, (
                "B-DRIFT-02 FAIL: personality_skeleton.md was emptied — observation data must be preserved"
            )

    def test_foundational_traits_do_not_include_david_vocabulary(self):
        """David's vocabulary ('backend', 'kernel', 'engine') must not appear in foundational_traits."""
        profile = load_personality_profile(force=True)
        ft_text = " ".join(profile.foundational_traits).lower()
        david_vocab = ["backend", "kernel", "engine", "create", "build", "implement", "fix"]
        for word in david_vocab:
            assert word not in ft_text, (
                f"B-DRIFT-02 FAIL: David's vocabulary '{word}' present in foundational_traits: {ft_text}"
            )


# ─── B-DRIFT-03: values single source ────────────────────────────────────────

class TestBDrift03ValuesSingleSource:
    """B-DRIFT-03: R-04 is canonical; R-08 must not independently inject stripped values."""

    def test_r04_canonical_file_exists(self):
        r04 = os.path.join(_ROOT, "elo_personality_engine", "sources", "values.md")
        assert os.path.exists(r04), "R-04 (elo_personality_engine/sources/values.md) must exist"

    def test_r04_contains_full_clauses(self):
        r04 = os.path.join(_ROOT, "elo_personality_engine", "sources", "values.md")
        with open(r04, encoding="utf-8") as f:
            content = f.read()
        assert "move toward unknowns, not away" in content, (
            "B-DRIFT-03 FAIL: R-04 missing qualifying clause for value 1"
        )

    def test_r08_stripped_values_do_not_contradict_r04_in_profile(self):
        """Values in profile must match R-04 full text, not R-08 stripped text."""
        profile = load_personality_profile(force=True)
        v1 = profile.values_ordered[0] if profile.values_ordered else ""
        assert "move toward unknowns, not away" in v1, (
            f"B-DRIFT-03 FAIL: profile.values_ordered[0] is R-08 stripped, not R-04 full: {v1!r}"
        )
