<#
.SYNOPSIS
    Lightweight, zero-dependency testing framework and test harness for Windows 11 Laptop Optimizer.
.DESCRIPTION
    Provides Describe/Context/It BDD structure, assertion library, test skipping/pending support,
    isolated sandboxing fixtures, and structured test result aggregation.
    Works natively on Windows PowerShell 5.1 and PowerShell 7+ without external modules (like Pester).
.NOTES
    Exclusive ownership: test_writer_e2e
#>

# Global test state
if (-not $global:TestRunnerState) {
    $global:TestRunnerState = [PSCustomObject]@{
        Results         = [System.Collections.Generic.List[psobject]]::new()
        CurrentSuite    = ""
        CurrentContext  = ""
        CurrentTier     = 0
        FilterName      = ""
        FilterTier      = 0
        VerboseOutput   = $false
        Sandboxes       = [System.Collections.Generic.List[string]]::new()
        OriginalFuncs   = @{}
    }
}

function Reset-TestState {
    [CmdletBinding()]
    param()
    $global:TestRunnerState.Results.Clear()
    $global:TestRunnerState.CurrentSuite = ""
    $global:TestRunnerState.CurrentContext = ""
}

# --- BDD Structure ---

function Describe {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$Name,

        [Parameter(Mandatory = $true, Position = 1)]
        [scriptblock]$Fixture,

        [Parameter(Mandatory = $false)]
        [int]$Tier = 0
    )

    $prevSuite = $global:TestRunnerState.CurrentSuite
    $prevTier = $global:TestRunnerState.CurrentTier
    $global:TestRunnerState.CurrentSuite = $Name
    if ($Tier -gt 0) { $global:TestRunnerState.CurrentTier = $Tier }

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ("  SUITE: {0} (Tier {1})" -f $Name, $global:TestRunnerState.CurrentTier) -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan

    try {
        & $Fixture
    } finally {
        $global:TestRunnerState.CurrentSuite = $prevSuite
        $global:TestRunnerState.CurrentTier = $prevTier
    }
}

function Context {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$Name,

        [Parameter(Mandatory = $true, Position = 1)]
        [scriptblock]$Fixture
    )

    $prevContext = $global:TestRunnerState.CurrentContext
    $global:TestRunnerState.CurrentContext = $Name

    Write-Host ""
    Write-Host ("  Context: {0}" -f $Name) -ForegroundColor Yellow

    try {
        & $Fixture
    } finally {
        $global:TestRunnerState.CurrentContext = $prevContext
    }
}

