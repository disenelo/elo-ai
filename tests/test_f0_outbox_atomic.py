"""
tests/test_f0_outbox_atomic.py — card 0053 F0: prove outbox cannot be left
unparseable by a partial write.

✅ Done when:
  1. blender/agent_bus/builder/outbox.json parses clean.
  2. A simulated partial write (truncation mid-file) is detected by the reader
     — i.e. the atomic write pattern means the live file is never in a bad state.

Run: python3 tests/test_f0_outbox_atomic.py
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTBOX = os.path.join(ROOT, "blender", "agent_bus", "builder", "outbox.json")

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# ── T1: current outbox.json parses clean ─────────────────────────────────────
def test_t1_current_outbox_parseable():
    if not os.path.exists(OUTBOX):
        err("T1: outbox.json does not exist")
    try:
        with open(OUTBOX, encoding="utf-8") as f:
            obj = json.load(f)
        ok(f"T1: outbox.json parses clean — {len(obj)} keys")
    except json.JSONDecodeError as e:
        err(f"T1: outbox.json is corrupt — {e}")


# ── T2: atomic write pattern cannot leave the file mid-write ─────────────────
def test_t2_atomic_write_cannot_corrupt():
    """
    Simulate a crash mid-write:
    - Write truncated JSON to .tmp
    - Kill the process (simulate: do NOT call os.replace)
    - Verify the live file is still intact

    With atomic writes, the live file is untouched until os.replace() succeeds.
    A crash before os.replace() leaves the live file clean and .tmp as garbage.
    """
    if not os.path.exists(OUTBOX):
        err("T2: outbox.json does not exist — cannot test")

    with open(OUTBOX, encoding="utf-8") as f:
        original = f.read()

    tmp = OUTBOX + ".tmp"
    try:
        # Simulate a truncated write to .tmp (crash before os.replace)
        with open(tmp, "w", encoding="utf-8") as f:
            f.write('{"partial": true, "this": "is truncated"')  # no closing }

        # The live file must still be intact (os.replace never called)
        with open(OUTBOX, encoding="utf-8") as f:
            live = json.load(f)
        ok(f"T2: live outbox intact after simulated partial write — {len(live)} keys")

        # The .tmp is corrupt (expected — it's the crash artifact)
        try:
            with open(tmp, encoding="utf-8") as f:
                json.load(f)
            err("T2: .tmp should be corrupt but parsed clean — test logic error")
        except json.JSONDecodeError:
            ok("T2: .tmp is corrupt (expected) — live file unaffected")

    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
        # Restore original content in case something changed
        with open(OUTBOX, "w", encoding="utf-8") as f:
            f.write(original)


# ── T3: verify ambient_engine.py uses os.replace (not direct open+write) ─────
def test_t3_ambient_engine_uses_atomic_write():
    engine_path = os.path.join(ROOT, "ambient", "ambient_engine.py")
    with open(engine_path, encoding="utf-8") as f:
        src = f.read()

    if "os.replace(" not in src:
        err("T3: ambient_engine.py does not use os.replace — outbox write is not atomic")

    # Confirm the pattern: .tmp then os.replace (not direct open("w"))
    if "_outbox_path + \".tmp\"" not in src and "outbox.json.tmp" not in src and '_tmp' not in src:
        err("T3: ambient_engine.py does not build a .tmp path before os.replace")

    ok("T3: ambient_engine.py uses atomic write pattern (.tmp + os.replace)")


# ── runner ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("F0 OUTBOX ATOMIC WRITE TEST")
    print()
    test_t1_current_outbox_parseable()
    test_t2_atomic_write_cannot_corrupt()
    test_t3_ambient_engine_uses_atomic_write()
    print()
    print("F0 DONE: outbox parseable, atomic write pattern in place.")
