#include <stdio.h>
#include <string.h>
#include "silicon_kernel.h"

int main(int argc, char* argv[]) {
    if (argc < 2 || strcmp(argv[1], "--status") == 0) {
        SiliconMemoryStats stats;
        if (Silicon_GetMemoryStats(&stats)) {
            printf("{\n");
            printf("  \"status\": \"ok\",\n");
            printf("  \"memory_load_pct\": %lu,\n", stats.memoryLoad);
            printf("  \"total_phys_mb\": %llu,\n", stats.totalPhysMb);
            printf("  \"avail_phys_mb\": %llu,\n", stats.availPhysMb);
            printf("  \"process_working_set_mb\": %llu,\n", stats.processWorkingSetMb);
            printf("  \"process_private_mb\": %llu\n", stats.processPrivateMb);
            printf("}\n");
            return 0;
        } else {
            fprintf(stderr, "{\"status\": \"error\", \"message\": \"Failed to read memory metrics\"}\n");
            return 1;
        }
    }

    if (strcmp(argv[1], "--compact") == 0) {
        SiliconTrimResult res = Silicon_CompactWorkingSets();
        printf("{\n");
        printf("  \"status\": \"compacted\",\n");
        printf("  \"scanned_processes\": %lu,\n", res.processCount);
        printf("  \"trimmed_processes\": %lu,\n", res.trimmedCount);
        printf("  \"reclaimed_mb\": %.2f,\n", (double)res.bytesReclaimed / (1024.0 * 1024.0));
        printf("  \"duration_ms\": %.3f\n", res.executionDurationMs);
        printf("}\n");
        return 0;
    }

    if (strcmp(argv[1], "--trim-pid") == 0 && argc >= 3) {
        DWORD pid = (DWORD)atoi(argv[2]);
        int ok = Silicon_TrimProcessWorkingSet(pid);
        printf("{\"pid\": %lu, \"trimmed\": %s}\n", pid, ok ? "true" : "false");
        return ok ? 0 : 1;
    }

    if (strcmp(argv[1], "--trim-drive") == 0 && argc >= 3) {
        char drive = argv[2][0];
        int ok = Silicon_TriggerDriveTrim(drive);
        printf("{\"drive\": \"%c:\", \"trimmed\": %s}\n", drive, ok ? "true" : "false");
        return ok ? 0 : 1;
    }

    printf("Usage: silicon_kernel_cli.exe [--status | --compact | --trim-pid <pid> | --trim-drive <drive>]\n");
    return 1;
}
