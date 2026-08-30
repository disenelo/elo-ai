"""
tests/test_wo068_phase2_second_brain.py — WO-068 Phase 2 acceptance tests.

Second Brain: visual capture + vision-indexed recall.

  AT-P2-1: capture_visual with image bytes → second_brain/ entry created with provenance
  AT-P2-2: capture_visual with image bytes → index.jsonl entry added (type, note, tags)
  AT-P2-3: capture_visual without image → falls back to text-only capture (no second_brain entry)
  AT-P2-4: search_second_brain with matching keyword → returns path + description
  AT-P2-5: search_second_brain on empty archive → honest "nothing yet" reply
  AT-P2-6: search_second_brain no keyword match → honest "nothing matching" reply
  AT-P2-7: elo_made=True → index entry tagged elo_made: true
  AT-P2-8: recall_thread with topic → also checks archive (returns archive suffix when match found)
  AT-P2-9: py_compile clean on thread_keeper.py

Run: python3 tests/test_wo068_phase2_second_brain.py
"""
import sys, os, json, time, py_compile, tempfile, shutil

sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

# ── Redirect file paths to temp dir for tests ─────────────────────────────────
_TMP = tempfile.mkdtemp(prefix="wo068p2_test_")
import faculties.thread_keeper as _tk

# Redirect all paths to temp dir
_tk._IDEAS_LOG          = os.path.join(_TMP, "ideas_log.jsonl")
_tk._INVOICE_DIR        = os.path.join(_TMP, "Invoices")
_tk._LAST_STATE         = os.path.join(_TMP, "last_state.jsonl")
_tk._SECOND_BRAIN_DIR   = os.path.join(_TMP, "second_brain")
_tk._SECOND_BRAIN_INDEX = os.path.join(_TMP, "second_brain", "index.jsonl")

# Minimal synthetic image bytes (1x1 transparent PNG)
_PNG_BYTES = bytes([
    0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
    0x00, 0x00, 0x00, 0x0d, 0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x06, 0x00, 0x00, 0x00, 0x1f, 0x15, 0xc4,
    0x89, 0x00, 0x00, 0x00, 0x0a, 0x49, 0x44, 0x41,
    0x54, 0x78, 0x9c, 0x62, 0x00, 0x00, 0x00, 0x02,
    0x00, 0x01, 0xe2, 0x21, 0xbc, 0x33, 0x00, 0x00,
    0x00, 0x00, 0x49, 0x45, 0x4e, 0x44, 0xae, 0x42,
    0x60, 0x82,
])


def _read_jsonl(path: str) -> list:
    if not os.path.exists(path):
        return []
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


# ── AT-P2-1: capture_visual → second_brain/ PNG file created ─────────────────
try:
    reply = _tk.capture_visual("moody typography ref", _PNG_BYTES)
    sb_files = [f for f in os.listdir(_tk._SECOND_BRAIN_DIR) if f.endswith(".png")]
    assert sb_files, "No PNG file found in second_brain/ after capture_visual"
    assert "second_brain" in reply or "screenshot" in reply.lower() or "capture" in reply.lower(), \
        f"Reply does not mention save path: {reply!r}"
    ok("AT-P2-1: capture_visual with image → PNG saved in second_brain/")
except AssertionError as e:
    fail("AT-P2-1", e)
except Exception as e:
    fail("AT-P2-1", e)


# ── AT-P2-2: index.jsonl entry has correct provenance fields ──────────────────
try:
    entries = _read_jsonl(_tk._SECOND_BRAIN_INDEX)
    assert entries, "index.jsonl is empty after capture_visual"
    entry = entries[-1]
    assert entry.get("type") == "screenshot", f"type field wrong: {entry.get('type')!r}"
    assert "moody typography" in entry.get("note", ""), f"note field wrong: {entry.get('note')!r}"
    assert "ts" in entry, "ts field missing"
    assert "saved" in entry, "saved field missing"
    assert "path" in entry, "path field missing"
    assert os.path.exists(entry["path"]), f"PNG path does not exist: {entry['path']}"
    tags = entry.get("tags", {})
    assert isinstance(tags, dict), f"tags not a dict: {tags!r}"
    ok("AT-P2-2: index.jsonl entry has correct provenance fields")
except AssertionError as e:
    fail("AT-P2-2", e)
except Exception as e:
    fail("AT-P2-2", e)


# ── AT-P2-3: capture_visual without image → text only, no second_brain entry ──
try:
    prev_entries = _read_jsonl(_tk._SECOND_BRAIN_INDEX)
    reply = _tk.capture_visual("just a text note", None)
    after_entries = _read_jsonl(_tk._SECOND_BRAIN_INDEX)
    assert len(after_entries) == len(prev_entries), \
        "index.jsonl grew without an image — should not add entry for text-only capture"
    assert "ideas_log" in reply or "saved" in reply.lower(), \
        f"Text-only reply should confirm save: {reply!r}"
    ok("AT-P2-3: capture_visual without image → text only, no second_brain index entry")
except AssertionError as e:
    fail("AT-P2-3", e)
except Exception as e:
    fail("AT-P2-3", e)


