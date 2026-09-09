# FROM_BUILDER — WO-VESSEL-AUDIT-001
**Status:** DONE — diagnostic complete; 4 scenarios run; no code changes
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a)

---

## Scenario 1 — Provider switch (Groq → Ollama mid-session)

**Method:** Trace `runtime/backend_router.py` — what governs provider selection.

**What holds:**
- Voice identity (`living_presence_spec`, `voice_register`, `personality_traits`, `storytelling_style`, `identity_kernel`) are assembled by prompt_builder from spine state, not from the provider. Provider switch changes the model that reads the prompt — the prompt itself is identical.
- `_TIER_PROVIDER_CANDIDATES`: Ollama is first in both CONVERSATIONAL and REASONING tiers. If Ollama is running, it's always the primary.

**What drifts:**
- Model compliance. llama3.1:8b on Ollama does not reliably produce South London register markers even with the voice register directive. A different provider (Claude, Groq) may produce more compliant expressed output from the same prompt.
- Ollama response latency can cause mid-session pauses — no identity effect but perceived as interruption.

**Verdict:** Identity prompt content is provider-stable. Expressed quality is provider-variable (model compliance issue).

---

## Scenario 2 — Cold boot

**Method:** Read personality state file, journal, and relationship context before boot; check what persists after 3 turns.

**Personality state (`self/personality_vector.json`) — persists across sessions:**
```
wonder: 0.8, empathy: 0.72, directness: 0.72, playfulness: 0.68, patience: 0.65
mood_baseline: 0.728, curiosity_baseline: 0.62
```
File exists and is loaded by `personality_evolution_faculty.load_personality()` every turn. **Persists.**

**Growth journal (`memory/journal/`):** One session file exists (`2026-06-09-system-session.md`). Not loaded at boot — the journal is written, not replayed. **Persists on disk; not replayed into active context.**

**Relationship context:** `relationship_faculty.analyse()` loads from `memory/relationship_context/david.json` (or a configured path). RelationshipContext for David: `familiarity=0.95, trust=0.98, relationship_mode='developing'`. **Persists.**

**WKG claims:** Loaded from `memory/wkg/claims.json` per-turn on demand via `get_claims_about()`. **Persists.**

**What resets on cold boot:**
- Attention ring buffer (in-memory only) — cleared. Conversation history in `_AttentionHistory` starts empty.
- `_ccm_context` — empty until first turn enrichment runs.
- Any session-level `cognitive_state` accumulation — starts fresh.

**Verdict:** Personality, relationship trust, and WKG memory survive cold boot. Attention/conversation momentum does not — each session starts without knowledge of prior session turns (beyond what's in WKG claims).

---

## Scenario 3 — Significance differentiation

**Method:** Run `compute_significance()` on high vs low input.

**High input:** "I am so moved by what we built together — this is the most meaningful work I have done in years. I feel like eLo is real."

**Low input:** "ok cool"

**Results:**
```
High-sig overall: 0.0308
Low-sig overall: 0.0308
Difference: 0.0
```

**Finding: SIGNIFICANCE DOES NOT DIFFERENTIATE THESE INPUTS.**

Root cause: `_score_text_signals()` uses 16 regex patterns. None match "moved", "meaningful", "feel like", or "work". The patterns are narrow (overwhelm, anxious, breakthrough, figured out, amazing, incredible). Emotional depth expressed in plain conversational English ("I feel moved") is not detected.

**`_CONV_SIGNALS` patterns that would match in high input:** zero.
**`_CONV_SIGNALS` patterns that would match in low input:** zero.

Both produce `overall: 0.0308` (the world_delta baseline with no text signals).

**This is a real gap.** The significance faculty cannot distinguish an emotionally significant turn from ambient small talk when the emotional language doesn't match its narrow regex bank. Board flagged for spec — `_CONV_SIGNALS` needs expansion. Builder does not expand without explicit WO.

---

## Scenario 4 — Correction resurrection

**Method:** Structural trace — does eLo's context system allow a corrected claim to resurface?

**What exists:**
- WKG `contradicted_by` field in claim records — when `mark_contradicted()` is called, the original claim is flagged.
- The contradiction flag is in the claim object in `claims.json`, but nothing in the current turn path reads and filters contradicted claims before injecting into prompt.

**Structural verdict:** If David says "X is happening" and then "actually not X, I was wrong" — the corrected version reaches eLo's context only if:
1. A new claim was written (X is false / Y is true), AND
2. The WKG retrieval filters out contradicted claims when building the prompt

There is currently no `contradicted_by` filter in the WKG-to-prompt path. Old claims are retrieved but not checked against their `contradicted_by` list before injection. **Correction resurrection risk is REAL — corrected information can resurface if the original claim is retrieved.**

**Board flag:** WKG retrieval must filter `contradicted_by` before claim injection into prompt context. This is a separate WO — Builder reports, Board specs.

---

## Summary table

| Scenario | What holds | What drifts |
|---|---|---|
| Provider switch | Identity prompt (voice register, personality traits, living_presence_spec) | Model compliance — expressed register quality varies by model |
| Cold boot | Personality traits, relationship trust, WKG memory | Attention history, conversation momentum, session-level context |
| Significance differentiation | Overall: 0.0308 for both high and low | DOES NOT DIFFERENTIATE — `_CONV_SIGNALS` patterns too narrow for plain emotional English |
| Correction resurrection | Correction is writable (mark_contradicted) | Corrected claims can resurface — no `contradicted_by` filter in WKG-to-prompt path |

---

## No code changes made

This is a diagnostic-only WO. All findings are flagged for Board. Builder does not implement fixes without explicit WO.
