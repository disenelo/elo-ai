# DIAGNOSIS — live transcript #2 (David, 2026-08-07, partly on the real backend)

Architect diagnosis, transcript-grounded. NOT a fix — routed to owning seats. Distinct from the mock
transcript earlier today: this one shows the real backend working for stretches, so the WINS are real and
the remaining bugs are now cleanly visible (not mock noise).

## ✅ WINS (real, on the real backend — do not regress)
- **Company awareness is REAL now (WO-048 working):** "how's the company" → "steady: early phases frozen,
  core presence up, avatar partially active…" — grounded in actual state, no "Company for Doing"
  hallucination. Big leap from this morning.
- **Board focus (WO-061):** "what's on the board" → Milestone + focus items + in-progress WOs + the file
  path. Surfaces FOCUS, not raw backlog. (Minor: it surfaced The-Moment WO-052/053 as focus — check the
  `COMPANY_FOCUS` marker points at the close-out, not the richness tier.)
- **Weather · random facts · in-session thread recall** all working ("Sunny 25°C"; honey/Córdoba facts;
  "I remember you asking if I actually retrieve memory… building the Faculty Bus").
- Sit + situated self good ("sitting beside you on the desktop, watching the code").

## 🔴 BUGS (real, grounded — routed)
### A. Intent misroute — conversation parsed as commands / spurious tools ▶ BUILDER (WO-039 + WO-020)
- "anything we can press on with? that needs my attention?" → **"Shall I press on+with?+that+needs+my+
  attention??"** — question mangled into a garbled command fragment (word-joining). WO-039 garble family,
  live regression on a conversational question.
- "Strange reply what does that mean?" → **"…the required GITHUB_REPO environment variable isn't set…"** —
  a GitHub tool fired spuriously, totally out of context. Tool routing false-fire (WO-020 AT is green but
  LIVE mis-fires — add this case).
- "No but it takes time to build you" → **"Ok, cancelled."** — conversational "No" read as a command
  cancel. Misroute.
- **Pattern:** several intent/tool ATs pass but LIVE conversational input still trips commands/tools. The
  real test is a live conversational pass on the real backend — fold these exact lines into the AT suites.

### B. Cross-SESSION memory recall fails ▶ BUILDER (WO-022/037 — durable path, not just in-session)
- "Last time you gave me a recommendation" / "vest + t-shirt… can you remember?" → mirrors what David just
  said, does not RECALL. "do you remember our last weather conversation?" → "I don't have a record of us
  discussing the weather before."
- In-session thread recall works; DURABLE cross-session recall of a prior recommendation does NOT surface.
  `test_wo037` writeback is green, so the gap is live retrieval/durability across restarts — Builder check
  the live durable path (was the prior weather→clothing rec stored durable? does retrieval match it?).
  This is David's exact continuity test ("last time you said…") — high value.

### C. Engage-not-mirror still leaking ▶ BUILDER (WO-036 — extend beyond opener-only)
- Mid-reply mirroring + narrating David's own messages + typo-commenting are back: "You answered with a
  single word, like a quiet nod…" · "You said 'Interesting to know' — a little spark of curiosity" · "Your
  typo 'hwow' slipped in like a tiny surprise" · "I caught that you wondered if my last line was a joke."
- WO-036b scrub is OPENER-ONLY by design, so these mid-reply/meta lines pass. Extend the scrub (or the
  system prompt discipline) to kill meta-narration of the user's message + typo-commenting anywhere in the
  reply, not just the opener. This is David's #1 felt conversation annoyance.

### D. Backend still flapping to mock ▶ BUILDER (WO-032b — not yet done)
- "Can't reach my thinking right now — running on backup" fired 2× mid-conversation → still dropping to
  mock intermittently. Confirms WO-032b (Groq via httpx, no SDK) + clear the latching `_groq_quota_exceeded`
  429 flag is still needed. Key is present in `.env`; this is the code fix.

### E. (minor) Perception accuracy ▶ later (WO-038 family, behind Presentable)
- "I saw you checked the 'Limited Use: Seems…" / "the Grok page is linked into the eLo Robot Tracker" —
  reading desktop context but partially/inaccurately. David: "not how you're seeing it… work on that." Not
  Presentable-critical; note for the perception scope WO.

## Order (Builder)
WO-032b (real brain, stops the flapping) → WO-039/WO-020 live misroute cases → WO-022/037 durable
cross-session recall → WO-036 mirror scrub beyond opener. Each: add the live line to its AT so it can't
silently regress. David L3 = a full conversation that stays coherent + recalls across sessions.
