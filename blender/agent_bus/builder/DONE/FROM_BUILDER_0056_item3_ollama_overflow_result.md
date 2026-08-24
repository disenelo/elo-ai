# FROM_BUILDER — 0056 item 3 + 0057 §2A/§2B/§3/R1 Result
**Seat:** Builder  
**Cards:** 0056 item 3 · 0057 §2A/§2B/§3/R1  
**Commits:** `bce1369` (llm_latency_ms in history), `c54e502` (outbox evidence)  
**Date:** 2026-08-24  

---

## 0056 item 3 — Ollama overflow measurement

`tests/measure_0052_ollama_overflow.py` run live against Ollama (llama3.1:8b, port 11434).

| Metric | Result |
|---|---|
| M1: prompt tokens / num_ctx | 7,394 / 8,192 = **90.3%** capacity · 798 tok headroom |
| M2/M4: Ollama at overflow | **Does NOT error — silently truncates** to num_ctx. No prompt_eval_count alarm. |
| M3: Block order (prompt_builder.py:304-330) | `[0] spec (frozen, ~4,460 tok)` → `[1] personality` → `[2] self` → `[3] lessons` → `[4] memory` → `[5] user turn` |
| M5: Growth rate | ~98 tok/day (2-point window, low confidence). ~7.3 days to overflow at current rate. |

**Open:** truncation direction not established from token count alone. If Ollama truncates from the front, spec (character DNA) is first to go — that is a Rule-1 level risk. Content-marker test required to confirm direction.

**Growth cause:** vault_context (lessons accumulate), self_block (facts.json grows), HEURISTICS.

---

## 0057 §2A/§2B resolved; §3 wired; R1 done

### §2A — 70b vs 8b
`ollama list` shows only `llama3.1:8b` (4.9 GB). 70b was never downloaded. The card's premise was incorrect — already resolved before this session.

### §2B — keep_alive
Direct timing across two back-to-back turns:
- Turn 1: load_ms=2.9, prompt_eval_ms=178, wall=491ms
- Turn 2 (warm): load_ms=**0.7ms**, prompt_eval_ms=82ms, wall=127ms

`keep_alive=30m` is working. Model stays resident. The 4.6s cold-load penalty the card named is NOT firing between back-to-back turns. Primary bottleneck is prompt_eval: ~6,700ms at full 7,394-token context (~77% of a turn as the card diagrams).

### §3 — Tier routing wired
`backend_router.py:1034-1038` fires `_route_by_tier()` using `_derived_tier = tier or _action_default_tier(action)`. `_action_default_tier` defaults to `_TIER_CONVERSATIONAL` (1) for unknown actions → all actions use the Ollama-first provider order.

**Currently gated:** `ELO_BACKEND=mock` in `.env` causes the condition `not os.environ.get("ELO_BACKEND", "")` to be False — tier routing is bypassed while mock is active. David fixes `.env` → tier routing fires.

### §4 R1 — Per-turn latency history
`server.py:4073` (commit `bce1369`) now writes `llm_latency_ms` to `backend_health_history.jsonl` alongside the Ollama phase breakdown (`load_ms / prompt_eval_ms / gen_ms`). Total LLM wall-clock is now recorded for every backend, not only Ollama.

---

## What remains blocked (report to Architect/David)

| Item | Blocker |
|---|---|
| 0056 items 4–6 (WO-048/061/022/037 live tests + WO-045 EXIT + baseline freeze) | David must fix `.env` (5 uncommented ELO_BACKEND lines, last-wins=mock). **DO NOT EDIT — it is David's.** |
| 0057 R2 (routes available when >4s) | Same `.env` fix + Groq key active |
| 0057 policy proposal | Blocked on R2 measurement |
| 0081 parity gate (XI-AD-2) | Needs live Unity moves to emit `brain_route` + `unity_route` into route_memory.jsonl |
| 05b WO-112 | executive.py frozen (L3/canon D3). Architect must unfreeze or reroute responsibility. |

**David action required:** open `.env`, comment out the bottom 4 `ELO_BACKEND` lines, leave only the one intended backend uncommented, restart server. That unblocks 0056 items 4–6 and 0057 R2 in one go.

---

*Builder · 2026-08-24*
