from shipcheck.engine import run_audit


def test_webhook_route_does_not_get_generic_rate_limit_finding(tmp_path):
    route = tmp_path / "app" / "api" / "stripe" / "webhook"
    route.mkdir(parents=True)
    (route / "route.ts").write_text(
        """
        export async function POST(req: Request) {
          const event = await req.json();
          return Response.json({ received: true });
        }
        """,
        encoding="utf-8",
    )
    report = run_audit(str(tmp_path))
    assert not any(f.id == "reliability.no_rate_limit" for f in report.findings)


def test_normal_mutation_route_still_gets_rate_limit_finding(tmp_path):
    route = tmp_path / "app" / "api" / "admin"
    route.mkdir(parents=True)
    (route / "route.ts").write_text(
        """
        export async function POST(req: Request) {
          return Response.json({ ok: true });
        }
        """,
        encoding="utf-8",
    )
    report = run_audit(str(tmp_path))
    assert any(f.id == "reliability.no_rate_limit" for f in report.findings)


def test_bad_fixture_has_reliability_findings():
    report = run_audit("tests/fixtures/next_supabase_bad")
    assert any(f.category == "reliability" for f in report.findings)


def test_clean_fixture_low_reliability_noise():
    report = run_audit("tests/fixtures/next_supabase_clean")
    assert report.categories["reliability"]["score"] <= 4
