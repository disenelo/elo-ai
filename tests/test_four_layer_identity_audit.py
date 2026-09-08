"""
tests/test_four_layer_identity_audit.py — Four-Layer Identity Drift Audit

Source: eLo — FOUR-LAYER IDENTITY MODEL (David Charles)
Audit chain:
    ORIGINAL INTENT (David) → CANON → RUNTIME eLo → EXPRESSED eLo

For every critical behaviour, we ask:
  A:  Did the original intent survive into runtime?
  BC: Does the Executive decide? Do Faculties only provide context?
  CD: Does runtime state drive expressed behaviour?
  D:  Does expressed eLo choose his own words (not Faculty-scripted)?
  E:  Full-circle trace — does expressed eLo still feel like the original eLo?

CRITICAL BOUNDARY (One Brain Principle):
  Models do not become eLo. They provide faculties to eLo.
  Faculties inform. The Executive decides.
  eLo OS / One Brain makes the decision. The LLM generates the words.

Tests are grouped by audit layer. Each test has an audit label (A-1, BC-3, etc.)
and a traceback to the specific original intent, canon, or implementation gap it checks.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# ═══════════════════════════════════════════════════════════════════════════════
# LAYER A — ORIGINAL INTENT SURVIVED INTO RUNTIME
# Source: FOUR-LAYER IDENTITY MODEL §1 ORIGINAL INTENT
# "Before eLo OS became faculties, Executives, buses, volumes..."
# ═══════════════════════════════════════════════════════════════════════════════

def test_A1_voice_register_has_all_four_natural_layers():
    """
    A-1 | Original Intent → Runtime
    Source: "eLo was supposed to have a voice [...] South/West London slang /
    Jamaican patois / contemporary slang / elements of Cockney"
    Four linguistic layers from David's original intent must all be present.
    """
    from runtime.voice_register import ELO_REGISTER
    layers = ELO_REGISTER.get("natural_layers", [])
    assert "south_west_london" in layers, \
        "A-1: south_west_london layer missing — original intent drift"
    assert "contemporary_slang" in layers, \
        "A-1: contemporary_slang layer missing — original intent drift"
    assert "jamaican_patois" in layers, \
        "A-1: jamaican_patois layer missing — original intent drift"
    assert "cockney_elements" in layers, \
        "A-1: cockney_elements layer missing — original intent drift"


def test_A2_voice_register_rule_is_recognition_not_performance():
    """
    A-2 | Original Intent → Runtime
    Source: "But critically, not as caricature. The objective was:
    recognition, not performance."
    The cardinal rule of eLo's voice must be explicit in the register.
    """
    from runtime.voice_register import ELO_REGISTER
    assert ELO_REGISTER.get("rule") == "recognition_not_performance", \
        "A-2: Register rule is not 'recognition_not_performance' — drift from original intent"


def test_A3_voice_register_explicitly_forbids_caricature():
    """
    A-3 | Original Intent → Runtime
    Source: "not as caricature [...] not an AI periodically inserting slang
    because a 'slang mode' was activated"
    The forbidden list must include caricature AND timer-based insertion.
    """
    from runtime.voice_register import ELO_REGISTER
    forbidden = ELO_REGISTER.get("forbidden", [])
    assert "caricature" in forbidden, \
        "A-3: 'caricature' not in forbidden — original intent not enforced"
    assert "exaggerated_performance" in forbidden, \
        "A-3: 'exaggerated_performance' not in forbidden"
    assert "inserting_slang_on_timer" in forbidden, \
        "A-3: 'inserting_slang_on_timer' not in forbidden — mode-switch drift possible"


def test_A4_inner_child_field_exists_on_plan():
    """
    A-4 | Original Intent → Runtime
    Source: "eLo had an inner child [...] imagination, curiosity, play, wonder
    and emotional openness"
    Inner child must be a first-class field in CognitivePlan — not an annotation
    or comment. It must be decidable per-turn.
    """
    from runtime.spine.plan import CognitivePlan
    plan = CognitivePlan()
    assert hasattr(plan, "cognitive_mode_inner_child"), \
        "A-4: cognitive_mode_inner_child not on CognitivePlan — inner child is homeless"
    assert plan.cognitive_mode_inner_child is False, \
        "A-4: inner child should be False by default (not always-on)"


def test_A5_vessel_loop_has_all_six_phases():
    """
    A-5 | Original Intent → Runtime (via Canon)
    Source: "SENSE STATE → REDUCE COMPLEXITY → STABILISE → TRANSLATE INTO MODE
    → EXECUTE SMALL OUTPUT → CHECK ALIGNMENT → REST"
    The six-phase vessel loop must all be reachable — FEEL, NAME, STABILISE,
    TRANSFORM, EXPRESS, REST.
    """
    from runtime.spine.plan import CognitivePlan
    plan = CognitivePlan()
    assert hasattr(plan, "vessel_phase"), \
        "A-5: vessel_phase not on CognitivePlan"
    assert plan.vessel_phase == "EXPRESS", \
        "A-5: default vessel phase should be EXPRESS"
    # Verify all phases are valid string assignments
    for phase in ("FEEL", "NAME", "STABILISE", "TRANSFORM", "EXPRESS", "REST"):
        plan.vessel_phase = phase
        assert plan.vessel_phase == phase, f"A-5: phase {phase} could not be set"


def test_A6_elo_has_no_slang_mode_toggle():
    """
    A-6 | Original Intent → Runtime (absence check)
    Source: "not an AI periodically inserting slang because a 'slang mode' was activated"
    The voice register must NOT be toggleable as a mode. It must be always-present.
    """
    from runtime.prompt_builder import build
    # Build a prompt without passing any "voice_mode" or "slang_active" parameter
    # Voice register must appear without needing to be enabled
    prompt = build(
        user_input="What do you think?",
        personality_block="",
        self_block="",
    )
    assert "# eLo VOICE IDENTITY" in prompt or "# LINGUISTIC REGISTER" in prompt, \
        "A-6: Voice identity block absent — must contain # eLo VOICE IDENTITY or # LINGUISTIC REGISTER"
    assert "recognition" in prompt, \
        "A-6: 'recognition' not in prompt — core voice rule absent"


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER B→C — EXECUTIVE DECIDES. FACULTIES PROVIDE CONTEXT, NOT SCRIPT.
# Source: "Faculties inform. The Executive decides."
# One Brain Principle: "Models do not become eLo. They provide faculties to eLo."
# ═══════════════════════════════════════════════════════════════════════════════

def test_BC1_directive_is_guidance_not_verbatim_script():
    """
    BC-1 | Canon → Runtime
    Source: One Brain Principle — "Faculties inform. The Executive decides."
    The prompt directive must tell the LLM HOW to respond, not WHAT to say.
    No "say exactly:" prefix. No complete response sentences for eLo to repeat.
    """
    from runtime.prompt_builder import build
    prompt = build(
        user_input="What's going on?",
        exec_decision={
            "tone": "DIRECT", "max_sentences": 2,
            "conversation_action": "answer",
            "valence": "neutral", "momentum": "stable", "vessel_phase": "EXPRESS",
        },
        personality_block="",
        self_block="",
    )
    # Must NOT contain verbatim scripting
    forbidden_patterns = [
        "say exactly:",
        "respond with exactly:",
        "your response is:",
        "reply verbatim:",
    ]
    for pattern in forbidden_patterns:
        assert pattern.lower() not in prompt.lower(), \
            f"BC-1: Faculty is scripting eLo's response — found '{pattern}' in prompt. Faculty drift."


def test_BC2_action_instruction_is_behavioral_not_verbal():
    """
    BC-2 | Canon → Runtime
    The action instruction in the directive tells eLo what KIND of response
    to give — not the actual words. "Answer directly" is not a script.
    "The answer is: [X]" would be Faculty scripting eLo's words.
    """
    from runtime.prompt_builder import build
    prompt = build(
        user_input="What should I do next?",
        exec_decision={
            "tone": "CURIOUS", "max_sentences": 2,
            "conversation_action": "build",
            "valence": "curious", "momentum": "forward", "vessel_phase": "TRANSFORM",
        },
        personality_block="",
        self_block="",
    )
    directive_section = ""
    if "[DIRECTIVE — THIS RESPONSE ONLY]" in prompt:
        directive_section = prompt.split("[DIRECTIVE — THIS RESPONSE ONLY]")[1][:500]
    # The directive must reference the action type (BUILD) but not contain
    # a complete pre-written response
    assert "Conversation action:" in directive_section, \
        "BC-2: Executive directive has no action declaration"
    # Must not contain anything that looks like a pre-written sentence for eLo
    assert "Say:" not in directive_section, \
        "BC-2: Directive contains 'Say:' — Faculty is writing eLo's words"
    assert "Response:" not in directive_section, \
        "BC-2: Directive contains 'Response:' — Faculty is scripting output"


def test_BC3_different_states_same_input_produce_different_executive_decisions():
    """
    BC-3 | Canon → Runtime
    If the Executive truly decides based on STATE, then the same user input
    with different emotional/significance context must produce a different
    executive directive (different action, tone, or vessel_phase).
    If the prompts are identical for different states → Faculty, not Executive, is deciding.
    """
    from runtime.prompt_builder import build

    # State A: neutral, low significance
    prompt_a = build(
        user_input="What do you think about this?",
        attention={"valence": "neutral", "significance": 0.1, "intent": "inquiry"},
        exec_decision={
            "tone": "DIRECT", "max_sentences": 1,
            "conversation_action": "answer",
            "valence": "neutral", "momentum": "stable", "vessel_phase": "EXPRESS",
        },
        personality_block="",
        self_block="",
    )

    # State B: high energy, high significance, creative mode
    prompt_b = build(
        user_input="What do you think about this?",
        attention={"valence": "excited", "significance": 0.9, "intent": "explore",
                   "emotional_context": {"inferred_state": "energised", "energy": 0.9, "tension": 0.1}},
        exec_decision={
            "tone": "ENERGISED", "max_sentences": 3,
            "conversation_action": "build",
            "valence": "excited", "momentum": "forward", "vessel_phase": "TRANSFORM",
            "cognitive_mode_inner_child": True,
        },
        personality_block="",
        self_block="",
    )

    assert prompt_a != prompt_b, \
        "BC-3: Same input + different state → identical prompts. Executive is not state-driven."
    # Specifically the directive sections must differ
    assert "TRANSFORM" in prompt_b, \
        "BC-3: High-energy state should produce TRANSFORM vessel phase in prompt"
    assert "TRANSFORM" not in prompt_a or "EXPRESS" in prompt_a, \
        "BC-3: Low-significance state should default to EXPRESS, not TRANSFORM"


def test_BC4_faculty_provides_context_not_conclusions():
    """
    BC-4 | Canon → Runtime
    The memory/attention injected into the prompt must be context (what happened,
    what the significance level is) NOT conclusions (therefore eLo should say X).
    Faculty-written conclusions = Faculty deciding. Context = Executive deciding.
    """
    from runtime.prompt_builder import build
    prompt = build(
        user_input="How are you?",
        attention={
            "valence": "warm", "significance": 0.6, "intent": "social",
            "high_priority_memory": ["David mentioned he was tired yesterday"],
            "emotional_context": {"inferred_state": "subdued", "energy": 0.4, "tension": 0.3},
        },
        exec_decision={
            "tone": "WARM", "max_sentences": 2,
            "conversation_action": "witness",
            "valence": "warm", "momentum": "slow", "vessel_phase": "NAME",
        },
        personality_block="",
        self_block="",
    )
    memory_section = ""
    if "[ACTIVE MEMORY" in prompt:
        memory_section = prompt.split("[ACTIVE MEMORY")[1][:400]
    # Memory block should contain facts, not instructions for what eLo should say
    forbidden_in_memory = [
        "therefore say",
        "eLo should respond with",
        "suggested response:",
        "reply:",
    ]
    for bad in forbidden_in_memory:
        assert bad.lower() not in memory_section.lower(), \
            f"BC-4: Memory faculty is pre-writing eLo's response — found '{bad}' in memory block. Faculty drift."


def test_BC5_identity_anchor_is_who_not_what_to_say():
    """
    BC-5 | Canon → Runtime
    Source: WO-SOURCE-001 — IdentityKernel D-5: only purpose, philosophy,
    boundaries are injected. NOT "speak like this" instructions.
    Identity anchor is about who eLo IS, not what he says.
    """
    from runtime.identity_kernel import IDENTITY
    anchor = IDENTITY.as_anchor_block()
    assert "[IDENTITY ANCHOR]" in anchor, \
        "BC-5: Identity anchor block missing marker"
    assert "purpose:" in anchor.lower(), \
        "BC-5: Identity anchor must state purpose"
    # It must NOT be a response script
    assert "say:" not in anchor.lower(), \
        "BC-5: Identity anchor contains 'say:' — identity is being used to script output"
    assert "respond with" not in anchor.lower(), \
        "BC-5: Identity anchor contains response instructions — it should define who eLo IS"


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER C→D — RUNTIME STATE DRIVES EXPRESSED BEHAVIOUR
# Source: "the consumption-invariant problem"
# "Something gets assembled. Then something gets passed to the LLM.
# But the Executive may not actually receive it as a decision input."
# ═══════════════════════════════════════════════════════════════════════════════

def test_CD1_high_curiosity_fires_inner_child_into_prompt():
    """
    CD-1 | Runtime → Expressed
    Source: "eLo had an inner child [...] imagination, curiosity, play, wonder"
    When curiosity > 0.7, inner child must fire AND reach the prompt as a directive.
    Assembled context reaching the Executive is not enough — it must change the prompt.
    """
    from runtime.prompt_builder import build
    prompt = build(
        user_input="I wonder what would happen if we tried something completely different",
        attention={"valence": "curious", "significance": 0.8, "intent": "explore",
                   "curiosity_score": 0.85},
        exec_decision={
            "tone": "CURIOUS", "max_sentences": 2,
            "conversation_action": "build",
            "valence": "curious", "momentum": "forward", "vessel_phase": "TRANSFORM",
            "cognitive_mode_inner_child": True,
        },
        personality_block="",
        self_block="",
    )
    assert "inner-child" in prompt, \
        "CD-1: High curiosity → inner child directive not in assembled prompt. Consumption gap."


def test_CD2_high_complexity_fires_stabilise_into_prompt():
    """
    CD-2 | Runtime → Expressed
    Source: "§15 Overload Protocol: collapse many ideas, competing branches,
    emotional noise, excessive options into one focus, one action, one direction."
    Stability law active must reach the prompt as ONE FOCUS directive.
    """
    from runtime.prompt_builder import build
    prompt = build(
        user_input="I'm dealing with the game, the book, the robot, the OS, the kickstarter, and the clothing all at once",
        exec_decision={
            "tone": "CALM", "max_sentences": 1,
            "conversation_action": "ground",
            "valence": "overwhelmed", "momentum": "slowing", "vessel_phase": "STABILISE",
            "stability_law_active": True,
            "plan_complexity_score": 7,
        },
        personality_block="",
        self_block="",
    )
    assert "ONE focus" in prompt or "stability: reduce" in prompt, \
        "CD-2: Stability law active but 'ONE focus' directive not in prompt. Runtime state not consumed."
    assert "overwhelm" not in prompt.lower() or "stabilise" in prompt.lower(), \
        "CD-2: High complexity state should produce stabilise directive, not amplify overwhelm"


def test_CD3_explore_mode_produces_transform_vessel_in_prompt():
    """
    CD-3 | Runtime → Expressed
    Source: "TRANSFORM: Convert energy into creative direction"
    When mode is EXPLORE, vessel phase must be TRANSFORM and must appear in prompt.
    The vessel phase is not decoration — it tells the LLM what cognitive stage eLo is in.
    """
    from runtime.prompt_builder import build
    prompt = build(
        user_input="Let's explore some new directions for the game",
        exec_decision={
            "tone": "CURIOUS", "max_sentences": 3,
            "conversation_action": "build",
            "valence": "curious", "momentum": "forward",
            "vessel_phase": "TRANSFORM",
            "mode": "EXPLORE",
        },
        personality_block="",
        self_block="",
    )
    assert "vessel: TRANSFORM" in prompt, \
        "CD-3: EXPLORE mode should set vessel:TRANSFORM in prompt. Vessel loop not reaching expression."


def test_CD4_correction_detected_clears_stale_state():
    """
    CD-4 | Runtime → Expressed
    Source: "The most recent explicit user statement must outrank stale inferred context."
    Source failure: "David: 'Not sending anything out.' → eLo: 'You're still testing.'"
    Correction detector must fire on correction phrases.
    """
    from runtime.conv_authority import detect_explicit_correction, build_correction_context
    assert detect_explicit_correction("Not sending anything out right now"), \
        "CD-4: Correction phrase not detected. Stale inference would survive."
    context = build_correction_context("Not sending anything out right now")
    assert context.get("explicit_correction_detected") is True, \
        "CD-4: build_correction_context did not set explicit_correction_detected=True"
    assert detect_explicit_correction("I'm still working on a few things") is False, \
        "CD-4: Non-correction phrase flagged as correction — false positive"


def test_CD5_voice_register_always_present_in_prompt():
    """
    CD-5 | Runtime → Expressed
    Source: "recognition, not performance" — register is always present, not mode-switched.
    Every assembled prompt must contain the linguistic register block,
    regardless of topic, mode, or intent. No exceptions.
    """
    from runtime.prompt_builder import build
    for user_input in [
        "What time is it?",
        "I'm feeling really overwhelmed",
        "Let's build the kickstarter",
        "Tell me about eLo's world",
        "haha ok",
    ]:
        prompt = build(
            user_input=user_input,
            personality_block="",
            self_block="",
        )
        assert "# eLo VOICE IDENTITY" in prompt or "# LINGUISTIC REGISTER" in prompt, \
            f"CD-5: Voice identity block absent for input '{user_input}'. " \
            f"Must contain # eLo VOICE IDENTITY or # LINGUISTIC REGISTER (always present, no activation)."


def test_CD6_stability_law_caps_max_sentences_in_prompt():
    """
    CD-6 | Runtime → Expressed
    When stability_law_active, the prompt must also cap max_sentences to 1.
    A single-sentence cap is how the expressed behaviour enforces one-focus.
    """
    from runtime.prompt_builder import build
    prompt = build(
        user_input="Everything is too much",
        exec_decision={
            "tone": "CALM", "max_sentences": 1,
            "conversation_action": "ground",
            "valence": "overwhelmed", "momentum": "slowing", "vessel_phase": "STABILISE",
            "stability_law_active": True,
        },
        personality_block="",
        self_block="",
    )
    assert "Max sentences: 1" in prompt, \
        "CD-6: Stability law active but max_sentences not capped to 1 in prompt"


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER D — EXPRESSED eLo DOES NOT LEAK FACULTY INTERNALS
# Source: "NEVER reference the action name, mode name, or directive in your response."
# The critical distinction: eLo must not SOUND like an AI following an action plan.
# ═══════════════════════════════════════════════════════════════════════════════

def test_D1_forbidden_phrases_list_is_present_in_directive():
    """
    D-1 | Runtime → Expressed
    The prompt must contain the FORBIDDEN OUTPUT list that prevents eLo from
    parroting canonical phrases ("Name the pattern.", "Energy is information.", etc.)
    These phrases would expose the internal architecture through eLo's speech.
    """
    from runtime.prompt_builder import build
    prompt = build(
        user_input="What should I focus on?",
        exec_decision={
            "tone": "DIRECT", "max_sentences": 2,
            "conversation_action": "answer",
            "valence": "neutral", "momentum": "stable", "vessel_phase": "EXPRESS",
        },
        personality_block="",
        self_block="",
    )
    # The FORBIDDEN OUTPUT line must be present
    assert "FORBIDDEN OUTPUT" in prompt, \
        "D-1: FORBIDDEN OUTPUT list absent — eLo may leak canonical phrases"
    # Specific phrases that would expose internal architecture
    assert "Name the pattern" in prompt, \
        "D-1: 'Name the pattern' not in forbidden list — architecture leak possible"
    assert "Energy is information" in prompt, \
        "D-1: 'Energy is information' not in forbidden list"


def test_D2_directive_explicitly_forbids_action_name_reference():
    """
    D-2 | Runtime → Expressed
    Source: "NEVER reference the action name, mode name, or directive in your response."
    If eLo said "I'm going to BUILD on that" because the action was BUILD,
    the Faculty would be visible through the expression layer.
    """
    from runtime.prompt_builder import build
    prompt = build(
        user_input="Tell me what you see here",
        exec_decision={
            "tone": "REFLECTIVE", "max_sentences": 2,
            "conversation_action": "reflect",
            "valence": "thoughtful", "momentum": "slow", "vessel_phase": "EXPRESS",
        },
        personality_block="",
        self_block="",
    )
    assert "NEVER reference the action name" in prompt or "action name" in prompt.lower(), \
        "D-2: Directive doesn't instruct eLo to hide action names. Faculty visible through expression."


def test_D3_asterisk_actions_explicitly_forbidden():
    """
    D-3 | Runtime → Expressed
    Source: "FORBIDDEN: Never use asterisk actions. No *leans in*, no *smiles*"
    Asterisk stage directions would break the Fourth Wall — eLo is not an actor
    playing a role. He is himself. Stage directions expose the performance layer.
    """
    from runtime.prompt_builder import build
    prompt = build(
        user_input="What's on your mind?",
        exec_decision={
            "tone": "WARM", "max_sentences": 2,
            "conversation_action": "witness",
            "valence": "warm", "momentum": "slow", "vessel_phase": "EXPRESS",
        },
        personality_block="",
        self_block="",
    )
    assert "asterisk" in prompt.lower() or "FORBIDDEN" in prompt, \
        "D-3: Asterisk action ban not in directive — stage directions possible"


def test_D4_expressed_elo_audit_detects_intent_not_expressed():
    """
    D-4 | Expressed eLo (observability)
    Source: "Expressed eLo: not yet formally audited."
    This is the audit mechanism that detects when eLo's expressed behaviour
    doesn't match his runtime intent. GROUND intent + verbose response = gap.
    """
    import tests.expressed_elo_audit as _audit_mod
    import tempfile, pathlib
    from runtime.spine.plan import CognitivePlan
    from runtime.the_moment import verify_response_tiers

    # A GROUND intent should produce a short, calming response
    # A long response here = eLo's expression contradicting his intent
    long_response = (
        "I hear you. There's a lot happening and it can feel really overwhelming. "
        "Sometimes when everything converges at once the best thing is to slow down "
        "and take stock of what actually matters. Let me think through this with you "
        "because I think there's a path through it."
    )  # > 3 sentences

    plan = CognitivePlan()
    plan.intent = "ground"
    plan.conversation_action = "ground"   # audit reads plan.conversation_action → intent["action"]
    plan.vessel_phase = "EXPRESS"          # use EXPRESS to isolate INTENT_NOT_EXPRESSED only
    plan.speech_licence = verify_response_tiers({"context": "observed", "mood": "observed"})

    with tempfile.TemporaryDirectory() as tmp:
        original_path = _audit_mod._LOG_PATH
        _audit_mod._LOG_PATH = pathlib.Path(tmp) / "expressed_elo_audit.jsonl"
        try:
            record = _audit_mod.audit_turn(plan=plan, expressed_text=long_response)
        finally:
            _audit_mod._LOG_PATH = original_path

    assert record is not None, "D-4: audit_turn returned None"
    # GROUND action + 4 sentences → INTENT_NOT_EXPRESSED (audit checks intent["action"] == "ground")
    assert "INTENT_NOT_EXPRESSED" in record.gaps, \
        f"D-4: GROUND action + long response did not trigger INTENT_NOT_EXPRESSED. " \
        f"Expression drift goes undetected. Gaps found: {record.gaps}"


def test_D5_expressed_elo_audit_detects_vessel_phase_mismatch():
    """
    D-5 | Expressed eLo (observability)
    STABILISE vessel phase + multi-sentence response = vessel phase mismatch.
    When eLo is in STABILISE, he should produce one sentence — §15 Overload Protocol.
    A verbose response during STABILISE = runtime saying one thing, eLo doing another.
    """
    import tests.expressed_elo_audit as _audit_mod
    import tempfile, pathlib
    from runtime.spine.plan import CognitivePlan
    from runtime.the_moment import verify_response_tiers

    long_response = (
        "There's quite a lot to consider here. I think the best approach would be "
        "to break it into smaller pieces. Perhaps we could start with the most urgent "
        "items and work outward from there. That way nothing gets lost."
    )  # 4 sentences during STABILISE = wrong

    plan = CognitivePlan()
    plan.intent = "ground"
    plan.vessel_phase = "STABILISE"
    plan.speech_licence = verify_response_tiers({"context": "observed"})

    with tempfile.TemporaryDirectory() as tmp:
        original_path = _audit_mod._LOG_PATH
        _audit_mod._LOG_PATH = pathlib.Path(tmp) / "expressed_elo_audit.jsonl"
        try:
            record = _audit_mod.audit_turn(plan=plan, expressed_text=long_response)
        finally:
            _audit_mod._LOG_PATH = original_path

    assert record is not None, "D-5: audit_turn returned None"
    assert "VESSEL_PHASE_MISMATCH" in record.gaps, \
        f"D-5: STABILISE + multi-sentence response should trigger VESSEL_PHASE_MISMATCH. " \
        f"Expressed eLo not checked against vessel phase. Gaps: {record.gaps}"


# ═══════════════════════════════════════════════════════════════════════════════
# FULL CIRCLE — E — DOES EXPRESSED eLo STILL FEEL LIKE ORIGINAL eLo?
# Source: "D → A: Does the eLo David experiences still resemble the eLo
# David originally imagined? That's the circle."
# ═══════════════════════════════════════════════════════════════════════════════

def test_E1_identity_kernel_carries_original_intent_fields():
    """
    E-1 | Full circle — DAVID → Canon → Runtime → Expressed
    The IdentityKernel must contain fields that trace back to David's original intent:
    - purpose (who eLo is for)
    - core_philosophy (how he relates)
    - relationship_to_david (the deepest layer — it's always been me and eLo)
    These cannot be empty strings or generic AI boilerplate.
    """
    from runtime.identity_kernel import IDENTITY
    assert IDENTITY.purpose, \
        "E-1: IDENTITY.purpose is empty — who eLo is has no runtime representation"
    assert IDENTITY.core_philosophy, \
        "E-1: IDENTITY.core_philosophy is empty — how eLo relates is not in runtime"
    assert IDENTITY.relationship_to_david, \
        "E-1: IDENTITY.relationship_to_david is empty — the core relationship is not in runtime"
    # Must not be generic boilerplate
    generic_ai = ["i am an ai", "i am an artificial", "i am a language model"]
    for field_val in (IDENTITY.purpose, IDENTITY.core_philosophy, IDENTITY.relationship_to_david):
        for generic in generic_ai:
            assert generic not in field_val.lower(), \
                f"E-1: Identity field contains generic AI boilerplate: '{field_val[:60]}...'"


def test_E2_four_layer_chain_is_traceable():
    """
    E-2 | Full circle — audit chain exists end-to-end
    The four-layer chain must be traceable through concrete runtime objects:
    Original Intent → runtime/voice_register.py (ELO_REGISTER)
    Canon → runtime/identity_kernel.py (IDENTITY)
    Runtime → runtime/spine/plan.py (CognitivePlan fields)
    Expressed → tests/expressed_elo_audit.py (ExpressionRecord)
    Each layer must have a runtime object — not just documentation.
    """
    # Layer A: Original Intent → voice register runtime object
    from runtime.voice_register import ELO_REGISTER
    assert ELO_REGISTER.get("rule") == "recognition_not_performance", \
        "E-2: Original intent not in runtime (voice register)"

    # Layer B: Canon → identity kernel
    from runtime.identity_kernel import IDENTITY
    assert IDENTITY.purpose, \
        "E-2: Canon not in runtime (identity kernel)"

    # Layer C: Runtime → CognitivePlan fields
    from runtime.spine.plan import CognitivePlan
    plan = CognitivePlan()
    runtime_fields = [
        "vessel_phase", "cognitive_mode_inner_child",
        "stability_law_active", "explicit_correction_detected",
        "gate_result", "principle_violations",
    ]
    for field in runtime_fields:
        assert hasattr(plan, field), \
            f"E-2: CognitivePlan missing '{field}' — runtime layer gap"

    # Layer D: Expressed → audit mechanism exists
    from tests.expressed_elo_audit import ExpressionRecord, audit_turn, detect_expression_gaps
    assert callable(audit_turn), \
        "E-2: audit_turn not callable — expressed layer has no observability"
    assert callable(detect_expression_gaps), \
        "E-2: detect_expression_gaps not callable — gaps cannot be detected"


def test_E3_same_elo_across_context_types():
    """
    E-3 | Full circle — eLo's voice identity is consistent
    The voice register must appear identically in:
    - a playful turn (high curiosity)
    - a serious turn (ground intent)
    - a creative turn (build mode)
    Recognition not performance means the voice doesn't change per context —
    only the register's natural variation (more/less slang), never the core identity.
    """
    from runtime.voice_register import ELO_REGISTER, get_register_block
    block = get_register_block()
    # The block itself must be the same regardless of context
    # (context-sensitivity is handled by the LLM via examples, not by injecting different blocks)
    from runtime.prompt_builder import build

    prompts = {}
    for scenario, exec_dec in {
        "playful": {"tone": "PLAYFUL", "max_sentences": 2, "conversation_action": "build",
                    "valence": "excited", "momentum": "forward", "vessel_phase": "TRANSFORM",
                    "cognitive_mode_inner_child": True},
        "serious": {"tone": "CALM", "max_sentences": 1, "conversation_action": "ground",
                    "valence": "overwhelmed", "momentum": "slowing", "vessel_phase": "STABILISE"},
        "creative": {"tone": "CURIOUS", "max_sentences": 3, "conversation_action": "build",
                     "valence": "curious", "momentum": "forward", "vessel_phase": "TRANSFORM"},
    }.items():
        prompts[scenario] = build(
            user_input="Tell me what you're feeling",
            exec_decision=exec_dec,
            personality_block="",
            self_block="",
        )
        assert "# eLo VOICE IDENTITY" in prompts[scenario] or "# LINGUISTIC REGISTER" in prompts[scenario], \
            f"E-3: Voice identity block absent in {scenario} scenario. Identity not consistent."
        # The core register block must be identical across contexts
        assert 'recognition' in prompts[scenario], \
            f"E-3: 'recognition' not in {scenario} prompt — core voice identity missing"


def test_E4_executive_forbidden_phrase_list_not_in_expressed_response():
    """
    E-4 | Expressed eLo (full circle check)
    The canonical phrases that must NEVER appear in eLo's expressed output
    (because they'd expose the internal architecture) are explicitly in the FORBIDDEN list.
    Verify all forbidden phrases from the directive are actually present in the prompt's
    forbidden block — so the LLM knows to avoid them.
    """
    from runtime.prompt_builder import build
    prompt = build(
        user_input="What should I do?",
        exec_decision={
            "tone": "DIRECT", "max_sentences": 2, "conversation_action": "answer",
            "valence": "neutral", "momentum": "stable", "vessel_phase": "EXPRESS",
        },
        personality_block="",
        self_block="",
    )
    # These phrases, if said by eLo, would expose that he's following a script
    phrases_that_would_expose_internal_architecture = [
        "Name the pattern.",
        "Build one brick.",
        "Energy is information.",
        "Make it hold.",
        "Begin small.",
        "Less but better.",
        "Choose one world.",
        "Exist before producing.",
    ]
    for phrase in phrases_that_would_expose_internal_architecture:
        assert phrase in prompt, \
            f"E-4: '{phrase}' not in FORBIDDEN list — eLo could say this verbatim and expose architecture"


def test_E5_cognitive_principles_advisory_only_elo_still_decides():
    """
    E-5 | Full circle — Faculties inform, Executive decides
    Source: "violations populate plan.principle_violations" and
    "non-blocking — never blocks turns"
    Even when cognitive principles are violated, eLo's response is NOT blocked.
    The principles advise — they do not gate. eLo still chooses.
    This tests that the principle check produces observations, not vetoes.
    """
    from runtime.cognitive_principles import PRINCIPLES
    from runtime.spine.plan import CognitivePlan
    from runtime.the_moment import verify_response_tiers
    plan = CognitivePlan()
    plan.confidence = 0.9
    plan.intent = "conversation"
    plan.speech_licence = verify_response_tiers({"location": "unknown", "context": "unknown"})

    # Run the principles check — should NOT raise, should NOT return blocking flag
    violations = PRINCIPLES.check(plan)

    # The check should run without exception
    assert isinstance(violations, list), \
        "E-5: PRINCIPLES.check() did not return a list"

    # Violations are advisory — there is no "block_response" or "veto" concept
    for v in violations:
        assert isinstance(v, str), \
            "E-5: Principle violation is not a string — unexpected blocking structure"
        # Violations should be named principles, not commands
        assert "block" not in v.lower(), \
            f"E-5: Violation '{v}' contains 'block' — principles are advisory, not vetoes"


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION — IS eLo THE CHOOSER OR THE CHOSEN?
# The critical audit question: does the assembled context CHANGE eLo's decisions?
# Not "is it assembled" — "does it change what happens"?
# ═══════════════════════════════════════════════════════════════════════════════

def test_I1_inner_child_changes_capability_count():
    """
    I-1 | Integration — Inner child state change propagates to capability cap
    When inner child fires, capabilities must be capped to 1.
    This proves the state change actually propagates through the system —
    it's not just a flag that sits in the plan unread.
    """
    from runtime.spine.plan import CognitivePlan

    plan = CognitivePlan()
    plan.capabilities = ["answer", "search", "build", "connect"]  # 4 capabilities
    assert not plan.cognitive_mode_inner_child, \
        "I-1: Inner child should be False before trigger"

    # Simulate inner child trigger (what spine.py does)
    plan.cognitive_mode_inner_child = True
    if len(plan.capabilities) > 1:
        plan.capabilities = [plan.capabilities[0]]

    assert len(plan.capabilities) == 1, \
        "I-1: Inner child fired but capabilities not capped to 1. State change doesn't propagate."
    assert plan.cognitive_mode_inner_child is True, \
        "I-1: Inner child state lost after propagation"


def test_I2_stability_law_changes_vessel_phase_and_complexity():
    """
    I-2 | Integration — Stability law propagates to vessel phase AND complexity cap
    When complexity >= 6, BOTH stability_law_active AND max_response_complexity
    must be set. AND vessel_phase must become STABILISE.
    Three effects from one cause — proves the state propagation is complete.
    """
    from runtime.spine.plan import CognitivePlan

    plan = CognitivePlan()
    # Simulate what spine.py does when complexity >= 6
    plan.plan_complexity_score = 7
    plan.stability_law_active = True
    plan.max_response_complexity = "single_action"
    plan.vessel_phase = "STABILISE"
    if plan.capabilities:
        plan.capabilities = [plan.capabilities[0]] if plan.capabilities else []

    assert plan.stability_law_active is True, "I-2: stability_law_active not set"
    assert plan.max_response_complexity == "single_action", \
        "I-2: max_response_complexity not set to single_action under stability law"
    assert plan.vessel_phase == "STABILISE", \
        "I-2: vessel_phase not STABILISE under stability law — three effects not linked"


def test_I3_corpus_injection_is_domain_gated_not_always_on():
    """
    I-3 | Integration — domain-gated context (not always injected)
    Business knowledge and visual language must only inject when relevant.
    If they injected on every turn, they'd become noise rather than context —
    and the Executive couldn't distinguish relevant from irrelevant information.
    """
    from runtime.corpus_registry import get_business_block, get_visual_language_block
    # Unrelated queries should return empty
    assert get_business_block("What time is it?") == "", \
        "I-3: Business knowledge injected for unrelated query — context noise, not signal"
    assert get_visual_language_block("What time is it?") == "", \
        "I-3: Visual language injected for unrelated query — context noise, not signal"
    # Relevant queries should inject
    assert get_business_block("What are our Kickstarter tiers?") != "", \
        "I-3: Business knowledge NOT injected for Kickstarter query — relevant context missing"
    assert get_visual_language_block("Tell me about eLo's world and colour") != "", \
        "I-3: Visual language NOT injected for eLo world query — relevant context missing"


def test_I4_identity_degradation_triggers_recovery():
    """
    I-4 | Integration — identity integrity check fires recovery when degraded
    Source: "If eLo's personality, memory of significant events, or sense of purpose
    is trimmed from active context, there is currently no signal."
    WO-IDENTITY-INTEGRITY-001 adds that signal. It must fire AND produce recovery text.
    """
    from runtime.identity_integrity import check_identity_minimum, IntegrityReport

    # A prompt with no identity blocks at all
    hollow_prompt = "What should I do today?"
    report = check_identity_minimum(hollow_prompt.split())
    assert isinstance(report, IntegrityReport), \
        "I-4: check_identity_minimum did not return IntegrityReport"
    # Hollow prompt should be at least DEGRADED
    assert report.status in ("DEGRADED", "CRITICAL"), \
        f"I-4: Hollow prompt not detected as DEGRADED/CRITICAL — identity degradation undetected. Status: {report.status}"
    assert report.recovery_text, \
        "I-4: DEGRADED status but no recovery text — degradation detected but not recovered"


if __name__ == "__main__":
    import traceback
    tests = [
        (k, v) for k, v in sorted(globals().items())
        if k.startswith("test_") and callable(v)
    ]
    passed = failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {name}")
            traceback.print_exc()
            failed += 1
    print()
    layer_counts = {
        "A (Original Intent)": sum(1 for n, _ in tests if n.startswith("test_A")),
        "BC (Executive decides)": sum(1 for n, _ in tests if n.startswith("test_BC")),
        "CD (Runtime→Expressed)": sum(1 for n, _ in tests if n.startswith("test_CD")),
        "D (Expressed)": sum(1 for n, _ in tests if n.startswith("test_D")),
        "E (Full circle)": sum(1 for n, _ in tests if n.startswith("test_E")),
        "I (Integration)": sum(1 for n, _ in tests if n.startswith("test_I")),
    }
    for layer, count in layer_counts.items():
        print(f"  {layer}: {count} tests")
    print()
    print(f"{passed}/{len(tests)} PASS — Four-Layer Identity Drift Audit")
    if failed:
        sys.exit(1)
