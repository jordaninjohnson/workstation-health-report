# Changelog

## [0.1.0] — 2026-10-14

- First local CLI implementation with read-only hardware, OS, storage, network, CPU, memory, and battery snapshots where accessible.
- HTML and JSON reports with documented coverage and configurable threshold rules.
- Fixed privacy allowlist, generic failure reasons, synthetic examples and error-path tests.
- Windows/Linux CI workflow configuration, docs and interview learning walkthrough.
- Windows-specific security status providers are **not implemented**; Windows Defender is an explicit `UNKNOWN` check. Real Windows and macOS device validation remains pending.

**Release verification (2026-10-15):** [v0.1.0](https://github.com/jordaninjohnson/workstation-health-report/releases/tag/v0.1.0) was published from commit `f6ddafc11364ff89b4311f3025a8071720f46d41`, following a successful four-job [Windows/Linux CI run](https://github.com/jordaninjohnson/workstation-health-report/actions/runs/38681589575) on Python 3.10 and 3.13. Real Windows device behavior remains unverified.