<#
.SYNOPSIS
    Diagnostics and performance profiling engine for Windows 11 Laptop Optimizer.
.DESCRIPTION
    Captures live snapshots of CPU, RAM, memory compression, pagefile usage,
    storage, active power scheme, startup items, scheduled tasks, and top
    processes. Works without Administrator privileges, gracefully handling
    elevated-only counters.
.NOTES
    Part of Milestone M1 (Diagnostics & Performance Profiling).
#>

# Dot-source common dependencies if available
$commonDir = Join-Path $PSScriptRoot "..\Common"
if (Test-Path (Join-Path $commonDir "Platform.ps1")) {
    . (Join-Path $commonDir "Platform.ps1")
}
if (Test-Path (Join-Path $commonDir "Types.ps1")) {
    . (Join-Path $commonDir "Types.ps1")
}

function Get-LaptopStartupItems {
    <#
    .SYNOPSIS
        Scans startup items across HKCU, HKLM, and StartupApproved registry keys.
    .OUTPUTS
        [array] Array of custom objects describing each startup item.
    #>
    [CmdletBinding()]
    param()

    $items = [System.Collections.Generic.List[PSCustomObject]]::new()

    # 1. User Run Key (HKCU)
    $hkcuRun = Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -ErrorAction SilentlyContinue
    $hkcuApproved = Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run" -ErrorAction SilentlyContinue
    if ($hkcuRun) {
        foreach ($prop in $hkcuRun.PSObject.Properties) {
            if ($prop.Name -notin @("PSPath", "PSParentPath", "PSChildName", "PSDrive", "PSProvider")) {
                $status = "Enabled"
                if ($hkcuApproved -and ($hkcuApproved.PSObject.Properties[$prop.Name])) {
                    $bin = $hkcuApproved.PSObject.Properties[$prop.Name].Value
                    if ($bin -and $bin.Length -ge 1 -and ($bin[0] % 2 -eq 1)) {
                        $status = "Disabled"
                    }
                }
                $items.Add([PSCustomObject]@{
                    Name     = $prop.Name
                    Command  = if ($null -ne $prop.Value) { $prop.Value.ToString() } else { "" }
                    Scope    = "User"
                    Status   = $status
                    Location = "HKCU\Software\Microsoft\Windows\CurrentVersion\Run"
                })
            }
        }
    }

    # 2. System Run Key (HKLM)
    $hklmRun = Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" -ErrorAction SilentlyContinue
    $hklmApproved = Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run" -ErrorAction SilentlyContinue
    if ($hklmRun) {
        foreach ($prop in $hklmRun.PSObject.Properties) {
            if ($prop.Name -notin @("PSPath", "PSParentPath", "PSChildName", "PSDrive", "PSProvider")) {
                $status = "Enabled"
                if ($hklmApproved -and ($hklmApproved.PSObject.Properties[$prop.Name])) {
                    $bin = $hklmApproved.PSObject.Properties[$prop.Name].Value
                    if ($bin -and $bin.Length -ge 1 -and ($bin[0] % 2 -eq 1)) {
                        $status = "Disabled"
                    }
                }
                $items.Add([PSCustomObject]@{
                    Name     = $prop.Name
                    Command  = if ($null -ne $prop.Value) { $prop.Value.ToString() } else { "" }
                    Scope    = "System"
                    Status   = $status
                    Location = "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
                })
            }
        }
    }

    # 3. Startup Folders via Win32_StartupCommand
    $wmiStartup = Get-CimInstance Win32_StartupCommand -ErrorAction SilentlyContinue
    if ($wmiStartup) {
        foreach ($s in $wmiStartup) {
            $alreadyAdded = $items | Where-Object { $_.Name -eq $s.Name -or ($_.Command -eq $s.Command -and $_.Command -ne "") }
            if (-not $alreadyAdded) {
                $items.Add([PSCustomObject]@{
                    Name     = $s.Name
                    Command  = if ($null -ne $s.Command) { $s.Command } else { "" }
                    Scope    = if ($s.User -match "NT AUTHORITY|All Users") { "System" } else { "User" }
                    Status   = "Enabled"
                    Location = if ($null -ne $s.Location) { $s.Location } else { "StartupFolder" }
                })
            }
        }
    }

    return @($items)
}

