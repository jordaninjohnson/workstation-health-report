# Maintainer publishing and release checklist

The [v0.1.0 release](https://github.com/jordaninjohnson/workstation-health-report/releases/tag/v0.1.0) was published from CI-verified commit `f6ddafc11364ff89b4311f3025a8071720f46d41` after the [four-job hosted matrix passed](https://github.com/jordaninjohnson/workstation-health-report/actions/runs/38681589575). Subsequent release work should follow the checks below.

This project targets the public repository [`jordaninjohnson/workstation-health-report`](https://github.com/jordaninjohnson/workstation-health-report). Whether the repository actually contains this tree, has passing Actions, and has a published release **must be verified through GitHub**; local tests and prepared Git commits are not equivalent to publication.

## First upload

1. Confirm the linked GitHub identity is `jordaninjohnson` and the target is that personal account, not an organization.
2. Inspect the remote before pushing; **do not force-push** or overwrite other work. The original source arrived as a Git bundle with local commit `86b72272f83ace6aa1d3c40515cb7d5ecc599efe`. Preserve it where tools permit; if the remote was bootstrapped differently, retain the bundle for historical reference and document the actual commit ancestry.
3. Review staged files: `git status`, `git diff --cached --stat`, `git diff --cached`, `git ls-files`. Confirm private scan reports, credentials, env files and caches are excluded.
4. Verify clean install, package import, CLI help/version, synthetic scenarios, `pytest`, `ruff check .`, `ruff format --check .` and relevant docs links. An offline environment may prevent installing Ruff; record it as **not verified**.
5. Push to the authorized existing repository and verify source files and SHA by reading the remote back.
6. Inspect GitHub Actions jobs for Linux and Windows; fix project failures without claiming that hosted mocks validate real workstation hardware.

## Release requirements

Publish `v0.1.0` only when **all** of these are true:

- Source published to the verified personal repository.
- Installable application and synthetic output smoke tests pass.
- Required tests, Ruff lint and formatting checks pass.
- The hosted Windows and Linux CI matrix succeeds.
- README, CONTRIBUTING, SECURITY and changelog describe **implemented** features accurately.
- No actual computer reports, sensitive paths or credentials are tracked.
- Synthetic preview and sample reports are properly marked.

Then tag the passing commit and prepare release notes covering features, installation, privacy, platform limitations, known issues and future enhancements. **Do not tag an unverified build.**

## After publishing

Review your repository settings manually for useful items such as a short description, topics, community health files, and private vulnerability reporting where GitHub offers them. Do not enable broad permissions or automated privileges merely to improve a score or badge. Encourage small testable pull requests and handle security reports outside public issues.
