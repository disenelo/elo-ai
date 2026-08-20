"""
self_improvement/finetune — WO-104: understudy fine-tune pipeline.

Ruling F [DAVID 2026-08-10]: style-only weight learning is allowed.
Verification and L3-override deltas are collected but MUST NOT train.

Modules:
    tagger      classify delta_cause for every shadow row; backfill legacy rows
    trainer     refuses on any untagged row; filters to `style` only; trains adapter
    adapter     versioned adapter files; delete-to-revert
    pipeline    end-to-end: tag → filter → train → eval → gate → report
"""
