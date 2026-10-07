"""Incremental SPG backfill — add new turns without rebuilding.

Guarded: refuses if the graph shrinks, and archives before writing.
"""
import hashlib, json, pathlib, shutil, sys, time
sys.path.insert(0, "/Users/Disenelo/elo-ai")
from memory.spg_backfill import load_interactions, unprocessed, update

R = pathlib.Path("/Users/Disenelo/elo-ai")
LIVE = R / "data/spg_graph.json"
ARCHIVE = R / ".memory-archive"

def summary(p):
    d = json.loads(p.read_text())
    return (f"{d.get('node_count')} nodes, {d.get('edge_count')} edges, "
            f"sha {hashlib.sha256(p.read_bytes()).hexdigest()[:12]}")

print("BEFORE :", summary(LIVE))
rows = load_interactions()
pend = unprocessed(rows)
print(f"source : {len(rows)} interactions, {len(pend)} unprocessed")
if not pend:
    print("nothing to do"); raise SystemExit(0)

ARCHIVE.mkdir(exist_ok=True)
backup = ARCHIVE / f"spg_graph.json.before_update_{time.strftime('%Y%m%d_%H%M%S')}"
shutil.copy2(LIVE, backup)
print("backup :", backup.name)

before = json.loads(LIVE.read_text())["node_count"]
graph, added = update(rows)
n, e = len(graph._nodes), len(graph._edges)
if n < before:
    print(f"REFUSING: graph would shrink {before} -> {n}"); raise SystemExit(1)

graph.save(LIVE)
print("AFTER  :", summary(LIVE))
live = [x for x in json.loads(LIVE.read_text())["nodes"]
        if not str(x["id"]).startswith("bf-")]
print(f"verify : {len(added)} added, {len(live)} live-written nodes preserved")
