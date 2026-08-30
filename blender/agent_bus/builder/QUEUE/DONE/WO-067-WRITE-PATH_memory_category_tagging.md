# WO-067 Write-Path Fix — Memory category tagging

**Authority:** David L3, 2026-08-30
**Source:** `docs/architecture/_intake/SOURCE_2026-08-30_DAVID_CA_architectural_locks_unlocks.md`
**Priority:** P1
**Background:** WO-067 Step 1 confirmed `memory_categories: []` on contextual turns — data never lifted to vault. This WO tags the right turn types so the write path stores them durably.

---

## The governing principle (David verbatim)

> "eLo should durably remember information that changes his understanding of David, their relationship, ongoing work, commitments, preferences, experiences, decisions, or future context."
> "The point is meaningful continuity, not a transcript database."

---

## Memory categories to tag

When a turn contains any of the following, `memory_categories` must be populated:

| Category | What it covers |
|---|---|
| `identity` | Stable facts about David or eLo |
| `relationship` | Things that matter between David and eLo |
| `preferences` | Recurring likes, dislikes, ways of working |
| `plans` | Things David intends to do |
| `commitments` | Things David has agreed to or needs to remember |
| `projects` | Ongoing DISENELO / eLo work items |
| `decisions` | Architectural, creative, or personal decisions that should persist |
| `experiences` | Meaningful things that happened |
| `contextual_state` | Clothing, current circumstances, temporary plans with future conversational value |
| `learning` | Things eLo has learned from consequences |

**Not tagged:** passing remarks, acknowledgements, generic questions with no persistent value, conversation filler.

---

## What to build

Tag the correct `memory_categories` on turns at the point where the turn is written to `interactions.json`. The tagger must:
1. Detect which of the 10 categories apply to a given turn (user input + eLo response)
2. Populate `memory_categories` with the relevant category strings
3. The lift-to-vault pipeline already works — once `memory_categories` is non-empty, the existing write path handles storage

The tagger may be a rules-based classifier (keyword + intent patterns) or a cheap LLM call — whichever is more reliable. It must NOT add latency to the main turn response (run async or as a post-process step).

`executive.py` — do NOT touch (FREEZE_V1_LOCK, unless this WO is explicitly given a lift).

---

## Acceptance Tests

- **AT-1:** "What should I wear for the weather?" → turn tagged `contextual_state`. Lifted to vault. Readable cross-session.
- **AT-2:** "I've decided to go with the pneumatic joint design" → tagged `decisions` + `projects`. Lifted.
- **AT-3:** "I prefer direct replies, no padding" → tagged `preferences`. Lifted.
- **AT-4:** Generic "how are you?" exchange → NOT tagged. Not lifted.
- **AT-5:** `memory_categories` field is non-empty on tagged turns in `interactions.json`.
- **AT-6:** `vault_layer.lookup()` finds the AT-1 turn on a paraphrased query ("what did eLo recommend I wear").

---

## Return

`DONE/FROM_BUILDER_WO-067-WRITE-PATH_memory_tagging_result.md` · AT pass count · commit hash · sample tagged turn

*Board / Lead Architect · 2026-08-30*
