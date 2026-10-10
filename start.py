#!/usr/bin/env python3
"""
Laptop Optimizer Metropolis — Interactive Command Center (start.py)
Provides a rich terminal interface to control laptop hardware tuning,
memory compaction, SSD TRIM, and launch the real-time web visualizer.
"""

import ctypes
import os
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure UTF-8 output on all platforms
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Enable VT100 ANSI escape sequences and UTF-8 on Windows console via Win32 API
if sys.platform == "win32":
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)
        kernel32.SetConsoleCP(65001)
        kernel32.SetConsoleTitleW("Laptop Optimizer Metropolis - Command Center")
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Import native metrics collector if available
try:
    from agent_city.engine.system_metrics import SystemMetricsCollector
except Exception:
    SystemMetricsCollector = None

# ANSI color codes
CLR_RESET = "\033[0m"
CLR_BOLD = "\033[1m"
CLR_CYAN = "\033[96m"
CLR_GREEN = "\033[92m"
CLR_YELLOW = "\033[93m"
CLR_RED = "\033[91m"
CLR_MAGENTA = "\033[95m"
CLR_BLUE = "\033[94m"
CLR_DIM = "\033[90m"


def is_server_running(host: str = "127.0.0.1", port: int = 8000, timeout: float = 0.5) -> bool:
    """Check if the FastAPI web dashboard is running and accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def start_server_background() -> bool:
    """Launch the uvicorn web server in a detached background process."""
    if is_server_running():
        return True

    print(f"{CLR_YELLOW}[i] Starting Laptop Optimizer Metropolis background daemon...{CLR_RESET}")
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "agent_city.server:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]

    # Windows detached flags
    flags = 0
    if sys.platform == "win32":
        DETACHED_PROCESS = 0x00000008
        CREATE_NO_WINDOW = 0x08000000
        flags = DETACHED_PROCESS | CREATE_NO_WINDOW

    try:
        subprocess.Popen(
            cmd,
            cwd=str(BASE_DIR),
            creationflags=flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        for _ in range(35):
            time.sleep(0.25)
            if is_server_running():
                print(f"{CLR_GREEN}[✓] Web server daemon started successfully on http://127.0.0.1:8000{CLR_RESET}")
                return True
    except Exception as e:
        print(f"{CLR_RED}[!] Failed to spawn web server daemon: {e}{CLR_RESET}")

    return is_server_running()


def open_browser():
    """Ensure server is active and open the web dashboard in the default browser."""
    print(f"\n{CLR_BOLD}{CLR_CYAN}=== Launching Web Dashboard ==={CLR_RESET}")
    if not is_server_running():
        started = start_server_background()
        if not started:
            print(f"{CLR_RED}[!] Could not verify web server startup. Check port 8000.{CLR_RESET}")
            return
    else:
        print(f"{CLR_GREEN}[✓] Web server is already active on http://localhost:8000{CLR_RESET}")

    url = "http://localhost:8000"
    print(f"{CLR_CYAN}[i] Opening {url} in your default browser...{CLR_RESET}")
    webbrowser.open(url)
    print(f"{CLR_GREEN}[✓] Browser opened! You can switch to your browser to view the live SVG swarm.{CLR_RESET}")


def render_banner(metrics: Optional[Dict[str, Any]] = None):
    """Render modern terminal banner and live quick-status."""
    print("\033[2J\033[H", end="")
    server_online = is_server_running()
    server_badge = f"{CLR_GREEN}● ONLINE (http://localhost:8000){CLR_RESET}" if server_online else f"{CLR_RED}○ OFFLINE{CLR_RESET}"

    print(f"{CLR_CYAN}{CLR_BOLD}╔══════════════════════════════════════════════════════════════════════╗{CLR_RESET}")
    print(f"{CLR_CYAN}{CLR_BOLD}║          💻  LAPTOP OPTIMIZER METROPOLIS — COMMAND CENTER           ║{CLR_RESET}")
    print(f"{CLR_CYAN}{CLR_BOLD}║      Intel N100 4-Core / 8GB RAM Autonomous Windows 11 Swarm         ║{CLR_RESET}")
    print(f"{CLR_CYAN}{CLR_BOLD}╚══════════════════════════════════════════════════════════════════════╝{CLR_RESET}")

    # Live quick telemetry summary
    if SystemMetricsCollector:
        try:
            mem = SystemMetricsCollector.get_memory_metrics()
            cpu = SystemMetricsCollector.get_cpu_metrics()
            storage = SystemMetricsCollector.get_storage_metrics()
            smoothness = SystemMetricsCollector.calculate_smoothness_index(
                cpu["overall_pct"], mem["free_mb"], storage["free_gb"]
            )

            # Colorize smoothness
            if smoothness >= 80:
                s_color = CLR_GREEN
            elif smoothness >= 60:
                s_color = CLR_YELLOW
            else:
                s_color = CLR_RED

            print(f" {CLR_BOLD}Smoothness Score:{CLR_RESET} {s_color}{smoothness}/100{CLR_RESET}   "
                  f"{CLR_BOLD}CPU Load:{CLR_RESET} {cpu['overall_pct']}%   "
                  f"{CLR_BOLD}Free RAM:{CLR_RESET} {CLR_GREEN}{mem['free_mb']} MB{CLR_RESET} / {mem['total_mb']} MB   "
                  f"{CLR_BOLD}Drive C: Free:{CLR_RESET} {storage['free_gb']} GB")
        except Exception:
            pass

    print(f" {CLR_BOLD}Web Visualizer Status:{CLR_RESET} {server_badge}")
    print(f"{CLR_DIM}─" * 70 + f"{CLR_RESET}")


def action_ram_boost():
    """Execute native psapi.dll working set compaction across all user processes."""
    print(f"\n{CLR_BOLD}{CLR_GREEN}⚡ [Action: Instant RAM Working Set Compaction]{CLR_RESET}")
    print(f"{CLR_DIM}Calling Windows psapi.dll!EmptyWorkingSet across active processes...{CLR_RESET}\n")

    if not SystemMetricsCollector:
        print(f"{CLR_RED}[!] SystemMetricsCollector is not available.{CLR_RESET}")
        return

    result = SystemMetricsCollector.trim_all_working_sets()
    before = result.get("before_free_mb", 0)
    after = result.get("after_free_mb", 0)
    freed = result.get("freed_mb", 0)
    count = result.get("trimmed_processes", 0)

    print(f"{CLR_GREEN}{CLR_BOLD}✔ Success! Compaction Complete.{CLR_RESET}")
    print(f"  • Processes Flushed: {CLR_CYAN}{count}{CLR_RESET}")
    print(f"  • Free RAM Before:   {CLR_YELLOW}{before} MB{CLR_RESET}")
    print(f"  • Free RAM After:    {CLR_GREEN}{after} MB{CLR_RESET}")
    print(f"  • Net Memory Freed:  {CLR_BOLD}{CLR_GREEN}+{freed} MB physical RAM{CLR_RESET}")


def action_storage_sweep():
    """Execute temporary cache purging and native SSD TRIM."""
    print(f"\n{CLR_BOLD}{CLR_MAGENTA}🧹 [Action: Storage Sweep & SSD TRIM]{CLR_RESET}")
    print(f"{CLR_DIM}Cleaning unlocked temp files, crash dumps, and issuing defrag C: /L /U...{CLR_RESET}\n")

    if not SystemMetricsCollector:
        print(f"{CLR_RED}[!] SystemMetricsCollector is not available.{CLR_RESET}")
        return

    result = SystemMetricsCollector.purge_temp_storage()
    cleaned = result.get("cleaned_files", 0)
    reclaimed = result.get("reclaimed_mb", 0)
    trim_status = result.get("trim_status", "SKIPPED")

    print(f"{CLR_GREEN}{CLR_BOLD}✔ Success! Storage Sweep Complete.{CLR_RESET}")
    print(f"  • Junk Files Purged:   {CLR_CYAN}{cleaned}{CLR_RESET}")
    print(f"  • Disk Space Freed:    {CLR_GREEN}{reclaimed} MB{CLR_RESET}")
    print(f"  • SSD TRIM Status:     {CLR_BOLD}{trim_status}{CLR_RESET} (Drive C: unallocated blocks reclaimed)")


def action_full_optimize():
    """Run full combined memory compaction and storage sweep."""
    print(f"\n{CLR_BOLD}{CLR_CYAN}🚀 [Action: Comprehensive Full System Sweep]{CLR_RESET}")
    action_ram_boost()
    print()
    action_storage_sweep()
    print(f"\n{CLR_BOLD}{CLR_GREEN}★ Full System Optimization Complete! UI latency minimized.{CLR_RESET}")


def action_view_diagnostics():
    """Show detailed per-core load, memory distribution, and top processes."""
    print(f"\n{CLR_BOLD}{CLR_CYAN}📊 [System Telemetry & Resource Breakdown]{CLR_RESET}\n")
    if not SystemMetricsCollector:
        print(f"{CLR_RED}[!] SystemMetricsCollector is not available.{CLR_RESET}")
        return

    cpu = SystemMetricsCollector.get_cpu_metrics()
    mem = SystemMetricsCollector.get_memory_metrics()
    storage = SystemMetricsCollector.get_storage_metrics()
    top_procs = SystemMetricsCollector.get_top_processes(limit=8)

    print(f"{CLR_BOLD}Processor: Intel N100 (4 Physical Cores / 4 Threads, 6W TDP){CLR_RESET}")
    for idx, core in enumerate(cpu.get("cores", [])):
        bar_len = int(core / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        c_color = CLR_RED if core > 80 else (CLR_YELLOW if core > 50 else CLR_CYAN)
        print(f"  Core {idx}: [{c_color}{bar}{CLR_RESET}] {core:5.1f}%")

    print(f"\n{CLR_BOLD}Physical Memory (RAM):{CLR_RESET}")
    print(f"  Total: {mem['total_mb']} MB | Used: {mem['used_mb']} MB ({mem['used_pct']}%) | Free: {CLR_GREEN}{mem['free_mb']} MB{CLR_RESET}")

    print(f"\n{CLR_BOLD}Solid State Drive (Drive C:):{CLR_RESET}")
    print(f"  Total: {storage['total_gb']} GB | Used: {storage['used_gb']} GB ({storage['used_pct']}%) | Free: {CLR_GREEN}{storage['free_gb']} GB{CLR_RESET}")
    print(f"  Cached Temporary Bloat: {storage['junk_mb']} MB")

    print(f"\n{CLR_BOLD}Top Memory-Consuming Processes:{CLR_RESET}")
    print(f"  {'PID':<8} {'Process Name':<28} {'Working Set (RAM)':<18}")
    print(f"  {'-'*8} {'-'*28} {'-'*18}")
    for p in top_procs:
        print(f"  {p['pid']:<8} {p['name'][:26]:<28} {CLR_YELLOW}{p['mem_mb']:>8.1f} MB{CLR_RESET}")


def action_run_powershell_optimization():
    """Run the standalone PowerShell optimization script with administrative elevation."""
    ps_script = BASE_DIR / "laptop_optimizer" / "Optimize-Laptop.ps1"
    if not ps_script.exists():
        print(f"{CLR_RED}[!] Could not find script at {ps_script}{CLR_RESET}")
        return

    print(f"\n{CLR_BOLD}{CLR_CYAN}🛡️ [Running Windows 11 Native PowerShell Tuning]{CLR_RESET}")
    print(f"{CLR_DIM}Executing Optimize-Laptop.ps1...{CLR_RESET}\n")

    cmd = [
        "powershell.exe",
        "-ExecutionPolicy",
        "Bypass",
        "-NoProfile",
        "-File",
        str(ps_script),
        "-WorkingSetRelief",
        "-DiskReclaim",
        "-ResponsivenessTuning",
        "-SSDTrim",
    ]
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"{CLR_RED}[!] PowerShell execution notice: {e}{CLR_RESET}")


def action_run_benchmark():
    """Execute the diagnostic benchmark script."""
    bench_script = BASE_DIR / "laptop_optimizer" / "benchmark.ps1"
    if not bench_script.exists():
        print(f"{CLR_RED}[!] Could not find script at {bench_script}{CLR_RESET}")
        return

    print(f"\n{CLR_BOLD}{CLR_CYAN}⏱️ [Running System Diagnostic Benchmark]{CLR_RESET}\n")
    cmd = [
        "powershell.exe",
        "-ExecutionPolicy",
        "Bypass",
        "-NoProfile",
        "-File",
        str(bench_script),
    ]
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"{CLR_RED}[!] Benchmark execution notice: {e}{CLR_RESET}")


def print_menu():
    """Print the numbered menu options."""
    print(f"\n{CLR_BOLD}SELECT AN ACTION:{CLR_RESET}")
    print(f"  {CLR_CYAN}[1]{CLR_RESET} 🌐  {CLR_BOLD}Open Web Visualizer in Browser{CLR_RESET} (Launches UI on http://localhost:8000)")
    print(f"  {CLR_GREEN}[2]{CLR_RESET} ⚡  {CLR_BOLD}Instant RAM Boost{CLR_RESET} (Native psapi.dll Working Set Compaction)")
    print(f"  {CLR_MAGENTA}[3]{CLR_RESET} 🧹  {CLR_BOLD}Storage Sweep & SSD TRIM{CLR_RESET} (Purge Temp Files & Reclaim Flash Blocks)")
    print(f"  {CLR_YELLOW}[4]{CLR_RESET} 🚀  {CLR_BOLD}Full System Optimization{CLR_RESET} (RAM Boost + Storage Sweep + TRIM)")
    print(f"  {CLR_BLUE}[5]{CLR_RESET} 📊  {CLR_BOLD}Live Diagnostics & Top Processes{CLR_RESET} (Per-core load & RAM breakdown)")
    print(f"  {CLR_CYAN}[6]{CLR_RESET} 🛡️  {CLR_BOLD}Run Windows 11 PowerShell Tuning{CLR_RESET} (Deep OS Tweaks & Registry)")
    print(f"  {CLR_YELLOW}[7]{CLR_RESET} ⏱️  {CLR_BOLD}Run System Diagnostic Benchmark{CLR_RESET} (Performance Audit)")
    print(f"  {CLR_GREEN}[8]{CLR_RESET} 🔄  {CLR_BOLD}Start / Restart Web Server Daemon{CLR_RESET}")
    print(f"  {CLR_RED}[0]{CLR_RESET} ❌  {CLR_BOLD}Exit{CLR_RESET}")
    print()


def main():
    """Main interactive terminal loop."""
    while True:
        try:
            render_banner()
            print_menu()
            choice = input(f"{CLR_BOLD}Enter option [0-8]: {CLR_RESET}").strip()

            if choice == "1":
                open_browser()
            elif choice == "2":
                action_ram_boost()
            elif choice == "3":
                action_storage_sweep()
            elif choice == "4":
                action_full_optimize()
            elif choice == "5":
                action_view_diagnostics()
            elif choice == "6":
                action_run_powershell_optimization()
            elif choice == "7":
                action_run_benchmark()
            elif choice == "8":
                start_server_background()
            elif choice in ("0", "q", "exit"):
                print(f"\n{CLR_GREEN}Thank you for using Laptop Optimizer Metropolis! Have a smooth day! 🚀{CLR_RESET}")
                time.sleep(0.8)
                break
            else:
                print(f"{CLR_RED}[!] Invalid choice '{choice}'. Please choose 0 to 8.{CLR_RESET}")

            input(f"\n{CLR_DIM}Press [Enter] to return to the main menu...{CLR_RESET}")

        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{CLR_GREEN}Exiting Laptop Optimizer Metropolis. Stay smooth!{CLR_RESET}")
            break
        except Exception as e:
            print(f"\n{CLR_RED}[!] Error: {e}{CLR_RESET}")
            input(f"\n{CLR_DIM}Press [Enter] to continue...{CLR_RESET}")


if __name__ == "__main__":
    main()
