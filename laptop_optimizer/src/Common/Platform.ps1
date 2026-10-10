<#
.SYNOPSIS
    Platform and runtime compatibility module for Windows 11 Laptop Optimizer.
.DESCRIPTION
    Provides hardware specs, OS information, elevation checks, and cross-version
    PowerShell 5.1 / 7+ compatibility utilities.
.NOTES
    Part of Milestone M1 (Diagnostics & Performance Profiling).
#>

function Test-IsElevated {
    <#
    .SYNOPSIS
        Checks whether the current PowerShell session has Administrator privileges.
    .OUTPUTS
        [bool] True if running elevated as Administrator, False otherwise.
    #>
    [CmdletBinding()]
    param()

    try {
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = [Security.Principal.WindowsPrincipal]$identity
        return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } catch {
        return $false
    }
}

function Test-IsPS7 {
    <#
    .SYNOPSIS
        Checks if the current runtime is PowerShell 7 or higher.
    .OUTPUTS
        [bool] True if PS 7+, False if Windows PowerShell 5.1.
    #>
    [CmdletBinding()]
    param()

    return ($PSVersionTable.PSVersion.Major -ge 7)
}

function Get-Coalesce {
    <#
    .SYNOPSIS
        Returns the first non-null argument, providing null-coalescing compatibility for PowerShell 5.1.
    .PARAMETER First
        First candidate value.
    .PARAMETER Second
        Fallback value if First is null.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $false, Position = 0)]
        [object]$First,

        [Parameter(Mandatory = $false, Position = 1)]
        [object]$Second
    )

    if ($null -ne $First) { return $First }
    return $Second
}

function ConvertTo-JsonSafe {
    <#
    .SYNOPSIS
        Serializes an object to JSON with a safe default depth (10) for both PS 5.1 and PS 7+.
    .PARAMETER InputObject
        The object to convert to JSON.
    .PARAMETER Depth
        Serialization depth (default: 10).
    .PARAMETER Compress
        Omits white space and indented formatting.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
        [object]$InputObject,

        [int]$Depth = 10,

        [switch]$Compress
    )

    if ($Compress) {
        return ($InputObject | ConvertTo-Json -Depth $Depth -Compress)
    } else {
        return ($InputObject | ConvertTo-Json -Depth $Depth)
    }
}

function Get-LaptopPlatformInfo {
    <#
    .SYNOPSIS
        Retrieves hardware, OS, architecture, and runtime platform details for the laptop.
    .OUTPUTS
        [PSCustomObject] containing OS, CPU, RAM, and runtime environment specifications.
    #>
    [CmdletBinding()]
    param()

    $os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
    $cs = Get-CimInstance Win32_ComputerSystem -ErrorAction SilentlyContinue
    $cpu = Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue | Select-Object -First 1

    $totalRamBytes = 0L
    if ($cs -and $cs.TotalPhysicalMemory) {
        $totalRamBytes = [int64]$cs.TotalPhysicalMemory
    } elseif ($os -and $os.TotalVisibleMemorySize) {
        $totalRamBytes = [int64]$os.TotalVisibleMemorySize * 1024L
    }

    $totalRamMB = [math]::Round($totalRamBytes / 1MB, 2)
    $totalRamGB = [math]::Round($totalRamBytes / 1GB, 2)

    $osArch = if ($os -and $os.OSArchitecture) {
        $os.OSArchitecture
    } else {
        [System.Environment]::GetEnvironmentVariable("PROCESSOR_ARCHITECTURE")
    }

    $buildNumber = if ($os -and $os.BuildNumber) {
        $os.BuildNumber
    } else {
        [System.Environment]::OSVersion.Version.Build.ToString()
    }

    $isWin11 = $false
    $buildInt = 0
    if ([int]::TryParse($buildNumber, [ref]$buildInt)) {
        $isWin11 = ($buildInt -ge 22000)
    }

    $cpuName = if ($cpu -and $cpu.Name) {
        $cpu.Name.Trim()
    } else {
        [System.Environment]::GetEnvironmentVariable("PROCESSOR_IDENTIFIER")
    }

    $cores = if ($cpu -and $cpu.NumberOfCores) {
        [int]$cpu.NumberOfCores
    } else {
        [System.Environment]::ProcessorCount
    }

    $logical = if ($cpu -and $cpu.NumberOfLogicalProcessors) {
        [int]$cpu.NumberOfLogicalProcessors
    } else {
        [System.Environment]::ProcessorCount
    }

    return [PSCustomObject]@{
        OSName                 = if ($os -and $os.Caption) { $os.Caption.Trim() } else { "Microsoft Windows" }
        OSVersion              = if ($os -and $os.Version) { $os.Version } else { [System.Environment]::OSVersion.Version.ToString() }
        OSBuild                = $buildNumber
        OSArchitecture         = $osArch
        IsWindows11            = $isWin11
        CPUName                = $cpuName
        CPUCores               = $cores
        CPULogicalProcessors   = $logical
        TotalPhysicalRAM_Bytes = $totalRamBytes
        TotalPhysicalRAM_MB    = $totalRamMB
        TotalPhysicalRAM_GB    = $totalRamGB
        PSVersion              = $PSVersionTable.PSVersion.ToString()
        PSEdition              = $PSVersionTable.PSEdition
        IsElevated             = (Test-IsElevated)
        Hostname               = [System.Environment]::MachineName
    }
}
