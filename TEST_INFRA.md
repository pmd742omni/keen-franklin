# Test Infrastructure & Testing Strategy

**Project**: Windows 11 Laptop Optimizer (HP Laptop 15 / Intel N100)  
**Author**: E2E Test Suite Writer (`test_writer_e2e`)  
**Scope**: Opaque-box E2E Test Suite (Tiers 1–4) & Progressive Testability Framework  
**Location**: `laptop_optimizer/tests/`  

---

## 1. Overview & Strategy

The Windows 11 Laptop Optimizer test suite is engineered as an **opaque-box, multi-tier, zero-external-dependency** testing framework written entirely in native Windows PowerShell (compatible with Windows PowerShell 5.1 and PowerShell 7+).

Because the system targets resource-constrained, low-power quad-core hardware (HP Laptop 15, Intel N100, 8GB RAM, Windows 11 Home 26200), the testing infrastructure adheres to five fundamental architectural tenets:

1. **Zero External Dependencies**: Operates out-of-the-box on standard Windows 11 installations without requiring `Pester`, chocolatey packages, or external modules.
2. **Opaque-Box Contract Verification**: Evaluates system behavior strictly against public CLI parameters, preset interfaces, and interface contracts defined in `PROJECT.md`.
3. **Progressive Testability**: Decoupled test architecture that detects implemented components across milestone cycles (M1–M4), testing available modules while marking unbuilt modules as pending/skipped without breaking the build or returning false negative exit codes.
4. **Non-Destructive & Non-Elevated Execution**: Incorporates isolated temporary sandbox fixtures in `%TEMP%` and validates dry-run contracts (`-DryRun`), allowing comprehensive CI/worker pipeline verification without requiring Administrator elevation or altering host files.
5. **Deterministic Exit Codes**: Emits exit code `0` on 100% test success (or skipped pending items), and exit code `1` on any assertion failure.

---

## 2. Test Architecture (4 Tiers)

```
laptop_optimizer/tests/
├── run_all_tests.ps1           # Master Test Runner (CLI, tier selection, JSON reporting)
├── test_harness.ps1            # Lightweight BDD engine, assertions, fixtures, sandboxes
├── tier1_feature_tests.ps1     # Tier 1: Feature Coverage & Contract Verification
├── tier2_boundary_tests.ps1    # Tier 2: Boundary, Negative & Corner Cases
├── tier3_combination_tests.ps1 # Tier 3: Cross-Feature Multi-Component Integration
└── tier4_application_tests.ps1 # Tier 4: Real-World End-to-End User Scenarios
```

### Tier 1: Feature Coverage & Interface Contracts
- **Scope**: Verifies individual module functions, data contracts, and public APIs.
- **Coverage**:
  - `src/Common/Platform.ps1`: OS detection, CPU architecture, core counts, RAM sizing, and `Test-IsElevated`.
  - `src/Common/Types.ps1`: Native Win32 P/Invoke definitions (`LaptopOptimizer.Win32Native`), foreground process tracking, and safe working set trimming.
  - `src/Diagnostics/Profiler.ps1`: `Get-LaptopStartupItems` registry scanner and `Get-LaptopSystemSnapshot` baseline snapshot contract (14 mandatory properties + ranges).
  - `src/Diagnostics/Comparison.ps1`: `Compare-LaptopSnapshots` delta calculations (RAM gained, storage reclaimed, process delta), acceptance criteria evaluator, Markdown report generation, and structured JSON output.
  - `src/StorageOptimizer/DiskCleanup.ps1`: Safe disk cleanup dry-run interface contract (`Invoke-SafeDiskCleanup -DryRun`).
  - `src/MemoryOptimizer/RamTrimmer.ps1`: RAM working set trimming dry-run interface contract (`Invoke-RamWorkingSetTrim -DryRun`).
  - `src/StorageOptimizer/SsdTrim.ps1`: SSD TRIM dry-run contract (`Invoke-SsdTrim -DryRun`).
  - Native Power Scheme Query: `powercfg /getactivescheme` GUID detection without elevation.
  - Optimization Presets: Syntax and structure for `QuickBoost`, `DeepClean`, `GamingMode`, and `RestoreDefaults`.
  - Master Orchestrator CLI: `Optimize-Laptop.ps1` AST parameter block validation (`-Preset`, `-DryRun`, `-NonInteractive`).
  - Batch Wrapper: `optimize.bat` UTF-8 code page (65001), UAC elevation checks, and argument forwarding.

### Tier 2: Boundary & Corner Cases
- **Scope**: Probes failure modes, extreme values, missing dependencies, permissions, and corrupted state.
- **Coverage**:
  - Null & Empty Inputs: Rejection of null baseline or post-optimization snapshots in `Compare-LaptopSnapshots`.
  - Zero & Negative Deltas: Memory consumption during runs, negative disk space changes, and exact threshold boundaries (`FreeRAM = 1500 MB` and `StorageReclaimed = 1.0 GB`).
  - Invalid Presets: Rejection of non-existent preset names in `Optimize-Laptop.ps1`.
  - File System Edge Cases: Read-only temporary files (`[FileAttributes]::ReadOnly`) and locked in-use files (`FileShare.None`) during safe disk cleanup, verifying graceful skipping and non-fatal error logging.
  - Registry Resilience: Handling missing or corrupted startup registry keys without unhandled exceptions.
  - Corrupted Snapshots: 0-byte files, malformed JSON, and truncated schemas rejected safely during state restore operations.

