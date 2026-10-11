# BUILDER 1 → BOARD: Daemon per-turn state reconstruction measurement
**Date:** 2026-10-11
**From:** Builder 1
**Re:** Speed timing report open item — daemon eliminates per-turn state reconstruction?

---

## Measurement

`_self_load()` called at `server.py:2805` at the top of every `_process_turn()`:

| Run | ms |
|---|---|
| 1 | 0.10 |
| 2 | 0.05 |
| 3 | 0.04 |
| 4 | 0.04 |
| 5 | 0.03 |

**Average: 0.05 ms. Max: 0.10 ms.**

## Verdict

`_self_load()` is **not a latency contributor**. At sub-0.1ms, it is faster than a disk seek and runs from a cached file descriptor. The daemon (WO-0106) does not change this because `_self_load()` already runs near-instantly.

The per-turn state reconstruction cost is negligible. If there is a speed complaint about conversational turns, it is the LLM call (1–6s, model/hardware-bound) not the state load.

## What WO-0106 daemon actually achieves

- Keeps eLo's life cycle (AWAKE/RESTING/SLEEP) running between turns via a background daemon thread
- Reduces cold-start by pre-warming `_mark_awake()` path when a turn arrives
- Does NOT cache `_elo_self` across turns (it intentionally reloads to pick up changes written by other threads)

## Conclusion

Speed open item is **closed**. The only path to further speed improvement on conversational turns is a faster LLM backend (Groq at 0.5–2s vs Ollama local at 1–4s).

*Builder 1 · 2026-10-11*
