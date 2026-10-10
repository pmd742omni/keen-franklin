. "c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/src/Common/Platform.ps1"
. "c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/src/Common/Types.ps1"
. "c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/src/Diagnostics/Profiler.ps1"

$p = [System.Diagnostics.Process]::GetCurrentProcess()
Write-Host ("Initial HandleCount: " + $p.HandleCount)

for ($i = 1; $i -le 10; $i++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $s = Get-LaptopSystemSnapshot
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
    $sw.Stop()
    $p.Refresh()
    Write-Host ("Iteration " + $i + " (" + $sw.ElapsedMilliseconds + " ms) -> Handles: " + $p.HandleCount)
}
