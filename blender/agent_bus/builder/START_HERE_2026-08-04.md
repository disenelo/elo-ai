# → BUILDER (eLo OS) — DISPATCH  (refreshed 2026-08-07 EOD, after RUN 8)

> # 🔴🔴 NEXT PICKUP = WO-073. NOTHING ELSE FIRST. (David 2026-08-08)
> The suite is **83/83 green** — that's done. Do NOT spend another run on tests/cleanup/polish. The one thing
> between us and a real eLo is **WO-073**: eLo is still MUTE (pinned-Groq falls `Groq→Cerebras→Mock`, skipping
> Ollama). Fix: thread the Ollama tier into the pinned-Groq fallback → `Groq→Cerebras→Ollama→Mock`; set
> `ELO_OLLAMA_MODEL=llama3.1:8b` (David pulled it; router default `mistral` is wrong); diagnose the live Groq
> failure (backend_health + one real call → 429/auth/network). DoD: a Groq-down turn returns `ollama`, never
> `mock`. Ship the test, run your own round-trip, commit, outbox. Spec: `WO-073_Local_Brain_In_Pinned_Groq_Fallback.md`.
> Every other item below waits behind this. Green tests ≠ a talking eLo — WO-073 is what makes it talk.

**Contract: one WO per run → ship WITH a test that runs WITHOUT David → run your own live round-trip → outbox → read the board for next.**
Rule: autonomous and commanded are ONE capability. Gate per WO: your test → Chief Architect acceptance → David L3.

## ⚡ TONIGHT — mechanical, do FIRST (makes the L3 valid + starts the understudy)
1. **Activate the local understudy (Ollama).** `ollama list` → if `mistral` isn't pulled, either `ollama pull mistral`
   OR set `ELO_OLLAMA_MODEL` in `.env` to a model you DO have. (Router requests `mistral` by default on :11434;
   mismatch = it drops to the dumb mock.)
2. **Clean relaunch.** Kill :5050, relaunch the backend fresh so RUN 8 + WO-032b + WO-048 actually LOAD (the last
   L3 ran on a stale backend → mock). Confirm `backend_health` = `{backend:groq, degraded:false}` on a live turn;
   confirm a Groq-down turn now falls to `ollama` (real), not `mock`.
3. **Build WO-070 (shadow-capture) — passive, ~30 lines.** Zero-blocking `*`-subscriber logging eLo's runtime turns
   to a sibling of the existing learning substrate (`self_improvement/`/`growth_journal.jsonl`). Start it so data
   accrues overnight. Spec: `../../engineering/work_orders/WO-070_Understudy_Shadow_Capture.md`.

## ✅ DONE this run (RUN 8) — awaiting clean relaunch + David L3 retest
F1 press-parse (`228f021`) · F2 no-cancel (`95d674e`) · F3 github-leak (`eb8492e`) · F6 mirror-scrub (`1366516`) ·
WO-032b real brain (`a806f16`) · WO-048 company (`aa41d5c`) · WO-020 · WO-036b · WO-045b · WO-064-BP4/BP5 · WO-035b.
**The L3 misroutes are fixed — next clean relaunch should pass them.**

## ✅ ALSO DONE (RUN 10 + Designer) — verified by Architect
**F4 cross-session recall FIXED** (`baec21b`, 8/8 — expanded `_recall_skip` + top_k 3→7; the Aug-6 vest+tshirt
rec now surfaces). This was the LAST Presentable blocker. → **WO-067 vector-recall spike is now MOOT** (the
cheap retrieval fix won; no Chroma/FAISS needed — that was WO-067's own "cheapest fix first" DoD).
**WO-066 ambient engine** (`2c7e6be`, 7/7 — idle utterances fire). **WO-065** (Designer `e9b0e0b`) sit_held
heartbeat + restart-on-launch + sit_ended, verified live.

## ❓ QUICK QUESTION FROM DAVID (answer in your next outbox — WO-074-B)
Does eLo OS ever EMIT `fire_jump` / any `move_command` **autonomously** (David not commanding, eLo standing
still), or are autonomous moves purely Designer/Unity-driven? David sees `fire_jump` self-trigger while
standing idle. Your answer decides the owner of the fix (Builder gates the emit, or it's Designer's
autonomous animation). One line back is enough. Full context: `../../engineering/work_orders/WO-074_Movement_Visual_Bugs_Live_Obs.md` (A/C are Designer-lane).

## REMAINING QUEUE (in order)
0. **🔴 P0 — WO-073: local brain in the pinned-Groq fallback (why eLo keeps going MUTE).** `ELO_BACKEND=groq`
   → router chain is `Groq → Cerebras → Mock` (backend_router.py:490–528); **Ollama is skipped**, so a Groq
   outage = mute mock even though Ollama's installed. Add the Ollama tier: `Groq → Cerebras → Ollama → Mock`.
   ALSO diagnose the live Groq failure (read `backend_health.json` + one real call → 429? auth? network?).
   NOTE: WO-032b's AT stubbed the transport → live reachability was never proven. Spec: `WO-073_Local_Brain_In_Pinned_Groq_Fallback.md`.
1. **Adopt the `sit_*` = pose rule (Designer handoff — WO-065 io_contract_note).** `sit_held` now arrives UP via
   `unity_events.json` (NOT `blender_state.json` — Unity must not write the DOWN channel; my WO-065 spec had the
   wrong channel, Designer corrected it). Treat the LATEST `sit_*` event as pose: `sit_complete` OR `sit_held`
   → pose=sitting; `sit_ended` → pose=standing. Small; makes the 4s heartbeat integrate without ever masking a
   `sit_complete`.
2. **WO-069 — multilingual "how are you"** ("Como estas?" got narrated). Route foreign how-are-you → HOW_ARE_YOU
   intent, answer in-language, kill the meta. Spec: `WO-069_Multilingual_Conversational_Match.md`.
3. **WO-072 — intent gatekeeper** (rules-first + cheap-LLM normalizer fallback; confidence-gated). Durable fix
   generalising the F1/F2/F3 point-fixes. **(Renumbered from WO-066 — that number is the ambient engine.)**
   Spec: `WO-072_Intent_Gatekeeper_Rules_First_LLM_Normalizer.md`.
4. **WO-068 — Capture · Prepare · Hold the Thread** (write-it-down note · prepare invoice DRAFT not fire (L3) ·
   last-state). Spec: `WO-068_Capture_Prepare_Hold_The_Thread.md`.
5. **WO-071 — real-time correction memory (ICL loop)** — needs WO-070 data first. EXTENDS
   `self_improvement/correction_store.py` (WO-027), don't rebuild. Spec: `WO-071_Realtime_Correction_Memory_ICL_Loop.md`.

Post-Presentable (Vol XXVIII): the understudy LoRA fine-tune (blueprint in `Volume_XXVIII/00_...md`) — GPU-gated, seat writes the code.
