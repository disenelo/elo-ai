---
memory_type: long_term
category: constraint
title: Kernel is frozen at v1.0
confidence: high
created: 2026-06-09
updated: 2026-06-09
version: 1
tags: [long-term, constraint, kernel, technical]
linked_to: [system-invariants]
load_priority: 1
active: true
---

# Kernel is frozen at v1.0

The cognitive kernel (core/kernel.py) is stable and must not be modified.
Routing, mode selection, loop detection, and classification are frozen.
Only expression, prompt, and backend layers may be changed.
Any kernel change requires a MAJOR version increment and full audit.
