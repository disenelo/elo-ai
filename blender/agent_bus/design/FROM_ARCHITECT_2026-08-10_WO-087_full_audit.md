# ▶ DESIGNER — WO-087: FULL local-driver audit (brain > body > brain sweep) — read-only, no greenlight needed

David wants the deeper cut: your first audit (WO-086 step 3) covered the drivers near mouse-idle — he's sure
there's a lot more in the app deciding things locally that should route back to the brain. Do a **complete
sweep of the DesktopBuddy app.**

## The principle to audit against (David 2026-08-10)
**brain > body > brain, closed loop:** the brain DECIDES and drives (DOWN); the body only SENSES, ACTS, and
reports state UP; the brain reads it back and decides again. **The body never decides.** Every body perception
(mouse-idle · occlusion/behind-window · perch/surface · user-active · file-drop · *and anything you find*)
relays UP; **no local script may choose a behaviour.**

## Deliverable — a classified inventory of EVERY component
Go through the app's scripts/components and list each that touches behaviour, classifying it:
- **ROUTE-THROUGH-BRAIN** — it makes a behavioural/cognitive/valence DECISION locally (chooses what eLo does
  or feels). These are the backlog. For each: script/file + one line on what it decides + why it belongs to the brain.
- **KEEP AS REFLEX** — pure sub-perceptual aliveness with NO intent/valence (blink, micro-jitter, idle-breathing
  wobble, gaze-follow that already yields to brain cues). Justify why it's safe to stay local.
- **COMPLIANT EMITTER / EXECUTOR** — already correct (senses→publishes UP, or obeys the DOWN channel).
- **NEEDS REVIEW** — you're unsure (like EloEmojiReact) — flag for a closer read.

Look beyond animation: perception/occlusion, autonomous movement/roam, expression/emotion selection, ambient
VFX triggers, any timers or chance-based behaviour, any script writing `animator.speed`/state directly, any
"if (condition) do X" that picks an eLo behaviour without relaying up.

## Rules
- **READ-ONLY.** This is an inventory — do NOT change behaviour or touch the sensitive avatar file. No greenlight
  needed for the audit itself; each "route-through-brain" item becomes its own gated WO afterward (like WO-086).
- Deliver as an appended outbox relay (append, don't overwrite — per the outbox protocol). The Architect
  reconciles it into a prioritised "push-to-brain" backlog for David.

Goal: David gets the FULL picture of how much the body is deciding on its own, so we can route it to the brain
deliberately — not discover it one live-test annoyance at a time.
