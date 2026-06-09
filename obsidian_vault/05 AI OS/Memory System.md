---
type: memory
domain: ai-os
tags: [memory, obsidian, loader, vault, persistent]
version: 0.1
---

# Memory System

The Obsidian-based persistent memory for eLo AI OS. Markdown files are the source of truth.

## Architecture

Obsidian Vault → memory_loader.py → memory_pack.json → eLo Kernel Context → Response

## Memory types

- long_term — permanent facts (priority 1 — always load)
- character — entity profiles (priority 1)
- personal — user patterns (priority 1)
- project — project state (priority 2 — topic match)
- world — lore and locations (priority 2)
- technical — architecture decisions (priority 3 — on request)

## Note format

Every memory note requires: type, domain, tags, version in frontmatter.

## Connections

- [[eLo AI OS]]
- [[Kernel]]
- [[eLo Vault]]
