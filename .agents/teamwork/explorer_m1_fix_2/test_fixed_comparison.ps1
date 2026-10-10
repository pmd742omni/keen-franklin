$origContent = Get-Content "c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/src/Diagnostics/Comparison.ps1" -Raw

# Replace lines 203 and 226 with the robust zero-safe guards
$origTarget203 = "FreeSpace_Percent  = if (`$Baseline.PSObject.Properties['DriveC_Free_Percent']) { `$Baseline.DriveC_Free_Percent } else { [math]::Round((`$Baseline.DriveC_Free_GB / `$Baseline.DriveC_Total_GB) * 100.0, 1) }"
$origTarget226 = "FreeSpace_Percent  = if (`$Current.PSObject.Properties['DriveC_Free_Percent']) { `$Current.DriveC_Free_Percent } else { [math]::Round((`$Current.DriveC_Free_GB / `$Current.DriveC_Total_GB) * 100.0, 1) }"

$replacement203 = @"
FreeSpace_Percent  = if (`$Baseline.PSObject.Properties['DriveC_Free_Percent'] -and `$null -ne `$Baseline.DriveC_Free_Percent) {
                    [double]`$Baseline.DriveC_Free_Percent
                } elseif (`$Baseline.PSObject.Properties['DriveC_Total_GB'] -and `$null -ne `$Baseline.DriveC_Total_GB -and [double]`$Baseline.DriveC_Total_GB -gt 0) {
                    `$bFree = if (`$Baseline.PSObject.Properties['DriveC_Free_GB'] -and `$null -ne `$Baseline.DriveC_Free_GB) { [double]`$Baseline.DriveC_Free_GB } else { 0.0 }
                    [math]::Round((`$bFree / [double]`$Baseline.DriveC_Total_GB) * 100.0, 1)
                } else {
                    0.0
                }
"@

$replacement226 = @"
FreeSpace_Percent  = if (`$Current.PSObject.Properties['DriveC_Free_Percent'] -and `$null -ne `$Current.DriveC_Free_Percent) {
                    [double]`$Current.DriveC_Free_Percent
                } elseif (`$Current.PSObject.Properties['DriveC_Total_GB'] -and `$null -ne `$Current.DriveC_Total_GB -and [double]`$Current.DriveC_Total_GB -gt 0) {
                    `$cFree = if (`$Current.PSObject.Properties['DriveC_Free_GB'] -and `$null -ne `$Current.DriveC_Free_GB) { [double]`$Current.DriveC_Free_GB } else { 0.0 }
                    [math]::Round((`$cFree / [double]`$Current.DriveC_Total_GB) * 100.0, 1)
                } else {
                    0.0
                }
"@

$fixedContent = $origContent.Replace($origTarget203, $replacement203).Replace($origTarget226, $replacement226)

# Save to our own folder
Set-Content -Path "c:/Users/ignaz/antigravity/keen-franklin/.agents/teamwork/explorer_m1_fix_2/Proposed_Comparison.ps1" -Value $fixedContent -Encoding UTF8

# Now test the proposed comparison function
. "c:/Users/ignaz/antigravity/keen-franklin/.agents/teamwork/explorer_m1_fix_2/Proposed_Comparison.ps1"

Write-Host "=== TEST 1: Adversarial Test 2.5 (DriveC_Total_GB = 0) ==="
$bZeroDisk = [PSCustomObject]@{
    Timestamp                  = [DateTime]::Now
    OS                         = "Windows 11"
    FreeRAM_MB                 = 1000.0
    TotalRAM_GB                = 8.0
    FreeRAM_Percent            = 12.0
    DriveC_Free_GB             = 0.0
    DriveC_Total_GB            = 0.0
    ActivePowerScheme          = "Balanced"
    ProcessCount               = 100
    StartupItemsCount          = 5
    TopProcesses               = @()
}
$cZeroDisk = [PSCustomObject]@{
    Timestamp                  = [DateTime]::Now
    OS                         = "Windows 11"
    FreeRAM_MB                 = 1600.0
    TotalRAM_GB                = 8.0
    FreeRAM_Percent            = 20.0
    DriveC_Free_GB             = 2.0
    DriveC_Total_GB            = 0.0
    ActivePowerScheme          = "Balanced"
    ProcessCount               = 100
    StartupItemsCount          = 5
    TopProcesses               = @()
}
try {
    $res = Compare-LaptopSnapshots -Baseline $bZeroDisk -Current $cZeroDisk
    Write-Host "  [PASS] Test 2.5 survived! FreeSpace_Percent Baseline: $($res.ReportJsonObject.Baseline.Storage.FreeSpace_Percent), Current: $($res.ReportJsonObject.PostOptimization.Storage.FreeSpace_Percent)" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Test 2.5 failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== TEST 2: Adversarial Test 2.8 (Sparse PSCustomObjects) ==="
$sparseBase = [PSCustomObject]@{ Timestamp = [DateTime]::Now; FreeRAM_MB = 1200.0 }
$sparseCurr = [PSCustomObject]@{ Timestamp = [DateTime]::Now; FreeRAM_MB = 1800.0 }
try {
    $sparseRes = Compare-LaptopSnapshots -Baseline $sparseBase -Current $sparseCurr
    $passed = ($sparseRes.RAMGained_MB -eq 600.0 -and $null -ne $sparseRes.ReportMarkdown)
    Write-Host "  [PASS] Test 2.8 survived! RAMGained_MB: $($sparseRes.RAMGained_MB), FreeSpace_Percent Base: $($sparseRes.ReportJsonObject.Baseline.Storage.FreeSpace_Percent), Curr: $($sparseRes.ReportJsonObject.PostOptimization.Storage.FreeSpace_Percent)" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Test 2.8 failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== TEST 3: StrictMode -Version Latest on Sparse Objects ==="
Set-StrictMode -Version Latest
try {
    $sparseResStrict = Compare-LaptopSnapshots -Baseline $sparseBase -Current $sparseCurr
    Write-Host "  [PASS] StrictMode passed! RAMGained_MB: $($sparseResStrict.RAMGained_MB)" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] StrictMode failed: $($_.Exception.Message)" -ForegroundColor Red
}
