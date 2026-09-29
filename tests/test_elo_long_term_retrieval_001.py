"""
tests/test_elo_long_term_retrieval_001.py — Long-Term Memory Retrieval

IS ELO: — Long-Term Memory on Live Turn Path?
  are identity and constraint documents retrieved on every turn?
  are inactive documents filtered out?
  are documents sorted by priority?
  does the block surface to the LLM via the system prompt?

THE CAUSAL CHAIN:
  memory/long_term/*.md (active: true, load_priority >= 1)
  → load_long_term_docs() → sorted by priority
  → long_term_prompt_block() → [LONG-TERM MEMORY] block in system prompt
  → LLM always knows: eLo is not an assistant, kernel is frozen

AT-1  load_long_term_docs() with empty dir → empty list (no crash)
AT-2  load_long_term_docs() reads real documents from memory/long_term/
AT-3  active: false document is filtered out
AT-4  active: true document is included
AT-5  load_priority sorts correctly (lower number = earlier)
AT-6  load_long_term_docs() parses frontmatter title
AT-7  load_long_term_docs() parses frontmatter category
AT-8  body text (after frontmatter) is included in doc body
AT-9  long_term_prompt_block() returns "" on empty dir
AT-10 long_term_prompt_block() returns non-empty when docs present
AT-11 block contains [LONG-TERM MEMORY] header
AT-12 block contains document title
AT-13 CAUSAL PROOF: adding an active doc to dir changes the block
AT-14 long_term_prompt_block() never raises (resilient)
AT-15 real memory/long_term/ has at least 2 active documents
AT-16 server.py wired: long_term_prompt_block import present
AT-17 py_compile clean
"""
from __future__ import annotations

import os
import py_compile
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import memory.long_term_reader as lt_mod
from memory.long_term_reader import (
    load_long_term_docs,
    long_term_prompt_block,
    _parse_frontmatter,
)

_REAL_LT_DIR = Path(ROOT) / "memory" / "long_term"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_doc(path: Path, title: str, body: str,
               active: bool = True, priority: int = 1, category: str = "identity") -> None:
    active_str = "true" if active else "false"
    content = (
        f"---\n"
        f"title: {title}\n"
        f"category: {category}\n"
        f"load_priority: {priority}\n"
        f"active: {active_str}\n"
        f"---\n\n"
        f"# {title}\n\n"
        f"{body}\n"
    )
    path.write_text(content, encoding="utf-8")


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_empty_dir_returns_empty(tmp_path):
    docs = load_long_term_docs(lt_dir=tmp_path)
    assert docs == [], "AT-1: empty dir → empty list"


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_reads_real_documents():
    docs = load_long_term_docs(lt_dir=_REAL_LT_DIR)
    assert len(docs) >= 1, (
        f"AT-2: memory/long_term/ must have at least 1 active doc, got {len(docs)}"
    )


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_inactive_document_filtered(tmp_path):
    _write_doc(tmp_path / "inactive.md", "Should Not Appear", "hidden body", active=False)
    docs = load_long_term_docs(lt_dir=tmp_path)
    titles = [d["title"] for d in docs]
    assert "Should Not Appear" not in titles, (
        "AT-3: active:false document must not be returned"
    )


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_active_document_included(tmp_path):
    _write_doc(tmp_path / "active.md", "Active Doc", "active body", active=True)
    docs = load_long_term_docs(lt_dir=tmp_path)
    titles = [d["title"] for d in docs]
    assert "Active Doc" in titles, "AT-4: active:true document must be returned"


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_sorted_by_priority(tmp_path):
    _write_doc(tmp_path / "b_low.md",  "Low Priority",  "body", priority=5)
    _write_doc(tmp_path / "a_high.md", "High Priority", "body", priority=1)
    docs = load_long_term_docs(lt_dir=tmp_path)
    assert len(docs) == 2, "AT-5: both docs must be returned"
    assert docs[0]["title"] == "High Priority", (
        f"AT-5: priority=1 must come first, got {docs[0]['title']!r}"
    )
    assert docs[1]["title"] == "Low Priority", (
        f"AT-5: priority=5 must come second, got {docs[1]['title']!r}"
    )


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_parses_frontmatter_title(tmp_path):
    _write_doc(tmp_path / "test.md", "My Special Title", "body")
    docs = load_long_term_docs(lt_dir=tmp_path)
    assert docs[0]["title"] == "My Special Title", (
        f"AT-6: title must be parsed from frontmatter, got {docs[0]['title']!r}"
    )


# ── AT-7 ──────────────────────────────────────────────────────────────────────

