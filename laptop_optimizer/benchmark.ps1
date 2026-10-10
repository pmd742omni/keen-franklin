<#
.SYNOPSIS
    System Performance Benchmark and Diagnostics Collector.
.DESCRIPTION
    Collects key health and performance metrics on Windows 11 systems,
    including CPU utilization, memory pressure, disk utilization,
    process counts, and top resource consumers.
#>
param(
    [string]$OutputFile = ""
)

$ErrorActionPreference = "SilentlyContinue"

$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor
$cs = Get-CimInstance Win32_ComputerSystem
$diskC = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"

$totalRamMB = [math]::Round($os.TotalVisibleMemorySize / 1024, 1)
$freeRamMB = [math]::Round($os.FreePhysicalMemory / 1024, 1)
$usedRamMB = [math]::Round($totalRamMB - $freeRamMB, 1)
$ramPercent = [math]::Round(($usedRamMB / $totalRamMB) * 100, 1)

$diskTotalGB = [math]::Round($diskC.Size / 1GB, 2)
$diskFreeGB = [math]::Round($diskC.FreeSpace / 1GB, 2)
$diskUsedGB = [math]::Round($diskTotalGB - $diskFreeGB, 2)
$diskUsedPct = [math]::Round(($diskUsedGB / $diskTotalGB) * 100, 1)

$procs = Get-Process
$procCount = $procs.Count
$threadCount = ($procs | Measure-Object -Property Threads -Sum).Sum

# CPU measurement over 2 seconds
$cpuSample = (Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 2 -MaxSamples 1).CounterSamples.CookedValue
$cpuUsage = [math]::Round($cpuSample, 1)

# Power Plan
$powerScheme = (powercfg /getactivescheme) -replace '.*GUID:\s*([^\s]+)\s*\((.*)\)', '$2 ($1)'

# Top memory consumers
$topMem = $procs | Sort-Object WorkingSet64 -Descending | Select-Object -First 5 | ForEach-Object {
    [PSCustomObject]@{
        Name = $_.Name
        PID  = $_.Id
        MB   = [math]::Round($_.WorkingSet64 / 1MB, 1)
    }
}

# Top CPU consumers
$topCPU = $procs | Where-Object { $_.CPU -gt 0 } | Sort-Object CPU -Descending | Select-Object -First 5 | ForEach-Object {
    [PSCustomObject]@{
        Name    = $_.Name
        PID     = $_.Id
        CPUSec  = [math]::Round($_.CPU, 1)
        RAM_MB  = [math]::Round($_.WorkingSet64 / 1MB, 1)
    }
}

$results = [PSCustomObject]@{
    Timestamp        = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    ComputerName     = $cs.Name
    Model            = "$($cs.Manufacturer) $($cs.Model)"
    CPU              = $cpu.Name
    CoresLogical     = "$($cpu.NumberOfCores)C / $($cpu.NumberOfLogicalProcessors)T"
    CPU_Load_Pct     = $cpuUsage
    Total_RAM_MB     = $totalRamMB
    Used_RAM_MB      = $usedRamMB
    Free_RAM_MB      = $freeRamMB
    RAM_Usage_Pct    = $ramPercent
    Disk_C_Total_GB  = $diskTotalGB
    Disk_C_Free_GB   = $diskFreeGB
    Disk_C_Used_Pct  = $diskUsedPct
    ProcessCount     = $procCount
    ActivePowerPlan  = $powerScheme.Trim()
    TopMemoryProcs   = $topMem
    TopCPUProcs      = $topCPU
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "        SYSTEM PERFORMANCE BENCHMARK REPORT              " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Time:             $($results.Timestamp)"
Write-Host "Hardware:         $($results.Model) | $($results.CPU) ($($results.CoresLogical))"
Write-Host "CPU Active Load:  $($results.CPU_Load_Pct) %"
Write-Host "RAM Total:        $($results.Total_RAM_MB) MB ($([math]::Round($results.Total_RAM_MB/1024, 2)) GB)"
Write-Host "RAM Used:         $($results.Used_RAM_MB) MB ($($results.RAM_Usage_Pct) %)"
Write-Host "RAM Free:         $($results.Free_RAM_MB) MB ($([math]::Round($results.Free_RAM_MB/1024, 2)) GB)"
Write-Host "Disk C: Free:     $($results.Disk_C_Free_GB) GB / $($results.Disk_C_Total_GB) GB ($($results.Disk_C_Used_Pct) % used)"
Write-Host "Process Count:    $($results.ProcessCount)"
Write-Host "Power Scheme:     $($results.ActivePowerPlan)"
Write-Host "----------------------------------------------------------"
Write-Host "Top Memory Processes:"
$topMem | Format-Table -AutoSize | Out-String | Write-Host
Write-Host "Top CPU Historical Processes:"
$topCPU | Format-Table -AutoSize | Out-String | Write-Host
Write-Host "==========================================================" -ForegroundColor Cyan

if ($OutputFile) {
    $results | ConvertTo-Json -Depth 4 | Set-Content -Path $OutputFile -Force
    Write-Host "Benchmark saved to: $OutputFile" -ForegroundColor Green
}

return $results
