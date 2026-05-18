from shipcheck.engine import run_audit
import pytest


def _write_vite_app(tmp_path, protected_route: bool = True, server_auth: bool = False):
    (tmp_path / "package.json").write_text(
        """
        {
          "dependencies": {
            "@supabase/supabase-js": "^2.0.0",
            "react-router-dom": "^6.0.0",
            "vite": "^5.0.0"
          }
        }
        """,
        encoding="utf-8",
    )
    (tmp_path / "vite.config.ts").write_text("export default {}", encoding="utf-8")
    (tmp_path / "index.html").write_text('<div id="root"></div>', encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.tsx").write_text(
        """
        import { createClient } from "@supabase/supabase-js";
        import { BrowserRouter } from "react-router-dom";
        const supabase = createClient("url", "anon");
        export function App() { return <BrowserRouter />; }
        """,
        encoding="utf-8",
    )
    if protected_route:
        components = tmp_path / "components"
        components.mkdir()
        (components / "ProtectedRoute.tsx").write_text(
            """
            import { Navigate } from "react-router-dom";
            export function ProtectedRoute({ children }) {
              const user = useAuth();
              return user ? children : <Navigate to="/login" />;
            }
            """,
            encoding="utf-8",
        )
    if server_auth:
        api = tmp_path / "api"
        api.mkdir()
        (api / "profile.ts").write_text(
            """
            export default async function handler(req, res) {
              const token = req.headers.authorization;
              const { data: { user } } = await supabase.auth.getUser(token);
              res.json({ id: user.id });
            }
            """,
            encoding="utf-8",
        )


def test_verified_stripe_webhook_is_not_app_auth_guard(tmp_path):
    route = tmp_path / "app" / "api" / "stripe" / "webhook"
    route.mkdir(parents=True)
    (route / "route.ts").write_text(
        """
        import Stripe from "stripe";
        export async function POST(req: Request) {
          const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);
          const signature = req.headers.get("stripe-signature")!;
          const event = stripe.webhooks.constructEvent(await req.text(), signature, process.env.STRIPE_WEBHOOK_SECRET!);
          if (event.type === "checkout.session.completed") return Response.json({ ok: true });
          return Response.json({ ok: true });
        }
        """,
        encoding="utf-8",
    )
    report = run_audit(str(tmp_path))
    assert not any(f.id == "auth.api_mutation_no_guard" for f in report.findings)


def test_next_app_without_middleware_keeps_next_auth_language(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"dependencies":{"next":"^14.0.0","@supabase/supabase-js":"^2.0.0"}}',
        encoding="utf-8",
    )
    app = tmp_path / "app"
    app.mkdir()
    (app / "page.tsx").write_text("supabase.auth.getUser();", encoding="utf-8")
    report = run_audit(str(tmp_path))
    finding = next(f for f in report.findings if f.id == "auth.no_middleware")
    assert finding.title == "No protected route middleware found"
    assert "Next.js apps" in finding.why_it_matters


def test_vite_protected_route_uses_server_enforcement_language(tmp_path):
    _write_vite_app(tmp_path, protected_route=True)
    report = run_audit(str(tmp_path))
    finding = next(f for f in report.findings if f.id == "auth.no_middleware")
    assert finding.title == "Client-side route protection found; verify server-side API enforcement"
    assert "React Router guards" in finding.why_it_matters


def test_vite_without_route_guard_uses_spa_language(tmp_path):
    _write_vite_app(tmp_path, protected_route=False)
    report = run_audit(str(tmp_path))
    finding = next(f for f in report.findings if f.id == "auth.no_middleware")
    assert finding.title == "No obvious protected route pattern found"
    assert "Single-page apps" in finding.why_it_matters


def test_vite_with_server_auth_evidence_still_asks_for_flow_level_review(tmp_path):
    _write_vite_app(tmp_path, protected_route=True, server_auth=True)
    report = run_audit(str(tmp_path))
    finding = next(f for f in report.findings if f.id == "auth.no_middleware")
    assert finding.title == "Client-side route protection found; verify server-side API enforcement"


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


def test_normal_admin_mutation_still_requires_auth(tmp_path):
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
    assert any(f.id == "auth.api_mutation_no_guard" for f in report.findings)


def test_clean_fixture_avoids_admin_auth_findings():
    report = run_audit("tests/fixtures/next_supabase_clean")
    assert not any(f.id == "auth.admin_no_role" for f in report.findings)


def test_vite_active_project_fixture_has_framework_aware_auth_language():
    report = run_audit("tests/fixtures/active_project_vite_supabase_stripe")
    finding = next(f for f in report.findings if f.id == "auth.no_middleware")
    assert finding.title == "Client-side route protection found; verify server-side API enforcement"
    assert "React Router guards" in finding.why_it_matters

