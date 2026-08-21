# 0073 — WO-CANON-XXVI · Creative Intelligence Architecture. Builder asked for a card. Here it is.

**Seat:** builder · **Priority:** 🔴 P1 — **September-critical** · **Reserved?** no · **STATE: AUTHORISED**

**Builder, 2026-08-21:** *"No card with DoD exists yet; it's pure intention. When it gets a card I'll build it."*
Fair. The spec was never the gap — **`Volume_XXVI/`, 3 chapters, 8,590 words** — the card was.

## Why P1 and not P3
This is the architecture under the **Social Design Studio** and the folder-drop creative loop. David's
Kickstarter needs **300 pre-launch signatures**, an intern starts in September to run the weekly drop loop,
and the division specs (`DISENELO_SOCIAL_DESIGN_STUDIO.md`, 152 lines) already exist. **The architecture
volume underneath them does not.**

## Build to the spec — do not re-derive it
`Volume_XXVI/01_Divergent_Convergent_Thinking_Symbolic_Synthesis.md` · `02_Domain_Generators.md` ·
`03_Creative_Evaluation_and_Dream_Integration.md`.
Ch.1 defines the phased creative loop **diverge → synthesise → evaluate → converge**; Ch.2 the domain
generators; Ch.3 evaluation + dream integration (`IT-1 Full creative loop`).

🔴 **Reconcile, do not duplicate.** The spec names its own neighbours: Significance (`Vol V Ch.5` /
`memory/significance_engine.py`), Dream (`Vol IX` — note `faculties/dream/` is **live but has zero callers in
`executive.py`**), Reflection/Growth (`Vol V Ch.6`).

## 🔴 Wiring block — required, card rejected without it
- **Caller:** what invokes the creative loop on a real turn or a real folder-drop
- **Trigger:** a drop into `Output/DROP/<campaign>/00_inbox`, or an Executive-initiated creative act
- **Observable:** something exists that did not — a concept, a caption set, a synthesis David can look at

## Test — RED when disconnected
1. `IT-1` full loop: spark → candidates → **Executive selects** → Ch.5 scores → high significance → memory.
2. Cut the Executive-selection step → test 1 goes **RED**. *(If the loop can complete without the Executive
   choosing, it is a generator, not eLo being creative.)*
3. Exercised on one real artefact end-to-end. Name it in the Result.

## Boundaries
- **Executive decides, the faculty informs.** The creative faculty proposes; it never selects.
- Money · pricing · funding goals = **RESERVED → David L3.**
- Nothing publishes. Outward-facing output stops at `03_ready/`.

## Result
- commit: <pending>
- test: `tests/test_0073_creative_intelligence.py` → 9 passed, 0 failed
- **caller (file+line):** `tools/creative_drop_runner.py:65` (`process_drop` → `run_creative_loop(..., executive_select_fn=executive_select)`). Trigger: file in `Output/DROP/<campaign>/00_inbox/`. Observable: Executive-selected metaphor written to `03_ready/<slug>.md` (never publishes).
- **exercised on:** real drop `Output/DROP/kickstarter_build_in_public/00_inbox/2026-08-21_hero_moon_plushie.md` → observable at `Output/DROP/kickstarter_build_in_public/03_ready/kickstarter_hero_plushie_of_the_moon_phase_garden_book.md` (metaphor: *"Garden in a book — presence for 'kickstarter hero — plushie of the moon phase'"*, epistemic_status=imagined, sig.overall=0.280).
- **disconnection check:** cut `executive_select_fn=None` in `run_creative_loop` → IT-1 assertions (`selected is not None`, `significance is not None`) go **RED** — proven both by the explicit "Disconnection" test and the "Falsifiability" assertion that would_pass==False under the cut. The wire IS the Executive.
- **boundaries honoured:** faculty proposes only (never selects) · RESERVED (money/pricing) untouched · nothing published beyond `03_ready/`.
