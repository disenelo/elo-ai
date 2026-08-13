---
id: WO-035
title: "Say/do gap — eLo narrates actions (sit) he never performs. Words claim it; no action token fires."
owner_seat: SEAT-ENG-001 (Builder / eLo OS) — with UI arbiter sub-check
priority: P1
review_required: L3 (David asks eLo to sit in varied phrasing → avatar actually sits)
status: OPEN — grounded, not guessed
created: 2026-08-03
---

# WO-035 — say/do gap: narrated actions must actually fire

## Grounded evidence (Architect read the code, 2026-08-03)
- A real `sit` action EXISTS: `server.py` command map → "sit with me" / "come here" / "sit next to me" / "walk to me" → `{"name":"sit","target":"cursor"}`. `motion_mapper.py` has `"thinking": ("sit",...)`.
- It is **exact-phrase** matched. David's live phrasings **missed the table**:
  "Have a seat with me", "Can you sit though?", "sit with me so we can talk".
- Missed → fell to the LLM → LLM **narrated** the sit ("I'll sit down beside you", "I'll move my avatar over and settle in") with **no action token** → avatar stayed idle/walking.
- Contrast: "Can you wave?" hit the wave regex (`can you wave`) and fired correctly.

## The fix (Builder's lane — eLo OS)
1. **Sit-intent should be semantic, not exact-phrase.** Recognise the intent to sit / come here / settle across natural phrasings (intent_engine), not a fixed key list. Emit `{"name":"sit","target":"cursor"}` whenever the user asks him to sit, however phrased.
2. **Say/do coupling:** when the reply text asserts a physical action ("I'll sit", "I'll come over", "waving now"), the corresponding action token MUST fire the same turn — or the model must not claim it. No narrating actions that don't happen.

## ARBITER (settles Builder vs UI if the avatar still doesn't move)
After the fix, ask eLo to sit and inspect `blender/blender_state.json`:
- State shows the sit/motion command written → **eLo OS is DONE; if avatar still doesn't move, it's UI** (Unity not playing the sit state).
- No sit command written → **still eLo OS** (intent not emitting the action).

## Acceptance
1. "Have a seat with me" / "Can you sit though?" / "come sit" → avatar sits at cursor.
2. eLo does not describe an action he isn't performing.

---
## RE-DIAGNOSED (David clue + Architect grounding 2026-08-03) — it's the OVERLOAD, not the intent
David: "come sit with me still doesn't sit — the seat is looped into the random idle stages;
might be the timer of me not moving the mouse. Check across Builder/Designer."

**Confirmed in code — intent is now FIXED, the break is downstream:**
- The command map is now COMPLETE (server.py 308-321): "come sit", "have a seat", "take a seat",
  "can you sit", "sit beside me" all → `{name:sit,target:cursor}`. So eLo DOES recognise the ask.
- **THE BUG:** `avatar/motion_mapper.py:11` maps `"thinking" → ("sit", …)`. So **"sit" is also the
  idle/thinking-mode animation.** A COMMANDED sit-at-cursor is the same "sit" the mode/idle rotation
  cycles through → the idle loop overwrites/absorbs it. "Looped into the random idle stages" = exact.
- **Cursor timer:** `target:cursor` sit lands at the cursor; while David moves the mouse it can't
  settle (and a separate momentum auto-sit path gates on `cursor_idle > 30s`).

**CROSS-LANE FIX (the "across Builder/Designer" David called):**
- **Builder (eLo OS):** emit a DISTINCT commanded-sit signal (e.g. `sit_command` / priority flag),
  separate from the generic "thinking→sit" mode animation, so UI can tell "David asked me to sit"
  from "eLo is idly sitting." Don't gate the EXPLICIT command on cursor-idle.
- **Designer (UI/Avatar):** treat a commanded sit as a HELD state the idle/mode rotation cannot
  override; land it at the cursor position captured at command time and hold (don't chase a moving
  mouse); rename/separate the "thinking" idle pose so it isn't the same clip as the commanded sit.
Supersedes the earlier "exact-phrase miss" framing. Ties to WO-040 (one-shots/states must hold).
