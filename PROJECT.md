# Project: Windows 11 Laptop Optimizer (HP Laptop 15 / Intel N100)

## Architecture

The Windows 11 Laptop Optimizer is a zero-dependency, modular, native Windows PowerShell 5.1/7+ and Batch optimization suite designed specifically for low-power quad-core systems (Intel N100, 8GB RAM, Windows 11 Home 26200).

```
laptop_optimizer/
├── optimize.bat                     # UTF-8 Batch launcher with UAC detection & headless guards
├── Optimize-Laptop.ps1              # Master orchestrator CLI script (PS 5.1 / 7+ compatible)
├── src/
│   ├── Common/
│   │   ├── Platform.ps1             # OS build, CPU architecture, elevation check, hardware info
│   │   └── Types.ps1                # Native C# P/Invoke definitions (EmptyWorkingSet, ForegroundWindow)
│   ├── Logger/
│   │   └── Logger.ps1               # Multi-channel structured logging (Console, Disk ISO-8601, Transcript)
│   ├── SafetyEngine/
│   │   ├── Snapshot.ps1             # Tier 1 Atomic JSON state snapshot & registry export
│   │   ├── Restore.ps1              # Tier 1 Non-reboot rollback engine (services, startup, power plan)
│   │   └── SystemRestore.ps1        # Tier 2 Checkpoint-Computer integration (defense-in-depth)
│   ├── Diagnostics/
│   │   ├── Profiler.ps1             # R1: Live snapshot of CPU, RAM, MemComp, Pagefile, Disk, Power, Tasks
│   │   └── Comparison.ps1           # R1: Baseline vs After metric comparator & acceptance criteria evaluator
│   ├── StorageOptimizer/
│   │   ├── DiskCleanup.ps1          # R2: Safe cache removal (>1GB safe cache: Temp, Explorer, Browser, CrashDumps)
│   │   └── SsdTrim.ps1              # R2: NVMe SSD TRIM execution via Optimize-Volume & defrag /L fallback
│   ├── MemoryOptimizer/
│   │   └── RamTrimmer.ps1           # R2: Working set trimming with foreground protection & paging churn guard
│   ├── ServiceOptimizer/
│   │   ├── ServiceTuning.ps1        # R2: Safe background service tuning (DiagTrack, SysMain, HP OEM bloat)
│   │   └── StartupTuning.ps1        # R2: Reversible startup bloat disabling via StartupApproved registry
│   └── MenuUI/
│       ├── AsciiArt.ps1             # ASCII headers, banners, styling
│       └── Menu.ps1                 # Interactive terminal menu with live hardware status bar
├── presets/
│   ├── QuickBoost.ps1               # Working set trim, user temp cleanup, priority boost
│   ├── DeepClean.ps1                # Full cache purge, DO cache, crash dumps, SSD TRIM, service tuning
│   ├── GamingMode.ps1               # High Performance power scheme unlock, background telemetry throttle
│   └── RestoreDefaults.ps1          # Reverts all settings using the Tier 1 snapshot
├── backups/                         # Atomic JSON snapshots and .reg backups
├── logs/                            # Execution logs (optimizer_run_YYYYMMDD_HHMMSS.log)
├── reports/                         # Metric comparison reports (JSON & Markdown)
├── docs/                            # R4: Comprehensive documentation suite
│   ├── ARCHITECTURE.md
│   ├── USER_GUIDE.md
│   ├── SAFETY_GUIDE.md
│   └── PRESETS.md
├── laptop-optimizer/                # R4: Antigravity Custom Skill
│   ├── SKILL.md                     # Skill description & YAML metadata
│   ├── scripts/
│   │   └── run_optimizer.ps1        # Headless agent automation wrapper
│   ├── references/
│   │   ├── presets_guide.md
│   │   └── safety_and_rollback.md
│   └── examples/
│       └── sample_optimization_report.json
├── tests/                           # Dual Track E2E Test Suite (Tiers 1-4)
│   ├── run_all_tests.ps1            # Standalone test runner
│   ├── tier1_feature_tests.ps1
│   ├── tier2_boundary_tests.ps1
│   ├── tier3_combination_tests.ps1
│   └── tier4_application_tests.ps1
└── README.md                        # Master project documentation
```

## Feature Inventory

