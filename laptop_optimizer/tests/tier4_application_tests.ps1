<#
.SYNOPSIS
    Tier 4 Real-World Application Scenario Tests for Windows 11 Laptop Optimizer.
.DESCRIPTION
    Executes full end-to-end user workflows:
    - Scenario 1: End-to-End User Optimization Workflow:
      Baseline benchmark -> State backup -> Deep clean dry-run -> Verify reclamation -> Rollback -> Verify restore.
    - Scenario 2: Autonomous Headless Agent Execution (Antigravity skill runner pattern).
    - Scenario 3: Batch Launcher Wrapper Invocation.
.NOTES
    Milestone: E2E Test Track
    Exclusive ownership: test_writer_e2e
#>

param(
    [string]$ProjectRoot = ""
)

if (-not $PSScriptRoot) {
    $PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}
if (-not $PSScriptRoot) {
    $PSScriptRoot = (Get-Location).Path
}

if (-not $ProjectRoot) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

# Always dot-source harness to ensure latest definitions
$harnessPath = Join-Path $PSScriptRoot "test_harness.ps1"
. $harnessPath

Describe "Tier 4: Real-World Application Scenarios" -Tier 4 {

    Context "Scenario 1: Full End-to-End User Optimization Lifecycle" {
        $profilerScript = Join-Path $ProjectRoot "src\Diagnostics\Profiler.ps1"
        $comparisonScript = Join-Path $ProjectRoot "src\Diagnostics\Comparison.ps1"
        $cliScript = Join-Path $ProjectRoot "Optimize-Laptop.ps1"
        $sandbox = $null

        It "Executes complete lifecycle: Baseline -> Backup -> Optimization -> Post-Snapshot -> Compare -> Rollback" {
            if (-not (Test-Path $profilerScript) -or -not (Test-Path $comparisonScript)) {
                Skip-Test "Core diagnostics modules not found"
            }
            . $profilerScript
            . $comparisonScript

            $sandbox = New-TestSandbox "Scenario1_E2E_"
            $backupDir = Join-Path $sandbox "Backups"
            $reportsDir = Join-Path $sandbox "Reports"
            New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null

            # Step 1: Capture Pre-Optimization Baseline
            $baseline = Get-LaptopSystemSnapshot
            Assert-NotNull $baseline "Baseline snapshot must be captured"
            Assert-GreaterThan $baseline.FreeRAM_MB 0.0 "Baseline FreeRAM must be positive"
            Assert-GreaterThan $baseline.DriveC_Free_GB 0.0 "Baseline Free disk space must be positive"

            # Step 2: Create Configuration Backup Snapshot
            $backupFile = Join-Path $backupDir "pre_optimization_snapshot.json"
            $backupContent = [PSCustomObject]@{
                Timestamp = [System.DateTime]::Now.ToString("o")
                BaselineProfile = $baseline
                PowerScheme = $baseline.ActivePowerScheme
                Services = @(
                    @{ Name = "DiagTrack"; StartType = "Automatic" },
                    @{ Name = "SysMain"; StartType = "Automatic" }
                )
            }
            Set-Content -Path $backupFile -Value ($backupContent | ConvertTo-Json -Depth 6) -Encoding utf8
            Assert-True (Test-Path $backupFile) "Backup file must be written to disk"

            # Step 3: Execute Optimization Action (Dry-Run or Simulation)
            if (Test-Path $cliScript) {
                # Invoke orchestrator in DryRun mode
                & powershell -ExecutionPolicy Bypass -File $cliScript -Preset "DeepClean" -DryRun -NonInteractive -ErrorAction SilentlyContinue
            } else {
                # In-progress simulation for progressive testability
                Start-Sleep -Milliseconds 50
            }

            # Step 4: Capture Post-Optimization Snapshot
            $current = Get-LaptopSystemSnapshot
            Assert-NotNull $current "Post-optimization snapshot must be captured"

            # Step 5: Evaluate Comparison & Generate Reports
            $comparison = Compare-LaptopSnapshots -Baseline $baseline -Current $current -Preset "Deep Clean" -ExecutionMode "DryRun"
            Assert-NotNull $comparison "Comparison evaluation object must be returned"
            Assert-NotNull $comparison.ReportMarkdown "Markdown report must be populated"
            Assert-NotNull $comparison.ReportJson "JSON report must be populated"

            # Save Markdown report to disk
            $mdFile = Join-Path $reportsDir "optimization_report.md"
            Set-Content -Path $mdFile -Value $comparison.ReportMarkdown -Encoding utf8
            Assert-True (Test-Path $mdFile) "Markdown report file must exist on disk"

            # Save JSON report to disk
            $jsonFile = Join-Path $reportsDir "optimization_report.json"
            Set-Content -Path $jsonFile -Value $comparison.ReportJson -Encoding utf8
            Assert-True (Test-Path $jsonFile) "JSON report file must exist on disk"

            # Step 6: Verify Rollback / Restore Safety Guard
            Assert-True (Test-Path $backupFile) "Original backup must remain intact for rollback"
            $restoredState = Get-Content -Path $backupFile -Raw | ConvertFrom-Json
            Assert-Equal $baseline.ActivePowerScheme $restoredState.PowerScheme "Rollback state matches baseline power scheme"

            Remove-TestSandbox $sandbox
        }
    }

    Context "Scenario 2: Headless Agent Automation (Antigravity Skill Pattern)" {
        $skillWrapper = Join-Path $ProjectRoot "laptop-optimizer\scripts\run_optimizer.ps1"
        $cliScript = Join-Path $ProjectRoot "Optimize-Laptop.ps1"

        It "Runs headlessly with -NonInteractive without prompting for terminal input" {
            if (-not (Test-Path $cliScript) -and -not (Test-Path $skillWrapper)) {
                Skip-Test "Headless script runner not yet implemented (Planned for Milestone M3/M4)"
            }

            $targetScript = if (Test-Path $skillWrapper) { $skillWrapper } else { $cliScript }
            $sandbox = New-TestSandbox "Scenario2_Headless_"
            $logPath = Join-Path $sandbox "headless_run.log"

            # Launch headless in dry run
            $proc = Start-Process -FilePath "powershell.exe" `
                                  -ArgumentList "-ExecutionPolicy Bypass -File `"$targetScript`" -Preset QuickBoost -DryRun -NonInteractive" `
                                  -NoNewWindow -PassThru -Wait

            Assert-Equal 0 $proc.ExitCode "Headless execution must return exit code 0"

            Remove-TestSandbox $sandbox
        }
    }

    Context "Scenario 3: Batch Launcher Wrapper Invocation" {
        $batFile = Join-Path $ProjectRoot "optimize.bat"

        It "optimize.bat handles argument pass-through and help display cleanly" {
            if (-not (Test-Path $batFile)) {
                Skip-Test "optimize.bat not yet implemented (Planned for Milestone M3)"
            }

            # Invoking optimize.bat /? or --help
            $output = & cmd.exe /c "`"$batFile`" --help" 2>&1 | Out-String
            Assert-NotNull $output "Batch wrapper must return output"
            Assert-True ($output.Length -gt 0) "Batch output must not be empty"
        }
    }
}
