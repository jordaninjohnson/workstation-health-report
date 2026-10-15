# Troubleshooting

**`workstation-health: command not found`** — Activate the virtual environment in which `python -m pip install -e .` was executed, or use `python -m workstation_health ...` instead.

**PowerShell script activation blocked** — You may execute `.venv\Scripts\python.exe -m workstation_health --help` directly without changing PowerShell execution policy.

**Access denied / unavailable fields** — The tool is designed for standard-user permissions. Unknown values should remain unknown. Do not elevate solely to hide an unavailable finding. Linux containers often provide no readable physical volumes or manufacturer metadata.

**An output report already exists** — Pass a new `--output` directory, or use `--overwrite` only after deciding you no longer need the older report.

**CPU spike from a short sample** — Re-run during a representative workload. 0.25 seconds is not a sustained benchmark and does not imply a persistent issue.

**No Defender status** — It is intentionally deferred, not proof that Defender or another antivirus is missing. Check native Windows Security screens if you are authorized, but do not record their results as measured by this tool.

**Filesystem scan hangs** — A local kernel storage call can stall; abort with Ctrl+C where possible. Avoid scanning devices with malfunctioning or slow mounted filesystems. Known network and pseudo mounts are filtered, but timeout guarantees are not offered for native I/O.

**Install fails due to network/package index** — Install when an approved package source is available, or use an approved pre-downloaded wheel in your environment. The actual scan does not need internet connectivity.

**Output contains unexpected personal information** — Stop distributing the report, preserve a sanitized reproduction, and follow [SECURITY.md](../SECURITY.md). Use synthetic fixtures for bug reports.
