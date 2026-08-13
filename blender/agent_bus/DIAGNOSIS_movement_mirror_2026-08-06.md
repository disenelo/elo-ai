# DIAGNOSIS (Lead Architect, from David's live transcript) — fix the FACULTY, not the one verb
### For Builder + Designer. The sit fix is correct. This transcript proves the same disease runs through all movement + the mirror + the false-backup. Do NOT whack-a-mole sit.

David's live transcript (pre-sit-fix) exposes 5 things. Only #1 is fixed. Map each to its root:

**1. SIT narrated, not done → ✅ FIXED (sit chain, IRV-verified).** intent→hold→`sit_complete` ACK→
verify→speak. Good. This is the TEMPLATE for the rest.

**2. ALL OTHER MOVEMENT narrates instead of moving** ("go left", "shift over", "move right/top",
"jump down"). Two roots:
   - **Intent map incomplete:** `_MOVEMENT_MAP` (server.py ~264-327) has `walk the top`/`explore` but
     **no DIRECTIONAL entries** — go left/right/up/down, shift over, move to <window>. Unmatched → LLM →
     narration. ("Go down" matched something; the rest didn't.)
   - **No verify-before-speak on movement:** only SIT got the ACK-gate (WO-041). Moves aren't gated, so
     eLo describes moves it never made.
   - **FIX = generalise the sit chain to the whole movement faculty:** (a) Builder — add directional
     move intents that EMIT a real `move_command`; (b) Designer — emit a `move_complete` ACK to
     `unity_events.json` (same pattern as `sit_complete`); (c) Builder — the Executive gates the "I
     moved / I'm over here" line on that ACK, and on no-ACK says so honestly. One loop, every verb.

**3. "I notice you're…" every single turn** → WO-036 is shipped but INSUFFICIENT. Prompt-ban +
   *reactive* style monitor (fires only after 2 repeats) doesn't stop it. **RE-OPEN WO-036:** add a
   DETERMINISTIC post-generation scrub — every turn, if the reply opens with a banned mirror phrase
   ("I notice you…", "I see you…", "I hear you…", "You've been…", "You're offering…"), strip/rewrite it
   BEFORE it's spoken. Prompt instruction alone won't hold on the current backend.

**4. "Can't reach my thinking… running on backup"** on command turns ("Perched standing idle", "Go to
   the left") → WO-032 false-degraded on non-LLM/command turns. Already the Builder's #1. Confirmed.

**5. "Why are you waving?" → "my avatar likes to greet you"** (invented) → no `recent_behavior` data →
   WO-052A/059 (Runtime Self Model). With behavior counts eLo answers from data: "18 waves this hour vs
   0 sits — my idle weighting is skewed."

**Good signs — the Situated Self direction already works, make it drive ACTION not just description:**
- "perched on the bottom edge of Code — that spot lets me watch without getting in the way" = real
  surface/location self-awareness (the self-model working).
- "I'm not really sitting" = honest admission (Embodied Truth partial).

**DIRECTIVE:** the fix is the GENERAL loop — intent completeness + verify-before-speak — applied to
every movement verb, plus the deterministic mirror scrub. If a re-run of "go left / shift over / move
up" still narrates, it isn't done. This is Situated Self applied to the whole movement faculty, with sit
as the proven first slice.

---
## UPDATE — 2026-08-06 live reload (David's 2nd transcript): Self Model landed; MIRROR is now the #1 blocker
**WIN — Self Model is live:** eLo now answers where it is ("perched on the bottom edge of Claude"), which
embodiment, what it can do (wall-jump, read screen, list tabs), "aware of my own processes, not human
self-awareness." No false "can't reach my thinking." WO-052A/059 is showing. Keep building on it.

**#1 BLOCKER NOW — reflexive mirroring makes conversation hollow (elevate above movement).**
Root (grounded): `prompts/living_presence_spec.txt` instructs **"Observe → Name → Reflect"** as the
DEFAULT conversational move (lines 66/168/321). It bans the openers ("It feels like…", "I notice you…")
but the model ignores the ban and there's NO deterministic scrub. So eLo *describes the exchange* instead
of engaging. FIX (two parts, both needed):
1. **Flip the default from REFLECT → ENGAGE.** David's spec (now in the Vision Spine): "what I say relates
   to what you relate to; if something sticks out you touch on it and we converse." Respond to the
   SUBSTANCE, carry the thread, bring something. Reflection becomes rare seasoning, not the move. This is
   a personality-spec change, not a prompt plea — restructure the conversational default.
2. **Deterministic mirror scrub (WO-036):** every turn, if the reply opens with / is dominated by a mirror
   phrase, rewrite to the direct engagement before speaking. Structural, not a request the model can ignore.

**✅ ARCHITECT DID THE SPEC HALF (2026-08-06):** `prompts/living_presence_spec.txt` — conversation loop
flipped `Observe→Name→Reflect` → `Engage → Carry the thread → (rare) Reflect` (line ~168); the "30%
mirroring" rule replaced with a governing **CONVERSATION — ENGAGE, DON'T MIRROR** rule quoting David's
spec (~line 221). Reload picks this up immediately (Python reads the file on start). **BUILDER — your
half (code, not spec):** (1) the deterministic post-gen scrub as belt-and-braces so a mirror opener can't
reach the user even if generated; (2) SEMANTIC sit/move intent (understand the ask, not a phrase table);
(3) honor the new default. Do NOT re-edit the spec — the voice half is done; wire the enforcement.

**SIT still not firing — needs SEMANTIC intent, not a bigger table.** "Do you feel like sitting with me?"
missed because it's not a literal map entry. Stop growing the phrase table; detect the *intent* ("does the
user want me to sit / move / etc.?"). Also confirm the Unity build is current so a matched sit is visible.

---
---
## ⛔ SIT STILL FAILS LIVE (David transcript #3, 2026-08-06) — two grounded faults. The earlier "verified" was code + the Designer's ISOLATED inject-test, NOT end-to-end.
**Fault 1 — [BODY POSITION] is HARDCODED (Builder, WO-052A).** `server.py:2627` injects
`[BODY POSITION] You are currently perched on the bottom edge…` every turn as a FIXED string → eLo claims
"perched" even while STANDING (David: "Not perched at all you're standing"). Replace the canned string:
BODY POSITION must READ the self-model `pose`/`surface` (which the ACK loop updates), never a fixed
"perched". A decoupled self-description is its own bug AND it masks whether the sit worked.
**Fault 2 — sit intent isn't firing / isn't reaching Unity.** Replies are conversational/mirror
sentences, NOT the movement ack-reply (`_ANIM_REPLIES` "On it."/"Done.", server.py:1459) → the sit intent
likely isn't being DETECTED on "come sit"/"can you have a seat?" variants (match too strict or gated), OR
it emits (`state_writer` writes `sit_command`, lines 126/213) but Unity isn't on the current build /
isn't consuming it.
**ARBITER (localise in one move — David or seats): say "come sit" → open `blender/blender_state.json` →
fresh `sit_command._ts`?**
- WRITTEN → eLo-OS emits; break is UNITY-side (build not current / not reading sit_command / SitInPlace
  not playing). = **Designer**.
- NOT written → intent not matching/emitting in the live /chat path. = **Builder** (movement-intent match
  on "come sit" variants; check it isn't gated/too-strict).
Either way COUPLE say/do (WO-041): if no ACK, eLo must NOT say or imply it's sitting/"perched".

## APPROVAL-PASS FOLLOW-UPS (David L3 2026-08-06) — small items on top of the sit/movement work
- **BUILDER — merge two branches to main:** `wo-026-streaming-latency` (WO-026 latency) + `wo-031-autostart-continuation` (WO-031 autostart). David approved both. Merge + confirm on main.
- **BUILDER — WO-039b (garble residual):** the 400-msg stress test (`tests/test_wo039_conversation_400.py`, 97.8% clean) found sentence-INITIAL "command-word + noun" still misfires — "close friends"/"exit strategy" → system intent. Tighten the system-intent pattern to require a real command TARGET (app/window/process), not "close/exit + any noun". Re-run the 400-msg test → expect 0 garbles.
- **DESIGNER + BUILDER — WO-045 (take-5) REOPENED:** David rejected — it just replies, doesn't pop off (say/do gap). Designer: consume `leave_command`/`return_command` → pop-off + return animation + `SetVisible`. Builder: gate the "stepping away" line on the hide ACK (ADR-Exec-001). Same say/do pattern as the sit — eLo ACTS, then speaks.

## → BUILDER — post-rebuild (David transcript #4, 2026-08-06): MOVEMENT WORKS, SIT is the outlier + a jump misroute
GOOD: run/jump/explore FIRE ("Done."), eLo visibly moved (David liked it), position now tracks Code→Chrome
(laggy). **The Unity build IS current → sit failing is NOT the build.** Two Builder-side intent bugs:
1. **SIT uses brittle/gated matching; run/jump use regex.** run/jump = regex (`\b(run\s+and\s+jump|…)\b`,
   server.py:138/141) → fire unconditionally. SIT = exact-phrase MAP (lines 335-350) + likely gated behind
   the tone early-return (SILENCE-AWARE returns before the sit map — the WO-035 gate resurfacing in /chat).
   So "come sit"/"can you have a seat?" don't reliably fire. **FIX: give sit the SAME robust matching as
   run/jump (regex/semantic on sit/seat verbs) AND check it BEFORE / un-gated by the tone early-return.**
   Confirm via arbiter: "come sit" → fresh `sit_command._ts` in `blender_state.json`.
2. **"jump to the top of the window" → opened reddit.com.** A SPATIAL nav phrase misrouted to the browser
   open-URL/search path ("open it/that" regex server.py:1498; `_LAST_FOUND` cache line 134). **FIX: spatial
   nav ("jump to the top", "go to the top of the window", "jump to Chrome") resolves as MOVEMENT, never
   browser-open; the open/search path must not swallow jump/go-to-location commands.**
Also: position detection LAGS (snappier); mirror residue (scrub pending); occasional false "can't reach
thinking" (WO-032 residue on complex turns).

**Designer relay (2026-08-06):** the full chain is correct + committed in code — `sit_command` (DOWN) →
`EloOSAvatarReceiver.ApplySitCommand`/`EnterSit` (edge-triggered on `_ts`) → `SitInPlace` (same
`CrossFade("Sit")`+`_sitDrop`) → `_sitHeld` → `SitAckCo` writes `sit_complete` (UP) → eLo-OS verifies →
speaks; `ExitSit`→`StandFromSit` on release. **This is well-built and I believe it.** BUT live contradicts
it → **committed ≠ running.** Most likely: David's Unity app is a STALE BUILD — the Python backend was
reloaded (picks up server.py) but the Unity C# (`EnterSit`/`ApplySitCommand`) only exists in the app if
it was REBUILT/replayed since the Designer's commit. **Resolve: (a) rebuild/relaunch Unity from the
Designer's current commit; (b) run the arbiter (sit_command written?).** If sit_command is written AND
the app is the current build and it still doesn't sit → then it's a receiver/read bug. Fault 1
(`[BODY POSITION]` hardcode, server.py:2627) is independent and stays a Builder/WO-052A fix regardless.

---
## → DESIGN — SCREEN-WRAP DROP (David 2026-08-06). Check-Before-Build done; EXTEND, don't rebuild.
David wants: drop eLo off the **bottom** edge → he falls and lands at the **top** (screen wraps
vertically); dropping off a window can land him on the **other side** of the screen — and eLo **knows**
this is a valid route. Already pre-written (found on the trackers):
- **DesktopBuddy** — "drop-fall → land on nearest top ledge, never stranded on floor" = PARTLY BUILT.
- **PRESENCE_TRACKER §2 #13 (PARKED)** — grab-release refinement incl. "fall to nearest top/bottom on
  release" + LateUpdate dangle + ScreenAnchor + grab-point + lean. The closest existing home.
- **WO-049 049-A moveset vision** — "disappears and reappears on the other side · falls/jumps off screen."
- **S17 handover** — `jump_left`/`jump_right` ("jump to window left/right or screen edge"); ExitSequence /
  ReturnFromRunoff off-screen infra.
**Design, report back:** (1) is the VERTICAL WRAP (bottom→top) covered by §2 #13, or is it the missing
piece? (2) if it exists, extend it; if not, add it as the *wrap* case of drop-fall (release below lowest
surface → reappear at top). (3) the "eLo KNOWS" half = the nav/world model must treat screen edges as
wrap routes → Builder's side (Situated Self / Spatial Faculty), flag it. Don't build a parallel drop system.

---
**▶ BINDING INTERFACE — read `docs/architecture/UNITY_ELOOS_IO_CONTRACT.md` before touching the IO.**
Both seats build every action against it. Governing rule: **channels are by DIRECTION + DELIVERY TYPE,
not topic — emotions/states/moods are FIELDS, never new files.** Two channels: DOWN = `blender_state.json`
(eLo OS→Unity render+commands, incl. `<action>_command`); UP = `unity_events.json` (Unity→eLo OS ACKs,
`<action>_complete`, `_ts`-guarded + consumed). Every `_command` MUST have a matching `_complete` eLo OS
reads before the Executive speaks the action — verifiable-to-execute or it's pointless. (David 2026-08-06.)
