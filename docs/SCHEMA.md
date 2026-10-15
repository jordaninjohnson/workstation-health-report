# JSON contract (schema version 1.0)

The JSON document is UTF-8, self-contained, with exactly these top-level keys:

- `schema_version`: string, currently `"1.0"` (independent of application version).
- `application`: `{name: string, version: string}`.
- `scan`: `{timestamp: ISO-8601 timezone-aware string, privacy_mode: "default-minimal", synthetic: boolean, scenario: string|null}`.
- `summary`: `{headline: string, status_counts: object with OK/WARNING/CRITICAL/UNKNOWN/NOT_APPLICABLE integer counts, evaluated: int, total: int, coverage: string, actionable_check_ids: string[], unavailable_check_ids: string[]}`.
- `inventory.system`: `{os, os_version, architecture, kernel, python_version, boot_time, uptime_seconds, environment_evidence}`.
- `inventory.hardware`: `{manufacturer, model, cpu_model, physical_cores, logical_cores, ram_total_bytes, ram_available_bytes, ram_used_percent, battery_present, battery_percent, battery_plugged_in}`.
- `inventory.resources`: `{cpu_percent, cpu_sample_seconds}`.
- `inventory.storage`: array of `{label, filesystem, total_bytes, used_bytes, free_bytes, used_percent}` objects.
- `inventory.network`: `{interface_count, interfaces_up, interfaces: [{label, is_up, speed_mbps}]}`.
- `checks`: array of `{id, title, status, evidence, rule, interpretation, next_step, source, limitations}` objects.
- `collection_issues`: array of `{component, reason, detail}` categorical objects; reasons are `permission_denied`, `timeout`, `unsupported`, `collection_error`, `not_implemented` or `excluded`. Details are fixed safe phrases.
- `limitations`: array of explanatory strings.

**Unavailable values:** `null`, never a fabricated zero; collections may be `[]`. `battery_present: false` is reserved for definite no-battery evidence (such as controlled synthetic fixtures); `null` means the operating system returned no battery data or the query failed. A real no-result response is interpreted conservatively as unknown, because absence cannot be proved. `environment_evidence: null` means the evidence is undetermined, **not** a physical-device claim. For collection errors and deferred Windows Defender, status is `UNKNOWN`, not passing.

**Units:** All capacities are base-2 **bytes** in JSON and GiB in HTML (1 GiB = 2^30 bytes). Utilization and battery percentages are numeric units of percent (0–100). Time: ISO-8601 with UTC offset for `scan.timestamp`, seconds for `uptime_seconds` and `cpu_sample_seconds`. Network interface `speed_mbps` is a reported **megabits/second** nominal link speed, not throughput.

Consumers should identify fields by stable names and treat new schema versions as potentially incompatible. Synthetic examples deliberately reuse this identical shape.
