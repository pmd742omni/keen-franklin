Set-StrictMode -Version Latest

$sparseBase = [PSCustomObject]@{
    Timestamp  = [DateTime]::Now
    FreeRAM_MB = 1200.0
}

Write-Host "Test 1: Challenger approach under StrictMode"
try {
    $freePercent = if ($sparseBase.PSObject.Properties['DriveC_Free_Percent'] -and $null -ne $sparseBase.DriveC_Free_Percent) {
        $sparseBase.DriveC_Free_Percent
    } elseif ($sparseBase.DriveC_Total_GB -gt 0) {
        [math]::Round(([double]$sparseBase.DriveC_Free_GB / [double]$sparseBase.DriveC_Total_GB) * 100.0, 1)
    } else {
        0.0
    }
    Write-Host "Challenger approach succeeded: $freePercent"
} catch {
    Write-Host "Challenger approach THREW under StrictMode: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nTest 2: Robust property-guarded approach under StrictMode"
try {
    $freePercent = if ($sparseBase.PSObject.Properties['DriveC_Free_Percent'] -and $null -ne $sparseBase.DriveC_Free_Percent) {
        [double]$sparseBase.DriveC_Free_Percent
    } elseif ($sparseBase.PSObject.Properties['DriveC_Total_GB'] -and $null -ne $sparseBase.DriveC_Total_GB -and [double]$sparseBase.DriveC_Total_GB -gt 0) {
        $freeGB = if ($sparseBase.PSObject.Properties['DriveC_Free_GB'] -and $null -ne $sparseBase.DriveC_Free_GB) { [double]$sparseBase.DriveC_Free_GB } else { 0.0 }
        [math]::Round(($freeGB / [double]$sparseBase.DriveC_Total_GB) * 100.0, 1)
    } else {
        0.0
    }
    Write-Host "Robust approach succeeded: $freePercent" -ForegroundColor Green
} catch {
    Write-Host "Robust approach THREW under StrictMode: $($_.Exception.Message)" -ForegroundColor Red
}
