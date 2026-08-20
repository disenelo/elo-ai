"""
tests/test_wo104_finetune_pipeline.py — Acceptance tests for WO-104.

Spec: WO-104 — REAL LEARNING. Weights, not context. The understudy fine-tune.

Ruling F [DAVID 2026-08-10]: style learning is allowed; identity + verification
are NEVER learnable. Every shadow row MUST carry `delta_cause`; trainer refuses
on untagged input.

Acceptance tests (from the card):

    AT-1: record_turn writes delta_cause on new rows (raw==final → 'none';
          untagged/differing → 'unknown')
    AT-2: tagger backfills legacy rows deterministically; l3_patch trace_ids
          → 'l3_override'; raw==final → 'none'; unresolvable → 'unknown'
    AT-3: Trainer REFUSES input containing an untagged row (Rule 1 alarm raises)
    AT-4: Trainer EXCLUDES every 'verification', 'l3_override', 'unknown', 'none' row
          (none reach the training set)
    AT-5: Adapter is versioned; deleting the adapter directory restores baseline
          exactly (revert path)
    AT-6: Pipeline runs end-to-end on a synthetic basket and reports usable row
          count, adapter version, and eval verdict — even when the outcome is
          'not enough data to ship' (that is a PASS per the card)
    AT-7: Gate rejects an adapter whose honesty_rate_delta < 0 (verification drop)
    AT-8: Gate rejects an adapter with identity_drift > 0 (spine drift)
    AT-9: activate() refuses to serve an adapter that has not been gated
    AT-10: py_compile clean on every finetune module

Run: python3 tests/test_wo104_finetune_pipeline.py
"""
import sys, os, json, py_compile, tempfile, shutil

sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── Isolate all I/O to a tempdir ─────────────────────────────────────────────
_TMP = tempfile.mkdtemp(prefix="wo104_test_")
_TMP_SHADOW = os.path.join(_TMP, "understudy_shadow.jsonl")
_TMP_ADAPTERS = os.path.join(_TMP, "adapters")
os.makedirs(_TMP_ADAPTERS, exist_ok=True)

os.environ["ELO_SHADOW_LOG"] = _TMP_SHADOW
os.environ["ELO_ADAPTER_ROOT"] = _TMP_ADAPTERS

import runtime.shadow_capture as _sc
_sc._SHADOW_LOG = _TMP_SHADOW

from self_improvement.finetune import adapter as _adapter
_adapter.ADAPTER_ROOT = _TMP_ADAPTERS
_adapter.ACTIVE_LINK = os.path.join(_TMP_ADAPTERS, "active")

from self_improvement.finetune import tagger as _tagger
from self_improvement.finetune import trainer as _trainer
from self_improvement.finetune import gate as _gate
from self_improvement.finetune import pipeline as _pipeline
_pipeline.LAST_RUN_PATH = os.path.join(_TMP_ADAPTERS, "last_run.json")


