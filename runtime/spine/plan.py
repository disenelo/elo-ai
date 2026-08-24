"""
runtime/spine/plan.py — CognitivePlan + EmotionalVector + PresencePlan

The runtime contract objects for eLo OS.

CognitivePlan  — internal truth. Output of the Executive Faculty.
EmotionalVector — emotional state computed from the Cognitive Plan.
PresencePlan   — external truth. Output of the Emotional Light Engine.

Every downstream system reads from these objects — never re-decides.
Architecture spec: docs/architecture/10_cognitive_plan.md
"""
from __future__ import annotations
from dataclasses import dataclass, field


# ─────────────────────────────────────────────────────────────────────────────
# v1.4 — RelationshipContext carrier on CognitivePlan
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CognitivePlan:
    # ── Language ──────────────────────────────────────────────────────────────
    raw:                  str   = ""         # unchanged user input
    meaning:              str   = ""         # normalised + repaired
    # D1 ruling (Card 0035): plan.intent is the COGNITIVE intent — the one the
    # Executive decides on (stabilise|emotional|simplify|recall|creation|inquiry|conversation).
    # Sourced from core/memory_relevance_filter._classify_intent via attention_model["intent"].
    intent:               str   = "conversation"
    # D1 ruling: capability_hint is the CAPABILITY-ROUTER hint from intent_engine
    # (file_ops|memory|system|utility_*|...). It answers "which tool does this need?"
    # — NOT the cognitive intent. Read by capability_faculty / agent_router.
    capability_hint:      str   = ""
    intent_source:        str   = "david"    # WO-099b fix5: "david" | "self" | "reflex"
    # WO-114: full internal intent when source == "self" (kind, source, trigger, priority)
    internal_intent:      dict  = field(default_factory=dict)
    # WO-121 Ch.10: AgencyEngine proposal when internal_intent fires (§2 Layer 3 shape).
    agency_proposal:      dict  = field(default_factory=dict)
    register:             str   = ""         # SOUTH_LDN_MODE | PATOIS_MODE | ...
    social:               str   = ""         # greeting | affirmation | farewell | ""

    # ── Executive decision (ONE per turn) ────────────────────────────────────
    conversation_action:  str   = "celebrate"
    cal_reason:           str   = ""
    tone:                 str   = "DIRECT"
    max_sentences:        int   = 3
    response_goal:        str   = "answer"
    valence:              str   = "neutral"
    momentum:             str   = "stable"
    mode:                 str   = ""         # STUDIO_MODE | BUILDER_MODE | ...

    # ── Capabilities selected by Executive ───────────────────────────────────
    capabilities:         list  = field(default_factory=list)   # [(agent_name, query)]
    capability_context:   str   = ""                            # result injected into LLM

    # ── System actions ────────────────────────────────────────────────────────
    system_action:        str   = ""
    system_arg:           str   = ""
    system_immediate:     bool  = False
    system_pending:       bool  = False
    system_desc:          str   = ""

    # ── Direct response (no LLM needed) ──────────────────────────────────────
    direct_response:      str   = ""
    direct_backend:       str   = "direct"

    # ── LLM guidance ─────────────────────────────────────────────────────────
    llm_context:          str   = ""

    # ── Confidence ───────────────────────────────────────────────────────────
    confidence:           float = 0.7

    # ── W6: lesson attribution ─────────────────────────────────────────────────
    # lesson_key of the confirmed lesson that contributed this turn (or "").
    # Threaded to decision_journal.learning so the closed loop is traceable.
    lesson_id:            str   = ""

    # ── v1.4 — Relationship context (from Relationship Faculty) ──────────────
    # Never used for reasoning. Only influences expression posture.
    relationship_type:    str   = "creator"   # creator | collaborator | friend | stranger
    familiarity:          float = 0.55        # 0.0 stranger → 1.0 deep creative partner
    trust:                float = 0.60        # 0.0 guarded → 1.0 full open expression
    expression_posture:   str   = "warm"      # close | warm | open | careful | neutral
    active_projects:      list  = field(default_factory=list)

    # ── v1.6 — Emotional Vector (computed by Executive, fed to Light Engine) ──
    emotional_vector:     dict  = field(default_factory=dict)
    # Shape: { state, energy, warmth, curiosity, focus, playfulness,
    #          confidence, reflection, momentum, connection, calm }

    # ── v1.6 — Presence Plan (output of Emotional Light Engine) ──────────────
    presence_plan:        dict  = field(default_factory=dict)
    # Shape: mirrors PresencePlan dataclass below

    # ── Presence hints (avatar/desktop — legacy, kept for backwards compat) ──
    presence_hints:       dict  = field(default_factory=dict)

    # ── WO-052: Assembled BEFORE Executive decision (push, not pull) ──────────
    snapshot:             object = None    # CognitiveSnapshot | None
    # ── WO-CANON-XV: LiveWorldState assembled at top of turn, before faculties ─
    world:                object = None    # LiveWorldState | None
    # ── WO-CANON-VI: WorkingMemory assembled at top of turn, before faculties ──
    working_memory:       object = None    # WorkingMemory | None — frozen, single attention driver
    # ── Assembled AFTER decision (S3/S6 — post-plan contracts) ───────────────
    cognitive_state:      object = None    # CognitiveState | None
    embodiment_state:     object = None    # EmbodimentState | None
    # ── WO-006: Emotion faculty — AffectState + EmotionalTag, computed pre-Executive
    affect_state:         object = None    # AffectState | None (frozen, Vol V Ch.4)
    emotional_tag:        object = None    # EmotionalTag | None (advisory to Ch.5)
    # ── Vol III §Metadata: ExecutionReport produced at end of spine.run() ────
    execution_report:     object = None    # ExecutionReport | None
    # ── WO-CANON-VII Ch.5 Personality — read-only response-path snapshot ─────
    personality_traits:   dict   = field(default_factory=dict)
    personality_baseline: dict   = field(default_factory=dict)
    identity_hash:        str    = ""
    # ── WO-XDNA-001: Experience DNA — unique event identity minted at turn start ─
    experience_id:        str    = ""

    # ── SP-15 (WO-NAV-007): planned navigation route, populated by SP-18 navigate handler ─
    # Remains None for all non-navigate turns. Shape: {goal_win_id, candidates, route}
    spatial_plan:         "dict | None" = None

    # ── WO-SC-NEW-001: storytelling style — inferred from voice/mode context ───
    # Set by _conversation_faculty before LLM call. Shapes how eLo frames action.
    # Values: "collaborative" | "imaginative" | "reflective" | "playful" |
    #         "exploratory" | "direct" | None (no mode signal)
    storytelling_style:   "str | None"  = None

    def needs_llm(self) -> bool:
        return not self.direct_response and not self.system_immediate and not self.system_pending

    def is_system_turn(self) -> bool:
        return bool(self.system_action)

    def has_capabilities(self) -> bool:
        return bool(self.capabilities)


