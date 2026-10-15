# Learning by maintaining this project

## Follow the data

1. `cli.main()` parses options, selects `scan` or `demo`, validates options, and chooses output files.
2. `collect.collect()` queries only local OS data; failures become categorical `collection_issues`. Demo data bypasses this module.
3. `evaluate.evaluate()` applies pure health rules and assigns one of five statuses.
4. `report.compose()` sorts checks and calculates assessment coverage, then `privacy.public_report()` constructs an allowlisted document.
5. `render.render_html()` HTML-escapes every dynamic field; the CLI writes HTML or serializes the same object as JSON.

## Add a collector responsibly

Choose one authorized, read-only source, describe precisely what it proves, and avoid personally identifying data. Add a small `attempt(component, ...)` call inside `collect.py`, returning `None` if unsupported. Add its output field to the intentional allowlist in `privacy.py` *only if safe*, along with the documented JSON contract. Test the source with mocks for success, access denied, malformed responses and timeouts; avoid promoting an OS indicator into a cybersecurity guarantee.

## Add a health check

Use `evaluate.py` and create a stable `finding(id, title, status, evidence, rule, interpretation, next_step, source, limitations)` value. If evidence is missing, return `UNKNOWN` or `NOT_APPLICABLE` as appropriate. Document exact boundary behavior in `docs/HEALTH_CHECKS.md`. Call the pure check from `evaluate()` and preserve sorting and coverage rules.

## Write a meaningful test

Begin with a specification, not a copy of the implementation. For a threshold of 15%, test `14.999`, `15.0`, and `15.001`, and also test when an absolute GiB threshold overrides the percentage rule. For a collector, mock the platform source and make it throw a `PermissionError` containing a fake sensitive path; assert that the final report never includes that text. Assert a failure does not stop unrelated collectors.

## Design decisions to explain in an interview

- Why a **fixed allowlist** protects better than stripping known secret fields from a raw dictionary.
- Why `UNKNOWN` and `NOT_APPLICABLE` are distinct, and why a pass is narrow.
- Why a sampled CPU value is not a 24-hour performance diagnosis.
- Why disk checks use **OR** between percent and absolute thresholds, and why exact boundaries matter.
- Why external Windows CIM calls have timeouts and argument lists, while native filesystem calls cannot promise a hard deadline.
- Why publicly shared examples are entirely synthetic.

## Required real-world validation before stronger support claims

- On an **authorized personal Windows 11 machine**, install as standard user; verify CIM manufacturer/model, registry CPU name, core counts, battery behavior (if present), and NTFS capacity versus native Windows displays. Record discrepancies **privately**, then publish only fabricated reproductions.
- On a **non-container Linux desktop**, confirm local storage filtering and compare reported free space against `df`; in isolated containers storage may be `UNKNOWN`.
- macOS behavior has not been real-device tested; treat all features as best-effort.
- Windows Defender, Firewall, encryption, SMART and backups are **not** validated checks and should not be described as implemented.

Finally, practice explaining a real bug you fixed by adding a failing test, making the smallest code change, and re-running the suite. That is stronger interview evidence than presenting a pretty dashboard alone.
