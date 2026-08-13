# WO-082 — Executive Decision Journal: "why did I do that?" (self-explanation from real cognition)

**Owner:** Builder (eLo OS — spine/executive). **Priority:** P2 — POST-Presentable. **Status:** OPEN —
spec'd 2026-08-08 (Chief Architect "one more thing"). **Canon:** ADR-Exec-001 (never invent) · ADR-Exec-006
(assembly) · ADR-Exec-005 (learn from verified consequences) · The Moment (WO-079). Reconciles onto the
existing "Executive Decision Journal" seed in the richness tier — NOT a new subsystem.

## The capability
David: "Why did you jump over there?" → eLo must NOT invent a poetic after-the-fact reason. The runtime
reconstructs the ACTUAL decision and eLo explains from it:
> "I noticed that wall was reachable and I wanted to explore the other side. Wall-jumping was the best route
> I knew I could make."
That's self-explanation grounded in cognition, not an LLM confabulating a motive.

## Scope
1. **Record a decision trace per Executive action** (append-only, e.g. `self/journals/decision_journal.jsonl`):
   `action · trigger (external cmd | internal intent) · world (affordance detected) · capability+confidence ·
   alternatives considered + why rejected · outcome (ACK success/fail) · significance · learning`.
2. **Failure updates the self-model** (Horizon #6): a missed attempt writes a `known_failure_condition`
   (e.g. `gap > reachable_distance`) + updates reliability → next time eLo can say "I don't think I can clear
   that from here." (Feeds capability confidence / WO-055.)
3. **"Why did you…?" reads the trace**, not the LLM's imagination — the answer is a readback of the recorded
   decision, phrased in eLo's voice.
4. Deterministic-first: the trace is composed from real runtime values (The Moment + ACK + capability
   registry), never estimated.

## Definition of Done (on the real brain)
- After a real action, `decision_journal.jsonl` holds a complete trace (trigger→alternatives→outcome→learning).
- "Why did you do that?" → eLo's answer matches the recorded trace (no fabricated motive); a spot-check shows
  the stated reason == the logged trigger/affordance/utility.
- A repeated failure produces a `known_failure_condition` that changes eLo's next relevant answer ("I don't
  think I can make that").

## Test — WITHOUT David
- Drive a scripted action with a known trigger/affordance → assert the journal entry fields; ask "why" via the
  explanation path → the answer references the logged trigger + chosen-over-alternatives, not a new invention.
- Force two failures on the same move → assert a `known_failure_condition` is written + the capability
  reliability drops + the "can I?" answer flips to honest-no.

## Lane / sequencing
Builder (Python — spine). POST-Presentable; gated on WO-079 (The Moment) + WO-073 (brain). Pairs with WO-081
(emergent behaviour needs explainable decisions) and the Capability Horizon register (#6, #11).
