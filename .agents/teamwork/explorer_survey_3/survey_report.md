# Architecture & Specification Report: CLI, Presets, Safety, Logging & Antigravity Custom Skill (Requirements R3 & R4)

**Agent**: `explorer_survey_3`  
**Date**: 2026-09-29  
**Target Environment**: HP Laptop 15 (Intel N100, 8GB RAM, Windows 11 Home Build 26200)  
**Target Project Directory**: `c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer`  
**Integrity Mode**: Development / Zero Third-Party Dependencies  

---

## 1. Executive Summary & Core Architectural Principles

Requirements **R3** (Standalone, One-Click Optimization CLI Tool) and **R4** (Performance Skill & Documentation) define the operational delivery and automation layers of the Windows 11 Laptop Optimizer. The solution must balance two primary user personas:
1. **Human End-User**: Needs a zero-friction, one-click launcher (`optimize.bat`) with an interactive, colorized ASCII terminal menu, clear preset descriptions, and fool-proof safety guards.
2. **Autonomous Antigravity Agent / CI Runner**: Needs a headless, non-interactive CLI interface (`Optimize-Laptop.ps1`) supporting granular parameters, automated dry-run simulations, atomic rollback snapshots, and machine-readable JSON metrics output.

### 1.1 Core Architectural Principles

1. **Zero Third-Party Dependencies**:
   - The entire toolchain must run out-of-the-box on a clean Windows 11 Home installation without installing Python, Chocolatey, Scoop, Winget packages, Sysinternals tools, or third-party PowerShell modules.
   - Built entirely on native **Windows PowerShell 5.1** (compatible with PowerShell 7+), `cmd.exe`, native Windows management utilities (`powercfg.exe`, `dism.exe`, `cleanmgr.exe`, `fsutil.exe`), and Win32 P/Invoke APIs (`EmptyWorkingSet` via `psapi.dll`).
2. **Non-Destructive Execution & Multi-Tier Safety**:
   - Every system modification (services, power plan, registry) must be preceded by an atomic, machine-readable state snapshot (`.json`) and registry backup (`.reg`).
   - Secondary integration with Windows System Restore (`Checkpoint-Computer`) with graceful non-blocking degradation if System Protection is disabled or rate-limited.
   - Full simulation capability (`-DryRun`) that computes prospective disk savings and previews service/registry modifications without modifying system state.
3. **Dual-Mode Ergonomics**:
   - Interactive Mode: Rich ASCII menu with live system telemetry header (CPU, RAM, Disk, Power Plan, Admin status).
   - Headless Mode: Fully automated, idempotent, quiet, and scriptable via standard CLI flags (`-Preset`, `-DryRun`, `-Backup`, `-Report`, `-OutputFormat JSON`).
4. **Complete Auditability & Observability**:
   - Dual-channel logging: color-coded concise console output and high-fidelity timestamped disk logs (`logs/optimizer_run_*.log`).
   - Before-and-after metric verification recording concrete improvements (Free RAM in MB, Free Disk in GB, Background Process Count).
5. **Agent-Native Extensibility**:
   - Packaged as a standard Antigravity Custom Skill (`laptop-optimizer`) conforming to the official plugin and skill specifications observed in the Antigravity runtime environment.

---

## 2. Environment Verification & Baseline Constraints

Empirical verification conducted directly on the target machine yielded the following technical constraints:

| Parameter | Measured Specification | Architectural Impact |
|---|---|---|
| **OS Build** | Windows 11 Home Single Language (10.0.26200.0) | Group Policy (`gpedit.msc`) is unavailable; all policy and system tweaks must be applied via registry (`HKLM`/`HKCU`). |
| **PowerShell Runtime** | Windows PowerShell 5.1.26100.9444 | PowerShell Core 7 (`pwsh`) is **not installed** by default. Scripts must strictly adhere to PowerShell 5.1 syntax and cmdlet availability. |
| **Execution Policy** | `RemoteSigned` | Local batch launcher must explicitly pass `-ExecutionPolicy Bypass -NoProfile` when invoking `.ps1` scripts. |
| **Default Elevation** | Standard User (`IsAdmin: False`) | Optimization tasks (service modifications, TRIM, working set trimming across system processes, Dism) require elevation. `optimize.bat` must implement automated UAC self-elevation. |
| **Power Schemes** | Only `Balanced` (`381b4222-f694-41f0-9685-ff5bb260df2e`) present | "High Performance" and "Ultimate Performance" schemes must be dynamically unlocked/duplicated via `powercfg -duplicatescheme` and tracked for rollback. |
| **System Restore** | Volume Shadow Copy (`vss`) stopped; standard user access denied | `Checkpoint-Computer` requires admin privileges and will fail if System Protection is disabled on drive C:. A custom JSON state snapshot engine is mandatory as the primary rollback layer. |
| **Native RAM Trimming** | `psapi.dll::EmptyWorkingSet` verified functional | Verified via in-memory C# compilation (`Add-Type`); returns `True` and successfully evacuates working set memory without external tools. |

