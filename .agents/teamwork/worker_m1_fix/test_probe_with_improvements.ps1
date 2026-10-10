. "c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/src/Common/Platform.ps1"
. "c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/src/Common/Types.ps1"

# We will test the improved Get-LaptopSystemSnapshot logic
$p = [System.Diagnostics.Process]::GetCurrentProcess()
$handlesBefore = $p.HandleCount
Write-Host "Initial Handles: $handlesBefore"

. "c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/src/Diagnostics/Profiler.ps1"

$snapshots = @()
for ($i = 1; $i -le 10; $i++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $s = Get-LaptopSystemSnapshot
    $sw.Stop()
    $p.Refresh()
    Write-Host "Iteration $i in $($sw.ElapsedMilliseconds) ms -> Handles: $($p.HandleCount)"
}

$p.Refresh()
$handlesAfter = $p.HandleCount
$delta = $handlesAfter - $handlesBefore
Write-Host "TOTAL DELTA: $delta (Before: $handlesBefore, After: $handlesAfter)"
