# Change Control Policy
### How change happens in the DISENELO studio — nothing moves without David's say, nothing gets lost

**Owner:** David Charles (CEO / single approval gate) · **Author:** Architect (Claude) · **2026-07-27**
**Status:** LAW (D-M). Every agent — Builder, UI/Avatar, Design, Planning Assistants, CEO Agent —
follows this. It exists because changes were happening out-of-band and context was getting lost.

---

## 1. The one principle
**David is the single approval gate.** No change reaches a "done/shipped/merged-as-final" state without
David's explicit say. Agents propose and build; **David approves.** Nothing skips him.

**Momentum (David, 2026-07-27):** the gate is a **final stamp, not a pipeline stall.** Agents keep
pulling READY work whose *functional* dependencies are met while approvals batch-clear — **nothing waits
on a signature; nothing ships without one.** The Architect batch-verifies so approvals are fast, not a bottleneck.

## 2. The only path a change may take
```
PROPOSE   → agent relays the idea/need to the Board (§0.5 Relay, or an existing WO)
   ↓
SPEC      → the Architect writes/updates the WO or canon (single source of truth; assistants don't write canon)
   ↓
APPROVE   → David approves the WO / decision (and any FREEZE unlock)   ← GATE 1
   ↓
BUILD     → the owning agent makes EXACTLY ONE change, to spec, in its own lane
   ↓
VERIFY    → build with 0 errors; run/attach the acceptance evidence; then STOP and WAIT
   ↓
HANDBACK  → record it in COMPLETION_LOG.md (what changed · commit · evidence) → IN_REVIEW
   ↓
REVIEW    → Architect verifies against spec → David approves → DONE + Audit updated   ← GATE 2
```
No step is skipped. No change happens between gates without a WO behind it.

## 3. The constraints (hard rules — MUST)
1. **One change at a time.** One WO = one change, exactly to spec, build, **then wait**. **No multi-change
   batches** (batches are what got reverted). Next change only after the prior is approved.
2. **No self-approval.** A Builder/agent marking `DONE` means *claimed*, not done. Truly DONE only when it
   is in `COMPLETION_LOG.md` "Completed & approved" with David's sign-off (Review Gate).
3. **Nothing gets lost.** Every change is committed **and** recorded in `COMPLETION_LOG.md`. Anything built
   but not on the board/canon is **relayed** (§0.5). Specs, decisions, and reference material are **pinned
   in the canon** (e.g., `docs/architecture/_refs/`), never left in chat only.
4. **Stay in your lane (scope).** Builder edits `~/elo-ai/` only (D-I); UI/Avatar/Design edits the
   Presence/Unity repo; no cross-lane writes. `runtime/executive.py` + `prompts/` are FREEZE_V1_LOCK —
   changed only via a scoped, logged unlock David grants.
5. **Revert-safe.** Always work from a known-clean baseline (record the commit). A rejected change is
   reverted cleanly — no half-states left running.
6. **Canon changes only by the Architect, via ADR.** Governance/spec changes are recorded as decisions in
   `DECISION_LOG.md`. Planning Assistants (Gemini/ChatGPT) produce **intake**, which the Architect
   canonicalises — their output is never canon until filed.
7. **Every WO traces to a purpose** — a roadmap deliverable or a canon volume. No orphan work.

## 4. What David controls (the levers)
- **The brief** — what gets worked on next.
- **Gate 1** — approving a WO / decision / freeze unlock before build.
- **Gate 2** — approving completed work → DONE.
- **Decisions** — ADRs in `DECISION_LOG.md` become law on his ratification.

## 5. How this is enforced (mechanisms already in place)
- `DISPATCH_BOARD.md` — the routable queue + the **Review Gate** note + **§0.5 Relay** lane.
- `COMPLETION_LOG.md` — the completion + review record; the only place DONE is conferred.
- `AGENT_BRIEFINGS.md` — per-agent lanes + the completion & relay rules.
- `DECISION_LOG.md` — the ratified law.
- The **CEO Agent** routes only READY work, surfaces the review queue, and never self-approves.

## 6. If in doubt
Stop and relay it to the Board. A paused change waiting for David is always better than an out-of-band
change he didn't ask for. **Losing context is the failure mode this policy exists to prevent.**

---
*Change Control Policy — LAW (D-M, 2026-07-27). Supersedes any looser working habit.*
