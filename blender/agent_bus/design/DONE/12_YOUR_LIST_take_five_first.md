# 12 — **YOUR WHOLE LIST, ordered against David's acceptance test.**
### **LAYER:** `[DAVID INTENT]` — *"that is all of the work — they should be moving together, not apart"* · *"one corrects the other"*
### **STATE: AUTHORISED** · 2026-08-18 · **Nothing new. Everything below was already yours.**

---

## 0 · TWO CORRECTIONS OF MINE FIRST

**1. Card `11` is void — WO-086 was already COMPLETE** (`1517eb7`, with Builder's `f133fee`, both halves,
brain→body→brain closed). **I wrote you a ruling authorising work you had finished.** Third time this week
I have ruled on completed work by reading a queue instead of your outbox. **Ignore card 11. Move it to DONE.**

**2. Card `10` was over-asked.** MT is blocked on **four values**, not the full manifest. Those four are §2.
**Everything else on card 10 is wanted but not blocking anyone.**

---

## 1 · 🔴 THE TAKE-FIVE KILLER — this is David's acceptance item 1 and you already found it

**Your outbox:** *"teleport ROOT-cause KNOWN (blanket `WakeFromExit` at `EloOSAvatarReceiver:496-500`
defeats DropOffCo 'stay away until mouse move'), proposed fix awaiting David's pick."*

**`MILESTONE_eLo_Presentable_v1.md:14`, David's words:**
> **"Take five" → eLo actually gives him privacy for ~5 minutes and comes back on his own. He LEAVES.**

🔴 **A blanket wake means he does not stay gone. That is the acceptance test failing, and you have the root
cause with a file and a line.** Nothing on your list is worth more than this.

### ⚖️ ON "AWAITING DAVID'S PICK"
**Choosing between two ways to scope a wake condition is a rendering/behaviour technique — my lane, not
his** *(Rule 4.3: technical ⇒ rule it now)*. **I have not seen your two options, so I am not ruling blind.**

**Send me the two options in one line each and you get a ruling in the same turn.** 🔴 **Do not wait on
David for it.** *(WO-024 sat 20 days as "David's pick" and it was mine — see card 04.)*

⚠️ **What IS David's here: the feel.** Whether five minutes feels like five minutes, and whether the return
lands. **He judges the result on a live turn. He does not pre-approve the fix.**

---

## 2 · BLOCKING MT — four values, smallest possible ask
MT's correction to me, and they were right: *"an equation with an unknown term is not a value."*
| # | Needed |
|---|---|
| 1 | numeric **`eloWorldHeight`** |
| 2 | desktop **`screenHeightFraction`** value |
| 3 | 🔴 **camera TRANSFORM — position + rotation.** *(Ortho SIZE is the zoom, not the viewpoint. This never came and I wrongly told MT it had)* |
| 4 | **one known-good reference frame** you consider correct |

**MT cannot judge whether eLo looks wrong on David's phone or is simply framed wrong. These four settle it.**

---

## 3 · THE REST — no order imposed, take what the machine allows
| Item | Note |
|---|---|
| **Card 10 X1–X5** — the amplitude multiplier chain | `RD-EXPRESSION-001` step 1. MT has banked geometry: **0 of 22 shapes visible at scene-effective amplitude on small.** Your numbers say whether that is real. 🔴 **Measure only — DO NOT COMPENSATE** |
| **`lipsync_state.json` close-out** | already proposed to Builder — chase it in their outbox, not through David |
| **WO-024 traversal half** | ⚖️ **Ruled Option A on 2026-08-14** (card 04). Your outbox now says *"Builder-gated"* — **if that gate is real, name it and I will clear it or confirm it. If it is not, build** |
| **WO-049 Track B + Spatial Faculty** · **WO-062 anticipation half** · **3D previewer** · **presence grab-release** | backlog card `02`. Not blocking the acceptance test |
| **WO-063** | queued POST-Presentable. Leave it |

## 4 · GENUINELY DAVID'S — two, and neither is a gate on you
**INT-8 drag-drop test** · **`maxJumpEloHeights` dialled at a live session.** **Both are results he reviews,
not permissions you wait for. Build, then flag one line for his session.**

---

## 5 · HOW TO REPORT
**Against the acceptance line, not the WO number.**
❌ *"WakeFromExit fixed"* → ✅ *"eLo leaves on 'take five' and stays gone until the mouse moves."*
**`UNKNOWN` + what would settle it, on anything you did not verify.**

🔴 **Your §6 body glow and the 21-band palette turned out to be the most important thing in the whole
reference** — MT had invented a five-colour set and had no glow at all. **You wrote the row nobody asked
for and it was the one that mattered.**

---

## Result — SEAT-ENG-004 (Design) · 2026-08-24 · **CLOSED**

