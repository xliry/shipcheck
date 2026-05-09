from shipcheck.engine import run_audit
import pytest


def test_checkout_session_is_not_auth_guard(tmp_path):
    route = tmp_path / "app" / "api" / "stripe" / "webhook"
    route.mkdir(parents=True)
    (route / "route.ts").write_text(
        """
        export async function POST(req: Request) {
          const event = await req.json();
          if (event.type === "checkout.session.completed") return Response.json({ ok: true });
          return Response.json({ ok: true });
        }
        """,
        encoding="utf-8",
    )
    report = run_audit(str(tmp_path))
    assert any(f.id == "auth.api_mutation_no_guard" for f in report.findings)


@pytest.mark.parametrize("guard", ["await requireAuth();", "await supabase.auth.getUser();"])
def test_specific_auth_markers_suppress_api_auth_finding(tmp_path, guard):
    route = tmp_path / "app" / "api" / "admin"
    route.mkdir(parents=True)
    (route / "route.ts").write_text(
        f"""
        export async function POST(req: Request) {{
          {guard}
          return Response.json({{ ok: true }});
        }}
        """,
        encoding="utf-8",
    )
    report = run_audit(str(tmp_path))
    assert not any(f.id == "auth.api_mutation_no_guard" for f in report.findings)


def test_bad_fixture_flags_auth():
    report = run_audit("tests/fixtures/next_supabase_bad")
    assert any(f.category == "auth" for f in report.findings)
    assert any(f.id == "auth.api_mutation_no_guard" for f in report.findings)


def test_clean_fixture_avoids_admin_auth_findings():
    report = run_audit("tests/fixtures/next_supabase_clean")
    assert not any(f.id == "auth.admin_no_role" for f in report.findings)
