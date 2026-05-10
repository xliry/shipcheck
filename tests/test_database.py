from shipcheck.engine import run_audit


def test_bad_fixture_flags_database_risks():
    report = run_audit("tests/fixtures/next_supabase_bad")
    ids = {f.id for f in report.findings}
    assert "database.wide_open_policy" in ids


def test_clean_fixture_has_no_database_findings():
    report = run_audit("tests/fixtures/next_supabase_clean")
    assert not [f for f in report.findings if f.category == "database"]


def test_server_only_service_role_helper_is_not_browser_exposure(tmp_path):
    helper = tmp_path / "src" / "libs" / "supabase" / "supabase-admin.ts"
    helper.parent.mkdir(parents=True)
    helper.write_text(
        """
        import "server-only";
        export const serviceRole = process.env.SUPABASE_SERVICE_ROLE_KEY!;
        """,
        encoding="utf-8",
    )
    report = run_audit(str(tmp_path))
    assert not any(f.id == "database.service_role_browser" for f in report.findings)


def test_client_service_role_usage_remains_browser_exposure(tmp_path):
    component = tmp_path / "components" / "Account.tsx"
    component.parent.mkdir(parents=True)
    component.write_text(
        """
        "use client";
        export const serviceRole = process.env.SUPABASE_SERVICE_ROLE_KEY!;
        """,
        encoding="utf-8",
    )
    report = run_audit(str(tmp_path))
    assert any(f.id == "database.service_role_browser" for f in report.findings)
