from shipcheck.engine import run_audit


def test_bad_fixture_flags_payment_risks():
    report = run_audit("tests/fixtures/next_supabase_bad")
    ids = {f.id for f in report.findings}
    assert "payments.webhook_no_signature" in ids
    assert "payments.success_grants_entitlement" in ids


def test_clean_fixture_avoids_signature_finding():
    report = run_audit("tests/fixtures/next_supabase_clean")
    assert not any(f.id == "payments.webhook_no_signature" for f in report.findings)
