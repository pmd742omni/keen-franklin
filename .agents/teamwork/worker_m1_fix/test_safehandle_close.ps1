$p = [System.Diagnostics.Process]::GetCurrentProcess()

function Check($label) {
    $p.Refresh()
    Write-Host "$label : $($p.HandleCount)"
}

Check "1. Start"
$procs = Get-Process
Check "2. After Get-Process"

foreach ($pr in $procs) {
    try { $c = $pr.CPU } catch {}
    try {
        if ($pr.SafeHandle -and -not $pr.SafeHandle.IsClosed) {
            $pr.SafeHandle.Close()
            $pr.SafeHandle.Dispose()
        }
    } catch {}
    try { $pr.Close() } catch {}
    try { $pr.Dispose() } catch {}
}
Check "3. After reading CPU & SafeHandle.Close()"

[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()
Check "4. After GC"
