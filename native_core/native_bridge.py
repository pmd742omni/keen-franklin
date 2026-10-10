"""Silicon Sanctuary Polyglot Native Bridge
Connects Python to C (Win32 NT kernel DLL), Rust (System Sentinel), and Java (Sanctuary Bridge).
"""

from __future__ import annotations

import ctypes
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("SiliconBridge")

_ROOT = Path(__file__).resolve().parent.parent
_C_DLL_PATH = _ROOT / "native_core" / "c" / "silicon_kernel.dll"
_RUST_EXE_PATHS = [
    _ROOT / "native_core" / "rust" / "system_sentinel.exe",
    _ROOT / "native_core" / "rust" / "target" / "release" / "system_sentinel.exe",
]
_JAVA_CLASS_DIR = _ROOT


class SiliconMemoryStats(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("memoryLoad", ctypes.c_ulong),
        ("totalPhysMb", ctypes.c_ulonglong),
        ("availPhysMb", ctypes.c_ulonglong),
        ("totalPageFileMb", ctypes.c_ulonglong),
        ("availPageFileMb", ctypes.c_ulonglong),
        ("processWorkingSetMb", ctypes.c_ulonglong),
        ("processPrivateMb", ctypes.c_ulonglong),
    ]


class SiliconTrimResult(ctypes.Structure):
    _fields_ = [
        ("processCount", ctypes.c_ulong),
        ("trimmedCount", ctypes.c_ulong),
        ("bytesReclaimed", ctypes.c_ulonglong),
        ("executionDurationMs", ctypes.c_double),
    ]