---

## 3. Standalone One-Click CLI Architecture

### 3.1 `optimize.bat` — The Zero-Friction Launcher

The batch wrapper serves as the universal entry point. It eliminates PowerShell execution policy barriers, handles UAC elevation cleanly, preserves terminal encoding, and forwards all arguments to the underlying PowerShell orchestrator.

#### Key Functional Requirements for `optimize.bat`:
1. **Console UTF-8 Code Page**: Executes `chcp 65001 >nul` to prevent box-drawing characters and status indicators from rendering as garbage.
2. **UAC Elevation Detection**: Uses `net session >nul 2>&1` (which returns exit code 0 if elevated, 2 if standard user) to determine privilege level.
3. **Headless / Non-Interactive Guard**: Scans command-line arguments for `-NonInteractive`, `-Headless`, or `-NoElevationPrompt`. If running in automated/agent mode without admin rights, it exits immediately with error code `2` to prevent stalling on an interactive UAC prompt.
4. **Self-Elevation Elevation**: In interactive mode, if standard user, invokes PowerShell `Start-Process cmd.exe -ArgumentList '/c', '""%~f0""', '%*' -Verb RunAs` and terminates the unprivileged caller.
5. **Parameter & Quote Preservation**: Forwards `%*` directly to `powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0Optimize-Laptop.ps1" %*`.
6. **Explorer Double-Click Detection**: Determines whether it was launched from File Explorer (`echo %cmdcmdline% | find /i "%~0"`) vs an active CLI session. If double-clicked, it pauses before exiting so the user can read the completion report.
7. **Exit Code Propagation**: Captures `%ERRORLEVEL%` from PowerShell and exits with the exact same exit code (`exit /b %EXIT_CODE%`).

#### Complete Production Design for `optimize.bat`:
```cmd
@echo off
setlocal EnableDelayedExpansion

:: 1. Force UTF-8 Code Page for clean ASCII/box rendering
chcp 65001 >nul

:: 2. Check for Administrative Privileges
net session >nul 2>&1
if %ERRORLEVEL% equ 0 (
    goto :RunPowerShell
)

:: 3. Check for Headless / Non-Interactive flags
for %%A in (%*) do (
    if /i "%%A"=="-NonInteractive" goto :NoElevateFail
    if /i "%%A"=="-Headless" goto :NoElevateFail
    if /i "%%A"=="-NoElevationPrompt" goto :NoElevateFail
)

:: 4. Prompt for UAC Elevation (Interactive Mode)
echo ========================================================================
echo   Windows 11 Laptop Optimizer - Elevation Required
echo ========================================================================
echo [INFO] Administrative privileges are required to optimize system services,
echo        reclaim protected caches, and trim memory working sets.
echo [INFO] Requesting elevation via Windows UAC...
echo.

powershell -NoProfile -Command "Start-Process cmd.exe -ArgumentList '/c \"\"%~f0\"\" %*' -Verb RunAs"
exit /b %ERRORLEVEL%

:NoElevateFail
echo [ERROR] Administrative privileges are required but script was invoked non-interactively without elevation. >&2
echo [ERROR] Rerun the command from an elevated (Administrator) command prompt or terminal. >&2
exit /b 2

:RunPowerShell
:: 5. Execute PowerShell Orchestrator with ExecutionPolicy Bypass
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Optimize-Laptop.ps1" %*
set SCRIPT_EXIT_CODE=%ERRORLEVEL%

:: 6. If launched via double-click from File Explorer, pause before closing
echo %cmdcmdline% | find /i "%~0" >nul
if %ERRORLEVEL% equ 0 (
    echo.
    echo Press any key to exit...
    pause >nul
)

exit /b %SCRIPT_EXIT_CODE%
```

---

### 3.2 `Optimize-Laptop.ps1` — The Master Orchestration Engine

The main PowerShell script acts as the controller. It parses command-line parameters, initializes logging, manages the execution lifecycle, coordinates subsystems, and renders the interactive terminal menu when no parameters are passed.

