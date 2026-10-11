#!/usr/bin/env python3
"""
Master E2E Test Suite Runner
Location: tests/e2e/test_runner.py

CLI Invocation:
  python tests/e2e/test_runner.py [--all] [--tier {1,2,3,4}] [--feature {F1..F8}] [--strict] [--json-report <path>]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import pytest

_tests_dir = Path(__file__).resolve().parent
_root_dir = _tests_dir.parent.parent

TIER_FILES = {
    1: str(_tests_dir / "test_tier1_features.py"),
    2: str(_tests_dir / "test_tier2_boundaries.py"),
    3: str(_tests_dir / "test_tier3_combinations.py"),
    4: str(_tests_dir / "test_tier4_scenarios.py"),
}


def build_pytest_args(
    tier: int | None = None,
    feature: str | None = None,
    verbose: bool = True,
    keyword: str | None = None,
    extra_args: List[str] | None = None,
) -> List[str]:
    args = []
    if verbose:
        args.append("-v")
    args.extend(["-s", "--tb=short"])

    # Target files
    if tier:
        if tier in TIER_FILES:
            args.append(TIER_FILES[tier])
        else:
            raise ValueError(f"Unknown tier: {tier}. Must be 1, 2, 3, or 4.")
    else:
        # Default all tiers
        for f in TIER_FILES.values():
            args.append(f)

    # Filter by feature or keyword
    exprs = []
    if feature:
        feature_key = feature.upper().strip()
        exprs.append(feature_key.lower())
    if keyword:
        exprs.append(keyword)

    if exprs:
        args.extend(["-k", " and ".join(exprs)])

    if extra_args:
        args.extend(extra_args)

    return args


class JsonReportPlugin:
    """Lightweight pytest plugin to capture structured test results."""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.summary = {"passed": 0, "failed": 0, "skipped": 0, "error": 0, "total": 0}
        self.start_time = time.time()
        self.duration = 0.0

    def pytest_runtest_logreport(self, report):
        if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
            self.summary["total"] += 1
            entry = {
                "nodeid": report.nodeid,
                "outcome": report.outcome,
                "duration": round(report.duration, 4),
            }
            if report.outcome == "passed":
                self.summary["passed"] += 1
            elif report.outcome == "failed":
                self.summary["failed"] += 1
                entry["message"] = str(report.longrepr)
            elif report.outcome == "skipped":
                self.summary["skipped"] += 1
                entry["reason"] = str(getattr(report, "wasxfail", getattr(report, "longrepr", "skipped")))
            self.results.append(entry)

    def pytest_sessionfinish(self, session, exitstatus):
        self.duration = round(time.time() - self.start_time, 2)


def run_tests(
    tier: int | None = None,
    feature: str | None = None,
    strict: bool = False,
    json_report_path: str | None = None,
    keyword: str | None = None,
) -> int:
    """Execute pytest with specified options and return exit code."""
    if strict:
        os.environ["STRICT_E2E"] = "1"
    else:
        os.environ.setdefault("STRICT_E2E", "0")

    pytest_args = build_pytest_args(tier=tier, feature=feature, keyword=keyword)
    print("=" * 80)
    print("  AUTONOMOUS MULTI-AGENT VISUAL DOCUMENTATION SYSTEM — E2E TEST SUITE")
    print(f"  Scope: Features F1-F8 | Strict Mode: {strict} | Tier: {tier or 'All (1-4)'}")
    print("=" * 80)

    json_plugin = JsonReportPlugin()
    exit_code = pytest.main(pytest_args, plugins=[json_plugin])

    print("\n" + "=" * 80)
    print(f"  EXECUTION SUMMARY:")
    print(f"  Total: {json_plugin.summary['total']} | Passed: {json_plugin.summary['passed']} | "
          f"Failed: {json_plugin.summary['failed']} | Skipped: {json_plugin.summary['skipped']} | "
          f"Duration: {json_plugin.duration}s")
    print("=" * 80)

    if json_report_path:
        out_p = Path(json_report_path).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        report_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "summary": json_plugin.summary,
            "duration_seconds": json_plugin.duration,
            "exit_code": int(exit_code),
            "strict_mode": strict,
            "results": json_plugin.results,
        }
        out_p.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
        print(f"  [+] Structured JSON report written to: {out_p}")

    # Determine exit code: 0 if all passed (or skipped in progressive mode), 1 if failure
    if json_plugin.summary["failed"] > 0:
        return 1
    return 0 if exit_code in (0, 5) else int(exit_code)


def main():
    parser = argparse.ArgumentParser(description="Autonomous Visual Documentation E2E Test Runner")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3, 4], help="Run a specific test tier (1-4)")
    parser.add_argument("--feature", type=str, choices=["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"],
                        help="Filter by feature (F1-F8)")
    parser.add_argument("--strict", action="store_true", help="Enforce strict mode (fail on unbuilt milestones)")
    parser.add_argument("--all", action="store_true", help="Run all test tiers (default)")
    parser.add_argument("-k", "--keyword", type=str, help="Pytest keyword expression filter")
    parser.add_argument("--json-report", type=str, help="Path to write JSON execution report")

    args = parser.parse_args()
    code = run_tests(
        tier=args.tier,
        feature=args.feature,
        strict=args.strict,
        json_report_path=args.json_report,
        keyword=args.keyword,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
