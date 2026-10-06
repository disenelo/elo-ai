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
        # WO-039-F3: return "" so tool_router skips context injection (no leak into LLM).
        # An error string here becomes [CONTEXT: GITHUB_REPO not set...] which the LLM
        # paraphrases directly into the reply — dev-context leak.
        return ""

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


# B3 2026-10-06: David's repos live on this Mac and are ahead of GitHub (elo-ai's
# origin was 1216 commits behind). "Last commit on my elo-ai repo" means the local one.
_LOCAL_REPOS = {
    "elo-ai":         os.path.expanduser("~/elo-ai"),
    "elo ai":         os.path.expanduser("~/elo-ai"),
    "elo-planet":     os.path.expanduser("~/eLo-Planet"),
    "elo planet":     os.path.expanduser("~/eLo-Planet"),
    "desktop buddy":  os.path.expanduser("~/Desktop/Output/DISENELO-eLoDesktopBuddy"),
    "desktopbuddy":   os.path.expanduser("~/Desktop/Output/DISENELO-eLoDesktopBuddy"),
    "presence":       os.path.expanduser("~/Desktop/Output/DISENELO-eLoDesktopBuddy"),
}


def _git(path: str, *args: str) -> str:
    import subprocess
    r = subprocess.run(["git", "-C", path, *args], capture_output=True, text=True, timeout=10)
    return r.stdout.strip() if r.returncode == 0 else ""


def local_last_commit(query: str) -> str | None:
    """'Last commit on elo-ai: "<subject>" — 2 minutes ago.' for a known local
    repo named in the query (plus how far GitHub is behind), else None."""
    q = query.lower()
    name = next((k for k in _LOCAL_REPOS if k in q), None)
    if not name or not os.path.isdir(_LOCAL_REPOS[name]):
        return None
    path = _LOCAL_REPOS[name]
    line = _git(path, "log", "-1", "--format=%s\x1f%cr")
    if not line:
        return None
    subject, ago = line.split("\x1f", 1)
    label = os.path.basename(path)
    out = f"Last commit on {label}: \u201c{subject[:120]}\u201d — {ago}."
    behind = _git(path, "rev-list", "--count", "@{upstream}..HEAD")
    if behind.isdigit() and int(behind) > 0:
        out += f" GitHub's {behind} commit{'s' if behind != '1' else ''} behind."
    return out


def agent(query: str) -> str:
    local = local_last_commit(query)
    if local:
        return local
    repo = _extract_repo(query)
    return get_status(repo)
