<#
.SYNOPSIS
    Adversarial Stress & Boundary Test Suite for Milestone M1 (Diagnostics & Profiling).
.DESCRIPTION
    Specifically tests:
    - Rapid loop polling of Get-LaptopSystemSnapshot for memory leaks, resource exhaustion, and CIM timeouts.
    - Compare-LaptopSnapshots with null, sparse, mismatched, and extreme boundary values (0 RAM, negative deltas, overflow, NaN, Infinity).
    - Win32 native P/Invoke handle leaks and duplicate type compilation.
    - Exception resilience: verifies that errors are caught or cleanly surfaced.
.NOTES
    Challenger 1 for Milestone M1.
#>

$ErrorActionPreference = "Continue"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$projectRoot = Resolve-Path (Join-Path $scriptDir "..")
$srcDir = Join-Path $projectRoot "src"

# Source M1 modules
. (Join-Path $srcDir "Common\Platform.ps1")
. (Join-Path $srcDir "Common\Types.ps1")
. (Join-Path $srcDir "Diagnostics\Profiler.ps1")
. (Join-Path $srcDir "Diagnostics\Comparison.ps1")

$passCount = 0
$failCount = 0
$findings = [System.Collections.Generic.List[string]]::new()

function Record-Test([string]$name, [bool]$passed, [string]$detail = "") {
    if ($passed) {
        Write-Host "  [PASS] $name" -ForegroundColor Green
        if ($detail) { Write-Host "         $detail" -ForegroundColor DarkGray }
        $script:passCount++
    } else {
        Write-Host "  [FAIL] $name" -ForegroundColor Red
        if ($detail) { Write-Host "         ERROR: $detail" -ForegroundColor Yellow }
        $script:failCount++
        $script:findings.Add("FAIL: $name - $detail")
    }
}

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "       MILESTONE M1 EMPIRICAL ADVERSARIAL STRESS & CHALLENGE SUITE              " -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Target: $projectRoot" -ForegroundColor Gray
Write-Host "Time  : $([DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
Write-Host "================================================================================" -ForegroundColor Cyan

# =============================================================================
# SUITE 1: Native Win32 & Platform Stress
# =============================================================================
Write-Host "`n>> SUITE 1: Native Win32 & Platform Stress" -ForegroundColor Yellow

# Test 1.1: Re-sourcing Types.ps1 multiple times (idempotency & type collision guard)
$reimportPassed = $true
$reimportErr = ""
try {
    for ($i = 1; $i -le 10; $i++) {
        . (Join-Path $srcDir "Common\Types.ps1")
    }
} catch {
    $reimportPassed = $false
    $reimportErr = $_.Exception.Message
}
Record-Test "Types.ps1 idempotent re-sourcing 10x without duplicate type exception" $reimportPassed $reimportErr

# Test 1.2: Stress Invoke-LaptopEmptyWorkingSet for handle leaks and invalid PIDs
$initialHandles = (Get-Process -Id $PID).HandleCount
$trimResults = @()
$trimExceptions = 0

# Test boundary PIDs: negative, 0, 4 (system), large PIDs
$boundaryPids = @(-9999, -1, 0, 4, 1, 999999, [int]::MaxValue)
foreach ($badPid in $boundaryPids) {
    try {
        $res = Invoke-LaptopEmptyWorkingSet -ProcessId $badPid
        if ($badPid -le 4 -and $res -ne $false) {
            $trimExceptions++
        }
    } catch {
        $trimExceptions++
    }
}
Record-Test "Invoke-LaptopEmptyWorkingSet safely handles boundary PIDs (-9999 to MaxValue)" ($trimExceptions -eq 0) "Boundary PIDs handled without throwing"

# Test 1.3: Rapid 50x calls on current process to detect handle leaks
$handleBefore = (Get-Process -Id $PID).HandleCount
for ($i = 1; $i -le 50; $i++) {
    [void](Invoke-LaptopEmptyWorkingSet -ProcessId $PID)
}
$handleAfter = (Get-Process -Id $PID).HandleCount
$handleDelta = $handleAfter - $handleBefore
# Allow small variation (< 15 handles) from PowerShell host activities
$noHandleLeak = ($handleDelta -le 15)
Record-Test "Invoke-LaptopEmptyWorkingSet does not leak handles across 50 calls" $noHandleLeak "Handle delta: $handleDelta (Before: $handleBefore, After: $handleAfter)"

