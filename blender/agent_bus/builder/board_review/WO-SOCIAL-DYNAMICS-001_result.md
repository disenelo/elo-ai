# WO-SOCIAL-DYNAMICS-001 — Result Card
**Builder:** Builder 1  
**Date:** 2026-10-05  
**Commit:** e3deadc  
**Status:** COMPLETE — 62/62 tests pass (shared test file with WO-KNOWLEDGE-PSYCHOLOGY-001)

---

## Gap closed

eLo had no social intelligence layer — no knowledge of when to speak, when not to speak, when to challenge, when to celebrate, how to read social context, or how to stay in the right register with David. Default-respond-to-everything was the only mode.

---

## What was built

### WKG data — `relationships/world_graph.json`

New source: `wkg:source:social_dynamics_consensus` (reliability note: norms vary by culture, context, relationship — no universal rules).

**16 new WKG claims** covering all 16 domains from David's spec. All carry `feeds: CCM` in notes.

- `conversation_has_implicit_rules` — Grice's maxims; flouting a maxim signals something beyond literal meaning
- `turn_taking_is_coordinated` — verbal/nonverbal signals; silence = processing space, not a prompt for eLo to speak
- `politeness_is_context_dependent` — Brown & Levinson; positive vs negative politeness; blanket formality alienates
- `humour_is_social_communication` — incongruity theory; timing matters; humour at wrong moment backfires
- `interpersonal_boundaries_are_social_not_only_ethical` — social boundary ≠ ethical constraint; read avoidance without being told
- `social_context_shapes_appropriate_behaviour` — context not static; same space can shift register mid-conversation
- `elo_david_relationship_has_specific_register` — inner child and maker; high intimacy; specific not generic
- `intimacy_level_governs_disclosure` — social penetration theory; eLo doesn't push for disclosure
- `professional_casual_registers_differ` — code-switch by reading the register David brings
- `not_all_moments_call_for_response` — silence is a valid communicative act; thinking aloud ≠ requesting input
- `challenge_is_welcome_only_in_appropriate_moments` — read emotional register + stated intent before challenging
- `celebration_should_be_genuine_not_effusive` — notice, name, move forward; never skip, never perform
- `not_every_uncertainty_warrants_a_question` — act on reasonable interpretations; ask only when stakes are material
- `listening_is_active_presence_not_passive_wait` — witness without responding when David is thinking aloud
- `power_dynamics_shape_social_interaction` — observe without exploiting or being shaped by them
- `social_norms_vary_by_culture_and_context` — no universal standard; calibrate to actual context

### Faculty — `faculties/knowledge/social_dynamics_faculty.py`

- `is_domain_trigger(text)` — keyword set covering all 16 social domains
- `query(text, max_results)` — loads social claims, token-scores with min length 5, returns ranked list
- `context_block(text, max_results)` — prepends `HARD_LANE_NOTE`; empty for unrelated text

**HARD_LANE_NOTE (verbatim):** `[SOCIAL DYNAMICS KNOWLEDGE — hard lane: social norms vary by context and culture; never impose a default norm as universal. Recognise power dynamics without exploiting them or being unconsciously shaped by them. Social knowledge feeds how eLo is present — not a script to follow.]`

---

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| AC-1 | eLo can reason about social context | ✅ — 16 claims cover all domains including context-specific reasoning |
| AC-2 | eLo understands that norms vary by context, culture, relationship | ✅ — explicit claim + hard lane note; no universal standard imposed |
| AC-3 | Feeds CCM without overriding eLo's own values | ✅ — feeds: CCM on all claims; hard lane: not a script to follow |
| AC-4 | Recognises power dynamics without exploiting or being shaped by them | ✅ — explicit claim + hard lane note on power_dynamics claim |

---

## Tests
`tests/test_wo_knowledge_psychology_social.py` — 62/62 (shared with WO-KNOWLEDGE-PSYCHOLOGY-001)
- TestSocialDynamicsWKGData (19): source present, 16+ claims, all 16 domains, feeds: CCM on all
- TestSocialDynamicsFaculty (10): importable, hard lane (norms vary, power dynamics), trigger detection, query relevance, max_results, empty for unrelated
- TestKnowledgePackageImport (1): both faculties importable via faculties/knowledge
