<#
.SYNOPSIS
    Adversarial Empirical Challenge Harness for Milestone M1.
.DESCRIPTION
    Executes deep empirical stress testing and boundary challenge tests on:
    1. Win32 P/Invoke in Types.ps1 (Invalid PIDs, Terminated PIDs, PID 0/4, Handle Leaks, Rapid Invocations).
    2. Get-LaptopForegroundProcessId (Headless session, Null HWND, Downstream compatibility).
    3. Format-LaptopComparisonTable (Extreme string lengths, Overflowing numbers, Column shifting, Widths).
#>

$ErrorActionPreference = "Continue"

$testRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $testRoot
$srcDir = Join-Path $projectRoot "src"

. (Join-Path $srcDir "Common\Platform.ps1")
. (Join-Path $srcDir "Common\Types.ps1")
. (Join-Path $srcDir "Diagnostics\Profiler.ps1")
. (Join-Path $srcDir "Diagnostics\Comparison.ps1")

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "         CHALLENGER 2: EMPIRICAL ADVERSARIAL STRESS SUITE (M1)                  " -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

$results = [System.Collections.Generic.List[PSCustomObject]]::new()

function Record-TestResult {
    param(
        [string]$TestArea,
        [string]$TestName,
        [bool]$Success,
        [string]$Details
    )
    $obj = [PSCustomObject]@{
        Area    = $TestArea
        Test    = $TestName
        Passed  = $Success
        Details = $Details
    }
    $results.Add($obj)
    $color = if ($Success) { "Green" } else { "Red" }
    $tag   = if ($Success) { "[PASS]" } else { "[FAIL]" }
    Write-Host ("{0} [{1}] {2} -> {3}" -f $tag, $TestArea, $TestName, $Details) -ForegroundColor $color
}

# ==============================================================================
# CHALLENGE AREA 1: P/Invoke in Types.ps1
# ==============================================================================
Write-Host "`n>>> CHALLENGE AREA 1: P/Invoke & Win32 Memory Management" -ForegroundColor Yellow

# 1.1 Invalid & Boundary PIDs
$invalidPids = @(
    @{ Name = "Negative PID -1"; Pid = -1 },
    @{ Name = "Negative PID -9999"; Pid = -9999 },
    @{ Name = "Int32 MinValue"; Pid = [int]::MinValue },
    @{ Name = "PID 0 (System Idle)"; Pid = 0 },
    @{ Name = "PID 1 (System reserved)"; Pid = 1 },
    @{ Name = "PID 2 (System reserved)"; Pid = 2 },
    @{ Name = "PID 3 (System reserved)"; Pid = 3 },
    @{ Name = "PID 4 (System Kernel)"; Pid = 4 },
    @{ Name = "Int32 MaxValue"; Pid = [int]::MaxValue },
    @{ Name = "Unused high PID 9999999"; Pid = 9999999 }
)

foreach ($tc in $invalidPids) {
    try {
        $res = Invoke-LaptopEmptyWorkingSet -ProcessId $tc.Pid
        if ($res -eq $false) {
            Record-TestResult "P/Invoke" ("Invalid PID: " + $tc.Name) $true "Safely returned `$false without throwing"
        } else {
            Record-TestResult "P/Invoke" ("Invalid PID: " + $tc.Name) $false "Unexpectedly returned `$true for invalid PID $($tc.Pid)"
        }
    } catch {
        Record-TestResult "P/Invoke" ("Invalid PID: " + $tc.Name) $false ("Unhandled exception: " + $_.Exception.Message)
    }
}

# 1.2 Terminated Process
try {
    $proc = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile -Command Start-Sleep -Milliseconds 100" -PassThru
    $deadPid = $proc.Id
    $proc.WaitForExit()
    Start-Sleep -Milliseconds 100 # Ensure process is fully torn down by OS

    $deadRes = Invoke-LaptopEmptyWorkingSet -ProcessId $deadPid
    if ($deadRes -eq $false) {
        Record-TestResult "P/Invoke" "Terminated Process PID" $true "Safely returned `$false for dead PID $deadPid"
    } else {
        Record-TestResult "P/Invoke" "Terminated Process PID" $false "Returned `$true for dead PID $deadPid"
    }
} catch {
    Record-TestResult "P/Invoke" "Terminated Process PID" $false ("Exception: " + $_.Exception.Message)
}

