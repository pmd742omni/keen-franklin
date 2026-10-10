<#
.SYNOPSIS
    Unit tests for Milestone M1 (Platform, Types, Profiler, Comparison).
.DESCRIPTION
    Validates genuine functionality, type safety, interface contract adherence,
    and edge-case handling for all M1 modules.
#>

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$srcDir = Join-Path $projectRoot "src"

$passed = 0
$failed = 0

function Assert-True([bool]$condition, [string]$message) {
    if ($condition) {
        Write-Host "  [PASS] $message" -ForegroundColor Green
        $script:passed++
    } else {
        Write-Host "  [FAIL] $message" -ForegroundColor Red
        $script:failed++
    }
}

function Assert-Equal($actual, $expected, [string]$message) {
    if ($actual -eq $expected) {
        Write-Host "  [PASS] $message (Expected: '$expected', Actual: '$actual')" -ForegroundColor Green
        $script:passed++
    } else {
        Write-Host "  [FAIL] $message (Expected: '$expected', Actual: '$actual')" -ForegroundColor Red
        $script:failed++
    }
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " RUNNING M1 UNIT TESTS: Common & Diagnostics Modules     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# -----------------------------------------------------------------------------
# Test 1: Platform.ps1
# -----------------------------------------------------------------------------
Write-Host "`n[Test Group 1] src/Common/Platform.ps1" -ForegroundColor Yellow
$platformPath = Join-Path $srcDir "Common\Platform.ps1"
Assert-True (Test-Path $platformPath) "Platform.ps1 file exists at $platformPath"

. $platformPath

# 1.1 Test-IsElevated
$isElevated = Test-IsElevated
Assert-True ($isElevated -is [bool]) "Test-IsElevated returns a boolean ($isElevated)"

# 1.2 Test-IsPS7
$isPS7 = Test-IsPS7
Assert-True ($isPS7 -is [bool]) "Test-IsPS7 returns a boolean ($isPS7)"

# 1.3 Get-Coalesce
$coalesced1 = Get-Coalesce $null "fallback"
Assert-Equal $coalesced1 "fallback" "Get-Coalesce returns fallback when first argument is null"
$coalesced2 = Get-Coalesce "primary" "fallback"
Assert-Equal $coalesced2 "primary" "Get-Coalesce returns primary value when non-null"

# 1.4 ConvertTo-JsonSafe
$sampleObj = [PSCustomObject]@{ A = 1; B = @{ C = "nested" } }
$jsonStr = ConvertTo-JsonSafe -InputObject $sampleObj
Assert-True ($jsonStr -match '"nested"') "ConvertTo-JsonSafe serializes nested objects"

# 1.5 Get-LaptopPlatformInfo
$platformInfo = Get-LaptopPlatformInfo
Assert-True ($null -ne $platformInfo) "Get-LaptopPlatformInfo returns an object"
Assert-True ($platformInfo.OSName.Length -gt 0) "OSName is non-empty ('$($platformInfo.OSName)')"
Assert-True ($platformInfo.CPUCores -ge 1) "CPUCores is >= 1 ($($platformInfo.CPUCores))"
Assert-True ($platformInfo.CPULogicalProcessors -ge 1) "CPULogicalProcessors is >= 1 ($($platformInfo.CPULogicalProcessors))"
Assert-True ($platformInfo.TotalPhysicalRAM_Bytes -gt 1GB) "TotalPhysicalRAM_Bytes is > 1GB ($($platformInfo.TotalPhysicalRAM_Bytes))"
Assert-True ($platformInfo.TotalPhysicalRAM_GB -gt 1.0) "TotalPhysicalRAM_GB is > 1.0 ($($platformInfo.TotalPhysicalRAM_GB))"
Assert-True ($platformInfo.PSVersion.Length -gt 0) "PSVersion is reported ('$($platformInfo.PSVersion)')"

# -----------------------------------------------------------------------------
# Test 2: Types.ps1
# -----------------------------------------------------------------------------
Write-Host "`n[Test Group 2] src/Common/Types.ps1" -ForegroundColor Yellow
$typesPath = Join-Path $srcDir "Common\Types.ps1"
Assert-True (Test-Path $typesPath) "Types.ps1 file exists at $typesPath"

. $typesPath

# 2.1 C# P/Invoke Type Loaded
$nativeType = [System.Type]::GetType("LaptopOptimizer.Win32Native")
if (-not $nativeType) {
    # Check in loaded assemblies
    $nativeType = [AppDomain]::CurrentDomain.GetAssemblies() |
        ForEach-Object { $_.GetType("LaptopOptimizer.Win32Native") } |
        Where-Object { $_ -ne $null } | Select-Object -First 1
}
Assert-True ($null -ne $nativeType) "LaptopOptimizer.Win32Native class compiled and loaded successfully"

# 2.2 Foreground process ID query
$fgPid = Get-LaptopForegroundProcessId
Assert-True ($fgPid -is [int]) "Get-LaptopForegroundProcessId returns an int ($fgPid)"
Assert-True ($fgPid -ge 0) "Get-LaptopForegroundProcessId returns valid PID or 0 ($fgPid)"

# 2.3 Foreground window handle query
$hwnd = Get-LaptopForegroundWindowHandle
Assert-True ($hwnd -is [System.IntPtr]) "Get-LaptopForegroundWindowHandle returns IntPtr"

# 2.4 Invoke-LaptopEmptyWorkingSet
# Safety check: PID 0 and 4 should be gracefully skipped and return false
$resPid0 = Invoke-LaptopEmptyWorkingSet -ProcessId 0
Assert-Equal $resPid0 $false "Invoke-LaptopEmptyWorkingSet gracefully rejects PID 0"
$resPid4 = Invoke-LaptopEmptyWorkingSet -ProcessId 4
Assert-Equal $resPid4 $false "Invoke-LaptopEmptyWorkingSet gracefully rejects System PID 4"

# Self-trim test on current PowerShell process
$resSelf = Invoke-LaptopEmptyWorkingSet -ProcessId $PID
Assert-True ($resSelf -is [bool]) "Invoke-LaptopEmptyWorkingSet on current process PID $PID executes and returns boolean ($resSelf)"

# -----------------------------------------------------------------------------
# Test 3: Profiler.ps1
# -----------------------------------------------------------------------------
Write-Host "`n[Test Group 3] src/Diagnostics/Profiler.ps1" -ForegroundColor Yellow
$profilerPath = Join-Path $srcDir "Diagnostics\Profiler.ps1"
Assert-True (Test-Path $profilerPath) "Profiler.ps1 file exists at $profilerPath"

. $profilerPath

# 3.1 Get-LaptopStartupItems
$startups = Get-LaptopStartupItems
Assert-True ($startups -is [array]) "Get-LaptopStartupItems returns an array"
Write-Host "    Found $($startups.Count) startup items" -ForegroundColor Gray
if ($startups.Count -gt 0) {
    $firstItem = $startups[0]
    Assert-True ($firstItem.PSObject.Properties['Name'] -ne $null) "Startup item contains Name property"
    Assert-True ($firstItem.PSObject.Properties['Status'] -ne $null) "Startup item contains Status property"
    Assert-True ($firstItem.PSObject.Properties['Scope'] -ne $null) "Startup item contains Scope property"
}

# 3.2 Get-LaptopSystemSnapshot Interface Contract Compliance
$snapshot = Get-LaptopSystemSnapshot
Assert-True ($null -ne $snapshot) "Get-LaptopSystemSnapshot returns snapshot object"

# Mandatory Interface Contract Properties from PROJECT.md:
$contractProps = @(
    "Timestamp",
    "OS",
    "FreeRAM_MB",
    "TotalRAM_GB",
    "FreeRAM_Percent",
    "MemoryCompression_MB",
    "PageFile_Usage_MB",
    "PageFile_Allocated_MB",
    "DriveC_Free_GB",
    "DriveC_Total_GB",
    "ActivePowerScheme",
    "ProcessCount",
    "StartupItemsCount",
    "TopProcesses"
)

foreach ($prop in $contractProps) {
    $hasProp = ($null -ne $snapshot.PSObject.Properties[$prop])
    Assert-True $hasProp "Snapshot has mandatory contract property '$prop'"
}

# Value sanity checks
Assert-True ($snapshot.FreeRAM_MB -gt 0) "FreeRAM_MB is positive ($($snapshot.FreeRAM_MB) MB)"
Assert-True ($snapshot.TotalRAM_GB -gt 0) "TotalRAM_GB is positive ($($snapshot.TotalRAM_GB) GB)"
Assert-True ($snapshot.FreeRAM_Percent -ge 0 -and $snapshot.FreeRAM_Percent -le 100) "FreeRAM_Percent is between 0% and 100% ($($snapshot.FreeRAM_Percent)%)"
Assert-True ($snapshot.DriveC_Total_GB -gt 10.0) "DriveC_Total_GB is > 10GB ($($snapshot.DriveC_Total_GB) GB)"
Assert-True ($snapshot.DriveC_Free_GB -gt 0) "DriveC_Free_GB is positive ($($snapshot.DriveC_Free_GB) GB)"
Assert-True ($snapshot.ProcessCount -gt 10) "ProcessCount is realistic (> 10 processes, found $($snapshot.ProcessCount))"
Assert-True ($snapshot.ActivePowerScheme.Length -gt 0) "ActivePowerScheme is non-empty ('$($snapshot.ActivePowerScheme)')"
Assert-True ($snapshot.TopProcesses.Count -gt 0) "TopProcesses returns list of processes (Count: $($snapshot.TopProcesses.Count))"

# Check TopProcesses item schema
$top1 = $snapshot.TopProcesses[0]
Assert-True ($top1.PSObject.Properties['Name'] -ne $null) "TopProcess has Name property"
Assert-True ($top1.PSObject.Properties['Id'] -ne $null) "TopProcess has Id property"
Assert-True ($top1.PSObject.Properties['WS_MB'] -ne $null) "TopProcess has WS_MB property"
Assert-True ($top1.PSObject.Properties['CPU_Sec'] -ne $null) "TopProcess has CPU_Sec property"

# 3.3 Detailed snapshot switch
$detailedSnapshot = Get-LaptopSystemSnapshot -Detailed
Assert-True ($detailedSnapshot.PSObject.Properties['StartupItems'] -ne $null) "Detailed snapshot includes StartupItems list"
Assert-True ($detailedSnapshot.PSObject.Properties['TopProcessesByCPU'] -ne $null) "Detailed snapshot includes TopProcessesByCPU list"

# -----------------------------------------------------------------------------
# Test 4: Comparison.ps1
# -----------------------------------------------------------------------------
Write-Host "`n[Test Group 4] ../.agents/teamwork/explorer_m1_fix_2/Proposed_Comparison.ps1" -ForegroundColor Yellow
$comparisonPath = "c:/Users/ignaz/antigravity/keen-franklin/.agents/teamwork/explorer_m1_fix_2/Proposed_Comparison.ps1"
Assert-True (Test-Path $comparisonPath) "Comparison.ps1 file exists at $comparisonPath"

. $comparisonPath

# 4.1 Mock baseline and current snapshots for deterministic acceptance criteria verification
$mockBaseline = [PSCustomObject]@{
    Timestamp                  = [DateTime]::Now.AddMinutes(-10)
    OS                         = "Microsoft Windows 11 Home"
    FreeRAM_MB                 = 1180.7
    TotalRAM_GB                = 7.66
    TotalRAM_MB                = 7845.5
    FreeRAM_Percent            = 15.0
    MemoryCompression_MB       = 219.2
    PageFile_Usage_MB          = 1713.0
    PageFile_Allocated_MB      = 12288.0
    DriveC_Free_GB             = 38.01
    DriveC_Total_GB            = 237.36
    DriveC_Free_Percent        = 16.0
    ActivePowerScheme          = "Balanced (381b4222-f694-41f0-9685-ff5bb260df2e)"
    ProcessCount               = 324
    StartupItemsCount          = 14
    TopProcesses               = @(
        [PSCustomObject]@{ Name = "chrome"; Id = 100; WS_MB = 650.0; CPU_Sec = 120.0 }
    )
}

$mockCurrentPass = [PSCustomObject]@{
    Timestamp                  = [DateTime]::Now
    OS                         = "Microsoft Windows 11 Home"
    FreeRAM_MB                 = 1985.4    # > 1500 MB (PASS)
    TotalRAM_GB                = 7.66
    TotalRAM_MB                = 7845.5
    FreeRAM_Percent            = 25.3
    MemoryCompression_MB       = 64.1      # -155.1 MB
    PageFile_Usage_MB          = 1240.0    # -473.0 MB
    PageFile_Allocated_MB      = 12288.0
    DriveC_Free_GB             = 40.25     # +2.24 GB >= 1.0 GB (PASS)
    DriveC_Total_GB            = 237.36
    DriveC_Free_Percent        = 17.0
    ActivePowerScheme          = "Balanced (381b4222-f694-41f0-9685-ff5bb260df2e)"
    ProcessCount               = 285       # -39 procs
    StartupItemsCount          = 14
    TopProcesses               = @(
        [PSCustomObject]@{ Name = "chrome"; Id = 100; WS_MB = 320.0; CPU_Sec = 125.0 }
    )
}

$mockCurrentFailRAM = [PSCustomObject]@{
    Timestamp                  = [DateTime]::Now
    OS                         = "Microsoft Windows 11 Home"
    FreeRAM_MB                 = 1350.0    # <= 1500 MB (FAIL)
    TotalRAM_GB                = 7.66
    TotalRAM_MB                = 7845.5
    FreeRAM_Percent            = 17.2
    MemoryCompression_MB       = 200.0
    PageFile_Usage_MB          = 1700.0
    PageFile_Allocated_MB      = 12288.0
    DriveC_Free_GB             = 40.25     # +2.24 GB (PASS)
    DriveC_Total_GB            = 237.36
    DriveC_Free_Percent        = 17.0
    ActivePowerScheme          = "Balanced (381b4222-f694-41f0-9685-ff5bb260df2e)"
    ProcessCount               = 310
    StartupItemsCount          = 14
    TopProcesses               = @()
}

$mockCurrentFailStorage = [PSCustomObject]@{
    Timestamp                  = [DateTime]::Now
    OS                         = "Microsoft Windows 11 Home"
    FreeRAM_MB                 = 1800.0    # > 1500 MB (PASS)
    TotalRAM_GB                = 7.66
    TotalRAM_MB                = 7845.5
    FreeRAM_Percent            = 22.9
    MemoryCompression_MB       = 150.0
    PageFile_Usage_MB          = 1600.0
    PageFile_Allocated_MB      = 12288.0
    DriveC_Free_GB             = 38.50     # +0.49 GB < 1.0 GB (FAIL)
    DriveC_Total_GB            = 237.36
    DriveC_Free_Percent        = 16.2
    ActivePowerScheme          = "Balanced (381b4222-f694-41f0-9685-ff5bb260df2e)"
    ProcessCount               = 310
    StartupItemsCount          = 14
    TopProcesses               = @()
}

# Run Comparison for Passing Case
$compPass = Compare-LaptopSnapshots -Baseline $mockBaseline -Current $mockCurrentPass -Preset "Quick Boost"
Assert-True ($null -ne $compPass) "Compare-LaptopSnapshots returns comparison object"

# Mandatory contract properties from PROJECT.md:
Assert-True ($compPass.PSObject.Properties['RAMGained_MB'] -ne $null) "Has RAMGained_MB property"
Assert-True ($compPass.PSObject.Properties['StorageReclaimed_GB'] -ne $null) "Has StorageReclaimed_GB property"
Assert-True ($compPass.PSObject.Properties['ProcessDelta'] -ne $null) "Has ProcessDelta property"
Assert-True ($compPass.PSObject.Properties['PassesAcceptanceCriteria'] -ne $null) "Has PassesAcceptanceCriteria property"
Assert-True ($compPass.PSObject.Properties['ReportMarkdown'] -ne $null) "Has ReportMarkdown property"

# Value verification
Assert-Equal $compPass.RAMGained_MB 804.7 "RAMGained_MB calculated correctly (804.7 MB)"
Assert-Equal $compPass.StorageReclaimed_GB 2.24 "StorageReclaimed_GB calculated correctly (2.24 GB)"
Assert-Equal $compPass.ProcessDelta -39 "ProcessDelta calculated correctly (-39)"
Assert-Equal $compPass.MemoryCompressionDelta_MB -155.1 "MemoryCompressionDelta_MB calculated correctly (-155.1 MB)"
Assert-Equal $compPass.PassesAcceptanceCriteria $true "PassesAcceptanceCriteria is true when both criteria met"

# Negative tests: failure cases for Acceptance Criteria
$compFailRAM = Compare-LaptopSnapshots -Baseline $mockBaseline -Current $mockCurrentFailRAM
Assert-Equal $compFailRAM.PassesAcceptanceCriteria $false "PassesAcceptanceCriteria is false when Free RAM <= 1500MB"
Assert-Equal $compFailRAM.AcceptanceCriteria.TargetFreeRAM_Exceeds1500MB $false "TargetFreeRAM_Exceeds1500MB is false when 1350MB"

$compFailStorage = Compare-LaptopSnapshots -Baseline $mockBaseline -Current $mockCurrentFailStorage
Assert-Equal $compFailStorage.PassesAcceptanceCriteria $false "PassesAcceptanceCriteria is false when Storage reclaimed < 1.0GB"
Assert-Equal $compFailStorage.AcceptanceCriteria.TargetStorageReclaimed_Exceeds1GB $false "TargetStorageReclaimed_Exceeds1GB is false when 0.49GB"

# Formatted Table Output verification
$table = $compPass.ReportTable
Assert-True ($table.Length -gt 0) "ReportTable contains non-empty string"
Assert-True ($table -match "LAPTOP OPTIMIZER PERFORMANCE COMPARISON") "ReportTable contains banner"
Assert-True ($table -match "Free RAM") "ReportTable contains Free RAM row"
Assert-True ($table -match "OVERALL EVALUATION: PASSED") "ReportTable contains PASSED evaluation"

# Markdown Report verification
$md = $compPass.ReportMarkdown
Assert-True ($md -match "# Laptop Optimization Performance Comparison Report") "ReportMarkdown contains header"
Assert-True ($md -match "Target Free RAM > 1,500 MB") "ReportMarkdown contains criteria checklist"
Assert-True ($md -match "Reclaimed Storage >= 1.00 GB") "ReportMarkdown contains storage criteria checklist"

# JSON Report Schema verification
$jsonObj = $compPass.ReportJson | ConvertFrom-Json
Assert-True ($null -ne $jsonObj) "ReportJson parses as valid JSON"
Assert-Equal $jsonObj.Deltas.RAMFreed_MB 804.7 "JSON Deltas.RAMFreed_MB matches calculation"
Assert-Equal $jsonObj.Deltas.StorageReclaimed_GB 2.24 "JSON Deltas.StorageReclaimed_GB matches calculation"
Assert-Equal $jsonObj.AcceptanceCriteriaVerification.OverallPassed $true "JSON AcceptanceCriteriaVerification.OverallPassed is true"

# 4.2 Live snapshot comparison test
Write-Host "`n[Test Group 5] Live End-to-End Snapshot & Self-Comparison" -ForegroundColor Yellow
$liveBaseline = Get-LaptopSystemSnapshot
Start-Sleep -Milliseconds 500
$liveCurrent = Get-LaptopSystemSnapshot
$liveComparison = Compare-LaptopSnapshots -Baseline $liveBaseline -Current $liveCurrent -Preset "Diagnostic Baseline Test"
Assert-True ($null -ne $liveComparison) "Compare-LaptopSnapshots succeeds on live snapshots"
Assert-True ($liveComparison.RAMGained_MB -is [double]) "RAMGained_MB is double on live comparison"
Assert-True ($liveComparison.StorageReclaimed_GB -is [double]) "StorageReclaimed_GB is double on live comparison"
Assert-True ($liveComparison.ProcessDelta -is [int]) "ProcessDelta is int on live comparison"

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " TEST EXECUTION SUMMARY" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Total Passed: $passed" -ForegroundColor Green
Write-Host " Total Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })

if ($failed -gt 0) {
    exit 1
} else {
    exit 0
}

