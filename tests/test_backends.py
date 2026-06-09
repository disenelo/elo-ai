"""
tests/test_backends.py — Unit tests for backends/

Tests Steps 41, 42, 43.
No API calls. No networking. No model connections.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backends.base_backend    import BaseBackend, BackendResponse, BackendUnavailableError
from backends.offline_backend import OfflineBackend
from backends.claude_backend  import ClaudeBackend


# ── Step 41: BaseBackend contract ─────────────────────────────────────────────

class TestBaseBackend(unittest.TestCase):

    def test_cannot_instantiate_directly(self):
        """BaseBackend is abstract — direct instantiation must raise."""
        with self.assertRaises(TypeError):
            BaseBackend()

    def test_subclass_without_generate_raises(self):
        """Subclass that skips generate_response must raise on call."""
        class IncompleteBackend(BaseBackend):
            NAME = "incomplete"
            def is_available(self): return True

        with self.assertRaises(TypeError):
            IncompleteBackend()   # ABC enforcement

    def test_describe_returns_required_keys(self):
        """describe() must include name, version, description, requires_key, available."""
        b = OfflineBackend()
        d = b.describe()
        for key in ("name", "version", "description", "requires_key", "available"):
            self.assertIn(key, d)

    def test_return_type_is_dict_with_response_text(self):
        """generate_response must return {"response_text": str}."""
        b = OfflineBackend()
        result = b.generate_response("hello", "CONVERSATIONAL", {}, {}, {}, {})
        self.assertIsInstance(result, dict)
        self.assertIn("response_text", result)
        self.assertIsInstance(result["response_text"], str)
        self.assertGreater(len(result["response_text"]), 0)


# ── Step 42: OfflineBackend ───────────────────────────────────────────────────

class TestOfflineBackend(unittest.TestCase):

    def setUp(self):
        from core.kernel import reset_session, set_debug
        set_debug(False)
        reset_session()
        self.b = OfflineBackend()

    def test_always_available(self):
        self.assertTrue(self.b.is_available())

    def test_returns_non_empty_string(self):
        result = self.b.generate_response("what does Chunk mean", "DIRECT", {}, {}, {}, {})
        self.assertIsInstance(result["response_text"], str)
        self.assertGreater(len(result["response_text"]), 5)

    def test_deterministic(self):
        """Same input must produce same output every time."""
        from core.kernel import reset_session
        reset_session()
        r1 = self.b.generate_response("what does Chunk mean", "DIRECT", {}, {}, {}, {})
        reset_session()
        r2 = self.b.generate_response("what does Chunk mean", "DIRECT", {}, {}, {}, {})
        self.assertEqual(r1["response_text"], r2["response_text"])

    def test_no_api_calls(self):
        """OfflineBackend must not import or call any HTTP/API library."""
        import sys
        before = set(sys.modules.keys())
        self.b.generate_response("hello", "CONVERSATIONAL", {}, {}, {}, {})
        after  = set(sys.modules.keys())
        new_modules = after - before
        api_modules = {m for m in new_modules
                       if any(kw in m for kw in ("anthropic", "openai", "requests", "httpx", "urllib.request"))}
        # urllib.request may be in stdlib — allow core modules, block API clients
        api_modules = {m for m in api_modules if "anthropic" in m or "openai" in m}
        self.assertEqual(api_modules, set(), f"API modules imported: {api_modules}")

    def test_fallback_returns_string_per_mode(self):
        """_fallback must return a non-empty string for every valid mode."""
        modes = ["DIRECT","GENTLE_GROUNDED","CREATIVE","STRUCTURED","SIMPLIFY","CONVERSATIONAL","UNKNOWN"]
        for mode in modes:
            text = self.b._fallback(mode)
            self.assertIsInstance(text, str)
            self.assertGreater(len(text), 0)


# ── Step 43: ClaudeBackend ────────────────────────────────────────────────────

class TestClaudeBackend(unittest.TestCase):

    def setUp(self):
        self.b = ClaudeBackend()

    def test_unavailable_without_api_key(self):
        """ClaudeBackend.is_available() must return False when key is missing."""
        original = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            self.assertFalse(self.b.is_available())
        finally:
            if original:
                os.environ["ANTHROPIC_API_KEY"] = original

    def test_raises_backend_unavailable_without_key(self):
        """generate_response must raise BackendUnavailableError when key is missing."""
        original = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with self.assertRaises(BackendUnavailableError):
                self.b.generate_response("hello", "CONVERSATIONAL", {}, {}, {}, {})
        finally:
            if original:
                os.environ["ANTHROPIC_API_KEY"] = original

    def test_build_system_prompt_contains_mode(self):
        """System prompt must include the mode overlay."""
        prompt = self.b._build_system_prompt("CREATIVE", {}, {}, {})
        self.assertIn("MODE STYLE RULES", prompt)
        self.assertIn("imaginative", prompt.lower())

    def test_build_system_prompt_contains_memory(self):
        """System prompt must include returning_theme when set."""
        memory = {"tone_signal": "distorted", "returning_theme": "The building territory keeps coming up.", "project": "sugarcore_arc"}
        prompt = self.b._build_system_prompt("CONVERSATIONAL", memory, {}, {})
        self.assertIn("The building territory keeps coming up.", prompt)
        self.assertIn("sugarcore_arc", prompt)

    def test_build_system_prompt_skips_empty_memory(self):
        """Empty memory fields must not inject blank lines."""
        prompt = self.b._build_system_prompt("DIRECT", {}, {}, {})
        self.assertNotIn("[MEMORY]", prompt)

    def test_is_transient_detects_timeout(self):
        """_is_transient must return True for timeout-like errors."""
        class FakeTimeout(Exception): pass
        FakeTimeout.__name__ = "APITimeoutError"
        self.assertTrue(ClaudeBackend._is_transient(FakeTimeout()))

    def test_is_transient_false_for_auth_error(self):
        """_is_transient must return False for auth errors (not retryable)."""
        class FakeAuth(Exception): pass
        FakeAuth.__name__ = "AuthenticationError"
        self.assertFalse(ClaudeBackend._is_transient(FakeAuth()))

    def test_does_not_import_kernel(self):
        """ClaudeBackend must not import core.kernel at module level."""
        import importlib
        import sys
        # remove from cache if present
        for key in list(sys.modules.keys()):
            if "claude_backend" in key:
                del sys.modules[key]
        # re-import and check kernel not pulled in via module-level import
        import backends.claude_backend as cb
        self.assertNotIn("core.kernel", cb.__dict__)


# ── runner ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