Every feature derived from user requirements and empirical survey is inventoried below with an assigned milestone:

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Baseline System Profiling | Captures CPU, RAM, MemCompression, Pagefile, Disk, Power, Process count in structured object | M1 | ORIGINAL_REQUEST §R1 |
| 2 | Memory Compression Tracking | Tracks PID 4452 WorkingSet and PerfOS_Memory counters un-elevated | M1 | ORIGINAL_REQUEST §R1 |
| 3 | Paging File & Churn Analysis | Measures Win32_PageFileUsage (12GB dynamic) and virtual memory commit | M1 | ORIGINAL_REQUEST §R1 |
| 4 | Startup & Scheduled Task Audit | Scans HKCU/HKLM Run keys, StartupApproved, and 163 active scheduled tasks | M1 | ORIGINAL_REQUEST §R1 |
| 5 | Top Resource Process Profiler | Lists top memory/CPU processes (WorkingSet64, PrivateMemorySize64) | M1 | ORIGINAL_REQUEST §R1 |
| 6 | Metric Comparison & Reporting | Computes exact delta (RAM MB, Disk GB, Procs) and exports JSON/Markdown reports | M1 | ORIGINAL_REQUEST §R1 |
| 7 | Safe Cache Storage Cleanup | Purges >1GB of Temp, Explorer thumbnails, Browser caches, CrashDumps without touching user docs | M2 | ORIGINAL_REQUEST §R2 |
| 8 | Windows Update & DO Cleanup | Safely clears SoftwareDistribution\Download and DeliveryOptimization cache | M2 | ORIGINAL_REQUEST §R2 |
| 9 | NVMe SSD TRIM Execution | Trims drive C: via Optimize-Volume -ReTrim and defrag /L fallback | M2 | ORIGINAL_REQUEST §R2 |
| 10 | RAM Working Set Trimming | Native P/Invoke EmptyWorkingSet freeing physical RAM >1.5GB | M2 | ORIGINAL_REQUEST §R2 |
| 11 | Foreground Process Protection | Resolves active HWND via GetForegroundWindow to prevent UI freezing | M2 | Survey Explorer 2 |
| 12 | Paging Churn Mitigation Guard | Prevents thrashing by leveraging standby list and event-driven invocation | M2 | ORIGINAL_REQUEST §R2 |
| 13 | HP OEM & Telemetry Tuning | Safely adjusts DiagTrack, SysMain, and 8 HP OEM background services | M2 | ORIGINAL_REQUEST §R2 |
| 14 | Reversible Startup Optimization| Toggles StartupApproved Byte 0 (0x02 to 0x03) with .reg rollback | M2 | Survey Explorer 1 & 2 |
| 15 | Standalone Batch Wrapper | optimize.bat with UTF-8, UAC elevation prompt, headless agent flag, double-click pause | M3 | ORIGINAL_REQUEST §R3 |
| 16 | Master PowerShell Orchestrator | Optimize-Laptop.ps1 with full parameter binding (-Preset, -DryRun, -Backup, -NonInteractive) | M3 | ORIGINAL_REQUEST §R3 |
| 17 | Interactive ASCII Terminal Menu | Terminal menu with ASCII banner and live hardware status bar | M3 | ORIGINAL_REQUEST §R3 |
| 18 | Safe Preset: Quick Boost | Fast RAM working set trim, user temp flush, responsiveness tuning | M3 | ORIGINAL_REQUEST §R3 |
| 19 | Safe Preset: Deep Clean | Complete cache purge, Delivery Optimization, crash dumps, SSD TRIM | M3 | ORIGINAL_REQUEST §R3 |
| 20 | Safe Preset: Gaming / Perf Mode| Unlocks & activates High Performance power scheme GUID, suppresses telemetry | M3 | ORIGINAL_REQUEST §R3 |
| 21 | Safe Preset: Restore Defaults | Reverts all services, startup items, and power schemes from Tier 1 snapshot | M3 | ORIGINAL_REQUEST §R3 |
| 22 | Tier 1 Atomic State Snapshot | Serializes services, startup, power plan to JSON and registry backups | M3 | ORIGINAL_REQUEST §R3 |
| 23 | Non-Destructive Dry-Run Mode | -DryRun flag simulates actions, logs savings without modifying disk or services | M3 | ORIGINAL_REQUEST §R3 |
| 24 | Tier 2 System Restore Point | Attempts Checkpoint-Computer with graceful degradation on Win 11 Home | M3 | ORIGINAL_REQUEST §R3 |
| 25 | Structured Multi-Channel Logging| Disk logs (ISO-8601 timestamps), color console, automatic log rotation | M3 | ORIGINAL_REQUEST §R3 |
| 26 | Antigravity Custom Skill | laptop-optimizer skill conforming to Antigravity standard (SKILL.md, scripts, refs) | M4 | ORIGINAL_REQUEST §R4 |
| 27 | Comprehensive Documentation | README.md, ARCHITECTURE.md, USER_GUIDE.md, SAFETY_GUIDE.md, PRESETS.md | M4 | ORIGINAL_REQUEST §R4 |
| 28 | Opaque-Box E2E Test Suite | 4-tier test suite (Tiers 1-4) verifying all acceptance criteria independently | E2E | Acceptance Criteria |
| 29 | Adversarial Coverage Hardening | Tier 5 white-box stress testing, edge-case probing, regression guards | M5 | Acceptance Criteria |

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | E2E Testing Suite Track | Opaque-box test harness, runner, and test cases covering Tiers 1-4; produces TEST_READY.md | none | IN_PROGRESS |
| M1 | Diagnostics & Profiling Module | Profiler.ps1, Comparison.ps1, Types.ps1, Platform.ps1, baseline JSON/MD reporting | none | IN_PROGRESS |
| M2 | Storage & Memory Reclamation Engine | DiskCleanup.ps1, SsdTrim.ps1, RamTrimmer.ps1, ServiceTuning.ps1, StartupTuning.ps1 | M1 | PLANNED |
| M3 | CLI, Presets, Safety Rollback & Logging | optimize.bat, Optimize-Laptop.ps1, Snapshot.ps1, Restore.ps1, Logger.ps1, MenuUI, 4 presets | M1, M2 | PLANNED |
| M4 | Antigravity Custom Skill & Documentation | laptop-optimizer/ (SKILL.md, scripts, refs), docs/ (User, Safety, Architecture, Presets guides) | M3 | PLANNED |
| M5 | Final E2E Verification & Adversarial Hardening | Pass 100% of E2E tests (Tiers 1-4), execute Tier 5 adversarial stress testing, Forensic Audit | E2E, M4 | PLANNED |

