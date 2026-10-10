$comparisonPath = "c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/src/Diagnostics/Comparison.ps1"
. $comparisonPath

$cases = @(
    @{
        Name = "Current only has DriveC_Total_GB = 0"
        Baseline = [PSCustomObject]@{ Timestamp = [DateTime]::Now; FreeRAM_MB = 1000; DriveC_Free_GB = 20; DriveC_Total_GB = 100; DriveC_Free_Percent = 20.0 }
        Current  = [PSCustomObject]@{ Timestamp = [DateTime]::Now; FreeRAM_MB = 1000; DriveC_Free_GB = 0; DriveC_Total_GB = 0 }
    },
    @{
        Name = "Current only is sparse"
        Baseline = [PSCustomObject]@{ Timestamp = [DateTime]::Now; FreeRAM_MB = 1000; DriveC_Free_GB = 20; DriveC_Total_GB = 100; DriveC_Free_Percent = 20.0 }
        Current  = [PSCustomObject]@{ Timestamp = [DateTime]::Now; FreeRAM_MB = 1200 }
    },
    @{
        Name = "Baseline only is sparse"
        Baseline = [PSCustomObject]@{ Timestamp = [DateTime]::Now; FreeRAM_MB = 1200 }
        Current  = [PSCustomObject]@{ Timestamp = [DateTime]::Now; FreeRAM_MB = 1000; DriveC_Free_GB = 20; DriveC_Total_GB = 100; DriveC_Free_Percent = 20.0 }
    },
    @{
        Name = "Both sparse"
        Baseline = [PSCustomObject]@{ Timestamp = [DateTime]::Now; FreeRAM_MB = 1200 }
        Current  = [PSCustomObject]@{ Timestamp = [DateTime]::Now; FreeRAM_MB = 1800 }
    }
)

foreach ($c in $cases) {
    Write-Host "Testing Case: $($c.Name)"
    try {
        $res = Compare-LaptopSnapshots -Baseline $c.Baseline -Current $c.Current
        Write-Host "  SUCCESS" -ForegroundColor Green
    } catch {
        Write-Host "  FAILED: $($_.Exception.GetType().FullName): $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "  StackTrace:`n$($_.ScriptStackTrace)" -ForegroundColor DarkGray
    }
}
