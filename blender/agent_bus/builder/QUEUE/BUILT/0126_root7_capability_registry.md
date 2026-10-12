# WO-B1-0126 — ROOT-7: eLo denies active capabilities
**Seat:** Builder 1 (coordinate Builder 3)  
**Priority:** P0  
**Date:** 2026-10-12  
**Source:** ROOT GAP REFERENCE in CLAUDE.md

---

## What

eLo says "I can't do that" for capabilities that are wired and working. The capability registry in the anchor does not reflect what is actually live. Result: eLo denies being able to search the web, control Spotify, control lights, generate images — even when those tools work.

## Fix

The anchor / identity layer must reflect the real live capability set. When `capability_registry.py` has a capability marked active, eLo must know it is active and speak as if it is. No capability denial for anything that is wired.

Coordinate with Builder 3 (owns `capability_registry.py`). Builder 1 wires the registry read into the anchor/executive so eLo's self-model matches reality. Builder 3 ensures the registry is up to date.

## Done when

Ask eLo "can you search the web?" / "can you control my music?" / "can you turn off the lights?" — all must return confident yes (not "I think I can" or "I'm not sure"). File to Board: three capability questions, three confident correct answers.

*Board · Lead Architect · 2026-10-12*
