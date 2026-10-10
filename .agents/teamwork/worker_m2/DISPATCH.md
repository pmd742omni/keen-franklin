# Dispatch: Worker M2 (Storage & Memory Reclamation Engine)

## Objective
Implement Milestone M2 based on `PROJECT.md` and `explorer_survey_2/survey_report.md`:
1. `src/StorageOptimizer/DiskCleanup.ps1`:
   - `Invoke-SafeDiskCleanup [-DryRun] [-IncludeDeliveryOptimization] [-IncludeBrowserCache]`
   - Purges stale temporary caches without touching user documents, downloads, or credentials.
   - Reclaims >1 GB safe cache (Temp, Explorer thumbnails, Browser caches, CrashDumps).
   - Robust per-item try/catch skipping locked files.
2. `src/StorageOptimizer/SsdTrim.ps1`:
   - `Invoke-SsdTrim [-DriveLetter "C"] [-DryRun]`
   - NVMe SSD TRIM execution via `Optimize-Volume -DriveLetter C -ReTrim` and fallback `defrag.exe C: /L /U /V`.
   - Privilege check (checks elevation before calling).
3. `src/MemoryOptimizer/RamTrimmer.ps1`:
   - `Invoke-RamWorkingSetTrim [-ExcludePids <int[]>] [-DryRun]`
   - Native Win32 `EmptyWorkingSet` trimming via `Types.ps1`.
   - Foreground process protection via `Get-LaptopForegroundProcessId`.
   - Paging churn guard (standby list soft faults, event-driven).
   - Stabilizes free physical RAM > 1.5 GB.
4. `src/ServiceOptimizer/ServiceTuning.ps1`:
   - Safe tuning for DiagTrack, SysMain, and 8 HP OEM background bloatware services.
   - Non-destructive toggle (supports saving original status for rollback).
5. `src/ServiceOptimizer/StartupTuning.ps1`:
   - Reversible startup optimization toggling `StartupApproved` byte 0 (0x02 to 0x03) with .reg backup.
6. Author and execute unit test suite `tests/test_m2_storage_memory.ps1` (verifying dry-run, live execution, error handling, contract compliance).
7. Report handoff to `c:/Users/ignaz/antigravity/keen-franklin/.agents/teamwork/worker_m2/handoff.md`.
