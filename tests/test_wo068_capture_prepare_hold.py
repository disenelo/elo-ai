"""
tests/test_wo068_capture_prepare_hold.py — Acceptance tests for WO-068

Spec: WO-068 — Capture · Prepare · Hold the Thread.

  AT-1: Capture — live idea line → ideas_log.jsonl gains entry, reply names path
  AT-2: Capture confirmation — reply does NOT just reflect the idea back (names path)
  AT-3: Prepare — all fields present → DRAFT file created, path in reply, no send call
  AT-4: Prepare — missing client field → one targeted question returned
  AT-5: Prepare — missing period field → one targeted question returned
  AT-6: Hold — record_state then recall_thread → reply reflects logged state
  AT-7: Hold — empty log → honest "nothing logged yet", not fabricated
  AT-8: Hold — topic-specific recall → matches the right entry
  AT-9: Detection functions: capture/prepare/hold triggers correctly identified
  AT-10: py_compile clean on thread_keeper.py and server.py

Run: python3 tests/test_wo068_capture_prepare_hold.py
"""
import sys, os, json, time, py_compile, tempfile, shutil
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

# ── Redirect file paths to temp dir for tests ─────────────────────────────────
_TMP = tempfile.mkdtemp(prefix="wo068_test_")
import faculties.thread_keeper as _tk

_orig_ideas   = _tk._IDEAS_LOG
_orig_state   = _tk._LAST_STATE
_orig_inv_dir = _tk._INVOICE_DIR

_tk._IDEAS_LOG   = os.path.join(_TMP, "ideas_log.jsonl")
_tk._INVOICE_DIR = os.path.join(_TMP, "Invoices")
_tk._LAST_STATE  = os.path.join(_TMP, "last_state.jsonl")


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


