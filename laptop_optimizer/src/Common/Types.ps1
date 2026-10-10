<#
.SYNOPSIS
    Win32 native P/Invoke definitions and memory management types.
.DESCRIPTION
    Compiles and exposes native Win32 APIs for working set trimming and foreground
    window identification across Windows PowerShell 5.1 and PowerShell 7+.
.NOTES
    Part of Milestone M1 (Diagnostics & Performance Profiling).
#>

if (-not ([System.Management.Automation.PSTypeName]'LaptopOptimizer.Win32Native').Type) {
    $csharpCode = @"
using System;
using System.Runtime.InteropServices;

namespace LaptopOptimizer
{
    public static class Win32Native
    {
        // Process access rights
        public const uint PROCESS_QUERY_INFORMATION = 0x0400;
        public const uint PROCESS_SET_QUOTA = 0x0100;

        [DllImport("psapi.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool EmptyWorkingSet(IntPtr hProcess);

        [DllImport("user32.dll")]
        public static extern IntPtr GetForegroundWindow();

        [DllImport("user32.dll", SetLastError = true)]
        public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern IntPtr OpenProcess(uint processAccess, bool bInheritHandle, int processId);

        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool CloseHandle(IntPtr hObject);

        /// <summary>
        /// Retrieves the Process ID of the currently active foreground window.
        /// Returns 0 if no foreground window is present.
        /// </summary>
        public static uint GetActiveProcessId()
        {
            IntPtr hwnd = GetForegroundWindow();
            if (hwnd == IntPtr.Zero) return 0;

            uint pid = 0;
            GetWindowThreadProcessId(hwnd, out pid);
            return pid;
        }

        /// <summary>
        /// Attempts to empty the working set of a target process by PID.
        /// Gracefully handles permission issues and returns false on failure.
        /// </summary>
        public static bool TryEmptyWorkingSetByPid(int pid)
        {
            if (pid <= 4) return false; // Skip System idle and System kernel

            IntPtr hProcess = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_SET_QUOTA, false, pid);
            if (hProcess == IntPtr.Zero) return false;

            try
            {
                return EmptyWorkingSet(hProcess);
            }
            finally
            {
                CloseHandle(hProcess);
            }
        }
    }
}
"@
    Add-Type -TypeDefinition $csharpCode -Language CSharp
}

function Get-LaptopForegroundProcessId {
    <#
    .SYNOPSIS
        Gets the process ID owning the currently active foreground window.
    .OUTPUTS
        [int] Process ID (or 0 if desktop/shell or inaccessible).
    #>
    [CmdletBinding()]
    param()

    try {
        $pidUint = [LaptopOptimizer.Win32Native]::GetActiveProcessId()
        return [int]$pidUint
    } catch {
        return 0
    }
}

function Get-LaptopForegroundWindowHandle {
    <#
    .SYNOPSIS
        Gets the HWND handle of the currently active foreground window.
    .OUTPUTS
        [IntPtr] HWND handle.
    #>
    [CmdletBinding()]
    param()

    try {
        return [LaptopOptimizer.Win32Native]::GetForegroundWindow()
    } catch {
        return [System.IntPtr]::Zero
    }
}

function Invoke-LaptopEmptyWorkingSet {
    <#
    .SYNOPSIS
        Empties the working set for a target process by ID or handle.
    .PARAMETER ProcessId
        The PID of the process to trim.
    .OUTPUTS
        [bool] True if successful, False otherwise.
    #>
    [CmdletBinding(DefaultParameterSetName = "ByPid")]
    param(
        [Parameter(Mandatory = $true, ParameterSetName = "ByPid", Position = 0)]
        [int]$ProcessId
    )

    try {
        return [LaptopOptimizer.Win32Native]::TryEmptyWorkingSetByPid($ProcessId)
    } catch {
        return $false
    }
}