function It {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$Name,

        [Parameter(Mandatory = $true, Position = 1)]
        [scriptblock]$Test
    )

    # Filter checks
    if ($global:TestRunnerState.FilterTier -gt 0 -and $global:TestRunnerState.CurrentTier -ne $global:TestRunnerState.FilterTier) {
        return
    }

    if (-not [string]::IsNullOrEmpty($global:TestRunnerState.FilterName)) {
        $fullName = "{0} - {1}" -f $global:TestRunnerState.CurrentSuite, $Name
        if ($fullName -notmatch $global:TestRunnerState.FilterName) {
            return
        }
    }

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $status = "Passed"
    $errorMessage = ""
    $stackTrace = ""
    $skipReason = ""

    try {
        & $Test
    } catch [System.Management.Automation.RuntimeException] {
        if ($_.Exception.Message -like "__TEST_SKIPPED__:*") {
            $status = "Skipped"
            $skipReason = ($_.Exception.Message -replace "^__TEST_SKIPPED__:\s*", "")
        } else {
            $status = "Failed"
            $errorMessage = $_.Exception.Message
            $stackTrace = $_.ScriptStackTrace
        }
    } catch {
        if ($_.Exception.Message -like "__TEST_SKIPPED__:*") {
            $status = "Skipped"
            $skipReason = ($_.Exception.Message -replace "^__TEST_SKIPPED__:\s*", "")
        } else {
            $status = "Failed"
            $errorMessage = $_.Exception.Message
            $stackTrace = $_.ScriptStackTrace
        }
    } finally {
        $sw.Stop()
    }

    $result = [PSCustomObject]@{
        Tier         = $global:TestRunnerState.CurrentTier
        Suite        = $global:TestRunnerState.CurrentSuite
        Context      = $global:TestRunnerState.CurrentContext
        Name         = $Name
        Status       = $status
        DurationMs   = [math]::Round($sw.Elapsed.TotalMilliseconds, 2)
        ErrorMessage = $errorMessage
        StackTrace   = $stackTrace
        SkipReason   = $skipReason
    }

    $global:TestRunnerState.Results.Add($result)

    switch ($status) {
        "Passed" {
            Write-Host ("    [ PASS ] {0} ({1} ms)" -f $Name, $result.DurationMs) -ForegroundColor Green
        }
        "Skipped" {
            Write-Host ("    [ SKIP ] {0} - {1}" -f $Name, $skipReason) -ForegroundColor DarkYellow
        }
        "Failed" {
            Write-Host ("    [ FAIL ] {0} ({1} ms)" -f $Name, $result.DurationMs) -ForegroundColor Red
            Write-Host ("             Error: {0}" -f $errorMessage) -ForegroundColor DarkRed
            if ($stackTrace) {
                Write-Host ("             Stack: {0}" -f ($stackTrace -split "`n")[0]) -ForegroundColor DarkGray
            }
        }
    }
}

function Skip-Test {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$Reason
    )
    throw ("__TEST_SKIPPED__: " + $Reason)
}

# --- Assertions ---

function Assert-True {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [bool]$Condition,

        [Parameter(Mandatory = $false, Position = 1)]
        [string]$Message = "Expected condition to be True, but was False."
    )

    if (-not $Condition) {
        throw "AssertionFailure: $Message"
    }
}

function Assert-False {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [bool]$Condition,

        [Parameter(Mandatory = $false, Position = 1)]
        [string]$Message = "Expected condition to be False, but was True."
    )

    if ($Condition) {
        throw "AssertionFailure: $Message"
    }
}

function Assert-Equal {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [AllowNull()]
        [object]$Expected,

        [Parameter(Mandatory = $true, Position = 1)]
        [AllowNull()]
        [object]$Actual,

        [Parameter(Mandatory = $false, Position = 2)]
        [string]$Message = ""
    )

    $equal = $false
    if ($null -eq $Expected -and $null -eq $Actual) {
        $equal = $true
    } elseif ($null -eq $Expected -or $null -eq $Actual) {
        $equal = $false
    } elseif ($Expected -is [double] -or $Expected -is [float] -or $Actual -is [double] -or $Actual -is [float]) {
        $equal = ([math]::Abs([double]$Expected - [double]$Actual) -lt 0.0001)
    } else {
        $equal = ($Expected -eq $Actual)
    }

    if (-not $equal) {
        $prefix = if ($Message) { "$Message - " } else { "" }
        throw "AssertionFailure: ${prefix}Expected: <$Expected> but got: <$Actual>"
    }
}

function Assert-NotEqual {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [AllowNull()]
        [object]$Expected,

        [Parameter(Mandatory = $true, Position = 1)]
        [AllowNull()]
        [object]$Actual,

        [Parameter(Mandatory = $false, Position = 2)]
        [string]$Message = ""
    )

    $equal = ($Expected -eq $Actual)
    if ($equal) {
        $prefix = if ($Message) { "$Message - " } else { "" }
        throw "AssertionFailure: ${prefix}Expected value to NOT equal <$Expected>"
    }
}

function Assert-Null {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [AllowNull()]
        [object]$Value,

        [Parameter(Mandatory = $false, Position = 1)]
        [string]$Message = "Expected value to be Null."
    )

    if ($null -ne $Value) {
        throw "AssertionFailure: $Message Value was: <$Value>"
    }
}