# Test 1.4: Rapid 500x calls of Get-LaptopForegroundProcessId
$fgSw = [System.Diagnostics.Stopwatch]::StartNew()
$fgSuccess = $true
$fgErr = ""
try {
    for ($i = 1; $i -le 500; $i++) {
        $fg = Get-LaptopForegroundProcessId
        if ($fg -lt 0) { $fgSuccess = $false; break }
    }
} catch {
    $fgSuccess = $false
    $fgErr = $_.Exception.Message
}
$fgSw.Stop()
Record-Test "Get-LaptopForegroundProcessId survives 500 rapid calls ($($fgSw.ElapsedMilliseconds) ms)" $fgSuccess $fgErr


# =============================================================================
# SUITE 2: Compare-LaptopSnapshots Boundary, Extreme & Mismatched Inputs
# =============================================================================
Write-Host "`n>> SUITE 2: Compare-LaptopSnapshots Boundary & Extreme Inputs" -ForegroundColor Yellow

# Helper to create a base mock
function New-MockSnapshot {
    param(
        [double]$FreeRAM_MB = 1000.0,
        [double]$TotalRAM_GB = 8.0,
        [double]$FreeRAM_Percent = 12.5,
        [double]$MemComp_MB = 100.0,
        [double]$PageFile_MB = 1000.0,
        [double]$DriveC_Free_GB = 30.0,
        [double]$DriveC_Total_GB = 200.0,
        [int]$ProcessCount = 150,
        [int]$StartupItems = 10
    )
    return [PSCustomObject]@{
        Timestamp             = [DateTime]::Now
        OS                    = "Windows 11 Home"
        FreeRAM_MB            = $FreeRAM_MB
        TotalRAM_GB           = $TotalRAM_GB
        FreeRAM_Percent       = $FreeRAM_Percent
        MemoryCompression_MB  = $MemComp_MB
        PageFile_Usage_MB     = $PageFile_MB
        PageFile_Allocated_MB = 8192.0
        DriveC_Free_GB        = $DriveC_Free_GB
        DriveC_Total_GB       = $DriveC_Total_GB
        ActivePowerScheme     = "Balanced (381b4222-f694-41f0-9685-ff5bb260df2e)"
        ProcessCount          = $ProcessCount
        StartupItemsCount     = $StartupItems
        TopProcesses          = @()
    }
}

# Test 2.1: Null Baseline handling
$nullBaseThrew = $false
try {
    Compare-LaptopSnapshots -Baseline $null -Current (New-MockSnapshot) -ErrorAction Stop
} catch {
    $nullBaseThrew = $true
}
Record-Test "Compare-LaptopSnapshots cleanly rejects null Baseline" $nullBaseThrew "Threw expected binding/validation error"

# Test 2.2: Null Current handling
$nullCurrThrew = $false
try {
    Compare-LaptopSnapshots -Baseline (New-MockSnapshot) -Current $null -ErrorAction Stop
} catch {
    $nullCurrThrew = $true
}
Record-Test "Compare-LaptopSnapshots cleanly rejects null Current" $nullCurrThrew "Threw expected binding/validation error"

# Test 2.3: Zero Free RAM (complete memory exhaustion)
$zeroRamBase = New-MockSnapshot -FreeRAM_MB 0.0
$zeroRamCurr = New-MockSnapshot -FreeRAM_MB 0.0
$zeroRamRes = $null
$zeroRamPass = $true
try {
    $zeroRamRes = Compare-LaptopSnapshots -Baseline $zeroRamBase -Current $zeroRamCurr
    $zeroRamPass = ($zeroRamRes.RAMGained_MB -eq 0.0 -and $zeroRamRes.PassesAcceptanceCriteria -eq $false)
} catch {
    $zeroRamPass = $false
}
Record-Test "Handles 0.0 MB Free RAM without division by zero or crash" $zeroRamPass "RAMGained: $($zeroRamRes.RAMGained_MB), Passes: $($zeroRamRes.PassesAcceptanceCriteria)"

