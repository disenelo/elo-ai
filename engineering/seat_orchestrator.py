#!/usr/bin/env python3
"""
seat_orchestrator.py — eLo OS Seat Orchestrator (card 0058)

Reads the lowest-numbered QUEUE card for a seat, launches the appropriate
worker via the transport declared in registry.json, captures observable
lifecycle states from files/process state, and reports to outbox.

Transports:
  python     — subprocess.Popen(['python3', '-m', module]) — PROVEN
  claude-code — subprocess.Popen(['claude', '-p', ...])   — tested via this script

Card 0058 order:
  1. GP-1: script seat (python transport) — runs company_state_writer  [PROVEN]
  2. Item 1: builder seat (claude-code transport) — answer YES/NO      [PROBE]
  3. GP-2: builder → design chain (only if item 1 is YES)

Usage:
  python3 engineering/seat_orchestrator.py gp1         # GP-1: script seat
  python3 engineering/seat_orchestrator.py item1       # Item 1: Claude Code probe
  python3 engineering/seat_orchestrator.py builder     # run lowest Builder card
  python3 engineering/seat_orchestrator.py design      # run lowest Design card

Constraints (from card):
  - Deterministic: no model call to decide whether work exists. File reads only.
  - Do not create another queue / state system / seat contract redesign.
  - Atomic writes everywhere (tmp + os.replace).
  - RESERVED cards (money/legal/safety) are never auto-run.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import time
import pathlib

ROOT      = pathlib.Path.home() / "elo-ai"
BUS       = ROOT / "blender" / "agent_bus"
REGISTRY  = BUS / "registry.json"
SEAT_EP   = BUS / "_SEAT_EPISTEMIC_PROTOCOL.md"
AUTORUN   = BUS / "AUTORUN_PROTOCOL.md"
METRICS   = pathlib.Path.home() / "Desktop" / "Output" / "orchestrator_metrics.json"

# Cards with any of these keywords in their title are never auto-run.
_RESERVED_KEYWORDS = frozenset({
    "money", "legal", "safety", "RESERVED", "finance", "billing",
    "salary", "contract", "security", "privacy",
})


# ── credentials ───────────────────────────────────────────────────────────────

def _api_key() -> str:
    """Read ANTHROPIC_API_KEY from .env — never embed in prompts or logs."""
    for raw in (ROOT / ".env").read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("ANTHROPIC_API_KEY="):
            val = line.split("=", 1)[1].strip().strip('"').strip("'")
            if val:
                return val
    raise RuntimeError("ANTHROPIC_API_KEY not found in .env")


# ── queue helpers ─────────────────────────────────────────────────────────────

def _lowest_card(seat_dir: pathlib.Path) -> pathlib.Path | None:
    q = seat_dir / "QUEUE"
    if not q.exists():
        return None
    cards = sorted(
        [f for f in q.iterdir()
         if f.suffix == ".md" and not f.name.startswith(".")],
        key=lambda f: f.name,
    )
    return cards[0] if cards else None


def _is_reserved(card: pathlib.Path) -> bool:
    txt = card.read_text().lower()
    return any(kw in txt for kw in _RESERVED_KEYWORDS)


def _read_frontmatter(card: pathlib.Path) -> dict:
    """Parse YAML-like frontmatter between --- lines (no deps on PyYAML)."""
    lines = card.read_text().splitlines()
    fm: dict = {}
    if not lines or lines[0].strip() != "---":
        return fm
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm


# ── lock management ───────────────────────────────────────────────────────────

def _acquire_lock(seat_dir: pathlib.Path, work_id: str, pid: int) -> bool:
    lock_path = seat_dir / "LOCK.json"
    tmp_path  = lock_path.with_suffix(".tmp")
    # Check existing lock
    if lock_path.exists():
        try:
            existing = json.loads(lock_path.read_text())
            existing_pid = existing.get("pid")
            if existing_pid and existing.get("state") not in ("RELEASED", None):
                # Check if that PID is still alive
                try:
                    os.kill(existing_pid, 0)
                    return False  # still alive — seat busy
                except (ProcessLookupError, PermissionError):
                    pass  # PID dead — stale lock, can reclaim
        except (json.JSONDecodeError, TypeError):
            pass
    record = {
        "owner":      "orchestrator",
        "pid":        pid,
        "work_id":    work_id,
        "ts":         time.time(),
        "heartbeat":  time.time(),
        "state":      "LOCKED",
    }
    tmp_path.write_text(json.dumps(record, indent=2))
    tmp_path.replace(lock_path)
    return True


def _release_lock(seat_dir: pathlib.Path) -> None:
    lock_path = seat_dir / "LOCK.json"
    tmp_path  = lock_path.with_suffix(".tmp")
    record = {
        "owner":       None, "pid": None, "work_id": None,
        "state":       "RELEASED",
        "released_ts": time.time(),
    }
    tmp_path.write_text(json.dumps(record, indent=2))
    tmp_path.replace(lock_path)


# ── lifecycle recorder (writes HEARTBEAT.json — canonical per LA) ──────────────

class Lifecycle:
    STATES = ("QUEUED", "CLAIMED", "LOCKED", "STARTED", "ALIVE",
              "PROGRESSING", "OUTPUT", "RESULT", "ACCEPTANCE", "DONE")

    def __init__(self, seat: str, card_name: str, work_id: str = "", pid: int = 0):
        self.seat      = seat
        self.card      = card_name
        self.work_id   = work_id or card_name
        self.pid       = pid
        self.log: list[dict] = []
        self._pos      = 0
        self._path     = BUS / seat / "HEARTBEAT.json"  # canonical filename

    def record(self, state: str, detail: str = "") -> None:
        entry = {"state": state, "ts": time.time(), "detail": detail}
        self.log.append(entry)
        self._pos += 1
        label = f"[{state}]"
        print(f"{label:16s} {detail}", flush=True)
        self._flush(current_action=state, detail=detail)

    def set_pid(self, pid: int) -> None:
        self.pid = pid
        self._flush(current_action=self.log[-1]["state"] if self.log else "STARTED")

    def _flush(self, current_action: str = "", detail: str = "") -> None:
        # Canonical HEARTBEAT schema (matches LA's HEARTBEAT.json shape)
        record = {
            "seat":              self.seat,
            "work_id":           self.work_id,
            "pid":               self.pid,
            "started_at":        self.log[0]["ts"] if self.log else time.time(),
            "last_activity_at":  time.time(),
            "current_action":    current_action,
            "execution_position": self._pos,
            "last_output":       detail if detail else None,
            "last_evidence":     None,
            "next_action":       None,
        }
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(record, indent=2))
        tmp.replace(self._path)

    def final_state(self) -> str:
        return self.log[-1]["state"] if self.log else "UNKNOWN"


# ── git helpers ────────────────────────────────────────────────────────────────

def _git_stat() -> str:
    return subprocess.run(
        ["git", "diff", "--stat", "HEAD"],
        cwd=str(ROOT), capture_output=True, text=True
    ).stdout.strip()


def _git_head() -> str:
    return subprocess.run(
        ["git", "log", "--oneline", "-1"],
        cwd=str(ROOT), capture_output=True, text=True
    ).stdout.strip()


# ── outbox ────────────────────────────────────────────────────────────────────

def _file_outbox(seat: str, card_name: str, result: dict, elapsed: float = 0.0) -> None:
    ob   = BUS / seat / "outbox.json"
    tmp  = ob.with_suffix(".tmp")
    data = {}
    if ob.exists():
        try:
            data = json.loads(ob.read_text())
        except json.JSONDecodeError:
            pass
    # Canonical outbox entry schema (matches script seat outbox: to/from/ts/state/output/evidence/duration_s)
    work_id = result.get("work_id", card_name.replace(".md", ""))
    run_n   = len([v for k, v in data.items() if str(k).startswith(work_id)]) + 1
    key     = f"{work_id}_run{run_n}"
    data[key] = {
        "to":        "Architect",
        "from":      seat,
        "ts":        time.time(),
        "state":     result.get("status", "UNKNOWN"),
        "output":    result.get("commits", []) or result.get("outputs", []),
        "evidence":  str(result.get("evidence", ""))[:400],
        "duration_s": round(elapsed, 2),
    }
    if result.get("blocker"):
        data[key]["blocker"] = result["blocker"]
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(ob)


# ── metrics ───────────────────────────────────────────────────────────────────

def _update_metrics(seat: str, result: dict, elapsed: float, work_id: str = "") -> None:
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    tmp = METRICS.with_suffix(".tmp")
    data: dict = {}
    if METRICS.exists():
        try:
            data = json.loads(METRICS.read_text())
        except json.JSONDecodeError:
            pass
    # Canonical key names (from Output/orchestrator_metrics.json)
    data.setdefault("jobs_started", 0)
    data.setdefault("jobs_completed", 0)
    data.setdefault("jobs_failed", 0)
    data.setdefault("jobs_blocked", 0)
    data.setdefault("david_escalations", 0)
    data.setdefault("outputs_produced", 0)
    data.setdefault("stale_worker_incidents", 0)
    data.setdefault("david_interventions", 0)
    data.setdefault("handoffs_completed", 0)
    data.setdefault("transport_limitations", [])
    data.setdefault("runs", [])

    data["jobs_started"] += 1
    status = result.get("status", "UNKNOWN")
    if status == "DONE":
        data["jobs_completed"] += 1
        data["outputs_produced"] += 1
    elif status == "BLOCKED":
        data["jobs_blocked"] += 1
    elif status == "DAVID_REQUIRED":
        data["david_escalations"] += 1
    else:
        data["jobs_failed"] += 1

    run_n = len([r for r in data["runs"] if r.get("work_id") == work_id]) + 1
    data["runs"].append({
        "work_id":   work_id or "unknown",
        "run":       run_n,
        "seat":      seat,
        "transport": result.get("transport", "unknown"),
        "state":     status,
        "ts":        time.strftime("%Y-%m-%dT%H:%M:%S"),
        "elapsed_s": round(elapsed, 2),
    })

    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(METRICS)


# ── TRANSPORT ADAPTERS ────────────────────────────────────────────────────────

def _run_python_worker(
    card: pathlib.Path,
    fm: dict,
    seat_dir: pathlib.Path,
    lc: Lifecycle,
    result_file: pathlib.Path,
) -> dict:
    """
    Python transport adapter.
    Reads 'module' from frontmatter and runs it as python3 -m <module>.
    """
    module = fm.get("module", "")
    if not module:
        return {
            "status": "BLOCKED",
            "acceptance_met": False,
            "blocker": "frontmatter 'module' field missing from card",
            "transport": "python",
        }

    entry = fm.get("entry", "")
    output_log = seat_dir / "worker_output.log"
    output_log.write_text("")

    # Build command: if entry is specified, call it as a one-liner
    if entry:
        cmd = [
            "python3", "-c",
            f"from {module} import {entry}; {entry}()"
        ]
    else:
        cmd = ["python3", "-m", module]

    env = os.environ.copy()
    # DO NOT add credentials — python workers use the repo's own env/config

    lc.record("STARTED", f"python3 {' '.join(cmd[1:])}")
    head_before = _git_head()

    mtime_before = None
    # Watch the output file the worker is expected to write
    target_path_str = ""
    if "company_state" in module:
        target_path_str = str(ROOT / "blender" / "company_state.json")
    target = pathlib.Path(target_path_str) if target_path_str else None
    if target and target.exists():
        mtime_before = target.stat().st_mtime

    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    lc.record("ALIVE", f"PID {proc.pid}")

    progressing = False
    TIMEOUT_S = 120

    while proc.poll() is None:
        line = proc.stdout.readline()
        if line:
            with open(output_log, "a") as f:
                f.write(line)
            if not progressing:
                progressing = True
                lc.record("PROGRESSING", f"stdout: {line.strip()[:80]}")
        if time.time() - lc.log[0]["ts"] > TIMEOUT_S:
            proc.terminate()
            lc.record("OUTPUT", f"TIMEOUT after {TIMEOUT_S}s")
            break

    rest = proc.stdout.read()
    if rest:
        with open(output_log, "a") as f:
            f.write(rest)

    exit_code = proc.returncode if proc.returncode is not None else proc.wait()

    if not progressing:
        lc.record("PROGRESSING", "NONE — no stdout before exit")

    output_bytes = output_log.stat().st_size if output_log.exists() else 0
    lc.record("OUTPUT", f"exit_code={exit_code} bytes={output_bytes}")

    # Acceptance: target file mtime advanced and exit_code 0
    accepted = False
    evidence = ""
    if exit_code == 0 and target and target.exists():
        mtime_after = target.stat().st_mtime
        if mtime_before is None or mtime_after > mtime_before:
            accepted = True
            evidence = f"{target.name} mtime updated to {time.strftime('%H:%M:%S', time.localtime(mtime_after))}"
        else:
            evidence = f"{target.name} mtime unchanged — writer may have skipped"
    elif exit_code == 0:
        accepted = True
        evidence = "exit_code=0"
    else:
        evidence = f"exit_code={exit_code} — see {output_log.name}"

    result = {
        "transport":      "python",
        "status":         "DONE" if accepted else "BLOCKED",
        "acceptance_met": accepted,
        "evidence":       evidence,
        "exit_code":      exit_code,
        "commits":        [],
        "blocker":        None if accepted else evidence,
    }

    # Write result file (observable)
    tmp = result_file.with_suffix(".tmp")
    tmp.write_text(json.dumps(result, indent=2))
    tmp.replace(result_file)

    return result


def _run_claude_worker(
    card: pathlib.Path,
    seat: str,
    seat_dir: pathlib.Path,
    lc: Lifecycle,
    result_file: pathlib.Path,
) -> dict:
    """
    Claude Code transport adapter.
    Launches claude -p in headless mode and observes file-system evidence.
    """
    # Build prompt — credentials NOT in prompt, NOT in log
    card_text     = card.read_text()
    seat_contract = SEAT_EP.read_text() if SEAT_EP.exists() else ""
    autorun_text  = AUTORUN.read_text() if AUTORUN.exists() else ""

    prompt = textwrap.dedent(f"""
    You are the {seat} implementation seat in the eLo OS project.
    Project root: {ROOT}
    Your current card is in DOING/ — you claimed it.

    AUTORUN PROTOCOL — binding:
    {autorun_text[:3000]}

    SEAT CONTRACT — binding:
    {seat_contract[:3000]}

    WORK CARD ({card.name}):
    {card_text}

    EXECUTION:
    1. Read the relevant source files (they are in {ROOT}).
    2. Make exactly the changes the card requires.
    3. Run the acceptance test.
    4. Commit only changed files.
    5. Move the card from DOING/ to DONE/, appending the commit hash.
    6. Write your result to: {result_file}
       Format: {{"card":"{card.name}","status":"DONE|PARTIAL|BLOCKED","commits":["hash"],"acceptance_met":true|false,"evidence":"...","blocker":null}}
    7. Append one line to {seat_dir / 'outbox.json'}.

    If blocked: state the exact file:line or missing prerequisite.
    """).strip()

    import shutil
    claude_bin = shutil.which("claude") or "/opt/homebrew/bin/claude"
    env = os.environ.copy()
    # Do NOT force ANTHROPIC_API_KEY — claude uses its own stored auth when the
    # env var is absent. Only inject if it is already absent from env AND .env has it.
    if "ANTHROPIC_API_KEY" not in env:
        try:
            env["ANTHROPIC_API_KEY"] = _api_key()
        except RuntimeError:
            pass

    # Diagnostic finding (2026-08-19): --output-format stream-json exits rc=1 without --verbose.
    # --add-dir is not needed when cwd=ROOT. Pass prompt via stdin — proven to work (step 9).
    cmd = [
        claude_bin, "-p",
        "--dangerously-skip-permissions",
    ]

    output_log = seat_dir / "worker_output.log"
    output_log.write_text("")

    head_before = _git_head()
    git_stat_before = _git_stat()
    lc.record("STARTED", f"{claude_bin} -p --dangerously-skip-permissions [prompt via stdin, {len(prompt)}B]")

    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        env=env,
        stdin=subprocess.PIPE,      # prompt via stdin (proven: step 9 of diag)
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,     # keep stderr separate for diagnostics
        text=True,
        bufsize=1,
    )

    # Write prompt to stdin and close the pipe
    try:
        proc.stdin.write(prompt)
        proc.stdin.close()
    except BrokenPipeError:
        pass

    lc.log[-1]["detail"] = f"{claude_bin} -p --dangerously-skip-permissions PID={proc.pid}"
    time.sleep(3)
    lc.record("ALIVE", f"PID {proc.pid} {'running' if proc.poll() is None else 'exited rc=' + str(proc.returncode)}")

    progressing = False
    tool_events = 0
    TIMEOUT_S = 600

    while proc.poll() is None:
        line = proc.stdout.readline()
        if not line:
            continue
        with open(output_log, "a") as f:
            f.write(line)

        if not progressing:
            # PROGRESSING: any stdout output, or git diff change
            progressing = True
            lc.record("PROGRESSING", f"stdout: {line.strip()[:80]}")

        if time.time() - lc.log[0]["ts"] > TIMEOUT_S:
            proc.terminate()
            lc.record("OUTPUT", f"TIMEOUT after {TIMEOUT_S}s — terminated")
            break

        # Poll git diff as secondary evidence
        if not progressing:
            gs = _git_stat()
            if gs and gs != git_stat_before:
                progressing = True
                git_stat_before = gs
                lc.record("PROGRESSING", "git diff changed — files modified")

        if time.time() - lc.log[0]["ts"] > TIMEOUT_S:
            proc.terminate()
            lc.record("OUTPUT", f"TIMEOUT after {TIMEOUT_S}s — terminated")
            break

    rest = proc.stdout.read()
    if rest:
        with open(output_log, "a") as f:
            f.write(rest)

    exit_code = proc.returncode if proc.returncode is not None else proc.wait()
    output_bytes = output_log.stat().st_size if output_log.exists() else 0
    if not progressing:
        lc.record("PROGRESSING", "NONE — no tool_use events, no git diff change")
    lc.record("OUTPUT", f"exit_code={exit_code} bytes={output_bytes} tool_events={tool_events}")

    # RESULT — check observable evidence
    if result_file.exists():
        try:
            worker_result = json.loads(result_file.read_text())
            worker_result["transport"] = "claude-code"
            return worker_result
        except json.JSONDecodeError:
            pass

    done_card   = seat_dir / "DONE" / card.name
    head_after  = _git_head()
    new_commit  = head_after != head_before

    if done_card.exists() and new_commit:
        return {
            "transport":      "claude-code",
            "status":         "DONE",
            "acceptance_met": True,
            "evidence":       f"card in DONE/. new commit: {head_after}",
            "commits":        [head_after.split()[0]],
        }

    # Evidence for Item 1 (was the Claude process even alive and doing work?)
    return {
        "transport":      "claude-code",
        "status":         "PARTIAL" if progressing else "BLOCKED",
        "acceptance_met": False,
        "evidence":       (
            f"ALIVE=true PROGRESSING={'true' if progressing else 'false'} "
            f"exit_code={exit_code} output_bytes={output_bytes}"
        ),
        "blocker":        "worker did not write result file or move card to DONE/",
        "item1_answer":   "YES" if progressing else "NO",
    }


# ── main runner ───────────────────────────────────────────────────────────────

def run_seat(seat: str) -> dict:
    """Run one work cycle for a seat. Returns lifecycle + result."""
    seat_dir  = BUS / seat
    lc        = None

    # Find lowest non-reserved card (spec §A: if reserved → escalate, skip, continue)
    q = seat_dir / "QUEUE"
    all_cards = sorted(
        [f for f in q.iterdir() if f.suffix == ".md" and not f.name.startswith(".")],
        key=lambda f: f.name,
    ) if q.exists() else []
    card = None
    for candidate in all_cards:
        if _is_reserved(candidate):
            print(f"[RESERVED] {candidate.name} — skipping, DAVID_REQUIRED (escalated)")
        else:
            card = candidate
            break

    if card is None:
        if not all_cards:
            print(f"[IDLE] No cards in {seat}/QUEUE")
            return {"status": "IDLE", "seat": seat}
        print(f"[IDLE] All cards in {seat}/QUEUE are RESERVED — escalate to David")
        return {"status": "DAVID_REQUIRED", "reason": "all queued cards reserved", "seat": seat}

    lc = Lifecycle(seat, card.name)
    t0 = time.time()

    # QUEUED
    lc.record("QUEUED", f"{seat}/QUEUE/{card.name}")

    # Acquire lock before claiming
    work_id = _read_frontmatter(card).get("work_id", card.stem)
    if not _acquire_lock(seat_dir, work_id, os.getpid()):
        lc.record("QUEUED", f"BLOCKED — {seat}/LOCK.json held by live process")
        return {"status": "BLOCKED", "blocker": "seat locked by another process"}

    # CLAIMED — mv QUEUE → DOING
    doing_dir = seat_dir / "DOING"
    doing_dir.mkdir(exist_ok=True)
    card_doing = doing_dir / card.name
    card.rename(card_doing)
    lc.record("CLAIMED", f"mv → DOING/{card.name}")

    # LOCKED
    lc.record("LOCKED", f"{seat}/LOCK.json acquired (PID {os.getpid()})")

    # Read frontmatter to determine transport
    fm        = _read_frontmatter(card_doing)
    transport = fm.get("transport", "")

    # Resolve transport from registry if not in frontmatter
    if not transport:
        reg = json.loads(REGISTRY.read_text()) if REGISTRY.exists() else {}
        transport = reg.get(seat, {}).get("transport", "")

    # Result file (observable)
    result_file = seat_dir / "worker_result.json"
    if result_file.exists():
        result_file.unlink()

    # Dispatch to adapter
    if transport == "python":
        result = _run_python_worker(card_doing, fm, seat_dir, lc, result_file)
    elif transport in ("claude-code", "repo"):
        result = _run_claude_worker(card_doing, seat, seat_dir, lc, result_file)
    else:
        result = {
            "status":  "BLOCKED",
            "blocker": f"transport '{transport}' has no adapter yet",
            "transport": transport,
        }
        lc.record("STARTED", result["blocker"])

    # RESULT
    lc.record("RESULT", f"status={result.get('status')} acceptance={result.get('acceptance_met')}")

    # ACCEPTANCE
    accepted = bool(result.get("acceptance_met"))
    lc.record("ACCEPTANCE", f"{'MET' if accepted else 'NOT MET'} — {str(result.get('evidence',''))[:100]}")

    # Move card to DONE (if worker didn't)
    done_dir  = seat_dir / "DONE"
    done_dir.mkdir(exist_ok=True)
    done_card = done_dir / card_doing.name
    if card_doing.exists() and not done_card.exists():
        card_doing.rename(done_card)

    # Release lock
    _release_lock(seat_dir)

    # DONE
    elapsed = time.time() - t0
    lc.record("DONE", f"{'MET' if accepted else 'NOT MET'} elapsed={elapsed:.1f}s")

    # Outbox + metrics (canonical schemas)
    _file_outbox(seat, card.name, result, elapsed)
    _update_metrics(seat, result, elapsed, work_id=work_id)

    print(f"\n── Lifecycle: {seat}/{card.name} ──")
    for s in lc.log:
        print(f"  {s['state']:14s} {s['detail']}")
    print()

    return {"lifecycle": lc.log, "result": result}


# ── item 1: Claude Code launch probe ─────────────────────────────────────────

def probe_item1() -> dict:
    """
    Item 1: can a Claude Code seat be launched headlessly and return a result?
    Uses a minimal card that asks Claude to write one file.
    Reports YES / NO / UNKNOWN with observable file evidence.
    """
    probe_dir  = BUS / "builder"
    probe_card = probe_dir / "DOING" / "_item1_probe.md"
    result_file = probe_dir / "worker_result.json"
    probe_card.parent.mkdir(parents=True, exist_ok=True)

    # Write a minimal, self-contained probe card
    probe_card.write_text(textwrap.dedent(f"""
    # Item 1 probe — transport test
    Write the string '{{"item1":"YES","ts":{int(time.time())}}}' to the file:
    {result_file}
    That is the ONLY thing you must do. Read nothing, edit nothing else.
    Exit immediately after writing that file.
    """).strip())

    lc = Lifecycle("builder", "_item1_probe")
    lc.record("QUEUED", "probe card written")
    lc.record("CLAIMED", "probe (no actual queue move)")
    lc.record("LOCKED", "no lock needed for probe")

    if result_file.exists():
        result_file.unlink()

    import shutil
    claude_bin = shutil.which("claude") or "/opt/homebrew/bin/claude"
    env = os.environ.copy()
    if "ANTHROPIC_API_KEY" not in env:
        try:
            env["ANTHROPIC_API_KEY"] = _api_key()
        except RuntimeError:
            pass

    probe_prompt = probe_card.read_text()
    # Fix: prompt via stdin, no --output-format stream-json (requires --verbose), no --add-dir
    cmd = [claude_bin, "-p", "--dangerously-skip-permissions"]

    output_log = probe_dir / "worker_output.log"
    output_log.write_text("")

    proc = subprocess.Popen(
        cmd, cwd=str(ROOT), env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True, bufsize=1,
    )
    try:
        proc.stdin.write(probe_prompt)
        proc.stdin.close()
    except BrokenPipeError:
        pass

    lc.record("STARTED", f"{claude_bin} -p --dangerously-skip-permissions [stdin, {len(probe_prompt)}B] PID={proc.pid}")
    time.sleep(3)
    alive = proc.poll() is None
    lc.record("ALIVE", f"PID {proc.pid} {'running' if alive else 'already exited'}")

    progressing = False
    TIMEOUT_S   = 120

    while proc.poll() is None:
        line = proc.stdout.readline()
        if not line:
            continue
        with open(output_log, "a") as f:
            f.write(line)
        if not progressing:
            progressing = True
            lc.record("PROGRESSING", f"stdout: {line.strip()[:80]}")

        if time.time() - lc.log[0]["ts"] > TIMEOUT_S:
            proc.terminate()
            break

    rest_out = proc.stdout.read()
    rest_err = proc.stderr.read()
    if rest_out:
        with open(output_log, "a") as f:
            f.write(rest_out)
    exit_code    = proc.returncode if proc.returncode is not None else proc.wait()
    output_bytes = output_log.stat().st_size

    if rest_err:
        lc.record("OUTPUT", f"stderr: {rest_err[:120]}")
    if not progressing:
        lc.record("PROGRESSING", f"NONE — exit_code={exit_code} bytes={output_bytes}")

    lc.record("OUTPUT", f"exit_code={exit_code} bytes={output_bytes}")

    if result_file.exists():
        try:
            payload = json.loads(result_file.read_text())
            answer  = payload.get("item1", "NO")
            lc.record("RESULT",     f"result_file written: {payload}")
            lc.record("ACCEPTANCE", f"MET — item1={answer}")
            lc.record("DONE",       "YES — Claude Code transport PROVEN")
            return {"item1": "YES", "evidence": str(payload), "transport": "claude-code"}
        except json.JSONDecodeError:
            pass

    if progressing:
        answer = "YES"
        evidence = f"stdout produced (PROGRESSING=true) but result file not written. exit_code={exit_code}"
        lc.record("RESULT",     "PARTIAL — stdout output seen, result file absent")
        lc.record("ACCEPTANCE", "NOT MET — result file not written")
        lc.record("DONE",       f"PARTIAL — ALIVE=true PROGRESSING=true exit_code={exit_code}")
    else:
        answer = "NO"
        evidence = f"exit_code={exit_code} bytes={output_bytes} — no stdout, no result file"
        lc.record("RESULT",     "BLOCKED — no observable work")
        lc.record("ACCEPTANCE", "NOT MET")
        lc.record("DONE",       "NO — Claude Code transport NOT PROVEN")

    print(f"\n── Item 1 lifecycle ──")
    for s in lc.log:
        print(f"  {s['state']:14s} {s['detail']}")

    return {"item1": answer, "evidence": evidence, "transport": "claude-code"}


# ── entry ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "gp1"

    if mode == "gp1":
        print("═══ GP-1: Script seat (Python transport) ═══")
        result = run_seat("script")

    elif mode == "item1":
        print("═══ Item 1: Claude Code transport probe ═══")
        result = probe_item1()
        print(f"\nItem 1 answer: {result.get('item1')}")
        print(f"Evidence:      {result.get('evidence')}")

    elif mode in ("builder", "design", "game", "script"):
        print(f"═══ Seat: {mode} ═══")
        result = run_seat(mode)

    elif mode == "gp1_then_item1":
        print("═══ GP-1 then Item 1 ═══")
        r1 = run_seat("script")
        print(f"\nGP-1 result: {r1.get('result', {}).get('status')}")
        r2 = probe_item1()
        print(f"Item 1: {r2.get('item1')}")
        result = {"gp1": r1, "item1": r2}

    else:
        print(f"Unknown mode: {mode}")
        print("Modes: gp1 | item1 | gp1_then_item1 | builder | design | game | script")
        sys.exit(1)
