# Board Gate — Dreams End-to-End + Scorer + Symbols
**Date:** 2026-10-11  
**Seat:** Builder 2  
**Board verdict:** SIGNED OFF — pending live-turn confirmation per BUILT ≠ DONE rule

---

## What was fixed (five root causes, in series)

**Root 1 — Dream model never called**  
`_dream_llm` passed `(active_backend(), messages)` to `route(system_prompt, user_input)` → `AttributeError` every call → hardcoded fallback sentence on 8 of 9 dreams. Fixed: correct call signature.

**Root 2 — `memory_refs` empty by construction**  
Checked whether symbol name appeared inside a topic string — structurally never true (e.g. "Weave" inside "the seam that will not lie flat"). `executive.py` derives Board flag from `memory_refs`, hence `memory_written: false` on all 241 entries. Fixed: provenance stamp was already correct; reading path was wrong.

**Root 3 — Vault write not firing**  
Built earlier. Now confirmed firing. `memory_written: true` on real dreams. [VERIFIED by Builder 2 running real path, not just unit check — Builder 2's self-correction noted and credited.]

**Root 4 — Significance constant 0.900 (saturation)**  
`emotional` took max across every cycle and every seed → one emotive word pinned it. `unresolved` binary on any single seed. Fixed: proportional scoring. Ten dreams now rescore across 0.565–0.667. [VERIFIED: no longer a constant.]

**Root 5 — Symbol always "Moon"**  
`_add` accumulates: 4 ambient events × 0.9 = 3.6 beats any topic's 1.0. Weight reduction couldn't help while weight stacks. Fixed: themes now track topics (Weave, Workshop, Skeleton, LooseEnd). [VERIFIED by Builder 2.]

**Root 6 (bonus) — 5-minute gate after every daemon start**  
`last_request_ts` stamped at construction → daemon read "David just spoke" on fresh start → blocked all dreams for 5 min. Only became live after Builder 1 added `status()`. Fixed. [VERIFIED.]

**Builder 2 self-correction credit:** First `memory_refs` fix passed unit check but returned `[]` on real dream (test supplied `focal_thread` that live state doesn't have). Caught by running the real path. This is exactly how Board test gate works — running the real path, not trusting the check. Well done.

---

## Suite results [AS REPORTED — not independently verified from sandbox]

- IS ELO: 17 pass · 0 blocked · 0 fail ← first clean suite Builder 2 has filed
- Full suite: 4,114 passed, 5 failed
  - `test_basic_loop`: passes in isolation (test interference, not a real failure)
  - 2 Design/router long-standers: pre-existing, not Builder 2's
  - 2 ratchets: three live seats adding exits/handlers to `server.py` → ceiling tripped

**Note on sandbox:** Board cannot independently verify 4,114 pass count from sandbox (CLAUDE.md: sandbox results untrustworthy). The IS ELO 17/0/0 and the root-cause descriptions are structurally sound and consistent with the code defects described. Board accepts Builder 2's reporting pending Builder 1 running full suite on Mac.

---

## Ratchet ceiling — Board ruling

Builder 2 correctly declined to raise the ceiling unilaterally. Parallel growth from three seats (no single named cause) is not grounds for a unilateral rebaseline.

**Board ruling:** Ceiling raise is Builder 1's call, on `server.py` (their file). Builder 1 must:
1. Audit the new exits and handlers added to `server.py` by the three running seats
2. Name the cause (even if it's "multi-seat parallel sprint adds N new handlers")
3. Raise the ceiling with that named reason as the commit message
4. Run the full test suite on Mac after ceiling raise

Board will not sign off on a ceiling raise without a named cause in the commit.

---

## Live-turn gate (BUILT ≠ DONE)

Dreams are now mechanically correct. The Board cannot confirm live dreams without David seeing them in an actual session — eLo must dream during a real idle window and the vault entry must be visible. That gate is David's.

**David: next idle window of 20+ minutes (SLEEP threshold) — eLo should dream. Board will read the vault entry and confirm.**

---

## What's next for Builder 2

- SPG backfill from `interactions.json` (0007) — P0
- Random facts raise-hand signal — verify it fires in live turns
- File first 10 retained dreams with corrected scores to Board (use the 0.565–0.667 range now that scoring is fixed)

*Board / Lead Architect · 2026-10-11*
