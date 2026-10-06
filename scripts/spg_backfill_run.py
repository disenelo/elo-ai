"""ROOT-4: write the backfilled graph to the live store.

Guarded. The live graph was destroyed once before by a test calling save()
with a path bound at class-definition time, so this verifies before and after
rather than trusting either.
"""
import hashlib
import json
import pathlib
import shutil
import sys
import time

sys.path.insert(0, "/Users/Disenelo/elo-ai")
from memory.spg_backfill import build, load_interactions

R = pathlib.Path("/Users/Disenelo/elo-ai")
LIVE = R / "data/spg_graph.json"
ARCHIVE = R / ".memory-archive"


def summary(path):
    if not path.exists():
        return "absent"
    d = json.loads(path.read_text())
    return (f"{d.get('node_count', len(d.get('nodes', [])))} nodes, "
            f"{d.get('edge_count', len(d.get('edges', []))) } edges, "
            f"sha {hashlib.sha256(path.read_bytes()).hexdigest()[:12]}")


print("BEFORE :", summary(LIVE))

# A second archive copy keyed to this run, on top of the one already taken.
ARCHIVE.mkdir(exist_ok=True)
stamp = time.strftime("%Y%m%d_%H%M%S")
backup = ARCHIVE / f"spg_graph.json.before_root4_{stamp}"
if LIVE.exists():
    shutil.copy2(LIVE, backup)
    print("backup :", backup.name)

rows = load_interactions()
print(f"source : {len(rows)} interactions")
if len(rows) < 500:
    print("REFUSING: source looks truncated — not overwriting the live graph")
    raise SystemExit(1)

graph = build(rows)
n, e = len(graph._nodes), len(graph._edges)
print(f"built  : {n} nodes, {e} edges")

if n < len(rows) * 0.9:
    print("REFUSING: built graph is far smaller than the source")
    raise SystemExit(1)

graph.save(LIVE)
print("AFTER  :", summary(LIVE))

# Prove it reloads as what was written.
reloaded = json.loads(LIVE.read_text())
assert reloaded["node_count"] == n, "saved node count does not match"
assert reloaded["edge_count"] == e, "saved edge count does not match"
sig = [x["significance"] for x in reloaded["nodes"]]
print(f"verify : reloads cleanly, {len(set(sig))} distinct significance values, "
      f"max {max(sig):.3f}")