function Assert-NotNull {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [AllowNull()]
        [object]$Value,

        [Parameter(Mandatory = $false, Position = 1)]
        [string]$Message = "Expected value to NOT be Null."
    )

    if ($null -eq $Value) {
        throw "AssertionFailure: $Message"
    }
}

function Assert-GreaterThan {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [double]$Value,

        [Parameter(Mandatory = $true, Position = 1)]
        [double]$Threshold,

        [Parameter(Mandatory = $false, Position = 2)]
        [string]$Message = ""
    )

    if ($Value -le $Threshold) {
        $prefix = if ($Message) { "$Message - " } else { "" }
        throw "AssertionFailure: ${prefix}Expected <$Value> to be greater than <$Threshold>."
    }
}

function Assert-LessThan {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [double]$Value,

        [Parameter(Mandatory = $true, Position = 1)]
        [double]$Threshold,

        [Parameter(Mandatory = $false, Position = 2)]
        [string]$Message = ""
    )

    if ($Value -ge $Threshold) {
        $prefix = if ($Message) { "$Message - " } else { "" }
        throw "AssertionFailure: ${prefix}Expected <$Value> to be less than <$Threshold>."
    }
}

function Assert-Match {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$InputString,

        [Parameter(Mandatory = $true, Position = 1)]
        [string]$Pattern,

        [Parameter(Mandatory = $false, Position = 2)]
        [string]$Message = ""
    )

    if ($InputString -notmatch $Pattern) {
        $prefix = if ($Message) { "$Message - " } else { "" }
        throw "AssertionFailure: ${prefix}String '$InputString' does not match pattern '$Pattern'."
    }
}

function Assert-Contains {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [object]$Collection,

        [Parameter(Mandatory = $true, Position = 1)]
        [object]$Item,

        [Parameter(Mandatory = $false, Position = 2)]
        [string]$Message = ""
    )

    $found = $false
    if ($Collection -is [System.Collections.IEnumerable]) {
        foreach ($el in $Collection) {
            if ($el -eq $Item) { $found = $true; break }
        }
    }
    if (-not $found) {
        $prefix = if ($Message) { "$Message - " } else { "" }
        throw "AssertionFailure: ${prefix}Collection does not contain expected item <$Item>."
    }
}

function Assert-Throws {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [scriptblock]$ScriptBlock,

        [Parameter(Mandatory = $false)]
        [string]$ExpectedMessagePattern = "",

        [Parameter(Mandatory = $false)]
        [string]$Message = "Expected scriptblock to throw an exception, but it succeeded."
    )

    $threw = $false
    $actualMessage = ""
    try {
        & $ScriptBlock
    } catch {
        $threw = $true
        $actualMessage = $_.Exception.Message
    }

    if (-not $threw) {
        throw "AssertionFailure: $Message"
    }

    if ($ExpectedMessagePattern -and ($actualMessage -notmatch $ExpectedMessagePattern)) {
        throw "AssertionFailure: Exception message '$actualMessage' did not match expected pattern '$ExpectedMessagePattern'."
    }
}

# --- Sandbox and Fixture Helpers ---

function New-TestSandbox {
    <#
    .SYNOPSIS
        Creates an isolated temporary folder structure simulating temp folders, caches, and backups.
    #>
    [CmdletBinding()]
    param(
        [string]$Prefix = "LaptopOptimizer_TestSandbox_"
    )

    $tempRoot = [System.IO.Path]::GetTempPath()
    $guid = [System.Guid]::NewGuid().ToString("N").Substring(0, 8)
    $sandboxPath = Join-Path $tempRoot ($Prefix + $guid)

    if (Test-Path $sandboxPath) {
        Remove-Item -Path $sandboxPath -Recurse -Force -ErrorAction SilentlyContinue
    }
    New-Item -ItemType Directory -Path $sandboxPath -Force | Out-Null

    # Subdirectories for mock disk cleanup
    New-Item -ItemType Directory -Path (Join-Path $sandboxPath "UserTemp") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $sandboxPath "WindowsTemp") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $sandboxPath "BrowserCache") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $sandboxPath "DeliveryOptimization") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $sandboxPath "CrashDumps") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $sandboxPath "Backups") -Force | Out-Null

    $global:TestRunnerState.Sandboxes.Add($sandboxPath)
    return $sandboxPath
}

