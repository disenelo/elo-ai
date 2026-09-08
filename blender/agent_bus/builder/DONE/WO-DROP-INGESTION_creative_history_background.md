# WO-DROP-INGESTION — Drag-and-Drop Company Ingestion / Background History Work
**Owner:** Builder
**Priority:** P3
**Status:** DISPATCHED 2026-08-30 — SPEC PENDING
**Dispatched by:** Board / Lead Architect (16th-pass BSU, 2026-08-30)
**Source:** Build List §6 CREATE — "Background tasks/history-driven work"; DISPATCH_BOARD G-17 — "`creative_drop_runner.py` stub; not specced; no WO" [SOURCE_ARCHIVE: eLo — FINISHING : BUILD LIST.rtf]
**Gate:** Spec required before implementation. Builder reads this WO now; does NOT implement until `SPEC_drop_ingestion_*.md` exists in `docs/architecture/specs/`.
**Lane:** Builder ONLY. No prompt changes.

---

## Intent

Wire the drag-and-drop company brain ingestion pathway so eLo can accept dropped files, documents, and data as background history-driven work — processing them through its cognitive spine and storing outputs in memory without requiring a live conversation turn.

---

## Gate status (as of 2026-08-30)

`tools/creative_drop_runner.py` stub exists. It is not specced and not wired into the capability registry or Executive. DISPATCH_BOARD G-17 flags this as a design-first item. Builder waits for spec.

Gate to open: Board authors SPEC. Look for `SPEC_drop_ingestion_*.md` in `docs/architecture/specs/`.

---

## Scope (once gate clears)

### VERIFY FIRST
```bash
# Check creative_drop_runner stub
cat /sessions/eager-inspiring-hopper/mnt/elo-ai/tools/creative_drop_runner.py 2>/dev/null | head -60

# Check what ingestion tooling exists
find /sessions/eager-inspiring-hopper/mnt/elo-ai/tools -name "*drop*" -o -name "*ingest*" 2>/dev/null | grep -v __pycache__

# Check SPEC exists before starting
ls /sessions/eager-inspiring-hopper/mnt/elo-ai/docs/architecture/specs/SPEC_drop_ingestion* 2>/dev/null || echo "SPEC NOT YET WRITTEN — DO NOT IMPLEMENT"

# Confirm HIST pipeline for reference
grep -n "HIST\|history_ingestion" /sessions/eager-inspiring-hopper/mnt/elo-ai/runtime/spine/spine.py 2>/dev/null | head -20
```

### Work items (from SPEC once available)
- **A. Drop receiver** — accept file paths from OS drag-and-drop or filesystem watch; validate type and size
- **B. Ingestion pipeline** — route dropped content through spine as `input_mode = "background_ingest"`, not a live turn
- **C. Memory write** — ingested content produces episodic/semantic memory entries; stored to vault with provenance tag `SOURCE=DROP`
- **D. Creative output** — if dropped content triggers creative work, output routes through eLo's style via Builder expression
- **E. Capability registration** — register `CREATE_INGEST_DROP` in capability registry; Executive must authorise each ingestion batch

---

## Acceptance Tests (run once SPEC and implementation complete)

1. `python3 -c "from tools.creative_drop_runner import CreativeDropRunner; r = CreativeDropRunner(); print('import ok')"` — passes.
2. `python3 tests/test_drop_ingestion.py --file sample.txt` — dropped file is processed; memory entry appears in vault with `SOURCE=DROP` provenance tag.
3. `grep -n "CREATE_INGEST_DROP" runtime/capability_registry.py` — capability is registered.
4. `python3 tests/test_drop_ingestion.py --no-exec-auth` — ingestion without Executive authorisation is rejected; assertion passes.
5. `python3 tests/test_drop_background.py` — background ingest does not block or delay a live conversation turn running concurrently.
