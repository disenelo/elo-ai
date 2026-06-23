"""
tools/github_agent.py — GitHub repo status via REST API.

Free — 5000 req/hr unauthenticated, more with GITHUB_TOKEN.
Set GITHUB_REPO=owner/repo in .env for a default repo.
Set GITHUB_TOKEN=ghp_... for higher rate limits.
"""
from __future__ import annotations

import os
import re

_TOKEN     = os.environ.get("GITHUB_TOKEN", "")
_DEFAULT   = os.environ.get("GITHUB_REPO", "")   # e.g. "disenelo/elo-planet"
_BASE      = "https://api.github.com"


def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if _TOKEN:
        h["Authorization"] = f"Bearer {_TOKEN}"
    return h


def _get(path: str) -> dict | list | None:
    try:
        import httpx
        r = httpx.get(f"{_BASE}{path}", headers=_headers(), timeout=8.0)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def _extract_repo(query: str) -> str:
    """Extract owner/repo from query or fall back to default."""
    match = re.search(r"([\w\-]+/[\w\-\.]+)", query)
    if match:
        return match.group(1)
    return _DEFAULT


def get_status(repo: str) -> str:
    """Return a one-line status for the repo."""
    if not repo:
        return "GITHUB: no repo set — add GITHUB_REPO=owner/repo to .env"

    # commits
    commits = _get(f"/repos/{repo}/commits?per_page=1")
    last_commit = ""
    if commits and isinstance(commits, list):
        c = commits[0]
        msg   = c.get("commit", {}).get("message", "").split("\n")[0][:60]
        author = c.get("commit", {}).get("author", {}).get("name", "")
        last_commit = f"last commit: {msg} by {author}"

    # open PRs
    prs = _get(f"/repos/{repo}/pulls?state=open&per_page=5")
    pr_count = len(prs) if isinstance(prs, list) else "?"

    # open issues
    info = _get(f"/repos/{repo}")
    issue_count = info.get("open_issues_count", "?") if isinstance(info, dict) else "?"

    parts = [f"GITHUB {repo}:"]
    if last_commit:
        parts.append(last_commit)
    parts.append(f"{pr_count} open PR(s), {issue_count} open issue(s)")
    return " | ".join(parts)


def agent(query: str) -> str:
    repo = _extract_repo(query)
    return get_status(repo)
