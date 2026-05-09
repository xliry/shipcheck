from __future__ import annotations

import json
from dataclasses import asdict

from rich.console import Console
from rich.table import Table

console = Console()


def render_json(report) -> str:
    return json.dumps(asdict(report), indent=2)


def render_terminal(report) -> None:
    table = Table(title=f"ShipCheck: {report.score}/100 ({report.verdict})")
    table.add_column("Category")
    table.add_column("Score", justify="right")
    for name, data in report.categories.items():
        table.add_row(name, f"{data['score']}/{data['max_score']}")
    console.print(table)
    for finding in report.findings[:10]:
        loc = f" ({finding.file}:{finding.line})" if finding.file and finding.line else ""
        console.print(f"[bold]{finding.severity.upper()}[/bold] {finding.title}{loc}")


def render_markdown(report) -> str:
    lines = [
        "# ShipCheck Report", "", f"Target: `{report.target}`", f"Risk score: **{report.score}/100**",
        f"Verdict: **{report.verdict}**", "", report.summary, "", "## Top Risks", "",
    ]
    top = report.findings[:5]
    lines.extend([f"{i}. [{f.severity.upper()}] {f.title}" for i, f in enumerate(top, 1)] or ["No findings."])
    lines.extend(["", "## Category Breakdown", ""])
    for name, data in report.categories.items():
        lines.append(f"- {name}: {data['score']}/{data['max_score']}")
    lines.extend(["", "## Findings", ""])
    if not report.findings:
        lines.append("No findings.")
    for i, f in enumerate(report.findings, 1):
        loc = f"{f.file}:{f.line}" if f.file and f.line else (f.file or "repo")
        lines.extend([
            f"### {i}. [{f.severity.upper()}] {f.title}", "",
            f"- Category: `{f.category}`", f"- Location: `{loc}`",
            f"- Evidence: `{f.evidence or 'No direct snippet'}`",
            f"- Why it matters: {f.why_it_matters}", f"- Remediation: {f.remediation}", "",
        ])
    return "\n".join(lines)
