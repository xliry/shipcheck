from __future__ import annotations

from pathlib import Path
import sys

import click

from .engine import run_audit
from .report import render_json, render_markdown, render_terminal


@click.command()
@click.argument("target")
@click.option("--json", "as_json", is_flag=True, help="Print JSON report")
@click.option("--markdown", type=click.Path(), default="shipcheck-report.md", help="Write Markdown report")
@click.option("--threshold", type=int, default=None, help="Exit 1 if risk score is greater than N")
@click.option("--profile", default="next-supabase-stripe", show_default=True)
@click.option("--max-files", type=int, default=500, show_default=True)
@click.option("--include-tests", is_flag=True, default=False)
def main(target: str, as_json: bool, markdown: str, threshold: int | None, profile: str, max_files: int, include_tests: bool) -> None:
    if profile != "next-supabase-stripe":
        raise click.ClickException("v1 supports only --profile next-supabase-stripe")
    try:
        report = run_audit(target=target, profile=profile, max_files=max_files, include_tests=include_tests)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
    if as_json:
        click.echo(render_json(report))
    else:
        render_terminal(report)
        Path(markdown).write_text(render_markdown(report), encoding="utf-8")
        click.echo(f"Wrote {markdown}")
    if threshold is not None and report.score > threshold:
        sys.exit(1)
