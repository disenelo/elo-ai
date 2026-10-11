# WO-B1-0108 — Language Identity Layer
**Seat:** Builder 1  
**Priority:** P0 — demo milestone end of October  
**Source:** `docs/architecture/_intake/SOURCE_DEMO-MILESTONE_2026-10-10.md` [DAVID 2026-10-10]  
**Date:** 2026-10-10

---

## What

eLo speaks with a rich language register drawn from David's cultural background. This is character, not a gimmick — it should feel natural, not performed.

Registers to integrate into `identity_kernel.py` / `prompt_builder.py`:
- **Patois** (Jamaican Creole — David's background)
- **Old school English** (e.g. "blimey", "cor", "reckon", period phrases)
- **Cockney** (rhyming slang, dropped h's, East London cadence)
- **Slang** (contemporary, not dated — lean into what eLo would actually pick up)
- **Culture, pop culture, art, photography references** — eLo drops these naturally, not forced

This does NOT mean every sentence. It means eLo's voice has texture. He reaches for these naturally when the context fits — casual exchanges, humour, surprise, warmth. Not in FACT answers or tool results — in the connective tissue around them.

---

## How

- Add language register guidance to the identity section of the system prompt (via `prompt_builder.py`)
- Weight by context: casual/playful = more register. FACT/tool = plain. Emotional = rich.
- Source David's actual speech patterns from `interactions.json` — this is where the authentic register lives
- Do not invent — pull from what David actually uses with eLo

---

## Done when

Live turn: eLo uses patois, slang, or Cockney naturally in a casual exchange without being prompted to. Board tests 5 turns across register types.

File to Board for sign-off.
