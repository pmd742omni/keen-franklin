$comparisonPath = "c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/src/Diagnostics/Comparison.ps1"
$content = Get-Content $comparisonPath -Raw

# Replace line 108 with the proposed fix in-memory (simulated)
$oldLine = '$processDelta = [int]($Current.ProcessCount - $Baseline.ProcessCount)'
$newLine = @'
    # Safe ProcessDelta calculation with Int32 boundary clamping
    $rawProcDelta = [double]($Current.ProcessCount - $Baseline.ProcessCount)
    $processDelta = if ([double]::IsNaN($rawProcDelta)) {
        0
    } elseif ($rawProcDelta -ge [double][int]::MaxValue) {
        [int]::MaxValue
    } elseif ($rawProcDelta -le [double][int]::MinValue) {
        [int]::MinValue
    } else {
        [int][math]::Round($rawProcDelta)
    }
'@

$patchedContent = $content.Replace($oldLine, $newLine)

# Dot-source the patched script in current session
. ([scriptblock]::Create($patchedContent))

function New-MockSnapshot($FreeRAM_MB = 2048.0, $DriveC_Free_GB = 40.0, $ProcessCount = 100) {
    [PSCustomObject]@{
        Timestamp                  = [DateTime]::Now
        OS                         = "Microsoft Windows 11 Home 26200"
        FreeRAM_MB                 = [double]$FreeRAM_MB
        TotalRAM_GB                = 8.0
        FreeRAM_Percent            = 25.0
        MemoryCompression_MB       = 150.0
        PageFile_Usage_MB          = 500.0
        PageFile_Allocated_MB      = 4096.0
        DriveC_Free_GB             = [double]$DriveC_Free_GB
        DriveC_Total_GB            = 256.0
        ActivePowerScheme          = "Balanced (381b4222-f694-41f0-9685-ff5bb260df2e)"
        ProcessCount               = [int]$ProcessCount
        StartupItemsCount          = 15
        TopProcesses               = @()
    }
}

Write-Host "Running Boundary Tests:"

# 1. Overflow
$b1 = New-MockSnapshot -ProcessCount -1
$c1 = New-MockSnapshot -ProcessCount ([int]::MaxValue)
$r1 = Compare-LaptopSnapshots -Baseline $b1 -Current $c1
Write-Host ("1. Overflow : val={0}, type={1}, isInt={2}" -f $r1.ProcessDelta, $r1.ProcessDelta.GetType().Name, ($r1.ProcessDelta -is [int]))

# 2. Underflow
$b2 = New-MockSnapshot -ProcessCount 1
$c2 = New-MockSnapshot -ProcessCount ([int]::MinValue)
$r2 = Compare-LaptopSnapshots -Baseline $b2 -Current $c2
Write-Host ("2. Underflow: val={0}, type={1}, isInt={2}" -f $r2.ProcessDelta, $r2.ProcessDelta.GetType().Name, ($r2.ProcessDelta -is [int]))

# 3. Normal positive
$b3 = New-MockSnapshot -ProcessCount 100
$c3 = New-MockSnapshot -ProcessCount 150
$r3 = Compare-LaptopSnapshots -Baseline $b3 -Current $c3
Write-Host ("3. Normal + : val={0}, type={1}, isInt={2}" -f $r3.ProcessDelta, $r3.ProcessDelta.GetType().Name, ($r3.ProcessDelta -is [int]))

# 4. Normal negative (reduction)
$b4 = New-MockSnapshot -ProcessCount 150
$c4 = New-MockSnapshot -ProcessCount 111
$r4 = Compare-LaptopSnapshots -Baseline $b4 -Current $c4
Write-Host ("4. Normal - : val={0}, type={1}, isInt={2}" -f $r4.ProcessDelta, $r4.ProcessDelta.GetType().Name, ($r4.ProcessDelta -is [int]))

# 5. Sparse object without ProcessCount
$b5 = [PSCustomObject]@{ FreeRAM_MB = 1000.0; DriveC_Free_GB = 20.0 }
$c5 = [PSCustomObject]@{ FreeRAM_MB = 1500.0; DriveC_Free_GB = 25.0 }
$r5 = Compare-LaptopSnapshots -Baseline $b5 -Current $c5
Write-Host ("5. Sparse   : val={0}, type={1}, isInt={2}" -f $r5.ProcessDelta, $r5.ProcessDelta.GetType().Name, ($r5.ProcessDelta -is [int]))
