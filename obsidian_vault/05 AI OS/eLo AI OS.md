---
type: memory
domain: ai-os
tags: [ai-os, system, python, kernel, stable]
version: 1.0
---

# eLo AI OS

The Python-based cognitive operating system for eLo. Offline-first, deterministic routing, multi-backend generation.

## Current status

v1.0 stable. Kernel frozen. Repository: github.com/disenelo/elo-ai

## Architecture

- Kernel: classify → route → generate → filter (frozen, never modified)
- Backends: Claude API / Mock / Offline deterministic / future local LLM
- Personality Engine: mode profiles + expression rules + philosophical control
- Memory: Obsidian vault + Python loader

## Key invariant

The kernel is the only decision-maker. Memory, emotion, state — passive inputs only.

## Connections

- [[eLo]]
- [[Kernel]]
- [[Personality Engine]]
- [[Memory System]]
