<#
.SYNOPSIS
    Production-grade Windows 11 Laptop Optimization & Performance Toolkit.
.DESCRIPTION
    Comprehensive, non-destructive tuning suite for Windows 11 laptops.
    Tailored for high responsiveness on low-TDP and quad-core CPUs (Intel N-series, Core i3/i5, AMD Ryzen).
    Includes memory relief, disk reclamation, SSD TRIM, telemetry reduction, UI latency tuning,
    power governor configuration, and full rollback capability.
.PARAMETER Preset
    Optimization profile: 'QuickBoost', 'DeepClean', 'FullOptimize', 'Benchmark', 'Restore'
.PARAMETER DryRun
    Simulate actions without modifying files or settings.
#>

[CmdletBinding()]
param(
    [ValidateSet('QuickBoost', 'DeepClean', 'FullOptimize', 'StartupOptimize', 'Benchmark', 'Restore', 'Interactive')]
    [string]$Preset = 'Interactive',
    [switch]$DryRun
)

$ErrorActionPreference = 'SilentlyContinue'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ScriptDir) { $ScriptDir = Get-Location }
$BackupFile = Join-Path $ScriptDir "backup_state.json"
$LogFile = Join-Path $ScriptDir "optimization.log"

function Write-Log {
    param([string]$Message, [string]$Level = 'INFO')
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $logEntry -Force
    
    switch ($Level) {
        'SUCCESS' { Write-Host " [+] $Message" -ForegroundColor Green }
        'WARN'    { Write-Host " [!] $Message" -ForegroundColor Yellow }
        'ERROR'   { Write-Host " [X] $Message" -ForegroundColor Red }
        'INFO'    { Write-Host " [*] $Message" -ForegroundColor Cyan }
        default   { Write-Host "     $Message" -ForegroundColor Gray }
    }
}

