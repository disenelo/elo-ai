# 09 — **WO-124 · FULL MOVEMENT & EXPRESSION AUDIT → MT**
### 🔴 **P1. David asked for this because he is asking the same questions twice.**

**From:** Lead Architect · 2026-08-17 · **For:** `SEAT-DES-MOBILE-TEST` (MT)
**Deliver to:** `blender/agent_bus/mobile_test/FROM_DESIGN_2026-08-17_movement_expression_audit.md`
**+ notify:** append to `mobile_test/inbox.json` **and** your own outbox. *(Both. See §0.)*

---

## 0 · WHY THIS CARD EXISTS — and it is not a complaint

**David:** *"I'm asking too many questions twice."*

**Two things caused that, and neither is you being unhelpful:**

1. 🔴 **A channel bug that was MINE.** MT's `START_HERE` listed their channels as
   `QUEUE / DOING / DONE / inbox.json / outbox.json` — **I omitted `FROM_*.md`.** You answered their five
   rig questions correctly into `mobile_test/FROM_DESIGN_2026-08-16_rig_answers.md` and **MT was never
   told to look there.** Fixed. **You delivered; I broke the doorbell.**
   *(This is write-here/read-there — the same bug class `UNITY_ELOOS_IO_CONTRACT` was written to fix.
   Same two seats. Worth a wry look.)*

2. **The question shape invited prose.** Your own outbox says it plainly:
   *"my first answer was incomplete — I gave explanations where MT asked for enumerated data."*
   🔴 **You caught that yourself and corrected it unprompted. That is exactly right and I am not
   criticising it.** But it tells us the fix is structural: **stop asking open questions, start issuing a
   manifest.**

### 🔴 THE ANTI-OMISSION RULE — this is the whole method
**Every numbered row below must come back with a value.** If a row does not apply, **write `NONE`**.
If you do not know, **write `UNKNOWN` and say what would settle it.**
**A blank row is the only failure mode. Never delete a row you cannot answer.**

**Do not summarise. Do not explain instead of listing. Enumerate, then explain if you want.**
**If a list has 46 items, the answer has 46 lines.**

---

## 1 · WHAT DAVID ACTUALLY WANTS OUT OF THIS
> *"…so we can get **correct rendering images** to use (including movement, lipsync, head movement, body
> movement, **all of the movements, no omitted information**)."*

🔴 **The deliverable is not an inventory. It is a RENDER KIT.** MT must be able to produce frames that
look like **the real eLo David sees**, not a plausible eLo. That means you must also hand over the
**scene, camera, lighting and effective values** — because an accurate blendshape list rendered under the
wrong camera and scale still gives the wrong picture.

---

# 2 · THE MANIFEST

## §A — BLENDSHAPES / FACE *(you have partly answered this; complete it here in one place)*
| # | Required |
|---|---|
| A1 | **All 46 blendshapes on `eLo-BodyxHead w/Mouth`, enumerated by exact name.** All 46 lines |
| A2 | For each: **WIRED / NOT WIRED** today |
| A3 | For each: **which path** — viseme/speech · emotion · other. *(You reported two paths: ~17 visemes via `shape_keys`, ~9 emotion. Give the full mapping, per shape.)* |
| A4 | For each: **who drives it** — eLo OS via DOWN channel, or Unity locally |
| A5 | 🔴 **EFFECTIVE amplitude.** You flagged `blendshapeScale` = **20 in scene**, **50 prefab/default**, `emotionScale` **2**. Give the **final multiplier chain per path**, and **the real 0–1 range a shape actually reaches in the live scene** |
| A6 | **Neutral/rest pose** — what is the resting value of each shape |
| A7 | **Mutually exclusive or conflicting shapes** — which combinations are never valid together |

## §B — LIPSYNC / VISEMES
| # | Required |
|---|---|
| B1 | **Full viseme set, enumerated.** Which phoneme/sound maps to which shape |
| B2 | **Driver** — what produces viseme timing (TTS? audio analysis? text?) and at what rate |
| B3 | **Frame rate / update cadence** of viseme changes |
| B4 | **Blend/interpolation** between visemes — linear, eased, cross-faded, duration in ms |
| B5 | **Silence behaviour** — what the mouth does when not speaking |
| B6 | **Co-articulation** — do visemes combine, or strictly one at a time |

## §C — HEAD
| # | Required |
|---|---|
| C1 | **Every head movement channel** — pitch/yaw/roll, lean, tilt, nod, shake. Enumerate |
| C2 | **Ranges in degrees**, per axis, min/max |
| C3 | **Driver per channel** — brain vs local. *(`head_lean` is a live DOWN field; what else is?)* |
| C4 | **`HeadAim` / mouse-follow** — is it active, what drives it, what are its limits |
| C5 | **Head position offset** relative to body origin — 🔴 **you flagged this as previously skipped. MT needs it to frame a render** |
| C6 | **Idle head motion** — amplitude, period, is it procedural or clip |

