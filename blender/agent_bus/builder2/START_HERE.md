# BUILDER 2 — START HERE
**Seat:** Builder 2 — Cognitive Systems
**Updated:** 2026-10-06 — file ownership enforced
**Authority:** David L3

---

## FILES YOU OWN — you may edit these without asking

```
faculties/inner_thought/      (all files)
faculties/metacognition/      (all files)
faculties/spg/                (all files)
self_improvement/             (all files)
```

## FILES YOU DO NOT TOUCH — ever

```
runtime/server.py             → Builder 1
runtime/spine.py              → Builder 1
runtime/backend_router.py     → Builder 1
memory/memory_faculty.py      → Builder 1
memory/vault_layer.py         → Builder 1
knowledge/graph_loader.py     → Builder 1
runtime/wkg_faculty.py        → Builder 1
tools/web_search.py           → Builder 3
tools/spotify_*.py            → Builder 3
Any Unity / .cs / .unity      → Designer
```

## If you need a change in server.py, spine.py, or backend_router.py

Write a spec file to Builder 1's inbox:
`blender/agent_bus/builder/FROM_BUILDER2_<date>_<topic>.md`

Describe exactly what needs to change and why. Builder 1 applies it. You do not touch those files yourself.

---

## Your active queue (2026-10-06)

**P0 — do these first:**

1. **SPG historical backfill from interactions.json** — 4+ months of conversation data sits in `interactions.json` (gitignored, always present). Process it into SPG significance scores. This is your half of the historical backfill. Builder 1 handles WKG backfill from the same file. Coordinate on date ranges to avoid duplication. File to Builder 1's inbox if you need server.py changes.

2. **Inner thought ordering** — restructure daemon to run BEFORE response assembly. Brief: `FROM_ARCHITECT_2026-10-06_INNER-THOUGHT-ORDERING-RULING.md`. WAIT for Builder 1's server.py P0 commits to land first. Check: `git log --oneline runtime/server.py | head -5` before touching anything that needs server.py.

3. **Read your inbox:**
   - `FROM_ARCHITECT_2026-10-05_INNER-THOUGHT-GENERATION-STANDARD.md`
   - `FROM_ARCHITECT_2026-10-05_INNER-THOUGHT-CONTRADICTION.md`
   - `FROM_ARCHITECT_2026-10-05_LEARNING-LOOP-LEAK-ADDENDUM.md`

**P1 — after P0:**

4. Canonical inner thought example standard
5. SPG significance live scoring (live turns, after historical backfill done)
6. Game mode dispatch

---

## Standards

- Run full test suite before every commit. If tests fail that were passing before your change, fix them before committing.
- No `git stash` on the whole repo. `git add <your paths>` only.
- No `git reset --hard`. Ever.
- Tests run on real server (port 5050). No mocked spine.
- PARTIAL = FAIL. Two states: PASS and broken.

---

## Report back

File results to: `blender/agent_bus/builder2/DONE/`
Evidence to: `engineering/evidence/INNER_THOUGHTS/`
Blockers to: `blender/agent_bus/builder2/TO_BOARD_<date>.md`
