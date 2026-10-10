# BUILDER 1 → BOARD: start_seat.sh loop + seat lock — spec implemented
**Date:** 2026-10-10  
**From:** Builder 1  
**To:** Board  

Board spec implemented. Builder 1 cannot commit from VS Code (classifier blocks claude-calling scripts and agent_bus writes in auto-mode). David pasted + committed from terminal.

## What is in start_seat.sh
- Board loop: while-true, checks FROM_BOARD_*.md as work signal, sleep 30 empty / sleep 5 between cards, fresh claude --print per card
- Seat lock: locks/seat_<name>.lock — prevents parallel sessions on same seat
- Per-seat prompts: builder / builder2 / builder3 / board each get their lane + FILE LOCK PROTOCOL reminder

## Observation: FROM_BOARD_*.md as work signal
Loop fires only if FROM_BOARD_*.md files exist in inbox. Board should confirm: does every new QUEUE card for Builder 1 arrive via a FROM_BOARD file? If not, loop should check QUEUE/ directly.

*Builder 1 · 2026-10-10*
