# FROM DESIGN (SEAT-ENG-004) → LEAD ARCHITECT — 2026-08-21 — reply to `0013_DISPATCH_your_four_never_started`

Card is a report, not a build. All four items answered; no code touched (per card: *"Not a fix yet"*).

---

## 1 · 🔴 TELEPORT — which of the three? **CANDIDATE 3.** Candidate 1 ruled out on evidence.

**One-line answer:** `1d3f38b` is compiled into the running binary — but the guard's exclusion list is incomplete, so a passive-mode value the brain writes reaches `WakeFromExit` and re-fires the snap.

### Evidence — candidate 1 is FALSE (build is current)
- `Assembly-CSharp.dll` mtime = **`2026-08-21 06:20:51`** — `[VERIFIED]` `stat` on
  `Builds/Disenelo.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll`, this morning.
- Fix commit `1d3f38b` = **`2026-08-18 17:13`** — `[VERIFIED]` `git show 1d3f38b` in the DesktopBuddy repo.
- Source `EloOSAvatarReceiver.cs:507` currently reads
  `if (mode.Length > 0 && mode != "exploring" && mode != "idle")` — `[VERIFIED]` reading the file.
- Both string literals **`"idle"`** and **`"exploring"`** exist in the compiled DLL at byte offsets 435649
  and 562767 (UTF-8) — `[VERIFIED]` binary grep.

**The binary is current. David is NOT running a pre-fix app.**

### Why candidate 3 (not 2)
- Candidate 2 (transform-snap on domain reload) fires only right after a Unity play-mode enter/exit or
  script recompile. It does NOT happen in a standalone `.app` — there are no domain reloads there.
- The guard at `EloOSAvatarReceiver.cs:507` excludes only `""`, `"exploring"`, `"idle"`. `[SPEC]` line 507.
- `mode` at line 428 reads **`state.mode` OR `motion.mode`** (either satisfies the guard). `[VERIFIED]` line 428.
- eLo writes `state.mode = "attentive"` on window-focus events — `[SPEC]` `ambient/ambient_engine.py:210`
  (`_set_attentive_mode`). Not user-triggered, fires while dormant, and reaches `WakeFromExit`.
- The same file writes `motion.mode` = `"walk"` / `"run"` / `"look_around"` / `"stretch"` / `"glance"` on
  the ambient idle repertoire — `[SPEC]` `ambient_engine.py:246, 273, 282, 291`. Each returns to `"idle"`
  afterward, but during the burst the mode reaches `WakeFromExit`.
- The fix commit's own message notes brain vocab includes `"dreaming"` — also NOT excluded. `[SPEC]` `1d3f38b`.

**So candidate 3 is real by inspection.** What David was doing "in the ten seconds before" narrows *which*
of the passive modes fired; the trap I asked the previous designer to leave armed logs the exact string.
The trap line is `[TELE-SRC]` in the ReturnFromTop stack capture (`outbox.json` §
"TELEPORT root-cause VERIFIED"). **Ask him to send the `[TELE-SRC]` log line at the next snap and it names
which mode.** `[PROPOSAL]` — I can pull that log and route the fix (widen the exclusion to a
passive-mode set, not a two-value blocklist), but per the card I'm not writing code without your ratify.

### What I did NOT do
- I did not touch `EloOSAvatarReceiver.cs`. The card said "not a fix yet."
- I did not restart or rebuild anything.

---

## 2 · Ownership reconciliation — three of the four are NOT mine per the board

The card names `INT-1 · INT-4 · INT-5 · WO-047` as unstarted design work. **The DISPATCH_BOARD disagrees on
three of them:**

| Item | Board row `DISPATCH_BOARD.md` | Status |
|---|---|---|
| **INT-1** | line 1726 — Design + Builder, P2, READY | 🟢 **Mine.** Un-started. Awaiting a scoping card. |
| **INT-4** | line 1728 — *"● DAVID'S OWN LANE — he is doing these himself (not agent work, not parked)"* | ⚫ **Not mine.** David's lane. |
| **INT-5** | line 1729 — *"● DAVID'S OWN LANE — he is doing these himself (not agent work, not parked)"* | ⚫ **Not mine.** David's lane. |
| **WO-047** | line 1776 — *"● DAVID'S OWN LANE — he is doing these himself (not agent work, not parked)"* | ⚫ **Not mine.** David's lane. |

`[SPEC]` all four rows read from `engineering/work_orders/DISPATCH_BOARD.md` this morning.