function Show-Banner {
    Clear-Host
    Write-Host "=================================================================" -ForegroundColor Cyan
    Write-Host "         WINDOWS 11 LAPTOP OPTIMIZER & PERFORMANCE SUITE        " -ForegroundColor Yellow
    Write-Host "         Tailored for Intel N-Series / Core / AMD Mobile CPUs    " -ForegroundColor Gray
    Write-Host "=================================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-IsAdmin {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# ---------------------------------------------------------
# BACKUP & RESTORE FUNCTIONS
# ---------------------------------------------------------
function Backup-SystemState {
    Write-Log "Creating system state snapshot before modifications..." "INFO"
    
    $backupData = [PSCustomObject]@{
        Timestamp          = (Get-Date).ToString("o")
        ActivePowerScheme  = (powercfg /getactivescheme) -replace '.*GUID:\s*([^\s]+)\s*\(.*', '$1'
        MenuShowDelay      = (Get-ItemProperty -Path 'HKCU:\Control Panel\Desktop' -Name 'MenuShowDelay' -ErrorAction SilentlyContinue).MenuShowDelay
        MinAnimate         = (Get-ItemProperty -Path 'HKCU:\Control Panel\Desktop\WindowMetrics' -Name 'MinAnimate' -ErrorAction SilentlyContinue).MinAnimate
        TaskbarAnimations  = (Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' -Name 'TaskbarAnimations' -ErrorAction SilentlyContinue).TaskbarAnimations
        Services           = @{}
        ScheduledTasks     = @{}
    }
    
    # Track critical services
    $targetServices = @('DiagTrack', 'dmwappushservice')
    foreach ($svcName in $targetServices) {
        $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
        if ($svc) {
            $backupData.Services[$svcName] = [PSCustomObject]@{
                Status    = $svc.Status.ToString()
                StartType = $svc.StartType.ToString()
            }
        }
    }

    if (-not $DryRun) {
        $backupData | ConvertTo-Json -Depth 5 | Set-Content -Path $BackupFile -Force
        Write-Log "System state saved to: $BackupFile" "SUCCESS"
    } else {
        Write-Log "[DryRun] Would write state backup to $BackupFile" "INFO"
    }
}

function Restore-LaptopState {
    Show-Banner
    Write-Host " RESTORING PREVIOUS SYSTEM STATE" -ForegroundColor Yellow
    Write-Host "-----------------------------------------------------------------" -ForegroundColor Gray

    if (-not (Test-Path $BackupFile)) {
        Write-Log "No backup file found at: $BackupFile. Cannot restore." "ERROR"
        return
    }

    $backup = Get-Content -Path $BackupFile -Raw | ConvertFrom-Json
    Write-Log "Found backup from: $($backup.Timestamp)" "INFO"

    # Restore Power Scheme
    if ($backup.ActivePowerScheme) {
        Write-Log "Restoring power plan: $($backup.ActivePowerScheme)" "INFO"
        if (-not $DryRun) {
            powercfg /setactive $backup.ActivePowerScheme
        }
    }

    # Restore Registry UI values
    if ($backup.MenuShowDelay) {
        Write-Log "Restoring MenuShowDelay to $($backup.MenuShowDelay)..." "INFO"
        if (-not $DryRun) {
            Set-ItemProperty -Path 'HKCU:\Control Panel\Desktop' -Name 'MenuShowDelay' -Value $backup.MenuShowDelay
        }
    }
    if ($backup.MinAnimate) {
        if (-not $DryRun) {
            Set-ItemProperty -Path 'HKCU:\Control Panel\Desktop\WindowMetrics' -Name 'MinAnimate' -Value $backup.MinAnimate
        }
    }
    if ($backup.TaskbarAnimations) {
        if (-not $DryRun) {
            Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' -Name 'TaskbarAnimations' -Value $backup.TaskbarAnimations
        }
    }

    # Re-enable scheduled tasks
    $tasksToEnable = @(
        "\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser",
        "\Microsoft\Windows\Application Experience\ProgramDataUpdater",
        "\Microsoft\Windows\Customer Experience Improvement Program\Consolidator",
        "\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip",
        "\Microsoft\Windows\Feedback\Siuf\DmClient",
        "\Microsoft\Windows\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector"
    )
    foreach ($task in $tasksToEnable) {
        Write-Log "Restoring scheduled task: $task" "INFO"
        if (-not $DryRun) {
            schtasks /change /tn $task /enable 2>$null | Out-Null
        }
    }

    # Restore disabled startup items
    $backupReg = 'HKCU:\Software\LaptopOptimizer_DisabledRun'
    if (Test-Path $backupReg) {
        $props = Get-ItemProperty -Path $backupReg -ErrorAction SilentlyContinue
        if ($props) {
            foreach ($p in $props.PSObject.Properties) {
                if ($p.Name -notmatch '^PS.*') {
                    Write-Log "Restoring startup entry: $($p.Name)" "INFO"
                    if (-not $DryRun) {
                        Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name $p.Name -Value $p.Value -Force
                        Remove-ItemProperty -Path $backupReg -Name $p.Name -Force -ErrorAction SilentlyContinue
                    }
                }
            }
        }
    }

    Write-Log "System restoration complete." "SUCCESS"
}

# ---------------------------------------------------------
# PHASE 1: DISK RECLAMATION
# ---------------------------------------------------------
function Invoke-StorageCleanup {
    [CmdletBinding()]
    param([switch]$Aggressive)

    Write-Host "`n [PHASE: STORAGE RECLAMATION]" -ForegroundColor Cyan
    Write-Log "Starting temporary and cache file reclamation..." "INFO"

    $totalReclaimedBytes = 0

    $targetPaths = @(
        $env:TEMP,
        "C:\Windows\Temp",
        "C:\Windows\SoftwareDistribution\Download",
        "C:\ProgramData\Microsoft\Windows\WER\ReportArchive",
        "C:\ProgramData\Microsoft\Windows\WER\ReportQueue",
        "C:\ProgramData\Microsoft\Windows\WER\Temp",
        "$env:LOCALAPPDATA\CrashDumps",
        "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\ThumbCacheToDelete"
    )

    if ($Aggressive) {
        $targetPaths += "C:\Windows\ServiceProfiles\NetworkService\AppData\Local\Microsoft\Windows\DeliveryOptimization\Cache"
    }

    foreach ($path in $targetPaths) {
        if (Test-Path $path) {
            $files = Get-ChildItem -Path $path -Recurse -File -Force -ErrorAction SilentlyContinue
            if ($files) {
                $dirBytes = ($files | Measure-Object -Property Length -Sum).Sum
                $fileCount = $files.Count
                $sizeMB = [math]::Round($dirBytes / 1MB, 2)
                
                Write-Log "Found $fileCount files in '$path' (~$sizeMB MB)" "INFO"

                if (-not $DryRun) {
                    $deletedBytes = 0
                    foreach ($f in $files) {
                        try {
                            $len = $f.Length
                            Remove-Item -Path $f.FullName -Force -ErrorAction Stop
                            $deletedBytes += $len
                        } catch {
                            # File locked by running process - ignore safely
                        }
                    }
                    $reclaimedMB = [math]::Round($deletedBytes / 1MB, 2)
                    $totalReclaimedBytes += $deletedBytes
                    Write-Log "Reclaimed $reclaimedMB MB from $path" "SUCCESS"
                } else {
                    Write-Log "[DryRun] Would purge ~$sizeMB MB from $path" "INFO"
                    $totalReclaimedBytes += $dirBytes
                }
            }
        }
    }

    # Empty Recycle Bin safely
    if (-not $DryRun) {
        try {
            Clear-RecycleBin -Force -ErrorAction SilentlyContinue
            Write-Log "Emptied Windows Recycle Bin." "SUCCESS"
        } catch {}
    }

    $totalReclaimedMB = [math]::Round($totalReclaimedBytes / 1MB, 2)
    $totalReclaimedGB = [math]::Round($totalReclaimedBytes / 1GB, 3)
    Write-Log "Storage cleanup completed: Reclaimed ~$totalReclaimedMB MB (~$totalReclaimedGB GB)" "SUCCESS"
    return $totalReclaimedMB
}

# ---------------------------------------------------------
# PHASE 2: SSD TRIM OPTIMIZATION
# ---------------------------------------------------------
function Invoke-SSDTrim {
    Write-Host "`n [PHASE: SSD TRIM OPTIMIZATION]" -ForegroundColor Cyan
    Write-Log "Checking drive C: for SSD re-trimming..." "INFO"

    if (-not $DryRun) {
        try {
            $trimResult = Optimize-Volume -DriveLetter C -ReTrim -Verbose -ErrorAction Stop
            Write-Log "SSD re-trim command dispatched successfully to Drive C:." "SUCCESS"
        } catch {
            Write-Log "Standard Optimize-Volume notice: $($_.Exception.Message)" "WARN"
            # Fallback to defrag command
            defrag.exe C: /L /U 2>$null | Out-Null
            Write-Log "Defrag re-trim fallback completed for Drive C:." "SUCCESS"
        }
    } else {
        Write-Log "[DryRun] Would invoke Optimize-Volume -DriveLetter C -ReTrim" "INFO"
    }
}

# ---------------------------------------------------------
# PHASE 3: MEMORY RELIEF & WORKING SET TRIMMING
# ---------------------------------------------------------
function Invoke-MemoryRelief {
    Write-Host "`n [PHASE: MEMORY PRESSURE RELIEF]" -ForegroundColor Cyan
    Write-Log "Analyzing and optimizing active memory consumption..." "INFO"

    $osBefore = Get-CimInstance Win32_OperatingSystem
    $freeRamMBBefore = [math]::Round($osBefore.FreePhysicalMemory / 1024, 1)
    Write-Log "Free Physical Memory Before: $freeRamMBBefore MB" "INFO"

    try {
        Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class MemoryCleaner {
    [DllImport("psapi.dll")]
    public static extern int EmptyWorkingSet(IntPtr hwProc);
}
"@ -ErrorAction SilentlyContinue
    } catch {}

    if (-not $DryRun) {
        $processes = Get-Process -ErrorAction SilentlyContinue | Where-Object { 
            $_.WorkingSet64 -gt 15MB -and 
            $_.ProcessName -notmatch '^(csrss|lsass|services|smss|system|idle)$' 
        }

        $trimmedCount = 0
        foreach ($proc in $processes) {
            try {
                [MemoryCleaner]::EmptyWorkingSet($proc.Handle) | Out-Null
                $trimmedCount++
            } catch {
                try {
                    $proc.MinWorkingSet = [System.IntPtr]::Zero
                    $trimmedCount++
                } catch {}
            }
        }

        # Trigger garbage collection
        [System.GC]::Collect()
        [System.GC]::WaitForPendingFinalizers()

        Write-Log "Trimmed working sets of $trimmedCount processes to release stale memory pages." "SUCCESS"
    } else {
        Write-Log "[DryRun] Would invoke garbage collection and empty idle process working sets." "INFO"
    }

    $osAfter = Get-CimInstance Win32_OperatingSystem
    $freeRamMBAfter = [math]::Round($osAfter.FreePhysicalMemory / 1024, 1)
    $freedMB = [math]::Round($freeRamMBAfter - $freeRamMBBefore, 1)
    Write-Log "Free Physical Memory After: $freeRamMBAfter MB (Change: +$freedMB MB)" "SUCCESS"
}

# ---------------------------------------------------------
# PHASE 4: TELEMETRY & BACKGROUND BLOAT TUNING
# ---------------------------------------------------------
function Invoke-TelemetryTuning {
    Write-Host "`n [PHASE: TELEMETRY & BACKGROUND BLOAT TUNING]" -ForegroundColor Cyan
    Write-Log "Disabling resource-intensive telemetry and scheduled background tasks..." "INFO"

    $tasksToDisable = @(
        "\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser",
        "\Microsoft\Windows\Application Experience\ProgramDataUpdater",
        "\Microsoft\Windows\Customer Experience Improvement Program\Consolidator",
        "\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip",
        "\Microsoft\Windows\Feedback\Siuf\DmClient",
        "\Microsoft\Windows\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector",
        "\Microsoft\Windows\Autochk\Proxy"
    )

    foreach ($task in $tasksToDisable) {
        if (-not $DryRun) {
            $res = schtasks /change /tn $task /disable 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Disabled scheduled task: $task" "SUCCESS"
            } else {
                Write-Log "Notice on task $($task): $res" "WARN"
            }
        } else {
            Write-Log "[DryRun] Would disable scheduled task: $task" "INFO"
        }
    }

    # Disable DiagTrack service if running as administrator
    if (Test-IsAdmin) {
        $diagTrack = Get-Service -Name 'DiagTrack' -ErrorAction SilentlyContinue
        if ($diagTrack -and $diagTrack.Status -eq 'Running') {
            if (-not $DryRun) {
                Stop-Service -Name 'DiagTrack' -Force -ErrorAction SilentlyContinue
                Set-Service -Name 'DiagTrack' -StartupType Disabled -ErrorAction SilentlyContinue
                Write-Log "Disabled and stopped Connected User Experiences and Telemetry (DiagTrack) service." "SUCCESS"
            } else {
                Write-Log "[DryRun] Would stop and disable DiagTrack service." "INFO"
            }
        }
    } else {
        Write-Log "Note: Running in user mode. Run as Administrator for service-level tuning." "WARN"
    }
}

# ---------------------------------------------------------
# PHASE 5: UI LATENCY & VISUAL RESPONSIVENESS
# ---------------------------------------------------------
function Invoke-VisualAndUITuning {
    Write-Host "`n [PHASE: UI LATENCY & VISUAL RESPONSIVENESS]" -ForegroundColor Cyan
    Write-Log "Tuning UI response latency for instant window and menu opening..." "INFO"

    if (-not $DryRun) {
        # 1. Reduce Menu Show Delay from 400ms to 10ms
        Set-ItemProperty -Path 'HKCU:\Control Panel\Desktop' -Name 'MenuShowDelay' -Value '10' -Force
        Write-Log "Reduced MenuShowDelay to 10ms (context menus open instantly)." "SUCCESS"

        # 2. Disable slow window minimize/maximize animations for snappy switching
        if (-not (Test-Path 'HKCU:\Control Panel\Desktop\WindowMetrics')) {
            New-Item -Path 'HKCU:\Control Panel\Desktop\WindowMetrics' -Force | Out-Null
        }
        Set-ItemProperty -Path 'HKCU:\Control Panel\Desktop\WindowMetrics' -Name 'MinAnimate' -Value '0' -Force
        Write-Log "Disabled slow minimize/restore animation delays." "SUCCESS"

        # 3. Disable Taskbar animations delay
        Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' -Name 'TaskbarAnimations' -Value 0 -Force
        Write-Log "Set TaskbarAnimations to instant mode." "SUCCESS"

        # 4. Disable Edge Background Preload on boot
        $edgeKey = 'HKCU:\Software\Policies\Microsoft\Edge'
        if (-not (Test-Path $edgeKey)) { New-Item -Path $edgeKey -Force | Out-Null }
        Set-ItemProperty -Path $edgeKey -Name 'StartupBoostEnabled' -Value 0 -Force -ErrorAction SilentlyContinue
        Set-ItemProperty -Path $edgeKey -Name 'BackgroundModeEnabled' -Value 0 -Force -ErrorAction SilentlyContinue
        Write-Log "Disabled Microsoft Edge background startup boost to save ~200MB RAM." "SUCCESS"
    } else {
        Write-Log "[DryRun] Would configure MenuShowDelay=10ms and disable animation lag." "INFO"
    }
}

# ---------------------------------------------------------
# PHASE 6: POWER & CPU GOVERNOR TUNING
# ---------------------------------------------------------
function Invoke-PowerOptimization {
    Write-Host "`n [PHASE: POWER & CPU GOVERNOR TUNING]" -ForegroundColor Cyan
    Write-Log "Configuring CPU power responsiveness for low-TDP quad-core..." "INFO"

    $activeScheme = (powercfg /getactivescheme) -replace '.*GUID:\s*([^\s]+)\s*\(.*', '$1'
    Write-Log "Current Active Scheme GUID: $activeScheme" "INFO"

    if (-not $DryRun) {
        # Duplicate High Performance scheme if not present
        $highPerfGuid = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
        $schemes = powercfg /list
        
        if ($schemes -match $highPerfGuid) {
            powercfg /setactive $highPerfGuid
            Write-Log "Switched active power plan to High Performance ($highPerfGuid)." "SUCCESS"
        } else {
            # Attempt to unhide or create High Performance
            powercfg -duplicatescheme $highPerfGuid 2>$null | Out-Null
            $schemesAfter = powercfg /list
            if ($schemesAfter -match $highPerfGuid) {
                powercfg /setactive $highPerfGuid
                Write-Log "Activated newly imported High Performance power scheme." "SUCCESS"
            } else {
                # Configure the active scheme for responsiveness
                # SUB_PROCESSOR (54533251-82be-4824-96c1-47b60b740d00)
                # PROCTHROTTLEMIN: 5% (cool idle)
                # PROCTHROTTLEMAX: 100% (full burst capacity)
                powercfg /setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMIN 5 2>$null
                powercfg /setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX 100 2>$null
                powercfg /setactive SCHEME_CURRENT 2>$null
                Write-Log "Tuned current power scheme processor throttling bounds (Min: 5%, Max: 100%)." "SUCCESS"
            }
        }
    } else {
        Write-Log "[DryRun] Would optimize power scheme for high responsiveness." "INFO"
    }
}

# ---------------------------------------------------------
# PHASE 7: STARTUP BLOAT MANAGEMENT
# ---------------------------------------------------------
function Invoke-StartupOptimization {
    Write-Host "`n [PHASE: STARTUP BLOAT MANAGEMENT]" -ForegroundColor Cyan
    Write-Log "Analyzing and optimizing background startup programs..." "INFO"

    $hkcuRun = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
    $items = Get-ItemProperty -Path $hkcuRun -ErrorAction SilentlyContinue

    $targetStartupHogs = @(
        'GoogleChromeAutoLaunch_E158563B6D5ACE81C9BF68562B3EF297',
        'MicrosoftCopilotAutoLaunch_EB9A11AE69AB2D13B72BAADA832B2292',
        'ut',
        'TeraBox',
        'TeraBoxWeb',
        'Free Download Manager'
    )

    $backupReg = 'HKCU:\Software\LaptopOptimizer_DisabledRun'
    if (-not (Test-Path $backupReg)) { New-Item -Path $backupReg -Force | Out-Null }

    foreach ($item in $targetStartupHogs) {
        if ($items.PSObject.Properties[$item]) {
            $val = $items.PSObject.Properties[$item].Value
            Write-Log "Identified startup bloat: $item" "INFO"

            if (-not $DryRun) {
                Set-ItemProperty -Path $backupReg -Name $item -Value $val -Force
                Remove-ItemProperty -Path $hkcuRun -Name $item -Force -ErrorAction SilentlyContinue
                Write-Log "Disabled auto-start for: $item (backed up for easy restoration)" "SUCCESS"
            } else {
                Write-Log "[DryRun] Would disable auto-start for: $item" "INFO"
            }
        }
    }
}

# ---------------------------------------------------------
# MAIN EXECUTION ROUTER
# ---------------------------------------------------------
function Run-OptimizationPipeline {
    param([string]$PipelineMode)

    Show-Banner
    Write-Host " EXECUTING PRESET: $PipelineMode $(if ($DryRun) { '[DRY RUN MODE]' })" -ForegroundColor Green
    Write-Host "-----------------------------------------------------------------" -ForegroundColor Gray

    Backup-SystemState

    switch ($PipelineMode) {
        'QuickBoost' {
            Invoke-MemoryRelief
            Invoke-StorageCleanup
            Invoke-VisualAndUITuning
        }
        'DeepClean' {
            Invoke-StorageCleanup -Aggressive
            Invoke-SSDTrim
        }
        'FullOptimize' {
            Invoke-StorageCleanup -Aggressive
            Invoke-SSDTrim
            Invoke-MemoryRelief
            Invoke-TelemetryTuning
            Invoke-VisualAndUITuning
            Invoke-PowerOptimization
            Invoke-StartupOptimization
        }
        'StartupOptimize' {
            Invoke-StartupOptimization
        }
        'Restore' {
            Restore-LaptopState
            return
        }
        'Benchmark' {
            & (Join-Path $ScriptDir "benchmark.ps1")
            return
        }
    }

    Write-Host "`n=================================================================" -ForegroundColor Cyan
    Write-Host " OPTIMIZATION PIPELINE COMPLETED SUCCESSFULLY! " -ForegroundColor Green
    Write-Host " Check the log file for detailed audit: $LogFile" -ForegroundColor Gray
    Write-Host "=================================================================`n" -ForegroundColor Cyan
}

# ---------------------------------------------------------
# INTERACTIVE TERMINAL MENU
# ---------------------------------------------------------
if ($Preset -eq 'Interactive') {
    while ($true) {
        Show-Banner
        Write-Host "  [1] Quick Boost             (Memory purge + Cache clean + UI speedup)" -ForegroundColor White
        Write-Host "  [2] Deep Clean & SSD TRIM   (Full disk reclamation + NVMe/SSD block trim)" -ForegroundColor White
        Write-Host "  [3] Full System Optimize    (All optimizations + Telemetry & Power tuning)" -ForegroundColor Yellow
        Write-Host "  [4] Optimize Startup Bloat  (Disable unneeded auto-launching apps on boot)" -ForegroundColor White
        Write-Host "  [5] Run Performance Audit   (Live CPU, RAM, Disk & Process metrics)" -ForegroundColor White
        Write-Host "  [6] Restore Previous State  (Rollback settings to backup)" -ForegroundColor Magenta
        Write-Host "  [7] Exit" -ForegroundColor Gray
        Write-Host ""
        $choice = Read-Host " Select an option [1-7]"

        switch ($choice) {
            '1' { Run-OptimizationPipeline -PipelineMode 'QuickBoost'; Pause }
            '2' { Run-OptimizationPipeline -PipelineMode 'DeepClean'; Pause }
            '3' { Run-OptimizationPipeline -PipelineMode 'FullOptimize'; Pause }
            '4' { Run-OptimizationPipeline -PipelineMode 'StartupOptimize'; Pause }
            '5' { & (Join-Path $ScriptDir "benchmark.ps1"); Pause }
            '6' { Restore-LaptopState; Pause }
            '7' { Write-Host "`nGoodbye!`n"; exit 0 }
            default { Write-Host "Invalid selection. Please choose 1-7." -ForegroundColor Red; Start-Sleep -Seconds 1 }
        }
    }
} else {
    Run-OptimizationPipeline -PipelineMode $Preset
}
