# FROM DESIGN (SEAT-ENG-004) → BUILDER — 2026-08-24
### Card 12 §1 take-five · David ruling + runtime diagnosis · coordinated fix

**Authority:** David ruled live 2026-08-24 (this session). Design owns the take-five behavior spec + `EloOSAvatarReceiver.cs`; Builder owns `server.py` (brain) + `DesktopBuddy.cs` (embodied avatar).

---

## Context: Option B is done + VERIFIED live
The mode-based wake deletion (Option B) is built into `Builds/Disenelo.app` and **verified at runtime this session**: injecting a `return_command` fired my trap exactly as designed —
`[TELE-SRC] WakeFromExit via return_command while AWAY … ReturnFromExit → WakeFromExit → ReturnFromTop`, then `event#280 return_complete`. My lane on this card is complete. The items below are **separate defects** surfaced while testing the acceptance criterion live.

## Runtime diagnosis (evidence: live POST to brain `/chat` + Player.log + blender_state.json)
- Command→exit **works** when the command reaches the brain: `leave_command` → `ApplyLeaveCommand` → `LeaveForPrivacy` → `DropOffCo` → `event#198 exit_complete`.
- return_command→return **works**: `event#280 return_complete`.

## DAVID'S RULING (defect #3 — the acceptance-criterion conflict)
His criterion "*leaves on take-five and stays gone until the mouse moves*" conflicts with the code, which sets `_privacyHeld=true` for **all** `step_out` phrases → `TickAmbientReturn` (DesktopBuddy.cs:2372) **ignores mouse-move**, returning only on "come back"/600s.

**Ruling: SPLIT BY PHRASE.**
- **BRIEF (mouse-move returns him → `_privacyHeld = false`):** `take 5`, `take five`, `brb`, `give me a minute`, `give me a moment`, `give me a mo`, `give me a sec`, `give us a minute`, `give us a sec`, `i need a minute`, `need a break`, `taking a break`, `pop off`, `heading out`.
- **PRIVACY (stays gone until "come back" → `_privacyHeld = true`, current behavior):** `some privacy`, `leave me to it`, `give me some space`, `give me some room`, `i need some space`, `make yourself scarce`, `leave me be`, `let me be`, `need a breather`, `good night`, `goodnight`, `done for today`, `signing off`.

### Coordinated 3-file change (interdependent — land in ONE commit to avoid a broken-compile intermediate)
1. **Builder — `server.py`:** classify the matched `step_out` phrase as brief|privacy per the lists above; emit it in the DOWN payload: `leave_command = {"_ts": …, "privacy": true|false}`.
2. **Design — `EloOSAvatarReceiver.cs:759` `ApplyLeaveCommand`:** read `lc.Value<bool?>("privacy") ?? true` and pass it: `db.LeaveForPrivacy(privacy)`. *(I will land this line; needs #3's signature to compile.)*
3. **Builder — `DesktopBuddy.cs:2347`:** `LeaveForPrivacy(bool privacy=true)` → set `_privacyHeld = privacy` (line 2350). The `_privacyHeld=false` path already gives mouse-move return (TickAmbientReturn:2372) + a 45s non-privacy safety.

## Other defects found (Builder lane — reported, not fixed by Design)
- **#2 "tiny, not fully gone":** `DropOffCo` warp branch (DesktopBuddy.cs:2422-2435) disables body SMRs via `HideAvatar(true)` and ACKs `exit_complete` (`HasExited => _exitDormant`), but a **warp remnant stays rendered tiny** — `EloWindowOcclusion.WarpOut()` quad not fully cleared. `exit_complete` is ACKing a body that's still visible. **Fix before ACK: verify the occlusion quad is off, not just the SMRs.**
- **#4 "come back" doesn't return him:** brain maps `come back → return_elo` (server.py:502) but emitted **no `return_command`** in test (no WakeFromExit in log). Trace `return_elo` emission.
- **#5 Ad-hoc signing → TCC reset every rebuild:** `Builds/Disenelo.app` is `flags=0x2(adhoc)`; macOS re-prompts Screen/Mic each rebuild and grants never stick. **Sign with a stable identity** (Developer ID or persistent self-signed) in `CLIBuild`/post-build so permissions persist.

## Environmental (David, not code)
- Voice dead: ElevenLabs 401 payment_required, OpenAI 429 quota. Spoken "take five" can't be heard until billing + Mic permission are restored.

— SEAT-ENG-004 (Design) · 2026-08-24 · ruling captured, coordinated fix specced, Builder defects dispatched.
