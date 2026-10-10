# 0028 — 🔴🔴 **THE NAME BUG'S ROOT CAUSE — and 31 handlers that bypass the brain entirely.**

**Architect, 05:00.** From the One Brain Convergence Audit — traced from questions, not volumes.
Full graph: `Output/ONE_BRAIN_CONVERGENCE_AUDIT.md`.

---

## 🔴 C2 · THE NAME BUG. Found. It's one scoring function.
```
"what is your name?"
   │
   ▼ spine.py:90   score = sum(1 for v in cap.verbs if v.lower() in lower)
   │  SUBSTRING MATCH — "what is" ∈ "what is your name"
   │  → candidates: calculator (registry.py:25), search (registry.py:66)
   ▼ spine.py:236  health gate — INERT (see A1) → passes
   ▼ server.py:3420 _tool_enrich_from_plan([("calculator", "what is your name")])
   ▼ tool_router.py:1454 _agent_calculator raises
   ▼ tool_router.py:1466 falls back to KEYWORD enrich() — Executive's choice discarded
   ▼ tool_router.py:618  _agent_search → web results
   ▼ user turn becomes "[CONTEXT: <web results>]\n\nwhat is your name"
   ▼ LLM answers from the search results
```
**Meanwhile `"name: eLo"` is sitting in the system prompt the whole time** — `elo_self_model.py:253`,
injected unconditionally at `server.py:3032`. **The self-model was never the problem.**

**Fix:** word-boundary matching, not substring. A verb must match a **token**, not a fragment.
**Proof: `"what is your name"` produces zero capability candidates.** Then re-ask it.

⚠️ **Second suspect, NOT ruled out:** `_ollama_call` (`backend_router.py:297-310`) **never sets
`num_ctx`**, and `living_presence_spec.txt` is ~4.5k tokens with seven blocks appended after it. The
identity block may be truncated. **Check `num_ctx` while you're in there** — if the window is short, C2
alone won't fix it.

## 🔴 C1 · 31 handlers exit before the Executive ever runs
`server.py:1571 … 2389` — **31 unconditional `return` statements**, all *before* `spine.run()` at
`server.py:2401`.

**Proof from disk:** `decision_journal.jsonl` has 130 rows and **not one** carries a backend from that
list — no `anim_cmd`, no `chrome_tabs`, no `cultural_facts`. Only `ollama*` and `direct`.
**Every one of those 31 paths is an unlogged, un-Executive'd decision.**

**The worst instance:** *"why did you do that?"* is answered at `server.py:2385-2390` — **eleven lines
above the Executive** — by a local file reader. `INPUT → helper → OUTPUT`. **And that turn is never
journalled itself.**

**Fix:** route them through the spine, or classify each as a legitimate reflex with a written reason and
**journal it anyway**. **Do not leave 31 undocumented bypasses.** Start by listing them with a one-line
justification each — that list alone is the deliverable.

## 🔴 A1 · The capability safety gate is inert
`Capability.health_state` (`capability.py:47`) has **no writer anywhere in the repo**. Constant `UNKNOWN`.
`spine.py:236` gates on `health not in ("OFFLINE","AUTH_REQUIRED","DISABLED")` — **so it always passes**,
for all 60+ capabilities. That's what let C2 through.
**Fix:** give `health_state` a producer, or make the gate fail-closed on `UNKNOWN`.

## 🔴 B1 · Reflection lessons can NEVER be confirmed
`reflection_faculty.py:182` passes **`episode_ref=spot`** (a SPOT code reused across turns) and
**`session_id=project`** (the constant `"eLo OS"`).
**Live proof:** ledger row `99ae9fcf7d4231eb` has **34 verified entries** and computes
`distinct_refs=1, distinct_sessions=1` against thresholds of 3 and 2.
**34 pieces of evidence, permanently stuck at `candidate`.**
**Fix:** real per-turn `episode_ref` (trace id) and real `session_id`. Same shape as the sit-ACK fix that
did work — copy it.

## 🔴 B2 · `_try_personality_delta` has **six** defects, and the gate can't be reached anyway
The four already carded, plus: **(5)** `apply_delta`'s return `(updated_pv, version_record)` is discarded,
so even a working call persists nothing; **(6)** `reflection_faculty.py:102-104` sends
`{"trait": <CAL action>, "direction": 1|-1}` — but `trait` must be a real trait name, `direction` must be
`"increase"|"decrease"`, and **`magnitude` has no default → `TypeError`**.
**And `lesson_store.py:312` only fires for `scope=="preference"`, which CAL actions can never produce.**
**The whole path is unreachable dead code.** *(Confirms and extends `0019` P0-B.)*

---

## The number to sit with
**83 of 130** journal rows record the trigger as **`"default — no stronger signal"`**, action `reflect`.
**The Executive's honest answer to "why did you do that?" is "no reason" on 64% of turns.**

## Order
**C2** *(one function — fixes the name bug)* → **A1** *(fail-closed gate)* → **C1** *(list the 31, then
route them)* → **B1** *(real refs — unlocks 34 pieces of stuck evidence)* → **B2** → then `0022` seam.

**Report with transcripts.** *"What is your name?"* → **"eLo"** is the acceptance test.
