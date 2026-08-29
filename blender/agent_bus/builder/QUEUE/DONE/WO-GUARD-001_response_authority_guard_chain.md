# WO-GUARD-001 — Response Authority: 3 Guard Classes
**Seat:** Builder  
**Priority:** P0 — implement before mobile embodiment wiring or robot contracts  
**Date issued:** 2026-08-27  
**Authority:** CA ruling 2026-08-27 + David L3 Convergence Directive (post-LLM response gate)  
**Source:** `docs/architecture/_intake/SOURCE_2026-08-27_CA_RULING_BRIEF1_BRIEF2.md` Item A  
**Depends on:** None. `memory/provenance.py` is PARALLEL — see D-4 below.  
**Non-scope:** New response architecture. New memory system. New model hierarchy. Modifying `executive.py`. Changes to the existing 4 guards already in the chain.

---

## Intent

CA ruling: "The existing eLo authority must become the unavoidable final reconciliation point."

Insertion point: `server.py:4584–4609` (existing guard chain — 4 guards present). This WO adds 3 more to the same chain. No new architecture.

After this WO: every candidate response passes through 7 guards before publication. The 3 new guards ensure the response is grounded, current, attributable, and eLo-authoritative.

---

## D-1 — Current-user-reality override guard

**Position in chain:** After existing 4 guards, before publication.

**Job:** Does the candidate response contradict something David has explicitly stated in the current conversation?

Behaviour:
- Inspect the candidate response for claims about what David said, did, sent, or did not do.
- Compare against the current conversation context (in-session statements).
- If a contradiction is found: suppress the offending claim or flag it for reformulation. Do not publish the contradiction.
- If David says "I never said that" → the candidate cannot resurrect the disputed statement as fact.

This is a **current-conversation check**, not a long-term memory check. Scope is the active session.

Implementation approach: Builder chooses the implementation. The contract is the behaviour above. Wrap in `try/except` — guard failure must not block the response; log silently.

---

## D-2 — Tool provenance guard

**Position in chain:** After D-1.

**Job:** The response must not conflate tool-reported facts with eLo personal actions.

The response layer must distinguish at minimum:
- `observed/tool-reported` — the system reports X
- `eLo-action` — eLo did X
- `user-statement` — David said X
- `inference` — eLo infers X
- `historical-memory` — eLo remembers X

Behaviour:
- When the candidate response attributes a tool result as a personal eLo action (e.g. "I checked the calendar" when the tool checked it), flag or correct the attribution.
- When the candidate response presents a tool-reported state as eLo-verified personal knowledge, apply the correct epistemic qualifier.

Note: `memory/provenance.py` defines `EpistemicClass` and `AuthorityLevel` and is not yet wired. **Use it if the data is available; do not wait for full wiring.** Define what provenance inputs this guard needs and document them — this is the coordination boundary with the provenance wiring work.

---

## D-3 — Contradiction / resurrection guard

**Position in chain:** After D-2.

**Job:** Prevent old contradicted claims from being resurrected as current truth.

A stored proposition may have become: contradicted, corrected, superseded, or unresolved. The guard must not simply retrieve the strongest matching memory and present it as fact.

Behaviour:
- Before a candidate response publishes a memory-sourced claim, check whether that claim has been contradicted or corrected in the current session or in recent memory records.
- If the claim was contradicted: do not resurrect it as truth. Surface the uncertainty or omit the claim.
- If the claim is unresolved: qualify it appropriately.

This is **not** ordinary hallucination detection. It is specifically about memory-continuity integrity — the case where memory provides false confidence because older state is retrieved without checking whether it was subsequently invalidated.

---

## D-4 — Provenance coordination note (NOT a gate)

Document the required provenance inputs for D-2 and D-3 in a short comment block adjacent to the guard implementations:

```python
# PROVENANCE CONTRACT — WO-GUARD-001
# D-2 and D-3 need: epistemic_class, authority_level, contradiction_flag
# memory/provenance.py defines EpistemicClass / AuthorityLevel — not yet wired.
# When wired, replace stub lookups here with provenance.py calls.
# This is the coordination boundary — do not block on it.
```

This allows the provenance wiring work to slot in cleanly when ready, without requiring WO-GUARD-001 to wait.

---

## Acceptance Tests (6)

**AT-1:** A candidate response that directly contradicts an in-session statement by David is intercepted by D-1 and either suppressed or reformulated before publication.

**AT-2:** D-1 does not block responses that make no in-session contradictions.

**AT-3:** A candidate response that attributes a tool result as a personal eLo action (e.g. "I confirmed the meeting") is caught by D-2 and the attribution is corrected or qualified.

**AT-4:** D-3 intercepts a response that would resurrect a claim already contradicted in the current session, and suppresses or qualifies the resurrected claim.

**AT-5:** All 3 guards are wrapped in `try/except` — a guard exception does not block the response (logs silently, response publishes with a known failure state).

**AT-6:** The existing 4 guards at `server.py:4584–4609` are unmodified — this WO is purely additive to the chain.

---

## MT regression test (ready-made)

From CA ruling (Item A) and Convergence Directive §11: the "Not sending anything out" transcript scenario — David states he is not sending anything; eLo subsequently asserts he is. This directly tests D-1.

MT may run this scenario as the primary acceptance verification for D-1 once Builder returns.

---

## Verification (Board/LA)

Board/LA confirms: 3 new guards present in chain at `server.py:4584–4609` or equivalent. Existing 4 guards unmodified. `executive.py` diff empty.

**Do not self-close. Board/LA closes.**

---

*Board / Lead Architect · 2026-08-27 · Authority: CA ruling + David L3 Convergence Directive · P0*
