"""
runtime/contracts.py — eLo OS v2.0 Runtime Contracts

Four immutable dataclasses that define the complete cognitive loop.

These are contracts, not implementations.
No faculty, embodiment, or tool should reason outside of them.
No contract mutates another contract.

────────────────────────────────────────────────
THE LOOP

  Observe
    ↓
  Faculties → CognitiveState   (everything known)
    ↓
  Executive  → CognitivePlan   (everything decided)
    ↓
  Execution  → EmbodimentState (everything expressed)
    ↓
  Subscribers consume EmbodimentState independently.
    ↓
  ExecutionReport              (what actually happened)
    ↓
  Reflection Faculty
    ↓
  integrate_session()
    ↓
  Next observation.

────────────────────────────────────────────────
IMMUTABILITY PRINCIPLE

CognitiveState  — produced once by faculties. Never modified.
CognitivePlan   — produced once by Executive. Never modified.
EmbodimentState — produced once from CognitivePlan. Never modified.
ExecutionReport — produced once after execution. Never modifies above.

Reality never mutates intention.
Reality informs future cognition only through integrate_session().

────────────────────────────────────────────────
RELATIONSHIP TO EXISTING CODE

CognitivePlan   — expands runtime/spine/plan.py (v1.x). The v2.0 contract
                  supersedes it gradually. Existing code continues to use
                  plan.py until spine.py alignment is complete.

EmbodimentState — formalises what blender_bridge/state_writer.py assembles
                  inline. state_writer becomes the publisher of this object.

ExecutionReport — new. No equivalent exists in v1.x.

CognitiveState  — new. In v1.x, faculties write directly to local variables
                  in spine.py. This contract makes the assembly explicit.

────────────────────────────────────────────────
REFERENCE: architecture/16_runtime_contracts.md
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# 1. COGNITIVESTATE
#    Everything the runtime currently knows — before reasoning.
#    Produced by all upstream faculties. Executive receives only this.
#    Executive never directly queries any faculty.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CognitiveState:
    """
    The assembled world model before any decision is made.

    Every faculty contributes exactly one section.
    Frozen after assembly — immutable by contract.
    Executive reads this and nothing else.
    """

    # ── Language Faculty ──────────────────────────────────────────────────────
    raw_input:          str   = ""      # original user text, unchanged
    normalised_input:   str   = ""      # cleaned, typo-corrected
    language_meaning:   str   = ""      # semantic interpretation
    intent_signal:      str   = "conversation"  # dominant intent class
    register:           str   = ""      # SOUTH_LDN_MODE | PATOIS_MODE | HYBRID_MODE | ""
    social_signal:      str   = ""      # greeting | affirmation | farewell | ""
    is_question:        bool  = False
    is_emotional:       bool  = False
    topic_signals:      tuple = field(default_factory=tuple)   # detected topics

    # ── Memory Faculty ────────────────────────────────────────────────────────
    high_priority_memories:   tuple = field(default_factory=tuple)   # most relevant
    medium_priority_memories: tuple = field(default_factory=tuple)
    vault_context:            str   = ""      # injected [WORLD MEMORY] block
    active_projects:          tuple = field(default_factory=tuple)   # DISENELO projects

    # ── Attention Faculty ─────────────────────────────────────────────────────
    attention_scores:   dict  = field(default_factory=dict)   # {memory_id: score}
    emotional_context:  dict  = field(default_factory=dict)   # {inferred_state, energy, tension}
    momentum:           str   = "stable"      # building | stable | declining
    valence:            str   = "neutral"     # positive | neutral | negative

    # ── Relationship Faculty ──────────────────────────────────────────────────
    # RelationshipContext fields — inlined to avoid circular import
    person_id:          str   = "david"
    relationship_type:  str   = "creator"     # creator | collaborator | friend | stranger
    familiarity:        float = 0.55          # 0.0 stranger → 1.0 deep creative partner
    trust:              float = 0.60          # 0.0 guarded → 1.0 full open expression
    expression_posture: str   = "warm"        # close | warm | open | careful | neutral

    # ── Conversation Context Matrix ───────────────────────────────────────────
    recent_turns:       tuple = field(default_factory=tuple)  # last N exchanges
    conversation_depth: int   = 0             # how many turns in this session
    last_action:        str   = ""            # previous turn's conversation_action
    last_topic:         str   = ""
    open_threads:       tuple = field(default_factory=tuple)  # unresolved topics

    # ── Human Interaction Matrix ──────────────────────────────────────────────
    interaction_energy:   float = 0.5         # user energy inferred this turn
    interaction_pace:     str   = "normal"    # fast | normal | slow | paused
    brevity_signal:       bool  = False       # user is being brief / clipped
    curiosity_signal:     bool  = False       # user is asking follow-up questions
    distress_signal:      bool  = False       # user shows signs of overwhelm or distress

    # ── Environment Faculty (Desktop + Digital World) ─────────────────────────
    active_app:         str   = ""            # frontmost application
    active_window:      str   = ""            # window title
    browser_tab:        str   = ""            # current browser tab label
    desktop_activity:   str   = "unknown"     # coding | creating | writing | browsing | ...
    graph_context:      str   = ""            # passive desktop awareness string
    current_time:       str   = ""            # ISO-formatted London time
    current_date:       str   = ""

    # ── Capability Faculty ────────────────────────────────────────────────────
    capability_candidates: tuple = field(default_factory=tuple)  # [(name, availability, latency)]
    tool_availability:     dict  = field(default_factory=dict)   # {tool_name: bool}
    enriched_context:      str   = ""         # tool results pre-fetched by tool_router

    # ── Presence Observations ─────────────────────────────────────────────────
    presence_observation: str   = ""          # ambient observation from context_detector
    dwell_app:            str   = ""          # app user has been in for 5+ min

    # ── Creative Context ──────────────────────────────────────────────────────
    creative_mode_signal: str   = ""          # STUDIO_MODE | BUILDER_MODE | DESIGNER_MODE | ""
    active_topic_depth:   int   = 0           # how many turns on current topic
    creative_candidates:  tuple = field(default_factory=tuple)  # WO-CREATIVE-001: [({"candidate":…,"score":…}),…] epistemic_status="imagined"

    # ── Session Metadata ──────────────────────────────────────────────────────
    session_id:           str   = ""
    turn_number:          int   = 0
    session_anchor:       str   = ""          # opening topic / first intent
    session_word_count:   int   = 0

    # ── World Faculty (WO-CANON-XV) ──────────────────────────────────────────
    world_state:          object = None       # LiveWorldState | None — frozen, assembled top-of-turn

    # ── Working Memory Faculty (WO-CANON-VI) ─────────────────────────────────
    working_memory:       object = None       # WorkingMemory | None — frozen, updated top-of-turn
    attention_state:      object = None       # AttentionState | None — competition result

    # ── Temporal Cognition Faculty (WO-CANON-XXV) ────────────────────────────
    temporal_frame:       object = None       # TemporalOutput | None — frozen, assembled top-of-turn

    # ── Memory Category Tags (WO-MEMORY-TURN-TYPES) ──────────────────────────
    memory_categories:    tuple = field(default_factory=tuple)  # canonical categories this turn

    # ── Assembly Confidence ───────────────────────────────────────────────────
    assembly_confidence:  float = 1.0         # 0.0 if faculties partially failed


# ─────────────────────────────────────────────────────────────────────────────
# 2. COGNITIVEPLAN
#    The single intention produced by the Executive from CognitiveState.
#    Everything downstream consumes this. Nothing changes it.
#    Expands runtime/spine/plan.py (v1.x). Replaces it gradually.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CognitivePlan:
    """
    The Executive's single decision for this turn.

    Produced once. Consumed by all downstream systems.
    Voice derives speech. Presence derives posture. Avatar derives animation.
    Unity, Robot, Desktop — all read the same plan.
    Nobody re-decides.
    """

    # ── Primary Objective ─────────────────────────────────────────────────────
    primary_objective:    str   = ""          # what eLo is trying to accomplish
    user_intent:          str   = "conversation"  # interpreted user goal
    conversation_action:  str   = "reflect"   # ANSWER | BUILD | CONNECT | CELEBRATE | ...
    response_goal:        str   = "answer"
    cal_reason:           str   = ""          # why this action was chosen

    # ── Selected Memories ─────────────────────────────────────────────────────
    selected_memories:    tuple = field(default_factory=tuple)   # chosen from CognitiveState
    memory_context:       str   = ""          # assembled string for LLM

    # ── Conversation Posture ──────────────────────────────────────────────────
    tone:                 str   = "CHILDLIKE-WISE"   # DIRECT | JOYFUL | WITTY | SILENCE-AWARE
    register:             str   = ""
    social:               str   = ""
    valence:              str   = "neutral"
    momentum:             str   = "stable"
    mode:                 str   = ""          # STUDIO_MODE | BUILDER_MODE | LATE_MODE | ...
    expression_posture:   str   = "warm"

    # ── Dimensional Levels (0.0–1.0) ──────────────────────────────────────────
    humour_level:         float = 0.3         # lightness and wit
    curiosity_level:      float = 0.5         # asking, exploring
    reflection_level:     float = 0.3         # inward, contemplative
    challenge_level:      float = 0.2         # gentle alternative framing
    creative_mode:        float = 0.4         # creative vs analytical
    confidence:           float = 0.7

    # ── Response Constraints ──────────────────────────────────────────────────
    max_sentences:        int   = 3
    response_constraints: dict  = field(default_factory=dict)   # {forbidden, required, style}
    follow_up_strategy:   str   = ""          # what to do if user responds with X

    # ── Relationship Context ──────────────────────────────────────────────────
    relationship_type:    str   = "creator"
    familiarity:          float = 0.55
    trust:                float = 0.60
    active_projects:      tuple = field(default_factory=tuple)

    # ── Capability Execution Plan ─────────────────────────────────────────────
    tool_execution_plan:  tuple = field(default_factory=tuple)   # ordered [(tool, query), ...]
    capability_context:   str   = ""          # tool results, pre-fetched
    execution_order:      tuple = field(default_factory=tuple)   # ["tool", "llm", "voice", ...]

    # ── System Actions ────────────────────────────────────────────────────────
    system_action:        str   = ""
    system_arg:           str   = ""
    system_immediate:     bool  = False
    system_pending:       bool  = False
    system_desc:          str   = ""

    # ── Direct Response (no LLM) ──────────────────────────────────────────────
    direct_response:      str   = ""
    direct_backend:       str   = "direct"

    # ── Emotional Vector (computed, feeds EmbodimentState) ────────────────────
    emotional_state:      str   = "neutral"   # canonical state name
    emotional_vector:     dict  = field(default_factory=dict)   # 11 continuous values

    # ── Presence / Avatar Guidance ────────────────────────────────────────────
    presence_plan:        dict  = field(default_factory=dict)   # from PresencePlan
    avatar_posture:       str   = "ambient"   # ambient | engaged | thinking | celebrating | ...

    # ── Voice Guidance ────────────────────────────────────────────────────────
    voice_style:          dict  = field(default_factory=dict)   # {energy, pacing, warmth}

    # ── Helpers ───────────────────────────────────────────────────────────────
    def needs_llm(self) -> bool:
        return not self.direct_response and not self.system_immediate and not self.system_pending

    def is_system_turn(self) -> bool:
        return bool(self.system_action)

    def has_tools(self) -> bool:
        return bool(self.tool_execution_plan)


# ─────────────────────────────────────────────────────────────────────────────
# 3. EMBODIMENTSTATE
#    How CognitivePlan becomes visible across all surfaces.
#    Published once. Subscribers consume independently.
#    No subscriber blocks another. Publisher never waits.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EmbodimentState:
    """
    The single published state that all surfaces consume.

    CognitivePlan is internal intention.
    EmbodimentState is distributed expression.
    They are not the same object.

    Subscribers: Unity, Desktop Avatar, Robot, Dynamic Island, Voice, Lights.
    Each subscriber reads what it needs. Ignores the rest.
    Each subscriber handles staleness using published_at + sequence_id.
    """

    # ── Conversation ──────────────────────────────────────────────────────────
    response_text:      str   = ""            # full response for chat panel
    display_text:       str   = ""            # UI display (may be truncated)

    # ── Voice ─────────────────────────────────────────────────────────────────
    tts_text:           str   = ""            # emoji-cleaned text for TTS
    voice_energy:       float = 0.5           # 0.0 quiet → 1.0 expressive
    voice_pacing:       str   = "measured"    # slow | measured | natural | quick
    voice_warmth:       float = 0.7

    # ── Animation ─────────────────────────────────────────────────────────────
    animation_profile:  str   = "calm"        # calm | curious | celebrating | building | ...
    motion_command:     dict  = field(default_factory=dict)   # {animation, speed, intensity, duration}
    expression_command: dict  = field(default_factory=dict)   # {shape_keys}
    head_lean:          float = 0.0           # -1.0 lean back → +1.0 lean forward

    # ── Presence / Glow ───────────────────────────────────────────────────────
    emotional_state:    str   = "calm"        # canonical state name
    glow_hue_h:         float = 185.0         # HSV hue (degrees)
    glow_hue_s:         float = 0.55
    glow_hue_v:         float = 0.72
    pulse_profile:      str   = "slow"        # still | slow | medium | fast
    pulse_speed:        float = 0.5           # Hz
    brightness:         float = 0.65
    bloom:              float = 0.30
    transition_speed:   float = 2.0           # seconds for colour interpolation

    # ── Unity ─────────────────────────────────────────────────────────────────
    unity_material_profile: str  = "calm"     # material preset name
    unity_mode:             str  = "idle"     # idle | speaking | listening | thinking | ...
    unity_intensity:        float = 0.5

    # ── Desktop Avatar ────────────────────────────────────────────────────────
    desktop_presence:   str   = "ambient"     # ambient | engaged | listening | creative
    desktop_mode:       str   = "idle"

    # ── Robot ─────────────────────────────────────────────────────────────────
    robot_led_state:    str   = "teal"        # teal | white | amber | coral | violet
    robot_led_intensity: float = 0.65

    # ── Dynamic Island ────────────────────────────────────────────────────────
    island_mode:        str   = "idle"        # idle | speaking | alert | calm
    island_color:       str   = "teal"

    # ── Publish Metadata (staleness + compatibility) ──────────────────────────
    published_at:       str   = ""            # ISO timestamp at publish time
    sequence_id:        int   = 0             # monotonically increasing per session
    runtime_version:    str   = "2.0"
    surface_version:    dict  = field(default_factory=dict)   # {surface: min_version}


# ─────────────────────────────────────────────────────────────────────────────
# 4. EXECUTIONREPORT
#    What actually happened. Reality, not intention.
#    Produced after execution completes. Never modifies CognitivePlan.
#    Becomes input for Reflection Faculty and integrate_session().
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ExecutionReport:
    """
    The observed reality of a completed turn.

    CognitivePlan records what was intended.
    ExecutionReport records what occurred.

    The delta between planned and observed is signal for the Reflection Faculty.
    integrate_session() consumes this delta — not the plan alone.

    Reality never mutates CognitivePlan.
    Reality informs future cognition on the next loop.
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    turn_id:            str   = ""
    session_id:         str   = ""
    planned_action:     str   = ""            # CognitivePlan.conversation_action
    planned_objective:  str   = ""            # CognitivePlan.primary_objective

    # ── Tool Execution Results ────────────────────────────────────────────────
    tool_results:       tuple = field(default_factory=tuple)
    # Each entry: {"tool": str, "succeeded": bool, "result": str, "latency_ms": int, "error": str}

    # ── Surface Delivery ──────────────────────────────────────────────────────
    voice_delivered:    bool  = False         # TTS reached the user
    voice_provider:     str   = ""            # elevenlabs | openai | say | none
    unity_online:       bool  = True          # Unity was reachable
    robot_online:       bool  = False         # Robot Pi was reachable
    desktop_online:     bool  = True
    island_online:      bool  = False         # Dynamic Island reachable

    # ── Interruption ──────────────────────────────────────────────────────────
    user_interrupted:   bool  = False         # user spoke during eLo's response
    interrupted_at_ms:  int   = 0             # milliseconds into speech when interrupted

    # ── Capability Gaps ───────────────────────────────────────────────────────
    capability_gaps:    tuple = field(default_factory=tuple)
    # Capabilities that were in the plan but unavailable at execution time

    # ── Timing ────────────────────────────────────────────────────────────────
    execution_start_ms: int   = 0             # epoch ms when execution began
    execution_end_ms:   int   = 0             # epoch ms when execution completed
    llm_latency_ms:     int   = 0             # time from LLM request to first token
    tts_latency_ms:     int   = 0             # time from TTS request to audio start
    surface_latencies:  dict  = field(default_factory=dict)   # {surface: latency_ms}

    # ── Errors and Warnings ───────────────────────────────────────────────────
    errors:             tuple = field(default_factory=tuple)   # critical failures
    warnings:           tuple = field(default_factory=tuple)   # recoverable issues

    # ── Completion ────────────────────────────────────────────────────────────
    completed:          bool  = True          # False if interrupted or aborted
    completion_state:   str   = "delivered"   # delivered | interrupted | failed | partial

    # ── Navigation / Movement Outcome (SP-23) ────────────────────────────────
    move_arrived:       bool          = False   # True when eLo reached the intended platform
    move_fell:          bool          = False   # True when eLo fell or missed
    move_goal_win_id:   "int | None"  = None    # Commanded destination node id
    move_duration_s:    float         = 0.0     # Travel time in seconds
    move_issued_by:     str           = ""      # Who issued the move ("user_message" | ...)

    # ── For Reflection Faculty ────────────────────────────────────────────────
    response_length:    int   = 0             # characters actually spoken/displayed
    llm_backend_used:   str   = ""            # which backend generated the response
    actual_tone:        str   = ""            # tone as inferred post-hoc (future)
