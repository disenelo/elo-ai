# eLo OS — Executive Faculty
# → SUPERSEDED BY **Volume VII — Executive Cortex**

**STATUS: POINTER.** This file was a stub (*"STATUS: PENDING — to be written in a dedicated
session."*) for as long as the Executive had no canon. It now has one.

**The Executive's canon lives in `docs/architecture/Volume_VII/`.**

| Chapter | Title | Covers |
|---|---|---|
| [`00_Metadata.md`](Volume_VII/00_Metadata.md) | Executive Cortex | Scope · anchors in live code · build queue · open questions · honest implementation status |
| [`01_The_Executive_and_One_Plan_Per_Turn.md`](Volume_VII/01_The_Executive_and_One_Plan_Per_Turn.md) | The Executive and One Plan Per Turn | Executive Authority · the nine-action Conversation Action Layer · one `CognitivePlan` · why the Executive is deterministic and the LLM is the voice, not the seat of self |
| [`02_Executive_Assembly_and_The_Moment.md`](Volume_VII/02_Executive_Assembly_and_The_Moment.md) | Executive Assembly and The Moment | **Ruling C** — `UnifiedCognitiveState` assembled BEFORE the decision · the ordering contract · The Moment · degradation → epistemic ceiling |
| [`03_Epistemic_Tiers_and_Verified_Speech.md`](Volume_VII/03_Epistemic_Tiers_and_Verified_Speech.md) | Epistemic Tiers and Verified Speech | "I know" / "I think" / "I don't have that" · the speech gate · ADR-Exec-001 enforcement · the **Situated Self Retrieval invariant** |
| [`04_Intent_Queue_and_Why_Did_I_Do_That.md`](Volume_VII/04_Intent_Queue_and_Why_Did_I_Do_That.md) | The Intent Queue and "Why Did I Do That?" | The dual-intent queue (conversational vs body/action) · arbitration · the decision journal — explanation from record, never confabulated |
| [`05_Brain_Body_Brain_The_Closed_Loop.md`](Volume_VII/05_Brain_Body_Brain_The_Closed_Loop.md) | brain > body > brain | The brain decides and drives DOWN; the body only senses, acts and reports UP; **the body never decides** · ACK before belief · the reflex line |

**Why this file still exists:** `runtime/spine/executive_faculty.py` names it in its docstring
(*"Architecture spec: docs/architecture/09_executive_faculty.md"*), and that module is in the
Builder's lane — the Architect does not edit code. The pointer stays until the seat updates the
reference. Do not add specification here; it belongs in Volume VII.

**Volume VII status: REVIEW.** Implementation is **PARTIAL** — `runtime/executive.py` is live and
FROZEN (`FREEZE_V1_LOCK.md`); `runtime/the_moment.py` (WO-079) and `self/decision_journal.py`
(WO-082) are live; the assemble-before-decide ordering (Ruling C), the dual-intent queue, and the
enforced UP-relay rule are PENDING. Each chapter marks its own gaps in place.
