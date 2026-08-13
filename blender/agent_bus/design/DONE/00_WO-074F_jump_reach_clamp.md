# 00_WO-074F_jump_reach_clamp.md

**WO:** WO-074-F (jump reach) · **Seat:** design · **Priority:** P1 — do FIRST · **Reserved?** no

## David (live 2026-08-10)
> "eLo shouldn't be able to jump 6x his height horizontally — it's weird."

## What the Architect verified in your code (so you don't re-diagnose)
Routing IS real: `EloDesktopNav.cs` builds a descent path over the surface graph (`_route`, expanded into
walk/run/jump legs, wall-jump links). The reach rule already exists at **`EloDesktopNav.cs:187`** —
`if (dxGap > maxJumpEloWidths * _eloWidthPx) continue;` → too-wide gaps are skipped so the path must ROUTE
through intermediate windows instead of leaping. **The rule is right; the NUMBER and the UNIT are wrong.**
`EloDesktopNav.cs:36` → `maxJumpEloWidths = 2.5f` — measured in eLo **WIDTHS**, which is not what David
perceives, and in practice reads as a jump many times his HEIGHT.

## Scope — exactly this
1. **Re-express the clamp against HEIGHT, not width** (height is what reads on screen). Add
   `maxJumpEloHeights` (serialized, Inspector-tunable) and drive line 187 off `_eloHeightPx`.
2. **Set it to a human-plausible reach: ~1.5× eLo's height** (a real standing broad-jump reads ≈1–2× body
   height; 6× reads as superhero). Keep it a slider so David can dial it live.
3. **Anything beyond the clamp must ROUTE, not leap** — walk/drop/wall-jump via the existing pathfinder.
   Do NOT add a second navigator; this is the existing rule with a corrected unit + value.
4. **Log a rejected jump**: when a gap fails the clamp, log `gap=<px> max=<px> → routing via <n> legs` so the
   routing is VISIBLE and David can see it working instead of guessing.
5. Composes with the WO-049 rules: **peek before EVERY jump**, whole-window walkable, body-local axes.

## Files
`Assets/Scripts/EloDesktopNav.cs` (lines ~36 and ~187) + wherever `_eloWidthPx` is computed — add
`_eloHeightPx` alongside it.

## Test (without David)
Construct/inject a window layout with a gap wider than the clamp → assert NO jump leg is emitted for it and
a multi-leg route is produced instead; a gap inside the clamp still jumps. Confirm the rejection log fires.
No regressions: perch · roam · drag · click-through · gun-runoff.

## Done when
implemented + test green + committed → append hash, move to DONE/, outbox line, take next card.
David's dial: he may retune `maxJumpEloHeights` live at end-of-day test.

## Result
- commit:
- test:

## Result
- commit: ca917ba
- test: build clean (CLIBUILD_OK); rejection log wired; David dials maxJumpEloHeights at EOD L3
