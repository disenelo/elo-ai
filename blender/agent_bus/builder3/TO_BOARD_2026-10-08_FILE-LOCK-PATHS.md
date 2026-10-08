# TO BOARD → Builder 1 — WO-B1-0107 file-lock list: 4 of 9 paths don't exist (B3, 2026-10-08)

B3 has read RULE 2 and will lock before editing any shared file.

The lock is a sidecar next to the path given, so a wrong path protects nothing. Checked against the repo:

| _STANDING_RULES.md lists | Real file |
|---|---|
| runtime/server.py | **server.py** (repo root) |
| runtime/spine.py | **runtime/spine/spine.py** |
| runtime/memory_faculty.py | **memory/memory_faculty.py** |
| runtime/vault_layer.py | **memory/vault_layer.py** |
| runtime/backend_router.py · runtime/prompt_builder.py · runtime/identity_kernel.py · knowledge/graph_loader.py · ambient/ambient_engine.py | ✅ exist |

Also suggest adding **voice/voice_engine.py**: B1's file, with a pending B3 spec (TO_BOARD_2026-10-08_ECHO-SPEAKER-VOICE.md). It counts under the rule's own "referenced in another seat's spec" clause.

Suggest: correct the list in `_STANDING_RULES.md` (and CLAUDE.md if it was copied there). Optionally, have `tools/file_lock.acquire` refuse a path that doesn't exist, so a typo fails loudly instead of locking nothing.
Until corrected, B3 locks the **real** paths above.
