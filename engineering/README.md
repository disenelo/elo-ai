# eLo OS Engineering Programme v1

**Status: ACTIVE**
**Started: 2026-07-10**
**Owner: David Charles / DISENELO**

---

## What This Is

This is the build programme for eLo OS — not code, not architecture, not prompts. The engineering discipline that governs how every phase is designed, built, validated, frozen, and handed forward.

Every phase follows the same lifecycle. Every Claude instance working on eLo reads the relevant playbook before touching anything. Every freeze is documented. Nothing advances without evidence.

This is how you build something that lasts 12–18 months without losing coherence.

---

## The Core Principle

> "Presence comes less from adding more capabilities and more from ensuring the cognitive pipeline accurately tracks what matters in the moment before deciding whether to speak."
> — David Charles, 2026-07-10

Every decision in this programme traces back to that sentence.

---

## The Two Eras

**Engineering Era** — WP_A through WP_I. The purpose is proof. Not features. Not improvement. Proof that every part of the cognition is coherent, isolated, and frozen.

```
WP_A  Engineering Manual        ← The discipline itself
WP_B  One Brain Validation      ← Prove the entire runtime is one cognition
WP_C  Language Faculty          ← Validate the language layer
WP_D  Memory Faculty            ← Validate the memory layer
WP_E  Attention Faculty         ← Validate the attention layer
WP_F  Relationship Faculty      ← Validate the relationship layer
WP_G  Executive Faculty         ← Validate the executive layer
WP_H  Cognitive Plan + Spine    ← Validate the integration layer
WP_X  Behaviour Consistency     ← Prove every embodiment thinks the same
WP_I  Cross-Embodiment          ← Formal hardware + software integration freeze
         ↓
      ENGINEERING ERA FREEZE
```

**Life Era** — after the Engineering Era freeze. The cognition is finished. It gains new senses, new bodies, new tools, new worlds. The brain does not change.

```
Desktop Life              ← eLo present throughout the creative day
Creative Collaboration    ← eLo participates in creative work, not just responds
World Participation       ← eLo-Planet + real world awareness merge
Robot Presence            ← Physical eLo, same brain
Learning Through Experience ← Memory deepens from shared history
Shared History            ← Long-term continuity
Long-term Evolution       ← eLo grows through time
```

The Engineering Era ends when WP_I freezes.
The Life Era begins when the first embodiment gains a new sense.

---

## Architecture Constants (Never Change)

These are not preferences. They are invariants. Every review checks against them.

1. **One Brain.** Single cognitive process across all embodiments. Desktop, Unity, Robot, Mobile — same brain, different bodies.
2. **One Executive.** The Executive Faculty is the only decision-maker. No other faculty decides.
3. **Faculties observe. Executive decides. Presence embodies.**
4. **FREEZE_V1_LOCK.** `runtime/executive.py` and `prompts/` are permanently frozen. Infrastructure evolves around them.
5. **Silence is valid output.** No faculty is required to contribute. Empty = nothing happens.
6. **Evidence gates expansion.** No phase begins implementation until the prior phase passes validation.

---

## Phase Sequence

| Phase | Name | Status |
|---|---|---|
| 0 | Philosophy | ✅ FROZEN |
| 1 | Cognitive Foundation | ✅ FROZEN |
| 2 | Cognitive Infrastructure | 🟡 REVIEW → FREEZE |
| 2.5 | Cognitive Validation | ⏳ PLAYBOOK READY — AWAITING RUNTIME |
| 3 | Semantic World Model | 📐 ARCHITECTURE PHASE |
| 3.5 | Working Context | 📐 ARCHITECTURE PHASE |
| X | Self Model | ○ |
| 4 | Participation | ○ |
| 5 | Relationship Intelligence | ○ |
| 6 | Presence | ⚠️ PARTIAL (Desktop Buddy running) |
| 7 | Avatar Intelligence | ○ |
| 8 | Voice Intelligence | ⚠️ PARTIAL (ElevenLabs + phoneme lipsync live) |
| 9 | Embodiment | ○ |
| 10 | World Awareness | ○ |
| 11 | Initiative | ○ |
| 12 | Companion Intelligence | ○ |
| 13 | Studio Intelligence | ○ |
| 14 | Robot | ○ |
| 15 | World Loop | ○ |

