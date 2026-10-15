from __future__ import annotations

import copy

import pytest

from workstation_health.evaluate import (
    Thresholds,
    assess_battery,
    assess_disk,
    assess_percent,
    evaluate,
    summarize,
)

GIB = 1024**3


def disk(free_gib: float, total_gib: float = 100) -> list[dict]:
    return [
        {"label": "Local volume 1", "total_bytes": total_gib * GIB, "free_bytes": free_gib * GIB}
    ]


@pytest.mark.parametrize(
    "free_gib,expected",
    [
        (16, "OK"),
        (15, "WARNING"),
        (10, "WARNING"),
        (5.001, "WARNING"),
        (5, "CRITICAL"),
        (2, "CRITICAL"),
        (1, "CRITICAL"),
    ],
)
def test_disk_percent_boundaries(free_gib, expected):
    # Default 10GiB warning and 2GiB critical absolute thresholds; note exact boundaries.
    assert assess_disk(disk(free_gib), Thresholds())["status"] == expected


def test_disk_absolute_threshold_independent_of_percentage():
    assert assess_disk(disk(10.0, 50), Thresholds())["status"] == "WARNING"
    assert assess_disk(disk(2.0, 20), Thresholds())["status"] == "CRITICAL"
    assert (
        assess_disk(disk(10.01, 1000), Thresholds())["status"] == "CRITICAL"
    )  # percentage rule overrides absolute threshold


def test_disk_combination_critical_overrides():
    result = assess_disk(disk(1.5, 1000), Thresholds())
    assert result["status"] == "CRITICAL"
    assert "OR" in result["rule"]


def test_disk_no_usable_data_unknown():
    assert assess_disk([], Thresholds())["status"] == "UNKNOWN"
    assert assess_disk([{"total_bytes": 0, "free_bytes": 0}], Thresholds())["status"] == "UNKNOWN"


@pytest.mark.parametrize(
    "pct,expected",
    [
        (None, "UNKNOWN"),
        (-1, "UNKNOWN"),
        (101, "UNKNOWN"),
        (84.99, "OK"),
        (85, "WARNING"),
        (94.9, "WARNING"),
        (95, "CRITICAL"),
    ],
)
def test_memory_cpu_boundaries(pct, expected):
    for check_id in ("memory.utilization", "cpu.utilization"):
        result = assess_percent(
            check_id, "Use", pct, warning=85, critical=95, source="mock", limitations="snapshot"
        )
        assert result["status"] == expected


def test_battery_states(inventory):
    hw = inventory["hardware"]
    assert assess_battery(hw)["status"] == "NOT_APPLICABLE"
    hw["battery_present"] = True
    hw["battery_percent"] = None
    assert assess_battery(hw)["status"] == "UNKNOWN"
    hw["battery_percent"], hw["battery_plugged_in"] = 20, False
    assert assess_battery(hw)["status"] == "WARNING"
    hw["battery_percent"] = 10
    assert assess_battery(hw)["status"] == "CRITICAL"
    hw["battery_plugged_in"] = True
    assert assess_battery(hw)["status"] == "OK"


def test_threshold_validation():
    for kwargs in (
        {"disk_warning_percent_free": 5, "disk_critical_percent_free": 5},
        {"disk_warning_gib_free": 1, "disk_critical_gib_free": 2},
        {"memory_warning_percent_used": 99, "memory_critical_percent_used": 90},
        {"cpu_critical_percent_used": 101},
        {"cpu_warning_percent_used": float("nan")},
        {"disk_warning_gib_free": float("inf")},
    ):
        with pytest.raises(ValueError):
            Thresholds(**kwargs).validate()


def test_aggregate_no_unknown_as_ok():
    checks = [
        {"id": "a", "status": "OK"},
        {"id": "b", "status": "UNKNOWN"},
        {"id": "c", "status": "NOT_APPLICABLE"},
    ]
    summary = summarize(checks)
    assert summary["evaluated"] == 1
    assert summary["total"] == 2
    assert summary["unavailable_check_ids"] == ["b"]
    assert "Some checks" in summary["headline"]
    assert summary["status_counts"]["OK"] == 1


def test_multiple_critical_warn_order(inventory):
    inv = copy.deepcopy(inventory)
    inv["hardware"]["ram_used_percent"] = 90
    inv["resources"]["cpu_percent"] = 99
    checks = evaluate(inv, Thresholds())
    assert checks[0]["status"] == "CRITICAL"
    assert checks[1]["status"] == "WARNING"
    assert summarize(checks)["actionable_check_ids"] == [checks[0]["id"], checks[1]["id"]]


def test_deferred_windows_security_not_mistaken_for_protection(inventory):
    result = evaluate(inventory, Thresholds())
    security = next(c for c in result if c["id"] == "security.windows_defender")
    assert security["status"] == "UNKNOWN"
    assert "not" in security["interpretation"].lower() or "no" in security["interpretation"].lower()
    inventory["system"]["os"] = "Linux"
    assert all(c["id"] != "security.windows_defender" for c in evaluate(inventory, Thresholds()))
