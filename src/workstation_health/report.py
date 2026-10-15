"""Compose reports without exposing raw collection or device-derived exceptions."""

from __future__ import annotations

from typing import Any

from . import SCHEMA_VERSION, __version__
from .evaluate import Thresholds, evaluate, summarize
from .privacy import public_report


def compose(
    observation: dict[str, Any],
    *,
    limits: Thresholds | None = None,
    synthetic: bool = False,
    scenario: str | None = None,
) -> dict[str, Any]:
    limits = limits or Thresholds()
    limits.validate()
    checks = observation.get("checks")
    if checks is None:
        checks = evaluate(observation["inventory"], limits)
    checks = sorted(
        checks,
        key=lambda c: (
            {"CRITICAL": 0, "WARNING": 1, "UNKNOWN": 2, "OK": 3, "NOT_APPLICABLE": 4}[c["status"]],
            c["id"],
        ),
    )
    raw = {
        "schema_version": SCHEMA_VERSION,
        "application": {"name": "Workstation Inventory & Health Report", "version": __version__},
        "scan": {
            "timestamp": observation["timestamp"],
            "privacy_mode": "default-minimal",
            "synthetic": synthetic,
            "scenario": scenario,
        },
        "summary": summarize(checks),
        "inventory": observation["inventory"],
        "checks": checks,
        "collection_issues": observation.get("collection_issues", []),
    }
    return public_report(raw)