function Get-LaptopSystemSnapshot {
    <#
    .SYNOPSIS
        Captures a comprehensive live diagnostic snapshot of laptop system resources.
    .PARAMETER Detailed
        If specified, includes granular lists of startup items, scheduled tasks, and secondary metrics.
    .OUTPUTS
        [PSCustomObject] containing baseline/live metric snapshot conforming to PROJECT.md interface contract.
    #>
    [CmdletBinding()]
    param(
        [switch]$Detailed
    )

    $now = [System.DateTime]::Now

    # 1. Operating System and Computer System
    $os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
    $cs = Get-CimInstance Win32_ComputerSystem -ErrorAction SilentlyContinue
    $cpu = Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue | Select-Object -First 1

    $osCaption = if ($os -and $os.Caption) { $os.Caption.Trim() } else { "Microsoft Windows 11" }

    # 2. Physical RAM
    $totalRamBytes = 0L
    if ($cs -and $cs.TotalPhysicalMemory) {
        $totalRamBytes = [int64]$cs.TotalPhysicalMemory
    } elseif ($os -and $os.TotalVisibleMemorySize) {
        $totalRamBytes = [int64]$os.TotalVisibleMemorySize * 1024L
    }

    $totalRamMB = [math]::Round($totalRamBytes / 1MB, 2)
    $totalRamGB = [math]::Round($totalRamBytes / 1GB, 2)

    $freeRamKB = if ($os -and $os.FreePhysicalMemory) { [double]$os.FreePhysicalMemory } else { 0.0 }
    $freeRamMB = [math]::Round($freeRamKB / 1024.0, 2)
    $freeRamPercent = if ($totalRamMB -gt 0) { [math]::Round(($freeRamMB / $totalRamMB) * 100.0, 2) } else { 0.0 }

    # 3. Memory Compression
    $memCompWS_MB = 0.0
    $memCompPrivate_MB = 0.0
    $memCompProc = $null
    try {
        $memCompProc = Get-Process -Name "Memory Compression" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($memCompProc) {
            $memCompWS_MB = [math]::Round($memCompProc.WorkingSet64 / 1MB, 2)
            $memCompPrivate_MB = [math]::Round($memCompProc.PrivateMemorySize64 / 1MB, 2)
        }
    } finally {
        if ($memCompProc) {
            try { $memCompProc.Dispose() } catch { }
        }
    }

    # 4. PerfOS_Memory Counters
    $perfMem = Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory -ErrorAction SilentlyContinue
    $committedBytesMB = if ($perfMem -and $perfMem.CommittedBytes) { [math]::Round($perfMem.CommittedBytes / 1MB, 2) } else { 0.0 }
    $commitLimitMB = if ($perfMem -and $perfMem.CommitLimit) { [math]::Round($perfMem.CommitLimit / 1MB, 2) } else { 0.0 }
    $pagesPerSec = if ($perfMem -and ($null -ne $perfMem.PagesPersec)) { [int64]$perfMem.PagesPersec } else { 0L }

    # 5. Paging File Usage
    $pageFiles = Get-CimInstance Win32_PageFileUsage -ErrorAction SilentlyContinue
    $pageAllocatedMB = 0.0
    $pageUsageMB = 0.0
    $pagePeakMB = 0.0
    if ($pageFiles) {
        foreach ($pf in $pageFiles) {
            $pageAllocatedMB += [double]$pf.AllocatedBaseSize
            $pageUsageMB += [double]$pf.CurrentUsage
            $pagePeakMB += [double]$pf.PeakUsage
        }
    }
    $pageAllocatedMB = [math]::Round($pageAllocatedMB, 2)
    $pageUsageMB = [math]::Round($pageUsageMB, 2)
    $pagePeakMB = [math]::Round($pagePeakMB, 2)
    $autoManagedPage = if ($cs -and ($null -ne $cs.AutomaticManagedPagefile)) { [bool]$cs.AutomaticManagedPagefile } else { $true }

    # 6. Disk C: Storage
    $driveCTotalGB = 0.0
    $driveCFreeGB = 0.0
    $driveCFreePct = 0.0
    $driveCFileSystem = "NTFS"
    $driveCHealth = "Healthy"

    $vol = Get-Volume -DriveLetter C -ErrorAction SilentlyContinue
    if ($vol) {
        $driveCTotalGB = [math]::Round($vol.Size / 1GB, 2)
        $driveCFreeGB = [math]::Round($vol.SizeRemaining / 1GB, 2)
        if ($vol.Size -gt 0) {
            $driveCFreePct = [math]::Round(($vol.SizeRemaining / $vol.Size) * 100.0, 2)
        }
        $driveCFileSystem = if ($vol.FileSystemType) { $vol.FileSystemType } else { "NTFS" }
        $driveCHealth = if ($vol.HealthStatus) { $vol.HealthStatus } else { "Healthy" }
    } else {
        $disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'" -ErrorAction SilentlyContinue
        if ($disk) {
            $driveCTotalGB = [math]::Round($disk.Size / 1GB, 2)
            $driveCFreeGB = [math]::Round($disk.FreeSpace / 1GB, 2)
            if ($disk.Size -gt 0) {
                $driveCFreePct = [math]::Round(($disk.FreeSpace / $disk.Size) * 100.0, 2)
            }
            $driveCFileSystem = if ($disk.FileSystem) { $disk.FileSystem } else { "NTFS" }
        }
    }

    # 7. Active Power Scheme
    $activeSchemeGuid = "381b4222-f694-41f0-9685-ff5bb260df2e"
    $activeSchemeName = "Balanced"
    try {
        $powerRaw = (powercfg /getactivescheme 2>$null) | Out-String
        if ($powerRaw -match '([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\s*\((.+?)\)') {
            $activeSchemeGuid = $matches[1]
            $activeSchemeName = $matches[2].Trim()
        } elseif ($powerRaw -match '([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})') {
            $activeSchemeGuid = $matches[1]
        }
    } catch {
        # Keep defaults
    }
    $activePowerScheme = "$activeSchemeName ($activeSchemeGuid)"

    # 8. Startup Items
    $startupList = Get-LaptopStartupItems
    $startupCount = $startupList.Count

    # 9. Scheduled Tasks
    $tasks = Get-ScheduledTask -ErrorAction SilentlyContinue
    $totalTasks = if ($tasks) { $tasks.Count } else { 0 }
    $activeTasks = if ($tasks) { ($tasks | Where-Object { $_.State -ne 'Disabled' }).Count } else { 0 }

    # 10. Process Count & Top Consumers (Deterministic Handle Hygiene Pattern)
    $procs = $null
    $procCount = 0
    $topProcesses = @()
    $topProcessesByCPU = @()

    try {
        $procs = Get-Process -ErrorAction SilentlyContinue
        if ($procs) {
            $procCount = $procs.Count
            $procList = [System.Collections.Generic.List[PSCustomObject]]::new($procCount)

            foreach ($p in $procs) {
                try {
                    $cpuSec = 0.0
                    try {
                        if ($null -ne $p.CPU) { $cpuSec = [math]::Round([double]$p.CPU, 2) }
                    } catch {
                        # Suppress access denied on system/protected processes or exited processes
                    }

                    $wsMB = 0.0
                    $pmMB = 0.0
                    try {
                        $wsMB = [math]::Round($p.WorkingSet64 / 1MB, 2)
                        $pmMB = [math]::Round($p.PrivateMemorySize64 / 1MB, 2)
                    } catch {
                        # Process exited between enumeration and property query
                    }

                    $procList.Add([PSCustomObject]@{
                        Name    = $p.ProcessName
                        Id      = $p.Id
                        WS_MB   = $wsMB
                        CPU_Sec = $cpuSec
                        PM_MB   = $pmMB
                    })
                } finally {
                    try { $p.Dispose() } catch { }
                }
            }

            # Sort pure PSCustomObjects: Zero handles held, ~5x faster comparison
            $topProcesses = @($procList | Sort-Object -Property WS_MB -Descending | Select-Object -First 10)
            $topProcessesByCPU = @($procList | Where-Object { $_.CPU_Sec -gt 0 } | Sort-Object -Property CPU_Sec -Descending | Select-Object -First 10)
        }
    } finally {
        # Defensive fallback: dispose any unhandled instances if loop was prematurely interrupted
        if ($procs) {
            foreach ($p in $procs) {
                try { $p.Dispose() } catch { }
            }
        }
    }

    # 11. CPU Details
    $cpuLoad = if ($cpu -and ($null -ne $cpu.LoadPercentage)) { [int]$cpu.LoadPercentage } else { 0 }
    $cpuName = if ($cpu -and $cpu.Name) { $cpu.Name.Trim() } else { "Intel(R) N100" }
    $cpuCores = if ($cpu -and $cpu.NumberOfCores) { [int]$cpu.NumberOfCores } else { 4 }
    $cpuLogical = if ($cpu -and $cpu.NumberOfLogicalProcessors) { [int]$cpu.NumberOfLogicalProcessors } else { 4 }

    # Elevation check (with deterministic identity disposal)
    $identity = $null
    $isElevated = try {
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = [Security.Principal.WindowsPrincipal]$identity
        $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } catch {
        $false
    } finally {
        if ($identity) {
            try { $identity.Dispose() } catch { }
        }
    }

    # Construct snapshot object conforming to PROJECT.md interface contract
    $snapshot = [PSCustomObject]@{
        # Core Contract Properties (Mandatory)
        Timestamp                  = $now
        OS                         = $osCaption
        FreeRAM_MB                 = $freeRamMB
        TotalRAM_GB                = $totalRamGB
        FreeRAM_Percent            = $freeRamPercent
        MemoryCompression_MB       = $memCompWS_MB
        PageFile_Usage_MB          = $pageUsageMB
        PageFile_Allocated_MB      = $pageAllocatedMB
        DriveC_Free_GB             = $driveCFreeGB
        DriveC_Total_GB            = $driveCTotalGB
        ActivePowerScheme          = $activePowerScheme
        ProcessCount               = $procCount
        StartupItemsCount          = $startupCount
        TopProcesses               = $topProcesses

        # Extended Diagnostic Properties
        TotalRAM_MB                = $totalRamMB
        DriveC_Free_Percent        = $driveCFreePct
        DriveC_FileSystem          = $driveCFileSystem
        DriveC_HealthStatus        = $driveCHealth
        PageFile_Peak_MB           = $pagePeakMB
        AutomaticManagedPagefile   = $autoManagedPage
        MemoryCompression_WS_MB    = $memCompWS_MB
        MemoryCompression_Private_MB = $memCompPrivate_MB
        CommittedVirtualMemory_MB  = $committedBytesMB
        CommitLimit_MB             = $commitLimitMB
        PagesPerSecond             = $pagesPerSec
        ScheduledTasksCount        = $totalTasks
        ActiveScheduledTasksCount  = $activeTasks
        CPU_Name                   = $cpuName
        CPU_Cores                  = $cpuCores
        CPU_LogicalCores           = $cpuLogical
        CPU_LoadPercent            = $cpuLoad
        IsElevated                 = $isElevated
    }

    if ($Detailed) {
        $snapshot | Add-Member -MemberType NoteProperty -Name "StartupItems" -Value $startupList
        $snapshot | Add-Member -MemberType NoteProperty -Name "TopProcessesByCPU" -Value $topProcessesByCPU
    }

    return $snapshot
}
