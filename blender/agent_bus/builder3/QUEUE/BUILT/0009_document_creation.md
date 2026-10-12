# WO-B3-0009 — Document Creation Capability
**Seat:** Builder 3  
**Priority:** P1 — demo milestone end of October  
**Source:** `docs/architecture/_intake/SOURCE_DEMO-MILESTONE_2026-10-10.md` [DAVID 2026-10-10]  
**Date:** 2026-10-10

---

## What

eLo can create documents on David's Mac when asked. "Make me a list of..." / "Write that up" / "Create a doc with..." → eLo produces a file.

---

## How

- Add `create_document` to capability registry (`capability_registry.py`)
- Initial formats: plain text (.txt) and markdown (.md) — simple, no dependencies
- Write to a known output path (e.g. `~/Documents/eLo/` or `~/Desktop/`) — confirm with David which directory
- eLo acknowledges before creating ("Give me a second, I'll write that up"), then confirms when done with path
- Integrate with inner thought acknowledgement pattern (WO-B1-0108 filing — execution acknowledgement)

Stretch: PDF or styled output if time permits. Plain text first.

---

## Capability registry entry

```python
"create_document": {
    "description": "Creates a text or markdown document on the local machine",
    "triggers": ["write that up", "make a list", "create a doc", "write me", "save that"],
    "handler": "tools/document_writer.py"
}
```

---

## Done when

Live turn: David asks eLo to write something up. eLo creates the file. David can open it. Board verifies file exists at expected path with correct content.

File to Board for sign-off.

---
## Result (Builder 3, 2026-10-10): built, a84dbe2. Needs a Presence relaunch + David's live turn
- `tools/document_writer.py`, wired as a direct answer in `tools/tool_router.py`; capability `create_document` in `runtime/capabilities/registry.py` (WO-018 gate). Extends draft_agent's cloud call (fallback) and the conversation tracker (for "write THAT up").
- Triggers: "make me a list/checklist…", "write that/this up", "create/make/write/draft a doc|document|file|list|summary|plan|outline|brief|report…", "save that as a document", "put that into a plan". **Not**: "make a note" (Apple Notes), "remind me" (reminders).
- Output: `~/Documents/eLo/<date>-<title>.md` (`.txt` when asked; never overwrites). eLo: "Done — I wrote it up: “<title>”, saved in ~/Documents/eLo as <file>."
- **Folder: ~/Documents/eLo is my default.** The card says to confirm with David; it can change via `ELO_DOCS_DIR`.
- Local model first (25 s for a real checklist), cloud fallback.
- Not done: the "give me a second…" acknowledgement before writing (that's B1's WO-0108 execution-ack pattern; the turn currently just takes ~25 s), and PDF (stretch).
- Tests 22/22 (temp folder, model stubbed).