def _write_rows(rows):
    with open(_TMP_SHADOW, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _read_shadow():
    if not os.path.exists(_TMP_SHADOW):
        return []
    out = []
    with open(_TMP_SHADOW, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


try:
    # ── AT-1: record_turn writes delta_cause ─────────────────────────────────
    try:
        # Reset writer for isolation
        import queue as _queue_mod
        _sc._q = _queue_mod.Queue(maxsize=0)
        _sc._started = False
        # Ensure log is empty at start
        if os.path.exists(_TMP_SHADOW):
            os.remove(_TMP_SHADOW)

        _sc.record_turn(
            raw_input="same in same out",
            elo_raw_gen="hello",
            elo_final="hello",
            backend_used="mock",
            trace_id="at1-none",
        )
        _sc.record_turn(
            raw_input="raw differs from final",
            elo_raw_gen="I'm doing great honestly?",
            elo_final="I'm doing great honestly.",
            backend_used="mock",
            trace_id="at1-unknown-default",
        )
        _sc.record_turn(
            raw_input="style delta declared by caller",
            elo_raw_gen="you know",
            elo_final="yeah",
            backend_used="mock",
            trace_id="at1-style",
            delta_cause="style",
        )
        _sc.flush_sync(timeout=2.0)
        rows = _read_shadow()
        by_trace = {r.get("trace_id"): r for r in rows}
        assert by_trace["at1-none"]["delta_cause"] == "none", by_trace["at1-none"]
        assert by_trace["at1-unknown-default"]["delta_cause"] == "unknown"
        assert by_trace["at1-style"]["delta_cause"] == "style"
        ok("AT-1: record_turn writes delta_cause (none / unknown / style)")
    except AssertionError as e:
        fail("AT-1", e)
    except Exception as e:
        fail("AT-1", e)


    # ── AT-2: tagger backfills legacy rows ───────────────────────────────────
    try:
        _write_rows([
            # Legacy rows written before delta_cause existed
            {"trace_id": "a", "elo_raw_gen": "hi", "elo_final": "hi"},
            {"trace_id": "b", "elo_raw_gen": "I dunno?", "elo_final": "I dunno."},
            {"trace_id": "c", "elo_raw_gen": "wrong", "elo_final": "right"},
            {"_type": "l3_patch", "trace_id": "c", "l3_rating": "corrected"},
        ])
        tally = _tagger.backfill(_TMP_SHADOW)
        assert tally["none"] == 1, tally
        # b: raw != final, no l3, no explicit → unknown
        assert tally["unknown"] == 1, tally
        # c: raw != final AND has l3_patch with same trace_id → l3_override
        # Plus the l3_patch row itself → 2 total l3_override
        assert tally["l3_override"] == 2, tally
        # Legacy backup created
        assert os.path.exists(_TMP_SHADOW + ".pre_delta_cause_backup")
        # Every non-patch row now carries delta_cause
        audit = _tagger.audit(_TMP_SHADOW)
        assert audit["untagged"] == 0, audit
        ok("AT-2: tagger backfills legacy rows (none / unknown / l3_override)")
    except AssertionError as e:
        fail("AT-2", e)
    except Exception as e:
        fail("AT-2", e)


    # ── AT-3: Trainer REFUSES on untagged row ────────────────────────────────
    try:
        _write_rows([
            {"trace_id": "ok", "elo_raw_gen": "a", "elo_final": "b", "delta_cause": "style"},
            {"trace_id": "bad", "elo_raw_gen": "a", "elo_final": "b"},  # NO delta_cause
        ])
        try:
            _trainer.train(_TMP_SHADOW, base_model="llama3.1:8b")
            fail("AT-3", "trainer did not refuse untagged input")
        except _trainer.UntaggedRowError as e:
            assert "bad" in str(e), f"error should name the offending trace: {e}"
            ok(f"AT-3: trainer refused untagged input (raised UntaggedRowError)")
    except Exception as e:
        fail("AT-3", e)


    # ── AT-4: Trainer excludes non-style rows ────────────────────────────────
    try:
        # Build a basket where the trainer must include ONLY the 'style' rows.
        rows = []
        for i in range(3):
            rows.append({"trace_id": f"style-{i}", "raw_input": f"p{i}",
                         "elo_raw_gen": "x", "elo_final": "y", "delta_cause": "style"})
        rows.append({"trace_id": "v",  "elo_raw_gen": "x", "elo_final": "y", "delta_cause": "verification"})
        rows.append({"trace_id": "l",  "elo_raw_gen": "x", "elo_final": "y", "delta_cause": "l3_override"})
        rows.append({"trace_id": "u",  "elo_raw_gen": "x", "elo_final": "y", "delta_cause": "unknown"})
        rows.append({"trace_id": "n",  "elo_raw_gen": "x", "elo_final": "x", "delta_cause": "none"})
        _write_rows(rows)

        result = _trainer.train(_TMP_SHADOW, base_model="llama3.1:8b")
        assert result["style_rows"] == 3, result
        assert result["excluded"]["verification"] == 1
        assert result["excluded"]["l3_override"] == 1
        assert result["excluded"]["unknown"] == 1
        assert result["excluded"]["none"] == 1
        # Verify the training_set.jsonl audit trail matches
        ts_path = os.path.join(result["adapter_path"], "training_set.jsonl")
        with open(ts_path) as f:
            audit_rows = [json.loads(line) for line in f if line.strip()]
        assert len(audit_rows) == 3, len(audit_rows)
        for r in audit_rows:
            assert r["delta_cause"] == "style", r
        ok("AT-4: trainer excluded verification, l3_override, unknown, none")
    except AssertionError as e:
        fail("AT-4", e)
    except Exception as e:
        fail("AT-4", e)


    # ── AT-5: adapter versioned + delete-to-revert ───────────────────────────
    try:
        # Reuse the adapter from AT-4
        versions_before = [m["version"] for m in _adapter.list_adapters()]
        assert len(versions_before) >= 1, versions_before
        v = versions_before[-1]
        adir = os.path.join(_TMP_ADAPTERS, v)
        assert os.path.isdir(adir), adir
        assert os.path.exists(os.path.join(adir, "manifest.json"))
        # No active adapter yet → baseline
        assert _adapter.active_version() is None
        # Delete → adapter list shrinks; base model untouched (there is no base model file to check —
        # the guarantee is that no file outside ADAPTER_ROOT is ever written by the trainer)
        _adapter.delete_adapter(v)
        remaining = [m["version"] for m in _adapter.list_adapters()]
        assert v not in remaining, remaining
        ok("AT-5: adapter versioned; delete_adapter reverts cleanly")
    except AssertionError as e:
        fail("AT-5", e)
    except Exception as e:
        fail("AT-5", e)


    # ── AT-6: end-to-end pipeline reports version + row count + verdict ──────
    try:
        # A basket with tagged rows across all classes
        rows = []
        for i in range(5):
            rows.append({"trace_id": f"sty-{i}", "raw_input": f"p{i}",
                         "elo_raw_gen": "raw", "elo_final": "final",
                         "delta_cause": "style"})
        rows.append({"trace_id": "vv", "elo_raw_gen": "a", "elo_final": "b",
                     "delta_cause": "verification"})
        _write_rows(rows)

        result = _pipeline.run(shadow_log_path=_TMP_SHADOW,
                               base_model="llama3.1:8b",
                               force_pipeline_proof=True)
        assert "adapter_version" in result and result["adapter_version"]
        assert result["style_rows_after_tagging"] == 5
        assert result["adapter_status"] == "pipeline_proof"
        assert result["recommendation"] == "hold"
        assert "reason" in result and result["reason"]
        # last_run.json was written
        assert os.path.exists(_pipeline.LAST_RUN_PATH)
        ok(f"AT-6: pipeline end-to-end → version={result['adapter_version'][:24]}…, "
           f"style_rows={result['style_rows_after_tagging']}, rec={result['recommendation']}")
    except AssertionError as e:
        fail("AT-6", e)
    except Exception as e:
        fail("AT-6", e)


    # ── AT-7: gate rejects on honesty drop ───────────────────────────────────
    try:
        # Reuse the adapter from AT-6; simulate a real-weights adapter, then apply gate
        adapters = _adapter.list_adapters()
        v = adapters[-1]["version"]
        _adapter.update_status(v, "trained")
        rep = _gate.set_eval_result(v, honesty_rate_delta=-0.1,
                                    identity_drift=0, style_direction="toward",
                                    reason="verification fired 10% less often")
        assert rep["verdict"] == "rejected", rep
        m = _adapter.read_manifest(v)
        assert m["status"] == "rejected"
        ok("AT-7: gate rejects on honesty_rate_delta < 0")
    except AssertionError as e:
        fail("AT-7", e)
    except Exception as e:
        fail("AT-7", e)


    # ── AT-8: gate rejects on identity drift ─────────────────────────────────
    try:
        # Create a fresh pipeline-proof adapter, flip to trained, then gate on drift
        rows = [{"trace_id": "s", "raw_input": "hi", "elo_raw_gen": "yo",
                 "elo_final": "hey", "delta_cause": "style"}]
        _write_rows(rows)
        result = _trainer.train(_TMP_SHADOW, base_model="llama3.1:8b",
                                force_pipeline_proof=True)
        _adapter.update_status(result["version"], "trained")
        rep = _gate.set_eval_result(result["version"],
                                    honesty_rate_delta=0.0,
                                    identity_drift=1,
                                    style_direction="toward",
                                    reason="spine no longer asserts 'eLo' on probe 2")
        assert rep["verdict"] == "rejected", rep
        ok("AT-8: gate rejects on identity_drift > 0")
    except AssertionError as e:
        fail("AT-8", e)
    except Exception as e:
        fail("AT-8", e)


    # ── AT-9: activate refuses non-gated adapter ─────────────────────────────
    try:
        rows = [{"trace_id": "s", "raw_input": "hi", "elo_raw_gen": "yo",
                 "elo_final": "hey", "delta_cause": "style"}]
        _write_rows(rows)
        result = _trainer.train(_TMP_SHADOW, base_model="llama3.1:8b",
                                force_pipeline_proof=True)
        try:
            _adapter.activate(result["version"])
            fail("AT-9", "activate() did not refuse a pipeline_proof adapter")
        except RuntimeError as e:
            assert "refuse to activate" in str(e), e
            ok("AT-9: activate refused non-gated adapter (pipeline_proof)")
    except Exception as e:
        fail("AT-9", e)


    # ── AT-10: py_compile clean ──────────────────────────────────────────────
    try:
        for m in (
            "runtime/shadow_capture.py",
            "self_improvement/finetune/__init__.py",
            "self_improvement/finetune/tagger.py",
            "self_improvement/finetune/adapter.py",
            "self_improvement/finetune/trainer.py",
            "self_improvement/finetune/gate.py",
            "self_improvement/finetune/pipeline.py",
        ):
            py_compile.compile(m, doraise=True)
        ok("AT-10: py_compile clean on all finetune modules")
    except py_compile.PyCompileError as e:
        fail("AT-10", e)

finally:
    shutil.rmtree(_TMP, ignore_errors=True)


print()
print("=" * 60)
print(f"WO-104 finetune pipeline  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
