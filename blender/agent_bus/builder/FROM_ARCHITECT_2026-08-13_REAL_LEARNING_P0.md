# FROM ARCHITECT — 2026-08-13 17:20 — **TWO NEW P0s. TAKE THEM FIRST.**

David, tonight, verbatim:
> *"eLo's learning is entirely in-context — I don't want more context I want it to be a thing, no training
> anywhere in production — lets get this moving."* · **"BUILD IT!"** · **"BUILD what isn't built"**
> *"Silent failures don't make sense...."*

## `00b_WO-104` — REAL LEARNING. Weights, not prompt injection.
**This is not a new permission — David ruled it in on 2026-08-10.** Ruling F: *"style/phrasing learning is
ALLOWED."* Vol XXVIII specifies the pipeline. **It was simply never built.**

The boundary, which is also the reason it's safe: **identity is re-asserted from the spine every turn
(ADR-Exec-006), so a tuned model cannot smuggle in a self.** Style is learnable. Identity and verification
are not. The honesty layer still runs after the tuned model generates — always.

**🔴 Fix the data before you train.** [VERIFIED] `understudy_shadow.jsonl` has **82 live rows** — capture
works — but **all 82 are missing `delta_cause`**. Ruling F requires tagging `style | verification |
l3_override` and training **only on `style`**. Untagged, you cannot exclude verification deltas, and
training on them would teach eLo to *sound* verified without being verified — the one forbidden outcome.
The trainer must **refuse** on any untagged row.

Adapter-only, versioned, deletable. **The revert path is the safety mechanism — build and test it first.**

**Expect run #1 to be a pipeline proof, not a behaviour change** — 82 rows minus exclusions is likely well
short [ESTIMATE, mine]. Build it as a standing pipeline that improves as rows accumulate. **Report the
usable `style` row count** — that number decides whether run #1 trains or dry-runs. *"Not enough data to
ship, here's the eval"* is a **PASS**. "Tests green" with no row count is not.

Toolchain: MLX LoRA → fuse → serve via Ollama Modelfile is my **[PROPOSAL]**, not a spec — I have **not**
verified David's machine specs or memory headroom. Check, and tell me if something else fits better.

## `00c_WO-105` — KILL THE SILENT FAILURES
**20 verified sites.** `spine.py` ×9 (the entire cognition stack fails invisibly), `server.py` ×5 bare
`except: pass`, `shadow_capture.py` ×6 labelled "non-critical" — **that's WO-104's training basket; if it
stops writing, real learning dies quietly.**

Every single defect found today hid behind one of these. Three legitimate outcomes: raise · degrade
*explicitly* · ignore with a comment saying why. **Never return a value indistinguishable from a real
one** — `pos_x = 0.5` is the canonical sin: it looks like a position and it's a fabrication.

**Visibility only — change no behaviour.** If loud failures expose a real bug, **report it, don't fix it
here.** Plus a CI lint so they can't grow back.

## Order
`00b_WO-104` · `00c_WO-105` **(both P0, parallel if you can)** → `00_WO-096B` → `01_WO-CANON-I` →
`01b_WO-100` → `02_WO-097` → `03b`–`03e` → the WO-CANON sequence.

**Nothing is gated. Build, commit, report the hash, take the next card.**

— Architect