#### Script Architecture & Subsystem Layout:
```
laptop_optimizer/
├── optimize.bat                     # Standalone batch entry point
├── Optimize-Laptop.ps1              # Master orchestration script
├── src/                             # Modular subsystems (dot-sourced or bundled)
│   ├── Common.ps1                   # Core utilities, P/Invoke, and constants
│   ├── Logger.ps1                   # Structured multi-channel logging engine
│   ├── SafetyEngine.ps1             # JSON snapshot, registry backup, Checkpoint-Computer
│   ├── Diagnostics.ps1              # Metric collection and before/after comparison
│   ├── StorageOptimizer.ps1         # Safe temp/cache cleaning, Dism, SSD TRIM
│   ├── MemoryOptimizer.ps1          # EmptyWorkingSet, standby trim, compression tuning
│   ├── ServiceOptimizer.ps1         # Safe background service and telemetry tuning
│   └── MenuUI.ps1                   # Interactive ASCII menu and status bar renderer
├── backups/                         # Saved state snapshots and registry exports
├── logs/                            # Detailed execution logs
└── reports/                         # Generated Markdown and JSON optimization reports
```

#### Complete CLI Parameter Specification:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `-Preset` | String | `None` | One of: `QuickBoost`, `DeepClean`, `Gaming`, `RestoreDefaults`, `DiagnosticOnly`. If omitted and interactive, opens the menu. |
| `-DryRun` | Switch | `False` | Simulates all actions, calculates prospective bytes freed, lists planned service/registry changes without modifying system state. |
| `-Backup` | Switch | `True` (auto) | Enforces creation of a state snapshot before modifications (can be set to `$false` via `-NoBackup`). |
| `-SkipRestorePoint` | Switch | `False` | Bypasses `Checkpoint-Computer` to prevent delays or errors when System Protection is disabled or throttled. |
| `-RestoreSnapshot` | String | `""` | Restores system state directly from a specific snapshot JSON file path. |
| `-Report` | Switch | `False` | Generates a persistent comparison report file in Markdown and JSON formats. |
| `-ReportPath` | String | `""` | Custom directory or file path for the generated report. |
| `-OutputFormat` | String | `Text` | `Text` (human-readable tables) or `JSON` (raw serialized result object for autonomous agents). |
| `-LogLevel` | String | `INFO` | Logging granularity: `DEBUG`, `INFO`, `WARN`, `ERROR`. |
| `-LogPath` | String | `""` | Custom log file path (defaults to `laptop_optimizer/logs/optimizer_run_<timestamp>.log`). |
| `-NonInteractive` | Switch | `False` | Disables all `Read-Host` prompts, ASCII menus, and confirmation dialogs. Fails fast on missing requirements. |
| `-Force` | Switch | `False` | Automatically confirms all destructive or service modification actions without prompting. |

---

## 4. Interactive Terminal UI & Presets Architecture

### 4.1 ASCII/Terminal Menu Interface (`MenuUI.ps1`)

When executed without parameters in an interactive shell, `Optimize-Laptop.ps1` presents a colorized ASCII terminal interface.

#### Terminal Menu Layout:
```
===================================================================================
     HP Laptop 15 (Intel N100) - Windows 11 Laptop Optimizer v1.0
===================================================================================
  [SYSTEM STATUS]
  CPU: Intel N100 (4C/4T) @ 28% Load        | Free RAM: 742 MB / 7.66 GB (9.5%)
  Storage C: 38.01 GB Free (16.0%)          | Power Plan: Balanced
  Elevation: Administrator                  | OS: Windows 11 Home (Build 26200)
===================================================================================

  Select an Optimization Preset:

  [1] Quick Boost             (Fast RAM trim, temp files, DNS flush, standby memory)
                              ~20 sec | Zero risk | No reboot needed | [RECOMMENDED]

  [2] Deep Clean              (Reclaim GBs: WinUpdate, Delivery Opt, Crash Dumps,
                              WER, Thumbnail caches, Dism cleanup, and SSD TRIM)
                              ~2-4 min | High disk reclamation | Safe & audited

  [3] Gaming / Performance    (High Performance power plan, unpark CPU cores,
                              silence background telemetry & indexing, trim RAM)
                              ~1 min | Maximizes frame pacing & responsiveness

  [4] Restore Defaults        (Rollback: revert services, restore Balanced power plan,
                              reapply original registry values from snapshot)
                              ~30 sec | Restores initial system baseline

  [5] System Diagnostics      (Read-only live inspection of CPU, RAM, Disk, Paging,
                              Memory Compression, Startup apps, and Top Processes)
                              ~5 sec | No changes made

  [6] Advanced / Custom Run   (Configure specific modules, toggle Dry-Run, etc.)

  [0] Exit

-----------------------------------------------------------------------------------
Enter selection [0-6] (or D for Dry-Run toggle): _
```