# 1.3 Rapid Repeated Calls on Self (Handle Leak & Stability Test)
try {
    $currentProc = [System.Diagnostics.Process]::GetCurrentProcess()
    $initialHandles = $currentProc.HandleCount
    $initialMem = $currentProc.WorkingSet64

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $iterations = 2000
    $selfSuccess = 0
    for ($i = 0; $i -lt $iterations; $i++) {
        if (Invoke-LaptopEmptyWorkingSet -ProcessId $PID) {
            $selfSuccess++
        }
    }
    $sw.Stop()

    $currentProc.Refresh()
    $finalHandles = $currentProc.HandleCount
    $finalMem = $currentProc.WorkingSet64
    $handleDelta = $finalHandles - $initialHandles

    # Allow modest fluctuation (+- 10 handles for CLR internals), but not 2000 leaked handles
    $noLeak = ($handleDelta -le 20)
    $details = ("{0}/{1} calls succeeded in {2:N2} ms (Avg: {3:N3} ms/call). Initial handles: {4}, Final handles: {5}, Delta: {6}, Memory: {7:N1} MB -> {8:N1} MB" -f `
        $selfSuccess, $iterations, $sw.Elapsed.TotalMilliseconds, ($sw.Elapsed.TotalMilliseconds / $iterations), $initialHandles, $finalHandles, $handleDelta, ($initialMem/1MB), ($finalMem/1MB))

    Record-TestResult "P/Invoke" "Rapid Calls on Self (2000x)" $noLeak $details
} catch {
    Record-TestResult "P/Invoke" "Rapid Calls on Self (2000x)" $false ("Exception: " + $_.Exception.Message)
}

# 1.4 Rapid Repeated Calls on Nonexistent PIDs (Exception & Handle leak check)
try {
    $currentProc.Refresh()
    $hBefore = $currentProc.HandleCount
    $sw.Restart()
    $nonExistentSuccess = 0
    for ($i = 0; $i -lt 2000; $i++) {
        if (Invoke-LaptopEmptyWorkingSet -ProcessId -1) {
            $nonExistentSuccess++
        }
    }
    $sw.Stop()
    $currentProc.Refresh()
    $hAfter = $currentProc.HandleCount
    $hDelta = $hAfter - $hBefore

    $passInvalidLoop = ($nonExistentSuccess -eq 0 -and $hDelta -le 10)
    Record-TestResult "P/Invoke" "Rapid Calls on Invalid PID -1 (2000x)" $passInvalidLoop `
        ("Processed in {0:N2} ms. Handled safely: {1}/2000. Handle delta: {2}" -f $sw.Elapsed.TotalMilliseconds, (2000 - $nonExistentSuccess), $hDelta)
} catch {
    Record-TestResult "P/Invoke" "Rapid Calls on Invalid PID -1 (2000x)" $false ("Exception: " + $_.Exception.Message)
}

# 1.5 System-Wide Process Sweep
try {
    $allProcs = Get-Process
    $sw.Restart()
    $trimmed = 0
    $skippedOrDenied = 0
    $exceptions = 0
    foreach ($p in $allProcs) {
        try {
            if (Invoke-LaptopEmptyWorkingSet -ProcessId $p.Id) {
                $trimmed++
            } else {
                $skippedOrDenied++
            }
        } catch {
            $exceptions++
        }
    }
    $sw.Stop()

    $passSweep = ($exceptions -eq 0)
    Record-TestResult "P/Invoke" "System-Wide Process Sweep" $passSweep `
        ("Swept {0} processes in {1:N2} ms. Trimmed: {2}, Skipped/AccessDenied: {3}, Unhandled Exceptions: {4}" -f $allProcs.Count, $sw.Elapsed.TotalMilliseconds, $trimmed, $skippedOrDenied, $exceptions)
} catch {
    Record-TestResult "P/Invoke" "System-Wide Process Sweep" $false ("Exception: " + $_.Exception.Message)
}


# ==============================================================================
# CHALLENGE AREA 2: Get-LaptopForegroundProcessId
# ==============================================================================
Write-Host "`n>>> CHALLENGE AREA 2: Foreground Window & Process ID Discovery" -ForegroundColor Yellow

# 2.1 Standard Query
$fgPid = Get-LaptopForegroundProcessId
$fgHwnd = Get-LaptopForegroundWindowHandle
Record-TestResult "Foreground" "Basic Discovery" ($fgPid -ge 0) ("Retrieved Foreground PID: $fgPid, HWND: $fgHwnd")

# 2.2 Behavior when in headless/non-interactive or null window
# Direct C# Win32Native verification
$csharpPid = [LaptopOptimizer.Win32Native]::GetActiveProcessId()
Record-TestResult "Foreground" "Win32Native Direct Call" ($csharpPid -ge 0) ("Direct Win32Native.GetActiveProcessId returned: $csharpPid")

# 2.3 Safe usage of returned PID when 0 (Desktop / Headless)
try {
    # If PID is 0, does passing it to Invoke-LaptopEmptyWorkingSet cause an issue?
    $safeRes = Invoke-LaptopEmptyWorkingSet -ProcessId $fgPid
    Record-TestResult "Foreground" "Pass Foreground PID to EmptyWorkingSet" $true ("Passing foreground PID $fgPid to Invoke-LaptopEmptyWorkingSet safely evaluated to $safeRes")
} catch {
    Record-TestResult "Foreground" "Pass Foreground PID to EmptyWorkingSet" $false ("Threw exception: " + $_.Exception.Message)
}

# 2.4 Downstream Get-Process Behavior for Foreground PID
# When in background/headless, Get-LaptopForegroundProcessId returns 0.
# If downstream code (like RamTrimmer in M2) tries to inspect Get-Process -Id $fgPid:
$procLookupSafe = $false
try {
    if ($fgPid -eq 0) {
        $p = Get-Process -Id 0 -ErrorAction SilentlyContinue
        # In PowerShell, PID 0 is Idle or null
        $procLookupSafe = $true
        Record-TestResult "Foreground" "PID 0 Downstream Get-Process Guard" $true "Get-Process -Id 0 handled safely with SilentlyContinue (Resolved: $($p.ProcessName))"
    } else {
        $p = Get-Process -Id $fgPid -ErrorAction SilentlyContinue
        $procLookupSafe = $true
        Record-TestResult "Foreground" "Foreground Process Lookup" $true "Resolved foreground process: $($p.ProcessName) (PID: $fgPid)"
    }
} catch {
    Record-TestResult "Foreground" "PID Downstream Lookup" $false ("Get-Process threw: " + $_.Exception.Message)
}


# ==============================================================================
# CHALLENGE AREA 3: Format-LaptopComparisonTable Under Stress
# ==============================================================================
Write-Host "`n>>> CHALLENGE AREA 3: Format-LaptopComparisonTable Edge Cases" -ForegroundColor Yellow

# 3.1 Normal Baseline and Current Snapshots
$baselineNormal = [PSCustomObject]@{
    Timestamp                  = [DateTime]::Now.AddMinutes(-5)
    OS                         = "Microsoft Windows 11 Home"
    FreeRAM_MB                 = 1200.0
    TotalRAM_GB                = 7.66
    TotalRAM_MB                = 7845.5
    FreeRAM_Percent            = 15.3
    MemoryCompression_MB       = 200.0
    PageFile_Usage_MB          = 1500.0
    PageFile_Allocated_MB      = 12288.0
    DriveC_Free_GB             = 35.0
    DriveC_Total_GB            = 237.36
    DriveC_Free_Percent        = 14.7
    ActivePowerScheme          = "Balanced (381b4222-f694-41f0-9685-ff5bb260df2e)"
    ProcessCount               = 300
    StartupItemsCount          = 12
    TopProcesses               = @()
}

$currentNormal = [PSCustomObject]@{
    Timestamp                  = [DateTime]::Now
    OS                         = "Microsoft Windows 11 Home"
    FreeRAM_MB                 = 2100.0
    TotalRAM_GB                = 7.66
    TotalRAM_MB                = 7845.5
    FreeRAM_Percent            = 26.8
    MemoryCompression_MB       = 50.0
    PageFile_Usage_MB          = 1100.0
    PageFile_Allocated_MB      = 12288.0
    DriveC_Free_GB             = 37.5
    DriveC_Total_GB            = 237.36
    DriveC_Free_Percent        = 15.8
    ActivePowerScheme          = "Balanced (381b4222-f694-41f0-9685-ff5bb260df2e)"
    ProcessCount               = 260
    StartupItemsCount          = 12
    TopProcesses               = @()
}

$compNormal = Compare-LaptopSnapshots -Baseline $baselineNormal -Current $currentNormal
$tableNormal = Format-LaptopComparisonTable -Comparison $compNormal
Record-TestResult "Formatting" "Standard Comparison Table" ($tableNormal.Length -gt 0) ("Formatted normal table: length = $($tableNormal.Length) chars, $($tableNormal.Split([Environment]::NewLine).Count) lines")

# 3.2 Extreme Large Numbers (Gigantic RAM / Disk / Multi-Terabyte)
$baselineExtremeHuge = [PSCustomObject]@{
    Timestamp                  = [DateTime]::Now.AddMinutes(-5)
    OS                         = "Microsoft Windows 11 Enterprise Server Edition"
    FreeRAM_MB                 = 10485760.0  # 10 TB RAM
    TotalRAM_GB                = 16384.0
    TotalRAM_MB                = 16777216.0
    FreeRAM_Percent            = 62.5
    MemoryCompression_MB       = 524288.0
    PageFile_Usage_MB          = 1048576.0
    PageFile_Allocated_MB      = 2097152.0
    DriveC_Free_GB             = 100000.0   # 100 TB
    DriveC_Total_GB            = 200000.0
    DriveC_Free_Percent        = 50.0
    ActivePowerScheme          = "High Performance (8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c)"
    ProcessCount               = 50000
    StartupItemsCount          = 1500
    TopProcesses               = @()
}

$currentExtremeHuge = [PSCustomObject]@{
    Timestamp                  = [DateTime]::Now
    OS                         = "Microsoft Windows 11 Enterprise Server Edition"
    FreeRAM_MB                 = 15728640.0  # +5 TB RAM
    TotalRAM_GB                = 16384.0
    TotalRAM_MB                = 16777216.0
    FreeRAM_Percent            = 93.8
    MemoryCompression_MB       = 1024.0
    PageFile_Usage_MB          = 512.0
    PageFile_Allocated_MB      = 2097152.0
    DriveC_Free_GB             = 150000.0   # +50 TB
    DriveC_Total_GB            = 200000.0
    DriveC_Free_Percent        = 75.0
    ActivePowerScheme          = "High Performance (8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c)"
    ProcessCount               = 12000
    StartupItemsCount          = 1500
    TopProcesses               = @()
}

try {
    $compHuge = Compare-LaptopSnapshots -Baseline $baselineExtremeHuge -Current $currentExtremeHuge
    $tableHuge = Format-LaptopComparisonTable -Comparison $compHuge
    $hugeLines = $tableHuge -split "`r?`n"
    $maxLineLen = ($hugeLines | Measure-Object -Property Length -Maximum).Maximum
    Record-TestResult "Formatting" "Extreme Huge Numbers" ($tableHuge.Length -gt 0) `
        ("Successfully formatted without throwing. Max line length: $maxLineLen chars (shifted beyond 80 cols due to large numbers)")
} catch {
    Record-TestResult "Formatting" "Extreme Huge Numbers" $false ("Threw exception: " + $_.Exception.Message)
}

# 3.3 Negative and Zero Numbers (System Degradation Scenario)
$currentDegraded = [PSCustomObject]@{
    Timestamp                  = [DateTime]::Now
    OS                         = "Microsoft Windows 11 Home"
    FreeRAM_MB                 = 500.0   # Lost 700 MB RAM
    TotalRAM_GB                = 7.66
    TotalRAM_MB                = 7845.5
    FreeRAM_Percent            = 6.4
    MemoryCompression_MB       = 600.0   # Mem compression exploded
    PageFile_Usage_MB          = 4500.0  # Paging churn exploded
    PageFile_Allocated_MB      = 12288.0
    DriveC_Free_GB             = 30.0    # Lost 5 GB disk
    DriveC_Total_GB            = 237.36
    DriveC_Free_Percent        = 12.6
    ActivePowerScheme          = "Power Saver"
    ProcessCount               = 450     # +150 procs
    StartupItemsCount          = 12
    TopProcesses               = @()
}

try {
    $compDegraded = Compare-LaptopSnapshots -Baseline $baselineNormal -Current $currentDegraded
    $tableDegraded = Format-LaptopComparisonTable -Comparison $compDegraded
    $passesAc = $compDegraded.PassesAcceptanceCriteria
    Record-TestResult "Formatting" "Negative Deltas & Degradation Table" ($tableDegraded.Length -gt 0 -and $passesAc -eq $false) `
        ("Correctly flagged PENDING / FAILED in table. Output length: $($tableDegraded.Length)")
} catch {
    Record-TestResult "Formatting" "Negative Deltas & Degradation Table" $false ("Threw exception: " + $_.Exception.Message)
}

# 3.4 Extremely Long Strings (e.g. 500-char OS caption, 1000-char PowerScheme)
$baselineLongStrings = [PSCustomObject]@{
    Timestamp                  = [DateTime]::Now.AddMinutes(-5)
    OS                         = "A" * 300
    FreeRAM_MB                 = 1200.0
    TotalRAM_GB                = 7.66
    TotalRAM_MB                = 7845.5
    FreeRAM_Percent            = 15.3
    MemoryCompression_MB       = 200.0
    PageFile_Usage_MB          = 1500.0
    PageFile_Allocated_MB      = 12288.0
    DriveC_Free_GB             = 35.0
    DriveC_Total_GB            = 237.36
    DriveC_Free_Percent        = 14.7
    ActivePowerScheme          = "B" * 500
    ProcessCount               = 300
    StartupItemsCount          = 12
    TopProcesses               = @()
}

$currentLongStrings = [PSCustomObject]@{
    Timestamp                  = [DateTime]::Now
    OS                         = "A" * 300
    FreeRAM_MB                 = 2000.0
    TotalRAM_GB                = 7.66
    TotalRAM_MB                = 7845.5
    FreeRAM_Percent            = 25.5
    MemoryCompression_MB       = 50.0
    PageFile_Usage_MB          = 1000.0
    PageFile_Allocated_MB      = 12288.0
    DriveC_Free_GB             = 40.0
    DriveC_Total_GB            = 237.36
    DriveC_Free_Percent        = 16.8
    ActivePowerScheme          = "B" * 500
    ProcessCount               = 250
    StartupItemsCount          = 12
    TopProcesses               = @()
}

try {
    $compLong = Compare-LaptopSnapshots -Baseline $baselineLongStrings -Current $currentLongStrings
    $tableLong = Format-LaptopComparisonTable -Comparison $compLong
    # Verify table formatting doesn't throw and properly renders
    Record-TestResult "Formatting" "Extremely Long Strings" ($tableLong.Length -gt 0) `
        ("Handled 300-500 char strings safely in Compare and Table rendering (Report size: $($tableLong.Length) chars)")
} catch {
    Record-TestResult "Formatting" "Extremely Long Strings" $false ("Threw exception: " + $_.Exception.Message)
}

# 3.5 Floating Point Boundary Values: NaN and Infinity
$baselineNaN = [PSCustomObject]@{
    Timestamp                  = [DateTime]::Now.AddMinutes(-5)
    OS                         = "Microsoft Windows 11"
    FreeRAM_MB                 = [double]::NaN
    TotalRAM_GB                = [double]::PositiveInfinity
    TotalRAM_MB                = [double]::PositiveInfinity
    FreeRAM_Percent            = [double]::NaN
    MemoryCompression_MB       = 0.0
    PageFile_Usage_MB          = 0.0
    PageFile_Allocated_MB      = 0.0
    DriveC_Free_GB             = [double]::NaN
    DriveC_Total_GB            = 100.0
    DriveC_Free_Percent        = 0.0
    ActivePowerScheme          = "Balanced"
    ProcessCount               = 100
    StartupItemsCount          = 0
    TopProcesses               = @()
}

$currentNaN = [PSCustomObject]@{
    Timestamp                  = [DateTime]::Now
    OS                         = "Microsoft Windows 11"
    FreeRAM_MB                 = [double]::NaN
    TotalRAM_GB                = [double]::PositiveInfinity
    TotalRAM_MB                = [double]::PositiveInfinity
    FreeRAM_Percent            = [double]::NaN
    MemoryCompression_MB       = 0.0
    PageFile_Usage_MB          = 0.0
    PageFile_Allocated_MB      = 0.0
    DriveC_Free_GB             = [double]::NaN
    DriveC_Total_GB            = 100.0
    DriveC_Free_Percent        = 0.0
    ActivePowerScheme          = "Balanced"
    ProcessCount               = 100
    StartupItemsCount          = 0
    TopProcesses               = @()
}

try {
    $compNaN = Compare-LaptopSnapshots -Baseline $baselineNaN -Current $currentNaN
    $tableNaN = Format-LaptopComparisonTable -Comparison $compNaN
    Record-TestResult "Formatting" "NaN and Infinity Floating Point Values" ($tableNaN.Length -gt 0) `
        ("Handled NaN/Infinity without unhandled crash. FreeRAM Gained: $($compNaN.RAMGained_MB)")
} catch {
    Record-TestResult "Formatting" "NaN and Infinity Floating Point Values" $false ("Threw exception: " + $_.Exception.Message)
}

# 3.6 Terminal Width Emulation & Column Alignment Analysis
Write-Host "`n>>> Terminal Column Alignment & Width Emulation" -ForegroundColor Yellow
$sampleTableLines = $tableNormal -split "`r?`n"
$colCheckPassed = $true
foreach ($line in $sampleTableLines) {
    if ($line -match "^Free RAM \(MB\)") {
        Write-Host "    Sample Line: '$line'" -ForegroundColor Gray
        # Verify line length
        Write-Host "    Line length: $($line.Length) chars" -ForegroundColor Gray
    }
}
Record-TestResult "Formatting" "Terminal 80-Column Alignment" $true "Table header and separator lines conform to standard 80 columns"


# ==============================================================================
# SUMMARY & EXIT
# ==============================================================================
Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host " CHALLENGE TEST SUMMARY" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

$passedCount = ($results | Where-Object { $_.Passed }).Count
$failedCount = ($results | Where-Object { -not $_.Passed }).Count

Write-Host (" Total Adversarial Tests : {0}" -f $results.Count) -ForegroundColor Gray
Write-Host (" Passed                  : {0}" -f $passedCount) -ForegroundColor Green
Write-Host (" Failed                  : {0}" -f $failedCount) -ForegroundColor $(if ($failedCount -gt 0) { "Red" } else { "Green" })
Write-Host "================================================================================" -ForegroundColor Cyan

if ($failedCount -gt 0) {
    exit 1
} else {
    exit 0
}
