#!/usr/bin/env python3
"""
diag_claude_transport.py — Claude worker transport diagnostic (card 0058)

Run from external shell:
  python3 ~/elo-ai/engineering/diag_claude_transport.py

Progressively tests each flag combination and reports what the orchestrator
actually sends vs what the known-good invocations do.
Each step prints: argv · exit_code · stdout_bytes · stderr_bytes · first_100_bytes_of_each.
"""
from __future__ import annotations
import json, os, pathlib, subprocess, sys, time, shutil, textwrap

ROOT = pathlib.Path.home() / "elo-ai"

CLAUDE = shutil.which("claude") or "/opt/homebrew/bin/claude"
SHORT_PROMPT = "Reply with exactly one word: hello"
DIAG_LOG = ROOT / "engineering" / "diag_transport_log.json"

results: list[dict] = []

def run_step(label: str, cmd: list[str], stdin_text: str | None = None, env_extra: dict | None = None) -> dict:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)

    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            input=stdin_text,
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        elapsed = round(time.time() - t0, 2)
        out_preview = proc.stdout[:200].replace("\n", "\\n")
        err_preview = proc.stderr[:200].replace("\n", "\\n")
        r = {
            "step":         label,
            "argv":         cmd,
            "stdin":        stdin_text[:80] if stdin_text else None,
            "exit_code":    proc.returncode,
            "stdout_bytes": len(proc.stdout),
            "stderr_bytes": len(proc.stderr),
            "stdout_head":  out_preview,
            "stderr_head":  err_preview,
            "elapsed_s":    elapsed,
            "ok":           proc.returncode == 0 and len(proc.stdout) > 0,
        }
    except subprocess.TimeoutExpired:
        r = {"step": label, "argv": cmd, "exit_code": -1, "ok": False, "error": "TIMEOUT 30s"}
    except Exception as e:
        r = {"step": label, "argv": cmd, "exit_code": -1, "ok": False, "error": str(e)}

    status = "✅ OK" if r.get("ok") else "❌ FAIL"
    print(f"\n{status}  [{label}]")
    print(f"  argv:    {' '.join(cmd)[:120]}")
    if stdin_text:
        print(f"  stdin:   {stdin_text[:60]}")
    print(f"  rc={r.get('exit_code')}  stdout={r.get('stdout_bytes',0)}B  stderr={r.get('stderr_bytes',0)}B  elapsed={r.get('elapsed_s')}s")
    if r.get("stdout_head"):
        print(f"  stdout:  {r['stdout_head'][:100]}")
    if r.get("stderr_head"):
        print(f"  stderr:  {r['stderr_head'][:100]}")
    if r.get("error"):
        print(f"  error:   {r['error']}")

    results.append(r)
    return r


def load_api_key() -> str:
    for raw in (ROOT / ".env").read_text().splitlines():
        line = raw.strip()
        if line.startswith("ANTHROPIC_API_KEY=") and not line.startswith("#"):
            val = line.split("=", 1)[1].strip().strip('"').strip("'")
            if val:
                return val
    return ""


def make_orchestrator_prompt() -> str:
    """Exact prompt the orchestrator would build for a real Builder card."""
    autorun = (ROOT / "blender" / "agent_bus" / "AUTORUN_PROTOCOL.md").read_text()[:3000]
    seat_ep = (ROOT / "blender" / "agent_bus" / "_SEAT_EPISTEMIC_PROTOCOL.md")
    seat_contract = seat_ep.read_text()[:3000] if seat_ep.exists() else ""
    card_text = "Card: test card. Write the string OK to /tmp/elo_probe_result.txt"
    return textwrap.dedent(f"""
    You are the builder implementation seat in the eLo OS project.
    Project root: {ROOT}

    AUTORUN PROTOCOL:
    {autorun}

    SEAT CONTRACT:
    {seat_contract}

    WORK CARD:
    {card_text}

    Write the string {{"status":"DONE","evidence":"probe complete"}} to /tmp/elo_probe_result.txt
    """).strip()


print(f"═══ Claude transport diagnostic ═══")
print(f"CLAUDE binary: {CLAUDE}")
print(f"cwd:           {ROOT}")
print(f"env PATH:      {os.environ.get('PATH','')[:120]}")
print(f"ANTHROPIC_API_KEY in env: {'YES' if 'ANTHROPIC_API_KEY' in os.environ else 'NO'}")

