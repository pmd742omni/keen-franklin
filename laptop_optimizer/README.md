# Windows 11 Laptop Performance Optimizer

A lightweight, non-destructive system tuning toolkit engineered specifically for low-TDP and quad-core Windows 11 laptops (such as the Intel N100, Core i3/i5, and AMD Ryzen mobile series).

---

## Quick Start (How to Run When Antigravity Is Not Available)

### Option 1: Double-Click Launcher
Simply double-click `optimize.bat` in this folder. It will prompt for administrative privileges (optional, but recommended for full SSD TRIM and service control) and open the interactive menu:

```text
=================================================================
         WINDOWS 11 LAPTOP OPTIMIZER & PERFORMANCE SUITE        
         Tailored for Intel N-Series / Core / AMD Mobile CPUs    
=================================================================

  [1] Quick Boost             (Memory purge + Cache clean + UI speedup)
  [2] Deep Clean & SSD TRIM   (Full disk reclamation + NVMe/SSD block trim)
  [3] Full System Optimize    (All optimizations + Telemetry & Power tuning)
  [4] Run Performance Audit   (Live CPU, RAM, Disk & Process metrics)
  [5] Restore Previous State  (Rollback settings to backup)
  [6] Exit
```

### Option 2: PowerShell Terminal
You can run any preset directly from PowerShell:

```powershell
# Run full optimization
powershell -ExecutionPolicy Bypass -File .\Optimize-Laptop.ps1 -Preset FullOptimize

# Run quick memory and cache boost
powershell -ExecutionPolicy Bypass -File .\Optimize-Laptop.ps1 -Preset QuickBoost

# Run deep clean and SSD TRIM
powershell -ExecutionPolicy Bypass -File .\Optimize-Laptop.ps1 -Preset DeepClean

# View live system diagnostics and hardware metrics
powershell -ExecutionPolicy Bypass -File .\Optimize-Laptop.ps1 -Preset Benchmark

# Restore original settings (Undo)
powershell -ExecutionPolicy Bypass -File .\Optimize-Laptop.ps1 -Preset Restore
```

---

## What Does the Optimizer Do?

| Module | What It Optimizes | Why It Matters on Intel N100 / 8GB RAM |
|---|---|---|
| **Storage Reclamation** | Purges `$env:TEMP`, `C:\Windows\Temp`, SoftwareDistribution download cache, WER crash reports. | Intel N100 laptops usually have 128GB–256GB SSDs. Free space >15% is crucial to prevent SSD write degradation. |
| **SSD Block TRIM** | Issues `Optimize-Volume -DriveLetter C -ReTrim`. | Cleans discarded flash memory blocks so future writes are fast and SSD wear leveling operates efficiently. |
| **Memory Pressure Relief** | Cleans idle working sets using Windows API `EmptyWorkingSet` and triggers GC. | With 8GB RAM at 95% utilization, Windows constantly compresses memory in background threads, lagging the 4-core CPU. |
| **Telemetry & Bloat** | Disables `Microsoft Compatibility Appraiser`, `Consolidator`, `UsbCeip`, `DiagTrack`. | The Compatibility Appraiser is notorious for spiking quad-core CPUs to 100% and freezing the UI during background scans. |
| **UI Latency Tuning** | Sets `MenuShowDelay` from 400ms to 10ms, disables slow minimize/maximize animations. | Eliminates artificial animation delays, making the desktop and menus feel instantaneous on integrated Intel UHD Graphics. |
| **Edge Background Boost** | Disables pre-launching Edge background instances on boot. | Prevents ~200MB–300MB of RAM from being locked up on startup. |
| **Power Responsiveness** | Activates High Performance or sets processor throttle minimum/maximum bounds. | Prevents the CPU governor from aggressively dropping clock speeds to 800MHz during interactive clicks. |
| **Rollback Safety** | Automatically writes `backup_state.json` before touching settings; one-click restore. | Restores power plans, registry keys, and scheduled tasks back to defaults anytime with `restore.bat`. |

---

## File Structure

- `optimize.bat`: One-click double-clickable launcher with UAC elevation.
- `restore.bat`: One-click rollback launcher to revert to original state.
- `Optimize-Laptop.ps1`: The core PowerShell optimization engine.
- `benchmark.ps1`: Performance and hardware diagnostic benchmark script.
- `backup_state.json`: Saved registry and power plan configuration backup.
- `baseline_benchmark.json`: Captured initial state before optimization.
- `optimization.log`: Real-time timestamped audit log of all operations performed.
