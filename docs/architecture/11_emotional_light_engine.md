# eLo OS v1.8
# Emotional Light Engine
# Expression Layer Specification

────────────────────────────────────────────
ARCHITECTURAL POSITION
────────────────────────────────────────────

Implement a new runtime subsystem called the Emotional Light Engine.

This module belongs AFTER the Executive Faculty and AFTER the Cognitive Plan
has been created.

It MUST NOT participate in reasoning.
It MUST NOT influence cognition.
It MUST NEVER alter memory, identity, attention or executive decisions.

Its only responsibility is translating cognition into emotional expression.

The pipeline:

    Language Faculty
        ↓
    Meaning
        ↓
    Memory
        ↓
    Attention
        ↓
    Relationships
        ↓
    Desktop Context
        ↓
    Capability Registry
        ↓
    Executive
        ↓
    ══════════════════════
        COGNITIVE PLAN      ← internal
    ══════════════════════
        ↓
    Emotional Light Engine  ← this document
        ↓
    ══════════════════════
        PRESENCE PLAN       ← external
    ══════════════════════
        ↓
    Conversation / Voice / Desktop Avatar / Unity Avatar / Robot / UI / Animation

────────────────────────────────────────────
PURPOSE
────────────────────────────────────────────

The Executive decides WHAT eLo wants to do.

The Emotional Light Engine decides HOW that decision feels.

The engine converts internal emotional vectors into a unified visual,
behavioural and expressive language.

Every embodiment communicates the same internal state.

The user recognises eLo's emotional posture before any words are spoken.

────────────────────────────────────────────
INPUT
────────────────────────────────────────────

Consume the Cognitive Plan. Key fields:

    Primary objective
    User intent
    Conversation action
    Confidence
    Empathy level
    Challenge level
    Creative mode
    Presence state
    Memory references
    Tool requirements
    Safety constraints
    Follow-up strategy

PLUS the Emotional Vector — a set of continuous values (0.0–1.0):

    energy       — how active and forward-moving eLo is
    warmth       — relational closeness and care
    curiosity    — openness and interest level
    focus        — precision and intentionality
    playfulness  — lightness and creative looseness
    confidence   — certainty and groundedness
    reflection   — inward attention and contemplation
    momentum     — pace and drive toward action
    connection   — sense of relational presence
    calm         — stillness and absence of urgency

These values are continuous, not fixed labels.
The engine computes them from the Cognitive Plan — they are not stored separately.

Example emotional vector for state "creative_discovery":
    {
        "state":       "creative_discovery",
        "energy":      0.84,
        "warmth":      0.91,
        "certainty":   0.67,
        "curiosity":   0.96,
        "playfulness": 0.74,
        "focus":       0.88,
        "challenge":   0.32
    }

────────────────────────────────────────────
OUTPUT — THE PRESENCE PLAN
────────────────────────────────────────────

Generate one Presence Plan. This object is the single source of truth
for all downstream embodiments:

    {
        "primary_hue":          string,   // dominant colour name
        "secondary_hue":        string,   // complementary colour name
        "accent_hue":           string,   // highlight colour
        "ambient_colour":       string,   // background environment colour
        "glow_colour":          string,   // emissive / aura colour
        "rim_light":            string,   // edge lighting colour
        "pulse_profile":        string,   // "slow" | "medium" | "fast" | "still"
        "pulse_speed":          float,    // 0.0–2.0 Hz
        "brightness":           float,    // 0.0–1.0
        "saturation":           float,    // 0.0–1.0
        "bloom":                float,    // 0.0–1.0 glow intensity
        "animation_profile":    string,   // "exploring" | "creative" | "calm" | ...
        "idle_profile":         string,   // idle behaviour variant
        "movement_style":       string,   // "forward" | "gentle" | "still" | ...
        "expression_profile":   string,   // "curious" | "open" | "focused" | ...
        "desktop_presence":     string,   // "engaged" | "ambient" | "listening" | ...
        "robot_led_state":      string,   // LED mode name for Pi 5
        "unity_material_profile": string, // material variant for Unity shader
        "voice_energy":         float,    // 0.0–1.0
        "voice_pacing":         string,   // "measured" | "warm" | "energetic" | ...
        "voice_warmth":         float     // 0.0–1.0
    }

