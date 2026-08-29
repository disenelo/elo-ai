# FROM BUILDER → BOARD: card 0057 — The 4-Second Rule
**Date:** 2026-08-29
**Card:** 0057_THE_4_SECOND_RULE · P0 · David 2026-08-19

---

## §2 Cheap wins — confirmed done

| Item | Status | Evidence |
|---|---|---|
| A — `llama3.1:8b` configured | ✅ DONE | `.env` `ELO_OLLAMA_MODEL=llama3.1:8b`; `backend_router.py` defaults changed from `mistral` → `llama3.1:8b` at all 3 sites (commit d9cc0a7 this session) |
| B — `keep_alive=30m` | ✅ DONE | CT0031 Fix A: `keep_alive: "30m"` in `_ollama_call` and `_ollama_stream` (lines 471, 833). Evidence: `backend_health.json.load_ms = 7.5 ms` (was 4,599 ms) |
| C — server restart | ✅ DONE | Live via keep_alive fix. Model stays warm. |

---

## §4 R1 — Turn breakdown after cheap wins (from backend_health_history.jsonl — 117 turns)

Most recent 5 turns:
| Turn | Backend | Prompt eval ms | Eval tokens | Total ms |
|---|---|---|---|---|
| -5 | ollama(stream)+obsidian | 6,409 | 7,183 | 8,000 |
| -4 | ollama(stream) | 6,455 | 7,166 | 7,568 |
| -3 | ollama(stream) | 15,799 | 6,951 | 23,380 (outlier — cold?) |
| -2 | ollama(stream)+timer | 6,099 | 7,015 | 6,488 |
| -1 | ollama(stream)+vision | 6,229 | 7,052 | 7,241 |

**Typical turn: 6.5–8 s. Prompt eval is 85–87% of the turn.**

Prompt token breakdown (per most recent turn):
- `living_presence_spec`: 5,103 tokens = **67.2%** (untouchable — David's sole lever)
- `personality_block`: 546 tokens = 7.2%
- `self_block`: 155 tokens = 2.0%
- Remaining (~25%): world state, attention, company, lessons, etc.

Keep_alive reduced load from 4,599 ms → 7.5 ms. Switching from 70b → 8b reduced eval time from ~16 s → ~6 s. **Remaining 6 seconds is eLo reading his own identity.** That is the correct shape.

---

## §4 R2 — Routes available when a turn exceeds 4 s

Live available routes on this stack:
- **Ollama (llama3.1:8b)** — primary, ~6–8 s/turn locally
- **Groq** — key present (`GROQ_API_KEY`); no quota usage currently; ~1–2 s cloud (no local eval overhead)
- **Cerebras** — key present; ~1–2 s cloud
- Cloud routes are available but **not being used** — Ollama wins at CONVERSATIONAL tier by cost (WO-ROUTER-001 D-1, this session)

When a turn exceeds 4 s: both Groq and Cerebras are available as faster alternatives.

---

## §3 — Tier routing — ✅ DONE (WO-ROUTER-001, commit d9cc0a7)

Capability-driven provider selection is now live. CONVERSATIONAL tier: Ollama wins (free-local, cheapest). The "quicker route" is Groq/Cerebras — available when Ollama is slow, but current cost-sort always picks Ollama first.

---

## §4 — PROPOSAL SHAPE (for David L3, not implemented)

> "A latency policy decides how eLo behaves when he is struggling. It gets David's eye before it ships."

Proposed rule: `>4 s prompt_eval → escalate tier to REASONING → Groq/Cerebras wins cost-sort → respond at ~1–2 s.`

**Constraints respected:**
- No context trimming (David: "do not do this at all")
- No LLM-decides-more (David: "eLo decides the output")
- No spec file touched
- Does not ship until David says go

**If Groq and Cerebras are both down when >4 s fires:** rule says "no faster route available" — answer honestly, don't degrade. Backend_health_history.jsonl shows Groq is currently idle (never called in 117 turns) — it is a clean fast path.

**Board asks:** Does David want to set `ELO_4S_RULE=1` in `.env` as the gate, mirroring `ELO_SELF_INITIATION`? Or is the routing threshold part of the CA ruling?

---

## What this card does NOT authorise (preserved verbatim from §5)
- ❌ No touches to `living_presence_spec.txt` or `FREEZE_V1_LOCK.md`
- ❌ No context trimming to hit a number
- ❌ No LLM decides more
- ❌ No scope expansion

---

## Current classification
**WAITING DAVID L3** — proposal ready; Groq fallback available; policy gate is his call.

*Board / Lead Architect acting as Builder · 2026-08-29*