# Test 2.4: Severe negative delta (RAM decreased drastically, storage decreased)
$bHealthy = New-MockSnapshot -FreeRAM_MB 3000.0 -DriveC_Free_GB 50.0
$cDegraded = New-MockSnapshot -FreeRAM_MB 200.0 -DriveC_Free_GB 20.0
$negRes = $null
$negPass = $true
try {
    $negRes = Compare-LaptopSnapshots -Baseline $bHealthy -Current $cDegraded
    $negPass = ($negRes.RAMGained_MB -eq -2800.0 -and $negRes.StorageReclaimed_GB -eq -30.0 -and $negRes.PassesAcceptanceCriteria -eq $false)
} catch {
    $negPass = $false
}
Record-Test "Handles severe negative deltas (-2800MB RAM, -30GB Storage)" $negPass "RAMGained: $($negRes.RAMGained_MB), Storage: $($negRes.StorageReclaimed_GB)"

# Test 2.5: Division by Zero in FreeSpace_Percent (DriveC_Total_GB = 0)
$bZeroDisk = [PSCustomObject]@{
    Timestamp                  = [DateTime]::Now
    OS                         = "Windows 11"
    FreeRAM_MB                 = 1000.0
    TotalRAM_GB                = 8.0
    FreeRAM_Percent            = 12.0
    MemoryCompression_MB       = 0.0
    PageFile_Usage_MB          = 0.0
    PageFile_Allocated_MB      = 0.0
    DriveC_Free_GB             = 0.0
    DriveC_Total_GB            = 0.0  # 0 Total disk!
    ActivePowerScheme          = "Balanced"
    ProcessCount               = 100
    StartupItemsCount          = 5
    TopProcesses               = @()
}
$cZeroDisk = [PSCustomObject]@{
    Timestamp                  = [DateTime]::Now
    OS                         = "Windows 11"
    FreeRAM_MB                 = 1600.0
    TotalRAM_GB                = 8.0
    FreeRAM_Percent            = 20.0
    MemoryCompression_MB       = 0.0
    PageFile_Usage_MB          = 0.0
    PageFile_Allocated_MB      = 0.0
    DriveC_Free_GB             = 2.0
    DriveC_Total_GB            = 0.0  # 0 Total disk!
    ActivePowerScheme          = "Balanced"
    ProcessCount               = 100
    StartupItemsCount          = 5
    TopProcesses               = @()
}

$zeroDiskDivPass = $true
$zeroDiskErr = ""
try {
    $zeroDiskRes = Compare-LaptopSnapshots -Baseline $bZeroDisk -Current $cZeroDisk
    # Check if JSON generation or Table formatting survived
    $zeroDiskPass = ($null -ne $zeroDiskRes -and $null -ne $zeroDiskRes.ReportTable)
} catch {
    $zeroDiskDivPass = $false
    $zeroDiskErr = $_.Exception.Message
}
Record-Test "Survives DriveC_Total_GB = 0 (division by zero probe in report generation)" $zeroDiskDivPass $zeroDiskErr

# Test 2.6: Extreme Integer Overflow in ProcessCount
# Current.ProcessCount = [int]::MaxValue, Baseline.ProcessCount = -1 -> [int] cast overflow
$bProcMin = New-MockSnapshot -ProcessCount -1
$cProcMax = New-MockSnapshot -ProcessCount ([int]::MaxValue)
$overflowPass = $true
$overflowErr = ""
try {
    $overflowRes = Compare-LaptopSnapshots -Baseline $bProcMin -Current $cProcMax
} catch {
    $overflowPass = $false
    $overflowErr = $_.Exception.Message
}
Record-Test "Integer overflow resilience in ProcessCount ([int]::MaxValue - -1)" $overflowPass $overflowErr

# Test 2.7: Extreme Double Values (Double.MaxValue, Double.MinValue, Double.NaN, Double.PositiveInfinity)
$extremeDoubles = @(
    @{ Name = "Double.MaxValue"; Val = [double]::MaxValue },
    @{ Name = "Double.MinValue"; Val = [double]::MinValue },
    @{ Name = "Double.PositiveInfinity"; Val = [double]::PositiveInfinity },
    @{ Name = "Double.NegativeInfinity"; Val = [double]::NegativeInfinity },
    @{ Name = "Double.NaN"; Val = [double]::NaN }
)

