#!/usr/bin/env python3
"""
INTENT CHECK gate — reads David's message, maps it to source/WO/evidence files,
and outputs a structured digest for the Board.

Usage:
    python3 engineering/hooks/intent_align_gate.py "David's message here"
    echo "David's message" | python3 engineering/hooks/intent_align_gate.py
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDEX_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "topic_index.json")
EXCERPT_LINES = 50


def load_index():
    with open(INDEX_PATH) as f:
        return json.load(f)


def read_excerpt(rel_path):
    if not rel_path:
        return None
    abs_path = os.path.join(REPO_ROOT, rel_path)
    if not os.path.exists(abs_path):
        return f"[file not found: {rel_path}]"
    if os.path.isdir(abs_path):
        files = [fn for fn in os.listdir(abs_path) if fn.endswith(".md")]
        if not files:
            return f"[empty directory: {rel_path}]"
        abs_path = os.path.join(abs_path, sorted(files)[-1])
        rel_path = os.path.relpath(abs_path, REPO_ROOT)
    try:
        with open(abs_path) as f:
            lines = f.readlines()
        excerpt = "".join(lines[:EXCERPT_LINES]).strip()
        if len(lines) > EXCERPT_LINES:
            excerpt += f"\n... [{len(lines) - EXCERPT_LINES} more lines]"
        return f"[{rel_path}]\n{excerpt}"
    except Exception as e:
        return f"[error reading {rel_path}: {e}]"


def match_topics(message, index):
    msg_lower = message.lower()
    matched = {}
    for keyword, entry in index.items():
        if keyword.lower() in msg_lower:
            matched[keyword] = entry
    return matched


def format_digest(message, matched, index):
    lines = ["INTENT CHECK:"]
    lines.append(f"- David's message: {message.strip()}")

    if not matched:
        lines.append("- Relevant source: INTENT CHECK: No source mapping found for this topic.")
        return "\n".join(lines)

    for keyword, entry in matched.items():
        lines.append(f"\n--- Topic: {keyword} ---")

        source = entry.get("source")
        if source:
            excerpt = read_excerpt(source)
            lines.append(f"- Relevant source: {excerpt}")
        else:
            lines.append("- Relevant source: none mapped")

        wo = entry.get("wo")
        if wo:
            abs_wo = os.path.join(REPO_ROOT, wo)
            if os.path.exists(abs_wo):
                lines.append(f"- Code state: {wo}")
            else:
                lines.append(f"- Code state: [WO not found: {wo}]")
        else:
            lines.append("- Code state: no WO mapped")

        evidence = entry.get("evidence")
        if evidence:
            abs_ev = os.path.join(REPO_ROOT, evidence)
            if os.path.exists(abs_ev):
                ev_excerpt = read_excerpt(evidence)
                lines.append(f"- Test evidence: {ev_excerpt}")
            else:
                lines.append(f"- Test evidence: [evidence not yet filed: {evidence}]")
        else:
            lines.append("- Test evidence: none mapped")

    return "\n".join(lines)


def main():
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
    elif not sys.stdin.isatty():
        message = sys.stdin.read()
    else:
        print("Usage: intent_align_gate.py <message>")
        sys.exit(1)

    index = load_index()
    matched = match_topics(message, index)
    digest = format_digest(message, matched, index)
    print(digest)


if __name__ == "__main__":
    main()
