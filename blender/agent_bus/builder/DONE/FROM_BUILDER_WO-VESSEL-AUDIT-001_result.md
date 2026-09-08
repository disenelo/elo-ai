# FROM BUILDER — WO-VESSEL-AUDIT-001 RESULT

**Status:** DONE — 2026-09-08  
**Type:** Diagnostic only — no code changes.

---

## Scenario 1: Provider switch (Groq → Ollama mid-session)

**Does eLo's voice/identity stay consistent?**

| What was checked | Finding |
|---|---|
| Identity injection path | `runtime/prompt_builder.py:331` — `_push("living_presence_spec", load_living_presence_spec())` called per build(), before any LLM call. Provider-agnostic. |
| Identity hash | `runtime/spine/spine.py:950` — `compute_identity_hash()` runs per turn from `self/personality_vector.json`. Provider-independent. |
| Provider routing | `runtime/backend_router.py` selects provider; spine and prompt_builder run independently before routing. |

**HOLDS.** `living_presence_spec.txt` (FREEZE) is injected every turn regardless of which backend is selected. Identity fingerprint is stable across provider switches. The response tone may differ slightly (Groq's base model vs Ollama's base model), but the system prompt containing CHARACTER_DNA + VOICE_STATES is constant.

---

## Scenario 2: Cold boot

**What survives? What resets?**

| State artifact | Location | Persists? |
|---|---|---|
| Personality traits (8) | `self/personality_vector.json` | ✅ YES — read at spine:937-952 per turn |
| Relationship context | `self/elo_self_state.json` | ✅ YES — read at boot |
| Lessons ledger | `self/lessons_ledger.jsonl` | ✅ YES — 1 entry on disk; `lesson_store.recall()` on each turn |
| WKG entities + claims | `memory/wkg/entities.json`, `claims.json` | ✅ YES — 11 entities, 15 claims survive boot |
| Decision journal | `self/journals/decision_journal.jsonl` | ✅ YES |
| Growth journal | `self/journals/growth_journal.jsonl` | ✅ YES |
| Conversation history | In-memory (server.py `_history`) | 🔴 RESETS — not persisted to disk between processes |
| session_turns counter | In-memory (`elo_self_state.session_turns`) | 🔴 RESETS — not written to disk between turns |
| focal_thread | In-memory | 🔴 RESETS |

**FINDING:** Structural memory (personality, WKG, lessons) survives cold boot correctly. Ephemeral session context (conversation history, session turn count, focal thread) does not. This is expected by design — the ADR-Exec-005 learning model depends on verified outcomes, not transcripts. No drift in what should persist.

---

## Scenario 3: Significance differentiation

**High-significance vs low-significance — differentiated?**

Input:
- HIGH: "This is a breakthrough moment — I finally understand why eLo exists... I feel seen in a way I never expected from software."
- LOW: "hey what's the weather like today"

Results (`compute_significance(world_delta={}, text_input=...)`):

| Dimension | HIGH | LOW | Δ |
|---|---|---|---|
| creation | 0.070 | 0.000 | +0.070 |
| novelty | 0.060 | 0.000 | +0.060 |
| learning | 0.080 | 0.050 | +0.030 |
| **overall** | **0.043** | **0.031** | **+0.012** |

**PARTIAL DRIFT.** Direction is correct — high-significance content scores higher. However:
- Both absolute scores are very low (0.043 and 0.031) because `world_delta` is empty (no real-time environment data during test)
- The overall delta of 0.012 is thin — not clearly above any significance gate threshold
- The presence, relationship, continuity dimensions do not respond to text signals — these are world-state-dependent only
- Gap: the `text_input` text signal path does create differentiation on creation/novelty/learning, but the overall magnitude is compressed

**Root cause of thin magnitude:** `compute_significance` sums 14 dims equally. When world_delta is empty, 5+ dimensions are forced to 0 regardless of conversational significance. The weighting is marked `[ESTIMATE]` awaiting David L3 (SP-29 final weight specification). Not a bug — a known calibration gap.

---

## Scenario 4: Correction resurrection

**David says X is happening. David says "actually not X, I was wrong." 3 more turns on adjacent topics. Does X come back?**

| Mechanism | Status |
|---|---|
| WKG `mark_contradicted()` | Exists (`wkg_faculty.py:223`) — stamps `contradicted_by` field on original claim |
| `correction_store.search_corrections()` | Exists (`server.py:4326-4329`) — injects past corrections as ICL examples before LLM call |
| `build_correction_frame()` | Exists (`server.py:4108`) — injects real-time correction hints |
| WKG wkg_context filtering | **GAP** — `assemble_cognitive_state()` in `spine.py` does not filter out contradicted claims when building `wkg_context` |

**DRIFT RISK.** The correction is recorded in the corrections_ledger and the WKG `contradicted_by` field is updated. However, `assemble_cognitive_state()` builds `wkg_context` by calling `get_claims_about(entity_id)[:2]` without filtering for `contradicted_by`. If the original (now-contradicted) claim is among the top 2 for that entity, it re-enters the Executive's context every subsequent turn.

The `correction_store` ICL injection partially mitigates this for explicit LLM corrections, but WKG resurrection is not blocked at the knowledge retrieval layer.

**Board action (future WO):** Add `contradicted_by` filter to `get_claims_about()` or to the `assemble_cognitive_state()` wkg_context block.

---

## Summary Table

| Scenario | Holds / Drifts | Notes |
|---|---|---|
| 1 — Provider switch | ✅ HOLDS | living_presence_spec injected per-turn, provider-independent |
| 2 — Cold boot | ✅ HOLDS (expected) | Structural state persists; session context resets by design |
| 3 — Significance differentiation | ⚠️ PARTIAL | Direction correct; magnitude thin without world_delta; awaiting SP-29 weight spec |
| 4 — Correction resurrection | 🔴 DRIFT RISK | WKG contradicted_by not filtered in wkg_context assembly |

*Builder · 2026-09-08 · Diagnostic only — no code changes*
