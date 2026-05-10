from __future__ import annotations

import re

from shipcheck.models import AuditContext, Finding
from .common import code_files, finding, is_api_route, is_stripe_webhook_route, line_has

AUTH_WORDS = (
    "requireAuth",
    "getServerSession",
    "getUser(",
    "supabase.auth.getUser",
    "currentUser",
    "auth()",
    "verifySession",
    "validateSession",
)
ROLE_WORDS = ("role", "admin", "isAdmin", "permissions", "claims")


def check(ctx: AuditContext) -> list[Finding]:
    out: list[Finding] = []
    uses_auth = ctx.any_text("@supabase/supabase-js", "next-auth", "clerk", "supabase.auth", "getServerSession")
    has_middleware = any(f.rel_path in {"middleware.ts", "middleware.js", "src/middleware.ts"} for f in ctx.files)
    if uses_auth and not has_middleware:
        out.append(finding("auth.no_middleware", "auth", "medium", "No protected route middleware found", why="Next.js apps commonly need server-side route protection beyond client state.", fix="Add middleware or an equivalent server-side protected route pattern."))
    for f in code_files(ctx):
        low_path = f.rel_path.lower()
        if is_api_route(f.rel_path):
            mutates = re.search(r"export\s+async\s+function\s+(POST|PUT|PATCH|DELETE)|method\s*===\s*['\"](?:POST|PUT|PATCH|DELETE)", f.text)
            if mutates and not is_stripe_webhook_route(f) and not line_has(f.text, *AUTH_WORDS):
                out.append(finding("auth.api_mutation_no_guard", "auth", "critical" if "admin" in low_path else "high", "API mutation route has no auth guard evidence", f, 1, "mutation route without auth keyword", "Unauthenticated mutation endpoints can expose user data or admin actions.", "Verify users server-side before mutating data."))
        if "admin" in low_path and not line_has(f.text, *ROLE_WORDS):
            out.append(finding("auth.admin_no_role", "auth", "high", "Admin route has no role check evidence", f, 1, "admin path without role keyword", "Admin paths need explicit authorization, not just authentication.", "Check an admin role or permission claim server-side."))
        if line_has(f.text, "use client") and line_has(f.text, "router.push('/login", "router.replace('/login", "localStorage") and not line_has(f.text, *AUTH_WORDS):
            out.append(finding("auth.client_only_protection", "auth", "high", "Route protection appears client-side only", f, 1, "client redirect/localStorage auth marker", "Client-only checks can be bypassed by direct requests.", "Move authorization checks to middleware or server handlers."))
        for idx, line in enumerate(f.text.splitlines(), 1):
            if line_has(line, "todo auth", "skip auth", "temporary auth", "disable auth"):
                out.append(finding("auth.temporary_marker", "auth", "medium", "Temporary auth bypass marker found", f, idx, line, "Auth TODOs are often left in launch builds.", "Replace bypasses with production auth checks."))
    return out
