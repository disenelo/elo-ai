"""
tests/test_wo073b_stream_and_deadline.py  WO-073b / card 0059

Five invariants. Each goes RED when the feature it guards is removed.

1. _groq_stream fires on_first_sentence before the last token arrives.
2. route_streaming(mode="groq") returns first_token_ms != 0.0
   (0.0 is the non-streaming fall-through that existed before this card).
3. Output identity: _groq_call and _groq_stream carry identical model/temperature/max_tokens payloads.
   The only difference must be {"stream": True}.
4. First-token deadline exceeded → hand-off fires, total wall clock < 4s (not the old 30s block).
5. When Groq 403s and Ollama handles the turn, the backend label must contain "ollama".
"""
import json
import os
import pathlib
import sys
import socket
import time
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "runtime"))

import backend_router as br


# ── SSE helpers ───────────────────────────────────────────────────────────────

def _sse_lines(*tokens, include_done=True):
    """Build a list of SSE byte-lines from token strings."""
    lines = []
    for tok in tokens:
        data = {"choices": [{"delta": {"content": tok}}]}
        lines.append(f"data: {json.dumps(data)}\n".encode())
    if include_done:
        lines.append(b"data: [DONE]\n")
    return lines


class _FakeResp:
    """Context-manager iterable that yields pre-built SSE lines."""
    def __init__(self, lines):
        self._lines = lines

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass

    def __iter__(self):
        return iter(self._lines)


# ── test class ────────────────────────────────────────────────────────────────

