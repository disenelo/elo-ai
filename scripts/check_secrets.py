#!/usr/bin/env python3
"""
scripts/check_secrets.py — WO-CANON-XXVII §C / Vol XXIII OQ-3.6.3
Pre-commit secret check. Rejects a staged diff containing:
  - API-key-shaped literals (OpenAI sk-, Google AIza, Bearer + long token, etc.)
  - Tracked .env files

Usage:
    python scripts/check_secrets.py                 # checks staged diff (git diff --cached)
    python scripts/check_secrets.py --fixture FILE  # check a plain text file (for testing)
    python scripts/check_secrets.py --help

Returns exit code 1 (reject) if any secret-shaped content is found.
Must be standalone so tests can call it on fixtures.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


# ── patterns that match real API-key shapes ────────────────────────────────────
# Each is (name, compiled_regex). A staged line (+/-) matching any of these is rejected.

_SECRET_PATTERNS: list[tuple[str, re.Pattern]] = [
    # OpenAI sk- key — 51 chars, starts with sk-
    ("OpenAI API key",      re.compile(r'\bsk-[A-Za-z0-9]{48,}\b')),
    # OpenAI project key sk-proj-
    ("OpenAI project key",  re.compile(r'\bsk-proj-[A-Za-z0-9_-]{40,}\b')),
    # Google AIzaSy key
    ("Google API key",      re.compile(r'\bAIzaSy[A-Za-z0-9_-]{33}\b')),
    # Bearer token (long, ≥ 40 chars, not a placeholder)
    ("Bearer token",        re.compile(r'Bearer\s+[A-Za-z0-9+/=_-]{40,}')),
    # Anthropic keys
    ("Anthropic API key",   re.compile(r'\bsk-ant-[A-Za-z0-9_-]{40,}\b')),
    # Groq keys
    ("Groq API key",        re.compile(r'\bgsk_[A-Za-z0-9]{52}\b')),
    # ElevenLabs
    ("ElevenLabs key",      re.compile(r'\b[a-f0-9]{32}\b')),  # narrow: 32-char hex (sha-like)
    # Generic high-entropy assignment (fallback): FOO_API_KEY = "long_string"
    ("Generic API key assignment", re.compile(
        r'(?:API_KEY|SECRET|TOKEN|PASSWORD)\s*=\s*["\'][A-Za-z0-9+/=_-]{30,}["\']',
        re.IGNORECASE
    )),
]

# File paths that should never be tracked
_BLOCKED_TRACKED_FILES: list[re.Pattern] = [
    re.compile(r'^\.env$'),
    re.compile(r'^\.env\.[a-z]+$'),  # .env.local, .env.production, etc.
    re.compile(r'\.pem$'),
    re.compile(r'\.key$'),
]


def _staged_diff() -> str:
    """Return the staged diff as a string, or empty string on error."""
    try:
        return subprocess.check_output(
            ["git", "diff", "--cached", "--unified=0"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _staged_files() -> list[str]:
    """Return list of staged (added/modified) file paths."""
    try:
        out = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=AM"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return out.strip().splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def check_diff(diff_text: str) -> list[dict]:
    """Scan diff_text for secret-shaped literals on added lines (+).

    Returns list of {"name": pattern_name, "line": n, "excerpt": "..."}.
    """
    findings: list[dict] = []
    for n, line in enumerate(diff_text.splitlines(), 1):
        if not line.startswith("+"):
            continue  # only added lines
        if line.startswith("+++"):
            continue  # file header
        for name, pat in _SECRET_PATTERNS:
            m = pat.search(line)
            if m:
                # Truncate the match in the excerpt — don't log the full secret
                start, end = m.span()
                excerpt = line[start:start + 20] + "…"
                findings.append({"name": name, "line": n, "excerpt": excerpt})
                break  # one finding per line
    return findings


def check_tracked_files(file_paths: list[str]) -> list[str]:
    """Return any staged file paths that match the blocked patterns."""
    blocked: list[str] = []
    for fp in file_paths:
        name = Path(fp).name
        if any(pat.match(name) for pat in _BLOCKED_TRACKED_FILES):
            blocked.append(fp)
    return blocked


def run_checks(diff_text: str | None = None,
               file_paths: list[str] | None = None) -> dict:
    """Run both checks. Returns {"diff_findings": [...], "blocked_files": [...]}.

    If diff_text/file_paths are None, they are read from git staging area.
    """
    if diff_text is None:
        diff_text = _staged_diff()
    if file_paths is None:
        file_paths = _staged_files()

    return {
        "diff_findings":  check_diff(diff_text),
        "blocked_files":  check_tracked_files(file_paths),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Pre-commit secret check — WO-CANON-XXVII §C")
    parser.add_argument("--fixture", help="Check a plain text file instead of staged diff")
    args = parser.parse_args()

    if args.fixture:
        text = Path(args.fixture).read_text(encoding="utf-8")
        results = run_checks(diff_text=text, file_paths=[])
    else:
        results = run_checks()

    ok = True
    if results["blocked_files"]:
        ok = False
        print("🔴 BLOCKED: tracked .env / credential file(s):")
        for f in results["blocked_files"]:
            print(f"   {f}")

    if results["diff_findings"]:
        ok = False
        print("🔴 BLOCKED: secret-shaped literal(s) in staged diff:")
        for f in results["diff_findings"]:
            print(f"   line {f['line']}: [{f['name']}] {f['excerpt']}")

    if ok:
        print("✅ Secret check passed — no secrets detected in staged diff")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
