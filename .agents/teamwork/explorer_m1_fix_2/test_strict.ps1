Set-StrictMode -Version Latest
$obj = [PSCustomObject]@{ A = 1 }
try {
    $val = $obj.B
    Write-Host "Accessed without error: $val"
} catch {
    Write-Host "StrictMode caught: $($_.Exception.Message)"
}

try {
    $hasProp = $null -ne $obj.PSObject.Properties['B']
    Write-Host "PSObject.Properties check works under StrictMode: $hasProp"
} catch {
    Write-Host "PSObject.Properties check failed under StrictMode: $($_.Exception.Message)"
}
