# Dispatch: Worker M1 (Diagnostics & Performance Profiling)

## Objective
Implement Milestone M1:
- `src/Common/Platform.ps1`
- `src/Common/Types.ps1`
- `src/Diagnostics/Profiler.ps1`
- `src/Diagnostics/Comparison.ps1`

## Ownership
- `c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/src/Common/**`
- `c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/src/Diagnostics/**`

## 2026-09-29T12:05:07Z
Task:
Read ORIGINAL_REQUEST.md, PROJECT.md, and explorer_survey_1's survey_report.md.
Implement Milestone M1 (Diagnostics & Performance Profiling):
1. Create directory structure under `c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/src/` if not present.
2. `src/Common/Platform.ps1`:
   - OS name, build, architecture, CPU name, core/logical processor count, total physical RAM.
   - Elevation status check (`[Security.Principal.WindowsPrincipal]...IsInRole(...)`).
   - PowerShell 5.1/7+ compatibility helpers.
3. `src/Common/Types.ps1`:
   - C# P/Invoke definitions for Win32 memory and process functions (`psapi.dll!EmptyWorkingSet`, `user32.dll!GetForegroundWindow`, `user32.dll!GetWindowThreadProcessId`).
4. `src/Diagnostics/Profiler.ps1`:
   - `Get-LaptopSystemSnapshot [-Detailed]`:
     - Free physical RAM (MB and %), Total RAM.
     - Memory Compression WorkingSet and PerfOS_Memory counters (handling un-elevated execution gracefully).
     - Paging file allocated size and current usage (`Win32_PageFileUsage`).
     - Disk C: total size, free space (GB), free space percentage.
     - Active power scheme name and GUID (`powercfg /getactivescheme`).
     - Startup items count and details (`StartupApproved`, `Run` keys).
     - Scheduled tasks count (total and active).
     - Process count and Top resource-consuming processes by WorkingSet and CPU.
5. `src/Diagnostics/Comparison.ps1`:
   - `Compare-LaptopSnapshots -Baseline $b -Current $c`:
     - Calculates RAM gained (MB), Storage reclaimed (GB), Process delta, Memory compression delta.
     - Evaluates Acceptance Criteria: Free RAM > 1500MB, Reclaimed Storage >= 1GB.
     - Generates structured console table, JSON report, and Markdown comparison string.
6. Verify your code by running PowerShell unit tests against your modules and confirm 100% genuine implementation.
7. Deliver your report to `c:/Users/ignaz/antigravity/keen-franklin/.agents/teamwork/worker_m1/handoff.md` and notify parent via send_message.

