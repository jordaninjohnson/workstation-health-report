from __future__ import annotations

import json
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import psutil
import pytest

from workstation_health import collect as collector
from workstation_health.platform_helpers import run_json_command
from workstation_health.privacy import issue, safe_label, unavailable_reason


def test_disallowed_filesystems_and_remote_devices():
    def part(fs, opts="rw", device="/dev/vda1"):
        return SimpleNamespace(fstype=fs, opts=opts, device=device)
    assert collector.include_volume(part("ext4"))
    for fs in ("nfs", "cifs", "overlay", "fuse.sshfs", "tmpfs", "9p", ""):
        assert not collector.include_volume(part(fs))
    assert not collector.include_volume(part("ext4", "rw,removable"))
    assert not collector.include_volume(part("ntfs", device="\\\\server\\share"))


def test_privacy_safe_exception_and_label():
    assert unavailable_reason(PermissionError("/home/alice/hidden.txt")) == "permission_denied"
    assert unavailable_reason(TimeoutError("token=SECRET")) == "timeout"
    assert unavailable_reason(subprocess.TimeoutExpired("cmd", 2)) == "timeout"
    assert unavailable_reason(FileNotFoundError("private hostname")) == "unsupported"
    assert unavailable_reason(ValueError("my-private-password")) == "collection_error"
    assert "alice" not in issue("storage", "permission_denied")["detail"]
    assert safe_label("Intel Core i7") == "Intel Core i7"
    assert safe_label("/home/alice/private") is None
    assert safe_label("aa:bb:cc:dd:ee:ff") is None
    assert safe_label("192.168.1.1") is None
    assert safe_label("my.name@example.com") is None


def test_command_args_timeout_and_bad_json(monkeypatch):
    calls = []

    def completed(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout='{"Model":"Example"}')

    monkeypatch.setattr(subprocess, "run", completed)
    assert run_json_command(["mock.exe", "-Property", "Model"]) == {"Model": "Example"}
    assert calls[0][0] == ["mock.exe", "-Property", "Model"]
    assert calls[0][1]["timeout"] == 4.0
    assert calls[0][1]["check"] is False
    assert "shell" not in calls[0][1]

    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout="garbage")
    )
    with pytest.raises(ValueError):
        run_json_command(["x"])
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired("x", 4))
    )
    with pytest.raises(subprocess.TimeoutExpired):
        run_json_command(["x"])


def test_partial_failure_mock_collector(monkeypatch):
    monkeypatch.setattr(collector.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        collector.psutil,
        "boot_time",
        lambda: (_ for _ in ()).throw(PermissionError("/home/someone")),
    )
    monkeypatch.setattr(
        collector.psutil,
        "virtual_memory",
        lambda: (_ for _ in ()).throw(psutil.AccessDenied(pid=1)),
    )
    monkeypatch.setattr(collector.psutil, "sensors_battery", lambda: None)
    monkeypatch.setattr(collector.psutil, "cpu_percent", lambda interval: 22.5)
    monkeypatch.setattr(collector.psutil, "cpu_count", lambda logical: 8 if logical else 4)
    monkeypatch.setattr(
        collector.psutil,
        "disk_partitions",
        lambda all: [
            SimpleNamespace(mountpoint="/secret/home", device="/dev/sda1", fstype="ext4", opts="rw")
        ],
    )
    monkeypatch.setattr(
        collector.psutil,
        "disk_usage",
        lambda p: (_ for _ in ()).throw(PermissionError("alice private path")),
    )
    monkeypatch.setattr(
        collector.psutil,
        "net_if_stats",
        lambda: {"privateSSID": SimpleNamespace(isup=True, speed=1000)},
    )
    monkeypatch.setattr(collector, "manufacturer_model", lambda: ("Acme", "Desktop"))
    monkeypatch.setattr(collector, "cpu_model", lambda: "Sample CPU")
    monkeypatch.setattr(collector, "environment_evidence", lambda: None)
    data = collector.collect(sample_seconds=0.2)
    assert data["inventory"]["hardware"]["ram_total_bytes"] is None
    assert data["inventory"]["hardware"]["battery_present"] is None
    assert data["inventory"]["storage"] == []
    assert data["inventory"]["network"]["interfaces"][0]["label"] == "Interface 1"
    assert "privateSSID" not in json.dumps(data)
    assert "alice" not in json.dumps(data)
    assert len(data["collection_issues"]) >= 3
    assert all(i["reason"] == "permission_denied" for i in data["collection_issues"])


def test_timeout_collector_continues(monkeypatch):
    # Fully mocked: CI must not inspect runner hardware in this unit test.
    monkeypatch.setattr(collector.psutil, "boot_time", lambda: 1000)
    monkeypatch.setattr(
        collector.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(total=16 * 1024**3, available=8 * 1024**3, percent=50.0),
    )
    monkeypatch.setattr(collector.psutil, "sensors_battery", lambda: None)
    monkeypatch.setattr(collector.psutil, "disk_partitions", lambda all: [])
    monkeypatch.setattr(collector.psutil, "net_if_stats", lambda: {})
    monkeypatch.setattr(collector.psutil, "cpu_count", lambda logical: 4)
    monkeypatch.setattr(collector, "manufacturer_model", lambda: (None, None))
    monkeypatch.setattr(collector, "cpu_model", lambda: "Synthetic CPU")
    monkeypatch.setattr(collector, "environment_evidence", lambda: None)
    monkeypatch.setattr(
        collector.psutil, "cpu_percent", Mock(side_effect=TimeoutError("topsecret"))
    )
    data = collector.collect(sample_seconds=0.1)
    assert data["inventory"]["resources"]["cpu_percent"] is None
    assert {i["reason"] for i in data["collection_issues"]} >= {"timeout"}
    assert "topsecret" not in json.dumps(data)