function Remove-TestSandbox {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$SandboxPath
    )

    if (Test-Path $SandboxPath) {
        # Clear read-only attributes if any
        Get-ChildItem -Path $SandboxPath -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) {
                $_.Attributes = $_.Attributes -bxor [System.IO.FileAttributes]::ReadOnly
            }
        }
        Remove-Item -Path $SandboxPath -Recurse -Force -ErrorAction SilentlyContinue
    }
    if ($global:TestRunnerState.Sandboxes.Contains($SandboxPath)) {
        [void]$global:TestRunnerState.Sandboxes.Remove($SandboxPath)
    }
}

function Remove-AllSandboxes {
    [CmdletBinding()]
    param()

    foreach ($sb in @($global:TestRunnerState.Sandboxes)) {
        Remove-TestSandbox -SandboxPath $sb
    }
}

function New-MockFile {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [int64]$SizeBytes = 1024,

        [string]$Content = "TEST_FIXTURE_DATA"
    )

    $parent = Split-Path -Parent $Path
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    if ($SizeBytes -gt 4096) {
        # Create sized file using FileStream
        $fs = [System.IO.File]::Create($Path)
        $fs.SetLength($SizeBytes)
        $fs.Close()
    } else {
        Set-Content -Path $Path -Value $Content -NoNewline -Encoding utf8
    }
    return $Path
}

function New-SyntheticSnapshot {
    <#
    .SYNOPSIS
        Creates a synthetic [PSCustomObject] system snapshot conforming exactly to PROJECT.md interface contract.
    #>
    [CmdletBinding()]
    param(
        [double]$FreeRAM_MB = 1200.0,
        [double]$TotalRAM_GB = 7.72,
        [double]$DriveC_Free_GB = 45.0,
        [double]$DriveC_Total_GB = 237.5,
        [string]$ActivePowerScheme = "Balanced (381b4222-f694-41f0-9685-ff5bb260df2e)",
        [int]$ProcessCount = 115,
        [int]$StartupItemsCount = 12,
        [double]$MemoryCompression_MB = 128.5,
        [double]$PageFile_Usage_MB = 450.0,
        [double]$PageFile_Allocated_MB = 12288.0,
        [string]$OS = "Microsoft Windows 11 Home (Build 26200)"
    )

    $totalRamMB = [math]::Round($TotalRAM_GB * 1024.0, 2)
    $freeRamPercent = [math]::Round(($FreeRAM_MB / $totalRamMB) * 100.0, 2)

    return [PSCustomObject]@{
        Timestamp                  = [System.DateTime]::Now
        OS                         = $OS
        FreeRAM_MB                 = $FreeRAM_MB
        TotalRAM_GB                = $TotalRAM_GB
        FreeRAM_Percent            = $freeRamPercent
        MemoryCompression_MB       = $MemoryCompression_MB
        PageFile_Usage_MB          = $PageFile_Usage_MB
        PageFile_Allocated_MB      = $PageFile_Allocated_MB
        DriveC_Free_GB             = $DriveC_Free_GB
        DriveC_Total_GB            = $DriveC_Total_GB
        ActivePowerScheme          = $ActivePowerScheme
        ProcessCount               = $ProcessCount
        StartupItemsCount          = $StartupItemsCount
        TopProcesses               = @(
            [PSCustomObject]@{ Name = "explorer"; Id = 1001; WS_MB = 85.0; CPU_Sec = 12.3; PM_MB = 65.0 },
            [PSCustomObject]@{ Name = "powershell"; Id = 1002; WS_MB = 75.0; CPU_Sec = 5.1; PM_MB = 55.0 }
        )
        TotalRAM_MB                = $totalRamMB
        DriveC_Free_Percent        = [math]::Round(($DriveC_Free_GB / $DriveC_Total_GB) * 100.0, 2)
        DriveC_FileSystem          = "NTFS"
        DriveC_HealthStatus        = "Healthy"
        PageFile_Peak_MB           = [math]::Round($PageFile_Usage_MB * 1.2, 2)
        AutomaticManagedPagefile   = $true
        CPU_Name                   = "Intel(R) N100"
        CPU_Cores                  = 4
        CPU_LogicalCores           = 4
        CPU_LoadPercent            = 15
        IsElevated                 = $false
    }
}

