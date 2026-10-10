$p = [System.Diagnostics.Process]::GetCurrentProcess()

function Check($label) {
    $p.Refresh()
    Write-Host "$label : $($p.HandleCount)"
}

Check "1. Start"
$procs = Get-Process
Check "2. After Get-Process"

$handles = @()
foreach ($pr in $procs) {
    # Check if SafeHandle exists
    $sh = $pr.SafeHandle
    if ($sh) { $handles += $sh }
}
Write-Host "SafeHandles before accessing .CPU: $($handles.Count)"
Check "3. After SafeHandle check"

foreach ($pr in $procs) {
    try { $c = $pr.CPU } catch {}
}
Check "4. After reading CPU"

$handlesAfterCPU = @()
foreach ($pr in $procs) {
    $sh = $pr.SafeHandle
    if ($sh) { $handlesAfterCPU += $sh }
}
Write-Host "SafeHandles after accessing .CPU: $($handlesAfterCPU.Count)"

foreach ($pr in $procs) {
    try { $pr.Close() } catch {}
    try { $pr.Dispose() } catch {}
}
Check "5. After Close() and Dispose()"

$procs = $null
[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()
Check "6. After GC.Collect and WaitForPendingFinalizers"