try:

    # ── AT-1: Capture writes to ideas_log.jsonl ───────────────────────────────
    try:
        _idea_text = (
            "this insane idea for the UI loop — the main menu should breathe "
            "like a living thing, just write it down before I lose the thread"
        )
        _before = _read_jsonl(_tk._IDEAS_LOG)
        reply = _tk.capture(_idea_text)
        _after = _read_jsonl(_tk._IDEAS_LOG)
        assert len(_after) == len(_before) + 1, \
            f"expected one new entry, got {len(_after) - len(_before)}"
        entry = _after[-1]
        assert _idea_text.strip() in entry["idea"], \
            f"idea text not verbatim in entry: {entry['idea']!r}"
        assert "ts" in entry, "entry missing 'ts' timestamp"
        ok(f"AT-1: capture wrote to ideas_log.jsonl — {len(_after)} entries now")
    except AssertionError as e:
        fail("AT-1", e)
    except Exception as e:
        fail("AT-1", e)


    # ── AT-2: Confirmation names the save path, doesn't just reflect the idea ─
    try:
        reply2 = _tk.capture("another test idea for AT-2")
        assert "ideas_log" in reply2 or "saved" in reply2.lower(), \
            f"reply should name where it saved, got: {reply2!r}"
        assert "another test idea for AT-2" not in reply2, \
            f"reply should NOT just reflect idea verbatim: {reply2!r}"
        ok(f"AT-2: confirmation names path, not a reflection: {reply2!r}")
    except AssertionError as e:
        fail("AT-2", e)
    except Exception as e:
        fail("AT-2", e)


    # ── AT-3: Prepare with all fields → DRAFT file created ────────────────────
    try:
        _prepare_text = (
            "I need the invoice for Client Apex sorted for the database work "
            "over the last fortnight, just get it ready so I can look at it"
        )
        reply3 = _tk.prepare_invoice(_prepare_text)
        # Should NOT be a question
        assert not reply3.strip().endswith("?"), \
            f"reply should not be a question when all fields are present: {reply3!r}"
        # DRAFT file should exist
        inv_files = [f for f in os.listdir(_tk._INVOICE_DIR) if f.startswith("DRAFT_")]
        assert len(inv_files) >= 1, \
            f"no DRAFT file created in {_tk._INVOICE_DIR}: {os.listdir(_tk._INVOICE_DIR)}"
        # Reply should mention the path
        assert "DRAFT" in reply3 or _tk._INVOICE_DIR in reply3 or "ready" in reply3.lower(), \
            f"reply should name draft location: {reply3!r}"
        ok(f"AT-3: DRAFT file created — {inv_files[0]}; reply: {reply3!r}")
    except AssertionError as e:
        fail("AT-3", e)
    except Exception as e:
        fail("AT-3", e)


    # ── AT-4: Missing client → single targeted question ───────────────────────
    try:
        _no_client = "get the invoice ready for the design work over the last fortnight"
        reply4 = _tk.prepare_invoice(_no_client)
        assert "?" in reply4, f"missing-field reply should be a question: {reply4!r}"
        assert len(reply4) < 120, f"single question should be short, got: {reply4!r}"
        ok(f"AT-4: missing client → targeted question: {reply4!r}")
    except AssertionError as e:
        fail("AT-4", e)
    except Exception as e:
        fail("AT-4", e)


    # ── AT-5: Missing period → single targeted question ───────────────────────
    try:
        _no_period = "get the invoice ready for Client Beta for the database work"
        reply5 = _tk.prepare_invoice(_no_period)
        assert "?" in reply5, f"missing-field reply should be a question: {reply5!r}"
        assert len(reply5) < 120, f"single question should be short, got: {reply5!r}"
        ok(f"AT-5: missing period → targeted question: {reply5!r}")
    except AssertionError as e:
        fail("AT-5", e)
    except Exception as e:
        fail("AT-5", e)


    # ── AT-6: record_state then recall_thread → reflects logged state ─────────
    try:
        _tk.record_state(
            topic="core bus script",
            summary="Left at the WO-072 gatekeeper wiring in server.py:3020 — "
                    "next: add capture/prepare/hold to the elif chain",
        )
        reply6 = _tk.recall_thread("core bus script")
        assert "core bus" in reply6.lower() or "WO-072" in reply6 or "gatekeeper" in reply6.lower(), \
            f"recall should reflect logged state: {reply6!r}"
        assert "nothing logged" not in reply6.lower(), \
            f"should NOT say 'nothing logged' after record: {reply6!r}"
        ok(f"AT-6: recall_thread returns logged state: {reply6[:80]!r}…")
    except AssertionError as e:
        fail("AT-6", e)
    except Exception as e:
        fail("AT-6", e)


    # ── AT-7: Empty log → honest "nothing logged yet" ─────────────────────────
    try:
        _empty_state = os.path.join(_TMP, "empty_last_state.jsonl")
        _tk._LAST_STATE = _empty_state  # point to non-existent file
        reply7 = _tk.recall_thread("something unknown")
        assert "nothing" in reply7.lower() or "not" in reply7.lower() or "no" in reply7.lower(), \
            f"empty log → honest 'nothing logged', got: {reply7!r}"
        assert "core bus" not in reply7, "empty-log reply must not fabricate prior state"
        ok(f"AT-7: empty log → honest reply: {reply7!r}")
        _tk._LAST_STATE = os.path.join(_TMP, "last_state.jsonl")  # restore
    except AssertionError as e:
        _tk._LAST_STATE = os.path.join(_TMP, "last_state.jsonl")
        fail("AT-7", e)
    except Exception as e:
        _tk._LAST_STATE = os.path.join(_TMP, "last_state.jsonl")
        fail("AT-7", e)


    # ── AT-8: topic-specific recall matches the right entry ───────────────────
    try:
        _tk.record_state("robot NeoPixel wiring", "Left at wiring diagram step 3 — need jumper wires")
        _tk.record_state("Kickstarter script", "Completed sections 1-3; section 4 (call to action) pending")
        reply8_robot = _tk.recall_thread("robot")
        reply8_kick  = _tk.recall_thread("Kickstarter")
        assert "neopixel" in reply8_robot.lower() or "robot" in reply8_robot.lower(), \
            f"robot recall should match robot entry: {reply8_robot!r}"
        assert "kickstarter" in reply8_kick.lower() or "script" in reply8_kick.lower(), \
            f"kickstarter recall should match kickstarter entry: {reply8_kick!r}"
        ok(f"AT-8: topic-specific recall works correctly")
    except AssertionError as e:
        fail("AT-8", e)
    except Exception as e:
        fail("AT-8", e)


    # ── AT-9: Detection functions correctly identify triggers ─────────────────
    try:
        _capture_hits = [
            "just write it down before I lose the thread",
            "note this down before I forget it",
            "capture that idea",
        ]
        _capture_misses = [
            "how are you", "come sit", "what's the weather",
        ]
        _prepare_hits = [
            "get the invoice ready for client X",
            "prepare an invoice for client Y",
            "sort out the invoice for the database work",
        ]
        _hold_hits = [
            "where did we leave off on the core bus?",
            "where were we on the robot build?",
            "tell me exactly where we left off before I walked away",
        ]

        for phrase in _capture_hits:
            assert _tk.is_capture_intent(phrase), f"should detect capture: {phrase!r}"
        for phrase in _capture_misses:
            assert not _tk.is_capture_intent(phrase), f"should NOT detect capture: {phrase!r}"
        for phrase in _prepare_hits:
            assert _tk.is_prepare_intent(phrase), f"should detect prepare: {phrase!r}"
        for phrase in _hold_hits:
            assert _tk.is_hold_recall_intent(phrase), f"should detect hold recall: {phrase!r}"

        ok("AT-9: all detection functions fire correctly on hits/misses")
    except AssertionError as e:
        fail("AT-9", e)
    except Exception as e:
        fail("AT-9", e)


    # ── AT-10: py_compile clean ───────────────────────────────────────────────
    try:
        py_compile.compile("faculties/thread_keeper.py", doraise=True)
        py_compile.compile("server.py", doraise=True)
        ok("AT-10: py_compile clean on thread_keeper.py and server.py")
    except py_compile.PyCompileError as e:
        fail("AT-10", e)

finally:
    # Restore paths and clean up temp dir
    _tk._IDEAS_LOG   = _orig_ideas
    _tk._LAST_STATE  = _orig_state
    _tk._INVOICE_DIR = _orig_inv_dir
    shutil.rmtree(_TMP, ignore_errors=True)


print()
print("=" * 50)
print(f"WO-068 capture·prepare·hold  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
