from shipcheck.engine import run_audit


def _finding(report, id_):
    return next(f for f in report.findings if f.id == id_)


def test_webhook_route_does_not_get_generic_rate_limit_finding(tmp_path):
    route = tmp_path / "app" / "api" / "stripe" / "webhook"
    route.mkdir(parents=True)
    (route / "route.ts").write_text(
        """
        import Stripe from "stripe";
        export async function POST(req: Request) {
          const event = { type: "checkout.session.completed" };
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


def test_next_app_without_error_boundary_keeps_next_wording(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "package.json").write_text(
        '{"dependencies":{"next":"^14.0.0","react":"^18.0.0"}}',
        encoding="utf-8",
    )
    (tmp_path / "app" / "page.tsx").write_text("export default function Page() { return <main />; }", encoding="utf-8")

    report = run_audit(str(tmp_path))
    finding = _finding(report, "reliability.no_error_boundary")

    assert finding.title == "No Next.js error boundary evidence found"
    assert finding.remediation == "Add app/error.tsx or an ErrorBoundary component."


def test_vite_react_router_without_error_boundary_uses_react_wording(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"dependencies":{"@vitejs/plugin-react":"latest","vite":"^5.0.0","react-router-dom":"^6.0.0"}}',
        encoding="utf-8",
    )
    (tmp_path / "vite.config.ts").write_text("export default {}", encoding="utf-8")
    (tmp_path / "index.html").write_text('<div id="root"></div>', encoding="utf-8")
    (tmp_path / "index.tsx").write_text(
        'import { BrowserRouter } from "react-router-dom"; export function App() { return <BrowserRouter />; }',
        encoding="utf-8",
    )

    report = run_audit(str(tmp_path))
    finding = _finding(report, "reliability.no_error_boundary")

    assert finding.title == "No React error boundary evidence found"
    assert "Single-page apps" in finding.why_it_matters
    assert "React ErrorBoundary" in finding.remediation
    assert "Next.js" not in finding.title
    assert "app/error.tsx" not in finding.remediation


def test_unknown_app_without_error_boundary_uses_neutral_wording(tmp_path):
    (tmp_path / "package.json").write_text('{"dependencies":{"react":"^18.0.0"}}', encoding="utf-8")
    (tmp_path / "index.tsx").write_text("export function App() { return <main />; }", encoding="utf-8")

    report = run_audit(str(tmp_path))
    finding = _finding(report, "reliability.no_error_boundary")

    assert finding.title == "No error boundary evidence found"
    assert finding.remediation == "Add a framework-appropriate error boundary or controlled recovery UI."
    assert "Next.js" not in finding.title
    assert "app/error.tsx" not in finding.remediation


def test_vite_active_project_fixture_uses_react_error_boundary_wording():
    report = run_audit("tests/fixtures/active_project_vite_supabase_stripe")
    finding = _finding(report, "reliability.no_error_boundary")

    assert finding.title == "No React error boundary evidence found"
    assert "React ErrorBoundary" in finding.remediation
    assert "Next.js" not in finding.title
    assert "app/error.tsx" not in finding.remediation
