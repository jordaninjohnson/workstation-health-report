# Operations interview walkthrough — evidence and limits

This document explains how to demonstrate **existing, real code** in this repository to a technical interviewer. It does **not** imply that this utility is deployed to an enterprise fleet.

## Five-minute live demonstration

1. Clone this public repository to an **authorized training computer** and read the README's safety section.
2. Create a virtual environment and install the package as instructed in the README.
3. Run `python -m workstation_health demo --scenario attention-needed --output demo-attention`. This uses synthetic fixture data; no host inventory is collected.
4. Open the generated HTML file. Explain which measurements are **critical**, **warning**, **unavailable**, or **not applicable**. Explain why unavailable evidence must never be reported as healthy.
5. Inspect the matching JSON file. Discuss how a system operator might use structured output in authorized inventory or ticket workflows.
6. Run the automated test suite and inspect the existing Linux/Windows CI workflow in `.github/workflows/ci.yml`. State the actual workflow result; an available workflow file alone is not proof of a green build.

## Technical discussion prompts

- **Scope:** What is the difference between a short local health snapshot and continuous enterprise monitoring?
- **Disk pressure:** Why does percent free matter? How do file-system sizes, mounts, and workload growth affect interpretation?
- **Service ownership:** What should an administrator do when a collector cannot access a metric?
- **Change safety:** Why should a utility default to read-only collection and avoid overwriting output?
- **Security:** Why avoid collecting credentials, addresses, usernames, or other unrelated private metadata?
- **Troubleshooting:** What information would you gather before restarting a production service?
- **Escalation:** When should you engage server, storage, network, database, or security colleagues?
- **Productionization:** What would need to change before a tool like this could be used operationally—identity, authorization, secure storage, CI, agent deployment, alerting, inventory integration, test coverage, change control and retention?

## Boundaries

This is an independent software project and an illustrative operations tool, **not** an assertion of professional Linux server administration, production storage management, backup ownership, or infrastructure team employment. Demonstrate only commands you have tested on an environment you control, and do not publish scans of real devices.

## Behavioral interview bridge

A candidate with experience supporting technology-intensive services can relate the design decisions here to principles that apply in any production environment: clear status, minimizing surprises, isolating failures, communicating uncertainty, preserving evidence, documenting recovery, and escalating appropriately. Explain the practical source of those principles separately from hands-on Linux infrastructure experience.
