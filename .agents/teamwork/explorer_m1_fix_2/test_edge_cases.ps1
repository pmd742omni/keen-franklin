function Get-SafeDriveCFreePercent($snapshot) {
    if ($snapshot.PSObject.Properties['DriveC_Free_Percent'] -and $null -ne $snapshot.DriveC_Free_Percent) {
        return [double]$snapshot.DriveC_Free_Percent
    } elseif ($snapshot.PSObject.Properties['DriveC_Total_GB'] -and $null -ne $snapshot.DriveC_Total_GB -and [double]$snapshot.DriveC_Total_GB -gt 0) {
        $freeGB = if ($snapshot.PSObject.Properties['DriveC_Free_GB'] -and $null -ne $snapshot.DriveC_Free_GB) { [double]$snapshot.DriveC_Free_GB } else { 0.0 }
        return [math]::Round(($freeGB / [double]$snapshot.DriveC_Total_GB) * 100.0, 1)
    } else {
        return 0.0
    }
}

$testCases = @(
    @{ Name = "Standard snapshot"; Obj = [PSCustomObject]@{ DriveC_Free_Percent = 16.0; DriveC_Total_GB = 237.36; DriveC_Free_GB = 38.01 }; Expected = 16.0 },
    @{ Name = "Calculated from Total and Free"; Obj = [PSCustomObject]@{ DriveC_Total_GB = 200.0; DriveC_Free_GB = 50.0 }; Expected = 25.0 },
    @{ Name = "Sparse snapshot (no storage props)"; Obj = [PSCustomObject]@{ Timestamp = [DateTime]::Now; FreeRAM_MB = 1200.0 }; Expected = 0.0 },
    @{ Name = "DriveC_Total_GB = 0"; Obj = [PSCustomObject]@{ DriveC_Total_GB = 0; DriveC_Free_GB = 0 }; Expected = 0.0 },
    @{ Name = "DriveC_Total_GB = 0.0 double"; Obj = [PSCustomObject]@{ DriveC_Total_GB = 0.0; DriveC_Free_GB = 5.0 }; Expected = 0.0 },
    @{ Name = "DriveC_Total_GB = null"; Obj = [PSCustomObject]@{ DriveC_Total_GB = $null; DriveC_Free_GB = 10.0 }; Expected = 0.0 },
    @{ Name = "DriveC_Total_GB = -10 (negative)"; Obj = [PSCustomObject]@{ DriveC_Total_GB = -10.0; DriveC_Free_GB = 5.0 }; Expected = 0.0 },
    @{ Name = "DriveC_Free_Percent = null, Total = 0"; Obj = [PSCustomObject]@{ DriveC_Free_Percent = $null; DriveC_Total_GB = 0 }; Expected = 0.0 },
    @{ Name = "DriveC_Free_Percent = 0.0 (full disk)"; Obj = [PSCustomObject]@{ DriveC_Free_Percent = 0.0; DriveC_Total_GB = 200.0; DriveC_Free_GB = 0.0 }; Expected = 0.0 },
    @{ Name = "DriveC_Free_Percent = 0 (integer zero)"; Obj = [PSCustomObject]@{ DriveC_Free_Percent = 0; DriveC_Total_GB = 200.0 }; Expected = 0.0 },
    @{ Name = "String types ('200.0' and '50.0')"; Obj = [PSCustomObject]@{ DriveC_Total_GB = "200.0"; DriveC_Free_GB = "50.0" }; Expected = 25.0 },
    @{ Name = "Total = 100, Free = null"; Obj = [PSCustomObject]@{ DriveC_Total_GB = 100.0; DriveC_Free_GB = $null }; Expected = 0.0 }
)

Write-Host "=== TEST RUN 1: Normal Mode ==="
$passed = 0
foreach ($tc in $testCases) {
    try {
        $actual = Get-SafeDriveCFreePercent $tc.Obj
        if ($actual -eq $tc.Expected -and $actual -is [double]) {
            Write-Host "  [PASS] $($tc.Name) -> $actual" -ForegroundColor Green
            $passed++
        } else {
            Write-Host "  [FAIL] $($tc.Name) -> Expected: $($tc.Expected), Actual: $actual (Type: $($actual.GetType().Name))" -ForegroundColor Red
        }
    } catch {
        Write-Host "  [ERROR] $($tc.Name) -> $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n=== TEST RUN 2: StrictMode -Version Latest ==="
Set-StrictMode -Version Latest
$strictPassed = 0
foreach ($tc in $testCases) {
    try {
        $actual = Get-SafeDriveCFreePercent $tc.Obj
        if ($actual -eq $tc.Expected -and $actual -is [double]) {
            Write-Host "  [PASS Strict] $($tc.Name) -> $actual" -ForegroundColor Green
            $strictPassed++
        } else {
            Write-Host "  [FAIL Strict] $($tc.Name) -> Expected: $($tc.Expected), Actual: $actual" -ForegroundColor Red
        }
    } catch {
        Write-Host "  [ERROR Strict] $($tc.Name) -> $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`nSummary: Normal $passed/$($testCases.Count) passed | Strict $strictPassed/$($testCases.Count) passed."
