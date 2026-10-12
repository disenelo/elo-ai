# WO-B2-0009 — Dream image generation: trigger on high-significance dreams
**Seat:** Builder 2  
**Priority:** P0 — demo milestone  
**Date:** 2026-10-11

## What
248 dreams in dream_journal.jsonl. All have image_ref: null. image_gen_agent.py pipeline exists but is failing silently.

Builder 2 owns the dream faculty. Diagnose why image generation is not firing. If the DALL-E call is failing (key, model name, endpoint), fix it. If the trigger condition is wrong, fix it. Dreams with significance > 0.5 should produce an image.

## Done when
At least one dream has image_ref pointing to a real file. File to Board: dream entry before (image_ref: null) and after (image_ref: path), confirm file exists on disk.
