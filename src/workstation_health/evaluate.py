"""Explainable rules applied only to collected evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

STATUSES = ("OK", "WARNING", "CRITICAL", "UNKNOWN", "NOT_APPLICABLE")
SEVERITY = {"CRITICAL": 0, "WARNING": 1, "UNKNOWN": 2, "OK": 3, "NOT_APPLICABLE": 4}


@dataclass(frozen=True)
class Thresholds:
    disk_warning_percent_free: float = 15.0
    disk_critical_percent_free: float = 5.0
    disk_warning_gib_free: float = 10.0
    disk_critical_gib_free: float = 2.0
    memory_warning_percent_used: float = 85.0
    memory_critical_percent_used: float = 95.0
    cpu_warning_percent_used: float = 85.0
    cpu_critical_percent_used: float = 95.0

    def validate(self) -> None:
        pairs = (
            (self.disk_critical_percent_free, self.disk_warning_percent_free, 100),
            (self.disk_critical_gib_free, self.disk_warning_gib_free, None),
            (self.memory_warning_percent_used, self.memory_critical_percent_used, 100),
            (self.cpu_warning_percent_used, self.cpu_critical_percent_used, 100),
        )
        from math import isfinite

        for low, high, cap in pairs:
            if not (isfinite(low) and isfinite(high) and 0 < low < high):
                raise ValueError("Thresholds must be finite, positive, and strictly ordered")
            if cap is not None and high > cap:
                raise ValueError("Percentage threshold cannot exceed 100")


def finding(
    check_id: str,
    title: str,
    status: str,
    evidence: str,
    rule: str,
    interpretation: str,
    next_step: str | None,
    source: str,
    limitations: str,
) -> dict[str, Any]:
    if status not in STATUSES:
        raise ValueError("Invalid status")
    return {
        "id": check_id,
        "title": title,
        "status": status,
        "evidence": evidence,
        "rule": rule,
        "interpretation": interpretation,
        "next_step": next_step,
        "source": source,
        "limitations": limitations,
    }


def assess_disk(storage: list[dict[str, Any]], limits: Thresholds) -> dict[str, Any]:
    rule = (
        f"WARNING if free <= {limits.disk_warning_percent_free:g}% OR <= "
        f"{limits.disk_warning_gib_free:g} GiB; CRITICAL if free <= "
        f"{limits.disk_critical_percent_free:g}% OR <= {limits.disk_critical_gib_free:g} GiB. "
        "Critical overrides warning; boundaries are inclusive."
    )
    valid = [
        v
        for v in storage
        if isinstance(v.get("total_bytes"), (int, float))
        and v["total_bytes"] > 0
        and isinstance(v.get("free_bytes"), (int, float))
        and v["free_bytes"] >= 0
    ]
    if not valid:
        return finding(
            "storage.free",
            "Local disk capacity",
            "UNKNOWN",
            "No readable local volumes",
            rule,
            "Local disk free space could not be evaluated.",
            "Check access to a local volume.",
            "psutil.disk_partitions + disk_usage",
            "Remote, pseudo and removable volumes are excluded where identifiable.",
        )
    severity = "OK"
    alerts = []
    for volume in valid:
        free_gib = volume["free_bytes"] / 1024**3
        free_pct = 100 * volume["free_bytes"] / volume["total_bytes"]
        if (
            free_pct <= limits.disk_critical_percent_free
            or free_gib <= limits.disk_critical_gib_free
        ):
            status = "CRITICAL"
        elif (
            free_pct <= limits.disk_warning_percent_free or free_gib <= limits.disk_warning_gib_free
        ):
            status = "WARNING"
        else:
            status = "OK"
        if SEVERITY[status] < SEVERITY[severity]:
            severity = status
        if status != "OK":
            alerts.append(f"{volume['label']}: {free_gib:.1f} GiB ({free_pct:.1f}%) free")
    observation = (
        "; ".join(alerts)
        if alerts
        else f"{len(valid)} local volume(s) checked; none crossed thresholds"
    )
    return finding(
        "storage.free",
        "Local disk capacity",
        severity,
        observation,
        rule,
        "One or more local volumes have limited free capacity."
        if alerts
        else "No low-space thresholds were crossed on evaluated volumes.",
        "Review storage usage and free space; no files are changed by this tool."
        if alerts
        else None,
        "psutil.disk_partitions + disk_usage",
        "Does not assess disk wear or all possible mounts; filesystem reads can block.",
    )


def assess_percent(
    check_id: str,
    title: str,
    value: float | None,
    *,
    warning: float,
    critical: float,
    source: str,
    limitations: str,
) -> dict[str, Any]:
    rule = f"WARNING at >= {warning:g}%; CRITICAL at >= {critical:g}%; boundaries inclusive."
    if value is None or not isinstance(value, (float, int)) or not 0 <= value <= 100:
        return finding(
            check_id,
            title,
            "UNKNOWN",
            "Measurement unavailable",
            rule,
            "Insufficient evidence for evaluation.",
            None,
            source,
            limitations,
        )
    status = "CRITICAL" if value >= critical else "WARNING" if value >= warning else "OK"
    return finding(
        check_id,
        title,
        status,
        f"{value:.1f}% used",
        rule,
        "This snapshot crossed a utilization threshold."
        if status != "OK"
        else "This snapshot did not cross a utilization threshold.",
        "Check usage again during a representative workload if symptoms persist."
        if status != "OK"
        else None,
        source,
        limitations,
    )


def assess_battery(hardware: dict[str, Any]) -> dict[str, Any]:
    present = hardware.get("battery_present")
    pct = hardware.get("battery_percent")
    plugged = hardware.get("battery_plugged_in")
    rule = "If unplugged: WARNING at <= 20% charge; CRITICAL at <= 10%; otherwise informational."
    if present is False:
        return finding(
            "battery.charge",
            "Battery charge",
            "NOT_APPLICABLE",
            "No battery reported",
            rule,
            "A battery is not reported on this machine.",
            None,
            "psutil.sensors_battery",
            "Battery may be unreported by the OS.",
        )
    if (
        present is not True
        or not isinstance(pct, (int, float))
        or not 0 <= pct <= 100
        or plugged is None
    ):
        return finding(
            "battery.charge",
            "Battery charge",
            "UNKNOWN",
            "Battery information unavailable",
            rule,
            "Charge status cannot be established.",
            None,
            "psutil.sensors_battery",
            "Does not assess battery wear, capacity, or remaining service life.",
        )
    status = (
        "CRITICAL"
        if not plugged and pct <= 10
        else "WARNING"
        if not plugged and pct <= 20
        else "OK"
    )
    evidence = f"{pct:.1f}% charged; {'plugged in' if plugged else 'on battery'}"
    return finding(
        "battery.charge",
        "Battery charge",
        status,
        evidence,
        rule,
        "Low current charge."
        if status != "OK"
        else "Charge state reported; battery wear not assessed.",
        "Connect a charger when convenient." if status != "OK" else None,
        "psutil.sensors_battery",
        "Percentage is current charge, not battery wear or capacity.",
    )


def evaluate(inventory: dict[str, Any], limits: Thresholds) -> list[dict[str, Any]]:
    limits.validate()
    hw = inventory["hardware"]
    resource = inventory["resources"]
    result = [
        assess_disk(inventory["storage"], limits),
        assess_percent(
            "memory.utilization",
            "Memory utilization",
            hw.get("ram_used_percent"),
            warning=limits.memory_warning_percent_used,
            critical=limits.memory_critical_percent_used,
            source="psutil.virtual_memory",
            limitations="One sample does not diagnose a leak or determine adequate RAM.",
        ),
        assess_percent(
            "cpu.utilization",
            "CPU utilization",
            resource.get("cpu_percent"),
            warning=limits.cpu_warning_percent_used,
            critical=limits.cpu_critical_percent_used,
            source=f"psutil.cpu_percent(interval={resource.get('cpu_sample_seconds')}s)",
            limitations="A short sampled interval is not sustained workload analysis.",
        ),
        assess_battery(hw),
    ]
    if inventory["system"].get("os") == "Windows":
        result.append(
            finding(
                "security.windows_defender",
                "Microsoft Defender status",
                "UNKNOWN",
                "Not collected",
                "Read-only provider assessment deferred.",
                "No inference about antivirus presence or protection is possible.",
                "Review Windows Security directly, if authorized.",
                "Deferred Windows provider",
                "Not an assessment of other antivirus products.",
            )
        )
    return sorted(result, key=lambda c: (SEVERITY[c["status"]], c["id"]))


def summarize(checks: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {s: sum(c["status"] == s for c in checks) for s in STATUSES}
    evaluated = counts["OK"] + counts["WARNING"] + counts["CRITICAL"]
    total = evaluated + counts["UNKNOWN"]  # N/A explicitly excluded from applicable denominator
    if counts["CRITICAL"]:
        headline = "Critical findings need attention."
    elif counts["WARNING"]:
        headline = "Some evaluated checks need attention."
    else:
        headline = "No issues detected in evaluated checks."
    if counts["UNKNOWN"]:
        headline += " Some checks could not be completed."
    coverage = f"{evaluated} of {total} applicable checks evaluated; {counts['NOT_APPLICABLE']} not applicable."
    return {
        "headline": headline,
        "status_counts": counts,
        "evaluated": evaluated,
        "total": total,
        "coverage": coverage,
        "actionable_check_ids": [c["id"] for c in checks if c["status"] in ("CRITICAL", "WARNING")],
        "unavailable_check_ids": [c["id"] for c in checks if c["status"] == "UNKNOWN"],
    }
