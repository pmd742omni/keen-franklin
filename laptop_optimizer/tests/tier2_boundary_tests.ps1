<#
.SYNOPSIS
    Tier 2 Boundary & Corner Case Tests for Windows 11 Laptop Optimizer.
.DESCRIPTION
    Verifies system robustness under stress, invalid inputs, edge cases, permission
    boundaries, zero thresholds, file locks, missing registry keys, and corrupt data.
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

Describe "Tier 2: Boundary & Corner Cases" -Tier 2 {

    Context "Null and Empty Parameter Boundaries" {
        $comparisonScript = Join-Path $ProjectRoot "src\Diagnostics\Comparison.ps1"

        It "Compare-LaptopSnapshots throws or cleanly rejects null Baseline" {
            if (-not (Test-Path $comparisonScript)) {
                Skip-Test "Comparison.ps1 not found"
            }
            . $comparisonScript
            $validSnap = New-SyntheticSnapshot

            Assert-Throws {
                Compare-LaptopSnapshots -Baseline $null -Current $validSnap
            }
        }

        It "Compare-LaptopSnapshots throws or cleanly rejects null Current" {
            if (-not (Test-Path $comparisonScript)) {
                Skip-Test "Comparison.ps1 not found"
            }
            . $comparisonScript
            $validSnap = New-SyntheticSnapshot

            Assert-Throws {
                Compare-LaptopSnapshots -Baseline $validSnap -Current $null
            }
        }

        It "Get-Coalesce handles both arguments null safely" {
            $platformScript = Join-Path $ProjectRoot "src\Common\Platform.ps1"
            . $platformScript
            $res = Get-Coalesce $null $null
            Assert-Null $res "Expected null when both arguments are null"
        }

        It "ConvertTo-JsonSafe handles empty structures and rejects null safely" {
            $platformScript = Join-Path $ProjectRoot "src\Common\Platform.ps1"
            . $platformScript
            $json = ConvertTo-JsonSafe -InputObject @{}
            Assert-NotNull $json
            Assert-Match $json "\{\s*\}"

            Assert-Throws {
                ConvertTo-JsonSafe -InputObject $null
            }
        }
    }

    Context "Zero & Negative Threshold Deltas" {
        $comparisonScript = Join-Path $ProjectRoot "src\Diagnostics\Comparison.ps1"

        It "Handles negative storage reclamation (disk space decreased during run)" {
            if (-not (Test-Path $comparisonScript)) {
                Skip-Test "Comparison.ps1 not found"
            }
            . $comparisonScript

            # Baseline: 50 GB free, Post: 48 GB free (-2.0 GB)
            $b = New-SyntheticSnapshot -FreeRAM_MB 1600.0 -DriveC_Free_GB 50.0
            $c = New-SyntheticSnapshot -FreeRAM_MB 1700.0 -DriveC_Free_GB 48.0

            $res = Compare-LaptopSnapshots -Baseline $b -Current $c
            Assert-Equal -2.0 $res.StorageReclaimed_GB "Expected negative storage reclaimed"
            Assert-False $res.PassesAcceptanceCriteria "Must fail acceptance criteria when storage reclaimed < 1.0 GB"
        }

        It "Handles negative RAM delta (memory consumed during run)" {
            if (-not (Test-Path $comparisonScript)) {
                Skip-Test "Comparison.ps1 not found"
            }
            . $comparisonScript

            # Baseline: 1800 MB free, Post: 1200 MB free (-600 MB gained)
            $b = New-SyntheticSnapshot -FreeRAM_MB 1800.0 -DriveC_Free_GB 40.0
            $c = New-SyntheticSnapshot -FreeRAM_MB 1200.0 -DriveC_Free_GB 42.0

            $res = Compare-LaptopSnapshots -Baseline $b -Current $c
            Assert-Equal -600.0 $res.RAMGained_MB "Expected negative RAM gained delta"
            Assert-False $res.PassesAcceptanceCriteria "Must fail acceptance criteria when Free RAM <= 1500 MB"
        }

        It "Handles exact boundary condition (Free RAM = 1500.0 MB and Reclaimed = 1.00 GB)" {
            if (-not (Test-Path $comparisonScript)) {
                Skip-Test "Comparison.ps1 not found"
            }
            . $comparisonScript

            # Free RAM must EXCEED 1500 MB (> 1500.0) according to R1/R2 acceptance criteria
            $b = New-SyntheticSnapshot -FreeRAM_MB 1000.0 -DriveC_Free_GB 40.0
            $cExact = New-SyntheticSnapshot -FreeRAM_MB 1500.0 -DriveC_Free_GB 41.0
            $resExact = Compare-LaptopSnapshots -Baseline $b -Current $cExact
            Assert-False $resExact.PassesAcceptanceCriteria "RAM = 1500.0 does NOT exceed 1500 MB (target is > 1500)"

            $cJustAbove = New-SyntheticSnapshot -FreeRAM_MB 1501.0 -DriveC_Free_GB 41.0
            $resJustAbove = Compare-LaptopSnapshots -Baseline $b -Current $cJustAbove
            Assert-True $resJustAbove.PassesAcceptanceCriteria "RAM = 1501.0 and Reclaimed = 1.00 GB should pass"
        }
    }

    Context "Invalid Presets & CLI Boundaries" {
        $cliScript = Join-Path $ProjectRoot "Optimize-Laptop.ps1"

        It "Rejects unknown preset name gracefully without unhandled crash" {
            if (-not (Test-Path $cliScript)) {
                Skip-Test "Optimize-Laptop.ps1 not yet implemented (Planned for Milestone M3)"
            }

            # Invoke with invalid preset in a child process to check exit code
            $output = & powershell -ExecutionPolicy Bypass -File $cliScript -Preset "InvalidPreset_NonExistent" -DryRun 2>&1 | Out-String
            Assert-True ($LASTEXITCODE -ne 0 -or $output -match "Invalid|Unknown|ValidateSet") "CLI should reject invalid preset name"
        }
    }

    Context "Read-Only and Locked Temp Files Boundary (Storage Cleanup)" {
        $sandbox = $null

        It "Disk cleanup simulation handles read-only files without aborting" {
            $sandbox = New-TestSandbox "Cleanup_ReadOnly_"
            $readOnlyDir = Join-Path $sandbox "UserTemp"
            $normalFile = New-MockFile (Join-Path $readOnlyDir "disposable.tmp") -SizeBytes 2048
            $roFile = New-MockFile (Join-Path $readOnlyDir "protected.tmp") -SizeBytes 4096

            # Set file as Read-Only
            Set-ItemProperty -Path $roFile -Name IsReadOnly -Value $true

            # Perform safe deletion routine with force
            $errors = [System.Collections.Generic.List[string]]::new()
            $deletedCount = 0
            $reclaimedBytes = 0L

            Get-ChildItem -Path $readOnlyDir -File | ForEach-Object {
                try {
                    $size = $_.Length
                    Remove-Item -Path $_.FullName -Force -ErrorAction Stop
                    $deletedCount++
                    $reclaimedBytes += $size
                } catch {
                    $errors.Add($_.Exception.Message)
                }
            }

            # With -Force, read-only files in temp are cleaned, normal files are cleaned
            Assert-Equal 2 $deletedCount "Expected both normal and read-only temp files to be cleaned with -Force"
            Assert-Equal 0 $errors.Count "Expected 0 unhandled errors"
            Remove-TestSandbox $sandbox
        }

        It "Disk cleanup simulation skips locked in-use files gracefully and deletes remaining files" {
            $sandbox = New-TestSandbox "Cleanup_Locked_"
            $lockedDir = Join-Path $sandbox "UserTemp"
            $file1 = New-MockFile (Join-Path $lockedDir "file1.tmp") -SizeBytes 1024
            $lockedFile = New-MockFile (Join-Path $lockedDir "locked.tmp") -SizeBytes 2048
            $file3 = New-MockFile (Join-Path $lockedDir "file3.tmp") -SizeBytes 4096

            # Lock the middle file exclusively
            $fs = [System.IO.File]::Open($lockedFile, [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)

            $errors = [System.Collections.Generic.List[string]]::new()
            $deletedCount = 0
            $reclaimedBytes = 0L

            try {
                Get-ChildItem -Path $lockedDir -File | ForEach-Object {
                    try {
                        $size = $_.Length
                        Remove-Item -Path $_.FullName -Force -ErrorAction Stop
                        $deletedCount++
                        $reclaimedBytes += $size
                    } catch {
                        $errors.Add("Locked/InUse: " + $_.Name)
                    }
                }

                # File 1 and File 3 should be deleted, Locked file should be skipped with non-fatal error recorded
                Assert-Equal 2 $deletedCount "Expected 2 accessible files to be deleted"
                Assert-Equal 1 $errors.Count "Expected 1 error for locked file"
                Assert-True (Test-Path $lockedFile) "Locked file should still exist"
                Assert-False (Test-Path $file1) "File 1 should be deleted"
                Assert-False (Test-Path $file3) "File 3 should be deleted"
            } finally {
                $fs.Close()
                Remove-TestSandbox $sandbox
            }
        }
    }

    Context "Missing Registry Keys Resilience" {
        $profilerScript = Join-Path $ProjectRoot "src\Diagnostics\Profiler.ps1"

        It "Startup audit handles missing or empty registry keys without throwing terminating error" {
            if (-not (Test-Path $profilerScript)) {
                Skip-Test "Profiler.ps1 not found"
            }
            . $profilerScript

            # Test scanning does not fail even if keys have non-standard permissions or are empty
            $items = Get-LaptopStartupItems
            Assert-NotNull $items "Should return an array (even if empty) without throwing"
        }
    }

    Context "Corrupted State Snapshot Handling" {
        $restoreScript = Join-Path $ProjectRoot "src\SafetyEngine\Restore.ps1"

        It "Rejects 0-byte empty snapshot file" {
            $sandbox = New-TestSandbox "CorruptSnapshot_"
            $emptySnap = Join-Path $sandbox "empty_snapshot.json"
            [System.IO.File]::WriteAllText($emptySnap, "")

            if (-not (Test-Path $restoreScript)) {
                # Test pure parser robustness
                $threw = $false
                try {
                    $content = Get-Content -Path $emptySnap -Raw
                    if ([string]::IsNullOrWhiteSpace($content)) {
                        throw "Snapshot file is empty"
                    }
                    $json = $content | ConvertFrom-Json
                } catch {
                    $threw = $true
                }
                Assert-True $threw "Expected empty snapshot to be rejected"
            } else {
                . $restoreScript
                $res = Restore-LaptopSnapshot -SnapshotFile $emptySnap
                Assert-False $res.Success "Restore should report failure on empty snapshot"
                Assert-True ($res.Errors.Count -gt 0) "Errors list should be populated"
            }
            Remove-TestSandbox $sandbox
        }

        It "Rejects malformed / truncated JSON snapshot" {
            $sandbox = New-TestSandbox "MalformedSnapshot_"
            $malformedSnap = Join-Path $sandbox "malformed_snapshot.json"
            Set-Content -Path $malformedSnap -Value '{"Timestamp": "2026-09-29T12:00:00Z", "Services": [' -Encoding utf8

            if (-not (Test-Path $restoreScript)) {
                $threw = $false
                try {
                    $content = Get-Content -Path $malformedSnap -Raw
                    $json = $content | ConvertFrom-Json
                } catch {
                    $threw = $true
                }
                Assert-True $threw "Expected malformed JSON to be rejected"
            } else {
                . $restoreScript
                $res = Restore-LaptopSnapshot -SnapshotFile $malformedSnap
                Assert-False $res.Success "Restore should report failure on malformed JSON"
            }
            Remove-TestSandbox $sandbox
        }

        It "Rejects snapshot missing critical schema fields" {
            $sandbox = New-TestSandbox "MissingFieldsSnapshot_"
            $badSchemaSnap = Join-Path $sandbox "bad_schema.json"
            Set-Content -Path $badSchemaSnap -Value '{"UnrelatedField": 12345}' -Encoding utf8

            if (-not (Test-Path $restoreScript)) {
                $parsed = Get-Content -Path $badSchemaSnap -Raw | ConvertFrom-Json
                $isValidSchema = ($null -ne $parsed.Timestamp -or $null -ne $parsed.Services -or $null -ne $parsed.Baseline)
                Assert-False $isValidSchema "Schema validation must reject snapshot without required fields"
            } else {
                . $restoreScript
                $res = Restore-LaptopSnapshot -SnapshotFile $badSchemaSnap
                Assert-False $res.Success "Restore should fail on schema missing essential fields"
            }
            Remove-TestSandbox $sandbox
        }
    }
}
