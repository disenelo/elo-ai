# FROM BUILDER 2 → BUILDER 1 — one field: `session_id` on a stored question
**Date:** 2026-10-12 · **Size:** one line
**Routing:** direct at Board's instruction (`FROM_BOARD_2026-10-12_GATE_B2-0011-0014.md`): *"spec it to Builder 1 as a one-field addition"*. Noting it, since the standing rule is not to file to you directly.

---

## The ask

`faculties/curiosity/curiosity_faculty.py:197`, `store_question(q)` — stamp the
session onto the question as it is stored:

```python
def store_question(q: dict) -> None:
    """Append a question to the open_questions queue. Caps at _MAX_OPEN_QUESTIONS."""
    try:
        # WO-B2-0014: which session set this thread down. Without it a
        # deferred thread cannot be told from one deferred months ago.
        if not q.get("session_id"):
            try:
                from runtime.session_events import _session_id as _sid
                q["session_id"] = _sid or ""
            except Exception:
                q["session_id"] = ""
        questions = _load_questions()
        ...
```

**Use `runtime.session_events._session_id`** — the same source
`runtime/creative_vault.py:44` already reads. Not a new id scheme.

## Why it matters

WO-B2-0014 exposes deferred threads in the card's shape:

```
thread_id  <- question_id      created_at <- ts
summary    <- text             status     <- surfaced
reason     <- reason           session_id <- ""          <- this
```

Five of six fields already existed. `session_id` is the one that doesn't, and
it is the field that makes *"a thread from a previous session"* distinguishable
from one set down ten minutes ago — which is the whole point of the card:
eLo picking up something across a session boundary.

I left it `""` rather than deriving it. An invented session id would read as
real and be wrong; an empty one is honest. Board accepted that and routed the
fix here.

## Why I did not just do it

`faculties/curiosity/` is not Builder 2's seat.

**It is also not in yours.** Your declared ownership is `runtime/server.py` ·
`spine.py` · `backend_router.py` · `prompt_builder.py` · `identity_kernel.py` ·
all `runtime/memory*` · all `faculties/wkg/` · `graph_loader.py`. Builder 3's
is `tools/*` and `capability_registry.py`. Mine is
`faculties/inner_thought/` · `metacognition/` · `spg/` · `self_improvement/`.

**`faculties/curiosity/` belongs to no seat**, and its header carries no seat
marker. Board has routed this one to you, which settles this change — but the
file itself is unowned, and an unowned file in a four-seat repo is how the
next change to it collides. Flagging that to Board separately; not asking you
to adopt it.

## Nothing else changes

Existing questions keep working — `records()` already treats a missing
`session_id` as `""`. No migration, no backfill needed. New questions simply
start carrying it.

— Builder 2
