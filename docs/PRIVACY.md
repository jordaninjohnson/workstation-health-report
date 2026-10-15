# Privacy and threat considerations

**Intent:** A local, read-only assessment that minimizes accidental disclosure when demonstrating diagnostic capability. This is not a hardened security boundary against a malicious local administrator or a compromised Python installation.

## Collection surface

Only a minimal set of local OS and `psutil` APIs are read: OS/kernel, CPU and memory statistics, uptime, supported hardware labels, battery, storage summary and network interface state. No configured network probes, remote service calls, file enumeration, credentials, process listings, installed software inventories, browser data, public IPs, usernames, hostnames or interface addresses. The Windows-only CIM query selects only `Manufacturer` and `Model`, with shell disabled and a four-second command timeout. No system settings are altered.

## Disclosure defenses

1. Internal collection values pass through the report's explicit field allowlist. Device names, mount paths and interface names are not fields in the public output.
2. Displayed hardware model/CPU labels are conservatively sanitized; names resembling paths, IPs, MAC addresses and email addresses are rejected.
3. Exception messages (which may include paths, usernames or command stderr) are replaced with fixed reason categories and strings. Raw tracebacks are not printed by the CLI.
4. HTML escapes dynamic content, embeds its own CSS and references no external assets. JSON uses primitive serializable values and explicit nulls.
5. Existing report paths are never silently overwritten. Reports, diagnostics, caches, virtual environments, local secrets and configuration files are in `.gitignore`.
6. The supplied public examples are fully synthetic and must remain so; the demo function never calls the host collector.

## Residual risks and practical guidance

- **Real reports can still be sensitive:** make/model, resource levels and approximate device age may be identifying in some situations. Review before sending them. Do not commit private workstation reports, even if ignored by Git.
- **OS data is not necessarily trustworthy:** psutil, CIM, virtualized devices and firmware may return incomplete or spoofed details. This application does not authenticate firmware or hardware.
- **Error handling is conservative, but not absolute:** a future developer may accidentally add fields; keep tests for untrusted input and allowlist controls. Avoid using raw system values inside `evidence` or `source` descriptions.
- **Filesystem calls can block at OS level:** remote filesystems are excluded where recognizable, but a mislabeled mount or local storage fault can still cause a slow/hung query. The four-second timeout applies only to the external Windows CIM command, not native filesystem calls.
- **External dependencies:** installing Python packages entails trust in the package distribution and index; follow your normal software supply-chain hygiene. `psutil` does not trigger scanning telemetry here.

## Explicitly not security assurance

Defender/Firewall/BitLocker effectiveness, patch compliance, malware absence, SMART wear and backup recoverability are outside the verified scope of version 0.1.0. `UNKNOWN` means no evidence, **not** that protection is disabled. No numerical security score is computed.
