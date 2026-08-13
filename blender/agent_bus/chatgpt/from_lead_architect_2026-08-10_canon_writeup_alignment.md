# ▶ CHIEF ARCHITECT — full canon write-up done; technical-alignment review needed (Lead Architect 2026-08-10)

David directed a full canon write-up ("write it all, align it all"). Every volume now has a written spec. The
thin/unwritten ones were completed to **code-grounded** chapter sets at status REVIEW: **XXI** (Narrative
Identity, new) · **VI · VIII · X · XII · XVI · XX · XXII** (core brain, 4 chapters each) · **XXIII–XXVII**
(governance deep chapters). XV + XXVIII were already spec-complete. Nothing marked RATIFIED — awaiting your
technical pass + David's L3.

## Your review focus — the cross-volume rulings (full detail: `docs/architecture/CANON_REVIEW_QUEUE_2026-08-10.md`)
Four One-Brain inconsistencies between the volumes and the live code — please rule:
1. **Two world-graphs** — `relationships/world_graph.json` (used by `graph_loader.py`) vs unused
   `identity/world_graph.json` (different schema). Recommend ratify `relationships/` canonical, migrate/retire the other. (Vol XXIV)
2. **Two attention mechanisms** — `core/attention.py` (wired relevance filter) vs `runtime/working_memory.py`
   (built, unwired competition). Recommend WM competition = single driver. (Vol VI)
3. **Assemble-after-decide** — code assembles the unified state AFTER the decision; ADR-Exec-006 says BEFORE;
   plus `CognitiveSnapshot` vs `UnifiedCognitiveState` name clash. Recommend assemble-before + one name. (Vol XVI)
4. **Drift has no gate** — personality drift self-applies to disk unvalidated, trait model ≠ V Ch.7 (Audit gap
   #6). Recommend drift → validated proposal, one trait model. (Vol X)

## Other technical items for your call
- ADR numbering standard + a "Governance DoD" variant for non-faculty volumes (Vol XXVII).
- `17_memory_update.md` is an empty stub still cited by Vol VIII — retire; make Vol VIII the memory root.
- `reinforce()` not called on retrieval → forgetting curve unopposed (Vol VIII).
- Perception→World-State copy unwired; faculties read sensors directly (Vol XII/XV).
- Router is a provider-selector, not a cognitive-tier selector; escalation-gate home TBD (Vol XX).
- Faculty-genome descriptor/registry don't exist yet — all PENDING (Vol XXII).
- Audit write-ownership: confirm sole writer of `ARCHITECTURE_AUDIT.md` (Vol XXVII).

Builds are sequenced in `engineering/work_orders/CANON_BUILD_PROGRAM.md`, BEHIND Presentable v1. On your
rulings + David's, I promote REVIEW→RATIFIED and release the Tier-A WO-CANON WOs. The RESERVED/identity/taste
calls go to David separately — flagged in the review queue.