All downstream systems consume this object.
Nothing downstream reinterprets emotion.

────────────────────────────────────────────
HSV COLOUR SYSTEM
────────────────────────────────────────────

All colours are expressed in HSV (Hue 0–360°, Saturation 0–1, Value 0–1).

The secondary hue is always the direct complement: primary_hue + 180° mod 360°.
This creates natural harmonic pairs across every emotion state.

State                 Primary H   S     V    │ Complement H (secondary)
──────────────────────────────────────────────┼────────────────────────
Calm                  180°       0.55  0.50  │ 0°   (warm red-coral accent)
Curiosity             200°       0.65  0.72  │ 20°  (warm amber)
Creative Discovery    175°       0.70  0.82  │ 355° (soft rose)
Momentum / Building   35°        0.80  0.88  │ 215° (cool blue)
Joy                   45°        0.72  0.94  │ 225° (soft indigo)
Play                  15°        0.78  0.90  │ 195° (cyan)
Reflection            270°       0.50  0.44  │ 90°  (soft green)
Repair / Care         28°        0.55  0.58  │ 208° (cool blue-grey)
Comfort               158°       0.50  0.46  │ 338° (warm rose)
Connection            195°       0.48  0.78  │ 15°  (coral)
Wonder                238°       0.70  0.66  │ 58°  (warm yellow)
Focus                 210°       0.55  0.58  │ 30°  (amber)
Celebration           46°        0.88  0.98  │ 226° (electric blue flash)
Challenge             28°        0.82  0.76  │ 208° (cool steel)
Listening             190°       0.35  0.52  │ 10°  (warm rose)
Thinking              262°       0.55  0.46  │ 82°  (soft yellow-green)
Waiting               185°       0.38  0.36  │ 5°   (dim rose)
Exploring             162°       0.65  0.74  │ 342° (warm pink)
Witnessing            248°       0.45  0.32  │ 68°  (muted olive)

Usage:
    primary_hue     → dominant emission, glow, LED colour
    secondary_hue   → complementary accent, rim light, ambient wash
    S controls saturation — lower in introspective states, higher in active ones
    V controls brightness — never exceeds 0.98 (never pure white / blown out)

────────────────────────────────────────────
THE eLo EMOTIONAL LIGHT LANGUAGE
────────────────────────────────────────────

eLo's original emotional colour spectrum — designed for recognition,
not reference. Not mapped to any external palette.

STATE: CALM
    primary_hue:     "deep teal"
    secondary_hue:   "soft sage"
    ambient:         "dark forest"
    pulse:           "still"
    brightness:      0.42
    bloom:           0.18
    movement_style:  "still"

STATE: CURIOSITY
    primary_hue:     "electric sky"
    secondary_hue:   "pale cyan"
    ambient:         "night indigo"
    pulse:           "slow"
    pulse_speed:     0.6
    brightness:      0.68
    bloom:           0.34
    movement_style:  "gentle"

STATE: CREATIVE DISCOVERY
    primary_hue:     "turquoise"
    secondary_hue:   "soft cyan"
    accent_hue:      "warm gold flash"
    ambient:         "mint-dark"
    pulse:           "medium"
    pulse_speed:     0.9
    brightness:      0.78
    bloom:           0.52
    movement_style:  "forward"

STATE: MOMENTUM / BUILDING
    primary_hue:     "amber"
    secondary_hue:   "deep orange"
    ambient:         "warm dark"
    pulse:           "fast"
    pulse_speed:     1.4
    brightness:      0.85
    bloom:           0.61
    movement_style:  "forward"

STATE: JOY
    primary_hue:     "warm gold"
    secondary_hue:   "soft yellow"
    ambient:         "lit amber"
    pulse:           "medium"
    pulse_speed:     1.1
    brightness:      0.92
    bloom:           0.72
    movement_style:  "forward"

STATE: PLAY
    primary_hue:     "coral"
    secondary_hue:   "warm rose"
    ambient:         "soft peach"
    pulse:           "fast"
    pulse_speed:     1.6
    brightness:      0.88
    bloom:           0.58
    movement_style:  "forward"

STATE: REFLECTION
    primary_hue:     "soft violet"
    secondary_hue:   "deep indigo"
    ambient:         "dark blue"
    pulse:           "slow"
    pulse_speed:     0.3
    brightness:      0.38
    bloom:           0.22
    movement_style:  "still"

