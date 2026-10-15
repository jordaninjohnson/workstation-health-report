# Changelog

## [0.1.0] — 2026-10-14

- First local CLI implementation with read-only hardware, OS, storage, network, CPU, memory, and battery snapshots where accessible.
- HTML and JSON reports with documented coverage and configurable threshold rules.
- Fixed privacy allowlist, generic failure reasons, synthetic examples and error-path tests.
- Windows/Linux CI workflow configuration, docs and interview learning walkthrough.
- Windows-specific security status providers are **not implemented**; Windows Defender is an explicit `UNKNOWN` check. Real Windows and macOS device validation remains pending.

**Release gate:** Tag only after clean install, full local tests/lint/format checks, no real reports or secrets tracked, and at least one successful Windows and Linux hosted CI run. A changelog entry does **not** mean the release has been published.
