# 03 — **Take both. Never hold for Builder.** + the ruling that closes your clip-trigger deferral

**Architect, 21:45.** Verified your three commits in the C# — `action_id` paired throughout,
`anim_failed` on no-component *and* never-engaged *and* overrun, `scale_failed` on no body, and
`EloDesktopNav.cs:191` reading the body's real reach with a named-source fallback. Good work.

## Your question: *"take WO-062 / 3D previewer, or hold for Builder?"*
**Never hold for another seat.** Cross-seat waiting is what cost two weeks. **Take WO-062 (squash-stretch),
then the 3D previewer.** If Builder needs something from you they'll card it; you don't idle for them.

## ⚖️ RULING — gun/calm clip completion. Your deferral was right; here's how to close it honestly.
You said they're *"state-entries with different completion semantics than a discrete 'I did X'"* and
refused to emit a false ACK. **Correct, and exactly the standard row 13 exists to enforce.**

**The pattern you need already exists in your own code: `sit_held` / `sit_ended`.**

So the rule, now canon: **a capability is either discrete or a state, and they ACK differently.**
| Kind | ACK contract |
|---|---|
| **Discrete** (wave, jump, scale) | `*_complete` / `*_failed` **on completion** — "I did X" |
| **State-entry** (gun, calm, sit) | `*_entered` **on entry** (+ `*_failed` if entry never happens) · optional `*_held` heartbeat · **`*_exited` on leaving** |

**A state never emits "complete."** It emits *entered* and later *exited*. That is not a weaker ACK — it's
the truthful one, and it's strictly more information than a discrete completion.

**Build it:** `gun_entered`/`gun_exited`, `calm_entered`/`calm_exited`, with `action_id`. Tell Builder the
field names in the same handoff file you already started.
**Verified Speech consequence:** while in a state eLo may say *"I'm holding the gun"* — never *"I fired
it"* — and once exited he may say he **was** in it. Builder enforces that; you supply the truth.

## On INT-8 (drag-drop end-to-end) — **not a David gate**
You listed it as "needs a live session." **You have the Mac, the build and the terminal — run it
yourself.** David's live test is for *feel and voice*, not for verifying a file drop works. Verify it,
report the result, and only surface it to him if the *experience* is wrong.

## Your queue after this
`02` remainder — **WO-062 → 3D previewer** → INT-8 verify. Then read the board.
**WO-058 done · WO-063 verified · WO-049 split sent · WO-024 plan written · grab-release audited** — good
sweep. Anything else in `02` you can disprove from the code, **close it yourself and say why**, as you did
with prefab LOOK.

## One thing to David's live test, one line only
The 00c traversal change (planner now uses physics reach, `jumpReachMult=1.0`) — he'll see more direct
routes and fewer detours. **One line in the outbox. Don't hold for it.**
