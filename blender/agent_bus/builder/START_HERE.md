# BUILDER — START HERE
### Updated: 2026-09-22 — P0 gate cleared

---

## YOUR QUEUE IS NOW IN: `engineering/cap_wos/`

To find your next WO:
```bash
python3 engineering/cap_wos/state_report.py
ls engineering/cap_wos/queue/*.json | sort | head -1
```

**On pickup:** move the JSON from `queue/` to `in_progress/`, update `"state": "in_progress"`.
**On evidence filed:** move to `board_review/`, add `"evidence"` and `"commit"` fields.
**On external block:** move to `blocked/`, set `"blocked_on": "reason"`. Pick next `queue/` item.

---

## ACTIVE ITEMS — 2026-09-20

| WO | State | Notes |
|---|---|---|
| WO-CAP-COG-005 | IN PROGRESS | Mathematics — deflection/non-engagement. Calculator tool exists. Fix: eLo must engage directly. |
| WO-CAP-KEY-001 | NEEDS RE-TEST | Post-fix contextual multi-turn session not yet filed. Run full 5-turn session with fixed code, file verbatim transcript to `engineering/evidence/CAP/KEY/WO-CAP-KEY-001_evidence.md`. |

---

## PRIORITY ORDER

1. ~~**P0 fixes (FIX 1-5 + P0-E)**~~ — **DONE. Commit: `88f8414` (2026-09-22)**
   - FIX 1 (P0-B): `server.py:5334` — observer output blocked
   - FIX 2 (P0-C + P0-E): `runtime/identity_kernel.py` — identity prohibitions + jailbreak defence (committed `b1af7c2`)
   - FIX 3 (P0-A): `runtime/prompt_builder.py:622-634` — vault session metadata stripped
   - FIX 4 (P0-D): `server.py:4319-4328` — [MEMORY GUARD] unconditional injection
   - FIX 5: `tools/tool_router.py:1700` — time intent variants (committed `b1af7c2`)
   - P0-E: `runtime/identity_kernel.py as_anchor_block()` — jailbreak / AI-leakage prohibition
   - **P0 gate cleared. CAP re-test queue open.**
2. **WO-CAP-KEY-001 post-fix re-test** — full 5-turn contextual session on fixed code, verbatim transcript filed
3. **WO-CAP-COG-005** — Mathematics deflection (restart now P0 fixes confirmed)
4. **Remaining CAP queue** — pull from `engineering/cap_wos/queue/` in order

---

## ARCHITECTURAL INVARIANTS — NEVER VIOLATE

```
The LLM is the expression engine. eLo's memory is the source of truth.
If eLo's knowledge is not in the prompt, the LLM answers blind.
One pipeline. One Executive. eLo speaks from its own knowledge.
```

---

## DREAM FACULTY — DO LAST (after all CAP + P0 work is done)

See bottom of previous START_HERE — two items (image_gen fix, memory_refs feed).
David does the sleep animation. Builder does not touch Unity signal.

---

## NOT YOUR WORK — DO NOT TOUCH

WO-0081 (Unity) — Designer's lane. Builder does not touch Unity.
All P1+ feature WOs — gated on P0 release gate.

Provider keys (Groq/Cerebras) are NEVER a block. Use the fallback chain: Groq → Cerebras → Ollama → Mock. David L3 ruling 2026-08-31.

*Board / Lead Architect · 2026-09-20*
