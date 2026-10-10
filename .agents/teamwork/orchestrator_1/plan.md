# Master Plan: Windows 11 Laptop Optimizer

## Phase 0: Survey & Specification
- Dispatch 3 Explorers in parallel to explore:
  1. Explorer 1: Current Windows 11 environment, existing files in `laptop_optimizer`, OS APIs for diagnostics (WMI/CIM, powercfg, Get-Counter, memory compression, paging).
  2. Explorer 2: Storage & memory optimization mechanics (safe temp cleanup locations, Dism/cleanmgr/delivery optimization, Optimize-Volume / TRIM, working set trimming via native Windows APIs / psutil / EmptyWorkingSet).
  3. Explorer 3: Architecture for modular CLI, safe rollback/restore points, ASCII menus, logging, and Antigravity custom skill specification.
- Synthesize findings into `PROJECT.md` (Feature Inventory, Architecture, Interface Contracts, Milestones).

## Phase 1: Dual Track Dispatch
- Track A: E2E Testing Suite (Requirements-derived, 4 Tiers, opaque-box test runner).
- Track B: Implementation Track (Milestone decomposition).

## Implementation Milestones
- **M1: Diagnostics & Performance Profiling Module**
  - CPU, RAM, Memory Compression, Paging file, Disk space, Power plan, Startup apps, Scheduled tasks, Top resource processes.
  - Baseline capture & before/after JSON/object comparison.
- **M2: System Resource & Storage Optimization Engine**
  - Safe SSD cleanup (>1GB temporary/caches without touching user data).
  - SSD TRIM (Optimize-Volume).
  - RAM working set trimming & memory compression optimization.
  - Safe background service / telemetry tuning.
- **M3: Standalone CLI, Presets, Safety & Rollback**
  - `optimize.bat` and `Optimize-Laptop.ps1`.
  - Presets: Quick Boost, Deep Clean, Gaming/Performance Mode, Restore Defaults.
  - Non-destructive execution, Dry-run mode, Rollback / restore point.
  - Structured logging.
- **M4: Antigravity Custom Skill & Comprehensive Documentation**
  - Skill definition in standard skill structure (`SKILL.md`, scripts, references).
  - Full operational documentation, usage guide, architectural docs.
- **M5: Final Verification & Adversarial Hardening**
  - Phase 1: Pass 100% of E2E tests (Tiers 1-4).
  - Phase 2: White-box adversarial testing (Tier 5) with Challengers & Reviewers.
  - Forensic integrity audit & victory claim reporting.
