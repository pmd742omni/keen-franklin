$p = [System.Diagnostics.Process]::GetCurrentProcess()

function Check($label) {
    $p.Refresh()
    Write-Host "$label : $($p.HandleCount)"
}

Check "Start"

$d = [System.IO.DriveInfo]::new("C")
Write-Host "Drive C Total: $($d.TotalSize / 1GB) GB, Free: $($d.TotalFreeSpace / 1GB) GB, Format: $($d.DriveFormat)"
Check "After [System.IO.DriveInfo]"

$disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
Check "After Win32_LogicalDisk"

$vol = Get-Volume -DriveLetter C
Check "After Get-Volume"
