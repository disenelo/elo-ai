"""
runtime/contracts.py — eLo OS v2.0 Runtime Contracts

Four immutable dataclasses that define the complete cognitive loop.

These are contracts, not implementations.
No faculty, embodiment, or tool should reason outside of them.
No contract mutates another contract.

────────────────────────────────────────────────
THE COGNITIVE CHAIN (canonical, Four-Layer Identity Model 2026-08-31)

  PERCEPTION   — raw input arrives
    ↓
  ATTENTION    — what matters surfaces
    ↓
  INTENT       — dominant purpose identified
    ↓
  EMOTION      — affective state inferred
    ↓
  MEMORY       — relevant experience retrieved
    ↓
  REASONING    — Executive decides (CognitivePlan)
    ↓
  IMAGINATION  — creative / dream recombination (async, during lifecycle rest)
    ↓
  AGENCY       — plan executed across surfaces
    ↓
  EXPRESSION   — voice, avatar, glow, motion delivered

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
LIFECYCLE (canonical)

  AWAKE → ENGAGED → PROCESSING → LOW_LOAD → RECHARGING
    → CONSOLIDATING → DREAMING → RESTORED → AWAKE

  During RECHARGING / CONSOLIDATING: memory consolidation, significance
  reweighting, self-model update, unresolved-thread processing.
  During DREAMING: recombination, imagination, replay — dream entries are
  NOT automatically factual memory (see runtime/memory_origin.py).

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
# -1. GROUNDING CONTRACTS (WP-N)
#     GroundingContext  — what is actually happening in this conversation right now.
#     GroundingAssessment — produced by anchor_assessor; answers "is a response candidate
#                           connected to this conversation?"
#
#     Architecture position: Grounding Faculty runs AFTER CCM, BEFORE Executive.
#     It supplies information — it NEVER decides, overrides Executive, or speaks.
#     One Brain rule: Grounding is a service, not a brain.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class GroundingContext:
    """
    WO-002: What is happening in the conversation right now.

    Produced by faculties/grounding/grounding_faculty.py every turn.
    Consumed by: prompt_builder ([CONVERSATION GROUND] block), Executive (read-only).

    Producer: GroundingFaculty
    Authority: read-only downstream — no faculty modifies this after assembly
    Lifecycle: per-turn, assembled from current message + recent state
    Failure behaviour: falls back to empty strings; spine continues without it

    Referent Ladder (priority, highest first):
        CURRENT_MESSAGE → CURRENT_SUBJECT → CURRENT_THREAD →
        RECENT_REFERENT → ESTABLISHED_THREAD → MEMORY → NEW_INITIATIVE
    """
    current_subject:         str   = ""    # what the message is primarily about
    current_topic:           str   = ""    # the specific aspect being addressed
    active_thread:           str   = ""    # conversational thread this continues
    user_intent:             str   = ""    # asking | telling | updating | requesting | other
    current_referents:       tuple = field(default_factory=tuple)   # entities named this turn
    recent_referents:        tuple = field(default_factory=tuple)   # entities named in last 3 turns
    unresolved_threads:      tuple = field(default_factory=tuple)   # threads opened, not closed
    recent_conversation_state: str = ""   # brief summary of last 2 turns
    recent_register:         str   = ""   # tone of last few turns
    available_connections:   tuple = field(default_factory=tuple)   # cross-signal candidates
    referent_ladder_level:   str   = "CURRENT_MESSAGE"  # which rung this turn anchors to
    confidence:              float = 0.0   # 0.0 = no grounding available; 1.0 = fully grounded
    # WO-002 additions ────────────────────────────────────────────────────────
    active_entity:           str   = ""    # most specific concrete entity (may be multi-word)
    pronoun_resolution:      tuple = field(default_factory=tuple)  # ((pronoun, entity), ...)
    thread_age:              int   = 0     # turns since active_thread was first established
    stale_subjects:          tuple = field(default_factory=tuple)  # subjects from 4+ turns ago
    immediate_subject:       str   = ""    # subject from the very last completed turn
    is_continuation:         bool  = False # True when user sent a bare continuation signal ("keep going" etc.)


@dataclass(frozen=True)
class GroundingAssessment:
    """
    WP-N: Is a response candidate connected to this conversation?

    Produced by faculties/grounding/anchor_assessor.py.
    NOT produced every turn — only when the prompt_builder needs to annotate
    or the diagnostic layer requests it.

    grounded=True   → response has a clear conversational reason to exist
    grounded=False  → response is floating (philosophical, arbitrary, unanchored)
    """
    grounded:        bool  = False
    relation:        str   = "UNKNOWN"   # DIRECT | ADJACENT | BRIDGE | NEW_INITIATIVE
    anchor:          str   = ""          # what the response is anchored to
    referent:        str   = ""          # which referent it addresses
    confidence:      float = 0.0
    bridge_required: bool  = False       # response needs a transition sentence
    bridge_present:  bool  = False       # transition is present in candidate
    reason:          str   = ""          # diagnostic: why this assessment


# ─────────────────────────────────────────────────────────────────────────────
# 0. AFFECTIVESTATE (WO-AFFECTIVE-STATE-001)
#    13-dimensional continuous affective state space.
#    Labels (curious, fearful, calm) are regions in this space — not primitives.
#    Produced by significance_faculty; consumed by spine, exec_decision, prompt_builder.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AffectiveState:
    """
    eLo's internal affective geometry — 13 continuous dimensions.
    Source: SOURCE_2026-09-08_ELO_OS_AI_SOURCE_S01.md §7
    """
    valence:      float = 0.0   # -1.0 → +1.0 (negative ↔ positive)
    arousal:      float = 0.5   # 0.0 → 1.0
    safety:       float = 0.8   # 0.0 → 1.0
    novelty:      float = 0.3   # 0.0 → 1.0
    curiosity:    float = 0.5   # 0.0 → 1.0
    confidence:   float = 0.6   # 0.0 → 1.0
    uncertainty:  float = 0.3   # 0.0 → 1.0
    attachment:   float = 0.5   # 0.0 → 1.0
    tension:      float = 0.2   # 0.0 → 1.0
    comfort:      float = 0.7   # 0.0 → 1.0
    agency:       float = 0.6   # 0.0 → 1.0
    significance: float = 0.0   # 0.0 → 1.0 (mirrors SP-29 overall score)
    reward:       float = 0.0   # 0.0 → 1.0

    def to_dict(self) -> dict:
        return {
            "valence": self.valence, "arousal": self.arousal,
            "safety": self.safety, "novelty": self.novelty,
            "curiosity": self.curiosity, "confidence": self.confidence,
            "uncertainty": self.uncertainty, "attachment": self.attachment,
            "tension": self.tension, "comfort": self.comfort,
            "agency": self.agency, "significance": self.significance,
            "reward": self.reward,
        }

    def label(self) -> str:
        """Nearest canonical label from geometry."""
        if self.curiosity > 0.7 and self.valence >= 0.0:
            return "curious"
        if self.valence < -0.3 and self.arousal > 0.6 and self.safety < 0.4:
            return "fearful"
        if self.valence > 0.5 and self.arousal > 0.6:
            return "excited"
        if self.comfort > 0.7 and self.arousal < 0.4:
            return "calm"
        if self.tension > 0.6:
            return "tense"
        if self.novelty > 0.6:
            return "alert"
        return "neutral"


# ─────────────────────────────────────────────────────────────────────────────
# 0b. SELFMODEL (WO-SELF-MODEL-001)
#    eLo's internal model of its own state, capabilities, and history.
#    Assembled by _self_model_faculty() from existing faculty outputs.
#    Observes; does not decide.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SelfModel:
    """
    eLo's structured self-picture — v1 lean subset.
    Source: SOURCE_2026-09-08_ELO_OS_AI_SOURCE_S01.md §9
    """
    identity:               dict  = field(default_factory=dict)    # WKG foundational claims
    current_state:          dict  = field(default_factory=dict)    # AffectiveState + cognitive mode snapshot
    autobiographical_summary: str = ""                             # synthesised from WKG + lessons
    limitations:            list  = field(default_factory=list)    # capability gaps
    current_goal:           str   = ""                             # Executive's current intent
    prediction_confidence:  float = 0.5                            # 0.0–1.0
    internal_preferences:   dict  = field(default_factory=dict)    # learned tendencies from lesson store


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

    # ── Agency Faculty (WO-AGENCY-FACULTY-001) ───────────────────────────────
    agency_level:         float = 0.6         # 0.0 (deferring) → 1.0 (full initiative)

    # ── Q-BODY (proprioception) ───────────────────────────────────────────────
    body_moving:          bool  = False       # eLo is locomoting right now
    body_gait:            str   = "idle"      # idle | walk | run | jump | fall
    body_heading:         str   = "none"      # right | left | up | down | up_left | … | none
    body_position_x:      float = 0.0         # viewport x (0–1)
    body_position_y:      float = 0.0         # viewport y (0–1)
    body_on_window:       bool  = False       # perched on a window
    body_window:          str   = ""          # window name eLo is perched on
    body_edge:            str   = ""          # bottom | top | left | right | ""
    body_embodiment:      str   = "desktop"   # desktop | mobile | robot

    # ── Q-MOVEMENT (five lifecycle states) ──────────────────────────────────
    movement_where_i_am:   str  = ""          # "window:<name> edge:<edge>" summary
    movement_want_to_go:   int  = -1          # goal window ID (-1 = none)
    movement_am_moving:    bool = False        # currently locomoting
    movement_arrived:      bool = False        # arrived this turn
    movement_what_happened: str = ""          # arrived | fell | interrupted | none

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    lifecycle_state:      str   = "awake"     # LifecycleState.value — awake/engaged/recharging/etc.

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

    # ── Significance Faculty (WO-SP29) ────────────────────────────────────────
    significance_score:   float = 0.0          # overall score 0.0-1.0; gates memory write (>=0.72) and self-init (>=0.90)

    # ── WKG Faculty (WO-WKG-001..003 + WO-CONV-001) ─────────────────────────
    wkg_context:          str   = ""           # WKG claims relevant to this turn; epistemic_class VERIFIED

    # ── CCM Enrichment (WO-CCM-SPINE) ────────────────────────────────────────
    ccm_context:          dict  = field(default_factory=dict)   # 28-dim CCM enrichment per turn

    # ── Affective State (WO-AFFECTIVE-STATE-001) ──────────────────────────────
    affective_state:      object = None        # AffectiveState | None — 13-dim continuous affect

    # ── Self Model (WO-SELF-MODEL-001) ────────────────────────────────────────
    self_model:           object = None        # SelfModel | None — assembled by _self_model_faculty

    # ── Grounding Context (WP-N) ─────────────────────────────────────────────
    grounding_context:    object = None        # GroundingContext | None — current conversational ground

    # ── Assembly Confidence ───────────────────────────────────────────────────
    assembly_confidence:  float = 1.0         # 0.0 if faculties partially failed

    # ── Faculty Provenance (WO-PROVENANCE-001) ────────────────────────────────
    faculty_provenance:   dict  = field(default_factory=dict)  # {faculty_name: summary_string}

    # ── Reasoning Tier (WO-REASONING-001) ────────────────────────────────────
    # Tags the depth of evidence-based reasoning available this turn.
    # "retrieval_only" — answer from vault/WKG without additional inference
    # "single_step"    — one inference from evidence (default for most turns)
    # "multi_step"     — chained reasoning across multiple evidence sources
    # "generative"     — LLM generates from training data (no grounded evidence)
    reasoning_tier:       str   = "generative"  # conservative default until wired

    # ── Conversation Continuity (WO-CONVERSATION-001) ─────────────────────────
    last_elo_response:    str   = ""  # what eLo said last turn (≤500 chars); empty on first turn

    # ── Perception Faculty (WO-PERCEPTION-001) ────────────────────────────────
    # Environment delta: which blender_state.json fields changed since last turn.
    # Keys = field label; values = (old_value, new_value).
    environment_delta:    dict  = field(default_factory=dict)
    perception_changed:   bool  = False   # True if any environment field changed this turn

    # ── Simulation Tracker (WO-SIMULATION-001) ────────────────────────────────
    # What eLo planned vs what it actually completed, across turns.
    pending_actions:      tuple = field(default_factory=tuple)   # intended but not yet run
    executed_actions:     tuple = field(default_factory=tuple)   # completed this session


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

    # ── Affective State (WO-AFFECTIVE-STATE-001) ──────────────────────────────
    affective_state:      object = None        # AffectiveState | None — from significance_faculty

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
    gaze_target:            str | None = None  # object name or direction label from cognitive focal_thread
    world_state:            dict | None = None # world-state payload from Unity tick → spine

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    lifecycle_state:    str   = "awake"       # LifecycleState.value — awake/engaged/dreaming/etc.

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
