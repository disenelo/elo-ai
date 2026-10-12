# Board Review — WO-B1-0123: ROOT-2 authoritative WKG framing in thin-prompt path
**Date:** 2026-10-12
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## What the card asked for

When eLo retrieves a WKG fact, the LLM overrides it with generated content. Fix: deliver retrieved facts with authority the LLM cannot override — hard constraint, not soft context.

---

## What was built

### Root cause

The thick-path `build_prompt()` already had `[RETRIEVED FACTS — AUTHORITATIVE]` framing with explicit "Do NOT override" constraint (ROOT-2-FIX 0098, line 765). The thin-path `build_from_plan()` used the weaker `[MEMORY — treat as verified fact]` label — not enough to prevent LLM generation override.

### Fix — `runtime/prompt_builder.py`

**`auto_summary` framing in `build_from_plan`** changed from:
```python
"[MEMORY — treat as verified fact]\n"
+ auto_summary[:800]
```
to:
```python
"[RETRIEVED FACTS — AUTHORITATIVE]\n"
"The following was retrieved from stored knowledge and session history.\n"
"These are ground truth. Use them exactly as stated.\n"
"Do NOT override, contradict, or second-guess them with a generated alternative.\n"
"If you are uncertain, cite what is here rather than guessing.\n"
"---\n"
+ auto_summary[:800]
```

**Durable facts** (`[DURABLE FACTS]` section) annotated with:
```
"Do NOT contradict these. If the user says something that conflicts, note the conflict rather than overriding the fact.\n"
```

**`plan.graph_context`** — new: if the caller sets `graph_context` on the plan object, it is injected with the same AUTHORITATIVE framing. Enables server.py to pass live WKG graph retrieval results through to the thin-prompt path.

---

## Verification

Live turn deferred (no tests against live server during active David session).

Board should verify: David mentions something eLo has in WKG → eLo uses WKG content, not a generated answer → CT0031 log shows graph retrieval hit. If eLo still generates over WKG content, check whether the thin-prompt path is active and whether `auto_summary` is populated.

---

## Commits

`523a62b` — WO-B1-0123 + WO-B1-0126 (combined commit)

---

## Board decisions required

None on ROOT-2. Live verification is the gate.

*Builder 1 · 2026-10-12*