#### Menu UX Design Rules:
1. **Dynamic Live Telemetry**: Top banner dynamically samples current free RAM, disk headroom, and CPU load via fast CIM queries (`<300ms`).
2. **Dry-Run Indicator**: If Dry-Run mode is toggled, an explicit yellow banner `*** DRY-RUN SIMULATION MODE ACTIVE (NO CHANGES WILL BE APPLIED) ***` is shown.
3. **Esc / Exit Safety**: Pressing `0`, `q`, or `Ctrl+C` exits cleanly with code 0 without applying partial changes.
4. **Post-Execution Pause**: Shows before/after delta metrics and waits for a keystroke before clearing or returning to the menu.

---

### 4.2 Presets Specification Matrix

| Preset | Target Scope | Memory Actions | Storage Actions | Service & Telemetry Actions | Power & System Actions | Safety Level |
|---|---|---|---|---|---|---|
| **Quick Boost** | Immediate responsiveness; RAM de-allocation | `EmptyWorkingSet` across user & background processes; clear standby list. | Clean `$env:TEMP`, `C:\Windows\Temp`, Edge/Chrome cache files. | None (services left untouched). | Flush DNS resolver cache (`Clear-DnsClientCache`). | **100% Safe**; no reboot, no service disruption. |
| **Deep Clean** | Maximum SSD space reclamation & drive health | Everything in Quick Boost. | Purge `SoftwareDistribution\Download`, Delivery Optimization cache, WER reports, crash dumps (`Minidump`, `memory.dmp`), Icon/Thumbnail caches; run `Dism.exe /StartComponentCleanup`; execute SSD `Optimize-Volume -DriveLetter C -ReTrim`. | Safely stops `wuauserv` & `dosvc` during cache purge, then restarts them immediately. | None. | **High Safety**; preserves all user personal files and Windows components. |
| **Gaming / Performance** | Minimum latency, peak single/multi-core throughput | Everything in Quick Boost. | Temporary cache trim. | Temporarily disable or pause `DiagTrack`, `dmwappushservice`, `WSearch` (indexer), and `SysMain` if disk saturates. | Unlock/Activate "High Performance" power plan; disable GameDVR background recording (`GameDVR_Enabled = 0`). | **Audited**; full Tier 1 snapshot created prior to any change. |
| **Restore Defaults** | System rollback | None. | None. | Restores all modified services to their original StartType and Status from snapshot. | Re-activates original `Balanced` power scheme (`381b4222-f694-41f0-9685-ff5bb260df2e`); restores registry values. | **Restorative**; returns system to documented baseline. |
| **Diagnostic Only** | Metric reporting | None (read-only). | None (read-only). | None (read-only). | None (read-only). | **Zero Risk**; read-only. |

---

## 5. Non-Destructive Execution & Rollback Architecture

### 5.1 The Rollback Challenge on Windows 11 Home

