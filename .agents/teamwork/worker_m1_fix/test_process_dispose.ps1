$p = [System.Diagnostics.Process]::GetCurrentProcess()
Write-Host "Start: " $p.HandleCount

$procs = Get-Process
Write-Host "After Get-Process: " $p.HandleCount

foreach ($proc in $procs) {
    try {
        $c = $proc.CPU
    } catch { }
}
$p.Refresh()
Write-Host "After reading .CPU: " $p.HandleCount

foreach ($proc in $procs) {
    $proc.Dispose()
}
$p.Refresh()
Write-Host "After foreach .Dispose(): " $p.HandleCount

[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()
$p.Refresh()
Write-Host "After GC: " $p.HandleCount