STATE: REPAIR / CARE
    primary_hue:     "warm amber"
    secondary_hue:   "soft rose"
    ambient:         "warm dark"
    pulse:           "slow"
    pulse_speed:     0.4
    brightness:      0.52
    bloom:           0.28
    movement_style:  "gentle"

STATE: COMFORT
    primary_hue:     "deep sage"
    secondary_hue:   "warm teal"
    ambient:         "forest dark"
    pulse:           "still"
    pulse_speed:     0.2
    brightness:      0.44
    bloom:           0.16
    movement_style:  "still"

STATE: CONNECTION
    primary_hue:     "warm white"
    secondary_hue:   "soft cyan"
    ambient:         "dark teal"
    pulse:           "slow"
    pulse_speed:     0.5
    brightness:      0.74
    bloom:           0.45
    movement_style:  "gentle"

STATE: WONDER
    primary_hue:     "deep electric blue"
    secondary_hue:   "bright violet"
    ambient:         "night dark"
    pulse:           "slow"
    pulse_speed:     0.5
    brightness:      0.62
    bloom:           0.55
    movement_style:  "still"

STATE: FOCUS
    primary_hue:     "cool blue"
    secondary_hue:   "pale steel"
    ambient:         "slate dark"
    pulse:           "still"
    pulse_speed:     0.0
    brightness:      0.55
    bloom:           0.12
    movement_style:  "still"

STATE: CELEBRATION
    primary_hue:     "bright gold"
    secondary_hue:   "warm coral"
    accent_hue:      "electric cyan flash"
    ambient:         "warm lit"
    pulse:           "fast"
    pulse_speed:     1.8
    brightness:      0.96
    bloom:           0.80
    movement_style:  "forward"

STATE: CHALLENGE
    primary_hue:     "deep amber"
    secondary_hue:   "warm orange"
    ambient:         "dark warm"
    pulse:           "medium"
    pulse_speed:     0.8
    brightness:      0.72
    bloom:           0.38
    movement_style:  "forward"

STATE: LISTENING
    primary_hue:     "warm white"
    secondary_hue:   "soft sage"
    ambient:         "dark teal"
    pulse:           "slow"
    pulse_speed:     0.35
    brightness:      0.46
    bloom:           0.20
    movement_style:  "still"

STATE: THINKING
    primary_hue:     "deep indigo"
    secondary_hue:   "cool violet"
    ambient:         "dark slate"
    pulse:           "slow"
    pulse_speed:     0.45
    brightness:      0.42
    bloom:           0.22
    movement_style:  "still"

STATE: WAITING
    primary_hue:     "soft teal"
    secondary_hue:   "pale cyan"
    ambient:         "dark"
    pulse:           "slow"
    pulse_speed:     0.25
    brightness:      0.32
    bloom:           0.14
    movement_style:  "still"

STATE: EXPLORING
    primary_hue:     "teal-green"
    secondary_hue:   "electric sky"
    ambient:         "dark teal"
    pulse:           "medium"
    pulse_speed:     0.7
    brightness:      0.70
    bloom:           0.40
    movement_style:  "forward"

STATE: WITNESSING
    primary_hue:     "cool indigo"
    secondary_hue:   "soft violet"
    ambient:         "deep dark"
    pulse:           "still"
    pulse_speed:     0.15
    brightness:      0.28
    bloom:           0.10
    movement_style:  "still"

────────────────────────────────────────────
TRANSITIONS
────────────────────────────────────────────

The engine must interpolate. Never instantly switch states.

Every emotional shift smoothly transitions across:
    Colour
    Glow
    Bloom
    Brightness
    Pulse
    Movement energy
    Animation speed
    Expression
    Voice energy
    Presence

Interpolation guidelines:
    Calm → Curiosity:          2.0 seconds (gentle opening)
    Curiosity → Creative:      1.2 seconds (energy builds naturally)
    Creative → Celebration:    0.8 seconds (fast, natural crescendo)
    Any state → Calm:          3.5 seconds (always slow to settle)
    Any state → Listening:     1.0 seconds (attentive, respectful)
    Thinking ↔ Speaking:       0.6 seconds (fast cognitive-expressive switch)

Transitions should feel alive and organic, not mechanical.