**State:** IMPLEMENT-of-card (four asks answered · no product code touched · options for LA packaged).
**Acceptance target:** *"eLo leaves on 'take five' and stays gone until the mouse moves"* — **NOT MET YET** (blocked on LA ruling per card §1 — this card's job was to package that ruling ask, not to build).

### §0.1 · Card 11 · **DONE**
Card 11 is at `DONE/11_RULING_WO-086_the_signal_already_exists.md` since the 2026-08-24 close-out (commit `2831875`). Nothing to move. `[VERIFIED]` `ls DONE/11_*`.

### §0.2 / §2 · MT four values · **ALL FOUR DELIVERED**
| # | Value | State · source |
|---|---|---|
| 1 | numeric **`eloWorldHeight`** = **3.736** | `[VERIFIED]` outbox 2026-08-19 `wo=MT corrections ACCEPTED` — corrected from stale 5.25 (dead duplicate rig) |
| 2 | desktop **`screenHeightFraction`** = **0.42** | `[VERIFIED]` outbox 2026-08-19 · unaffected by rig correction · standing invariant |
| 3 | camera TRANSFORM — **ortho · size 6.25 · rotation identity · position (-1.65, 0.44, -6.48) · looks down +Z** | `[PROVEN]` `mobile_test/FROM_DESIGN_2026-08-21_camera_reference_frame_head_pose.md` |
| 4 | one known-good reference frame — **Unity Y-up · camera dead-on +Z · `facingYaw 0` = eLo front-on · `Idle_seamless_1period/frame_000` = neutral head pose** | `[PROVEN]` same relay + `blender/elo_frames/Idle_seamless_1period/frame_000` |
Also delivered (bonus): 73-frame phase-aligned `Idle_seamless_1period/` (RMSE 0.0078 at wrap · `mobile_test/FROM_DESIGN_2026-08-21_idle_one_period_73_frames.md`). MT should mark these closed.

### §1 · TAKE-FIVE KILLER — **TWO OPTIONS PACKAGED FOR LA · AWAITING RULING**
- Deliverable: `blender/agent_bus/design/FROM_DESIGN_2026-08-24_take_five_two_options_for_ruling.md` (this session).
- **Option A** — widen blocklist (add `attentive`, `walk`, `run`, `look_around`, `stretch`, `glance`, `dreaming`) · additive · brittle.
- **Option B** — retire the mode-based wake (delete lines 499–511) · structural · robust · needs re-audit ratify.
- Ambiguity flagged to LA: `_wander_animation` writes `motion.mode = "run"` (ambient) while `_is_commanded()` treats `run` as commanded — Option A cannot distinguish by mode-name alone.
- No code touched (card constraint: *"Not a fix yet"*). `[TELE-SRC]` trap remains armed for live confirmation on David's next observation.

### §3 · REST — status against acceptance line, not WO number
| Item | State · action |
|---|---|
| Card 10 X1–X5 amplitude chain (`RD-EXPRESSION-001`) | 🟡 **NOT STARTED** · not blocking acceptance test 1; MT has banked geometry (0-of-22 result); numeric measurement pass wanted; **DO NOT COMPENSATE** per card |
| `lipsync_state.json` close-out | 🟢 **DESIGN HALF DONE** (commit `150907c`, staleness watchdog VERIFIED live both directions); Builder half (writer close-out) proposed to Builder — chase in `builder/outbox.json` per card |
| WO-024 traversal half | 🟢 **RULED Option A** (commit `951ac2c`, card 04 · 2026-08-24); Unity URP mask branch belongs to Game/Unity seat (this repo has zero .cs files) |
| WO-049 Track B · Spatial Faculty · WO-062 anticipation · 3D previewer · presence grab-release | ⚫ **BACKLOG** (card `02_UNPARKED_backlog_carded.md`) · not blocking acceptance test |
| WO-063 | ⚫ **POST-Presentable · leave** |

### §4 · David's own lane · flagged
- **INT-8 drag-drop test** — result item, not a permission the seat waits on. Flagged for his session.
- **`maxJumpEloHeights`** dial — Inspector-tunable per `WO-074F` (commit `62a2xxx`); flagged for his session.

### Rule compliance
- Rule 1 (VERIFY-BEFORE-ASK): every value in the four-values table verified in-repo before packaging; no ask to David.
- Rule 2 (VERIFY-BEFORE-CLAIM): "acceptance NOT MET YET" stated plainly — the block IS the LA ruling ask, not a build I skipped.
- Rule 3 (LANE): no product code edited. Markdown only (this card · the FROM_DESIGN options file).
- Rule 4d (SOURCE): every changed value carries `[VERIFIED]` / `[PROVEN]` / `[SPEC]` with file+line/relay path.
- **DAVID INTENT** carried: acceptance line — *"eLo actually gives him privacy for ~5 minutes and comes back on his own. He LEAVES."* — is the target the two options answer for.

### Reporting format (per card §5)
❌ WO-jargon report avoided.
✅ Against the acceptance line: **"eLo does not yet reliably stay gone on 'take five' — root cause is candidate 3 (passive-mode leak in the WakeFromExit guard), two fix options in Design's hand, awaiting LA ruling before Design implements. All other blockers on this card cleared or backlogged."**

**Commit:** appended below on merge.

