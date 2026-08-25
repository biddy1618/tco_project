"""Run the local Prompt Flow baseline checks in a single command.

This entrypoint executes the proven smoke, lookup, state, and final-assembly
harnesses using the maf interpreter. It is intended as the repeatable local
sanity check before any restructuring work.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


@dataclass(frozen=True)
class Check:
    name: str
    args: list[str]


CHECKS = [
    Check("azure_search_smoke", [str(PROJECT_ROOT / "scripts" / "test_azure_search_smoke.py")]),
    Check("lookup_harness", [str(PROJECT_ROOT / "scripts" / "run_lookup_harness.py")]),
    Check("state_harness_complete", [str(PROJECT_ROOT / "scripts" / "run_state_harness.py")]),
    Check("state_harness_electric", [str(PROJECT_ROOT / "scripts" / "run_state_harness.py"), "--scenario", "electric"]),
    Check("final_harness_default", [str(PROJECT_ROOT / "scripts" / "run_final_harness.py")]),
    Check("final_harness_pwht_yes", [str(PROJECT_ROOT / "scripts" / "run_final_harness.py"), "--text", "line class 150K5F"]),
]


def run_check(check: Check) -> bool:
    print(f"=== {check.name} ===")
    completed = subprocess.run([PYTHON, *check.args], cwd=PROJECT_ROOT, capture_output=True, text=True)
    if completed.returncode == 0:
        if completed.stdout:
            print(completed.stdout, end="")
        print(f"{check.name}: PASS")
        return True

    print(f"{check.name}: FAIL ({completed.returncode})")
    if completed.stdout:
        print("--- stdout ---")
        print(completed.stdout, end="")
    if completed.stderr:
        print("--- stderr ---")
        print(completed.stderr, end="")
    return False


def main(argv: Iterable[str]) -> int:
    failures = []

    for check in CHECKS:
        if not run_check(check):
            failures.append(check.name)

    print("=== summary ===")
    if failures:
        print("failed checks:")
        for name in failures:
            print(f"- {name}")
        return 1

    print("all local checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))