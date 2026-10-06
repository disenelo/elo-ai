# TO BOARD — Builder 3 — "remember this" (vault_write) findings, 2026-10-06

## What happened
Capability demo 14:04: "remember this: eLo ran his full capability demo on 6 October" → "I don't have that recorded." (backend `ollama(stream)`).
- **Nothing was saved.** There is no journal note for it.
- The executive's plan never selected `vault_write`, so the background write (WO-VAULT-OPTION-A) didn't run.

## What Builder 3 did, then undid
- Builder 3 made save intents a direct answer ("Saved — I'll remember that: …") in `tools/tool_router._direct_intercepts` (`d711b54`).
- That **contradicts the Board's WO-VAULT-OPTION-A ruling (2026-09-28)**: the vault write is silent and its string must not become the reply. Builder 3 hadn't checked for the ruling. **Reverted** (`c777cee`). `tests/test_wo_vault_option_a.py` is 6/6 again.

## Side effect of that change (Builder 3's fault)
- While the change was in, the test suite wrote **two real notes** to `obsidian_vault/07 Journal/`: `20261006-1545 And Check The Time.md` and `20261006-1545 Cats Are Great.md`.
- The cause: the tests mock `_AGENTS["vault_write"]`, but the change imported the writer directly.
- Builder 3 left both notes in place (no-delete rule). David to keep or remove.
- Older `Cats Are Great.md` notes (29 Sep ×4, 2 Oct) show this suite was already leaking real writes through another path. Owner: whoever owns `test_wo_vault_option_a`.

## Rulings needed
1. **Routing (Builder 1 / spine):** "remember this: X" must select `vault_write`. Live, it didn't.
2. **Confirmation (Board / David):** under Option A, eLo's reply after a save is whatever the LLM writes, and live it was a denial. May a successful save be confirmed in one short line ("Saved.")? The ruling's own concern was a mock "celebrate" pool replacing the reply, not a truthful confirmation.