# ── AT-P2-4: search_second_brain with matching keyword → returns path ─────────
try:
    result = _tk.search_second_brain("typography")
    assert "Nothing" not in result, f"Expected a match; got: {result!r}"
    assert "second_brain" in result or ".png" in result, \
        f"Result should name the file path: {result!r}"
    ok(f"AT-P2-4: search_second_brain match → {result[:80]!r}")
except AssertionError as e:
    fail("AT-P2-4", e)
except Exception as e:
    fail("AT-P2-4", e)


# ── AT-P2-5: search_second_brain on empty archive → honest reply ─────────────
try:
    _TMP2 = tempfile.mkdtemp(prefix="wo068p2_empty_")
    orig_index = _tk._SECOND_BRAIN_INDEX
    _tk._SECOND_BRAIN_INDEX = os.path.join(_TMP2, "index.jsonl")  # does not exist
    result = _tk.search_second_brain("anything")
    _tk._SECOND_BRAIN_INDEX = orig_index
    assert "Nothing" in result or "nothing" in result, \
        f"Empty archive should return honest 'nothing' reply, got: {result!r}"
    ok("AT-P2-5: empty archive → honest 'nothing yet' reply")
except AssertionError as e:
    fail("AT-P2-5", e)
except Exception as e:
    fail("AT-P2-5", e)
finally:
    try:
        shutil.rmtree(_TMP2)
    except Exception:
        pass


# ── AT-P2-6: search_second_brain with non-matching keyword → honest reply ─────
try:
    result = _tk.search_second_brain("absolutely_nonexistent_zzzxxx")
    assert "Nothing" in result or "nothing" in result, \
        f"Non-matching query should return honest reply, got: {result!r}"
    ok("AT-P2-6: no keyword match → honest 'nothing matching' reply")
except AssertionError as e:
    fail("AT-P2-6", e)
except Exception as e:
    fail("AT-P2-6", e)


# ── AT-P2-7: elo_made=True → tag reflects it ─────────────────────────────────
try:
    _tk.capture_visual("elo made this", _PNG_BYTES, elo_made=True)
    entries = _read_jsonl(_tk._SECOND_BRAIN_INDEX)
    last_elo = next((e for e in reversed(entries) if "elo made" in e.get("note", "")), None)
    assert last_elo is not None, "Could not find elo_made entry in index"
    assert last_elo["tags"]["elo_made"] is True, \
        f"elo_made tag should be True: {last_elo['tags']!r}"
    assert last_elo["tags"]["david_reference"] is False, \
        f"david_reference should be False for elo_made: {last_elo['tags']!r}"
    ok("AT-P2-7: elo_made=True → tagged correctly in index")
except AssertionError as e:
    fail("AT-P2-7", e)
except Exception as e:
    fail("AT-P2-7", e)


# ── AT-P2-8: recall_thread with topic appends archive suffix when match found ──
try:
    import faculties.thread_keeper as _tk2
    _TMP3 = tempfile.mkdtemp(prefix="wo068p2_recall_")
    _tk2._LAST_STATE         = os.path.join(_TMP3, "last_state.jsonl")
    _tk2._SECOND_BRAIN_DIR   = os.path.join(_TMP3, "second_brain")
    _tk2._SECOND_BRAIN_INDEX = os.path.join(_TMP3, "second_brain", "index.jsonl")
    _tk2._IDEAS_LOG          = os.path.join(_TMP3, "ideas_log.jsonl")

    # Seed a thread entry
    _tk2.record_state("brand typography", "reviewed moody type samples in Figma")

    # Seed a second_brain entry with matching keyword
    os.makedirs(_tk2._SECOND_BRAIN_DIR, exist_ok=True)
    with open(os.path.join(_TMP3, "second_brain", "capture_test.png"), "wb") as f:
        f.write(_PNG_BYTES)
    sb_entry = {
        "ts": time.time(), "saved": "2026-08-30 10:00 UTC",
        "path": os.path.join(_TMP3, "second_brain", "capture_test.png"),
        "type": "screenshot", "note": "moody typography ref",
        "description": "dark text layout", "tags": {"david_reference": True, "elo_made": False},
    }
    with open(_tk2._SECOND_BRAIN_INDEX, "a") as f:
        f.write(json.dumps(sb_entry) + "\n")

    reply = _tk2.recall_thread(topic="typography")
    assert "brand typography" in reply, f"Thread topic missing from reply: {reply!r}"
    assert "archive" in reply.lower(), \
        f"Expected archive suffix in reply when archive has match: {reply!r}"

    shutil.rmtree(_TMP3)
    ok("AT-P2-8: recall_thread with topic → includes archive suffix when match found")
except AssertionError as e:
    fail("AT-P2-8", e)
except Exception as e:
    fail("AT-P2-8", e)


# ── AT-P2-9: py_compile clean ────────────────────────────────────────────────
try:
    _f = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "faculties", "thread_keeper.py")
    py_compile.compile(_f, doraise=True)
    ok("AT-P2-9: py_compile clean on faculties/thread_keeper.py")
except py_compile.PyCompileError as e:
    fail("AT-P2-9", e)
except Exception as e:
    fail("AT-P2-9", e)


# ── cleanup ──────────────────────────────────────────────────────────────────
try:
    shutil.rmtree(_TMP)
except Exception:
    pass


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"WO-068 Phase 2 second brain  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