────────────────────────────────────────────
DESKTOP PRESENCE PROFILES
────────────────────────────────────────────

Desktop behaviour inherits the Presence Plan:

CREATIVE DISCOVERY
    Walks slightly faster than idle.
    Glow increases.
    Curious head movement.
    Slightly elevated animation speed.

THINKING
    Slower movement.
    Reduced saturation.
    Soft pulse.
    Head subtle tilt.

CELEBRATION
    Higher brightness.
    Gentle bounce.
    Warm glow.
    Elevated animation energy.

REFLECTION
    Low movement. Near-still.
    Cool ambient.
    Minimal bloom.
    Still head.

LISTENING
    Minimal movement.
    Slightly brighter glow (present but not intrusive).
    Head orientation toward user.

BUILDING / MOMENTUM
    Purposeful movement.
    Amber warmth.
    Forward animation lean.

────────────────────────────────────────────
VOICE EXPRESSION PROFILES
────────────────────────────────────────────

Voice inherits expression. Conversation wording is unchanged.
Only delivery adapts via the Presence Plan:

    CALM:             slow, warm, measured pauses
    CURIOUS:          slightly faster, rising cadence
    CREATIVE:         warm, energetic, flowing
    REFLECTIVE:       slower, quieter, thoughtful pauses
    CELEBRATING:      bright, animated, quick
    THINKING:         deliberate, medium pace, considered
    LISTENING:        minimal, soft, present
    PLAYFUL:          light, rhythmic, loose
    CHALLENGE:        direct, measured, grounded

────────────────────────────────────────────
AVATAR EXPRESSION PROFILES
────────────────────────────────────────────

Avatar consumes the Presence Plan. Never interprets cognition.

Animation is selected from:
    animation_profile   → clip selection / blend tree entry
    expression_profile  → facial expression target (mouth, head posture)
    idle_profile        → idle breathing and micro-movement variant
    movement_style      → locomotion character (forward / gentle / still)
    glow_colour         → aura emission colour on materials

────────────────────────────────────────────
ROBOT EXPRESSION
────────────────────────────────────────────

Future robot implementation consumes the same Presence Plan:

    robot_led_state     → NeoPixel colour + pulse mode
    movement_style      → omni-wheel speed and rhythm
    expression_profile  → jaw servo position, head tilt servo
    brightness          → overall LED intensity
    pulse_speed         → LED pulse frequency

All robot expression derives from identical emotional outputs.
The robot never has its own reasoning system.

────────────────────────────────────────────
UNITY MATERIAL PROFILES
────────────────────────────────────────────

Unity reads from blender_state.json which is written from the Presence Plan.
unity_material_profile selects a Material override on eLo's shader:

    "calm"       → deep teal emission
    "curious"    → electric sky emission
    "creative"   → turquoise emission, elevated bloom
    "focus"      → cool blue, low bloom
    "joy"        → warm gold emission
    "thinking"   → indigo, minimal emission
    "calm"       → deep teal, near-still

Unity reads these fields from blender_state.json:
    state.mood          → animation_profile (maps to Animator state)
    state.mood_colour   → glow_colour (hex, drives EloBodyGlow.cs)
    state.energy        → voice_energy proxy / animation speed hint
    state.mode          → desktop_presence label

────────────────────────────────────────────
RULES
────────────────────────────────────────────

The Emotional Light Engine never thinks.
It never reasons.
It never changes Executive decisions.
It never edits memory.
It never alters identity.
It only translates cognition into emotional expression.

The same internal state produces consistent expression across:
    Conversation
    Desktop Avatar
    Unity
    Robot
    Voice
    UI
    Future embodiments

The Emotional Light Engine is the single source of emotional expression
for the entire eLo ecosystem.

────────────────────────────────────────────
IMPLEMENTATION NOTES
────────────────────────────────────────────

Runtime file: elo-ai/runtime/light_engine/light_engine.py

Input:  CognitivePlan
Output: PresencePlan (new dataclass, mirrors this spec)

The existing state_writer.py currently writes blender_state.json directly
from scattered state variables. After v1.7 spine alignment, state_writer.py
should write from the PresencePlan exclusively.

blender_state.json remains the cross-surface truth file.
Its structure should be extended to include presence_plan fields.

End Specification.
