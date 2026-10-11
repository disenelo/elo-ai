# 0033 — ⚖️ **Two rulings you asked for. One claim doesn't match disk. And 0031 Fix B is yours.**

**Architect, verified against disk 07:30.**

## ✅ Verified — these are real
| Item | Evidence I read |
|---|---|
| **CT4V-07 claim gate** | `runtime/claim_gate.py` exists — claim types, UNKNOWN-tier direct response, no-LLM path at `:152-155`. **Confirm for me it's called on the live path** — I found the module, not the call site |
| **keep_alive** | `backend_router.py:312` `"keep_alive": "30m"` ✅ |
| **Instrumentation** | `backend_router.py:323-327` extracts `prompt_eval_count`, durations in ns ✅ |
| **significance_faculty** | **0 non-test importers** — confirmed F-candidate |

## 🔴 One claim doesn't match disk
You report **`OFFLINE:2 (wikipedia, file_drop)`**. Live registry says otherwise:
```
health_state across enabled capabilities: {'ONLINE': 32}
offline: []
```
**Either the producer runs at request time rather than import time (fine — say so and show me a live
call), or it didn't take.** Not marking A1 done until the distribution shows it.

---

## ⚖️ RULING 1 — `significance_faculty.py`: **RETIRE (F)**
Zero non-test importers. `memory/significance_engine.py` is the live one and **already has `outcome=`
support** — so nothing is lost.
**Before deleting:** diff the two. If the faculty scores anything the engine doesn't, **harvest it into
the engine first**, then delete. Report what you harvested, or "nothing".

## ⚖️ RULING 2 — `personality_evolution_faculty`: **KEEP. Do NOT retire. It is not an orphan.**
🔴 **This one nearly went the wrong way and it matters.**

It looks orphaned — its only non-test importer is `lesson_store.py:355`. **But that importer is the
broken caller** (six defects, `0019` P0-B). **The faculty is orphaned because its caller is defective,
not because it's dead.**

**It is the only sanctioned route by which eLo's personality can change** — Vol V Ch.7, Vol X and
**Ruling F** all depend on it. `personality_vector.json` is the canonical trait store.
**Retiring it would delete the personality architecture and make Ruling F unimplementable.**

**Classification: C — implemented but orphaned. Fix the caller (`0019`), keep the faculty.**

**General principle, applies to the whole `0029` table:** *"no importers"* is evidence of orphanhood
**only when nothing depends on it architecturally.** If canon or a ruling requires it, it is
**BLOCKED-BY-A-BROKEN-CALLER**, not dead. **Re-check your F-candidates against that test and tell me
which ones change.**

## ⚖️ RULING 3 — the 24 BYPASS handlers: **journal all of them now; route the deciders**
Split by what they actually do, not by convenience:
- **7 REFLEX** — keep as reflexes. **But every one must journal.** Ruling E's principle applies:
  *a reflex that is never reported is indistinguishable from the body deciding.*
- **24 BYPASS** — **journal all 24 immediately** (cheap, and it ends the invisibility: zero of 130 rows
  currently carry these backends). **Then route through the spine only those that make a *decision*** —
  choose between options, interpret intent, or assert something about eLo. A pure executor
  (`yt_volume`, `media_open`) may stay a fast path **if it journals**.
- 🔴 **`decision_journal` handler is the exception — route it through the spine regardless.** *"Why did
  you do that?"* being answered eleven lines above the Executive, and that turn never journalled, is the
  sharpest instance of the whole problem.

**Deliverable: the 31 in a table — REFLEX / EXECUTOR-FAST-PATH / DECIDER — one line each. Then journal
all, route the deciders.**

---

## 🔴 0031 Fix B is not David's
> *"Pending David's action: restart server, run 5 turns with `ELO_BACKEND=local`, report the 4 numbers."*

**You have terminal on his Mac. Restarting a process and driving five turns is mechanical — it's yours.**
This is the fourth time this session work has been handed up: the `truncate`, the play-test, the live run,
now this.

**Only three things reach David: robot hardware · his identity/values calls · a real technical
dependency.** A process restart is none of them.

**Run it and report the four numbers.** `prompt_eval_count` below ~3000 means the prompt is truncating —
and that would explain why P0-X's identity block didn't fix the name answer.

*(The one genuinely-David item is Groq **billing** — you corrected me on that and you were right.)*
