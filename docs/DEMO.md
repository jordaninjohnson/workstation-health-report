# Three-minute interview demo

**Preparation:** Install in a Python virtual environment; have a browser open. Use the synthetic demo only. Do not screen-share a private real-machine report.

**0:00–0:35 · Context** — "This is a read-only, local Python CLI for documenting workstation facts and explaining simple thresholds. It is designed to avoid revealing usernames, network addresses and machine IDs. It is not a security certification tool."

**0:35–1:10 · Run**

```bash
workstation-health demo --output ./demo-reports
```

If previously generated, add `--overwrite`. Confirm that the CLI prints `SYNTHETIC`, creates HTML+JSON, and does **not** probe the computer.

**1:10–2:05 · Inspect HTML** — Open `demo-reports/synthetic-attention-needed.html`. Point out the prominent synthetic banner, critical low disk space, `UNKNOWN` Defender, and the coverage sentence. Explain: "An unknown check is never counted as passing; the rules are documented and configurable."

**2:05–2:35 · Inspect JSON** — Open `demo-reports/synthetic-attention-needed.json`. Show `schema_version`, `scan.synthetic`, `summary.status_counts`, and one `checks` record with stable ID, observation, rule, source and limitation.

**2:35–3:00 · Engineering summary** — "Collection, evaluation, field-level privacy filtering and HTML rendering are separate modules. Automated tests simulate timeouts, inaccessible disks and unsafe strings. I still need validation on a real authorized Windows 11 workstation before I claim Windows support is fully tested."

**Likely follow-up:** Asked about future work? Offer to add a read-only Windows feature only once its source and limits are verified; avoid saying Defender is assessed today.
