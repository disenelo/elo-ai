# Unity Agent Handover — Presence Plan Integration
# For: Unity Agent (DISENELO Presence app)
# Project: DISENELO-eLoDesktopBuddy
# Date: 2026-07-04

────────────────────────────────────────────
OVERVIEW
────────────────────────────────────────────

eLo OS is evolving from scattered state variables to a unified Presence Plan —
a single object that every embodiment (Unity, robot, voice, desktop) reads from.

The Unity side (DISENELO Presence / DesktopBuddy app) is in a GOOD POSITION
already: `EloOSAvatarReceiver.cs` reads `blender_state.json` and the glow
system (`EloOSChatTMP.cs`) already maps mood → colour. 

This handover defines the CONTRACT between eLo OS Python and Unity, so that
when the Python Presence Plan is implemented it flows through automatically
without breaking anything on the Unity side.

────────────────────────────────────────────
DO NOT TOUCH
────────────────────────────────────────────

The following are complete and working. Do not modify:

    EloOSAvatarReceiver.cs     — reads blender_state.json, drives animation
    EloOSChatTMP.cs            — glow/hover system, MoodHueDeg(), GlowHue()
    DesktopBuddy.cs            — main controller, locomotion, drag, exit
    EloPresenceSignal.cs       — presence/hover detection
    EloIdleBehaviour.cs        — idle animation system
    EloSquashStretch.cs        — squash/stretch physics

────────────────────────────────────────────
THE SINGLE SOURCE OF TRUTH
────────────────────────────────────────────

blender_state.json at ~/elo-ai/blender/blender_state.json is the
cross-surface truth file. Unity polls this file. Python writes it.

Current structure (do not remove any of these fields):

    {
      "motion":     { "animation", "speed", "intensity", "duration", "mood", "mode" },
      "expression": { "shape_keys": {name:val}, "head_lean", "pacing", "intensity" },
      "state":      { "energy", "mode", "emotion", "intensity" },
      "_ts":        float
    }

