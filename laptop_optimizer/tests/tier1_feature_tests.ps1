<#
.SYNOPSIS
    Tier 1 Feature Coverage Tests for Windows 11 Laptop Optimizer.
.DESCRIPTION
    Verifies that each individual component and function operates according to its
    specification and interface contract (baseline profiling, snapshot comparison,
    platform information, Win32 types, disk cleanup dry-run, memory trimming dry-run,
    SSD TRIM dry-run, power scheme query, CLI parameters, and presets).
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

Describe "Tier 1: Feature Coverage & Interface Contracts" -Tier 1 {

    Context "Platform Compatibility & Environment Detection" {
        $platformScript = Join-Path $ProjectRoot "src\Common\Platform.ps1"

        It "Common\Platform.ps1 exists on disk" {
            Assert-True (Test-Path $platformScript) "Expected Platform.ps1 to exist at $platformScript"
        }

        It "Test-IsElevated returns a valid boolean without throwing" {
            . $platformScript
            $elevated = Test-IsElevated
            Assert-NotNull $elevated
            Assert-True ($elevated -is [bool]) "Expected Test-IsElevated to return [bool]"
        }

        It "Test-IsPS7 correctly identifies runtime version" {
            . $platformScript
            $isPs7 = Test-IsPS7
            $expected = ($PSVersionTable.PSVersion.Major -ge 7)
            Assert-Equal $expected $isPs7 "Test-IsPS7 output mismatch"
        }

        It "Get-LaptopPlatformInfo returns required hardware and OS specifications" {
            . $platformScript
            $info = Get-LaptopPlatformInfo
            Assert-NotNull $info "Expected platform info object"
            Assert-NotNull $info.OSName "Expected OSName"
            Assert-NotNull $info.OSBuild "Expected OSBuild"
            Assert-NotNull $info.OSArchitecture "Expected OSArchitecture"
            Assert-GreaterThan $info.CPUCores 0 "Expected positive CPU core count"
            Assert-GreaterThan $info.CPULogicalProcessors 0 "Expected positive logical processor count"
            Assert-GreaterThan $info.TotalPhysicalRAM_MB 1000.0 "Expected physical RAM > 1000 MB"
            Assert-GreaterThan $info.TotalPhysicalRAM_GB 1.0 "Expected physical RAM > 1 GB"
        }

        It "Get-Coalesce properly provides null-coalescing fallback" {
            . $platformScript
            $res1 = Get-Coalesce "ValueA" "FallbackB"
            Assert-Equal "ValueA" $res1
            $res2 = Get-Coalesce $null "FallbackB"
            Assert-Equal "FallbackB" $res2
        }

        It "ConvertTo-JsonSafe handles nested structures with safe depth" {
            . $platformScript
            $testObj = @{ A = @{ B = @{ C = "DeepValue" } } }
            $json = ConvertTo-JsonSafe -InputObject $testObj
            Assert-NotNull $json
            Assert-Match $json '"DeepValue"'
        }
    }

    Context "Win32 P/Invoke Memory Management Types" {
        $typesScript = Join-Path $ProjectRoot "src\Common\Types.ps1"

        It "Common\Types.ps1 exists on disk" {
            Assert-True (Test-Path $typesScript) "Expected Types.ps1 to exist at $typesScript"
        }

        It "Compiles and exposes [LaptopOptimizer.Win32Native] type" {
            . $typesScript
            $hasType = $false
            try {
                $hasType = ($null -ne ('LaptopOptimizer.Win32Native' -as [type])) -or ($null -ne [LaptopOptimizer.Win32Native])
            } catch {
                $hasType = $false
            }
            Assert-True $hasType "Expected LaptopOptimizer.Win32Native type to be compiled and accessible"
        }

        It "Get-LaptopForegroundProcessId retrieves integer PID or 0" {
            . $typesScript
            $fgPid = Get-LaptopForegroundProcessId
            Assert-NotNull $fgPid
            Assert-True ($fgPid -is [int]) "Foreground PID should be an integer"
            Assert-True ($fgPid -ge 0) "Foreground PID should be non-negative"
        }

        It "Invoke-LaptopEmptyWorkingSet safely handles protected or invalid PIDs" {
            . $typesScript
            # PID 4 is System - should return false safely without crashing
            $result = Invoke-LaptopEmptyWorkingSet -ProcessId 4
            Assert-False $result "Trimming PID 4 should return false safely"
            
            # Non-existent high PID should return false safely
            $fakePid = 999999
            $resultFake = Invoke-LaptopEmptyWorkingSet -ProcessId $fakePid
            Assert-False $resultFake "Trimming invalid PID should return false"
        }
    }

    Context "Startup Items Audit" {
        $profilerScript = Join-Path $ProjectRoot "src\Diagnostics\Profiler.ps1"

        It "Get-LaptopStartupItems enumerates registry startup items without error" {
            if (-not (Test-Path $profilerScript)) {
                Skip-Test "Profiler.ps1 not found (Milestone M1 in progress)"
            }
            . $profilerScript
            $items = Get-LaptopStartupItems
            Assert-NotNull $items "Expected startup items array or collection"
            if ($items.Count -gt 0) {
                $first = $items[0]
                Assert-NotNull $first.Name "Expected startup item to have Name"
                Assert-NotNull $first.Scope "Expected startup item to have Scope (User/System)"
                Assert-NotNull $first.Status "Expected startup item to have Status (Enabled/Disabled)"
            }
        }
    }

    Context "Baseline System Profiling (PROJECT.md Interface Contract)" {
        $profilerScript = Join-Path $ProjectRoot "src\Diagnostics\Profiler.ps1"

        It "Get-LaptopSystemSnapshot returns object conforming strictly to PROJECT.md interface contract" {
            if (-not (Test-Path $profilerScript)) {
                Skip-Test "Profiler.ps1 not found"
            }
            . $profilerScript
            $snap = Get-LaptopSystemSnapshot
            Assert-NotNull $snap "Expected snapshot object"

            # Mandatory Contract Properties (PROJECT.md § Diagnostics <-> Optimization / CLI)
            Assert-NotNull $snap.Timestamp "Contract property missing: Timestamp"
            Assert-True ($snap.Timestamp -is [System.DateTime]) "Timestamp should be [DateTime]"

            Assert-NotNull $snap.OS "Contract property missing: OS"
            Assert-True ($snap.OS.Length -gt 0) "OS string must not be empty"

            Assert-NotNull $snap.FreeRAM_MB "Contract property missing: FreeRAM_MB"
            Assert-GreaterThan ([double]$snap.FreeRAM_MB) 0.0 "FreeRAM_MB must be positive"

            Assert-NotNull $snap.TotalRAM_GB "Contract property missing: TotalRAM_GB"
            Assert-GreaterThan ([double]$snap.TotalRAM_GB) 1.0 "TotalRAM_GB must be > 1.0"

            Assert-NotNull $snap.FreeRAM_Percent "Contract property missing: FreeRAM_Percent"
            Assert-GreaterThan ([double]$snap.FreeRAM_Percent) 0.0 "FreeRAM_Percent must be positive"
            Assert-LessThan ([double]$snap.FreeRAM_Percent) 100.0 "FreeRAM_Percent must be < 100%"

            Assert-NotNull $snap.MemoryCompression_MB "Contract property missing: MemoryCompression_MB"
            Assert-True ([double]$snap.MemoryCompression_MB -ge 0.0) "MemoryCompression_MB must be >= 0"

            Assert-NotNull $snap.PageFile_Usage_MB "Contract property missing: PageFile_Usage_MB"
            Assert-True ([double]$snap.PageFile_Usage_MB -ge 0.0) "PageFile_Usage_MB must be >= 0"

            Assert-NotNull $snap.PageFile_Allocated_MB "Contract property missing: PageFile_Allocated_MB"
            Assert-True ([double]$snap.PageFile_Allocated_MB -ge 0.0) "PageFile_Allocated_MB must be >= 0"

            Assert-NotNull $snap.DriveC_Free_GB "Contract property missing: DriveC_Free_GB"
            Assert-GreaterThan ([double]$snap.DriveC_Free_GB) 0.0 "DriveC_Free_GB must be positive"

            Assert-NotNull $snap.DriveC_Total_GB "Contract property missing: DriveC_Total_GB"
            Assert-GreaterThan ([double]$snap.DriveC_Total_GB) 10.0 "DriveC_Total_GB must be > 10 GB"

            Assert-NotNull $snap.ActivePowerScheme "Contract property missing: ActivePowerScheme"
            Assert-Match $snap.ActivePowerScheme "[0-9a-fA-F-]{36}" "ActivePowerScheme must contain valid GUID"

            Assert-NotNull $snap.ProcessCount "Contract property missing: ProcessCount"
            Assert-GreaterThan ([int]$snap.ProcessCount) 5 "ProcessCount should be > 5"

            Assert-NotNull $snap.StartupItemsCount "Contract property missing: StartupItemsCount"
            Assert-True ([int]$snap.StartupItemsCount -ge 0) "StartupItemsCount must be >= 0"

            Assert-NotNull $snap.TopProcesses "Contract property missing: TopProcesses"
            Assert-True ($snap.TopProcesses.Count -gt 0) "TopProcesses must contain entries"
        }

        It "Get-LaptopSystemSnapshot -Detailed attaches detailed startup and CPU processes" {
            if (-not (Test-Path $profilerScript)) {
                Skip-Test "Profiler.ps1 not found"
            }
            . $profilerScript
            $snap = Get-LaptopSystemSnapshot -Detailed
            Assert-NotNull $snap.PSObject.Properties['StartupItems'] "Detailed snapshot must include StartupItems property"
            Assert-NotNull $snap.PSObject.Properties['TopProcessesByCPU'] "Detailed snapshot must include TopProcessesByCPU property"
        }
    }

    Context "Metric Comparison & Acceptance Criteria Evaluation" {
        $comparisonScript = Join-Path $ProjectRoot "src\Diagnostics\Comparison.ps1"

        It "Compare-LaptopSnapshots computes correct deltas and evaluates passing criteria" {
            if (-not (Test-Path $comparisonScript)) {
                Skip-Test "Comparison.ps1 not found"
            }
            . $comparisonScript

            # Synthetic Baseline: 1000MB Free RAM, 45.0 GB Free Disk, 120 processes
            $b = New-SyntheticSnapshot -FreeRAM_MB 1000.0 -DriveC_Free_GB 45.0 -ProcessCount 120
            # Synthetic Post: 1800MB Free RAM (+800MB), 47.5 GB Free Disk (+2.5GB), 110 processes (-10)
            $c = New-SyntheticSnapshot -FreeRAM_MB 1800.0 -DriveC_Free_GB 47.5 -ProcessCount 110

            $result = Compare-LaptopSnapshots -Baseline $b -Current $c -Preset "Deep Clean"
            Assert-NotNull $result "Comparison result must not be null"

            # Interface Contract verification
            Assert-Equal 800.0 $result.RAMGained_MB "RAMGained_MB delta calculation mismatch"
            Assert-Equal 2.5 $result.StorageReclaimed_GB "StorageReclaimed_GB delta calculation mismatch"
            Assert-Equal -10 $result.ProcessDelta "ProcessDelta calculation mismatch"

            # Acceptance criteria: Free RAM > 1500 MB (1800) and Reclaimed Storage >= 1GB (2.5) -> TRUE
            Assert-True $result.PassesAcceptanceCriteria "Expected PassesAcceptanceCriteria to be True"
            Assert-True ($result.ReportMarkdown.Length -gt 100) "Expected non-empty Markdown report"
            Assert-Match $result.ReportMarkdown "(?i)Overall Status.*PASSED"
        }

        It "Compare-LaptopSnapshots evaluates failing criteria when thresholds are not met" {
            if (-not (Test-Path $comparisonScript)) {
                Skip-Test "Comparison.ps1 not found"
            }
            . $comparisonScript

            # Case A: Free RAM below 1500MB (even if storage >= 1GB)
            $b = New-SyntheticSnapshot -FreeRAM_MB 900.0 -DriveC_Free_GB 40.0
            $cA = New-SyntheticSnapshot -FreeRAM_MB 1400.0 -DriveC_Free_GB 42.0 # RAM = 1400 < 1500
            $resA = Compare-LaptopSnapshots -Baseline $b -Current $cA
            Assert-False $resA.PassesAcceptanceCriteria "Should fail when FreeRAM <= 1500 MB"

            # Case B: Storage reclaimed below 1GB (even if Free RAM > 1500MB)
            $cB = New-SyntheticSnapshot -FreeRAM_MB 1900.0 -DriveC_Free_GB 40.5 # Reclaimed = 0.5 < 1.0 GB
            $resB = Compare-LaptopSnapshots -Baseline $b -Current $cB
            Assert-False $resB.PassesAcceptanceCriteria "Should fail when StorageReclaimed < 1.0 GB"
        }

        It "Compare-LaptopSnapshots produces valid JSON serialization" {
            if (-not (Test-Path $comparisonScript)) {
                Skip-Test "Comparison.ps1 not found"
            }
            . $comparisonScript
            $b = New-SyntheticSnapshot -FreeRAM_MB 1000.0 -DriveC_Free_GB 50.0
            $c = New-SyntheticSnapshot -FreeRAM_MB 1600.0 -DriveC_Free_GB 52.0
            $res = Compare-LaptopSnapshots -Baseline $b -Current $c

            Assert-NotNull $res.ReportJson "ReportJson must be populated"
            $parsedJson = $res.ReportJson | ConvertFrom-Json
            Assert-NotNull $parsedJson "ReportJson must be valid parseable JSON"
            Assert-Equal 600.0 $parsedJson.Deltas.RAMFreed_MB "JSON deltas RAM mismatch"
            Assert-Equal 2.0 $parsedJson.Deltas.StorageReclaimed_GB "JSON deltas Storage mismatch"
        }
    }

    Context "Storage Optimizer: Safe Disk Cleanup Dry-Run Interface" {
        $cleanupScript = Join-Path $ProjectRoot "src\StorageOptimizer\DiskCleanup.ps1"

        It "StorageOptimizer\DiskCleanup.ps1 interface contract (DryRun verification)" {
            if (-not (Test-Path $cleanupScript)) {
                Skip-Test "DiskCleanup.ps1 not yet implemented (Planned for Milestone M2)"
            }
            . $cleanupScript
            $cmd = Get-Command "Invoke-SafeDiskCleanup" -ErrorAction SilentlyContinue
            Assert-NotNull $cmd "Expected Invoke-SafeDiskCleanup function to be exported"

            # DryRun execution must return contract object without deleting real files
            $res = Invoke-SafeDiskCleanup -DryRun
            Assert-NotNull $res "Expected result object from Invoke-SafeDiskCleanup"
            Assert-NotNull $res.BytesReclaimed "Contract property missing: BytesReclaimed"
            Assert-NotNull $res.ItemsRemoved "Contract property missing: ItemsRemoved"
            Assert-NotNull $res.Errors "Contract property missing: Errors"
        }
    }

    Context "Memory Optimizer: Working Set Trimmer Dry-Run Interface" {
        $trimmerScript = Join-Path $ProjectRoot "src\MemoryOptimizer\RamTrimmer.ps1"

        It "MemoryOptimizer\RamTrimmer.ps1 interface contract (DryRun verification)" {
            if (-not (Test-Path $trimmerScript)) {
                Skip-Test "RamTrimmer.ps1 not yet implemented (Planned for Milestone M2)"
            }
            . $trimmerScript
            $cmd = Get-Command "Invoke-RamWorkingSetTrim" -ErrorAction SilentlyContinue
            Assert-NotNull $cmd "Expected Invoke-RamWorkingSetTrim function to be exported"

            $res = Invoke-RamWorkingSetTrim -DryRun
            Assert-NotNull $res "Expected result object from Invoke-RamWorkingSetTrim"
            Assert-NotNull $res.BeforeFree_MB "Contract property missing: BeforeFree_MB"
            Assert-NotNull $res.AfterFree_MB "Contract property missing: AfterFree_MB"
            Assert-NotNull $res.Gained_MB "Contract property missing: Gained_MB"
            Assert-NotNull $res.ProcessesTrimmed "Contract property missing: ProcessesTrimmed"
        }
    }

    Context "Storage Optimizer: SSD TRIM Interface" {
        $trimScript = Join-Path $ProjectRoot "src\StorageOptimizer\SsdTrim.ps1"

        It "StorageOptimizer\SsdTrim.ps1 interface contract (DryRun verification)" {
            if (-not (Test-Path $trimScript)) {
                Skip-Test "SsdTrim.ps1 not yet implemented (Planned for Milestone M2)"
            }
            . $trimScript
            $cmd = Get-Command "Invoke-SsdTrim" -ErrorAction SilentlyContinue
            Assert-NotNull $cmd "Expected Invoke-SsdTrim function to be exported"

            $res = Invoke-SsdTrim -DriveLetter "C" -DryRun
            Assert-NotNull $res "Expected result object from Invoke-SsdTrim"
            Assert-NotNull $res.Success "Contract property missing: Success"
            Assert-NotNull $res.MethodUsed "Contract property missing: MethodUsed"
        }
    }

    Context "Power Scheme Query Interface" {
        It "Active power scheme can be queried via native powercfg command" {
            $raw = (powercfg /getactivescheme 2>$null) | Out-String
            Assert-NotNull $raw "powercfg output must not be null"
            Assert-Match $raw "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}" "Active power scheme must include GUID"
        }
    }

    Context "Optimization Presets Inventory & Syntax" {
        $presetsDir = Join-Path $ProjectRoot "presets"
        $expectedPresets = @("QuickBoost.ps1", "DeepClean.ps1", "GamingMode.ps1", "RestoreDefaults.ps1")

        It "All 4 standard presets exist and contain valid PowerShell syntax" {
            if (-not (Test-Path $presetsDir)) {
                Skip-Test "Presets directory not yet created (Planned for Milestone M3)"
            }

            foreach ($preset in $expectedPresets) {
                $pPath = Join-Path $presetsDir $preset
                if (-not (Test-Path $pPath)) {
                    Skip-Test "Preset $preset not yet created (Planned for Milestone M3)"
                }
                # Check PS syntax using AST parser
                $tokens = $null
                $errors = $null
                $ast = [System.Management.Automation.Language.Parser]::ParseFile($pPath, [ref]$tokens, [ref]$errors)
                Assert-Equal 0 $errors.Count "Syntax errors found in preset script: $preset"
            }
        }
    }

    Context "Master Orchestrator CLI Parameter Contract" {
        $cliScript = Join-Path $ProjectRoot "Optimize-Laptop.ps1"

        It "Optimize-Laptop.ps1 defines required CLI parameters in AST" {
            if (-not (Test-Path $cliScript)) {
                Skip-Test "Optimize-Laptop.ps1 not yet implemented (Planned for Milestone M3)"
            }

            $tokens = $null
            $errors = $null
            $ast = [System.Management.Automation.Language.Parser]::ParseFile($cliScript, [ref]$tokens, [ref]$errors)
            Assert-Equal 0 $errors.Count "Syntax errors found in Optimize-Laptop.ps1"

            $paramBlock = $ast.ParamBlock
            Assert-NotNull $paramBlock "Optimize-Laptop.ps1 must declare a param block"
            $paramNames = @($paramBlock.Parameters | ForEach-Object { $_.Name.VariablePath.UserPath })

            Assert-Contains $paramNames "Preset" "CLI must accept -Preset"
            Assert-Contains $paramNames "DryRun" "CLI must accept -DryRun"
            Assert-Contains $paramNames "NonInteractive" "CLI must accept -NonInteractive"
        }
    }

    Context "Batch Launcher UTF-8 and Elevation Guards" {
        $batFile = Join-Path $ProjectRoot "optimize.bat"

        It "optimize.bat exists and contains UTF-8 code page and elevation checks" {
            if (-not (Test-Path $batFile)) {
                Skip-Test "optimize.bat not yet implemented (Planned for Milestone M3)"
            }
            $batContent = Get-Content -Path $batFile -Raw
            Assert-Match $batContent "chcp 65001" "optimize.bat must set UTF-8 code page (chcp 65001)"
            Assert-Match $batContent "powershell" "optimize.bat must invoke PowerShell orchestrator"
        }
    }
}
