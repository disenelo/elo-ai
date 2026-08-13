# ▶ BUILDER — WO-048/061 refinement: drop eLo's location from the board/company status answer (David live 2026-08-10)

## David confirmed the WIN (both work)
> "How's the company works, and how's the board work just — Full Board: location is also added which isn't
> needed"

"How's the company" and "how's the board" now return real answers — David-confirmed live. Close to done.

## The one trim
The **full-board answer appends eLo's situated-self LOCATION** (e.g. "perched on the bottom edge of Pages…")
— David: **not needed** in a company/board STATUS reply. A status question wants company/board content +
focus + recommendation + links, not where eLo is sitting.

**Fix (small, Builder lane):** in the company/board briefing path (`_build_briefing` / `_build_board_reply`),
do NOT append the situated-self location line. Keep location for where it belongs (where-are-you /
situated-self questions) — just strip it from the how's-the-company / how's-the-board / full-board replies.
Ship with the existing `tests/test_wo048_company_real.py` extended by one assertion: a board/company answer
contains NO location string. This closes WO-048/061 to David's live bar.

---

## Second trim (David live 2026-08-10) — eLo addresses David as "you," never says his name back
> "Also need eLo to know I'm David and not say my name back to me, instead say you"

**eLo knows its interlocutor is David** (the owner / sole L3). So in conversation it must **address him in the
second person — "you" — and NOT repeat his name back** ("David, …" / "…, David"). Saying the user's own name
back at them reads robotic/uncanny, not like eLo knows them.

**Fix (small, Builder lane, conversation voice):** the current speaker identity = David is known state — use
it to (a) suppress inserting "David" as a vocative/third-person reference in replies TO him, and (b) resolve
first/second person so eLo says "you"/"your" when addressing him. This is a voice/user-model fix, pairs with
WO-036 (no meta/narration reflex). Ship with a test: a reply addressed to David contains no "David" vocative
and uses second person. (Names are still fine when eLo refers to OTHER people, or when David explicitly asks
eLo to use his name — the rule is: don't name the person you're talking to back at them.)