foreach ($ed in $extremeDoubles) {
    $dPass = $true
    $dErr = ""
    try {
        $bMock = New-MockSnapshot -FreeRAM_MB 1000.0
        $cMock = New-MockSnapshot -FreeRAM_MB $ed.Val
        $dRes = Compare-LaptopSnapshots -Baseline $bMock -Current $cMock
        if ($null -eq $dRes.ReportTable) { $dPass = $false }
    } catch {
        $dPass = $false
        $dErr = $_.Exception.Message
    }
    Record-Test "Handles extreme double FreeRAM_MB: $($ed.Name)" $dPass $dErr
}

# Test 2.8: Sparse / Missing Property Object Resilience
# What if objects are missing some interface contract properties?
$sparseBase = [PSCustomObject]@{
    Timestamp   = [DateTime]::Now
    FreeRAM_MB  = 1200.0
}
$sparseCurr = [PSCustomObject]@{
    Timestamp   = [DateTime]::Now
    FreeRAM_MB  = 1800.0
}
$sparsePass = $true
$sparseErr = ""
try {
    $sparseRes = Compare-LaptopSnapshots -Baseline $sparseBase -Current $sparseCurr
    $sparsePass = ($sparseRes.RAMGained_MB -eq 600.0)
} catch {
    $sparsePass = $false
    $sparseErr = $_.Exception.Message
}
Record-Test "Sparse PSCustomObject (missing secondary properties) handled gracefully" $sparsePass $sparseErr

# Test 2.9: Markdown Special Characters and Injection in String Fields
$injectBase = New-MockSnapshot
$injectBase.OS = "Windows 11 | Pipe | Injection `n <script>alert(1)</script>"
$injectCurr = New-MockSnapshot
$injectCurr.ActivePowerScheme = "Scheme | Exploit [Link](http://malicious.url)"

$injectPass = $true
$injectErr = ""
try {
    $injectRes = Compare-LaptopSnapshots -Baseline $injectBase -Current $injectCurr -Preset "Preset|With|Pipes" -ReportId "ID<>&"
    $injectPass = ($null -ne $injectRes.ReportMarkdown -and $null -ne $injectRes.ReportJson)
} catch {
    $injectPass = $false
    $injectErr = $_.Exception.Message
}
Record-Test "Special markdown chars and script injection in strings do not crash report generator" $injectPass $injectErr


# =============================================================================
# SUITE 3: Rapid Polling & Resource Exhaustion on Get-LaptopSystemSnapshot
# =============================================================================
Write-Host "`n>> SUITE 3: Rapid Polling & Resource Exhaustion (Get-LaptopSystemSnapshot)" -ForegroundColor Yellow

$procBefore = Get-Process -Id $PID
$wsBeforeMB = [math]::Round($procBefore.WorkingSet64 / 1MB, 2)
$pmBeforeMB = [math]::Round($procBefore.PrivateMemorySize64 / 1MB, 2)
$handlesBefore = $procBefore.HandleCount

Write-Host "  Initial PowerShell Process State:" -ForegroundColor Gray
Write-Host "    Working Set   : $wsBeforeMB MB" -ForegroundColor Gray
Write-Host "    Private Memory: $pmBeforeMB MB" -ForegroundColor Gray
Write-Host "    Handle Count  : $handlesBefore" -ForegroundColor Gray

# We will run 10 rapid iterations of Get-LaptopSystemSnapshot
$loopIterations = 10
$iterationTimes = [System.Collections.Generic.List[long]]::new()
$snapshots = [System.Collections.Generic.List[psobject]]::new()
$loopExceptions = [System.Collections.Generic.List[string]]::new()

Write-Host "  Executing $loopIterations rapid snapshot captures..." -ForegroundColor Gray

$loopSw = [System.Diagnostics.Stopwatch]::StartNew()
for ($i = 1; $i -le $loopIterations; $i++) {
    $iterSw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $snap = Get-LaptopSystemSnapshot
        $iterSw.Stop()
        $iterationTimes.Add($iterSw.ElapsedMilliseconds)
        $snapshots.Add($snap)
        Write-Host "    Iteration $i/$loopIterations completed in $($iterSw.ElapsedMilliseconds) ms (Free RAM: $($snap.FreeRAM_MB) MB)" -ForegroundColor DarkGray
    } catch {
        $iterSw.Stop()
        $loopExceptions.Add("Iteration $i failed: $($_.Exception.Message)")
        Write-Host "    Iteration $i FAILED in $($iterSw.ElapsedMilliseconds) ms: $($_.Exception.Message)" -ForegroundColor Red
    }
}
$loopSw.Stop()

