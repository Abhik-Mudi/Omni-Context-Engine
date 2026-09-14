#!/usr/bin/env python3
"""
Phase 0 test harness for the Omni-Context Engine.

Purpose: answer ONE question before writing any real infrastructure —
is a local model, given a hand-written workflow timeline + the relevant
code, actually good at diagnosing the error? No daemon, no DB, no AST.

Usage:
    ollama pull qwen3.5:4b        # or whatever tag your model uses
    python run_test.py cases/*.json

Each case is a JSON file (see cases/example_01.json for the format).
Results are printed to stdout AND appended to results.jsonl so you can
review/score them later without re-running the model.
"""

import json
import sys
import time
from pathlib import Path
from urllib import request

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen-coder:latest"

PROMPT_TEMPLATE = """You are an expert developer assistant. You are provided with the developer's recent timeline and a terminal error. Analyze if the error is a direct result of the recent timeline actions. If it is unrelated (e.g., a global test suite failure), state that explicitly, ignore the timeline, and solve the localized code error. Below is the exact sequence \
of things they did leading up to the error, followed by the relevant code.

=== WORKFLOW TIMELINE (most recent last) ===
{timeline}

=== RELEVANT CODE ===
{code}

=== ERROR ===
{error}

Based on the timeline and code, explain:
1. What the developer was most likely trying to build/change
2. The most probable root cause of this specific error (be concrete, cite the \
timeline event that likely caused it, not just the error message)
3. A concrete fix

Keep it under 200 words. Do not restate the error message back at me."""


def call_ollama(prompt: str) -> str:
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
    }).encode("utf-8")

    req = request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=300) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body.get("response", "").strip()


def run_case(path: Path) -> dict:
    case = json.loads(path.read_text())
    prompt = PROMPT_TEMPLATE.format(
        timeline=case["timeline"],
        code=case["code"],
        error=case["error"],
    )

    start = time.time()
    diagnosis = call_ollama(prompt)
    elapsed = time.time() - start

    result = {
        "case": path.stem,
        "elapsed_seconds": round(elapsed, 1),
        "diagnosis": diagnosis,
        # you fill this in by hand after reading the diagnosis:
        # "correct" | "plausible_but_wrong" | "garbage"
        "score": None,
    }
    return result


def main(argv: list[str]) -> None:
    if not argv:
        print("Usage: python run_test.py cases/*.json")
        sys.exit(1)

    results_path = Path("results.jsonl")
    all_results = []

    for arg in argv:
        path = Path(arg)
        print(f"\n{'=' * 60}")
        print(f"CASE: {path.stem}")
        print("=" * 60)
        try:
            result = run_case(path)
        except Exception as e:
            print(f"  ERROR running case: {e}")
            print("  (Is `ollama serve` running? Is the MODEL name correct —")
            print(f"   check `ollama list`, currently set to '{MODEL}')")
            continue

        print(f"[{result['elapsed_seconds']}s]\n")
        print(result["diagnosis"])
        all_results.append(result)

    with results_path.open("a") as f:
        for r in all_results:
            f.write(json.dumps(r) + "\n")

    print(f"\n\nAppended {len(all_results)} results to {results_path}")
    print("Now go score each one by hand: correct / plausible_but_wrong / garbage")
    print("Gate: if <70% are 'correct', stop and rethink before Phase 1.")


if __name__ == "__main__":
    main(sys.argv[1:])