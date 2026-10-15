"""User-facing CLI; uses explicit exit codes and safe file output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .collect import collect
from .demo import synthetic_observation
from .evaluate import Thresholds
from .render import render_html
from .report import compose


def formats(value: str) -> tuple[str, ...]:
    values = tuple(v.strip() for v in value.split(","))
    if not values or len(set(values)) != len(values) or not set(values) <= {"html", "json"}:
        raise argparse.ArgumentTypeError(
            "--format must be html, json, or html,json (without repeats)"
        )
    return values


def float_threshold(value: str) -> float:
    try:
        parsed = float(value)
        from math import isfinite

        if not isfinite(parsed) or parsed <= 0:
            raise ValueError
        return parsed
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a finite positive number") from exc


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="workstation-health",
        description="Read-only local inventory and explainable health reports; no network telemetry.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)
    for command in ("scan", "demo"):
        c = sub.add_parser(
            command,
            help="Scan this authorized computer"
            if command == "scan"
            else "Generate synthetic examples without inspecting the host",
        )
        c.add_argument(
            "--output",
            type=Path,
            default=Path("reports"),
            help="Output directory (default: ./reports)",
        )
        c.add_argument(
            "--format",
            type=formats,
            default=("html", "json"),
            help="html, json, or html,json (default)",
        )
        c.add_argument(
            "--overwrite", action="store_true", help="Explicitly replace existing named reports"
        )
        if command == "scan":
            c.add_argument(
                "--cpu-sample-seconds",
                type=float_threshold,
                default=0.25,
                help="CPU blocking sample interval in seconds (0.1–5)",
            )
            for option, default in (
                ("disk-warning-percent-free", 15),
                ("disk-critical-percent-free", 5),
                ("disk-warning-gib-free", 10),
                ("disk-critical-gib-free", 2),
                ("memory-warning-percent-used", 85),
                ("memory-critical-percent-used", 95),
                ("cpu-warning-percent-used", 85),
                ("cpu-critical-percent-used", 95),
            ):
                c.add_argument(f"--{option}", type=float_threshold, default=default)
        else:
            c.add_argument(
                "--scenario", choices=("healthy", "attention-needed", "all"), default="all"
            )
    return p


def make_thresholds(args: argparse.Namespace) -> Thresholds:
    return Thresholds(**{key: getattr(args, key) for key in Thresholds.__dataclass_fields__})


def write_reports(
    data: dict, out: Path, basename: str, requested: tuple[str, ...], *, overwrite: bool
) -> list[Path]:
    targets = [(out / f"{basename}.{extension}", extension) for extension in requested]
    if any(path.exists() for path, _ in targets) and not overwrite:
        raise ValueError("A report already exists; choose another directory or pass --overwrite")
    if out.exists() and not out.is_dir():
        raise ValueError("Output path is not a directory")
    out.mkdir(parents=True, exist_ok=True)
    for path, extension in targets:
        text = (
            render_html(data)
            if extension == "html"
            else json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        )
        # Exclusive creation protects against unexpected overwrites even after preflight.
        with path.open("w" if overwrite else "x", encoding="utf-8") as stream:
            stream.write(text)
    return [path for path, _ in targets]


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "scan":
            if not 0.1 <= args.cpu_sample_seconds <= 5:
                raise ValueError("CPU sample interval must be between 0.1 and 5 seconds")
            limits = make_thresholds(args)
            limits.validate()
            jobs = [
                (
                    "workstation-health",
                    compose(collect(sample_seconds=args.cpu_sample_seconds), limits=limits),
                )
            ]
        else:
            scenarios = (
                ("healthy", "attention-needed") if args.scenario == "all" else (args.scenario,)
            )
            jobs = [
                (
                    f"synthetic-{scenario}",
                    compose(synthetic_observation(scenario), synthetic=True, scenario=scenario),
                )
                for scenario in scenarios
            ]
        # Preflight all target names to avoid partial output on collisions.
        targets = [args.output / f"{name}.{ext}" for name, _ in jobs for ext in args.format]
        if not args.overwrite and any(path.exists() for path in targets):
            raise ValueError(
                "An output report already exists; choose another directory or use --overwrite"
            )
        for name, data in jobs:
            for path in write_reports(
                data, args.output, name, args.format, overwrite=args.overwrite
            ):
                print(f"Created: {path}")
            summary = data["summary"]
            label = "SYNTHETIC " if data["scan"]["synthetic"] else ""
            print(f"{label}{name}: {summary['headline']} {summary['coverage']}")
        return 0
    except (ValueError, FileExistsError) as exc:
        print(f"Configuration/output error: {exc}", file=sys.stderr)
        return 2
    except Exception:
        # No untrusted exception text can reach output (or public diagnostics).
        print(
            "Execution failed; check output permissions and local Python installation.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
