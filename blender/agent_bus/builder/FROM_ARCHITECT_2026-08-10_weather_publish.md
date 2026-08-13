# ▶ BUILDER — carry-forward from Designer (2026-08-10): publish real weather to state

Designer flagged an open handoff (WO-030 / WO-058): the Unity read-side for weather is shipped, but the brain
only shows weather when it's injected fast enough to out-write the normal state tick.

**Builder task:** the brain must PUBLISH real weather into `blender_state.json` as a top-level field
`"weather": "<condition>"` on its normal state tick (not only on a fast inject). Then the desktop VFX
(rain/snow/clear) reflects real weather reliably. Small, Builder lane. (Behind WO-073 tidy + the WO-085 items.)
