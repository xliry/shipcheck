from shipcheck.engine import run_audit


def test_bad_fixture_flags_database_risks():
    report = run_audit("tests/fixtures/next_supabase_bad")
    ids = {f.id for f in report.findings}
    assert "database.wide_open_policy" in ids
    assert "database.service_role_browser" in ids


def test_clean_fixture_has_no_database_findings():
    report = run_audit("tests/fixtures/next_supabase_clean")
    assert not [f for f in report.findings if f.category == "database"]
