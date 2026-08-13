# WP_H — Cognitive Plan and Spine Audit

**Status:** PENDING
**Priority:** HIGH
**Depends On:** WP_G (Executive audited)
**Architecture Reference:** `docs/architecture/10_cognitive_plan.md`, `docs/architecture/16_spine_runtime.md`, `docs/architecture/13_conversation_faculty.md`, `docs/architecture/14_presence_faculty.md`, `docs/architecture/15_execution_gate.md`

---

## Purpose

Audit the Cognitive Plan and Spine. The spine is the assembly layer — it collects all faculty outputs, runs the Executive, and produces a CognitivePlan that drives both the response and embodiment. It is the single integration point.

---

## Objective

At the end of WP_H:
- The CognitivePlan dataclass fields are all validated and documented
- The spine's integration of every faculty is traced and confirmed
- The conversation faculty (direct response pools) is validated
- The presence faculty (blender_state.json write) is validated
- The execution gate is validated
- The spine is frozen

---

## Existing Architecture Review Required

**Files to audit:**

| File | Role |
|---|---|
| `runtime/spine/spine.py` | The integration layer |
| `runtime/spine/plan.py` | CognitivePlan dataclass |
| `runtime/spine/executive_faculty.py` | Executive enrichment |
| `runtime/spine/relationship_faculty.py` | Relationship enrichment |
| `server.py` — spine call and response path | How spine output becomes response |
| `docs/architecture/10_cognitive_plan.md` | Architecture specification |
| `docs/architecture/16_spine_runtime.md` | Spine runtime specification |

---

## CognitivePlan Fields Audit

| Field | Purpose | Source | Validated? |
|---|---|---|---|
| conversation_action | CAL action | Executive | |
| tone | Voice tone | Executive | |
| max_sentences | Length cap | Executive | |
| response_goal | Response objective | Executive | |
| valence | Emotional valence | Executive | |
| momentum | Session momentum | Executive | |
| mode | Conversation mode | Executive | |
| register | Language register | Language / Executive | |
| direct_response | Pre-LLM pool response | Conversation Faculty | |
| direct_backend | Backend label for direct | — | |
| system_action | OS action to execute | System Faculty | |
| system_arg | Argument for action | System Faculty | |
| system_immediate | Execute now or gate? | Execution Gate | |
| system_pending | Awaiting confirmation? | Execution Gate | |
| system_desc | Confirmation description | Execution Gate | |
| capabilities | Selected agent capabilities | Capability Faculty | |
| presence_plan | Embodiment state | Presence Faculty | |
| control_context | Additional system context | — | |

---

## Key Audit Questions

1. Does `direct_response` always draw from a fixed pool? Can any path set `direct_response` to LLM-generated content?
2. When the spine fails (`_plan = None`), what happens? Does the server fall through gracefully?
3. Does `presence_plan` correctly drive `blender_state.json`?
4. Are there any fields in CognitivePlan that are set but never read downstream?

---

## Freeze Criteria

- [ ] All CognitivePlan fields traced from source to consumer
- [ ] `direct_response` paths confirmed to use fixed pools only
- [ ] Spine failure graceful fallback confirmed
- [ ] Presence plan validated against blender_state.json
- [ ] Execution gate validated
- [ ] Regression tests pass (B through G regressions must pass)