────────────────────────────────────────────
NEW FIELDS COMING (add support, don't break existing)
────────────────────────────────────────────

The Python Emotional Light Engine will add a "presence_plan" block to
blender_state.json. Unity should READ these fields when present, but
continue using existing fields as fallback when absent.

New block (added alongside existing, never replacing):

    "presence_plan": {
        "primary_hue_h":       float,    // 0–360 HSV hue degrees
        "primary_hue_s":       float,    // 0.0–1.0 saturation
        "primary_hue_v":       float,    // 0.0–1.0 value (brightness)
        "secondary_hue_h":     float,    // complement = primary + 180 mod 360
        "pulse_profile":       string,   // "still" | "slow" | "medium" | "fast"
        "pulse_speed":         float,    // 0.0–2.0 Hz
        "brightness":          float,    // 0.0–1.0
        "bloom":               float,    // 0.0–1.0 glow intensity
        "animation_profile":   string,   // "calm" | "creative" | "curious" | ...
        "movement_style":      string,   // "still" | "gentle" | "forward"
        "expression_profile":  string,   // "open" | "curious" | "focused" | ...
        "desktop_presence":    string,   // "ambient" | "engaged" | "listening"
        "emotional_state":     string,   // canonical state name e.g. "creative_discovery"
        "voice_energy":        float,    // 0.0–1.0
        "transition_speed":    float     // seconds for colour interpolation
    }

────────────────────────────────────────────
UNITY-SIDE WORK NEEDED
────────────────────────────────────────────

1. UPDATE EloMoodGlow.cs (the body aura, from the previous handover):

   - When presence_plan block is present in blender_state.json:
       Read primary_hue_h, primary_hue_s, primary_hue_v
       Convert HSV → Color: Color.HSVToRGB(h/360f, s, v)
       Use this colour for the aura instead of MoodToColour(string)

   - When presence_plan is absent: keep existing string-based MoodToColour()

   - Add bloom support:
       auraSprite.material has an "_Intensity" or emission property
       Multiply it by presence_plan.bloom (0.0–1.0) if present

   - Add pulse_speed support:
       pulseSpeed = presence_plan.pulse_speed when present
       "still" profile → pulseRange = 0 (no oscillation)

2. UPDATE EloOSChatTMP.cs — GlowHue() method (line ~837):

   - When presence_plan block is present:
       Use primary_hue_h + gentle drift → same HSV → Color conversion
       This replaces the MoodHueDeg() string lookup for glow surfaces

   - When absent: keep existing MoodHueDeg() fallback

   - Add colour interpolation:
       Don't snap to new hue instantly. Lerp currentHue → targetHue
       at rate: 1f / presence_plan.transition_speed (seconds)
       This is the smooth transition the Light Engine requires

3. UPDATE EloOSAvatarReceiver.cs — ApplyEmotionState() (line ~795):

   - When presence_plan block is present:
       Read animation_profile → map to Animator state via existing Canonical dict
       Read movement_style ("still" / "gentle" / "forward") → set locomotion hint
       Read desktop_presence → expose as public string PresenceProfile
       for DesktopBuddy to read

   - Existing emotion/mood fields still work as before (backwards compatible)

4. NEW: Read presence_plan in ReadStateOnce() (line ~316):

   Add parsing for the presence_plan JSON block after existing ApplyX calls:

       ApplyPresencePlan(root["presence_plan"] as JObject);

   This should be null-safe — if absence of the block → no change.

────────────────────────────────────────────
ADDING THESE MOODS TO MoodHueDeg() NOW
────────────────────────────────────────────

Python currently emits state.emotion values that fall through the existing
MoodHueDeg() switch statement. Add these five cases immediately (line ~857
in EloOSChatTMP.cs):

    case "confident":   hue = 210f; return true;   // cool blue
    case "exploring":   hue = 162f; return true;   // teal-green
    case "inspired":    hue = 285f; return true;   // bright purple
    case "reflecting":  hue = 262f; return true;   // deep indigo
    case "concerned":   hue = 28f;  return true;   // warm orange

────────────────────────────────────────────
DESKTOP BEHAVIOUR — PresenceProfile mapping
────────────────────────────────────────────

When presence_plan.desktop_presence is present, DesktopBuddy should
read it from EloOSAvatarReceiver.PresenceProfile and adjust behaviour:

    "engaged"   → normal walk speed, normal wander
    "ambient"   → slower wander, longer idle holds
    "listening" → minimal movement, head toward user
    "creative"  → slightly faster, curious head movement
    "thinking"  → very slow movement, minimal wander
    "celebrate" → brief bounce energy burst

This is a GENTLE INFLUENCE on existing DesktopBuddy behaviour — not a
new system. DesktopBuddy already has speed/wander controls; presence_profile
just nudges them. If DesktopBuddy already handles mode changes, route through
that.

────────────────────────────────────────────
COLOUR INTERPOLATION — IMPLEMENTATION
────────────────────────────────────────────

Target pattern for smooth colour transitions in EloOSChatTMP.cs:

    float currentHueH, targetHueH;   // fields
    float currentS, targetS;
    float currentV, targetV;
    float colourTransitionSpeed = 2f; // seconds (overridden by transition_speed)

    // In Update(), every frame:
    currentHueH = Mathf.LerpAngle(currentHueH, targetHueH,
                    Time.unscaledDeltaTime / colourTransitionSpeed);
    currentS    = Mathf.Lerp(currentS, targetS,
                    Time.unscaledDeltaTime / colourTransitionSpeed);
    currentV    = Mathf.Lerp(currentV, targetV,
                    Time.unscaledDeltaTime / colourTransitionSpeed);

    Color glowColor = Color.HSVToRGB(currentHueH / 360f, currentS, currentV);

    // Apply alpha separately (hover fade logic unchanged)

────────────────────────────────────────────
DONE WHEN
────────────────────────────────────────────

1. Five new moods added to MoodHueDeg() — compile passes, no errors
2. presence_plan block parsed from blender_state.json (null-safe)
3. EloBodyGlow.cs reads HSV from presence_plan when present
4. GlowHue() uses HSV from presence_plan when present, MoodHueDeg fallback
5. Colour transitions smoothly (lerp, not snap) between emotional states
6. Manually writing presence_plan.emotional_state = "creative_discovery" to
   blender_state.json → turquoise glow at H=175° appears within 2 seconds
7. Removing presence_plan block → system falls back to existing string-based
   mood system without error

────────────────────────────────────────────
FILE LOCATIONS
────────────────────────────────────────────

Unity project:  ~/Desktop/Output/DISENELO-eLoDesktopBuddy/
Scripts:        Assets/Scripts/
State file:     ~/elo-ai/blender/blender_state.json
Architecture:   ~/elo-ai/docs/architecture/11_emotional_light_engine.md
                (full HSV colour table and Presence Plan spec)