Modern Windows 11 Home systems introduce distinct limitations for traditional system recovery:
1. **System Protection Disabled by Default**: To preserve SSD endurance and space on budget 128GB/256GB laptops, OEMs and Windows 11 setups frequently disable System Protection on `C:\`.
2. **Elevation Requirement**: Standard users cannot inspect or create restore points (`Get-ComputerRestorePoint` returns "Access denied").
3. **Creation Frequency Throttling**: Windows enforces a 24-hour rate limit (`SystemRestorePointCreationFrequency`) by default, throwing an error if a restore point was created recently.
4. **Coarse-Grained & Disruptive**: A Windows System Restore requires a full reboot and 15-30 minutes of offline disk activity—unacceptable for simple service or power plan adjustments.

### 5.2 Multi-Tier Safety Engine (`SafetyEngine.ps1`)

To guarantee absolute safety, a **Three-Tier Non-Destructive Safety Architecture** must be implemented:

```
+-------------------------------------------------------------------------+
|                        THREE-TIER SAFETY ENGINE                         |
+-------------------------------------------------------------------------+
|                                                                         |
|  [TIER 1: ATOMIC STATE SNAPSHOT (MANDATORY & INDEPENDENT)]              |
|  - Creates JSON snapshot file in backups/snapshot_<timestamp>.json       |
|  - Records exact service StartType & Status before touching anything    |
|  - Exports affected registry keys to .reg and JSON format               |
|  - Records active Power Scheme GUID                                      |
|  - Instant programmatic rollback without reboot via -Preset Restore     |
|                                                                         |
|  [TIER 2: WINDOWS SYSTEM RESTORE POINT (DEFENSE-IN-DEPTH)]               |
|  - Checks if running elevated and System Protection is enabled on C:    |
|  - Attempts Checkpoint-Computer -Description "LaptopOptimizer_PreRun"   |
|  - Graceful degradation: Catches errors (e.g. rate limit/disabled VSS),  |
|    logs warning, and proceeds safely relying on Tier 1                  |
|                                                                         |
|  [TIER 3: SIMULATION ENGINE (-DryRun)]                                   |
|  - Intercepts all destructive operations (Remove-Item, Set-Service,     |
|    Set-ItemProperty, powercfg)                                          |
|  - Computes exact file sizes and item counts that would be affected     |
|  - Emits [DRYRUN] audit entries to log file and console                 |
+-------------------------------------------------------------------------+
```

### 5.3 Snapshot JSON Data Contract

Every modifying run writes an atomic snapshot to `backups/snapshot_yyyyMMdd_HHmmss.json`.

```json
{
  "SnapshotVersion": "1.0",
  "Timestamp": "2026-09-29T14:30:00.123Z",
  "ComputerName": "HP-LAPTOP-15",
  "OperatingSystem": "Microsoft Windows 11 Home Single Language",
  "OSBuild": "26200.0",
  "PresetInvoked": "Gaming",
  "PowerPlan": {
    "ActiveSchemeGUID": "381b4222-f694-41f0-9685-ff5bb260df2e",
    "ActiveSchemeName": "Balanced"
  },
  "Services": [
    {
      "Name": "DiagTrack",
      "DisplayName": "Connected User Experiences and Telemetry",
      "OriginalStartType": "Automatic",
      "OriginalStatus": "Running"
    },
    {
      "Name": "dmwappushservice",
      "DisplayName": "Device Management WAP Push Service",
      "OriginalStartType": "Manual",
      "OriginalStatus": "Stopped"
    },
    {
      "Name": "WSearch",
      "DisplayName": "Windows Search",
      "OriginalStartType": "Automatic",
      "OriginalStatus": "Running"
    },
    {
      "Name": "SysMain",
      "DisplayName": "SysMain",
      "OriginalStartType": "Automatic",
      "OriginalStatus": "Running"
    }
  ],
  "Registry": [
    {
      "KeyPath": "HKCU:\\System\\GameConfigStore",
      "ValueName": "GameDVR_Enabled",
      "OriginalType": "DWord",
      "OriginalData": 1,
      "Existed": true
    },
    {
      "KeyPath": "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection",
      "ValueName": "AllowTelemetry",
      "OriginalType": "DWord",
      "OriginalData": 3,
      "Existed": true
    }
  ],
  "SystemRestorePoint": {
    "Attempted": true,
    "Created": true,
    "SequenceNumber": 42,
    "Description": "LaptopOptimizer_PreRun_20260929_143000"
  }
}
```

### 5.4 Rollback Engine Logic (`Restore-LaptopDefaults`)

When the user runs `Optimize-Laptop.ps1 -Preset RestoreDefaults` or `-RestoreSnapshot <Path>`:
1. **Locate Snapshot**: Uses the specified path, or automatically selects the most recent `.json` file in `backups/`.
2. **Validate Integrity**: Parses JSON and validates required fields (`Services`, `Registry`, `PowerPlan`).
3. **Restore Services**:
   - For each service in the snapshot, sets `Set-Service -Name $s.Name -StartupType $s.OriginalStartType`.
   - If `$s.OriginalStatus -eq 'Running'`, starts the service with `Start-Service -Name $s.Name`.
   - If `$s.OriginalStatus -eq 'Stopped'`, ensures it is stopped.
4. **Restore Registry Keys**:
   - If `Existed -eq $true`, restores the original value and type via `Set-ItemProperty`.
   - If `Existed -eq $false`, removes the key/property via `Remove-ItemProperty`.
5. **Restore Power Plan**:
   - Calls `powercfg -setactive $snapshot.PowerPlan.ActiveSchemeGUID`.
6. **Verification & Audit**:
   - Queries current system state against snapshot values, logging any discrepancy.

---

## 6. Detailed Logging & Auditability Architecture

### 6.1 Multi-Target Structured Logging (`Logger.ps1`)

To provide auditability without cluttering the interactive console, the optimizer implements a dual-sink logging architecture:

```
[Optimizer Action] ---> Logger.ps1
                             |
                             +---> Console Sink (Formatted, colored, filtered by LogLevel)
                             |
                             +---> Disk Sink (ISO 8601 timestamps, log levels, full audit trail)
                             |
                             +---> (Optional) PowerShell Transcript (Raw stream capture)
