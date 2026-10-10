<#
.SYNOPSIS
    Master E2E Test Runner for Windows 11 Laptop Optimizer.
.DESCRIPTION
    Executes the 4-tier opaque-box E2E test suite (Tiers 1-4) or individual tiers.
    Aggregates test results, outputs formatted terminal summaries, writes optional
    JSON reports, and exits with code 0 on pass or non-zero on failure.
.PARAMETER Tier
    Specify 1, 2, 3, 4 to run an individual tier, or 0 to run all tiers (default: 0).
.PARAMETER TestName
    Optional regex filter to run tests matching a specific name or pattern.
.PARAMETER JsonReport
    Optional path to write structured JSON test execution report.
.PARAMETER VerboseReport
    Switch to output verbose progress.
.EXAMPLE
    .\run_all_tests.ps1
    .\run_all_tests.ps1 -Tier 1
    .\run_all_tests.ps1 -Tier 2 -JsonReport "results.json"
.NOTES
    Milestone: E2E Test Track
    Exclusive ownership: test_writer_e2e
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false, Position = 0)]
    [ValidateSet(0, 1, 2, 3, 4)]
    [int]$Tier = 0,

    [Parameter(Mandatory = $false, Position = 1)]
    [string]$TestName = "",

    [Parameter(Mandatory = $false)]
    [string]$JsonReport = "",

    [Parameter(Mandatory = $false)]
    [switch]$VerboseReport
)

$ErrorActionPreference = "Continue"

# Resolve directories
$testsDir = $PSScriptRoot
if (-not $testsDir) { $testsDir = (Get-Location).Path }
$projectRoot = Resolve-Path (Join-Path $testsDir "..")

# Load harness
$harnessPath = Join-Path $testsDir "test_harness.ps1"
if (-not (Test-Path $harnessPath)) {
    Write-Error "Test harness not found at: $harnessPath"
    exit 2
}
. $harnessPath

Reset-TestState
$global:TestRunnerState.FilterTier = $Tier
$global:TestRunnerState.FilterName = $TestName
$global:TestRunnerState.VerboseOutput = $VerboseReport.IsPresent

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "           WINDOWS 11 LAPTOP OPTIMIZER - E2E TEST RUNNER                        " -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ("Target Directory : {0}" -f $projectRoot) -ForegroundColor Gray
$tierLabel = if ($Tier -eq 0) { "All Tiers (1-4)" } else { "Tier $Tier" }
Write-Host ("Execution Tier   : {0}" -f $tierLabel) -ForegroundColor Gray
if ($TestName) {
    Write-Host ("Name Filter      : {0}" -f $TestName) -ForegroundColor Gray
}
Write-Host ("Timestamp        : {0}" -f [System.DateTime]::Now.ToString("yyyy-MM-dd HH:mm:ss")) -ForegroundColor Gray
Write-Host "================================================================================" -ForegroundColor Cyan

$tierFiles = @(
    @{ Tier = 1; Script = "tier1_feature_tests.ps1"; Name = "Tier 1: Feature Coverage" },
    @{ Tier = 2; Script = "tier2_boundary_tests.ps1"; Name = "Tier 2: Boundary & Corner Cases" },
    @{ Tier = 3; Script = "tier3_combination_tests.ps1"; Name = "Tier 3: Cross-Feature Combinations" },
    @{ Tier = 4; Script = "tier4_application_tests.ps1"; Name = "Tier 4: Real-World Scenarios" }
)

$suiteStopwatch = [System.Diagnostics.Stopwatch]::StartNew()

try {
    foreach ($tf in $tierFiles) {
        if ($Tier -eq 0 -or $Tier -eq $tf.Tier) {
            $scriptPath = Join-Path $testsDir $tf.Script
            if (Test-Path $scriptPath) {
                Write-Host ""
                Write-Host (">> Executing {0} ({1})..." -f $tf.Name, $tf.Script) -ForegroundColor Yellow
                . $scriptPath -ProjectRoot $projectRoot
            } else {
                Write-Warning ("Test file not found: {0}" -f $scriptPath)
            }
        }
    }
} finally {
    $suiteStopwatch.Stop()
    Remove-AllSandboxes
}

# Aggregate and present results
$summary = Get-TestResultsSummary
$summary | Add-Member -NotePropertyName "TotalSuiteWallClockMs" -NotePropertyValue ([math]::Round($suiteStopwatch.Elapsed.TotalMilliseconds, 2)) -Force

Show-TestSummaryTable -Summary $summary

# Export JSON report if requested
if ($JsonReport) {
    try {
        $jsonDir = Split-Path -Parent $JsonReport
        if ($jsonDir -and -not (Test-Path $jsonDir)) {
            New-Item -ItemType Directory -Path $jsonDir -Force | Out-Null
        }
        $jsonPayload = $summary | ConvertTo-Json -Depth 5
        Set-Content -Path $JsonReport -Value $jsonPayload -Encoding utf8
        Write-Host ("JSON report exported to: {0}" -f $JsonReport) -ForegroundColor Gray
    } catch {
        Write-Warning ("Failed to write JSON report: {0}" -f $_.Exception.Message)
    }
}

# Exit code: 0 on all pass, 1 on failure
if ($summary.FailedCount -gt 0) {
    exit 1
} else {
    exit 0
}