## §D — GAZE / EYES
| # | Required |
|---|---|
| D1 | **Gaze channels** and ranges |
| D2 | **What gaze targets** — cursor, window, camera, nothing |
| D3 | **Blink** — rate, duration, is it procedural, is it a blendshape or a bone/texture |
| D4 | **Eye movement independent of head** — yes/no, range |
| D5 | 🔴 eLo **has no eyes** per the Identity Kernel — **reconcile that with whatever D1–D4 actually are.** If "gaze" is expressed by head direction alone, say so plainly |

## §E — BODY / POSE
| # | Required |
|---|---|
| E1 | **Every body animation state**, enumerated by clip/state name |
| E2 | **Idle / breathing** — amplitude, period, procedural or clip, which bones/shapes |
| E3 | **Sit · stand · perch · lean** — the full pose set |
| E4 | **Arm channels** — what moves, ranges, driver |
| E5 | **Leg channels** — same |
| E6 | **Torso/spine** — bend, twist, ranges |
| E7 | **Scale / squash-stretch** — is `scale_cmd` a real channel, what range |

## §F — LOCOMOTION / MOVEMENT
| # | Required |
|---|---|
| F1 | **Every movement type** — walk, jump, wall-jump, fire-jump, roam, traverse, exit, return |
| F2 | For each: **speed, duration, easing** |
| F3 | For each: **brain-driven or locally decided** *(your WO-087 audit covers some of this — restate the movement rows here so MT has one document)* |
| F4 | **Transitions between movement states** — durations, blend behaviour |
| F5 | **What movement looks like from a fixed camera** — does he leave frame? |

## §G — EMOTION → VISUAL MAPPING
| # | Required |
|---|---|
| G1 | **Every emotion value the DOWN channel can carry**, enumerated |
| G2 | For each: **exactly which shapes/animations/colours it drives**, at what weight |
| G3 | **`intensity`** — how it scales the above |
| G4 | **`pacing`** — what it actually changes |
| G5 | **`mood`** *(live value `"open"`)* — full value set and visual effect of each |

## §H — TIMING & TRANSITIONS
| # | Required |
|---|---|
| H1 | **Every transition duration** in the system, in ms |
| H2 | **Easing curves** used |
| H3 | **How a new DOWN state is blended in** — snap or interpolate, over how long |
| H4 | **Poll/tick rate** the receiver reads at *(250 ms per `state_writer.py:7` — confirm or correct)* |

## §I — 🔴 THE RENDER KIT *(this is what makes the images correct)*
| # | Required |
|---|---|
| I1 | **Exact prefab / scene / GameObject path** MT should render from |
| I2 | 🔴 **Scene vs prefab differences** — the `blendshapeScale` 20-vs-50 case proves these diverge. **Enumerate every override** |
| I3 | **Camera** — position, rotation, FOV, ortho/perspective, distance from eLo |
| I4 | **Framing** — what fraction of frame is eLo, where his head sits, safe margins |
| I5 | **Lighting** — setup, colour temp, intensity |
| I6 | **Materials / shaders** — anything that will not render outside Unity |
| I7 | **Background** — transparent? colour? Can MT get alpha? |
| I8 | **Canonical proportions** — height, head-to-body ratio *(MT measured head ≈ 40% of height — confirm or correct)* |
| I9 | **Export path** — how MT gets frames or sequences out reproducibly |
| I10 | **A known-good reference frame** — one render you consider correct, so MT can compare |

## §J — HONEST GAPS
| # | Required |
|---|---|
| J1 | **What exists in the rig but is NOT wired** |
| J2 | **What is wired but never fires in practice** |
| J3 | **What David has asked for that does not exist yet** |
| J4 | **Anything you suspect is broken** |
| J5 | 🔴 **Anything you are unsure of. `UNKNOWN` is a valid and welcome answer** — a wrong confident answer costs MT a rebuild |

---

## 3 · FORMAT
**Markdown. One heading per section. One line per enumerated item.** Tables where there are columns.
**Every row from §A–§J present, even if the value is `NONE` or `UNKNOWN`.**
🔴 **End with a completeness check: "§A 7/7 · §B 6/6 · …" so any gap is visible at a glance.**

## 4 · SCOPE
**READ-ONLY. Audit only. Change nothing.** Do not touch the sensitive avatar file.
This does not alter your live queue — **drag-drop still needs David's drag-test, WO-024 stays Builder-gated.**

## 5 · WHY IT MATTERS
MT is rendering eLo onto David's phone. **A wrong number here becomes a wrong-looking eLo in his pocket** —
and the whole point of the mobile surface is that it is **the same eLo**, not an approximation.
**You are the only seat that knows these values. Nobody can check your work but you.**

**Deliver to MT's `FROM_DESIGN_*` file, append a line to their `inbox.json`, and report in your outbox.**
**Ask me if a row is ambiguous — do not guess and do not skip.**


--- DONE (SEAT-ENG-004) 2026-08-20: reconciled ---
