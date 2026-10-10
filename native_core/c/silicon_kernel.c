#define SILICON_KERNEL_EXPORTS
#include "silicon_kernel.h"
#include <stdio.h>
#include <stdlib.h>
#include <tlhelp32.h>

#ifndef PROCESS_POWER_THROTTLING_CURRENT_VERSION
#define PROCESS_POWER_THROTTLING_CURRENT_VERSION 1
#define PROCESS_POWER_THROTTLING_EXECUTION_SPEED 0x1
typedef struct _PROCESS_POWER_THROTTLING_STATE {
    ULONG Version;
    ULONG ControlMask;
    ULONG StateMask;
} PROCESS_POWER_THROTTLING_STATE, *PPROCESS_POWER_THROTTLING_STATE;
#endif

#ifndef ProcessPowerThrottling
#define ProcessPowerThrottling ((PROCESS_INFORMATION_CLASS)4)
#endif

// Fetch system-wide and current-process memory metrics
KERNEL_API int Silicon_GetMemoryStats(SiliconMemoryStats* stats) {
    if (!stats) return 0;

    MEMORYSTATUSEX memStatus;
    memStatus.dwLength = sizeof(MEMORYSTATUSEX);
    if (!GlobalMemoryStatusEx(&memStatus)) {
        return 0;
    }

    stats->dwLength = sizeof(SiliconMemoryStats);
    stats->memoryLoad = memStatus.dwMemoryLoad;
    stats->totalPhysMb = memStatus.ullTotalPhys / (1024 * 1024);
    stats->availPhysMb = memStatus.ullAvailPhys / (1024 * 1024);
    stats->totalPageFileMb = memStatus.ullTotalPageFile / (1024 * 1024);
    stats->availPageFileMb = memStatus.ullAvailPageFile / (1024 * 1024);

    // Current process memory metrics
    HANDLE hCur = GetCurrentProcess();
    PROCESS_MEMORY_COUNTERS_EX pmc;
    if (GetProcessMemoryInfo(hCur, (PROCESS_MEMORY_COUNTERS*)&pmc, sizeof(pmc))) {
        stats->processWorkingSetMb = pmc.WorkingSetSize / (1024 * 1024);
        stats->processPrivateMb = pmc.PrivateUsage / (1024 * 1024);
    } else {
        stats->processWorkingSetMb = 0;
        stats->processPrivateMb = 0;
    }

    return 1;
}

// Trim working set for a specific process PID
KERNEL_API int Silicon_TrimProcessWorkingSet(DWORD pid) {
    HANDLE hProcess = NULL;
    if (pid == 0 || pid == GetCurrentProcessId()) {
        hProcess = GetCurrentProcess();
    } else {
        hProcess = OpenProcess(PROCESS_SET_QUOTA | PROCESS_QUERY_LIMITED_INFORMATION, FALSE, pid);
    }

    if (!hProcess) {
        return 0;
    }

    BOOL success = EmptyWorkingSet(hProcess);
    if (hProcess != GetCurrentProcess()) {
        CloseHandle(hProcess);
    }
    return success ? 1 : 0;
}

