---
name: laptop-optimizer
description: >-
  Automated diagnostics, disk reclamation, SSD TRIM, working set memory relief,
  and responsiveness tuning for Windows 11 laptops, with specialized presets for
  low-TDP quad-core systems (such as Intel N100, Core i3/i5, and AMD Ryzen mobile).
---

# Laptop Optimizer Skill

This skill provides a standardized, battle-tested operational guide for analyzing and boosting the performance of Windows 11 laptops directly from the terminal or using standalone scripts.

## When to Use This Skill
- The user reports laptop sluggishness, thermal throttling, stuttering UI animations, or high fan noise.
- Windows memory pressure exceeds 80–90% or `Memory Compression` process is consuming high CPU.
- Primary drive (C:) free space drops below 20% (impairing SSD write caching and virtual memory swap).
- Scheduled background tasks (such as `Microsoft Compatibility Appraiser`) are causing periodic freezes.

---

## Architecture & Tool Location
All executable scripts are housed in:
`c:/Users/ignaz/antigravity/keen-franklin/laptop_optimizer/`

- `optimize.bat`: One-click interactive launcher with UAC administrator elevation.
- `restore.bat`: One-click rollback script to restore original settings and scheduled tasks.
- `Optimize-Laptop.ps1`: Primary PowerShell optimization engine with CLI parameters.
- `benchmark.ps1`: Hardware and metric diagnostic collector.
- `backup_state.json`: Saved state snapshot created prior to any modifications.
- `optimization.log`: Timestamped audit trail of all operations.

---

## Automated Workflow

### Step 1: Run Diagnostic Audit
Collect live metrics on CPU load, memory utilization, disk free space, and top resource hogs:
```powershell
powershell -ExecutionPolicy Bypass -File c:\Users\ignaz\antigravity\keen-franklin\laptop_optimizer\benchmark.ps1 -OutputFile baseline.json
```

### Step 2: Execute Optimization Profiles
Run the appropriate preset based on system state:

#### A. Quick Boost (Daily/Weekly Tune-up)
Cleans temporary caches, trims idle process working sets, and tunes UI latency:
```powershell
powershell -ExecutionPolicy Bypass -File c:\Users\ignaz\antigravity\keen-franklin\laptop_optimizer\Optimize-Laptop.ps1 -Preset QuickBoost
```

#### B. Deep Clean & SSD TRIM (Storage Recovery)
Purges Windows Update cache, crash reports, delivery optimization cache, and issues SSD re-trim:
```powershell
powershell -ExecutionPolicy Bypass -File c:\Users\ignaz\antigravity\keen-franklin\laptop_optimizer\Optimize-Laptop.ps1 -Preset DeepClean
```

#### C. Full System Optimization (Maximum Performance)
Applies all cleanup, SSD TRIM, memory relief, telemetry suppression, UI instant opening, and power plan tuning:
```powershell
powershell -ExecutionPolicy Bypass -File c:\Users\ignaz\antigravity\keen-franklin\laptop_optimizer\Optimize-Laptop.ps1 -Preset FullOptimize
```

---

## Safe Rollback & Recovery
To revert all registry keys, power schemes, and scheduled tasks back to their original states:
```powershell
powershell -ExecutionPolicy Bypass -File c:\Users\ignaz\antigravity\keen-franklin\laptop_optimizer\Optimize-Laptop.ps1 -Preset Restore
```
Or execute `restore.bat` from Windows Explorer.
