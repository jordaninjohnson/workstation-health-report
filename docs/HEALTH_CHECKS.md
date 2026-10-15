# Health checks, rules, and interpretation

Default evaluation uses a single snapshot, not continuous monitoring. Configurable rules are applied only when their evidence is available. `UNKNOWN` is not OK, and missing data is never filled with guesses.

| Stable ID | Default warning | Default critical | Sources and limits |
| --- | --- | --- | --- |
| `storage.free` | Free **<= 15% OR <= 10 GiB** | Free **<= 5% OR <= 2 GiB** | `psutil.disk_partitions` and `disk_usage`, readable local volumes only; no SMART/backup evidence |
| `memory.utilization` | **>= 85% used** | **>= 95% used** | `psutil.virtual_memory`; a single sample does not prove a memory leak |
| `cpu.utilization` | **>= 85% used** | **>= 95% used** | `psutil.cpu_percent(interval=0.25)` by default; timed interval, not sustained benchmarking |
| `battery.charge` | Unplugged, **<= 20% charge** | Unplugged, **<= 10% charge** | `psutil.sensors_battery`; charge is not battery wear or service life |
| `security.windows_defender` | No thresholds | No thresholds | Windows-only `UNKNOWN`: reliable provider intentionally deferred; no claim about other antivirus software |

## Disk thresholds

For every readable included local volume, both free percentage and free GiB are computed from actual free/total bytes. **Either** a percentage or an absolute threshold crossing is sufficient. Critical takes precedence over warning. Equality **does** trigger a threshold. A large volume with 3% free is critical even if it has more than 2 GiB available; a small volume with 20% free is warning if the actual free space is 10 GiB or less. Unknown or excluded volumes are not evaluated. All evaluated volumes contribute to one `storage.free` result, reported at the worst observed severity.

All percentage thresholds must be finite, strictly positive and <= 100. Free-space GiB thresholds must be finite and strictly positive. Disk *critical-free* thresholds must be strictly **smaller** than warning-free thresholds. Memory/CPU *critical-used* values must be strictly **greater** than warning-used values. The CLI rejects contradictions. See `workstation-health scan --help` for exact option names.

## Other checks

Uptime is **context only**, with no healthy/unhealthy threshold. Battery absence can be not applicable when established; a real `psutil` no-result or battery query failure is conservatively unknown because it cannot prove absence. `cpu_percent` is called with a blocking interval so its first returned value is based on a real sample. An interface reported up does not prove internet access, and advertised link rate does not equal application throughput.

For Windows 11 in v0.1.0, there is no claimed Defender, Firewall or BitLocker proof. The synthetic attention-needed example includes an unavailable Defender check to teach coverage interpretation. No security assessment is attempted on other operating systems.

## Aggregation

Statuses are counted separately; `evaluated = OK + WARNING + CRITICAL`, and `applicable = evaluated + UNKNOWN`. `NOT_APPLICABLE` is excluded from applicable coverage. The headline prioritizes critical, then warning, then "No issues detected in evaluated checks". Any unknown adds "Some checks could not be completed." Actionable IDs enumerate warnings/critical items; unavailable IDs enumerate unknowns. The reports deliberately have **no numerical health score**.
