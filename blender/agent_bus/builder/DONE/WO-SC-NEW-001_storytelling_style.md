# WO-SC-NEW-001 — storytelling_style in Meaning Object
**Seat:** Builder  
**Issued:** 2026-08-24  
**Authority:** CA directive (re-centre on observable eLo capability) + David L3 ratification 2026-08-24  
**SPEC:** `docs/architecture/specs/SPEC_SC_NEW_001_storytelling_style_2026-08-24.md` — read it; this WO is a subset.  
**RTR:** RTR-031  
**Priority:** After WO-NAV-013 + WO-WORLD-001 defect fix — parallel if capacity allows.  
**Depends on:** Meaning Object ✅ · Conversation Faculty ✅ · Response generation ✅ · No navigation WOs required.

---

## Why this matters (observable eLo capability)

eLo currently speaks in a single register regardless of conversational context. This WO gives him per-turn narrative range: direct when the answer just needs stating, exploratory when thinking together, playful when it fits, reflective when looking back. David will be able to hear a different eLo. This is intent recovery (RTR-031) — one of the gaps from the CCM audit.

---

## Scope — 3 changes, same lane (.py only)

### D-1 — Add field to Meaning Object schema

File: wherever `MeaningObject` / the meaning dataclass is defined (`runtime/` — find it, do not guess).

```python
storytelling_style: str | None = None
```

That is the entire D-1 change. One line. Default `None` = use CHARACTER DNA defaults.

---

### D-2 — Inference in Conversation Faculty

File: Conversation Faculty (`runtime/` — find the file that assembles the Meaning Object, do not guess).

Add a new inference step that sets `storytelling_style` before the Meaning Object is passed forward. Infer from available signals in priority order:

1. **Voice State context** (until SP-29/CP-003 are built):
   - `VOICE_CREATING` / `VOICE_BUILDING` → `"collaborative"` or `"imaginative"`
   - `VOICE_REFLECTING` / `VOICE_REVIEWING` → `"reflective"`
   - `VOICE_PLAYING` → `"playful"`
   - `VOICE_LEARNING` → `"exploratory"`
   - Other / default → `"direct"`

2. **Relationship state** (if available in current context): David in a creative session → prefer `"collaborative"` or `"imaginative"`. Problem-solving → `"exploratory"`. Casual → `"playful"`.

3. **CHARACTER DNA constraint**: eLo never loses directness and curiosity. Any inferred style must be compatible with his core character (calm, grounded, earnest). Do not let style override character — augment it.

4. **Fallback**: `None` — if Voice State is absent or indeterminate, leave `None`. Response generation handles `None` gracefully (falls back to CHARACTER DNA).

Do NOT hard-code a static `"direct"` or any single value. The inference must actually vary by context.

---

### D-3 — Consume in response generation

File: wherever response generation assembles the prompt / CAL action expression.

Add a read of `meaning.storytelling_style` that influences how the CAL action is expressed. The CAL action is the anchor — `storytelling_style` shapes the framing:

```python
if meaning.storytelling_style == "playful":
    # riff-able, light framing
elif meaning.storytelling_style == "exploratory":
    # open-ended, thinking-aloud
elif meaning.storytelling_style == "reflective":
    # slow, depth-first, looking back
elif meaning.storytelling_style == "collaborative":
    # step-by-step, building together
elif meaning.storytelling_style == "imaginative":
    # wide associative, possibility-space
elif meaning.storytelling_style == "grounded":
    # anchored, practical, steadying
elif meaning.storytelling_style is None:
    # CHARACTER DNA defaults — eLo's baseline
```

Exact implementation: Builder's call. What matters is the field is read and has a visible effect on the response prompt or output assembly. Do not leave it as dead code.

---

## Lane rules

- `.py` only. No `.cs`, no test file creation.
- Do not touch `executive.py`, `CHARACTER DNA`, Voice State definitions, or CAL Actions.
- Do not change the Meaning Object schema beyond adding the one field.
- If you find the existing Conversation Faculty or response generation code is not structured to support this cleanly, note the gap in your result and implement what you can. Do not refactor unrelated code.

---

## Acceptance tests

| AT | Test | Pass criterion |
|---|---|---|
| AT-1 | `MeaningObject()` initialises with `storytelling_style=None` | Field present, default None, no error |
| AT-2 | Conversation Faculty produces a non-None `storytelling_style` for a creative-context turn (e.g. Voice State = CREATING) | Field populated, not None |
| AT-3 | Conversation Faculty produces `storytelling_style=None` or `"direct"` for a default/low-signal turn | Field present, correct for context |
| AT-4 | Decision journal / per-turn log shows `storytelling_style` value | Field visible in turn output |
| AT-5 | Response generation reads `storytelling_style` and the field is not dead code | Code path exercised (can be verified via log output or code read) |

---

## Return evidence

File in `builder/DONE/` (or `FROM_BUILDER_WO-SC-NEW-001_result.md`) with:
- Which files changed
- Commit hash
- AT-1 through AT-5 pass/fail
- One example: what `storytelling_style` eLo inferred in a test turn

---

*Board / Lead Architect · 2026-08-24*
