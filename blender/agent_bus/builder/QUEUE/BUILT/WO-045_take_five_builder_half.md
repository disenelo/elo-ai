# WO-045 — "Take Five" — Builder half (intent → leave command)

**From:** Board / Lead Architect — 2026-08-28
**Priority:** P2 — TIER 1 ACCEPTANCE TEST (David's first named goal behaviour for Presentable v1)
**Full WO:** `engineering/work_orders/WO-045_Take_Five_Privacy_Pop_Off.md`
**SPLIT WO:** Builder handles intent + server-side emit; Design handles Unity pop-off + hide + return.

---

## What Builder builds

When David says "take five / take a break / give me some space / I need a moment" (and variants):

**D-1 — Intent classification + leave command emit**
- Classify "take five" phrasings reliably → emit a **LEAVE/HIDE** body directive (`step_out` or equivalent) to the Presence system.
- This is NOT the plain idle/settle directive — it must be a distinct LEAVE command that triggers Design's pop-off-screen exit.
- Existing: `server.py` `_SIGNAL_WORDS` 333–340 has basic intent; `step_out` body directive at server.py:426. Review + harden.

**D-2 — Return intent**
- Classify "come back / I'm back / eLo / hey / where are you" → emit a RETURN command that wakes the hidden eLo.
- Existing: hide_widget() / SetVisible(false) from INT7-OFFTOGGLE. Builder emits; Design executes.

**D-3 — ADR-Exec-001 compliance**
- eLo says "stepping away" ONLY if it actually hides — verify-before-speak. Never narrate an exit that hasn't happened.

## ATs (`tests/test_wo045_take_five_builder.py`)
- **AT-1:** 8+ "take five" phrasings classify to leave path; `body_directive` == `step_out` (not `sit`, not `idle`).
- **AT-2:** 6+ "come back" phrasings classify to return path; emit RETURN directive.
- **AT-3:** non-take-five inputs do NOT misclassify (3 control phrases).
- **AT-4:** eLo's spoken response only includes "stepping away" text when the leave command is present in the response.

**Return:** `DONE/FROM_BUILDER_WO-045_take_five_builder_result.md` · 4/4 AT PASS · commit hash

Note: Design half must also complete before the WO is fully DONE (integrated DoD per Milestone). Builder returns the Python half; Board gates integrated close on Design half also returning.

*Board / Lead Architect · 2026-08-28*