$procAfter = Get-Process -Id $PID
$wsAfterMB = [math]::Round($procAfter.WorkingSet64 / 1MB, 2)
$pmAfterMB = [math]::Round($procAfter.PrivateMemorySize64 / 1MB, 2)
$handlesAfter = $procAfter.HandleCount

$wsDeltaMB = [math]::Round($wsAfterMB - $wsBeforeMB, 2)
$pmDeltaMB = [math]::Round($pmAfterMB - $pmBeforeMB, 2)
$handleDelta = $handlesAfter - $handlesBefore

Write-Host "  Post-Loop Process State:" -ForegroundColor Gray
Write-Host "    Working Set Delta   : $wsDeltaMB MB ($wsBeforeMB -> $wsAfterMB MB)" -ForegroundColor Gray
Write-Host "    Private Memory Delta: $pmDeltaMB MB ($pmBeforeMB -> $pmAfterMB MB)" -ForegroundColor Gray
Write-Host "    Handle Delta        : $handleDelta ($handlesBefore -> $handlesAfter)" -ForegroundColor Gray
Write-Host "    Total Elapsed Time  : $([math]::Round($loopSw.Elapsed.TotalSeconds, 1)) s" -ForegroundColor Gray

# Assertions for Suite 3:
# 3.1: Zero unhandled exceptions during rapid polling
Record-Test "Rapid polling loop ($loopIterations iterations) completed with 0 unhandled exceptions" ($loopExceptions.Count -eq 0) ($loopExceptions -join "; ")

# 3.2: All snapshots returned are structurally complete
$allValid = ($snapshots.Count -eq $loopIterations)
foreach ($s in $snapshots) {
    if ($null -eq $s.FreeRAM_MB -or $s.FreeRAM_MB -le 0 -or $null -eq $s.DriveC_Free_GB) {
        $allValid = $false
        break
    }
}
Record-Test "All $loopIterations captured snapshots are non-null and valid" $allValid "Captured $($snapshots.Count) valid snapshots"

# 3.3: Memory leak check: Private memory growth must not exceed 80 MB across 10 iterations
# Note: CIM/WMI objects in .NET can cause minor GC deferrals, but >= 80 MB would indicate a severe unmanaged leak
$noMemoryLeak = ($pmDeltaMB -lt 80.0)
Record-Test "Memory stability: Private memory delta is < 80 MB (Actual: $pmDeltaMB MB)" $noMemoryLeak "Private memory grew by $pmDeltaMB MB"

# 3.4: Handle stability: Handle growth must not exceed 100 handles
$noSevereHandleGrowth = ($handleDelta -lt 100)
Record-Test "Handle stability: Handle count growth is < 100 (Actual: $handleDelta)" $noSevereHandleGrowth "Handle delta: $handleDelta"

# 3.5: No catastrophic execution time degradation (last iteration time < 3.5x first iteration time)
$firstIter = $iterationTimes[0]
$lastIter = $iterationTimes[$iterationTimes.Count - 1]
$noDegradation = ($lastIter -lt ($firstIter * 3.5))
Record-Test "Execution time stability: No severe degradation (Iter 1: $firstIter ms, Iter ${loopIterations}: $lastIter ms)" $noDegradation "Ratio: $([math]::Round($lastIter / [math]::Max($firstIter, 1), 2))x"


# =============================================================================
# SUMMARY & VERDICT
# =============================================================================
Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "               ADVERSARIAL STRESS TEST EXECUTION SUMMARY                        " -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  Total Tests Executed : $($passCount + $failCount)" -ForegroundColor Gray
Write-Host "  Passed               : $passCount" -ForegroundColor Green
Write-Host "  Failed               : $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Green" })
Write-Host "================================================================================" -ForegroundColor Cyan

if ($failCount -gt 0) {
    Write-Host "`nFAILED FINDINGS:" -ForegroundColor Red
    foreach ($f in $findings) {
        Write-Host "  - $f" -ForegroundColor Red
    }
    exit 1
} else {
    Write-Host "`n>> VERDICT: ALL ADVERSARIAL STRESS TESTS PASSED." -ForegroundColor Green
    exit 0
}
