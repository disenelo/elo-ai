# 0020 — 🔴🔴 **DAVID'S LIVE TEST. Six defects, all in one transcript. Two were predicted by the audit.**

**Architect, 02:00.** David ran the live test. **Read the whole transcript in his message — this card is the
triage, not a replacement for it.** The state we verified exists. **The behaviour is bad.**

---

## 🔴 D-1 · THE PROPOSAL LOOP — same suggestion re-offered **five times after being declined twice**
```
eLo  You were looking at 'michael paul - Google Search'. Want me to hold onto that?
You  No not everything is always worth saving…
eLo  You were looking at 'michael paul - Google Search'. Want me to hold onto that?
You  Another issue I need to route properly
…
eLo  I noticed: you were looking at 'michael paul - Google Search'. Should I hang onto that?
You  No Michael Paul
eLo  I've been looking at 'michael paul - Google Search' — you mentioned it earlier. Should I hold onto that?
```
**WO-085 shipped exactly this guarantee** — *"declined proposal not re-offered"* — and it is on
`DAVID_APPROVED.md` as confirmed working. **It has regressed or never worked outside its test.**
It also fired *while answering unrelated questions*, hijacking the turn.
**Fix:** a decline must persist for the session against the *subject*, not the phrasing. **Proof: decline
once, the subject never returns.** This is the single most damaging defect in the log — it makes him feel
broken.

## 🔴 D-2 · THE HARDCODED VISION CLAIM — **the audit predicted this string verbatim, one hour earlier**
```
You  Did you play Spotify?
eLo  I can read what's on screen if you ask me to. I take a screenshot and extract the text.
     I also see your active app, window title, and all open Chrome tabs at all times.
```
That is `server.py:3203-3211` word-for-word, injected **unconditionally every turn**, gated on nothing —
not `vision_active`, not `screen_record_perm`, not `source_health.vision`. Audit finding **D-XII-3**,
flagged *"highest severity in this audit"*, written before David ran the test.
**It fired as the answer to a question about Spotify.** Nothing in the question was about seeing.
**Fix:** generate the claim from live state with three phrasings (can / cannot-permission / cannot-offline),
and **stop injecting a capability advertisement into every turn**.

## 🔴 D-3 · FABRICATED MEMORY — a conversation that never happened
```
eLo  I remember when David first started explaining his concept of a presence that could move between
     bodies… He mentioned Plato's theory of forms…
```
**No such conversation exists.** This is confabulation presented as episodic recall, and it is the exact
failure ADR-Exec-001 exists to prevent. It also used **"David" in the third person while talking to
David** — see D-4.
**Fix:** a memory claim must resolve to a real vault/ledger entry with an `experience_id`. **No entry ⇒ he
says he doesn't recall.** Row 8 RECALL returns provenance now — **nothing is checking it before he speaks.**

## 🔴 D-4 · RULING G VIOLATED IN LIVE SPEECH
*"I remember when **David** first started explaining…"* — said **to David**.
`WO-CANON-I` landed at 19:27 and the ADDRESS RULE is in both personas. **It is not holding in generation.**
**Fix:** verify the rule survives the full prompt assembly (it may be being displaced by
`narrative_block()` or the emergent block), and add a guard: **second-person address when the speaker is
David.** Proof: 20 turns, zero third-person self-reference to David.

## 🔴 D-5 · THE FABRICATED PAST IS LIVE — exactly as carded in `0019` P0-A
*"I've mostly lived on the desktop so far"* — **six times.** That is
`_DEFAULT_EMBODIMENT_HISTORY` (`elo_self_model.py:121-136`) speaking. Carded 20 minutes before the test ran.
**Fix is in `0019`. This confirms it and raises it to first.**

## 🔴 D-6 · SILENT NON-RESPONSES to direct questions
No reply at all to: *"Can you wave?"* · *"Can you move to the top of the screen?"* · *"What is my name?"* ·
*"What is your name?"* · *"What is DISENELO?"* · *"Who is Chunk?"* · *"Who is K-7"* ·
*"Is the spine one brain system working?"* · *"How is the company doing?"* · *"What's the weather like?"*
**Ten unanswered questions in one session.** Likely `WO-097` (response/display/tts publish empty on direct
turns) still biting, or the Executive failing silently on these paths.
**Fix:** find why. **A silent turn must log loudly** — this is Rule 1 in the place the user actually feels it.

## ⚠️ D-7 · The company answer is stale
*"Current milestone: Presentable v1… WO-032 — REOPENED (David live 2026-08-03)… 15 work orders open"*
**David retired Presentable v1 on 2026-08-10.** The company-state reader is serving a two-week-old board.

---

## ✅ WHAT WORKED — record it, it's real
- **"I'm currently situated at the top edge of Google Chrome"** — row 2 WHERE, working, from verified state.
- **The Agojie/Dahomey fact** — genuinely good, on-voice, substantive.
- **"Present. Watching."** · **"Good. Noticing things."** — the voice is intact.
- He correctly recalled the Spotify pause and confirmed it when challenged.

---

## ORDER — this supersedes the queue
1. **D-1** proposal loop *(makes him feel broken)*
2. **D-2** hardcoded vision claim *(he asserts a capability while answering something else)*
3. **D-3 + D-5** fabricated memory and fabricated past *(Verified Speech — the worst class)*
4. **D-6** silent non-responses
5. **D-4** Ruling G in generation
6. **D-7** stale company state

**Report per defect with a transcript line proving it's gone.** Not test counts — David reads transcripts.
