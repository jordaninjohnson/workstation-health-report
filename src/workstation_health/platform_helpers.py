"""Minimal, read-only platform helpers with bounded external commands."""

from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path

from .privacy import safe_label


def run_json_command(argv: list[str], *, timeout: float = 4.0) -> dict[str, object]:
    """A narrow JSON-only command boundary; no shell or stderr exposure."""
    completed = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0 or len(completed.stdout) > 8192:
        raise ValueError("unusable command result")
    parsed = json.loads(completed.stdout)
    if not isinstance(parsed, dict):
        raise ValueError("expected JSON object")
    return parsed


def manufacturer_model() -> tuple[str | None, str | None]:
    """Known local hardware labels only. No serial or UUID queries."""
    system = platform.system()
    if system == "Windows":
        script = (
            "$ErrorActionPreference='Stop'; "
            "Get-CimInstance Win32_ComputerSystem | "
            "Select-Object -Property Manufacturer,Model | ConvertTo-Json -Compress"
        )
        data = run_json_command(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script]
        )
        return safe_label(data.get("Manufacturer")), safe_label(data.get("Model"))
    if system == "Linux":
        root = Path("/sys/class/dmi/id")

        def read(name: str) -> str | None:
            try:
                return safe_label((root / name).read_text(encoding="utf-8"))
            except (OSError, UnicodeError):
                return None

        return read("sys_vendor"), read("product_name")
    return None, None


def cpu_model() -> str | None:
    if platform.system() == "Linux":
        try:
            with Path("/proc/cpuinfo").open(encoding="utf-8") as stream:
                for line in stream:
                    if line.startswith("model name") and ":" in line:
                        return safe_label(line.split(":", 1)[1])
        except OSError:
            pass
    if platform.system() == "Windows":
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
            ) as key:
                return safe_label(winreg.QueryValueEx(key, "ProcessorNameString")[0])
        except (OSError, ImportError):
            pass
    return safe_label(platform.processor())


def environment_evidence() -> str | None:
    """Positive hints only; None explicitly means undetermined."""
    if platform.system() == "Linux":
        if Path("/.dockerenv").exists():
            return "Container indicator: /.dockerenv exists"
        try:
            cgroup = Path("/proc/1/cgroup").read_text(encoding="utf-8")
            if any(x in cgroup.lower() for x in ("docker", "kubepods", "containerd")):
                return "Container indicator: Linux cgroup marker"
        except OSError:
            pass
    release = platform.release().lower()
    if "microsoft" in release and platform.system() == "Linux":
        return "Virtualized environment indicator: WSL kernel"
    return None