---

## Engineering Lifecycle (Every Phase)

```
1.  Architecture Review      Read everything. Produce a report. No code.
2.  Current State Audit      What exists. What works. What is broken.
3.  Gap Analysis             What is missing. What Phase N needs that prior phases don't provide.
4.  Runtime Design           Exactly how data flows. Interfaces. Contracts.
5.  Implementation           Write the code.
6.  Unit Tests               Test individual components in isolation.
7.  Conversation Tests       Talk to eLo. Break eLo. Validate behaviour.
8.  Stress Tests             Long sessions. Edge cases. Unexpected sequences.
9.  Regression               Run prior phase tests. Nothing new breaks old behaviour.
10. Freeze Decision          Approve / Reject / Rollback.
11. Architecture Update      Update architecture docs to reflect what was built.
12. Handover                 What the next phase needs to know.
```

---

## Directory Structure

```
engineering/
    README.md                        ← This file — the Engineering Manual

    /templates/                      ← Reusable document templates
        architecture_review.md
        implementation_plan.md
        diagnostics.md
        regression.md
        freeze.md
        handover.md

    /playbooks/                      ← Full playbook for any work package
        phase_template.md

    /standards/                      ← Architectural and engineering rules
        architecture.md
        coding.md
        testing.md
        documentation.md

    /work_packages/                  ← Formal work package definitions
        WP_A_ENGINEERING_MANUAL.md   ← How eLo is built (this programme)
        WP_B_ONE_BRAIN.md            ← One Brain validation & architectural trace
        WP_C_LANGUAGE_FACULTY.md
        WP_D_MEMORY_FACULTY.md
        WP_E_ATTENTION_FACULTY.md
        WP_F_RELATIONSHIP_FACULTY.md
        WP_G_EXECUTIVE_FACULTY.md
        WP_H_COGNITIVE_PLAN_SPINE.md
        WP_X_BEHAVIOUR_CONSISTENCY.md ← Behaviour consistency across all embodiments
        WP_I_CROSS_EMBODIMENT.md     ← Formal cross-embodiment validation + freeze

    /proofs/                         ← Evidence that each part of the design has been validated
        00_one_brain_proof.md        ← Created during WP_B
        01_language_proof.md         ← Created during WP_C
        02_memory_proof.md           ← Created during WP_D
        03_attention_proof.md        ← Created during WP_E
        04_relationship_proof.md     ← Created during WP_F
        05_executive_proof.md        ← Created during WP_G
        06_spine_proof.md            ← Created during WP_H
        07_behaviour_proof.md        ← Created during WP_X
        08_embodiment_proof.md       ← Created during WP_I

    /Volume_1_Framework/             ← In-depth framework documents (existing)
    /TEMPLATE_PhasePlaybook/         ← Phase playbook template (existing)
    /Phase_02_*/                     ← Phase 2 complete playbook (existing)
    /Phase_025_*/                    ← Phase 2.5 complete playbook (existing)
    /Phase_03_*/                     ← Phase 3 complete playbook (existing)
    /Phase_035_*/                    ← Phase 3.5 complete playbook (existing)
```

`engineering/` defines **how eLo evolves**.
`docs/architecture/` defines **what eLo is**.
These are separate and stay separate.

---

## How to Use This Programme

**Starting a new phase:**
1. Copy `TEMPLATE_PhasePlaybook/` → `Phase_NN_Name/`
2. Open `01_review.md`. Use the Architecture Review prompt from Volume 1 Prompt Library.
3. Complete each document in order. Do not skip.
4. `10_freeze.md` is the gate. Nothing moves forward until it's signed.

**Picking up mid-phase:**
1. Read `10_freeze.md` — if blank, phase is not frozen.
2. Read the highest-numbered doc that has content.
3. Continue from there.

**After a freeze:**
1. `11_handover.md` must be complete.
2. Status table above updates to ✅ FROZEN.
3. Next phase folder is created.

---

## Security Rules

- `.env` is GITIGNORED. Never commit.
- `runtime/executive.py` and `prompts/` — FREEZE_V1_LOCK. Never modify.
- `logs/pending_commits.jsonl` — system never auto-commits to git.
- ElevenLabs, Cerebras, AccuWeather API keys — `.env` only.
