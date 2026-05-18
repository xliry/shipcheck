from __future__ import annotations

import re

from shipcheck.models import AuditContext, Finding
from .common import code_files, detect_app_context, finding, is_api_route, is_stripe_webhook_route, line_has


def _error_boundary_finding_text(stack: str) -> tuple[str, str, str]:
    if stack == "next":
        return (
            "No Next.js error boundary evidence found",
            "User-facing failures should render controlled recovery UI.",
            "Add app/error.tsx or an ErrorBoundary component.",
        )
    if stack == "vite-react":
        return (
            "No React error boundary evidence found",
            "Single-page apps should render controlled recovery UI when screens fail.",
            "Add a React ErrorBoundary around routed app surfaces or provider-heavy layouts.",
        )
    return (
        "No error boundary evidence found",
        "User-facing failures should render controlled recovery UI.",
        "Add a framework-appropriate error boundary or controlled recovery UI.",
    )


def _has_error_boundary_evidence(ctx: AuditContext) -> bool:
    return any(
        "error.tsx" in f.rel_path
        or "error.jsx" in f.rel_path
        or "ErrorBoundary" in f.text
        or "componentDidCatch" in f.text
        or "getDerivedStateFromError" in f.text
        or "react-error-boundary" in f.text
        or ("createBrowserRouter" in f.text and "errorElement" in f.text)
        or ("RouterProvider" in f.text and "errorElement" in f.text)
        for f in ctx.files
    )


def check(ctx: AuditContext) -> list[Finding]:
    out: list[Finding] = []
    app = detect_app_context(ctx)
    if not _has_error_boundary_evidence(ctx):
        title, why, fix = _error_boundary_finding_text(app.stack)
        out.append(finding("reliability.no_error_boundary", "reliability", "low", title, why=why, fix=fix))
    if not any(".github/workflows/" in f.rel_path for f in ctx.files):
        out.append(finding("reliability.no_ci", "reliability", "medium", "No CI workflow found", why="Critical flows need automated checks before launch.", fix="Add a GitHub Actions workflow for tests and linting."))
    has_tests = any(part in f.rel_path for f in ctx.files for part in ("test", "tests", "__tests__"))
    if not has_tests:
        has_tests = any(
            p.is_file() and any(part in p.relative_to(ctx.root).parts for part in ("test", "tests", "__tests__"))
            for p in ctx.root.rglob("*")
            if not (set(p.relative_to(ctx.root).parts) & {".git", "node_modules", ".next", "dist", "build", ".venv", "coverage"})
        )
    if not has_tests:
        out.append(finding("reliability.no_tests", "reliability", "medium", "No tests found", why="Payment and auth regressions are easy to ship without tests.", fix="Add focused tests for auth, payments, and core flows."))
    if not ctx.any_text("sentry", "datadog", "pino", "winston", "logger.", "console.error"):
        out.append(finding("reliability.no_logging", "reliability", "low", "No logging or error tracking evidence found", why="Production incidents need observable errors.", fix="Add structured logging or error tracking."))
    for f in code_files(ctx):
        for idx, line in enumerate(f.text.splitlines(), 1):
            if re.search(r"catch\s*\([^)]*\)\s*\{\s*\}|\bcatch\s*\{\s*\}", line):
                out.append(finding("reliability.empty_catch", "reliability", "medium", "Empty catch block found", f, idx, line, "Swallowed errors hide production failures.", "Log, rethrow, or return a controlled error response."))
        if is_api_route(f.rel_path) and not is_stripe_webhook_route(f) and line_has(f.text, "POST", "PUT", "PATCH", "DELETE") and not line_has(f.text, "rateLimit", "ratelimit", "upstash"):
            out.append(finding("reliability.no_rate_limit", "reliability", "high", "Public mutation endpoint has no rate-limit evidence", f, 1, "mutation route without rate limit keyword", "Public mutation endpoints can be abused.", "Add rate limiting around public mutation routes."))
    return out
