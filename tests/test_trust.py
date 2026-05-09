from shipcheck.engine import run_audit


def test_bad_fixture_flags_placeholder_copy():
    report = run_audit("tests/fixtures/next_supabase_bad")
    assert any(f.id == "trust.placeholder_copy" for f in report.findings)


def test_clean_fixture_low_score_and_no_critical():
    report = run_audit("tests/fixtures/next_supabase_clean")
    assert report.score <= 30
    assert not any(f.severity == "critical" for f in report.findings)
