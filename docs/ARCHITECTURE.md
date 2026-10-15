# Architecture and data flow

```text
CLI parsing & validated thresholds
            |
            +--> demo: synthetic_observation() [no host probes]
            |
            +--> scan: collect() [read-only local psutil/platform sources]
                              |
                              v
                  internal observations + categorical issues
                              |
                              v
                    evaluate() [pure health rules]
                              |
                              v
                    compose() and summarize()
                              |
                              v
                    public_report() [field allowlist]
                           /      \
                          v        v
                    HTML escaping   JSON serialization
                          \        /
                           output files (exclusive creation)
```

- `collect.py`: read-only local inventory, component-isolated errors; local mount paths used only to query disk usage, not output. No networking, processes, user files or passwords.
- `platform_helpers.py`: credible, narrow platform metadata and `subprocess.run([...], timeout=4)` for Windows CIM manufacturer/model. Unexpected output is discarded, not executed.
- `evaluate.py`: stable IDs and comprehensible threshold checks. Evaluations never write system changes.
- `demo.py`: fabricated Windows-shaped observations, completely independent of `collect()`.
- `report.py`: creates scan metadata, evaluates if necessary, sorts findings, calculates coverage.
- `privacy.py`: fixed report serialization schema and no raw exception text. `render.py`: HTML escaping plus embedded offline CSS. `cli.py`: options, conflicts, file writing, success/error exit codes.

**Trust boundaries:** Operating system values, platform command output and exception messages are untrusted. Output must not include raw dictionaries or subprocess stderr. `safe_label()` conservatively filters selected hardware labels, while JSON/HTML have separate serialization/escaping. Threat model and remaining limitations: [Privacy](PRIVACY.md).

**Known tradeoff:** Sequential disk usage calls can block in native OS operations; wrapping those synchronous calls in a Python thread would not safely terminate the underlying kernel call. For that reason, obvious remote mounts are excluded, and no hard deadline is promised.
