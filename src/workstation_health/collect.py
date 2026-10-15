"""Read-only local observation. No networking, process enumeration, or privileged probes."""

from __future__ import annotations

import platform
from datetime import datetime, timezone
from typing import Any

import psutil

from .platform_helpers import cpu_model, environment_evidence, manufacturer_model
from .privacy import issue, safe_label, unavailable_reason

REMOTE_FS = {"nfs", "nfs4", "cifs", "smbfs", "sshfs", "afs", "9p", "davfs", "fuse.sshfs"}
PSEUDO_FS = {
    "proc",
    "sysfs",
    "devtmpfs",
    "devpts",
    "tmpfs",
    "squashfs",
    "overlay",
    "cgroup",
    "cgroup2",
    "debugfs",
    "tracefs",
    "securityfs",
    "pstore",
    "mqueue",
    "autofs",
    "fusectl",
    "hugetlbfs",
    "configfs",
    "ramfs",
    "nsfs",
    "binfmt_misc",
}


def include_volume(part: Any) -> bool:
    fs = (part.fstype or "").lower()
    opts = (part.opts or "").lower().split(",")
    device = (part.device or "").lower()
    if not fs or fs in PSEUDO_FS or fs in REMOTE_FS or fs.startswith("fuse"):
        return False
    if any(flag in opts for flag in ("remote", "removable", "cdrom")):
        return False
    if device.startswith(("//", "\\\\")):
        return False
    return True


def collect(*, sample_seconds: float = 0.25) -> dict[str, Any]:
    """Collect an allowlisted inventory; failures are isolated by category."""
    issues: list[dict[str, str]] = []

    def attempt(component: str, func: Any, default: Any = None) -> Any:
        try:
            return func()
        except Exception as exc:
            issues.append(issue(component, unavailable_reason(exc)))
            return default

    now = datetime.now(timezone.utc).astimezone()
    system = {
        "os": platform.system() or None,
        "os_version": platform.version() or None,
        "architecture": platform.machine() or None,
        "kernel": platform.release() or None,
        "python_version": platform.python_version(),
        "boot_time": None,
        "uptime_seconds": None,
        "environment_evidence": attempt("system", environment_evidence),
    }
    boot_epoch = attempt("system", psutil.boot_time)
    if isinstance(boot_epoch, (int, float)) and 0 < boot_epoch <= now.timestamp():
        system["boot_time"] = (
            datetime.fromtimestamp(boot_epoch, timezone.utc).astimezone().isoformat()
        )
        system["uptime_seconds"] = round(now.timestamp() - boot_epoch)

    manufacturer, model = attempt("system", manufacturer_model, (None, None))
    mem = attempt("memory", psutil.virtual_memory)

    def positive_int(value: Any) -> int | None:
        return int(value) if isinstance(value, (int, float)) and 0 <= value < float("inf") else None

    def percentage(value: Any) -> float | None:
        return float(value) if isinstance(value, (int, float)) and 0 <= value <= 100 else None

    battery_error = object()
    battery = attempt("battery", psutil.sensors_battery, battery_error)
    battery_available = battery is not battery_error
    hardware = {
        "manufacturer": manufacturer,
        "model": model,
        "cpu_model": attempt("cpu", cpu_model),
        "physical_cores": attempt("cpu", lambda: psutil.cpu_count(logical=False)),
        "logical_cores": attempt("cpu", lambda: psutil.cpu_count(logical=True)),
        "ram_total_bytes": positive_int(getattr(mem, "total", None)),
        "ram_available_bytes": positive_int(getattr(mem, "available", None)),
        "ram_used_percent": percentage(getattr(mem, "percent", None)),
        "battery_present": True if battery_available and battery is not None else None,
        "battery_percent": percentage(getattr(battery, "percent", None)),
        "battery_plugged_in": getattr(battery, "power_plugged", None)
        if isinstance(getattr(battery, "power_plugged", None), bool)
        else None,
    }
    cpu_pct = attempt("cpu", lambda: psutil.cpu_percent(interval=sample_seconds))
    resources = {
        "cpu_percent": float(cpu_pct) if cpu_pct is not None else None,
        "cpu_sample_seconds": sample_seconds,
    }

    storage: list[dict[str, Any]] = []
    partitions = attempt("storage", lambda: psutil.disk_partitions(all=False), [])
    seen: set[str] = set()
    for part in partitions:
        # Mount point is used internally only; never sent to renderer.
        if not include_volume(part) or part.mountpoint in seen:
            continue
        seen.add(part.mountpoint)
        usage = attempt("storage", lambda path=part.mountpoint: psutil.disk_usage(path))
        if usage is None:
            continue
        storage.append(
            {
                "label": f"Local volume {len(storage) + 1}",
                "filesystem": (safe_label(part.fstype, max_chars=32) or "Unknown").upper(),
                "total_bytes": int(usage.total),
                "used_bytes": int(usage.used),
                "free_bytes": int(usage.free),
                "used_percent": round(100 * usage.used / usage.total, 2)
                if usage.total > 0
                else None,
            }
        )

    interface_stats = attempt("network", psutil.net_if_stats)
    interfaces = []
    if interface_stats is not None:
        for stats in interface_stats.values():
            speed = (
                stats.speed if isinstance(stats.speed, (int, float)) and stats.speed > 0 else None
            )
            interfaces.append(
                {
                    "label": f"Interface {len(interfaces) + 1}",
                    "is_up": bool(stats.isup),
                    "speed_mbps": int(speed) if speed is not None else None,
                }
            )
    network = {
        "interface_count": len(interfaces) if interface_stats is not None else None,
        "interfaces_up": sum(i["is_up"] for i in interfaces)
        if interface_stats is not None
        else None,
        "interfaces": interfaces,
    }
    return {
        "timestamp": now.isoformat(),
        "inventory": {
            "system": system,
            "hardware": hardware,
            "resources": resources,
            "storage": storage,
            "network": network,
        },
        "collection_issues": issues,
    }
