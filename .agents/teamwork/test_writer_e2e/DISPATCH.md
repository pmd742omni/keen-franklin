# Dispatch: E2E Test Suite Writer

## Objective
Design and implement the complete, opaque-box 4-tier E2E test suite for the Windows 11 Laptop Optimizer.
Produce `TEST_INFRA.md` and `TEST_READY.md`.

## Ownership
- `c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/tests/**`
- `c:/Users/ignaz/antigravity/keen-franklin/TEST_READY.md`
- `c:/Users/ignaz/antigravity/keen-franklin/TEST_INFRA.md`

## 2026-09-29T12:05:07Z
You are the E2E Test Suite Writer (test_writer_e2e).
Working directory: c:/Users/ignaz/antigravity/keen-franklin/.agents/teamwork/test_writer_e2e
Original request path: c:/Users/ignaz/antigravity/keen-franklin/.agents/teamwork/ORIGINAL_REQUEST.md
Project plan path: c:/Users/ignaz/antigravity/keen-franklin/PROJECT.md
Target project directory: c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer

Task:
1. Read ORIGINAL_REQUEST.md and PROJECT.md carefully.
2. Design and build a comprehensive, opaque-box E2E testing suite in `c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/tests/`.
   - Test runner: `tests/run_all_tests.ps1` that can execute all tiers or individual tiers, returning exit code 0 on all pass, non-zero on failure.
   - Tier 1: Feature Coverage tests (verifying baseline profiling, disk cleanup dry-run, memory trimming dry-run, power scheme query, CLI parameter parsing, presets existence).
   - Tier 2: Boundary & Corner Cases (empty parameters, invalid presets, non-elevated behavior, zero disk space threshold, read-only temp files, missing registry keys, corrupted snapshot handling).
   - Tier 3: Cross-Feature Combinations (e.g., Snapshot + QuickBoost + Compare, DryRun + DeepClean + Verify unchanged disk, Backup + GamingMode + RestoreDefaults).
   - Tier 4: Real-World Application Scenarios (end-to-end user workflow: baseline benchmark -> deep clean -> verify reclamation -> rollback -> verify restore).
3. Ensure progressive testability: tests must mock or check dry-run where elevation is needed so that tests can execute cleanly and verify logic in standard CI/worker environments.
4. Author `c:/Users/ignaz/antigravity/keen-franklin/TEST_INFRA.md` following the template in the project guide.
5. Once test suite is implemented and tested, publish `c:/Users/ignaz/antigravity/keen-franklin/TEST_READY.md`.
6. Write your handoff to `c:/Users/ignaz/antigravity/keen-franklin/.agents/teamwork/test_writer_e2e/handoff.md` and notify parent via send_message.

Exclusive File Ownership:
`c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/tests/**`
`c:/Users/ignaz/antigravity/keen-franklin/TEST_INFRA.md`
`c:/Users/ignaz/antigravity/keen-franklin/TEST_READY.md`

