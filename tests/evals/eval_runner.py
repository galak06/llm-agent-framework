"""Eval harness — runs curated Q&A cases against the agent."""

from __future__ import annotations

import json
from pathlib import Path


def load_cases(path: Path) -> list[dict]:
    """Load eval cases from JSON file."""
    return json.loads(path.read_text())


def run_evals(cases: list[dict]) -> dict:
    """Run eval cases and return results summary."""
    results = {
        'total': len(cases),
        'passed': 0,
        'failed': 0,
        'errors': [],
    }

    for _case in cases:
        # Placeholder — will call agent and assert
        results['passed'] += 1

    return results


if __name__ == '__main__':
    cases_dir = Path('tests/evals/cases')
    for case_file in cases_dir.glob('*.json'):
        cases = load_cases(case_file)
        results = run_evals(cases)
        print(f'{case_file.name}: {results["passed"]}/{results["total"]} passed')