api_key = load_api_key()
print(f"ANTHROPIC_API_KEY from .env: {'SET (' + api_key[:8] + '...)' if api_key else 'MISSING'}")

# ── Step 1: Exact match of known-good invocation 1 ──────────────────────────
run_step(
    "1_known_good_inline",
    [CLAUDE, "-p", SHORT_PROMPT, "--dangerously-skip-permissions"],
)

# ── Step 2: Known-good via stdin ─────────────────────────────────────────────
run_step(
    "2_known_good_stdin",
    [CLAUDE, "-p", "--dangerously-skip-permissions"],
    stdin_text=SHORT_PROMPT,
)

# ── Step 3: Add --output-format stream-json ───────────────────────────────────
run_step(
    "3_stream_json_inline",
    [CLAUDE, "-p", SHORT_PROMPT, "--dangerously-skip-permissions", "--output-format", "stream-json"],
)

# ── Step 4: stream-json via stdin ─────────────────────────────────────────────
run_step(
    "4_stream_json_stdin",
    [CLAUDE, "-p", "--dangerously-skip-permissions", "--output-format", "stream-json"],
    stdin_text=SHORT_PROMPT,
)

# ── Step 5: Add --add-dir (the extra flag the orchestrator uses) ──────────────
run_step(
    "5_add_dir_inline",
    [CLAUDE, "-p", SHORT_PROMPT, "--dangerously-skip-permissions", "--output-format", "stream-json", "--add-dir", str(ROOT)],
)

# ── Step 6: Orchestrator's FULL prompt length via inline arg ──────────────────
big_prompt = make_orchestrator_prompt()
print(f"\n[6_full_prompt_inline] prompt length: {len(big_prompt)} chars")
run_step(
    "6_full_prompt_inline",
    [CLAUDE, "-p", big_prompt, "--dangerously-skip-permissions", "--output-format", "stream-json", "--add-dir", str(ROOT)],
)

# ── Step 7: Same prompt via stdin (proposed fix) ──────────────────────────────
run_step(
    "7_full_prompt_stdin",
    [CLAUDE, "-p", "--dangerously-skip-permissions", "--output-format", "stream-json"],
    stdin_text=big_prompt,
)

# ── Step 8: Same prompt stdin + explicit ANTHROPIC_API_KEY from .env ──────────
run_step(
    "8_stdin_plus_env_key",
    [CLAUDE, "-p", "--dangerously-skip-permissions", "--output-format", "stream-json"],
    stdin_text=big_prompt,
    env_extra={"ANTHROPIC_API_KEY": api_key} if api_key else {},
)

# ── Step 9: No --output-format, stdin ─────────────────────────────────────────
run_step(
    "9_no_format_stdin",
    [CLAUDE, "-p", "--dangerously-skip-permissions"],
    stdin_text=big_prompt,
)

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n═══ Summary ═══")
for r in results:
    mark = "✅" if r.get("ok") else "❌"
    print(f"  {mark} {r['step']:35s}  rc={r.get('exit_code',-1)}  "
          f"out={r.get('stdout_bytes',0)}B  err={r.get('stderr_bytes',0)}B")

# Write log atomically
tmp = DIAG_LOG.with_suffix(".tmp")
tmp.write_text(json.dumps({"ts": time.time(), "claude": CLAUDE, "steps": results}, indent=2))
tmp.replace(DIAG_LOG)
print(f"\nFull log: {DIAG_LOG}")

# Identify the best working invocation
working = [r for r in results if r.get("ok")]
if working:
    best = working[-1]
    print(f"\nBest working form: [{best['step']}]")
    if best.get("stdin"):
        print(f"  → Use stdin for prompt (not inline -p arg)")
    has_stream = "--output-format" in " ".join(best.get("argv", []))
    has_add_dir = "--add-dir" in " ".join(best.get("argv", []))
    print(f"  → stream-json supported: {has_stream}")
    print(f"  → --add-dir supported: {has_add_dir}")
else:
    print("\nNo working invocation found — check stderr output above")
