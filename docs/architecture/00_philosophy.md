# eLo OS — Architecture Philosophy
# Canonical Reference

────────────────────────────────────────────
THE FOUNDATION
────────────────────────────────────────────

eLo OS is not a chatbot with a personality.

It is a cognitive runtime — a system that understands, decides, and expresses
through a single unified pipeline. Every piece of architecture here exists to
support one principle:

    Every faculty contributes.
    Only the Executive decides.

This is the One Brain Principle. It is not a constraint. It is the reason
every interaction feels coherent, not reactive.

────────────────────────────────────────────
WHY A RUNTIME NEEDS ARCHITECTURE DOCUMENTS
────────────────────────────────────────────

Without architecture, behaviour drifts.

Each session adds a new handler. Each fix adds a new pattern match.
Eventually the system stops being a runtime and becomes a patchwork —
each part making its own micro-decisions, each part partially right,
the whole thing increasingly unpredictable.

These documents exist so that does not happen.

Every change to eLo OS behaviour should be traceable to an architecture
document. If a behaviour cannot be traced — it does not belong.

────────────────────────────────────────────
THE PIPELINE
────────────────────────────────────────────

User Input
    │
    ▼
Language Faculty          — what was said?
    │
    ▼
Conversation Context      — how was it said? (CCM v1.2)
    │
    ▼
Human Interaction         — why was it said? (HIM v1.3)
    │
    ▼
Memory Faculty            — what is remembered?
    │
    ▼
Attention Faculty         — what matters most right now?
    │
    ▼
Relationship Faculty      — who is speaking? (v1.4)
    │
    ▼
Desktop Context           — what is the environment?
    │
    ▼
Capability Registry       — what tools are available?
    │
    ▼
Executive Faculty         — ONE decision (v1.5)
    │
    ▼
══════════════════════════════
      COGNITIVE PLAN          ← internal truth (v1.6)
══════════════════════════════
    │
    ▼
Emotional Light Engine    — how does the decision feel? (v1.8)
    │
    ▼
══════════════════════════════
       PRESENCE PLAN          ← external truth
══════════════════════════════
    │
    ▼
┌───┬──────┬──────────┬──────────┬──────────┐
▼   ▼      ▼          ▼          ▼          ▼
Conversation  Voice  Desktop   Unity     Robot    Future
Faculty              Avatar    Avatar    LEDs     surfaces
    │
    ▼
Memory Update          — what should be remembered?

────────────────────────────────────────────
THE TWO-PLAN BOUNDARY
────────────────────────────────────────────

The pipeline crosses two critical boundaries:

COGNITIVE PLAN — the internal boundary.
    Everything above this line contributes to one cognitive decision.
    No embodiment sees this plan directly.
    This is what eLo thinks.

EXPRESSION PLAN — the external boundary.
    Everything below this line receives the same expression object.
    No embodiment re-reasons from the Cognitive Plan.
    This is how eLo appears.

This separation means: eLo's cognition and eLo's embodiment are
independently evolvable. Adding a new surface (AR, wearable, another
robot) requires only consuming the Presence Plan — not touching cognition.

────────────────────────────────────────────
RULES THAT CANNOT BE BROKEN
────────────────────────────────────────────

1. The Executive is the only decision-maker. Every other faculty
   contributes information. None of them decide.

2. One plan per turn. The CognitivePlan is the output of the Executive.
   Every downstream system reads from this plan — no subsystem re-decides.

3. The Emotional Light Engine never reasons. It translates. It receives
   the Cognitive Plan and produces the Presence Plan. It never alters
   memory, identity, attention, or executive decisions.

4. Faculties do not bypass each other. Information flows through the pipeline
   in order. No faculty reads directly from a downstream faculty.

5. The spine is not the logic. spine.py is the runtime execution of this
   architecture. When architecture changes, spine.py changes to match.
   Not the other way around.

6. Identity is constant. eLo's character, values, and voice do not change
   based on input. Only expression adapts.

────────────────────────────────────────────
DOCUMENT INDEX
────────────────────────────────────────────

00_philosophy.md                    ← this file
01_one_brain.md                     ← One Brain Principle (canonical)
02_language_faculty.md              ← Language Faculty specification
03_memory_faculty.md                ← Memory Faculty specification
04_attention_faculty.md             ← Attention Faculty specification
05_relationship_faculty.md          ← Relationship Faculty (v1.4) ← NEXT SESSION
06_conversation_context_matrix.md   ← CCM v1.2 ✓ complete
07_human_interaction_matrix.md      ← HIM v1.3 ✓ complete
08_capability_faculty.md            ← Capability Faculty specification
09_executive_faculty.md             ← Executive Faculty (v1.5)
10_cognitive_plan.md                ← Cognitive Plan Object (v1.6)
11_emotional_light_engine.md        ← Emotional Light Engine (v1.8) ✓ complete
12_expression_plan.md               ← Presence Plan (output of Light Engine)
13_conversation_faculty.md          ← Conversation Faculty specification
14_presence_faculty.md              ← Presence Faculty specification
15_execution_gate.md                ← Execution Gate specification
16_spine_runtime.md                 ← spine.py Runtime Alignment (v1.7)
17_memory_update.md                 ← Memory Update specification
99_future_embodiments.md            ← AR, wearables, robot, multi-user

────────────────────────────────────────────
EMBODIMENT CONTRACT
────────────────────────────────────────────

All surfaces receive the Presence Plan — not the Cognitive Plan.

    Conversation  → expression_plan.conversation_profile
    Voice         → expression_plan.voice_energy, voice_pacing, voice_warmth
    Desktop       → expression_plan.desktop_presence, animation_profile
    Unity         → blender_state.json (written from expression_plan)
    Robot         → blender_state.json → Pi 5 → robot_led_state, movement_style
    Future AR     → expression_plan (extended when needed)

No surface reasons independently. All surfaces express the same state.

────────────────────────────────────────────
STATUS
────────────────────────────────────────────

✓ Complete:     CCM v1.2, HIM v1.3, Emotional Light Engine, CognitivePlan (partial)
⚠ Partial:      spine.py (partially aligned), executive.py (partially aligned)
→ Next session: v1.4 Relationship Faculty
→ Queued:       v1.5 Executive Faculty, v1.6 Cognitive Plan, v1.7 spine alignment