## Interface Contracts

### Diagnostics ↔ Optimization / CLI
- `Get-LaptopSystemSnapshot [-Detailed]` -> Returns `[PSCustomObject]` containing:
  - `Timestamp`: `[datetime]`
  - `OS`: `[string]`
  - `FreeRAM_MB`: `[double]`
  - `TotalRAM_GB`: `[double]`
  - `FreeRAM_Percent`: `[double]`
  - `MemoryCompression_MB`: `[double]`
  - `PageFile_Usage_MB`: `[double]`
  - `PageFile_Allocated_MB`: `[double]`
  - `DriveC_Free_GB`: `[double]`
  - `DriveC_Total_GB`: `[double]`
  - `ActivePowerScheme`: `[string]` (Name and GUID)
  - `ProcessCount`: `[int]`
  - `StartupItemsCount`: `[int]`
  - `TopProcesses`: `[array]` (Name, Id, WS_MB, CPU_Sec)
- `Compare-LaptopSnapshots -Baseline $b -Current $c` -> Returns `[PSCustomObject]` containing:
  - `RAMGained_MB`: `[double]`
  - `StorageReclaimed_GB`: `[double]`
  - `ProcessDelta`: `[int]`
  - `PassesAcceptanceCriteria`: `[bool]` (Free RAM > 1500MB, Reclaimed Storage >= 1GB)
  - `ReportMarkdown`: `[string]`

### SafetyEngine ↔ CLI / Presets
- `New-LaptopSnapshot -BackupDir <path>` -> Returns `[string]` (Path to atomic snapshot JSON)
- `Restore-LaptopSnapshot -SnapshotFile <path>` -> Returns `[PSCustomObject]` (Success, RestoredItems, Errors)
- `Invoke-SystemRestorePoint -Description <string>` -> Returns `[bool]` (True if created, False if throttled/disabled)

### Storage & Memory ↔ CLI
- `Invoke-SafeDiskCleanup [-DryRun] [-IncludeDeliveryOptimization] [-IncludeBrowserCache]` -> Returns `[PSCustomObject]` (BytesReclaimed, ItemsRemoved, Errors)
- `Invoke-SsdTrim [-DriveLetter "C"] [-DryRun]` -> Returns `[PSCustomObject]` (Success, MethodUsed, Output)
- `Invoke-RamWorkingSetTrim [-ExcludePids <int[]>] [-DryRun]` -> Returns `[PSCustomObject]` (BeforeFree_MB, AfterFree_MB, Gained_MB, ProcessesTrimmed)

## Code Layout

Target Directory: `c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer`
All implementation files and modules will be written exclusively inside this target directory.
Test runner and test files will reside in `c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/tests`.
Antigravity skill files will reside in `c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/laptop-optimizer`.
Agent coordination metadata remains strictly inside `.agents/teamwork/`.
