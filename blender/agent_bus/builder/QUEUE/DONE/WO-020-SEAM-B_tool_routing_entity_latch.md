# WO-020 Seam B — Tool-routing drift + entity latch (P0)

> **⚡ VERIFY FIRST** — Check WO-018 status. `tools/tool_router.py` was being migrated to capability registry in WO-018. If that migration is complete, Seam B may be partially or fully resolved. Run the AT scenarios below before implementing anything. If all pass → close.

**Full WO:** `engineering/work_orders/WO-020_Kernel_Routing_Drift.md`
**Priority:** P0 · Live behaviour regression · **Architect-confirmed FREEZE_V1_LOCK SAFE**
**Owner:** Builder

---

## Scope — Seam B ONLY

**Seam A (action-selection drift in `executive.py` `_conversation_action()`) = FREEZE_V1_LOCK BLOCKED. Do NOT touch `executive.py`.** Seam B is independently fixable.

Seam B covers:
1. `tools/tool_router.py` — bare acknowledgement words ("done/ok/yes/what") being routed to web-search
2. `runtime/contracts.py` — stale entity latch: `active_topic_depth` / focal entity not cleared on new explicit request
3. Capability registry dispatch — "open Joe Budden Podcast on YouTube" → browser/computer-control with correct parsed target

---

## Routing trace (do first — required for verification)

Emit per-turn to a debug file (pattern: `movement_debug` in WO-017):

```
{intent, conversation_action_read_from_plan, capability_chosen, tool_dispatched, parsed_target, latched_entity}
```

**Instrument in `server.py`** reading from the plan/context object that arrives from executive. Do NOT add trace instrumentation inside `executive.py`.

---

## Acceptance Tests (reproduce David's live failures from WO-020)

- **AT-1:** Input "what is done?" after eLo said "Done" → must NOT web-search "done". Routes to CONVERSATION or direct answer.
- **AT-2:** Input "open Joe Budden Podcast latest episode on YouTube" → capability dispatch hits browser/computer-control with `target = Joe Budden Podcast on YouTube`. Entity latch clears; "DONE" NOT inherited.
- **AT-3:** New explicit imperative after any prior entity → prior entity cleared from focal context. New target parsed fresh.
- **AT-4:** Clean explicit command ("tell me Y") → ANSWER/execute (not CONNECT/REFLECT). *(This is Seam A; if Seam B trace shows it's in tool_router not executive.py, address it here. If it's definitively in executive.py `_conversation_action()` — flag, do NOT touch, report to Board.)*

---

## Constraints

- `executive.py` — MUST NOT TOUCH (FREEZE_V1_LOCK, LAW-017). If a fix requires it → mark as Seam A and report.
- WO-018 relationship: if tool_router → registry migration is done, confirm AT-1/AT-2 against the registry. Do not re-introduce legacy regex.
- Run frozen-kernel tests green after fix.

## Return

`DONE/FROM_BUILDER_WO-020-SEAM-B_tool_routing_entity_latch_result.md` · AT pass count · commit hash · routing trace sample (2 lines) confirming the fix

*Board / Lead Architect · 2026-08-29*
