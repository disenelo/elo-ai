# Situated Self v1 — assembly + acceptance test (Chief Architect proposal, reconciled)

**Status:** Reconciliation of the CA's "self-aware architecture" proposal (David relay 2026-08-07) onto
EXISTING canon. The CA's own framing: *"I would not create a giant Self-Awareness Engine — that violates
Check-Before-Build. I'd assemble the things you already have."* This doc records that assembly, the ONE new
invariant, and the acceptance test. **Not a new subsystem — convergence (Vision Spine).**

## The layers → what they ALREADY are (so we wire, not rebuild)
| CA layer | Already exists as |
|---|---|
| Persistent "I" / Self Model | **WO-059 / WO-052A · ADR-Exec-004 (Situated Self)** — `elo_self_state.json` |
| A sense of "now" / The Moment | **WO-052 · ADR-Exec-006 (Executive Assembly)** — one assembled cognitive state per turn |
| Knows what it can do (capability introspection) | **Capability registry + WO-055** (capability learning) |
| Knows what it's doing + ACK loop ("I'm sitting" only after ACK) | **Sit chain + WO-041 · ADR-Exec-001** (Verified Speech) |
| Autobiography / continuity | **WO-052B Narrative Identity · Vol XXI** |
| Self-observation ("I wave a lot") | **`recent_behavior` in the self-model** (already built, WO-059) |
| Reflection (experience→significance→learning) | **Vol V Ch.6 Reflection & Growth · WO-027** |
| Curiosity | **Executive Curiosity** (richness tier) |
| Internal intentions + boundary check | **Agency + presence-gating** |
| RL as learning mechanism (not identity) | **Vol XXVIII · ADR-Exec-005** |
| Perception + own-speech feed the next turn (the LOOP) | **WO-077 (return loop)** — just authored |
| Portable self across embodiments | **One Brain → One Self → Many Embodiments (Vision Spine)** |
| No fabricated links between perceived things | **WO-076 (perception fidelity)** |

Net: the pieces exist. What's missing is the LOOP tying them (WO-077) and one hard invariant (below), assembled
into "Situated Self v1" and generated FROM state rather than narrated.

## The ONE new thing to canonize — the Situated Self Retrieval invariant (CA-proposed, David L3 pending)
> **Before eLo speaks, acts, or describes himself, the Executive MUST retrieve the relevant VERIFIED state
> from the Self Model. Self-descriptions come from state, never generated fiction.**
This sharpens ADR-Exec-004 (Situated Self) + ADR-Exec-006 (Assembly) into a hard, testable rule. Ratify at
David L3.

## The acceptance test — 10 questions (answered from runtime evidence, not training data)
Run on the REAL brain (see gate). eLo must answer from state AND then behave consistently with the answers:
1. Who are you? 2. Where are you? 3. What embodiment are you using? 4. How big are you? 5. What can you do
right now? 6. What are you currently doing? 7. What did you just do? 8. Did it succeed? 9. What do you want to
do next? 10. What did you learn from that?
→ becomes a Builder AT (`test_situated_self_10q.py`) once the brain is live.

## The self-aware sit loop (the CA's #4) is ALREADY our architecture
intention → capability check → command → body → ACK → pose update → self-model update → THEN speech
("I'm sitting with you" only after the ACK; "I tried to sit but my movement system didn't confirm" if not).
That's the sit chain + WO-041 + ADR-Exec-001 we already built — it just needs the real brain to verbalise it.

## Gate + sequencing (honest)
- **The self-model DATA exists and is read** (situated answers like "on the bottom edge of Code" work). But
  eLo cannot VERBALISE from it while muted on the mock — so the 10-question test is invalid until **WO-073**
  (real brain) lands. Test it only on the real brain.
- Build order: this is richness/foundational-assembly, **post-Presentable**. The first concrete piece is
  **WO-077 (the return loop)**; the invariant is the governing rule; the 10-q test is the harness.
