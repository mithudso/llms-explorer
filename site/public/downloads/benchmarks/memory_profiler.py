#!/usr/bin/env python3
"""memory_profiler.py — Profile host unified memory and discrete GPU residency."""

import json
import subprocess
import sys

def get_macos_memory():
    out = {}
    try:
        vm = subprocess.run(["vm_stat"], capture_output=True, text=True, check=True).stdout
        for line in vm.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip().replace('"', '')
                v = v.strip().replace(".", "")
                try:
                    out[k] = int(v) * 4096  # page size is 4KB
                except ValueError:
                    pass
    except Exception as e:
        out["error"] = str(e)
    return out

def get_hardware_info():
    info = {}
    try:
        sp = subprocess.run(["system_profiler", "SPHardwareDataType", "SPDisplaysDataType"], capture_output=True, text=True).stdout
        lines = [line.strip() for line in sp.splitlines() if line.strip()]
        for line in lines:
            if "Chip:" in line or "Total Number of Cores:" in line or "Memory:" in line or "Chipset Model:" in line or "VRAM" in line:
                parts = line.split(":", 1)
                info[parts[0].strip()] = parts[1].strip() if len(parts) > 1 else ""
    except Exception as e:
        info["error"] = str(e)
    return info

def main():
    hw = get_hardware_info()
    mem = get_macos_memory()
    
    wired_gb = round(mem.get("Pages wired down", 0) / (1024**3), 2)
    active_gb = round(mem.get("Pages active", 0) / (1024**3), 2)
    inactive_gb = round(mem.get("Pages inactive", 0) / (1024**3), 2)
    free_gb = round(mem.get("Pages free", 0) / (1024**3), 2)
    
    summary = {
        "hardware": hw,
        "memory_gb": {
            "wired": wired_gb,
            "active": active_gb,
            "inactive": inactive_gb,
            "free": free_gb
        }
    }
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