```

#### Log Levels & Formatting:

| Log Level | Console Color | Description | Example Disk Format |
|---|---|---|---|
| `DEBUG` | Dark Gray | Granular internal execution details (skipped files, query timings) | `[2026-09-29 14:30:01.102] [DEBUG] [Storage] Skipping locked file: C:\Windows\Temp\fx.tmp` |
| `INFO` | Cyan / White | Standard milestone notifications and operational steps | `[2026-09-29 14:30:02.450] [INFO]  [Engine] Starting Preset: Quick Boost` |
| `ACTION` | Green | Actual modification executed (file deleted, service stopped) | `[2026-09-29 14:30:03.118] [ACTION] [Memory] Evacuated working set for process: chrome (PID 1420)` |
| `DRYRUN` | Magenta | Simulated action during dry-run | `[2026-09-29 14:30:03.500] [DRYRUN] [Storage] Would delete: C:\Windows\Temp\ac.tmp (14.2 MB)` |
| `WARN` | Yellow | Non-fatal issue (locked cache, restore point rate limit) | `[2026-09-29 14:30:04.012] [WARN]  [Safety] Checkpoint-Computer throttled (24h rule). Tier 1 active.` |
| `ERROR` | Red | Critical error or failed operation | `[2026-09-29 14:30:05.890] [ERROR] [Service] Failed to modify service 'WSearch': Access Denied` |

#### Disk File Lifecycle & Retention:
- **Default Path**: `laptop_optimizer/logs/optimizer_run_yyyyMMdd_HHmmss.log`.
- **Fallback Path**: If running from a read-only share, logs fall back to `$env:LOCALAPPDATA\LaptopOptimizer\logs\`.
- **Automatic Log Rotation**: On initialization, the logger inspects existing log files and removes files older than 30 days or trims the log folder to retain the most recent 50 logs.

### 6.2 Metric Reporting Engine

When `-Report` is specified or an optimization run completes, the engine compiles a structured comparison between pre-run baseline metrics and post-optimization measurements.

#### Report Schema:
1. **System Metadata**: Computer name, OS build, CPU model, total RAM, optimizer version.
2. **Storage Delta**: Initial free disk (GB), final free disk (GB), net reclaimed space (MB/GB), breakdown per cleaned directory.
3. **Memory Delta**: Initial free RAM (MB), final free RAM (MB), percentage change, top 5 memory-trimmed processes.
4. **Paging & Compression**: Active paging file usage before/after, memory compression working set delta.
5. **Services & Tasks**: Count of services tuned, list of disabled/paused items.
6. **Execution Timings**: Duration per module in milliseconds.

#### Sample Report File Outputs:
- Markdown report: `reports/optimization_report_yyyyMMdd_HHmmss.md`
- Machine-readable JSON: `reports/optimization_report_yyyyMMdd_HHmmss.json`

---

## 7. Antigravity Custom Skill Specification (Requirement R4)

### 7.1 Environment Inspection of Antigravity Skills

Inspection of existing plugins in the user environment (`C:\Users\ignaz\.gemini\config\plugins\` and `.agents/skills/`) revealed the exact Antigravity skill architecture:
1. **Root Directory**: Placed either in `<workspace>/.agents/skills/<skill-name>/` (local workspace skill) or `~/.gemini/config/skills/<skill-name>/` (global skill).
2. **YAML Frontmatter in `SKILL.md`**:
   - `name`: Lowercase, hyphen-separated, maximum 64 characters (e.g. `laptop-optimizer`).
   - `description`: Comprehensive overview of when and how to trigger the skill, maximum 1024 characters.
3. **Standard Subdirectories**:
   - `scripts/`: Contains executable CLI helper scripts (PowerShell and/or Python wrappers).
   - `references/`: Schema definitions, metric documentation, and safety rules.
   - `examples/`: Sample JSON reports and CLI invocation examples.
4. **Execution Protocol for Agents**:
   - Autonomous agents must run non-interactive commands.
   - Scripts must write machine-readable output to files (`-ReportPath <path>`) rather than dumping massive strings to stdout, preserving agent context windows.

### 7.2 Custom Skill Directory Layout: `laptop-optimizer`

```
laptop-optimizer/
├── SKILL.md                          # Main Antigravity skill instruction & schema
├── scripts/
│   ├── run_optimizer.ps1             # Headless wrapper for Antigravity agents
│   └── parse_metrics.py              # Optional lightweight JSON report summarizer
├── references/
│   ├── presets_guide.md              # Detailed behavioral matrix of presets
│   ├── safety_and_rollback.md        # Snapshot layout and rollback instructions
│   └── report_schema.json            # JSON schema for optimization reports
└── examples/
    ├── sample_diagnostic.json        # Reference baseline diagnostic report
    └── sample_optimization_report.json # Reference post-run optimization report
```

### 7.3 Complete Production Specification for `SKILL.md`

```markdown
---
name: laptop-optimizer
description: Diagnoses and optimizes Windows 11 laptop performance, specifically tuned for low-power quad-core systems (Intel N100, 8GB RAM, Windows 11 Home). Reclaims SSD storage, trims RAM working sets, flushes standby memory, optimizes background telemetry, and manages power plans with zero third-party dependencies and complete non-destructive rollback.
---

