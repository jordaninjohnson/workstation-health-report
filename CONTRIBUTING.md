# Contributing to Workstation Inventory & Health Report

Thank you for your interest in making local computer diagnostics easier to understand. **You do not have to be an experienced software developer to contribute.** Documentation, a reproducer with synthetic data, clearer error messages, new tests and accessibility suggestions all help.

We prioritize **accurate evidence, user privacy, read-only behavior, small patches, and approachable code** over collecting every conceivable system fact. Please work on systems you own or are authorized to inspect, and never share private real-device reports.

## Before you start

1. Check the [README](README.md), [health-check definitions](docs/HEALTH_CHECKS.md), and existing issues.
2. For larger changes or new platforms, open a **feature request** first to discuss evidence sources, compatibility, testability and privacy impact.
3. For a small documentation or deterministic-test improvement, a focused PR is welcome without prior discussion.
4. Do not add cloud services, telemetry, network scanning, privileged probes, process enumeration, identifying device fields, or silent system modifications.

## Fork → clone → branch

1. Click **Fork** on the GitHub project, creating a repository under your account.
2. Clone your fork, for example:

   ```bash
   git clone https://github.com/YOUR-USERNAME/workstation-health-report.git
   cd workstation-health-report
   git switch -c docs/clarify-windows-setup
   ```

3. Keep unrelated modifications out of a pull request. Commit in logical units with a clear message describing what changed.

## Set up for development

Requires **Python 3.10+**, a supported Python package installer and `git`. Your first dependency install may require internet access. You do not need administrator privileges.

**Windows PowerShell (no activation required):**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\python.exe -m workstation_health demo --output demo-reports
```

**Linux / macOS:**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m workstation_health demo --output demo-reports
```

`demo` uses synthetic fixtures and **does not inspect the host**. Report output directories are ignored by Git. If you rerun a demo against an existing output, use a new directory or explicit `--overwrite`.

## Find your way around

| Location | Responsibility |
| --- | --- |
| `src/workstation_health/cli.py` | Arguments, output paths, exit codes and user-readable messages |
| `collect.py`, `platform_helpers.py` | Read-only system observations and limited platform-specific sources |
| `privacy.py` | Explicit allowed report fields and safe issue categories |
| `evaluate.py` | Stable health IDs, evidence, rules, status and next steps |
| `report.py` | Combines sanitized inventory and evaluated findings |
| `render.py` | Escaped, self-contained HTML output |
| `demo.py` | Synthetic host-independent fixtures |
| `tests/` | Deterministic tests for behavior, failure cases, privacy and CLI |
| `docs/` | Architecture, rules, privacy, schema, learning and demos |

Read [ARCHITECTURE.md](docs/ARCHITECTURE.md) and [LEARNING.md](docs/LEARNING.md) for a guided tour.

## Adding a collector

1. Define a narrow, read-only observation (for example, an accessible OS metadata field) with a credible local source.
2. Put platform access in `collect.py` or `platform_helpers.py`, with controlled failure behavior and bounded subprocess calls.
3. Decide **before collecting** whether the value can be safely included in a public-format report. Never include hostnames, hardware serials, IP/MAC addresses, usernames, identifiable paths, credentials or command output.
4. Update the *explicit allowlist* in `privacy.py` only if the field is intentionally safe and necessary. Unavailable values should be `null`, never invented.
5. Test supported, unsupported, malformed, permission-denied and timeout cases with mocks.
6. Update `docs/SCHEMA.md`, `docs/PRIVACY.md` and platform support if relevant.

## Adding a health check

1. Explain **what observable evidence supports** the finding and what it does not prove.
2. Choose a stable descriptive check ID, explicit evidence/rule, meaningful status, source, limitation and practical action.
3. Define boundary behavior in `evaluate.py`; ensure `UNKNOWN` is not counted as passing and `NOT_APPLICABLE` is used appropriately.
4. Write tests for equality to each threshold, values just above and below, absent data and invalid evidence.
5. Update `docs/HEALTH_CHECKS.md`, synthetic data and report examples when the resulting format changes.
6. Do not invent security conclusions from a single indicator; propose uncertain checks as deferred work instead.

## Good tests and pull requests

A useful test has a descriptive name, deterministic fake inputs, a meaningful assertion, and no reliance on the contributor's real machine. Use `pytest` monkeypatch or mocks for platform interfaces and subprocesses. Avoid tests that require administrator access, active networking, removable drives or exact platform vendor strings.

Before opening a PR, run:

```bash
python -m pytest -q
ruff check .
ruff format --check .
python -m compileall -q src
python -m workstation_health demo --output demo-reports
```

Use fresh output paths or explicit `--overwrite` for repeat runs. Submit a PR against `main` and fill in the [pull request template](.github/PULL_REQUEST_TEMPLATE.md). Clearly say which operating systems you **actually ran on** and which behaviors are covered only by mocks or hosted CI. A passing mocked test is not a Windows hardware validation.

If changing stable JSON keys or check semantics, explain compatibility and update the schema version if the change breaks existing consumers.

## Privacy rules for issues, screenshots and fixtures

**Never attach real workstation reports, raw exception messages, private path names, OS login names, addresses, hardware identifiers, credentials, or employer diagnostics.** Use the shipped `demo` scenarios or hand-written synthetic examples labeled as fabricated. Remove identifiers from stack traces and keep reproduction commands limited to authorized devices. Sensitive vulnerabilities must be reported privately as described in [SECURITY.md](SECURITY.md), not discussed in public issues.

## Starter contribution ideas

These are proposals, **not defects already confirmed**:

- **Documentation:** Add a short PowerShell troubleshooting example for a Python launcher not found, with an accurately verified alternative command.
- **Test:** Add a deterministic missing-CPU-metadata fixture to verify `null` and safe collection issue handling.
- **Accessibility:** Review the synthetic HTML with a screen reader or keyboard and submit a focused issue or test for clearer table headings and status wording.
- **Platform validation:** Compare Windows 11 observations with built-in system tools on an authorized machine and share only sanitized findings.

Small, well-tested changes are preferred to wide refactors. Please be courteous, patient and technical in feedback; assume good intent while holding changes to the project's privacy and correctness standards.
