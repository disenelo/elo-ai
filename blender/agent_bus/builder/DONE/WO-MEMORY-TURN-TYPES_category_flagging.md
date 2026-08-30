# WO-MEMORY-TURN-TYPES — Define and Implement Memory Category Flagging by Turn Type
**Seat:** Builder  
**Priority:** P1  
**Date:** 2026-08-30  
**Authorised:** David L3 global ruling 2026-08-30  
**Source:** SOURCE_ALIGNMENT_REGISTER_2026-08-30.md G-17; WO-067-WRITE-PATH (DONE — root cause: memory_categories: [] never lifted); BOARD COMMAND eLo Response Authority §memory integrity; 10 memory categories (identity · relationship · preferences · plans · commitments · projects · decisions · experiences · contextual_state · learning)  
**Lane note:** Builder ONLY. Closes the write-path gap from WO-067.

---

## Intent

WO-067-WRITE-PATH (DONE) established the write path. Root cause confirmed: `memory_categories: []` on most turns — the category field is never populated, so nothing gets vaulted. This WO defines WHICH turns get WHICH memory categories, and implements that tagging in the cognitive spine.

The 10 memory categories (canonical, from David L3 ruling):
1. `identity` — facts about eLo's own nature, character, self-understanding
2. `relationship` — facts about David and eLo's relationship: history, dynamics, preferences
3. `preferences` — David's stated preferences, tastes, dislikes
4. `plans` — future intentions (David's or eLo's)
5. `commitments` — promises made, deadlines, obligations
6. `projects` — project state: DISENELO, eLo OS, robot, fashion
7. `decisions` — rulings, choices made (David L3 or Board)
8. `experiences` — things that happened: events, moments, conversations worth keeping
9. `contextual_state` — current situational context (mood, focus, environment)
10. `learning` — lessons learned, patterns noticed, growth moments

---

## Scope

### Turn-type → category mapping (authorised 2026-08-30)

| Turn type | Categories |
|---|---|
| David states a preference ("I like…", "I don't like…") | `preferences` |
| David mentions a project or gives a project update | `projects` |
| David makes a decision or David records a ruling | `decisions` |
| David sets a deadline or makes a commitment | `commitments`, `plans` |
| David describes a future intention or plan | `plans` |
| Relational exchange (David discusses the relationship with eLo) | `relationship` |
| David shares a story or experience | `experiences` |
| eLo learns something about itself | `identity`, `learning` |
| Current focus / mood / environment noted | `contextual_state` |
| Lesson or growth moment noted | `learning` |
| Contextual recommendation (e.g. clothing rec, taste-adjacent) | `contextual_state`, `preferences` |

### Implementation

In `spine.py`, AFTER intent gatekeeper (`intent_gatekeeper.py`) runs and BEFORE memory faculty write:
1. Call `memory_category_tagger(turn, intent_output, cognitive_state)` — new function in `memory/category_tagger.py`
2. `category_tagger` returns `List[str]` of applicable categories from the 10 canonical ones
3. Attach to `cognitive_state.memory_categories`
4. Memory faculty uses this list to tag vault writes — any turn with non-empty categories writes to vault

### Rules

- A turn may receive MULTIPLE categories (e.g. a clothing rec = contextual_state + preferences)
- A turn with NO applicable categories → `memory_categories: []` → NO vault write (correct behaviour — not everything is memory-worthy)
- Significance faculty (WO-SP29) gates WHICH category items are retained long-term; tagging happens for all; significance gates vault permanence

---

## Definition of Done

- [ ] AT-1: `memory/category_tagger.py` exists with `tag_turn(turn, intent_output, cognitive_state) -> List[str]`.
- [ ] AT-2: A turn where David says "I prefer X to Y" results in `memory_categories: ["preferences"]` (unit test).
- [ ] AT-3: A clothing recommendation turn results in `memory_categories: ["contextual_state", "preferences"]` (closes WO-067 root cause).
- [ ] AT-4: A turn where David mentions a project deadline results in `memory_categories: ["projects", "commitments", "plans"]`.
- [ ] AT-5: `cognitive_state.memory_categories` is non-empty on turns matching the table above.
- [ ] AT-6: Memory vault write IS triggered for AT-2, AT-3, AT-4 turns (vault has a record after the turn).
- [ ] AT-7: Existing WKG suite (82/82) passes. Full test suite passes with no new failures.

---

## Files in scope

- `memory/category_tagger.py` (create)
- `spine.py` (call category_tagger before memory write)
- `runtime/contracts.py` (confirm `memory_categories` field on CognitiveState — already exists per WO-067, verify)

## Files NOT in scope

- `executive.py` — category tagging is spine-level
- Vault schema changes — the field exists; we're populating it correctly now
- Unity / Design / MT files