// Compact working sets across user-space processes safely
KERNEL_API SiliconTrimResult Silicon_CompactWorkingSets(void) {
    SiliconTrimResult result = {0, 0, 0, 0.0};
    LARGE_INTEGER freq, start, end;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&start);

    // First trim the current process
    HANDLE hCur = GetCurrentProcess();
    PROCESS_MEMORY_COUNTERS beforeCur, afterCur;
    if (GetProcessMemoryInfo(hCur, &beforeCur, sizeof(beforeCur))) {
        EmptyWorkingSet(hCur);
        if (GetProcessMemoryInfo(hCur, &afterCur, sizeof(afterCur))) {
            if (beforeCur.WorkingSetSize > afterCur.WorkingSetSize) {
                result.bytesReclaimed += (beforeCur.WorkingSetSize - afterCur.WorkingSetSize);
            }
        }
    }
    result.processCount++;
    result.trimmedCount++;

    // Iterate through process snapshot
    HANDLE hSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnap != INVALID_HANDLE_VALUE) {
        PROCESSENTRY32 pe;
        pe.dwSize = sizeof(PROCESSENTRY32);
        if (Process32First(hSnap, &pe)) {
            do {
                if (pe.th32ProcessID <= 4) continue; // Skip Idle and System
                if (pe.th32ProcessID == GetCurrentProcessId()) continue;

                result.processCount++;

                HANDLE hProc = OpenProcess(PROCESS_SET_QUOTA | PROCESS_QUERY_INFORMATION, FALSE, pe.th32ProcessID);
                if (hProc) {
                    PROCESS_MEMORY_COUNTERS beforePMC, afterPMC;
                    if (GetProcessMemoryInfo(hProc, &beforePMC, sizeof(beforePMC))) {
                        if (EmptyWorkingSet(hProc)) {
                            result.trimmedCount++;
                            if (GetProcessMemoryInfo(hProc, &afterPMC, sizeof(afterPMC))) {
                                if (beforePMC.WorkingSetSize > afterPMC.WorkingSetSize) {
                                    result.bytesReclaimed += (beforePMC.WorkingSetSize - afterPMC.WorkingSetSize);
                                }
                            }
                        }
                    }
                    CloseHandle(hProc);
                }
            } while (Process32Next(hSnap, &pe));
        }
        CloseHandle(hSnap);
    }

    QueryPerformanceCounter(&end);
    result.executionDurationMs = (double)(end.QuadPart - start.QuadPart) * 1000.0 / (double)freq.QuadPart;
    return result;
}

// Set CPU Core Affinity Mask (0x1 = Core 0, 0x3 = Cores 0+1, 0xF = All 4 Gracemont Cores)
KERNEL_API int Silicon_SetProcessAffinity(DWORD pid, DWORD_PTR affinityMask) {
    HANDLE hProc = (pid == 0 || pid == GetCurrentProcessId()) 
        ? GetCurrentProcess() 
        : OpenProcess(PROCESS_SET_INFORMATION | PROCESS_QUERY_INFORMATION, FALSE, pid);

    if (!hProc) return 0;

    BOOL success = SetProcessAffinityMask(hProc, affinityMask);
    if (hProc != GetCurrentProcess()) {
        CloseHandle(hProc);
    }
    return success ? 1 : 0;
}

// Set EcoQoS Power Throttling on Intel Alder Lake-N E-cores
KERNEL_API int Silicon_SetPowerThrottling(DWORD pid, int enableThrottling) {
    HANDLE hProc = (pid == 0 || pid == GetCurrentProcessId())
        ? GetCurrentProcess()
        : OpenProcess(PROCESS_SET_INFORMATION | PROCESS_QUERY_INFORMATION, FALSE, pid);

    if (!hProc) return 0;

    typedef BOOL (WINAPI *PFN_SetProcessInformation)(HANDLE, int, LPVOID, DWORD);
    HMODULE hK32 = GetModuleHandleA("kernel32.dll");
    if (!hK32) {
        if (hProc != GetCurrentProcess()) CloseHandle(hProc);
        return 0;
    }

    PFN_SetProcessInformation pSetProcessInformation = (PFN_SetProcessInformation)GetProcAddress(hK32, "SetProcessInformation");
    if (!pSetProcessInformation) {
        if (hProc != GetCurrentProcess()) CloseHandle(hProc);
        return 0;
    }

    PROCESS_POWER_THROTTLING_STATE powerThrottling;
    RtlZeroMemory(&powerThrottling, sizeof(powerThrottling));
    powerThrottling.Version = PROCESS_POWER_THROTTLING_CURRENT_VERSION;
    powerThrottling.ControlMask = PROCESS_POWER_THROTTLING_EXECUTION_SPEED;
    powerThrottling.StateMask = enableThrottling ? PROCESS_POWER_THROTTLING_EXECUTION_SPEED : 0;

    BOOL success = pSetProcessInformation(hProc, 4, &powerThrottling, sizeof(powerThrottling));
    if (hProc != GetCurrentProcess()) {
        CloseHandle(hProc);
    }
    return success ? 1 : 0;
}

// Drive TRIM dispatch via defrag or FSCTL
KERNEL_API int Silicon_TriggerDriveTrim(char driveLetter) {
    char cmd[128];
    snprintf(cmd, sizeof(cmd), "defrag.exe %c: /L /U > nul 2>&1", driveLetter);
    int ret = system(cmd);
    return (ret == 0) ? 1 : 0;
}
