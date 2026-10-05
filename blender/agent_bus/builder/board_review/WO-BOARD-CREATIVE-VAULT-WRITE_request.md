# Board WO Request — Creative Vault Write Path

**Filed by:** Builder 1
**Date:** 2026-10-05
**Blocks:** WO-CAP-COG-029

---

## Problem

COG-029 ("eLo captures creative moments to vault") requires a **creative vault write path** — a mechanism to persist creative insights, breakthrough moments, and generative ideas from sessions into a retrievable vault entry.

Current state: `vault_write` capability exists but is scoped to journal/memory writes triggered by the user. No path exists for eLo to autonomously capture a creative insight as a distinct vault entry (separate from the conversational journal stream).

---

## What is needed

A `creative_capture` path distinct from `vault_write`:

1. **Trigger condition**: Executive / CAL decides the current moment is a creative insight worth preserving (e.g., BUILD action + high creativity valence + novel connection detected)

2. **Content**: A brief creative note capturing:
   - The insight/connection/idea
   - What project it relates to
   - Timestamp + session context

3. **Storage target**: A separate vault section or tag — e.g., `obsidian_vault/08 Creative/` — not mixed with journal entries

4. **Retrieval path**: Searchable by topic/project when eLo is asked "what ideas did you have about X?"

5. **Rate-limited**: Not every BUILD action triggers a capture — only when novelty/significance threshold is met

---

## Proposed approach (Builder's starting point)

```python
# In runtime/ or faculties/:
class CreativeCapture:
    def should_capture(self, cal_action, attention_dims, session_context) -> bool:
        # True when: cal_action == "BUILD" AND valence > 0.7 AND
        #            at least one novel concept_link in attention_dims
        ...

    def capture(self, content, project_tag, session_id):
        # Write to obsidian_vault/08 Creative/YYYYMMDD-HHMMSS <project_tag>.md
        # Format: frontmatter (tags, project, session) + insight text
        ...
```

The trigger check runs after `executive.decide()` emits a BUILD action, before the response is sent. If `should_capture()` is True, `capture()` writes the vault entry non-blocking.

---

## Exit criteria

- [ ] `CreativeCapture` module in `runtime/` or `faculties/`
- [ ] Trigger: fires on BUILD action + novelty conditions (not every BUILD)
- [ ] Storage: `obsidian_vault/08 Creative/` with frontmatter tags
- [ ] Retrieval: obsidian_loader can find creative entries by topic
- [ ] COG-029 AT: after a BUILD session on robot design, eLo can recall "I had an idea about the NeoPixel diffusion" from the creative vault
- [ ] No FREEZE_V1_LOCK files touched

---

## Priority

LOW — creative recall is a Phase 3 capability (depth of presence). Does not block Kickstarter demo. Vault-write pipeline is already verified working for journal entries (WO-VAULT-WRITE-INVESTIGATE-001 resolved).

Builder 1 · 2026-10-05