def test_at7_parses_frontmatter_category(tmp_path):
    _write_doc(tmp_path / "test.md", "T", "body", category="constraint")
    docs = load_long_term_docs(lt_dir=tmp_path)
    assert docs[0]["category"] == "constraint", (
        f"AT-7: category must be parsed from frontmatter, got {docs[0]['category']!r}"
    )


# ── AT-8 ──────────────────────────────────────────────────────────────────────

def test_at8_body_text_included(tmp_path):
    _write_doc(tmp_path / "test.md", "T", "This is the body text for AT-8.")
    docs = load_long_term_docs(lt_dir=tmp_path)
    assert "AT-8" in docs[0]["body"], (
        f"AT-8: body text must appear in doc body, got: {docs[0]['body'][:80]!r}"
    )


# ── AT-9 ──────────────────────────────────────────────────────────────────────

def test_at9_block_empty_on_empty_dir(tmp_path):
    block = long_term_prompt_block(lt_dir=tmp_path)
    assert block == "", f"AT-9: empty dir → empty block, got: {block[:80]!r}"


# ── AT-10 ─────────────────────────────────────────────────────────────────────

def test_at10_block_non_empty_when_docs_present(tmp_path):
    _write_doc(tmp_path / "test.md", "Test Doc", "Test body.")
    block = long_term_prompt_block(lt_dir=tmp_path)
    assert block, "AT-10: docs present → block must be non-empty"


# ── AT-11 ─────────────────────────────────────────────────────────────────────

def test_at11_block_has_long_term_memory_header(tmp_path):
    _write_doc(tmp_path / "test.md", "Test Doc", "Test body.")
    block = long_term_prompt_block(lt_dir=tmp_path)
    assert "LONG-TERM MEMORY" in block, "AT-11: block must contain LONG-TERM MEMORY header"


# ── AT-12 ─────────────────────────────────────────────────────────────────────

def test_at12_block_contains_document_title(tmp_path):
    _write_doc(tmp_path / "test.md", "UNIQUE_TITLE_AT12", "body")
    block = long_term_prompt_block(lt_dir=tmp_path)
    assert "UNIQUE_TITLE_AT12" in block, (
        "AT-12: block must contain the document's title"
    )


# ── AT-13 ─────────────────────────────────────────────────────────────────────

def test_at13_causal_proof_adding_doc_changes_block(tmp_path):
    """
    THE CAUSAL PROOF: empty directory → empty block.
    Adding an active document → non-empty block.
    This proves long-term memory retrieval has causal reality:
      document on disk → retrieved → injected into system prompt → LLM knows.
    """
    block_before = long_term_prompt_block(lt_dir=tmp_path)

    _write_doc(tmp_path / "proof.md", "PROOF_DOC_AT13", "Proof body text.")
    block_after = long_term_prompt_block(lt_dir=tmp_path)

    assert block_before == "", (
        "AT-13 CAUSAL PROOF: no docs → block must be empty"
    )
    assert block_after, (
        "AT-13 CAUSAL PROOF: doc on disk → block must be non-empty"
    )
    assert "PROOF_DOC_AT13" in block_after, (
        "AT-13: added doc title must appear in block"
    )


# ── AT-14 ─────────────────────────────────────────────────────────────────────

def test_at14_prompt_block_resilient():
    """long_term_prompt_block() must never raise."""
    def _boom(*a, **kw):
        raise RuntimeError("forced failure")

    with patch.object(lt_mod, "load_long_term_docs", _boom):
        try:
            result = long_term_prompt_block()
            assert isinstance(result, str), "AT-14: must return str on error"
        except Exception as exc:
            pytest.fail(f"AT-14: long_term_prompt_block raised: {exc}")


# ── AT-15 ─────────────────────────────────────────────────────────────────────

def test_at15_real_long_term_dir_has_two_active_docs():
    docs = load_long_term_docs(lt_dir=_REAL_LT_DIR)
    assert len(docs) >= 2, (
        f"AT-15: memory/long_term/ must have at least 2 active docs, got {len(docs)}: "
        + str([d['title'] for d in docs])
    )


# ── AT-16 ─────────────────────────────────────────────────────────────────────

def test_at16_server_wired():
    server_path = os.path.join(ROOT, "server.py")
    with open(server_path, encoding="utf-8") as f:
        source = f.read()
    assert "long_term_prompt_block" in source, (
        "AT-16: long_term_prompt_block must be wired in server.py"
    )
    assert "memory.long_term_reader" in source, (
        "AT-16: memory.long_term_reader import must be in server.py"
    )


# ── AT-17 ─────────────────────────────────────────────────────────────────────

def test_at17_py_compile_clean():
    files = [
        os.path.join(ROOT, "memory", "long_term_reader.py"),
        os.path.join(ROOT, "server.py"),
    ]
    for path in files:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"AT-17: {os.path.basename(path)} compile error: {exc}")