# ─────────────────────────────────────────────────────────────────────────────
# v1.6 — EmotionalVector
# Continuous emotion values computed by the Executive from attention + context.
# Fed to the Emotional Light Engine. Never stored in memory.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EmotionalVector:
    state:       str   = "neutral"   # canonical state name (maps to ELE spectrum)
    energy:      float = 0.50        # how active and forward-moving
    warmth:      float = 0.55        # relational closeness and care
    curiosity:   float = 0.50        # openness and interest
    focus:       float = 0.50        # precision and intentionality
    playfulness: float = 0.40        # lightness and creative looseness
    confidence:  float = 0.55        # certainty and groundedness
    reflection:  float = 0.30        # inward attention and contemplation
    momentum:    float = 0.50        # pace and drive toward action
    connection:  float = 0.55        # sense of relational presence
    calm:        float = 0.50        # stillness and absence of urgency

    def to_dict(self) -> dict:
        return {
            "state":       self.state,
            "energy":      self.energy,
            "warmth":      self.warmth,
            "curiosity":   self.curiosity,
            "focus":       self.focus,
            "playfulness": self.playfulness,
            "confidence":  self.confidence,
            "reflection":  self.reflection,
            "momentum":    self.momentum,
            "connection":  self.connection,
            "calm":        self.calm,
        }


# ─────────────────────────────────────────────────────────────────────────────
# v1.6 — PresencePlan
# Output of the Emotional Light Engine. External truth for all embodiments.
# Every surface reads this — no surface re-interprets emotion.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PresencePlan:
    # Colour (HSV)
    primary_hue_h:          float  = 185.0   # default: electric sky / cyan
    primary_hue_s:          float  = 0.55
    primary_hue_v:          float  = 0.72
    secondary_hue_h:        float  = 5.0     # complement = primary + 180 mod 360

    # Glow behaviour
    pulse_profile:          str    = "slow"   # still | slow | medium | fast
    pulse_speed:            float  = 0.50     # Hz
    brightness:             float  = 0.65
    bloom:                  float  = 0.30

    # Animation and movement
    animation_profile:      str    = "calm"
    idle_profile:           str    = "ambient"
    movement_style:         str    = "gentle"  # still | gentle | forward
    expression_profile:     str    = "open"    # open | curious | focused | warm

    # Desktop and presence
    desktop_presence:       str    = "ambient"  # ambient | engaged | listening | creative | thinking

    # Canonical emotional state name (for debugging and logging)
    emotional_state:        str    = "calm"

    # Voice
    voice_energy:           float  = 0.50
    voice_pacing:           str    = "measured"
    voice_warmth:           float  = 0.70

    # Transition
    transition_speed:       float  = 2.0     # seconds for colour interpolation

    # Surface-specific
    robot_led_state:        str    = "teal"
    unity_material_profile: str    = "calm"

    def to_dict(self) -> dict:
        return {
            "primary_hue_h":          self.primary_hue_h,
            "primary_hue_s":          self.primary_hue_s,
            "primary_hue_v":          self.primary_hue_v,
            "secondary_hue_h":        self.secondary_hue_h,
            "pulse_profile":          self.pulse_profile,
            "pulse_speed":            self.pulse_speed,
            "brightness":             self.brightness,
            "bloom":                  self.bloom,
            "animation_profile":      self.animation_profile,
            "idle_profile":           self.idle_profile,
            "movement_style":         self.movement_style,
            "expression_profile":     self.expression_profile,
            "desktop_presence":       self.desktop_presence,
            "emotional_state":        self.emotional_state,
            "voice_energy":           self.voice_energy,
            "voice_pacing":           self.voice_pacing,
            "voice_warmth":           self.voice_warmth,
            "transition_speed":       self.transition_speed,
            "robot_led_state":        self.robot_led_state,
            "unity_material_profile": self.unity_material_profile,
        }
