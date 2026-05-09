import json

from shipcheck.engine import run_audit
from shipcheck.report import render_json, render_markdown


def test_json_and_markdown_reports_are_structured():
    report = run_audit("tests/fixtures/next_supabase_bad")
    data = json.loads(render_json(report))
    md = render_markdown(report)
    assert data["score"] >= 60
    assert "Top Risks" in md
    assert "Category Breakdown" in md