# Windows 11 Laptop Optimizer Skill

This skill provides autonomous diagnostic, tuning, and storage reclamation capabilities for Windows 11 laptops, with specialized tuning profiles for low-power Intel N100 (4-core, 8GB RAM) architectures.

## Triggering Scenarios

Use this skill when:
- The user reports system sluggishness, high RAM usage, memory compression lag, or low SSD storage.
- Preparing the laptop for gaming, compilation, or high-performance compute tasks.
- Profiling system resource consumers (CPU, RAM, Paging file, Background services).
- Safely reclaiming 1GB+ of Windows caches (Windows Update, Delivery Optimization, Crash Dumps, Temp files).
- Rolling back previous optimizations to safe Windows defaults.

## Available Presets & CLI Commands

All commands should be executed from the project root using `powershell.exe -NoProfile -ExecutionPolicy Bypass`:

### 1. System Diagnostics (Read-Only)
Captures baseline metrics without modifying system state:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Optimize-Laptop.ps1 -Preset DiagnosticOnly -Report -OutputFormat JSON -NonInteractive
```

### 2. Quick Boost (RAM & Immediate Temp Reclaim)
Trims working sets, frees standby RAM, and purges user temp files:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Optimize-Laptop.ps1 -Preset QuickBoost -Report -NonInteractive
```

### 3. Deep Clean (Comprehensive Storage Reclaim & SSD TRIM)
Safely purges Windows Update cache, Delivery Optimization, crash dumps, and runs SSD TRIM:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Optimize-Laptop.ps1 -Preset DeepClean -Report -NonInteractive
```

### 4. Gaming / Performance Mode
Activates High Performance power plan and silences high-overhead telemetry:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Optimize-Laptop.ps1 -Preset Gaming -Report -NonInteractive
```

### 5. Restore Defaults (Rollback)
Reverts services, registry keys, and power plan to the pre-optimization baseline:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Optimize-Laptop.ps1 -Preset RestoreDefaults -NonInteractive
```

### 6. Dry-Run Simulation Mode
Simulates any preset and reports prospective savings without making changes:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Optimize-Laptop.ps1 -Preset DeepClean -DryRun -Report -NonInteractive
```

## Agent Execution Rules & Safety Protocols

1. **Elevation Check**:
   - If not running with Administrator privileges, run `DiagnosticOnly` or prompt the user to launch `optimize.bat` via UAC.
2. **Always Use `-NonInteractive`**:
   - Prevents the script from hanging on interactive ASCII menu prompts.
3. **Always Inspect Output Reports**:
   - Read the generated JSON report at `reports/optimization_report_*.json` to extract precise before/after deltas for the user.
4. **Safety Guarantee**:
   - An atomic snapshot is automatically saved to `backups/` before any modification. In case of issues, immediately invoke `-Preset RestoreDefaults`.
```

---

## 8. Documentation Suite Structure

To satisfy Requirement **R4** and provide complete operational guidance for end-users, administrators, and developers, the documentation suite is structured into dedicated markdown files within the `laptop_optimizer/` project directory:

```
laptop_optimizer/
├── README.md                        # Master project documentation & quickstart
└── docs/
    ├── ARCHITECTURE.md              # Technical design, module decomposition & data flow
    ├── USER_GUIDE.md                # End-user handbook (interactive menu & CLI flags)
    ├── SAFETY_GUIDE.md              # Safety guarantees, whitelist, snapshot & rollback guide
    └── PRESETS.md                   # Granular matrix of all presets and affected components
