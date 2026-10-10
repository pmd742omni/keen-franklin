$testCases = @(
    @{ Name = "Normal delta (+50)"; B = 100; C = 150 },
    @{ Name = "Normal negative delta (-39)"; B = 150; C = 111 },
    @{ Name = "Zero delta (0)"; B = 100; C = 100 },
    @{ Name = "Challenger Case 1 ([int]::MaxValue - (-1))"; B = -1; C = [int]::MaxValue },
    @{ Name = "Challenger Case 2 ([int]::MinValue - 1)"; B = 1; C = [int]::MinValue },
    @{ Name = "Extreme span underflow (MinValue - MaxValue)"; B = [int]::MaxValue; C = [int]::MinValue },
    @{ Name = "Extreme span overflow (MaxValue - MinValue)"; B = [int]::MinValue; C = [int]::MaxValue },
    @{ Name = "Null baseline"; B = $null; C = 50 },
    @{ Name = "Null current"; B = 50; C = $null },
    @{ Name = "Both null"; B = $null; C = $null },
    @{ Name = "Double.MaxValue in Current"; B = 100; C = [double]::MaxValue },
    @{ Name = "Double.MinValue in Current"; B = 100; C = [double]::MinValue },
    @{ Name = "Positive Infinity in Current"; B = 100; C = [double]::PositiveInfinity },
    @{ Name = "Negative Infinity in Current"; B = 100; C = [double]::NegativeInfinity },
    @{ Name = "NaN in Current"; B = 100; C = [double]::NaN },
    @{ Name = "String number in Current"; B = 100; C = "150" }
)

Write-Host "================ OPTION 1: [double] with [math]::Min/[math]::Max (with typed double bounds) ================"
foreach ($tc in $testCases) {
    try {
        $raw = [double]($tc.C - $tc.B)
        $val = [int][math]::Max([double][int]::MinValue, [math]::Min([double][int]::MaxValue, $raw))
        Write-Host ("{0,-45}: res={1,12}, type={2}" -f $tc.Name, $val, $val.GetType().Name)
    } catch {
        Write-Host ("{0,-45}: THREW: {1}" -f $tc.Name, $_.Exception.Message) -ForegroundColor Red
    }
}

Write-Host "`n================ OPTION 2: Robust Defensive Clamping (handles NaN, Infinity, Null) ================"
function Test-Option2($Baseline, $Current) {
    $bProc = if ($null -ne $Baseline -and [double]::TryParse("$Baseline", [ref]$null)) { [double]$Baseline } else { 0.0 }
    $cProc = if ($null -ne $Current -and [double]::TryParse("$Current", [ref]$null)) { [double]$Current } else { 0.0 }
    $diff = $cProc - $bProc

    if ([double]::IsNaN($diff) -or [double]::IsInfinity($diff)) {
        return [int]0
    } elseif ($diff -ge [double][int]::MaxValue) {
        return [int][int]::MaxValue
    } elseif ($diff -le [double][int]::MinValue) {
        return [int][int]::MinValue
    } else {
        return [int][math]::Round($diff)
    }
}

foreach ($tc in $testCases) {
    try {
        $val = Test-Option2 $tc.B $tc.C
        Write-Host ("{0,-45}: res={1,12}, type={2}" -f $tc.Name, $val, $val.GetType().Name)
    } catch {
        Write-Host ("{0,-45}: THREW: {1}" -f $tc.Name, $_.Exception.Message) -ForegroundColor Red
    }
}

Write-Host "`n================ OPTION 3: Concise Clamping (Safe Coercion & Clamping) ================"
function Test-Option3($Baseline, $Current) {
    $rawDelta = [double]($Current - $Baseline)
    if ([double]::IsNaN($rawDelta)) {
        return [int]0
    } elseif ($rawDelta -ge [double][int]::MaxValue) {
        return [int][int]::MaxValue
    } elseif ($rawDelta -le [double][int]::MinValue) {
        return [int][int]::MinValue
    } else {
        return [int][math]::Round($rawDelta)
    }
}

foreach ($tc in $testCases) {
    try {
        $val = Test-Option3 $tc.B $tc.C
        Write-Host ("{0,-45}: res={1,12}, type={2}" -f $tc.Name, $val, $val.GetType().Name)
    } catch {
        Write-Host ("{0,-45}: THREW: {1}" -f $tc.Name, $_.Exception.Message) -ForegroundColor Red
    }
}
