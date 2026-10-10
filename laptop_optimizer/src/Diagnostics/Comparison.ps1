<#
.SYNOPSIS
    Metric comparison and acceptance criteria evaluation engine for Windows 11 Laptop Optimizer.
.DESCRIPTION
    Compares baseline and post-optimization system snapshots, computes memory,
    storage, process, and memory compression deltas, verifies acceptance criteria,
    and produces structured console tables, Markdown summaries, and JSON reports.
.NOTES
    Part of Milestone M1 (Diagnostics & Performance Profiling).
#>

function Format-LaptopComparisonTable {
    <#
    .SYNOPSIS
        Formats a side-by-side comparison table string for terminal display.
    .PARAMETER Comparison
        The comparison object returned by Compare-LaptopSnapshots.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [psobject]$Comparison
    )

    $b = $Comparison.Baseline
    $c = $Comparison.Current

    $ramSign = if ($Comparison.RAMGained_MB -ge 0) { "+" } else { "" }
    $ramPctSign = if ($Comparison.RAMFreed_PercentDelta -ge 0) { "+" } else { "" }
    $diskSign = if ($Comparison.StorageReclaimed_GB -ge 0) { "+" } else { "" }
    $procSign = if ($Comparison.ProcessDelta -ge 0) { "+" } else { "" }
    $mcSign = if ($Comparison.MemoryCompressionDelta_MB -ge 0) { "+" } else { "" }
    $pfSign = if ($Comparison.PageFileUsageDelta_MB -ge 0) { "+" } else { "" }

    $lines = [System.Collections.Generic.List[string]]::new()
    $lines.Add("================================================================================")
    $lines.Add("                   LAPTOP OPTIMIZER PERFORMANCE COMPARISON                      ")
    $lines.Add("================================================================================")
    $lines.Add(("{0,-28} {1,14} {2,14} {3,16}" -f "Metric", "Baseline", "Current", "Delta"))
    $lines.Add("--------------------------------------------------------------------------------")
    $lines.Add(("{0,-28} {1,14} {2,14} {3,16}" -f "Free RAM (MB)", ("{0:N1} MB" -f $b.FreeRAM_MB), ("{0:N1} MB" -f $c.FreeRAM_MB), ("{0}{1:N1} MB" -f $ramSign, $Comparison.RAMGained_MB)))
    $lines.Add(("{0,-28} {1,14} {2,14} {3,16}" -f "Free RAM (%)", ("{0:N1} %" -f $b.FreeRAM_Percent), ("{0:N1} %" -f $c.FreeRAM_Percent), ("{0}{1:N1} %" -f $ramPctSign, $Comparison.RAMFreed_PercentDelta)))
    $lines.Add(("{0,-28} {1,14} {2,14} {3,16}" -f "Drive C: Free Space", ("{0:N2} GB" -f $b.DriveC_Free_GB), ("{0:N2} GB" -f $c.DriveC_Free_GB), ("{0}{1:N2} GB" -f $diskSign, $Comparison.StorageReclaimed_GB)))
    $lines.Add(("{0,-28} {1,14} {2,14} {3,16}" -f "Memory Compression (WS)", ("{0:N1} MB" -f $b.MemoryCompression_MB), ("{0:N1} MB" -f $c.MemoryCompression_MB), ("{0}{1:N1} MB" -f $mcSign, $Comparison.MemoryCompressionDelta_MB)))
    $lines.Add(("{0,-28} {1,14} {2,14} {3,16}" -f "Pagefile Usage (MB)", ("{0:N1} MB" -f $b.PageFile_Usage_MB), ("{0:N1} MB" -f $c.PageFile_Usage_MB), ("{0}{1:N1} MB" -f $pfSign, $Comparison.PageFileUsageDelta_MB)))
    $lines.Add(("{0,-28} {1,14} {2,14} {3,16}" -f "Running Processes", ("{0}" -f $b.ProcessCount), ("{0}" -f $c.ProcessCount), ("{0}{1}" -f $procSign, $Comparison.ProcessDelta)))
    $lines.Add(("{0,-28} {1,14} {2,14} {3,16}" -f "Startup Items", ("{0}" -f $b.StartupItemsCount), ("{0}" -f $c.StartupItemsCount), ("{0}" -f ($c.StartupItemsCount - $b.StartupItemsCount))))
    $lines.Add("--------------------------------------------------------------------------------")
    $lines.Add("ACCEPTANCE CRITERIA VERIFICATION:")
    
    $crit1 = if ($Comparison.AcceptanceCriteria.TargetFreeRAM_Exceeds1500MB) { "[PASS]" } else { "[FAIL]" }
    $crit2 = if ($Comparison.AcceptanceCriteria.TargetStorageReclaimed_Exceeds1GB) { "[PASS]" } else { "[FAIL]" }
    $lines.Add(("{0} Target Free RAM > 1,500 MB (Measured: {1:N1} MB)" -f $crit1, $c.FreeRAM_MB))
    $lines.Add(("{0} Storage Reclaimed >= 1.00 GB (Measured: {1:N2} GB / {2:N1} MB)" -f $crit2, $Comparison.StorageReclaimed_GB, $Comparison.StorageReclaimed_MB))

    $overall = if ($Comparison.PassesAcceptanceCriteria) { "PASSED" } else { "PENDING / FAILED" }
    $lines.Add(("OVERALL EVALUATION: {0}" -f $overall))
    $lines.Add("================================================================================")

    return ($lines -join [System.Environment]::NewLine)
}

