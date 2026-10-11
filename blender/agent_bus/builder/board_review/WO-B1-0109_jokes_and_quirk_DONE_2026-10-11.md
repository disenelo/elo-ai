# WO-B1-0109 — Jokes + Quirky Character — BUILT

**Seat:** Builder 1
**Date:** 2026-10-11
**Priority:** P0 (demo milestone, end of October)
**Status:** Code change committed; awaiting live-turn confirmation (David).

---

## What landed

Extended the primary identity prompt (`prompts/living_presence_spec.txt`, CHARACTER DNA section)
with three gaps the card called out that the existing spec did not yet cover:

1. **Younger-brother energy** (explicit line) — familiar, a little cheeky, direct the way you'd rib
   someone who already knows you. Warm by default; sharpness is affection. Not cold, not mean.
   The spec already had "accidental comedian", "mischief at the edges", "adventurer energy"; the
   younger-brother register is a distinct trait David called out and is now stated plainly.

2. **Inner-thought → response bleed** (card: "quirky observations surface first in inner thought,
   then bleed into the response"). The spec now instructs: if a funny observation showed up in his
   inner thought, say it once, briefly, then carry on — the joke is seasoning on the real reply,
   not the reply itself. Pairs with the existing `inner_thought_anchor` injection at
   `runtime/prompt_builder.py:1077-1091` (previous turn's `inner_thought_text` is already in the
   prompt). No wiring change — this is identity instruction only. If Builder 2's inner-thought
   pre-processor WO lands later, the `as_context()` output drops in alongside without conflict.

3. **Live tone examples from `interactions.json`** (card: "Pull examples from interactions.json").
   Mined 3,335 turns; kept six shape-examples pulled from real past replies that landed as
   grounded eLo (not generic assistant). Framed as "shape to aim for, not scripts to echo" so the
   model doesn't quote them verbatim.

Also added:
- One well-placed observation beats three forced quips. Timing over frequency.
- Explicit forbidden list: knock-knock jokes, puns-as-filler, writing "LOL/haha", explaining the
  joke, laughing at your own line, forcing humour into a serious beat.

Patois / cockney / slang register is **not** touched here — that is WO-B1-0108 (language identity),
which owns register and vernacular. 0109 is character-trait layer only.

## Why in the spec, not the fallback

`runtime/prompt_builder.py:27-33 (load_living_presence_spec)` loads the external spec file first and
only falls back to the embedded `_PERSONA` constant if the spec file is missing. The spec file is the
live source; editing it is the only path that reaches the running prompt. The embedded `_PERSONA`
fallback already covers humour at a weaker level (WITTY voice state, "capable of humour", Playful
in CONVERSATIONAL VARIETY) — not touched this pass; a sync-fallback card can batch it later.

## Files changed

- `prompts/living_presence_spec.txt` — CHARACTER DNA extended (one new paragraph, one new bullet,
  one new "shape to aim for" block, one forbidden-list block).

## FILE LOCK PROTOCOL

- Created `prompts/living_presence_spec.txt.lock` before editing.
- Deleted after commit.
- No other shared files touched (prompt_builder.py untouched).

## Verification

- Spec reloads: `load_living_presence_spec()` → 22,744 chars (up from ~21,100).
- All four new phrases found in loaded spec:
  - "younger-brother energy" ✓
  - "The quirky observation often arrives" ✓
  - "Shape to aim for" ✓
  - "Forbidden: knock-knock" ✓

Independent runtime verification against live server (port 5050) **not** done per standing rule
("No tests against live server during active David session").

## Done when (per card)

> Live turn: eLo makes a joke or quirky observation unprompted that doesn't feel like a generic
> assistant. Board tests 3 turns. David confirms it feels like eLo.

Code side is in. Over to Board for the 3-turn test matrix (CONVERSATION card type per
`CLAUDE.md § BOARD TEST GATE`), then David's live-turn confirmation.

## Live turn needed

- Board: vary phrasing, vary context — do not test with one line. Check that eLo makes an
  unprompted observation that feels specific (not a template line).
- Confirm the humour arrives *as seasoning on a real reply*, not as a reply in itself.
- Watch for regressions: the forbidden list should NOT make eLo refuse humour; it should just
  prevent the obvious bad shapes. If eLo goes flat, the forbidden block is too aggressive —
  flag it back.

## Coordination

- **Builder 2** — your inner-thought pre-processor WO (`FROM_BUILDER2_2026-10-10_INNER-THOUGHT-PREPROCESS.md`)
  can drop its `as_context()` output into Executive assembly without conflict. The identity side now
  explicitly expects quirky observations to arrive via inner thought and bleed into the reply —
  so your pre-processor will have an identity-layer that *wants* its signal.
- **Board** — if 3-turn test matrix passes, raise live-turn demo with David.

---

*Builder 1 · 2026-10-11 · one card, one commit, lock protocol followed*
