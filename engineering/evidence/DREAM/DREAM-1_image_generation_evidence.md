# DREAM-1 / WO-DREAM-ENGINE-001 PHASE 5a–5b — image generation

**Filed by:** Builder 2 · 2026-09-27
**Runtime:** `/Users/Disenelo/miniconda3/bin/python3` 3.13.13 · pytest 9.1.1

---

## DREAM-1 asks for three things

| Requirement | Before | After |
|---|---|---|
| Confirm `openai` installed | **MISSING** — every dream logged `No module named 'openai'` | **openai 3.19.2** installed into the miniconda env the live server runs |
| Surface the actual exception, not swallowed | Backends printed, but `generate()` collapsed all three to `"All image generation backends failed."` — the caller got no reason | `generate()` returns `errors[]` with the real per-backend reasons |
| `[dream] image generation failed: <reason>` — **never silent None** | `_generate_dream_image()` returned `None` with **no log at all** when `ok` was False | Every failure path logs the reason |

The third was the real defect and it was in the dream path, not the agent.
The agent was already printing; `dream_faculty` discarded the result and
returned `None` without a word.

---

## TWO MORE FOUND BY READING THE CODE

**1. Scene filenames collided.** `_output_path()` used a second-resolution
timestamp. A 14-scene dream generates well inside one second, so every scene
overwrote the last and a night's work would have left one file. Now the
dream pipeline names them `dream_<dream_id>_scene_<N>.png` per the WO, and
the unnamed path gets a uniqueness suffix.

**2. Preview.app would open once per scene.** `generate()` unconditionally
ran `open -a Preview`. A 14-scene dream at 3am would have opened 14 windows
on David's desktop. `preview` is now a parameter; the dream pipeline passes
False.

---

## COST — flagged, not blocked

One DALL-E 3 HD call per scene. A full five-cycle night is 14 scenes = 14
paid calls per dream. `DREAM_MAX_SCENE_IMAGES = 4` bounds that while still
clearing the WO's "minimum 2 per full sleep session". Scenes are taken
highest-intensity first, so a capped run keeps the most transformed images
rather than the first few grounded ones.

**[BUILDER DEFAULT — raise it when you want full nights.]**

Scene generation is gated on the live-run flag, the same gate as state
publishing and the lexicon, so **a test run can never spend money**. Pinned
by `test_a_test_run_never_spends_money`.

---

## WIRE-CUT PROOF

Cut: restore the silent `None` in the dream path and the generic error
string in the agent.

```
WIRE CUT: silent None restored + generic error restored
FAILED test_generate_returns_per_backend_reasons_not_a_generic_string
FAILED test_a_failed_scene_is_logged_with_its_reason_not_silent
FAILED test_legacy_single_image_path_also_logs_its_reason
3 failed, 12 passed
```

Restored:

```
15 passed in 0.62s
```

The three tests that guard DREAM-1 are the three that fail.

---

## REAL RUN — every backend down, no paid call made

```
openai installed: 3.19.2

generate() on total failure:
{
  "ok": false,
  "error": "DALL-E 3: simulated backend failure; DALL-E 2: simulated backend failure; SD local: simulated backend failure",
  "errors": [
    "DALL-E 3: simulated backend failure",
    "DALL-E 2: simulated backend failure",
    "SD local: simulated backend failure"
  ]
}

generate_scene_images() with every backend down:
[dream] image generation failed: DALL-E 3: simulated backend failure; DALL-E 2: simulated backend failure; SD local: simulated backend failure
[dream] image generation failed: DALL-E 3: simulated backend failure; DALL-E 2: simulated backend failure; SD local: simulated backend failure
[
  {
    "ok": false,
    "scene": 1,
    "error": "DALL-E 3: simulated backend failure; DALL-E 2: simulated backend failure; SD local: simulated backend failure"
  },
  {
    "ok": false,
    "scene": 2,
    "error": "DALL-E 3: simulated backend failure; DALL-E 2: simulated backend failure; SD local: simulated backend failure"
  }
]

[dream] image generation failed: DALL-E 3: simulated backend failure; DALL-E 2: simulated backend failure; SD local: simulated backend failure
legacy _generate_dream_image(): None

DREAM_MAX_SCENE_IMAGES: 4
```

Before this change that same run produced `None` and printed nothing from
the dream path. Now every layer says why.

---

## NOT PROVEN

- **No image has actually been generated.** No paid call has been made from
  this seat — spending is David's call, and the live dream path is gated so
  it only fires on a real dream. The first real image arrives when a dream
  fires on the live server with `publish_phases=True`.
- **PHASE 5c (`tools/dream_fx.py`) not built** — the CompositionDesigner FX
  pipeline is next. PIL and numpy are present, so it is unblocked.
- **PHASE 6 (`layer_compositor.py`) not built** — depends on 5c.

## STATUS

`IMPLEMENTED → WIRED → TESTED`. Not LIVE VERIFIED. Not declaring PASS.
