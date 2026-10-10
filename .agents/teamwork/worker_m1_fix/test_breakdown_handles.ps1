. "c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/src/Common/Platform.ps1"
. "c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/src/Common/Types.ps1"
. "c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/src/Diagnostics/Profiler.ps1"

$p = [System.Diagnostics.Process]::GetCurrentProcess()

function Check-Delta($label) {
    $p.Refresh()
    Write-Host "$label -> Current Handles: $($p.HandleCount)"
}

Check-Delta "Start"

# 1. Operating System and Computer System
$os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
Check-Delta "After Win32_OperatingSystem"

$cs = Get-CimInstance Win32_ComputerSystem -ErrorAction SilentlyContinue
Check-Delta "After Win32_ComputerSystem"

$cpu = Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue | Select-Object -First 1
Check-Delta "After Win32_Processor"

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
Check-Delta "After Memory Compression"

# 4. PerfOS_Memory Counters
$perfMem = Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory -ErrorAction SilentlyContinue
Check-Delta "After PerfOS_Memory"

# 5. Paging File Usage
$pageFiles = Get-CimInstance Win32_PageFileUsage -ErrorAction SilentlyContinue
Check-Delta "After Win32_PageFileUsage"

# 6. Disk C: Storage
$vol = Get-Volume -DriveLetter C -ErrorAction SilentlyContinue
Check-Delta "After Get-Volume"

# 7. Active Power Scheme
$powerRaw = (powercfg /getactivescheme 2>$null) | Out-String
Check-Delta "After powercfg"

# 8. Startup Items
$startupList = Get-LaptopStartupItems
Check-Delta "After Get-LaptopStartupItems"

# 9. Scheduled Tasks
$tasks = Get-ScheduledTask -ErrorAction SilentlyContinue
Check-Delta "After Get-ScheduledTask"

# 10. Process Count & Top Consumers
$procs = Get-Process -ErrorAction SilentlyContinue
if ($procs) {
    foreach ($pr in $procs) {
        try { $null = $pr.CPU } catch {}
        try { $pr.Dispose() } catch {}
    }
}
Check-Delta "After Get-Process & Dispose"

# 11. Elevation
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$identity.Dispose()
Check-Delta "After WindowsIdentity"