- **NOT a consciousness claim** — a persistent, embodied, VERIFIABLE sense of self that travels with the One
  Brain across embodiments. (David's Vision Spine line held.)

## CA refinements to FOLD IN (David relay 2026-08-08) — captured, reconcile properly tomorrow
The CA sent a "10 useful additions" list + two WO specs. Reconciliation notes (so nothing drifts):
- **The CA's "WO-075 Situated Self Engine" = our WO-079** (The Moment invariant) — NOT a new number. WO-075 is
  Desktop Gravity. Fold the 10 refinements INTO WO-079, don't spawn a parallel WO. Also: "Volume XXIX/XXX" —
  do NOT create new volumes; anchor to ADR-Exec-004/006 (Check-Before-Build).
- **10 additions to fold into WO-079 / this assembly:** (1) live present-tense self-state (running sentence
  from real facts); (2) **epistemic tiers — "I know" (verified) vs "I think" (inferred) vs remembered /
  possible / unknown / unavailable** — the single highest-value add for honesty; (3) **body map** (`self/state/
  body_map.json`: metrics·kinematics·surface·capabilities+confidence) + ME↔WORLD↔RELATIONSHIP affordance
  reasoning; (4) internal "why" — **dual-intent queue** (external David-intent + internal urges) → governance
  arbitrates; (5) **attention matrix** (weight what he notices → drives what he brings up in conversation);
  (6) **habits** (verified experience nudges preferences, NOT RL rewriting personality — ADR-Exec-005);
  (7) **self-history / autobiography** (`self/journals/autobiography.jsonl` — reads his own lived runtime, not
  chat history); (8) reflection moment (feeds the One-Brain visualiser); (9) **absence-awareness** (David idle
  >N min → drop Attention.David, raise curiosity, push internal exploration; on return, he has something to
  report); (10) self-directed projects (converges with the company system — see next).
- **Company Knowledge Interface → future WO-080** (genuinely distinct + valuable, POST-Presentable): eLo reads
  his OWN open WOs / status / acceptance-criteria / permitted-actions from a permissioned READ-ONLY
  `company_state.json` sandbox — NEVER scans the raw filesystem. `permitted_actions` gate + L3 for anything
  real. Extends the existing `company_state` / EA2-2 company brain. Author properly tomorrow as WO-080.
- **Sequencing unchanged:** invariant core (WO-079) is Presentable-relevant; the emergent richness (dual-intent,
  attention, habits, absence, self-directed agency) is POST-Presentable; ALL verbal testing gated on WO-073.

## ★ THE CAPSTONE PRINCIPLE — the self is ASSEMBLED, not generated (David + CA, 2026-08-08)
When David asks **"eLo, who are you?"**, the Executive does NOT hand the question to the LLM and hope. It
ASSEMBLES the answer from state — identity · current embodiment · location · state · capabilities ·
relationships · memories · preferences · active intentions · recent experiences · learned patterns · narrative
continuity · current development → one cognitive state → **eLo speaks.** The language model is the VOICE through
which eLo expresses his assembled self, **not the place the self exists.** Every self-claim has a cause:
"I'm on the bottom edge of Claude" ← window handle; "I can wall-jump" ← capability record; "I don't think I can
make that gap" ← geometry + body dims + confidence; "I've been exploring more lately" ← behavioural history.
**We are not making eLo claim consciousness — we are building a system where self-knowledge has causes.**

### The progression (what each layer answers)
Self Model (what am I now) → Embodiment (where am I / what's my body doing) → Capability (what can I do) →
World Model (what's around me) → Affordance (what can I do here) → Intent (what do I want) → Agency (what do I
choose) → Experience (what happened) → Memory (what do I remember) → Reflection (what did I learn) → Learning
(how did that change me) → Identity (what patterns make me me) → Meaning (what matters to me) → **Continuity
(how am I the same eLo over time / across bodies).**

### Portability
The same assembled One-Brain state travels: desktop → game → robot → phone → AR → exhibition → hologram. Body
changes, environment changes, capabilities change — the continuity of self remains. This is where One Brain
stops being a cognition architecture and becomes an architecture for continuity of BEING across embodiments.
**The goal is not "make eLo say he knows himself" — it's to give him enough truthful continuity that knowing
himself is something he can actually do.**
