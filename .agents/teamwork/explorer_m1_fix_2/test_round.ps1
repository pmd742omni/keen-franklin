Write-Host "Testing [math]::Round([double]0 / [double]0, 1):"
try {
    $res = [math]::Round([double]0 / [double]0, 1)
    Write-Host "Result: $res"
} catch {
    Write-Host "Caught: $($_.Exception.Message)"
}

Write-Host "Testing [math]::Round([double]1 / [double]0, 1):"
try {
    $res = [math]::Round([double]1 / [double]0, 1)
    Write-Host "Result: $res"
} catch {
    Write-Host "Caught: $($_.Exception.Message)"
}