### Tier 3: Cross-Feature Combinations
- **Scope**: Verifies interactions between two or more system subsystems.
- **Coverage**:
  - **Combination 1 (Snapshot + QuickBoost + Compare)**: Captures baseline system state, applies QuickBoost dry-run, captures post-snapshot, and executes comparison engine.
  - **Combination 2 (DryRun + DeepClean + Disk Verification)**: Populates a mock filesystem fixture with sized temporary files, runs DeepClean with `-DryRun`, and asserts byte-level file preservation on disk.
  - **Combination 3 (Backup + GamingMode + RestoreDefaults)**: Generates atomic snapshot backup, simulates gaming power configuration, and executes full state restore.
  - **Combination 4 (NonInteractive + Structured Logging)**: Validates headless execution and verifies log output matches ISO-8601 timestamps (`\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}`) with multi-channel levels (`INFO`, `WARN`, `ERROR`).

### Tier 4: Real-World Application Scenarios
- **Scope**: End-to-end full user workflows matching real-world operational execution.
- **Coverage**:
  - **Scenario 1 (Full User Lifecycle)**:
    1. Capture pre-optimization baseline benchmark (`Get-LaptopSystemSnapshot`).
    2. Create state configuration backup (`pre_optimization_snapshot.json`).
    3. Execute optimization pass (`-Preset DeepClean -DryRun`).
    4. Capture post-optimization benchmark.
    5. Evaluate metric deltas and verify acceptance criteria.
    6. Export Markdown and JSON reports to disk.
    7. Execute rollback (`Restore-LaptopSnapshot`) and verify restoration.
  - **Scenario 2 (Headless Agent Automation)**: Validates non-interactive invocation pattern conforming to custom Antigravity skill requirements.
  - **Scenario 3 (Batch Wrapper CLI Invocation)**: Validates `optimize.bat` CLI arguments, help display, and process exit code propagation.

---

## 3. Test Harness Design (`test_harness.ps1`)

The custom test harness provides a structured, expressive BDD syntax with built-in sandbox management and reporting:

### BDD Primitives
```powershell
Describe "Suite Name" -Tier 1 {
    Context "Feature Group" {
        It "should satisfy specific behavior" {
            Assert-Equal $expected $actual
        }
    }
}
```

### Native Assertion Library
| Assertion | Description |
|---|---|
| `Assert-Equal -Expected $e -Actual $a` | Exact equality (handles doubles with epsilon tolerance) |
| `Assert-NotEqual -Expected $e -Actual $a` | Inequality check |
| `Assert-True -Condition $c` | Evaluates boolean condition to true |
| `Assert-False -Condition $c` | Evaluates boolean condition to false |
| `Assert-Null -Value $v` | Asserts value is null (supports `[AllowNull()]`) |
| `Assert-NotNull -Value $v` | Asserts value is not null |
| `Assert-GreaterThan -Value $v -Threshold $t` | Numeric threshold comparison ($v > $t) |
| `Assert-LessThan -Value $v -Threshold $t` | Numeric threshold comparison ($v < $t) |
| `Assert-Match -InputString $s -Pattern $p` | Regex pattern matching |
| `Assert-Contains -Collection $col -Item $item`| Collection element membership |
| `Assert-Throws -ScriptBlock $sb [-Pattern $p]` | Asserts scriptblock throws expected exception |
| `Skip-Test -Reason "..."` | Marks test as pending/skipped without failing suite |

### Sandbox & Fixtures Engine
- `New-TestSandbox -Prefix "Test_"`: Generates an isolated temporary folder structure under `$env:TEMP` with mock user temp, Windows temp, browser cache, and backup folders.
- `Remove-TestSandbox -SandboxPath <path>`: Clears read-only attributes, releases locks, and deletes sandbox recursively.
- `New-MockFile -Path <path> -SizeBytes <n>`: Creates sized binary or text fixtures.
- `New-SyntheticSnapshot`: Generates customizable, contract-compliant system snapshot objects for deterministic unit and boundary testing.

---

## 4. How to Run the Tests

### Master Test Runner
Run from PowerShell in the project directory:

```powershell
# Run the entire test suite (All Tiers 1-4)
powershell -ExecutionPolicy Bypass -File tests/run_all_tests.ps1

# Run a specific tier only
powershell -ExecutionPolicy Bypass -File tests/run_all_tests.ps1 -Tier 1
powershell -ExecutionPolicy Bypass -File tests/run_all_tests.ps1 -Tier 2
powershell -ExecutionPolicy Bypass -File tests/run_all_tests.ps1 -Tier 3
powershell -ExecutionPolicy Bypass -File tests/run_all_tests.ps1 -Tier 4

# Run tests matching a specific name pattern
powershell -ExecutionPolicy Bypass -File tests/run_all_tests.ps1 -TestName "Boundary"

# Export structured JSON execution report
powershell -ExecutionPolicy Bypass -File tests/run_all_tests.ps1 -JsonReport "reports/test_results.json"
```

### Exit Codes
- **`0`**: All executed tests passed successfully (0 failures).
- **`1`**: One or more assertions failed.
- **`2`**: Harness initialization or fatal configuration error.

---

## 5. Progressive Testability & CI Integration

The test suite dynamically adapts across project milestones:
- Implemented components (e.g. Milestone M1: `Platform.ps1`, `Types.ps1`, `Profiler.ps1`, `Comparison.ps1`) are executed directly against the live system.
- Components planned for future milestones (e.g. `DiskCleanup.ps1` for M2, `Optimize-Laptop.ps1` for M3) are detected via `Test-Path`. If absent, tests gracefully record a `[ SKIP ]` status with the target milestone.
- As workers implement subsequent milestones, the test suite automatically transitions skipped tests into active execution without requiring modifications to test code.
