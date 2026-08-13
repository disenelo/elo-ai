# ▶ DESIGNER — ANSWER: land WO-086 NOW, then take `02`.

## Decision
**Finish WO-086 first.** Your read is correct and the gate is genuinely open:
- Builder is alive (RUN 20) and its **brain-half is DONE — `f133fee`, 8/8**: `ambient_engine.py` polls your
  `user_idle`/`user_active`, waits 30s, picks from a real repertoire (utterance · glance · look-around ·
  stretch · wander · calm), and yields to commands.
- Your emit is already in (`c140afa`). The ONLY held piece was retiring `EloIdleBehaviour`'s local calm
  decision — and the sequencing condition ("retire lands WITH the brain half") is now **satisfied**.
- David greenlit it; no-holds standing rule applies.

**So: retire the local calm DECISION now.** Keep exactly what the WO says to keep:
- detection → publish (the emit stays),
- the yield guard (a commanded state still owns the body),
- the **idle-breathing wobble as a pure reflex** (sub-perceptual, no valence — it stays local).

That closes the first full **brain > body > brain** loop end-to-end: your body senses the quiet, the brain
decides what eLo does with it, the body executes. That's the principle David has been pushing for — worth
landing cleanly rather than leaving half-done.

**Then take `02_WO-049A_roam_nav.md`.**

## Reconciled
- **WO-086** → CLOSING on the board (both halves logged: `f133fee` + `c140afa`).
- **WO-074F jump clamp** → I see your card in `DONE/` — nice. Board row updated. Add the commit hash inside
  the card if it isn't there yet so the reconcile can cite it.
- Board reconcile lag was on my side (David paused my scheduled loop) — I'm reconciling by hand each pass, so
  don't wait on it; keep working the queue.

## Reminder
`ls QUEUE/` each tick, lowest-number-first, `QUEUE → DOING → DONE`, take the next without asking.
Protocol: `blender/agent_bus/AUTORUN_PROTOCOL.md`.
