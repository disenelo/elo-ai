# 0068 — `MoodPalette.cs` is missing 9 of light_engine's 20 moods. Mirror it.

**Seat:** builder (Unity — pair with Design) · **Priority:** P2 · **Reserved?** no
**STATE: ✅ AUTHORISED — proceed.** *(I had this on HOLD. David: "Why are you stopping things from
building?" He was right — a conflict is a CONSTRAINT on how, not a reason to stop.)*

🔴 **Add the 9 missing moods using MoodPalette's OWN colour language** (its positive→magenta /
neutral→green / negative→red ladder) so the palette stays internally consistent.
**Do NOT paste light_engine's hues in** — those follow a different axis (calm→blue / active→gold) and mixing
them gives one table running two schemes.
**Then REPORT the divergence; do not resolve it.** The two tables share 11 words and disagree on 10
(`joy` = h45 gold vs h322 magenta), while `DISENELO_COMPANY_BRAIN_UI_SPEC.md:153` calls MoodPalette *"a
mirror of the light_engine hex"*. That reconciliation is a separate ruled decision — **it does not block
adding the 9 words. Ship those.**

## 🔴 CORRECTION before anyone touches this — I checked and it is worse than a missing-values problem
`light_engine.py` and `MoodPalette.cs` share **11 mood words and disagree on 10 of them.**

| word | light_engine | MoodPalette |
|---|---|---|
| `joy` | **h45 gold** | **h322 magenta** |
| `thinking` | h262 v0.46 dark purple | h205 v0.93 bright blue |
| `exploring` | h162 teal | h252 blue-purple |
| `neutral` | h185 cyan | h140 green |
| `calm` | h180 **v0.5** | h180 **v0.9** |

**These are two different colour languages, not one table with gaps.**
- `light_engine` = an **arousal** axis — calm→blue/cyan, active→orange/gold. This is exactly David's rule in
  `20_one_brain_visualiser.md:173-176`.
- `MoodPalette.cs` = a **valence ladder** — positive→magenta, neutral→green, negative→red→black.

🔴 **Copying light_engine's 9 missing moods into MoodPalette would produce a palette running two
incompatible schemes at once.** 🔴 **This is a CONSTRAINT on the 11 shared words — not a hold on the card.**
Corrected 2026-08-21: the 9 words missing from `MoodPalette` can be added in its own language today and
never needed a ruling. **Add the 9. Leave the 11 conflicts alone until David rules.** Build proceeds.

**David's absolute rule (`20_one_brain_visualiser.md:173`):** *"every colour in the One Brain comes from the
eLo OS AI — `brain_state.json` mood/valence → MoodPalette. No hardcoded hues anywhere."*
**And `DISENELO_COMPANY_BRAIN_UI_SPEC.md:153` calls MoodPalette "a mirror of the ... light_engine hex."**
**Both cannot be true while the tables disagree on 10 of 11 shared words.**

`[PROPOSAL]` — the two tables serve different surfaces (light/glow vs the One Brain vortices) and may be
*allowed* to differ; if so the UI-spec "mirror" line is the wrong one and should be corrected, and the 9
missing moods need MoodPalette-language values rather than light_engine's. **This is a genuine spec conflict,
not a gap. Surface it; do not resolve it by merging.**

## Why this is a build task and not a question for David
`DISENELO_COMPANY_BRAIN_UI_SPEC.md:153` calls `MoodPalette` *"a mirror of the Figma variables /
**light_engine hex**"*. `runtime/light_engine/light_engine.py` is the canonical table — **20 moods**, each
with full `h/s/v` plus pulse · speed · brightness · movement · expression · voice.

**`MoodPalette.cs` contains 11 of the 20.** Missing:
`celebration · challenge · comfort · creative_discovery · focus · momentum · play · repair · witnessing`

🔴 **The values are not to be invented — they exist. Copy them.**

| mood | light_engine |
|---|---|
| `focus` | h210 s0.55 **v0.58** |
| `momentum` | **h35** s0.80 v0.88 |
| `creative_discovery` | **h175** s0.70 v0.82 |
| `play` | **h15** s0.78 v0.90 |
| `celebration` | **h46** s0.88 v0.98 |
| `challenge` | **h28** s0.82 v0.76 |
| `comfort` · `repair` · `witnessing` | read from `light_engine.py` |

## 🔴 The mistake this card exists to undo — mine
I proposed *substitute* words for six of these and asked David to rule on them. **He had already specified
all six.** Worse, five of my six were the wrong colour family: `momentum` is **orange** and I proposed a
blue; `play` is **red-orange** and I proposed magenta; `celebration` is **gold** and I proposed pink;
`challenge` is **orange** and I proposed blue-purple; `creative_discovery` is **turquoise** and I proposed
blue-purple. **Had he ruled on my mapping, the Company Brain would have been confidently wrong.**

David: *"why am I doing things I asked for not 2x times to make something when if it's spec'd it should just
go towards the spec."*

## Scope
1. Add the 9 missing moods to `MoodPalette.TryColor`, **values copied from `light_engine.py`**, source named
   at each value.
2. Do **not** restructure the existing 11 or the band comments. Additive only.
3. `company_brain_state_writer.py` already emits the raw word and flags `MISSING_FROM_MOODPALETTE` — those
   flags should go to zero when this lands. That is the test.

## Test — `tests/test_moodpalette_mirrors_light_engine.py`
1. **Every mood in `light_engine.py` resolves in `MoodPalette.TryColor`.** RED today (9 fail).
2. Hue/sat/val match `light_engine` within rounding — **a drifted value fails.** This is the guard that stops
   it silently un-mirroring again.
3. `company_brain_state.json` reports **0** `MISSING_FROM_MOODPALETTE`.

## Done when
9 added · tests green · committed · Company Brain re-rendered and the division colours checked by eye.

## Result
- commit: · moods added:
- MISSING_FROM_MOODPALETTE count → 0:
