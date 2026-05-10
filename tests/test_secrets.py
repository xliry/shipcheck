from shipcheck.engine import run_audit
from shipcheck.report import render_json


def test_bad_fixture_has_critical_secret_and_redacts_value():
    report = run_audit("tests/fixtures/next_supabase_bad")
    ids = {f.id for f in report.findings}
    output = render_json(report)
    assert "secrets.env_committed" in ids
    assert "sk_test_1234567890abcdefghijklmnop" not in output
    assert "...REDACTED" in output


def test_clean_fixture_has_no_critical_secret():
    report = run_audit("tests/fixtures/next_supabase_clean")
    assert not [f for f in report.findings if f.category == "secrets" and f.severity == "critical"]


def test_server_only_service_role_helper_is_not_client_secret(tmp_path):
    helper = tmp_path / "src" / "libs" / "supabase" / "supabase-admin.ts"
    helper.parent.mkdir(parents=True)
    helper.write_text(
        """
        import "server-only";
        export const key = process.env.SUPABASE_SERVICE_ROLE_KEY!;
        """,
        encoding="utf-8",
    )
    report = run_audit(str(tmp_path))
    assert not any(f.id == "secrets.client_service_role" for f in report.findings)


def test_client_reachable_service_role_remains_critical(tmp_path):
    component = tmp_path / "components" / "Billing.tsx"
    component.parent.mkdir(parents=True)
    component.write_text(
        """
        "use client";
        export const key = process.env.SUPABASE_SERVICE_ROLE_KEY!;
        """,
        encoding="utf-8",
    )
    report = run_audit(str(tmp_path))
    assert any(f.id == "secrets.client_service_role" and f.severity == "critical" for f in report.findings)


def test_publishable_google_maps_key_is_not_high_secret_noise(tmp_path):
    component = tmp_path / "components" / "Map.tsx"
    component.parent.mkdir(parents=True)
    component.write_text(
        """
        "use client";
        const key = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
        const secret = process.env.NEXT_PUBLIC_STRIPE_SECRET;
        """,
        encoding="utf-8",
    )
    report = run_audit(str(tmp_path))
    public_secret_findings = [f for f in report.findings if f.id == "secrets.public_secret_name"]
    assert len(public_secret_findings) == 1
    assert public_secret_findings[0].evidence and "NEXT_PUBLIC_STRIPE_SECRET" in public_secret_findings[0].evidence