class TestGroqStreamAndDeadline(unittest.TestCase):

    def setUp(self):
        br._last_responses.clear()
        br._groq_quota_cooldown_until = 0.0
        os.environ.setdefault("GROQ_API_KEY", "test-key-not-real")
        os.environ.setdefault("ELO_GROQ_MODEL", "llama-3.3-70b-versatile")

    # ── 1: on_first_sentence fires mid-stream, not at end ─────────────────────

    def test_1_on_first_sentence_fires_before_last_token(self):
        """_groq_stream must call on_first_sentence before the final token arrives.

        Tokens: "Hello", " world", ". ", "And", " more."
        Sentence end matches after token 3 ("Hello world. ").
        Tokens 4-5 come after — callback must fire before them.
        RED when on_first_sentence block removed from _groq_stream.
        """
        tokens = ["Hello", " world", ". ", "And", " more."]
        lines = _sse_lines(*tokens)

        fired_sentences = []
        tokens_when_fired = []
        tokens_seen = []

        class _CountingResp:
            """Wrapper that records token index at on_first_sentence call time."""
            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

            def __iter__(self):
                for line in lines:
                    # Record which token this is before yielding
                    stripped = line.decode("utf-8", "replace").strip()
                    if stripped.startswith("data: ") and stripped[6:] != "[DONE]":
                        try:
                            delta = json.loads(stripped[6:])["choices"][0]["delta"].get("content", "")
                            if delta:
                                tokens_seen.append(delta)
                        except Exception:
                            pass
                    yield line

        def on_first(sentence):
            fired_sentences.append(sentence)
            tokens_when_fired.append(len(tokens_seen))

        with patch("urllib.request.urlopen", return_value=_CountingResp()):
            text, first_ms = br._groq_stream("sys", "user", on_first_sentence=on_first)

        self.assertTrue(fired_sentences, "on_first_sentence was never called — is the callback wired?")
        self.assertIn("Hello world.", fired_sentences[0])

        # fired before the last 2 tokens ("And", " more.") arrived
        self.assertLess(
            tokens_when_fired[0], len(tokens),
            f"on_first_sentence fired after token {tokens_when_fired[0]}, "
            f"but there were only {len(tokens)} tokens — must fire BEFORE the last one"
        )

    # ── 2: route_streaming(mode="groq") must return non-zero latency ──────────

    def test_2_route_streaming_groq_returns_nonzero_latency(self):
        """0.0 is the sentinel that the non-streaming fall-through ran.
        This must be != 0.0 — meaning _groq_stream was actually used.
        RED when the 'if mode == "groq"' branch is removed from route_streaming.
        """
        with patch.object(br, "_groq_available", return_value=True), \
             patch.object(br, "_groq_stream", return_value=("Hello world.", 45.3)), \
             patch.object(br, "_has_lore_drift", return_value=False):

            _text, backend, latency = br.route_streaming(
                "sys", "user", mode="groq", action="connect"
            )

        self.assertNotEqual(
            latency, 0.0,
            "latency == 0.0 means the non-streaming fall-through fired — _groq_stream was bypassed"
        )
        self.assertGreater(latency, 0.0)
        self.assertIn("groq", backend)

    # ── 3: output identity — _groq_call and _groq_stream send identical payloads

    def test_3_output_identity_same_payload_different_stream_flag(self):
        """_groq_call and _groq_stream must send identical model / temperature / max_tokens.
        The ONLY allowed difference is {"stream": True} in the streaming path.
        Assembled text must match (same bytes, modulo join whitespace).
        RED when max_tokens, temperature, or model is changed between the two paths.
        """
        MAX_TOKENS = 400
        RESPONSE = "Hello world. This is eLo."

        # Capture _groq_call payload via _json_post mock
        call_payload = {}

        def fake_json_post(url, payload, headers=None, timeout=None):
            call_payload.update(payload)
            return {"choices": [{"message": {"content": RESPONSE}}]}

        # Capture _groq_stream payload via urlopen mock; serve same text as SSE tokens
        stream_payload = {}
        stream_tokens = RESPONSE.split(" ")

        def fake_urlopen(req, timeout=None):
            stream_payload.update(json.loads(req.data.decode()))
            # Serve each word as a separate token (space-separated reassembly)
            lines = []
            for i, word in enumerate(stream_tokens):
                tok = word if i == 0 else " " + word
                lines.append(f"data: {json.dumps({'choices': [{'delta': {'content': tok}}]})}\n".encode())
            lines.append(b"data: [DONE]\n")
            return _FakeResp(lines)

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            stream_text, _ = br._groq_stream("sys", "user", max_tokens=MAX_TOKENS)

        with patch.object(br, "_json_post", side_effect=fake_json_post):
            call_text = br._groq_call("sys", "user", max_tokens=MAX_TOKENS)

        # Payload must agree on the identity fields
        self.assertEqual(
            call_payload.get("model"), stream_payload.get("model"),
            "model mismatch — eLo's voice changes between streaming and non-streaming calls"
        )
        self.assertEqual(
            call_payload.get("temperature"), stream_payload.get("temperature"),
            "temperature mismatch — output distribution changes based on transport"
        )
        self.assertEqual(
            call_payload.get("max_tokens"), stream_payload.get("max_tokens"),
            "max_tokens mismatch — eLo gets truncated in streaming mode"
        )

        # stream flag: present in streaming call, absent in blocking call
        self.assertTrue(stream_payload.get("stream"), "_groq_stream payload missing stream:true")
        self.assertFalse(call_payload.get("stream", False), "_groq_call must not set stream:true")

        # Assembled text must match
        self.assertEqual(
            call_text.strip(), stream_text.strip(),
            "assembled text differs between _groq_call and _groq_stream — eLo's output is transport-dependent"
        )

    # ── 4: first-token timeout → hand-off in < 4s (not old 30s) ──────────────

    def test_4_deadline_handoff_fires_under_4s(self):
        """When Groq doesn't respond within the first-token budget, hand-off must fire.
        Total wall clock < 4s — the old per-attempt block was 30s.
        RED if the socket.timeout is caught and re-raised as a 30s sleep.
        """
        def slow_urlopen(req, timeout=None):
            raise socket.timeout("simulated first-token timeout")

        t0 = time.monotonic()
        with patch("urllib.request.urlopen", side_effect=slow_urlopen), \
             patch.object(br, "_groq_available", return_value=True), \
             patch.object(br, "_ollama_available", return_value=True), \
             patch.object(br, "_ollama_stream", return_value=("Fallback.", 80.0)), \
             patch.object(br, "_has_lore_drift", return_value=False):

            _text, backend, _lat = br.route_streaming(
                "sys", "user", mode="groq", action="connect"
            )

        elapsed = time.monotonic() - t0

        self.assertLess(
            elapsed, 4.0,
            f"hand-off took {elapsed:.2f}s — the 30s blocking timeout is still in the path"
        )
        # Ollama was reached (not a mock fallback or silent empty)
        self.assertIn("ollama", backend.lower(),
                      f"expected ollama fallback, got backend '{backend}'")

    # ── 5: Groq 403 → Ollama label in backend string ──────────────────────────

    def test_5_groq_403_fallthrough_labelled_ollama(self):
        """When Groq returns 403 (Cloudflare or auth rejection) and Ollama handles
        the turn, the backend string must contain 'ollama'.
        David must never have to infer from the writing that the 8b brain answered.
        RED if the Groq exception is swallowed and the label is left as "groq".
        """
        def groq_403(system_prompt, user_input, max_tokens=None, on_first_sentence=None):
            raise urllib.error.HTTPError(
                url="https://api.groq.com/openai/v1/chat/completions",
                code=403, msg="Forbidden", hdrs=None, fp=None,
            )

        with patch.object(br, "_groq_available", return_value=True), \
             patch.object(br, "_groq_stream", side_effect=groq_403), \
             patch.object(br, "_ollama_available", return_value=True), \
             patch.object(br, "_ollama_stream", return_value=("Hello.", 120.0)), \
             patch.object(br, "_has_lore_drift", return_value=False):

            _text, backend, _lat = br.route_streaming(
                "sys", "user", mode="groq", action="connect"
            )

        self.assertIn(
            "ollama", backend.lower(),
            f"backend '{backend}' does not contain 'ollama' — "
            "a Groq-403 turn is silently mislabelled, David can't tell who answered"
        )


if __name__ == "__main__":
    unittest.main()
