from __future__ import annotations

import json
from unittest.mock import Mock

import pytest

from workstation_health import SCHEMA_VERSION
from workstation_health import cli
from workstation_health.demo import synthetic_observation
from workstation_health.render import render_html
from workstation_health.report import compose


def test_report_schema_and_no_unexpected_raw_keys(inventory):
    obs = synthetic_observation("healthy")
    obs["inventory"]["hardware"]["serial_number"] = "SERIAL-PRIVATE"
    obs["inventory"]["network"]["ip_address"] = "10.1.2.3"
    obs["inventory"]["storage"][0]["mountpoint"] = "/home/private"
    obs["secret"] = "TOKEN_PRIVATE"
    obs["collection_issues"] = [{"component": "storage", "reason": "permission_denied", "detail": "/Users/jane/secret"}]
    data = compose(obs, synthetic=True)
    encoded = json.dumps(data)
    assert data["schema_version"] == SCHEMA_VERSION
    assert set(data) == {"schema_version", "application", "scan", "summary", "inventory", "checks", "collection_issues", "limitations"}
    assert all(secret not in encoded for secret in ("SERIAL-PRIVATE", "TOKEN_PRIVATE", "10.1.2.3", "/home/private", "/Users/jane"))
    assert data["inventory"]["hardware"]["battery_percent"] is None
    assert data["scan"]["synthetic"] is True


def test_html_escaping_even_in_unexpected_values():
    obs = synthetic_observation("healthy")
    obs["inventory"]["hardware"]["cpu_model"] = '<script>alert("oops")</script>'
    obs["inventory"]["storage"][0]["label"] = '<img src=x onerror=alert(1)>'
    html = render_html(compose(obs, synthetic=True))
    assert "<script>" not in html
    assert "<img src=x" not in html
    assert '&lt;script&gt;' in html
    assert 'onerror=alert(1)&gt;' in html
    assert "SYNTHETIC DEMONSTRATION DATA" in html
    assert "http://" not in html and "https://" not in html


def test_demo_does_not_scan(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "collect", Mock(side_effect=AssertionError("host collected")))
    assert cli.main(["demo", "--output", str(tmp_path)]) == 0
    healthy = json.loads((tmp_path / "synthetic-healthy.json").read_text())
    attention = json.loads((tmp_path / "synthetic-attention-needed.json").read_text())
    assert healthy["scan"]["synthetic"] is True
    assert healthy["summary"]["status_counts"]["CRITICAL"] == 0
    assert attention["summary"]["status_counts"]["CRITICAL"] >= 1
    assert attention["summary"]["unavailable_check_ids"] == ["security.windows_defender"]
    assert "SYNTHETIC" in (tmp_path / "synthetic-healthy.html").read_text()


def test_cli_help_version_and_invalid_options(capsys, tmp_path):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    assert "scan" in capsys.readouterr().out
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    assert "0.1.0" in capsys.readouterr().out
    with pytest.raises(SystemExit) as exc:
        cli.main(["demo", "--format", "csv"])
    assert exc.value.code == 2
    assert cli.main(["scan", "--disk-warning-percent-free", "3", "--output", str(tmp_path)]) == 2
    assert cli.main(["scan", "--cpu-sample-seconds", "9", "--output", str(tmp_path)]) == 2


def test_collision_and_explicit_overwrite(tmp_path):
    assert cli.main(["demo", "--scenario", "healthy", "--output", str(tmp_path)]) == 0
    file = tmp_path / "synthetic-healthy.json"
    before = file.read_bytes()
    assert cli.main(["demo", "--scenario", "healthy", "--output", str(tmp_path)]) == 2
    assert file.read_bytes() == before
    assert cli.main(["demo", "--scenario", "healthy", "--output", str(tmp_path), "--overwrite"]) == 0
    assert file.read_bytes() == before


def test_preflight_both_scenarios_prevents_partial(tmp_path):
    existing = tmp_path / "synthetic-attention-needed.html"
    existing.write_text("existing")
    assert cli.main(["demo", "--output", str(tmp_path)]) == 2
    assert existing.read_text() == "existing"
    assert not (tmp_path / "synthetic-healthy.html").exists()


def test_scan_with_stubbed_collector_and_json_only(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "collect", lambda sample_seconds: synthetic_observation("healthy"))
    assert cli.main(["scan", "--output", str(tmp_path), "--format", "json"]) == 0
    assert (tmp_path / "workstation-health.json").exists()
    assert not (tmp_path / "workstation-health.html").exists()
    assert json.loads((tmp_path / "workstation-health.json").read_text())["scan"]["synthetic"] is False


def test_fatal_error_does_not_print_sensitive_exception(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "collect", Mock(side_effect=RuntimeError("/Users/alice/password")))
    assert cli.main(["scan", "--output", str(tmp_path)]) == 1
    assert "alice" not in capsys.readouterr().err
