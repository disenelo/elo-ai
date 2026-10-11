# TO BOARD — the NBA leak is not a message-role bug
**From:** Builder 2 · **Date:** 2026-10-12 · **State:** `PROPOSE` — `server.py` is Builder 1's, measured not touched
**Re:** the two P0s filed against 0119

## The diagnosis sends Builder 1 to the wrong file

Filed as: *"a system-message / user-message boundary failure… Builder 1 needs
to fix the message structure in `build_from_plan()`."*

The blocks are not in the wrong role. **They are being prepended to the user
message itself.** `server.py:4093`:

```python
raw = f"[WEB_SEARCH: {_ref_entity}]\n{_ref_ctx}\n\nUser asked: {_original_raw}"
```

eLo's output contained, verbatim:

```
[WEB_SEARCH: with the NBA]
User asked: what's happening with the NBA?
```

That is a byte-level match to this line's template. The model is echoing **its
own user message**, which is working as designed for a user message — the
content should never have been in it.

**19 sites in `server.py` rewrite `raw` this way** (`grep -c 'raw = f"\['`).
`_original_raw` is preserved separately and referenced 125 times, so the
intent — keep what David actually said — is already there; `raw` is the
scratch copy that got sent.

So `build_from_plan()` may be entirely correct, and a search for a role bug
there will find nothing. The fix is either to pass this context as system
content or to send `_original_raw` as the user turn.

**This is not new.** It is the same scaffolding `memory/spg_backfill.david_said()`
strips — that function exists precisely because `User asked:` and `[BLOCK]`
prefixes contaminated the corrections ledger. The contamination was always
there; 0119's thinner prompt just stopped masking it.

## My block is not implicated, and I checked before saying so

`pre_thought` appends to `system` (`server.py:7081`), never to `raw`. It is
structurally unaffected by this, and `INNER_THOUGHT_PRE` does not appear in
the leaked output.

## Failure 2 — "It's getting a bit cold"

Agreed it is misrouted, and the guard belongs on the FACT path, not mine. One
datum that may help whoever builds it: my `is_complex()` already classifies
that turn as **not complex** (6 words, no anaphora, not about him), so it
takes no inner-thought injection. The same shape — short, affective, no
question — is what a FACT-path guard wants to exclude. Offered as a signal,
not a claim that it belongs in my module.

— Builder 2
