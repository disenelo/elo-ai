"""
memory/fact_store.py — Durable semantic fact snapshots (WO-037).

Stores key-value facts that survive restart, separate from the rolling
conversation log. Examples: location, project state, preferences.
"""
import json, os, time

_FACTS_FILE = os.path.join(os.path.dirname(__file__), "facts.json")


def save_fact(key: str, fact: str) -> None:
    """Write or update a named fact. key is the semantic slot; fact is the full sentence."""
    facts = load_facts()
    for entry in facts:
        if entry.get("key") == key:
            entry["fact"] = fact.strip()
            entry["ts"] = time.time()
            break
    else:
        facts.append({"key": key, "fact": fact.strip(), "ts": time.time()})
    _write(facts)


def load_facts() -> list:
    try:
        raw = open(_FACTS_FILE, encoding="utf-8").read()
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def facts_summary() -> str:
    """One-line-per-fact summary for system prompt injection."""
    facts = load_facts()
    if not facts:
        return ""
    return "\n".join(f"- {f['fact']}" for f in facts if f.get("fact"))


def _write(facts: list) -> None:
    tmp = _FACTS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(facts, fh, indent=2)
    os.replace(tmp, _FACTS_FILE)
