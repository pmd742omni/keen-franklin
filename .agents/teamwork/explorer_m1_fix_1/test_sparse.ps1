$sparseCurrent = [PSCustomObject]@{ FreeRAM_MB = 1000 }
$sparseBaseline = [PSCustomObject]@{ FreeRAM_MB = 500 }

$rawProcDelta = [double]($sparseCurrent.ProcessCount - $sparseBaseline.ProcessCount)
$processDelta = if ([double]::IsNaN($rawProcDelta)) {
    0
} elseif ($rawProcDelta -ge [double][int]::MaxValue) {
    [int]::MaxValue
} elseif ($rawProcDelta -le [double][int]::MinValue) {
    [int]::MinValue
} else {
    [int][math]::Round($rawProcDelta)
}

Write-Host "Sparse test: raw=$rawProcDelta, delta=$processDelta, type=$($processDelta.GetType().Name)"
