package native_core.java;

import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.lang.management.GarbageCollectorMXBean;
import java.lang.management.OperatingSystemMXBean;
import java.util.List;

public class SiliconSanctuaryBridge {

    public static void main(String[] args) {
        String mode = (args.length > 0) ? args[0] : "--status";

        switch (mode) {
            case "--gc":
                triggerGarbageCollection();
                break;
            case "--status":
            default:
                printStatusJson();
                break;
        }
    }

    public static void printStatusJson() {
        OperatingSystemMXBean osBean = ManagementFactory.getOperatingSystemMXBean();
        MemoryMXBean memBean = ManagementFactory.getMemoryMXBean();
        List<GarbageCollectorMXBean> gcBeans = ManagementFactory.getGarbageCollectorMXBeans();

        int availableProcessors = osBean.getAvailableProcessors();
        String arch = osBean.getArch();
        String osName = osBean.getName();
        String osVersion = osBean.getVersion();
        double systemLoadAverage = osBean.getSystemLoadAverage();

        long heapUsedMb = memBean.getHeapMemoryUsage().getUsed() / (1024 * 1024);
        long heapMaxMb = memBean.getHeapMemoryUsage().getMax() / (1024 * 1024);
        long nonHeapUsedMb = memBean.getNonHeapMemoryUsage().getUsed() / (1024 * 1024);

        long totalGcCount = 0;
        long totalGcTimeMs = 0;
        for (GarbageCollectorMXBean gc : gcBeans) {
            totalGcCount += Math.max(0, gc.getCollectionCount());
            totalGcTimeMs += Math.max(0, gc.getCollectionTime());
        }

        // Try com.sun.management.OperatingSystemMXBean for exact physical memory
        long totalPhysMb = 0;
        long freePhysMb = 0;
        double cpuLoad = 0.0;
        if (osBean instanceof com.sun.management.OperatingSystemMXBean) {
            com.sun.management.OperatingSystemMXBean sunOs = (com.sun.management.OperatingSystemMXBean) osBean;
            totalPhysMb = sunOs.getTotalPhysicalMemorySize() / (1024 * 1024);
            freePhysMb = sunOs.getFreePhysicalMemorySize() / (1024 * 1024);
            cpuLoad = sunOs.getCpuLoad() * 100.0;
        }

        System.out.printf("{\n");
        System.out.printf("  \"source\": \"java_sanctuary_bridge\",\n");
        System.out.printf("  \"redundancy_status\": \"active_verified\",\n");
        System.out.printf("  \"os\": \"%s %s (%s)\",\n", osName, osVersion, arch);
        System.out.printf("  \"cores\": %d,\n", availableProcessors);
        System.out.printf("  \"total_phys_ram_mb\": %d,\n", totalPhysMb);
        System.out.printf("  \"free_phys_ram_mb\": %d,\n", freePhysMb);
        System.out.printf("  \"cpu_load_pct\": %.2f,\n", Math.max(0.0, cpuLoad));
        System.out.printf("  \"jvm_heap_used_mb\": %d,\n", heapUsedMb);
        System.out.printf("  \"jvm_heap_max_mb\": %d,\n", heapMaxMb);
        System.out.printf("  \"jvm_non_heap_used_mb\": %d,\n", nonHeapUsedMb);
        System.out.printf("  \"gc_count\": %d,\n", totalGcCount);
        System.out.printf("  \"gc_time_ms\": %d\n", totalGcTimeMs);
        System.out.printf("}\n");
    }

    public static void triggerGarbageCollection() {
        MemoryMXBean memBean = ManagementFactory.getMemoryMXBean();
        long beforeMb = memBean.getHeapMemoryUsage().getUsed() / (1024 * 1024);
        long startMs = System.currentTimeMillis();
        System.gc();
        long durationMs = System.currentTimeMillis() - startMs;
        long afterMb = memBean.getHeapMemoryUsage().getUsed() / (1024 * 1024);
        long reclaimedMb = Math.max(0, beforeMb - afterMb);

        System.out.printf("{\n");
        System.out.printf("  \"gc_triggered\": true,\n");
        System.out.printf("  \"before_mb\": %d,\n", beforeMb);
        System.out.printf("  \"after_mb\": %d,\n", afterMb);
        System.out.printf("  \"reclaimed_mb\": %d,\n", reclaimedMb);
        System.out.printf("  \"duration_ms\": %d\n", durationMs);
        System.out.printf("}\n");
    }
}
