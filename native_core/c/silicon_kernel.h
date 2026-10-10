#ifndef SILICON_KERNEL_H
#define SILICON_KERNEL_H

#include <windows.h>
#include <psapi.h>

#ifdef __cplusplus
extern "C" {
#endif

#if defined(SILICON_KERNEL_EXPORTS)
#define KERNEL_API __declspec(dllexport)
#elif defined(SILICON_KERNEL_STATIC)
#define KERNEL_API
#else
#define KERNEL_API __declspec(dllimport)
#endif

typedef struct {
    DWORD dwLength;
    DWORD memoryLoad;
    DWORDLONG totalPhysMb;
    DWORDLONG availPhysMb;
    DWORDLONG totalPageFileMb;
    DWORDLONG availPageFileMb;
    DWORDLONG processWorkingSetMb;
    DWORDLONG processPrivateMb;
} SiliconMemoryStats;

typedef struct {
    DWORD processCount;
    DWORD trimmedCount;
    DWORDLONG bytesReclaimed;
    double executionDurationMs;
} SiliconTrimResult;

// Memory Management
KERNEL_API int Silicon_GetMemoryStats(SiliconMemoryStats* stats);
KERNEL_API int Silicon_TrimProcessWorkingSet(DWORD pid);
KERNEL_API SiliconTrimResult Silicon_CompactWorkingSets(void);

// CPU Core & Power Throttling (Intel Gracemont / Alder Lake-N)
KERNEL_API int Silicon_SetProcessAffinity(DWORD pid, DWORD_PTR affinityMask);
KERNEL_API int Silicon_SetPowerThrottling(DWORD pid, int enableThrottling);

// Storage & SSD TRIM
KERNEL_API int Silicon_TriggerDriveTrim(char driveLetter);

#ifdef __cplusplus
}
#endif

#endif // SILICON_KERNEL_H