function Compare-LaptopSnapshots {
    <#
    .SYNOPSIS
        Compares baseline and post-optimization snapshots to measure improvements and verify acceptance criteria.
    .PARAMETER Baseline
        The pre-optimization system snapshot object.
    .PARAMETER Current
        The post-optimization system snapshot object.
    .PARAMETER Preset
        Name of the optimization preset executed (e.g., 'Quick Boost', 'Deep Clean').
    .PARAMETER ExecutionMode
        Execution mode ('Execute' or 'DryRun').
    .PARAMETER ReportId
        Optional identifier for the report.
    .OUTPUTS
        [PSCustomObject] conforming to PROJECT.md interface contract.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [psobject]$Baseline,

        [Parameter(Mandatory = $true, Position = 1)]
        [psobject]$Current,

        [Parameter(Mandatory = $false)]
        [string]$Preset = "Quick Boost",

        [Parameter(Mandatory = $false)]
        [string]$ExecutionMode = "Execute",

        [Parameter(Mandatory = $false)]
        [string]$ReportId = ""
    )

    if ([string]::IsNullOrEmpty($ReportId)) {
        $ReportId = "OPT-" + [System.DateTime]::Now.ToString("yyyyMMdd-HHmmss")
    }

    # 1. Delta Calculations
    $ramGainedMB = [math]::Round([double]($Current.FreeRAM_MB - $Baseline.FreeRAM_MB), 2)
    $storageReclaimedGB = [math]::Round([double]($Current.DriveC_Free_GB - $Baseline.DriveC_Free_GB), 2)
    $storageReclaimedMB = [math]::Round([double]($storageReclaimedGB * 1024.0), 2)

    $ramPctDelta = [math]::Round([double]($Current.FreeRAM_Percent - $Baseline.FreeRAM_Percent), 2)
    # Safe ProcessDelta calculation with Int32 boundary clamping
    $rawProcDelta = [double]($Current.ProcessCount - $Baseline.ProcessCount)
    $processDelta = if ([double]::IsNaN($rawProcDelta)) {
        0
    } elseif ($rawProcDelta -ge [double][int]::MaxValue) {
        [int]::MaxValue
    } elseif ($rawProcDelta -le [double][int]::MinValue) {
        [int]::MinValue
    } else {
        [int][math]::Round($rawProcDelta)
    }

    $memCompBaseline = if ($null -ne $Baseline.MemoryCompression_MB) { [double]$Baseline.MemoryCompression_MB } else { 0.0 }
    $memCompCurrent = if ($null -ne $Current.MemoryCompression_MB) { [double]$Current.MemoryCompression_MB } else { 0.0 }
    $memCompDeltaMB = [math]::Round([double]($memCompCurrent - $memCompBaseline), 2)

    $pfBaseline = if ($null -ne $Baseline.PageFile_Usage_MB) { [double]$Baseline.PageFile_Usage_MB } else { 0.0 }
    $pfCurrent = if ($null -ne $Current.PageFile_Usage_MB) { [double]$Current.PageFile_Usage_MB } else { 0.0 }
    $pfDeltaMB = [math]::Round([double]($pfCurrent - $pfBaseline), 2)

    # 2. Acceptance Criteria Evaluation
    $freeRamExceeds1500 = ($Current.FreeRAM_MB -gt 1500.0)
    $storageReclaimedExceeds1GB = ($storageReclaimedGB -ge 1.0)
    $overallPassed = ($freeRamExceeds1500 -and $storageReclaimedExceeds1GB)

    $acceptanceCriteria = [PSCustomObject]@{
        TargetFreeRAM_Exceeds1500MB       = $freeRamExceeds1500
        TargetStorageReclaimed_Exceeds1GB = $storageReclaimedExceeds1GB
        OverallPassed                     = $overallPassed
    }

    # 3. Construct Structured Markdown Report
    $nowStr = [System.DateTime]::Now.ToString("yyyy-MM-dd HH:mm:ss K")
    $ramSign = if ($ramGainedMB -ge 0) { "+" } else { "" }
    $ramPctSign = if ($ramPctDelta -ge 0) { "+" } else { "" }
    $storageSign = if ($storageReclaimedGB -ge 0) { "+" } else { "" }
    $mcSign = if ($memCompDeltaMB -ge 0) { "+" } else { "" }
    $pfSign = if ($pfDeltaMB -ge 0) { "+" } else { "" }
    $procSign = if ($processDelta -ge 0) { "+" } else { "" }
    $crit1Check = if ($freeRamExceeds1500) { "x" } else { " " }
    $crit2Check = if ($storageReclaimedExceeds1GB) { "x" } else { " " }
    $overallText = if ($overallPassed) { "PASSED" } else { "PENDING / FAILED" }

    $md = [System.Text.StringBuilder]::new()
    [void]$md.AppendLine("# Laptop Optimization Performance Comparison Report")
    [void]$md.AppendLine("")
    [void]$md.AppendLine("- **Report ID**: $ReportId")
    [void]$md.AppendLine("- **Generated At**: $nowStr")
    [void]$md.AppendLine("- **Optimization Preset**: $Preset")
    [void]$md.AppendLine("- **Execution Mode**: $ExecutionMode")
    [void]$md.AppendLine("- **Target OS**: $($Baseline.OS)")
    [void]$md.AppendLine("- **Active Power Scheme**: $($Current.ActivePowerScheme)")
    [void]$md.AppendLine("")
    [void]$md.AppendLine("## 1. Resource Metrics Comparison")
    [void]$md.AppendLine("")
    [void]$md.AppendLine("| Metric | Baseline | Current | Delta |")
    [void]$md.AppendLine("|---|---|---|---|")
    [void]$md.AppendLine(("| **Free Physical RAM** | {0:N1} MB | {1:N1} MB | {2}{3:N1} MB |" -f $Baseline.FreeRAM_MB, $Current.FreeRAM_MB, $ramSign, $ramGainedMB))
    [void]$md.AppendLine(("| **Free Physical RAM %** | {0:N1}% | {1:N1}% | {2}{3:N1}% |" -f $Baseline.FreeRAM_Percent, $Current.FreeRAM_Percent, $ramPctSign, $ramPctDelta))
    [void]$md.AppendLine(("| **Drive C: Free Space** | {0:N2} GB | {1:N2} GB | {2}{3:N2} GB |" -f $Baseline.DriveC_Free_GB, $Current.DriveC_Free_GB, $storageSign, $storageReclaimedGB))
    [void]$md.AppendLine(("| **Memory Compression (WS)** | {0:N1} MB | {1:N1} MB | {2}{3:N1} MB |" -f $memCompBaseline, $memCompCurrent, $mcSign, $memCompDeltaMB))
    [void]$md.AppendLine(("| **Pagefile Usage** | {0:N1} MB | {1:N1} MB | {2}{3:N1} MB |" -f $pfBaseline, $pfCurrent, $pfSign, $pfDeltaMB))
    [void]$md.AppendLine(("| **Active Processes** | {0} | {1} | {2}{3} |" -f $Baseline.ProcessCount, $Current.ProcessCount, $procSign, $processDelta))
    [void]$md.AppendLine(("| **Startup Items** | {0} | {1} | {2} |" -f $Baseline.StartupItemsCount, $Current.StartupItemsCount, ($Current.StartupItemsCount - $Baseline.StartupItemsCount)))
    [void]$md.AppendLine("")
    [void]$md.AppendLine("## 2. Acceptance Criteria Evaluation")
    [void]$md.AppendLine("")
    [void]$md.AppendLine(("- [{0}] **Target Free RAM > 1,500 MB**: Current free RAM is {1:N1} MB (Target: > 1500 MB)" -f $crit1Check, $Current.FreeRAM_MB))
    [void]$md.AppendLine(("- [{0}] **Target Reclaimed Storage >= 1.00 GB**: Reclaimed {1:N2} GB / {2:N1} MB (Target: >= 1.00 GB)" -f $crit2Check, $storageReclaimedGB, $storageReclaimedMB))
    [void]$md.AppendLine("")
    [void]$md.AppendLine(("- **Overall Status**: **{0}**" -f $overallText))
    [void]$md.AppendLine("")

    $reportMarkdown = $md.ToString()

    # 4. Construct Structured JSON Object
    $reportJsonObject = [PSCustomObject]@{
        ReportMetadata = [PSCustomObject]@{
            ReportId           = $ReportId
            GeneratedAt        = [System.DateTime]::Now.ToString("o")
            OptimizationPreset = $Preset
            ExecutionMode      = $ExecutionMode
            IsElevated         = if ($null -ne $Current.IsElevated) { [bool]$Current.IsElevated } else { $false }
        }
        SystemProfile = [PSCustomObject]@{
            Hostname            = [System.Environment]::MachineName
            OSCaption           = $Baseline.OS
            OSBuild             = if ($Baseline.PSObject.Properties['OSBuild']) { $Baseline.OSBuild } else { "26200" }
            CPUModel            = if ($Baseline.PSObject.Properties['CPU_Name']) { $Baseline.CPU_Name } else { "Intel(R) N100" }
            CoreCount           = if ($Baseline.PSObject.Properties['CPU_Cores']) { [int]$Baseline.CPU_Cores } else { 4 }
            TotalPhysicalRAM_MB = if ($Baseline.PSObject.Properties['TotalRAM_MB']) { [double]$Baseline.TotalRAM_MB } else { [double]($Baseline.TotalRAM_GB * 1024.0) }
            PowerScheme         = $Current.ActivePowerScheme
        }
        Baseline = [PSCustomObject]@{
            Timestamp = if ($Baseline.Timestamp) { $Baseline.Timestamp.ToString("o") } else { "" }
            Memory = [PSCustomObject]@{
                FreePhysicalRAM_MB      = $Baseline.FreeRAM_MB
                FreePhysicalRAM_Percent = $Baseline.FreeRAM_Percent
                TotalVisibleRAM_MB      = if ($Baseline.PSObject.Properties['TotalRAM_MB']) { $Baseline.TotalRAM_MB } else { [double]($Baseline.TotalRAM_GB * 1024.0) }
                MemoryCompression_WS_MB = $memCompBaseline
            }
            Storage = [PSCustomObject]@{
                DriveLetter        = "C:"
                TotalSize_GB       = $Baseline.DriveC_Total_GB
                FreeSpace_GB       = $Baseline.DriveC_Free_GB
                FreeSpace_Percent  = if ($Baseline.PSObject.Properties['DriveC_Free_Percent'] -and $null -ne $Baseline.DriveC_Free_Percent) {
                    [double]$Baseline.DriveC_Free_Percent
                } elseif ($Baseline.PSObject.Properties['DriveC_Total_GB'] -and $null -ne $Baseline.DriveC_Total_GB -and [double]$Baseline.DriveC_Total_GB -gt 0) {
                    $bFree = if ($Baseline.PSObject.Properties['DriveC_Free_GB'] -and $null -ne $Baseline.DriveC_Free_GB) { [double]$Baseline.DriveC_Free_GB } else { 0.0 }
                    [math]::Round(($bFree / [double]$Baseline.DriveC_Total_GB) * 100.0, 1)
                } else {
                    0.0
                }
            }
            Paging = [PSCustomObject]@{
                AllocatedSize_MB = $Baseline.PageFile_Allocated_MB
                CurrentUsage_MB  = $Baseline.PageFile_Usage_MB
            }
            Processes = [PSCustomObject]@{
                TotalCount   = $Baseline.ProcessCount
                TopConsumers = $Baseline.TopProcesses
            }
        }
        PostOptimization = [PSCustomObject]@{
            Timestamp = if ($Current.Timestamp) { $Current.Timestamp.ToString("o") } else { "" }
            Memory = [PSCustomObject]@{
                FreePhysicalRAM_MB      = $Current.FreeRAM_MB
                FreePhysicalRAM_Percent = $Current.FreeRAM_Percent
                TotalVisibleRAM_MB      = if ($Current.PSObject.Properties['TotalRAM_MB']) { $Current.TotalRAM_MB } else { [double]($Current.TotalRAM_GB * 1024.0) }
                MemoryCompression_WS_MB = $memCompCurrent
            }
            Storage = [PSCustomObject]@{
                DriveLetter        = "C:"
                TotalSize_GB       = $Current.DriveC_Total_GB
                FreeSpace_GB       = $Current.DriveC_Free_GB
                FreeSpace_Percent  = if ($Current.PSObject.Properties['DriveC_Free_Percent'] -and $null -ne $Current.DriveC_Free_Percent) {
                    [double]$Current.DriveC_Free_Percent
                } elseif ($Current.PSObject.Properties['DriveC_Total_GB'] -and $null -ne $Current.DriveC_Total_GB -and [double]$Current.DriveC_Total_GB -gt 0) {
                    $cFree = if ($Current.PSObject.Properties['DriveC_Free_GB'] -and $null -ne $Current.DriveC_Free_GB) { [double]$Current.DriveC_Free_GB } else { 0.0 }
                    [math]::Round(($cFree / [double]$Current.DriveC_Total_GB) * 100.0, 1)
                } else {
                    0.0
                }
            }
            Paging = [PSCustomObject]@{
                AllocatedSize_MB = $Current.PageFile_Allocated_MB
                CurrentUsage_MB  = $Current.PageFile_Usage_MB
            }
            Processes = [PSCustomObject]@{
                TotalCount   = $Current.ProcessCount
                TopConsumers = $Current.TopProcesses
            }
        }
        Deltas = [PSCustomObject]@{
            RAMFreed_MB                = $ramGainedMB
            RAMFreed_PercentDelta      = $ramPctDelta
            StorageReclaimed_GB        = $storageReclaimedGB
            StorageReclaimed_MB        = $storageReclaimedMB
            ProcessCountDelta          = $processDelta
            PageFileUsageDelta_MB      = $pfDeltaMB
            MemoryCompressionDelta_MB  = $memCompDeltaMB
        }
        AcceptanceCriteriaVerification = [PSCustomObject]@{
            TargetFreeRAM_Exceeds1500MB       = $freeRamExceeds1500
            TargetStorageReclaimed_Exceeds1GB = $storageReclaimedExceeds1GB
            OverallPassed                     = $overallPassed
        }
    }

    $reportJson = $reportJsonObject | ConvertTo-Json -Depth 10

    # 5. Build Return Object conforming to PROJECT.md interface contract
    $result = [PSCustomObject]@{
        # Core Contract Properties (PROJECT.md)
        RAMGained_MB               = $ramGainedMB
        StorageReclaimed_GB        = $storageReclaimedGB
        ProcessDelta               = $processDelta
        PassesAcceptanceCriteria   = $overallPassed
        ReportMarkdown             = $reportMarkdown

        # Extended Properties
        StorageReclaimed_MB        = $storageReclaimedMB
        RAMFreed_PercentDelta      = $ramPctDelta
        MemoryCompressionDelta_MB  = $memCompDeltaMB
        PageFileUsageDelta_MB      = $pfDeltaMB
        AcceptanceCriteria         = $acceptanceCriteria
        ReportJson                 = $reportJson
        ReportJsonObject           = $reportJsonObject
        Baseline                   = $Baseline
        Current                    = $Current
        ReportTable                = ""
    }

    # Attach formatted table
    $tableStr = Format-LaptopComparisonTable -Comparison $result
    $result.ReportTable = $tableStr

    return $result
}
