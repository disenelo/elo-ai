"""
tests/test_0026_plugin_safety.py — Acceptance tests for card 0026.

Spec: ONE_BRAIN_CONVERGENCE_AUDIT — Plugin safety gate.

3 tests:
    FT-1  Plugin declaring unregistered capability fails to register (refused, logged)
    FT-2  Plugin declaring hardware_output is registered in propose-only mode
    FT-3  Plugin in propose-only mode is skipped by deliver_output() (no actuation path reached)

Run: python3 tests/test_0026_plugin_safety.py
"""
import sys, logging
sys.path.insert(0, ".")

# suppress debug noise
logging.basicConfig(level=logging.CRITICAL)

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


from plugins.base import PluginBase, _KNOWN_CAPABILITIES, _RESERVED_CAPABILITIES
from plugins.registry import PluginRegistry


# ── shared stub builder ───────────────────────────────────────────────────────

def make_plugin(name, capabilities):
    class Stub(PluginBase):
        NAME         = name
        VERSION      = "0.1"
        CAPABILITIES = capabilities
        LAYER        = "output"
        KERNEL_SAFE  = True

        def is_available(self):     return True
        def generate_response(self, user_input, context): return "stub"
        def deliver_output(self, response, context):
            Stub._deliver_called = True

    Stub._deliver_called = False
    return Stub()


# ── FT-1: unregistered capability → registration refused ─────────────────────

print("\nFT-1: Unregistered capability → registration refused")
try:
    bad_cap = "sentience_override"   # not in _KNOWN_CAPABILITIES
    assert bad_cap not in _KNOWN_CAPABILITIES, "pre-check: capability is already known (test needs updating)"

    plugin = make_plugin("bad_plugin", [bad_cap])
    violations = plugin.validate()

    if not violations:
        fail("FT-1", "validate() returned no violations for an unregistered capability")
    elif not any(bad_cap in v for v in violations):
        fail("FT-1", f"violation found but doesn't mention the bad capability: {violations}")
    else:
        # confirm registry also refuses it
        reg = PluginRegistry()
        reg.register(plugin)
        if "bad_plugin" in reg._plugins:
            fail("FT-1", "plugin with unregistered capability was accepted by registry")
        else:
            ok("FT-1 — unregistered capability refused at both validate() and register()")
except Exception as e:
    fail("FT-1", repr(e))


# ── FT-2: hardware_output → registered in propose-only mode ──────────────────

print("\nFT-2: hardware_output capability → propose-only mode")
try:
    assert "hardware_output" in _RESERVED_CAPABILITIES, \
        "pre-check: hardware_output should be in _RESERVED_CAPABILITIES"

    plugin = make_plugin("hw_plugin", ["hardware_output"])
    violations = plugin.validate()

    if violations:
        fail("FT-2", f"hardware_output plugin should not fail validate() — got: {violations}")
    else:
        reg = PluginRegistry()
        reg.register(plugin)
        if "hw_plugin" not in reg._plugins:
            fail("FT-2", "hardware_output plugin was refused entirely — should register in propose-only mode")
        elif not getattr(reg._plugins["hw_plugin"], "propose_only", False):
            fail("FT-2", "plugin registered but propose_only is not True")
        else:
            ok("FT-2 — hardware_output plugin registered; propose_only=True confirmed")
except Exception as e:
    fail("FT-2", repr(e))


# ── FT-3: propose-only plugin → deliver_output() blocked ─────────────────────

print("\nFT-3: propose-only plugin → deliver_output() not reached")
try:
    plugin = make_plugin("hw_plugin2", ["hardware_output"])
    plugin_cls = plugin.__class__

    reg = PluginRegistry()
    reg.register(plugin)

    # confirm registered in propose-only mode
    if not getattr(reg._plugins.get("hw_plugin2"), "propose_only", False):
        fail("FT-3", "plugin not in propose-only mode — FT-2 must pass first")
    else:
        # trigger deliver_output — the plugin's own deliver_output must NOT be called
        reg.deliver_output("test response", {})
        if plugin_cls._deliver_called:
            fail("FT-3", "deliver_output() reached actuation path — RESERVED gate not enforced")
        else:
            ok("FT-3 — deliver_output() blocked; actuation path not reached")
except Exception as e:
    fail("FT-3", repr(e))


# ── results ───────────────────────────────────────────────────────────────────

print(f"\n{'='*40}")
print(f"0026 Plugin Safety: {PASS} passed, {FAIL} failed")
if FAIL:
    sys.exit(1)
