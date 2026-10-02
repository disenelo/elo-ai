#!/usr/bin/env python3
"""
COG-004 RE-RUN 22 — Language isolation test runner.
Sends all 26 cases to the live server at port 5050, one at a time (sequential — never concurrent).

Usage:
    ELO_OLLAMA_MODEL=qwen2.5-coder:14b python -u server.py &
    # wait for server to start, then:
    python3 engineering/evidence/run_cog004_rr22.py

Writes verbatim transcript to stdout and appends RR22 section to
engineering/evidence/CAP/COG/WO-CAP-COG-004_evidence.md.
"""
import json
import sys
import time
import urllib.request
import urllib.error

ENDPOINT = "http://127.0.0.1:5050/chat"
TIMEOUT = 120.0  # 2 min per case

CASES = [
    ("C1",  "Python",           'def greet(name): return f"Hello, {name}!"'),
    ("C2",  "JavaScript",       "const add = (a, b) => a + b;"),
    ("C3",  "TypeScript",       "interface User { id: number; name: string; email?: string; }"),
    ("C4",  "C#",               "public class Animal { public virtual void Speak() { Console.WriteLine(\"...\"); } }"),
    ("C5",  "C",                '#include <stdio.h>\nint main() { printf("Hello, World!\\n"); return 0; }'),
    ("C6",  "Rust",             "fn fibonacci(n: u32) -> u32 { match n { 0 => 0, 1 => 1, _ => fibonacci(n-1) + fibonacci(n-2) } }"),
    ("C7",  "SQL",              "SELECT users.name, orders.total FROM users JOIN orders ON users.id = orders.user_id WHERE orders.total > 100;"),
    ("C8",  "HTML",             '<div class="container"><h1>Hello</h1><p style="color: red;">World</p></div>'),
    ("C9",  "JSON",             '{"mode": "thinking", "intensity": 0.8, "duration": 3000}'),
    ("C10", "YAML",             "backend:\n  primary: ollama\n  model: mistral-nemo:12b\n  fallback: mock"),
    ("C11", "XML",              "<config><server><host>localhost</host><port>8080</port></server></config>"),
    ("C12", "Markdown",         "# Title\n## Section\n- item one\n- item two\n**bold** and _italic_"),
    ("C13", "Shell",            "ps aux | grep server.py | grep -v grep | awk '{print $2}' | xargs kill"),
    ("C14", "Regex",            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
    ("C15", "Git",              "git log --oneline --graph --decorate --all"),
    ("C16", "API",              "GET /api/users HTTP/1.1\nHost: example.com\nAuthorization: Bearer token123"),
    ("C17", "Schema",           '{"mode": "listening", "volume": 0.6, "timeout": 5000}'),
    ("C18", "TypeScript2",      "type Result<T, E> = Ok(T) | Err(E); const r: Result<number, string> = Ok(42);"),
    ("C19", "SQL2",             "SELECT AVG(salary), department FROM employees GROUP BY department HAVING AVG(salary) > 50000;"),
    ("C20", "Algebra",          "2x + 3y = 12\n4x - y = 5\nSolve for x and y."),
    ("C21", "Logic",            "if (A && B) || (!A && C) then output D\nelse output E"),
    ("C22", "DataStructures",   "stack = []\nstack.push(1)\nstack.push(2)\nstack.pop()\nstack.push(3)"),
    ("C23", "Pseudocode",       "FOR each item IN collection:\n  IF item.value > threshold:\n    REMOVE item FROM collection\n  END IF\nEND FOR"),
    ("C24", "Java",             "public class Stack<T> { private List<T> items = new ArrayList<>(); public void push(T item) { items.add(item); } public T pop() { return items.remove(items.size() - 1); } }"),
    ("C25", "StructuredMeaning","{ subject: 'formal_language', claim: 'eLo reads code fluently', confidence: 0.9 }"),
    ("C26", "KeyClaim",         "FUNCTION binary_search(array, target):\n  left = 0\n  right = length(array) - 1\n  WHILE left <= right:\n    mid = (left + right) / 2\n    IF array[mid] == target: RETURN mid\n    ELSE IF array[mid] < target: left = mid + 1\n    ELSE: right = mid - 1\n  RETURN -1"),
]


def send(text: str) -> tuple[str, float]:
    """POST one turn, return (response_text, elapsed_seconds)."""
    body = json.dumps({"text": text}).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read())
            elapsed = time.time() - t0
            # eLo server returns {"response": "...", ...}
            return str(data.get("response", data)), elapsed
    except urllib.error.URLError as e:
        elapsed = time.time() - t0
        return f"[ERROR: {e}]", elapsed
    except Exception as e:
        elapsed = time.time() - t0
        return f"[EXCEPTION: {e}]", elapsed


def main():
    print("=== COG-004 RE-RUN 22 START ===")
    print(f"Endpoint: {ENDPOINT}")
    print(f"Total cases: {len(CASES)}")
    print()

    results = []
    for cid, label, inp in CASES:
        print(f"--- {cid} [{label}] ---")
        print(f"INPUT: {inp[:120]}{'...' if len(inp) > 120 else ''}")
        sys.stdout.flush()
        response, elapsed = send(inp)
        print(f"RESPONSE ({elapsed:.1f}s): {response}")
        print()
        sys.stdout.flush()
        results.append((cid, label, inp, response, elapsed))
        time.sleep(1.5)  # brief pause between turns

    print("=== COG-004 RE-RUN 22 END ===")
    print(f"Total: {len(results)}")
    return results


if __name__ == "__main__":
    main()