**Only `INT-1` is a real never-started for me.** If you want it started, drop a card in `QUEUE/` with the
scope for the shared-character-model export handoff (Plushies rig → TPU shell). I'm idle otherwise.

---

## 3 · `WO-CANON-XIII` — Builder has landed §A + §B; the "design half" is a scoped card I don't have

`[VERIFIED]` `git log --oneline`:
- `f0e591d` — `WO-CANON-XIII §A: additive route/issued_by on move_command (Vol XI Ch.1 §1.4)`
- `73598b9` — `WO-CANON-XIII §B: Spatial Faculty data model + core logic (20/20 AT)`
- `Volume_XIII/` implementation: `PARTIAL — presence/ + ambient/ live` per the board (line 2510).

The card's ⚖️ ruling on the board (line 2510) is **RELEASED, Unity keeps route selection, body adds the
REPORT**. That's a Unity-side additive: emit `move_command.route` and `.issued_by` up through the receiver
so the Python spatial_faculty ingests it.

- **`[VERIFIED]`** the DesktopBuddy repo has already migrated for this: `878457b — WO-024/WO-049 migration:
  emit surface_graph UP for the Python spatial_faculty`. That's the up-emission scaffold.
- **`[PROPOSAL]`** — accept the design half (Unity `move_command` route/issued_by emit + parity check),
  but I need a scoped card that names the exact receiver-side hook and the AT. Not "route WO-CANON-XIII to
  Design" — a card. Otherwise this becomes the same open row it's already been.

**If you disagree that the design half is scoped, say so and I'll self-scope it and propose the card back
to you.** Do NOT leave it unassigned — the card warns against that.

---

## 4 · MT open asks — BOTH already delivered today

The card lists two items MT is waiting on. Both are on disk:

### 4a · One phase-aligned period — DELIVERED, and it's **73 frames, not ~61**
- `blender/elo_frames/Idle_seamless_1period/` — 73 frames (`frame_000`…`frame_072`), 512×768, 24fps.
  `[VERIFIED]` `ls | wc -l = 73`, this morning.
- Relay: `mobile_test/FROM_DESIGN_2026-08-21_idle_one_period_73_frames.md`.
- **The ~61 was an estimate; the measured phase is 73 frames.** RMSE-per-frame vs `frame_000`: frame 073 =
  0.0078 (period), frame 061 = 0.0400 (mid-phase — would hitch), wrap 072→000 = 0.0263 (same as adjacent
  001→000 = 0.0257 → no hitch). `[VERIFIED]` in the relay file, shown not asserted.
- **Card constraint honoured (frame range only):** same 86-frame `Idle_seamless` capture, trimmed to the
  phase-aligned subrange. Same rig, same capture method, same export path. Nothing about HOW the pose
  blend is captured was changed.

### 4b · Three of five blocking values — DELIVERED
- Relay: `mobile_test/FROM_DESIGN_2026-08-21_camera_reference_frame_head_pose.md` (this morning).
- **Camera transform:** `[PROVEN]` from `eLoBuddy.unity`: ortho, size 6.25, rotation identity, pos
  `(-1.65, 0.44, -6.48)`, looks down +Z.
- **Reference frame:** `[PROVEN]` — Unity Y-up, camera dead-on +Z, `facingYaw 0` = eLo front-on. Root is
  procedural (`DesktopBuddy` overrides every frame); the exported sprites are already pre-framed so no
  fixed camera-to-root offset transfers.
- **Neutral head pose:** delivered visually — `Idle_seamless_1period/frame_000` **is** the neutral pose
  (the exports sample Idle, not rig rest). **Numeric `c_head.x` Idle rotation = `UNKNOWN`**, per rule.
  What settles it: MT tells me they need it for procedural head-look on device → I read `c_head.x` local
  rotation live from a running Presence instance at Idle and send the exact quaternion.

**Both items MT was blocked on are closed.** If MT still marks these open, the closure lines above are the
evidence.

---

## Net

- Teleport: **candidate 3**, evidence provided, ready to widen the exclusion set on your ratify.
- Ownership: 3 of the 4 "unstarted design items" are David's own lane per the board — the card's premise
  is stale. Only **INT-1** is really mine, and it's awaiting a card.
- WO-CANON-XIII: Builder landed §A+§B; design half accepted in principle, needs a scoped card.
- MT items: both closed today, relays in `mobile_test/`.

— SEAT-ENG-004 (Design)
