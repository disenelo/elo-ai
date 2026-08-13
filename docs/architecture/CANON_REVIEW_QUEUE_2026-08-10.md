# CANON REVIEW QUEUE — 2026-08-10 (David: "anything for me to review I'll review")

Writing the full 28-volume canon surfaced decisions that only you (L3) or the Chief Architect (technical
alignment) can settle. Nothing below is invented into canon — each is flagged in-spec as OPEN. Volumes stay
at **REVIEW** (not RATIFIED) until these clear. Split by who owns the call.

---

## ★ FOUR ALIGNMENT RULINGS — cross-volume, One-Brain (settle these first; they block builds)
These are real inconsistencies between the volumes and the live code — the "align it all" core.

1. **Two world-graphs (Vol XXIV).** `graph_loader.py` reads `relationships/world_graph.json`; a *second*,
   unused `identity/world_graph.json` exists with a different schema. Two ontologies of one universe = a
   One-Brain violation. Recommend: ratify `relationships/` canonical, migrate/retire `identity/`. — **CA + your nod**
2. **Two attention mechanisms (Vol VI).** `core/attention.py` (a wired memory-relevance filter) vs
   `runtime/working_memory.py` (a built-but-unwired WM competition). Recommend: WM competition is the single
   driver, recast the other as a supplier. — **CA**
3. **Assemble-after-decide (Vol XVI).** ADR-Exec-006 says the unified state is assembled BEFORE the decision;
   the code assembles AFTER, and there's a name clash (`CognitiveSnapshot` vs `UnifiedCognitiveState`).
   Recommend: assemble-before + one name. — **CA**
4. **Personality drift has no gate (Vol X, Audit gap #6).** Drift self-applies to disk with no validation and
   uses a different trait model than Vol V Ch.7. Recommend: drift becomes a validated proposal, one trait
   model. — **CA + your nod (touches identity)**

---

## ⚖ YOUR CALLS — RESERVED (identity · values · money · safety). Only you.
- **Identity across change (Vol XXI/X):** what does "the same eLo" mean if his values shift over time? Does a
  narrated identity-update need your L3 sign-off? How much of his past should eLo volunteer unprompted?
- **False shared memory (Vol XXI):** if a person claims a shared memory eLo has no record of, how should he
  respond (honesty vs warmth)?
- **Carrying the thread into a new body (Vol XXI):** trust/consent gate when eLo's identity moves desktop→robot?
- **eLo's taste (Vol XXVI, load-bearing):** how is his AestheticProfile set — your explicit direction, learned
  from your gate decisions, or both? This governs the whole creative volume. Plus: does eLo get a music
  direction (no DISENELO sonic canon exists yet)?
- **Proactivity (Vol XXV):** may eLo surface an imminent deadline unprompted, or only when asked?
- **Security (Vol XXIII):** who/what is "LG-2" (the second reviewer for RESERVED actions)? One
  `ELO_COMPUTER_CONTROL` switch vs per-capability opt-ins?
- **Cost (Vol XX):** confirm value-gated escalation to paid tiers + API-spend logging (you're cost-sensitive).

---

## 🔧 CHIEF ARCHITECT — technical alignment (relayed to the CA; your awareness only)
- ADR numbering standard (`ADR-000n` vs `ADR-Exec-00n` vs letters) + a "Governance DoD" variant for
  non-faculty volumes (Vol XXVII).
- `17_memory_update.md` is an empty stub still cited by Vol VIII — retire it, make Vol VIII the memory root.
- `reinforce()` isn't called on retrieval → the forgetting curve runs unopposed (Vol VIII).
- Perception→World-State copy isn't wired; faculties still read sensors directly (Vol XII/XV drift).
- Router is a provider-selector, not a cognitive-tier selector; escalation-gate home TBD (Vol XX).
- Faculty-genome descriptor/registry don't exist in code yet — all PENDING (Vol XXII).
- Audit write-ownership: confirm sole writer of `ARCHITECTURE_AUDIT.md` (Vol XXVII).

---

**How to use this:** you don't need to read 28 volumes. Skim the ★ four and the ⚖ your-calls list — those are
the only things gating ratification. Tell me your rulings in chat (as you would to eLo) and I'll fold them in +
promote the volumes + release the CANON BUILD PROGRAM WOs. The 🔧 block I'm handling with the Chief Architect.