# --- Results Presentation ---

function Get-TestResultsSummary {
    [CmdletBinding()]
    param()

    $results = @($global:TestRunnerState.Results)
    $total = $results.Count
    $passed = @($results | Where-Object { $_.Status -eq "Passed" }).Count
    $failed = @($results | Where-Object { $_.Status -eq "Failed" }).Count
    $skipped = @($results | Where-Object { $_.Status -eq "Skipped" }).Count
    $totalMs = ($results | Measure-Object -Property DurationMs -Sum).Sum

    return [PSCustomObject]@{
        TotalCount     = $total
        PassedCount    = $passed
        FailedCount    = $failed
        SkippedCount   = $skipped
        AllPassed      = ($failed -eq 0)
        TotalDurationMs = [math]::Round($totalMs, 2)
        Results        = $results
    }
}

function Show-TestSummaryTable {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [psobject]$Summary
    )

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor White
    Write-Host "                           TEST EXECUTION SUMMARY                               " -ForegroundColor White
    Write-Host "================================================================================" -ForegroundColor White
    $failColor = if ($Summary.FailedCount -gt 0) { "Red" } else { "DarkGray" }
    $skipColor = if ($Summary.SkippedCount -gt 0) { "DarkYellow" } else { "DarkGray" }

    Write-Host ("  Total Tests Run : {0}" -f $Summary.TotalCount) -ForegroundColor White
    Write-Host ("  Passed          : {0}" -f $Summary.PassedCount) -ForegroundColor Green
    Write-Host ("  Failed          : {0}" -f $Summary.FailedCount) -ForegroundColor $failColor
    Write-Host ("  Skipped/Pending : {0}" -f $Summary.SkippedCount) -ForegroundColor $skipColor
    Write-Host ("  Execution Time  : {0:N2} ms" -f $Summary.TotalDurationMs) -ForegroundColor Gray
    Write-Host "--------------------------------------------------------------------------------" -ForegroundColor White

    if ($Summary.FailedCount -gt 0) {
        Write-Host "  FAILED TESTS:" -ForegroundColor Red
        $failures = @($Summary.Results | Where-Object { $_.Status -eq "Failed" })
        foreach ($f in $failures) {
            Write-Host ("  - [Tier {0}] {1} :: {2}" -f $f.Tier, $f.Suite, $f.Name) -ForegroundColor Red
            Write-Host ("      {0}" -f $f.ErrorMessage) -ForegroundColor DarkRed
        }
        Write-Host "================================================================================" -ForegroundColor Red
        Write-Host "  OVERALL SUITE STATUS: FAILED" -ForegroundColor Red
        Write-Host "================================================================================" -ForegroundColor Red
    } else {
        Write-Host "================================================================================" -ForegroundColor Green
        Write-Host "  OVERALL SUITE STATUS: ALL TESTS PASSED (0 FAILURES)" -ForegroundColor Green
        Write-Host "================================================================================" -ForegroundColor Green
    }
}
