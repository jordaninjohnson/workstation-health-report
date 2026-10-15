"""Strict report allowlists and privacy-safe failure descriptions.

Input from OS/device/commands is untrusted. Report only defined fields; never
serialize arbitrary collector dictionaries, command stderr, or exceptions.
"""

from __future__ import annotations

import re
import subprocess
from typing import Any

# Avoid displaying path-like, address-like, control, or very long device metadata.
_NETWORK = re.compile(
    r"(?:\b(?:\d{1,3}\.){3}\d{1,3}\b|"
    r"\b[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}\b|"
    r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b)"
)
_PATH = re.compile(r"(?:[A-Za-z]:[\\/]|[/\\](?:Users|home|mnt|Volumes)[/\\])", re.I)
_ALLOWED = re.compile(r"[^a-zA-Z0-9 _.,()/+@:-]")


def safe_label(value: Any, *, max_chars: int = 90) -> str | None:
    """Conservatively admit plain hardware labels, never paths or addresses."""
    if not isinstance(value, str):
        return None
    value = " ".join(value.split())
    if not value or _NETWORK.search(value) or _PATH.search(value) or "\\" in value:
        return None
    if len(value) > max_chars:
        return None
    value = _ALLOWED.sub("", value).strip()
    return value or None


def unavailable_reason(exc: BaseException) -> str:
    """Return a category, not potentially secret exception args/filenames."""
    if isinstance(exc, (PermissionError, psutil_access_denied_type())):
        return "permission_denied"
    if isinstance(exc, (TimeoutError, subprocess.TimeoutExpired)):
        return "timeout"
    if isinstance(exc, (FileNotFoundError, NotImplementedError)):
        return "unsupported"
    return "collection_error"


def psutil_access_denied_type() -> type:
    # Keep import small; AccessDenied is always an exception type.
    import psutil

    return psutil.AccessDenied


def issue(component: str, reason: str) -> dict[str, str]:
    """Fixed-message rendering; no untrusted error content."""
    reasons = {
        "permission_denied": "The operating system did not permit this observation.",
        "timeout": "A limited-time query did not finish.",
        "unsupported": "This source is not available on this platform.",
        "collection_error": "This observation could not be collected.",
        "not_implemented": "This read-only check is deferred in version 0.1.0.",
        "excluded": "Remote, pseudo, or removable storage is not assessed.",
    }
    return {
        "component": component if component in COMPONENTS else "other",
        "reason": reason if reason in reasons else "collection_error",
        "detail": reasons.get(reason, reasons["collection_error"]),
    }


COMPONENTS = frozenset(
    {"cpu", "memory", "battery", "storage", "network", "system", "security", "other"}
)


# Exact public report schema. Unknown keys never leave internal collectors.
def public_report(raw: dict[str, Any]) -> dict[str, Any]:
    inv = raw.get("inventory", {})
    hardware = inv.get("hardware", {})
    system = inv.get("system", {})
    resources = inv.get("resources", {})
    network = inv.get("network", {})

    def fields(source: dict[str, Any], names: tuple[str, ...]) -> dict[str, Any]:
        return {key: source.get(key) for key in names}

    storage = [
        fields(
            item, ("label", "filesystem", "total_bytes", "used_bytes", "free_bytes", "used_percent")
        )
        for item in inv.get("storage", [])
    ]
    interfaces = [
        fields(item, ("label", "is_up", "speed_mbps")) for item in network.get("interfaces", [])
    ]
    checks = [
        fields(
            item,
            (
                "id",
                "title",
                "status",
                "evidence",
                "rule",
                "interpretation",
                "next_step",
                "source",
                "limitations",
            ),
        )
        for item in raw.get("checks", [])
    ]
    return {
        "schema_version": raw.get("schema_version"),
        "application": fields(raw.get("application", {}), ("name", "version")),
        "scan": fields(raw.get("scan", {}), ("timestamp", "privacy_mode", "synthetic", "scenario")),
        "summary": fields(
            raw.get("summary", {}),
            (
                "headline",
                "status_counts",
                "evaluated",
                "total",
                "coverage",
                "actionable_check_ids",
                "unavailable_check_ids",
            ),
        ),
        "inventory": {
            "system": fields(
                system,
                (
                    "os",
                    "os_version",
                    "architecture",
                    "kernel",
                    "python_version",
                    "boot_time",
                    "uptime_seconds",
                    "environment_evidence",
                ),
            ),
            "hardware": fields(
                hardware,
                (
                    "manufacturer",
                    "model",
                    "cpu_model",
                    "physical_cores",
                    "logical_cores",
                    "ram_total_bytes",
                    "ram_available_bytes",
                    "ram_used_percent",
                    "battery_present",
                    "battery_percent",
                    "battery_plugged_in",
                ),
            ),
            "resources": fields(resources, ("cpu_percent", "cpu_sample_seconds")),
            "storage": storage,
            "network": {
                **fields(network, ("interface_count", "interfaces_up")),
                "interfaces": interfaces,
            },
        },
        "checks": checks,
        "collection_issues": [
            issue(i.get("component", "other"), i.get("reason", "collection_error"))
            for i in raw.get("collection_issues", [])
        ],
        "limitations": list(LIMITATIONS),
    }


LIMITATIONS = (
    "Not a vulnerability scanner, compliance audit, malware detector, or security certification.",
    "Does not confirm patch compliance, antivirus efficacy, firewall policy, or active encryption.",
    "Does not assess SMART disk health, backup restore success, or workload suitability.",
    "One brief CPU and memory observation cannot establish sustained performance or memory leaks.",
    "Reported interface link speed is not measured throughput; link-up does not prove internet access.",
    "Local filesystem calls can block in the operating system; Python cannot impose a hard timeout on them.",
    "Hardware and battery values may be unavailable or inaccurate in virtual environments.",
)
