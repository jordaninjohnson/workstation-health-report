"""Offline, print-friendly HTML built from the public report allowlist."""

from __future__ import annotations

import html
from typing import Any


def esc(value: Any) -> str:
    if value is None:
        return "Not available"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return html.escape(str(value), quote=True)


def gib(value: int | None) -> str:
    return f"{value / 1024**3:,.1f} GiB" if isinstance(value, (int, float)) else "Not available"


def stat_value(value: float | None, suffix: str = "%") -> str:
    return f"{value:,.1f}{suffix}" if isinstance(value, (float, int)) else "Not available"


def card(label: str, value: str) -> str:
    return f'<div class="metric"><span>{esc(label)}</span><strong>{value}</strong></div>'


def row(label: str, value: Any) -> str:
    return f"<tr><th scope='row'>{esc(label)}</th><td>{esc(value)}</td></tr>"


def render_html(data: dict[str, Any]) -> str:
    scan = data["scan"]
    summary = data["summary"]
    inventory = data["inventory"]
    hw, sysinfo, res, network = (inventory[x] for x in ("hardware", "system", "resources", "network"))
    synthetic = scan["synthetic"]
    banner = (
        '<div class="synthetic" role="note"><strong>SYNTHETIC DEMONSTRATION DATA</strong> — '
        'No computer was scanned. Values and findings are illustrative only.</div>'
    ) if synthetic else '<div class="privacy">Local read-only scan · Minimal privacy mode · Never transmitted by this application</div>'
    status_counts = "".join(
        card(s.replace("_", " ").title(), str(summary["status_counts"].get(s, 0)))
        for s in ("CRITICAL", "WARNING", "UNKNOWN", "OK", "NOT_APPLICABLE")
    )
    overview = "".join((
        card("CPU use, sampled", esc(stat_value(res["cpu_percent"]))),
        card("RAM in use", esc(stat_value(hw["ram_used_percent"]))),
        card("Available memory", esc(gib(hw["ram_available_bytes"]))),
        card("Interfaces up", esc(network["interfaces_up"])),
    ))
    sysrows = "".join((
        row("Operating system", sysinfo["os"]), row("OS version", sysinfo["os_version"]),
        row("Kernel / build", sysinfo["kernel"]), row("Architecture", sysinfo["architecture"]),
        row("Manufacturer", hw["manufacturer"]), row("Model", hw["model"]),
        row("CPU", hw["cpu_model"]), row("Physical / logical cores", f"{hw['physical_cores'] or 'Unknown'} / {hw['logical_cores'] or 'Unknown'}"),
        row("Total RAM", gib(hw["ram_total_bytes"])), row("Python", sysinfo["python_version"]),
        row("Uptime", f"{sysinfo['uptime_seconds'] / 3600:.1f} hours" if sysinfo["uptime_seconds"] is not None else None),
        row("Environment hint", sysinfo["environment_evidence"] or "Undetermined — not proof of a physical machine"),
        row("Battery", "Present" if hw["battery_present"] else "Not reported"),
        row("Battery charge", stat_value(hw["battery_percent"])),
        row("Connected to power", hw["battery_plugged_in"]),
    ))
    storage_rows = "".join(
        "<tr>" + "".join(f"<td>{v}</td>" for v in (
            esc(d["label"]), esc(d["filesystem"]), esc(gib(d["total_bytes"])),
            esc(gib(d["free_bytes"])), esc(stat_value(d["used_percent"])),
        )) + "</tr>" for d in inventory["storage"]
    ) or '<tr><td colspan="5">No readable local storage volumes.</td></tr>'
    netrows = "".join(
        f"<tr><td>{esc(i['label'])}</td><td>{'Up' if i['is_up'] else 'Down'}</td>"
        f"<td>{esc(str(i['speed_mbps']) + ' Mbps' if i['speed_mbps'] else None)}</td></tr>"
        for i in network["interfaces"]
    ) or '<tr><td colspan="3">Interface observations unavailable.</td></tr>'
    checks = "".join(
        f'<article class="finding {esc(c["status"].lower())}">'
        f'<div class="finding-head"><h3>{esc(c["title"])}</h3><span class="tag">{esc(c["status"].replace("_", " "))}</span></div>'
        f'<p class="evidence">Observed: {esc(c["evidence"])}</p>'
        f'<p>{esc(c["interpretation"])}</p>'
        f'<p><b>Rule:</b> {esc(c["rule"])}</p>'
        + (f'<p><b>Next step:</b> {esc(c["next_step"])}</p>' if c["next_step"] else "")
        + f'<small>Source: {esc(c["source"])} · Limits: {esc(c["limitations"])} · ID: {esc(c["id"])}</small></article>'
        for c in data["checks"]
    )
    issue_rows = "".join(
        f'<li><b>{esc(i["component"])}</b> — {esc(i["reason"].replace("_", " "))}: {esc(i["detail"])}</li>'
        for i in data["collection_issues"]
    ) or "<li>No collection errors recorded.</li>"
    limits = "".join(f"<li>{esc(v)}</li>" for v in data["limitations"])
    action = ", ".join(summary["actionable_check_ids"]) or "None"
    unknown = ", ".join(summary["unavailable_check_ids"]) or "None"
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Workstation Inventory &amp; Health Report</title>
<style>
:root{{--ink:#17253c;--muted:#4c6075;--line:#d9e2e9;--paper:#f4f7fb;--blue:#164f89;--white:#fff}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}
header{{background:#132f51;color:#fff;padding:2.8rem max(1.2rem,calc((100vw - 1080px)/2)) 2rem}}
.eyebrow{{text-transform:uppercase;letter-spacing:.15em;font-size:.75rem;font-weight:700;color:#bedaf3}}
h1{{font-size:clamp(1.6rem,3.5vw,2.5rem);line-height:1.2;margin:.7rem 0}} header p{{color:#e2eef8}}
main{{max-width:1080px;margin:0 auto;padding:1.25rem}} h2{{font-size:1.3rem;margin:0 0 1rem}} h3{{font-size:1rem;margin:0}}
section{{background:white;border:1px solid var(--line);border-radius:14px;padding:1.3rem;margin:1.25rem 0;break-inside:avoid}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:10px}} .metric{{border:1px solid var(--line);border-radius:9px;padding:1rem;background:#f9fbfd}}
.metric span{{display:block;color:var(--muted);font-size:.84rem}} .metric strong{{display:block;font-size:1.55rem;line-height:1.5}}
.synthetic{{border:2px solid #8e5500;background:#fff2d9;color:#563000;padding:1rem;font-weight:600;margin-top:1.3rem;border-radius:9px}}
.privacy{{background:#e5f3ed;color:#165a39;padding:1rem;margin-top:1.3rem;border-radius:8px}}
.hero{{font-size:1.2rem;font-weight:700}} .muted,small{{color:var(--muted)}} table{{width:100%;border-collapse:collapse;text-align:left}}th,td{{padding:.66rem;border-bottom:1px solid var(--line);vertical-align:top}} th{{font-weight:600;color:#33495d}} .scroll{{overflow-x:auto}}
.finding{{padding:1rem;border:1px solid var(--line);border-left:5px solid #62758a;border-radius:8px;margin:12px 0;break-inside:avoid}}
.finding.warning{{border-left-color:#ae6800}} .finding.critical{{border-left-color:#b12c35}} .finding.ok{{border-left-color:#24724a}}
.finding-head{{display:flex;justify-content:space-between;gap:1rem;align-items:flex-start}}.tag{{border:1px solid currentColor;border-radius:5px;padding:.15rem .55rem;font-size:.78rem;font-weight:750;white-space:nowrap}}
.evidence{{font-weight:650}} .finding p{{margin:.5rem 0}} .finding small{{display:block;margin-top:.8rem}}li{{margin:.4rem 0}} footer{{text-align:center;color:var(--muted);padding:2rem}}
@media print{{body{{background:#fff;font-size:11pt}}header{{background:#fff;color:#17253c;padding:1rem 0;border-bottom:2px solid #17253c}}header p,.eyebrow{{color:#17253c}}main{{padding:0}}section{{border:0;border-bottom:1px solid #ccc;border-radius:0;margin:.5rem 0;padding:1rem 0}}.finding{{break-inside:avoid}}}}
</style></head>
<body><header><div class="eyebrow">Local diagnostics · v{esc(data['application']['version'])}</div>
<h1>Workstation Inventory &amp; Health Report</h1>
<p>Human-readable system facts, explainable thresholds, and clear limits. No hidden health score.</p></header>
<main>{banner}
<section aria-labelledby="assessment"><h2 id="assessment">Assessment overview</h2><p class="hero">{esc(summary['headline'])}</p>
<p class="muted">{esc(summary['coverage'])} · Observed {esc(scan['timestamp'])} · Privacy: {esc(scan['privacy_mode'])}</p>
<div class="grid">{status_counts}</div><p><b>Actionable checks:</b> {esc(action)}. <b>Unavailable:</b> {esc(unknown)}.</p></section>
<section><h2>Resource snapshot</h2><p class="muted">A momentary observation, not a sustained performance test. CPU sample interval: {esc(res['cpu_sample_seconds'])} seconds.</p><div class="grid">{overview}</div></section>
<section><h2>Hardware &amp; operating system</h2><div class="scroll"><table><tbody>{sysrows}</tbody></table></div></section>
<section><h2>Local storage</h2><div class="scroll"><table><thead><tr><th>Volume</th><th>Filesystem</th><th>Capacity</th><th>Free</th><th>Used</th></tr></thead><tbody>{storage_rows}</tbody></table></div><small>1 GiB = 1,073,741,824 bytes. Network, pseudo and removable filesystems are excluded when identifiable. Names and mount paths are intentionally omitted.</small></section>
<section><h2>Network interfaces</h2><div class="scroll"><table><thead><tr><th>Interface</th><th>Operational state</th><th>Reported link speed</th></tr></thead><tbody>{netrows}</tbody></table></div><small>No addresses, network names or connection testing. Link speed is not throughput; up does not mean online.</small></section>
<section><h2>Findings, ordered by importance</h2>{checks}</section>
<section><h2>Collection limitations</h2><ul>{issue_rows}</ul></section>
<section><h2>What this report does not verify</h2><ul>{limits}</ul></section>
</main><footer>Workstation Inventory &amp; Health Report · Offline, local-only report · v{esc(data['application']['version'])}</footer></body></html>'''
