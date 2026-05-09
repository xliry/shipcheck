from shipcheck.engine import run_audit
from shipcheck.report import render_json


def test_bad_fixture_has_critical_secret_and_redacts_value():
    report = run_audit("tests/fixtures/next_supabase_bad")
    ids = {f.id for f in report.findings}
    output = render_json(report)
    assert "secrets.env_committed" in ids
    assert "secrets.client_service_role" in ids
    assert "sk_test_1234567890abcdefghijklmnop" not in output
    assert "...REDACTED" in output


def test_clean_fixture_has_no_critical_secret():
    report = run_audit("tests/fixtures/next_supabase_clean")
    assert not [f for f in report.findings if f.category == "secrets" and f.severity == "critical"]