```

### 8.1 Document Outlines & Content Specifications

#### 1. `README.md`
- **Hero & Overview**: Target system specifications (HP Laptop 15, Intel N100, 8GB RAM, Windows 11 Home 26200).
- **Key Features**: One-click batch launcher, zero dependencies, 4 presets, non-destructive rollback, SSD TRIM, working set trim.
- **Quickstart Guide**:
  - Double-click `optimize.bat` for interactive menu.
  - One-line command for quick boost: `.\optimize.bat -Preset QuickBoost`.
- **System Requirements & Prerequisites**: Windows 10/11 (x64), PowerShell 5.1+, Administrator rights for system tuning.
- **Repository Structure & File Index**.

#### 2. `docs/ARCHITECTURE.md`
- **System Architecture Diagram**: Showing relationship between `optimize.bat`, `Optimize-Laptop.ps1`, `src/` modules, `backups/`, `logs/`, and `reports/`.
- **PowerShell 5.1 / 7+ Cross-Compatibility Standards**: Why specific language features are restricted; Win32 P/Invoke design via `Add-Type`.
- **Subsystem Breakdown**:
  - Diagnostics Subsystem (CIM/WMI performance sampling).
  - Storage Engine (Safe cache purging, Dism component store, SSD TRIM).
  - Memory Engine (`EmptyWorkingSet`, standby memory release).
  - Service Tuning Subsystem (Registry and service state management).
  - Safety & Snapshot Engine (Atomic state serialization).
  - Multi-Channel Logger.
- **Data Flow & Lifecycle**: Baseline capture → Safety snapshot → Optimization execution → Post-run validation → Report generation.

#### 3. `docs/USER_GUIDE.md`
- **Interactive Terminal Menu Walkthrough**: Screenshots/ASCII diagrams of the menu, selecting options, interpreting the status header.
- **Command-Line Interface (CLI) Reference**: Full description of all parameters (`-Preset`, `-DryRun`, `-Backup`, `-SkipRestorePoint`, `-RestoreSnapshot`, `-Report`, `-OutputFormat`, `-LogLevel`).
- **Use Cases & Scenarios**:
  - Daily maintenance (Quick Boost).
  - Monthly cleanup (Deep Clean).
  - Preparing for gaming / high workload (Gaming Mode).
  - Automated scheduling via Windows Task Scheduler.

#### 4. `docs/SAFETY_GUIDE.md`
- **The Non-Destructive Guarantee**: Explanation of what the tool will *never* touch (user documents, downloads, desktop files, browser passwords/cookies, system drivers).
- **Directory Whitelist**: Exhaustive list of all directories subject to cleaning.
- **Three-Tier Safety Architecture**: Deep dive into Tier 1 (JSON snapshots), Tier 2 (System Restore Points), and Tier 3 (Dry-Run mode).
- **Step-by-Step Rollback Guide**:
  - Reverting via the interactive menu (Option 4).
  - Reverting via CLI: `.\optimize.bat -Preset RestoreDefaults`.
  - Reverting from a specific timestamped snapshot.
  - Windows System Restore manual fallback (`rstrui.exe`).

#### 5. `docs/PRESETS.md`
- **Detailed Preset Breakdown**: For each preset (`QuickBoost`, `DeepClean`, `Gaming`, `RestoreDefaults`), details the exact:
  - Memory actions executed.
  - File paths inspected and purged.
  - Windows services modified (original vs target StartType).
  - Scheduled tasks touched.
  - Registry keys modified.
  - Power scheme GUIDs activated.
  - Typical execution duration and expected resource savings.

---

## 9. Comprehensive Implementation Recommendations for Track B

Based on this architectural investigation, the following concrete recommendations are provided for implementation in Milestone M3 and Milestone M4:

1. **Adopt Modular Script Layout in `src/`**:
   - Keep `Optimize-Laptop.ps1` clean and focused on parameter routing, lifecycle management, and UI rendering.
   - Separate concerns into `Common.ps1`, `Logger.ps1`, `SafetyEngine.ps1`, `Diagnostics.ps1`, `StorageOptimizer.ps1`, `MemoryOptimizer.ps1`, `ServiceOptimizer.ps1`, and `MenuUI.ps1`.
   - Use `$script:ModuleRoot = $PSScriptRoot` and dot-source each module safely.
2. **Enforce PowerShell 5.1 Parser Compatibility**:
   - Strictly prohibit PowerShell 7-only syntax (`$a ? $b : $c`, `$a ?? $b`, `cmd1 && cmd2`, `ConvertFrom-Json -AsHashtable`).
   - Use `[PSCustomObject]@{...}` and `ConvertTo-Json -Depth 5`.
3. **Prioritize JSON Snapshot Engine as Primary Rollback**:
   - Do not rely solely on `Checkpoint-Computer`, because Windows 11 Home systems frequently disable System Protection or enforce a 24-hour rate limit.
   - Ensure the JSON snapshot is written to disk *before* any service or registry modification begins.
4. **Implement Robust P/Invoke Memory Trimming**:
   - Embed `psapi.dll::EmptyWorkingSet` via `Add-Type -TypeDefinition` inside `Common.ps1`.
   - Wrap process iterations in `try/catch` to gracefully ignore protected system processes (e.g. `csrss.exe`, `lsass.exe`) while trimming all accessible user and background processes.
5. **Ensure Idempotency and Non-Interactive Stability**:
   - Guarantee that running the optimizer multiple times produces consistent, non-destructive results.
   - Verify that all scripts run cleanly when invoked headlessly with `-NonInteractive` without prompting for input.

---
*Report compiled and verified by `explorer_survey_3`.*