class PolyglotBridge:
    """Unified controller interfacing C kernel DLL, Rust sentinel, and Java bridge."""

    _c_lib = None
    _c_available = False

    @classmethod
    def init_c_kernel(cls) -> bool:
        if cls._c_lib is not None:
            return cls._c_available

        if not _C_DLL_PATH.exists():
            logger.warning("C silicon_kernel.dll not found at %s", _C_DLL_PATH)
            cls._c_available = False
            return False

        try:
            cls._c_lib = ctypes.CDLL(str(_C_DLL_PATH))

            # Configure function prototypes
            cls._c_lib.Silicon_GetMemoryStats.argtypes = [ctypes.POINTER(SiliconMemoryStats)]
            cls._c_lib.Silicon_GetMemoryStats.restype = ctypes.c_int

            cls._c_lib.Silicon_TrimProcessWorkingSet.argtypes = [ctypes.c_ulong]
            cls._c_lib.Silicon_TrimProcessWorkingSet.restype = ctypes.c_int

            cls._c_lib.Silicon_CompactWorkingSets.argtypes = []
            cls._c_lib.Silicon_CompactWorkingSets.restype = SiliconTrimResult

            cls._c_lib.Silicon_SetProcessAffinity.argtypes = [ctypes.c_ulong, ctypes.c_size_t]
            cls._c_lib.Silicon_SetProcessAffinity.restype = ctypes.c_int

            cls._c_lib.Silicon_SetPowerThrottling.argtypes = [ctypes.c_ulong, ctypes.c_int]
            cls._c_lib.Silicon_SetPowerThrottling.restype = ctypes.c_int

            cls._c_lib.Silicon_TriggerDriveTrim.argtypes = [ctypes.c_char]
            cls._c_lib.Silicon_TriggerDriveTrim.restype = ctypes.c_int

            cls._c_available = True
            logger.info("Successfully loaded C silicon_kernel.dll")
            return True
        except Exception as e:
            logger.error("Failed to load C silicon_kernel.dll: %s", e)
            cls._c_available = False
            return False

    @classmethod
    def get_c_memory_stats(cls) -> Dict[str, Any]:
        """Fetch real-time memory metrics via direct Win32 PSAPI calls."""
        if not cls.init_c_kernel():
            return {"status": "unavailable", "engine": "c_kernel"}

        stats = SiliconMemoryStats()
        stats.dwLength = ctypes.sizeof(SiliconMemoryStats)
        ok = cls._c_lib.Silicon_GetMemoryStats(ctypes.byref(stats))
        if not ok:
            return {"status": "error", "engine": "c_kernel"}

        return {
            "status": "healthy",
            "engine": "c_kernel",
            "memory_load_pct": stats.memoryLoad,
            "total_phys_mb": stats.totalPhysMb,
            "avail_phys_mb": stats.availPhysMb,
            "used_phys_mb": stats.totalPhysMb - stats.availPhysMb,
            "process_working_set_mb": stats.processWorkingSetMb,
            "process_private_mb": stats.processPrivateMb,
        }

    @classmethod
    def compact_memory_c(cls) -> Dict[str, Any]:
        """Trigger instant system-wide working set compaction in C."""
        if not cls.init_c_kernel():
            return {"status": "unavailable", "engine": "c_kernel"}

        result = cls._c_lib.Silicon_CompactWorkingSets()
        reclaimed_mb = result.bytesReclaimed / (1024.0 * 1024.0)

        return {
            "status": "compacted",
            "engine": "c_kernel",
            "processes_scanned": result.processCount,
            "processes_trimmed": result.trimmedCount,
            "reclaimed_mb": round(reclaimed_mb, 2),
            "execution_duration_ms": round(result.executionDurationMs, 3),
        }

    @classmethod
    def _find_rust_binary(cls) -> Optional[Path]:
        for p in _RUST_EXE_PATHS:
            if p.exists():
                return p
        return None

    @classmethod
    def get_rust_telemetry(cls) -> Dict[str, Any]:
        """Query Rust system sentinel for high-precision telemetry."""
        rust_bin = cls._find_rust_binary()
        if not rust_bin:
            return {
                "status": "not_compiled",
                "engine": "rust_sentinel",
                "message": "Rust binary pending compilation",
            }

        try:
            proc = subprocess.run(
                [str(rust_bin)],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if proc.returncode == 0:
                data = json.loads(proc.stdout)
                data["engine"] = "rust_sentinel"
                return data
            return {"status": "error", "engine": "rust_sentinel", "stderr": proc.stderr}
        except Exception as e:
            return {"status": "error", "engine": "rust_sentinel", "error": str(e)}

    @classmethod
    def get_java_telemetry(cls) -> Dict[str, Any]:
        """Query Java Sanctuary Bridge for cross-platform JVM redundancy."""
        try:
            proc = subprocess.run(
                ["java", "-cp", str(_JAVA_CLASS_DIR), "native_core.java.SiliconSanctuaryBridge", "--status"],
                capture_output=True,
                text=True,
                timeout=4,
            )
            if proc.returncode == 0:
                data = json.loads(proc.stdout)
                data["engine"] = "java_sanctuary_bridge"
                return data
            return {"status": "error", "engine": "java_sanctuary_bridge", "stderr": proc.stderr}
        except Exception as e:
            return {"status": "error", "engine": "java_sanctuary_bridge", "error": str(e)}

    @classmethod
    def get_polyglot_status(cls) -> Dict[str, Any]:
        """Aggregate health and metrics across C, Rust, and Java components."""
        c_stats = cls.get_c_memory_stats()
        rust_stats = cls.get_rust_telemetry()
        java_stats = cls.get_java_telemetry()

        return {
            "timestamp": os.getenv("CURRENT_TIME", ""),
            "components": {
                "c_kernel": {
                    "available": cls.init_c_kernel(),
                    "stats": c_stats,
                },
                "rust_sentinel": {
                    "available": cls._find_rust_binary() is not None,
                    "stats": rust_stats,
                },
                "java_bridge": {
                    "available": (_ROOT / "native_core" / "java" / "SiliconSanctuaryBridge.class").exists(),
                    "stats": java_stats,
                },
            },
        }
