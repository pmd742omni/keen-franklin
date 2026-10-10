$obj = [PSCustomObject]@{
    Percent = [double]::NaN
    Inf     = [double]::PositiveInfinity
}
try {
    $json = $obj | ConvertTo-Json
    Write-Host "JSON Output: $json"
} catch {
    Write-Host "ConvertTo-Json Error: $($_.Exception.Message)"
}
