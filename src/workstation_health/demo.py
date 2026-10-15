"""Entirely synthetic data: never calls host collectors."""

from __future__ import annotations

from .evaluate import Thresholds, evaluate, finding


def synthetic_observation(scenario: str) -> dict:
    if scenario not in {"healthy", "attention-needed"}:
        raise ValueError("Unknown synthetic scenario")
    attention = scenario == "attention-needed"
    gib = 1024**3
    total = 512 * gib
    free = 5 * gib if attention else 220 * gib
    inventory = {
        "system": {
            "os": "Windows", "os_version": "11 (illustrative)", "architecture": "AMD64",
            "kernel": "Synthetic build", "python_version": "3.13 (synthetic)",
            "boot_time": "2026-01-01T09:00:00+00:00", "uptime_seconds": 172800,
            "environment_evidence": None,
        },
        "hardware": {
            "manufacturer": "Example Devices", "model": "Example Workstation",
            "cpu_model": "Synthetic 8-Core CPU", "physical_cores": 8, "logical_cores": 16,
            "ram_total_bytes": 16 * gib, "ram_available_bytes": 10 * gib,
            "ram_used_percent": 37.5, "battery_present": False,
            "battery_percent": None, "battery_plugged_in": None,
        },
        "resources": {"cpu_percent": 18.4, "cpu_sample_seconds": 0.25},
        "storage": [{"label": "Local volume 1", "filesystem": "NTFS", "total_bytes": total,
                     "used_bytes": total - free, "free_bytes": free,
                     "used_percent": round(100 * (total - free) / total, 2)}],
        "network": {"interface_count": 2, "interfaces_up": 1,
                    "interfaces": [{"label": "Interface 1", "is_up": True, "speed_mbps": 1000},
                                   {"label": "Interface 2", "is_up": False, "speed_mbps": None}]},
    }
    checks = evaluate(inventory, Thresholds())
    # A synthetic unavailable Windows security probe demonstrates honest UNKNOWN handling.
    security = finding("security.windows_defender", "Microsoft Defender status", "UNKNOWN",
                       "No provider result available", "Reliable Windows-only provider required.",
                       "Security status cannot be inferred from missing evidence.",
                       "Review Windows Security locally.", "Synthetic provider response",
                       "No actual device was inspected; other antivirus tools are not evaluated.")
    if attention:
        checks = [c for c in checks if c["id"] != security["id"]] + [security]
    else:
        checks = [c for c in checks if c["id"] != security["id"]]
    return {
        "timestamp": "2026-01-15T10:30:00-07:00", "inventory": inventory,
        "checks": checks, "collection_issues": ([{"component": "security", "reason": "unsupported"}]
                                             if attention else []),
    }
