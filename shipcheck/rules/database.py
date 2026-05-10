from __future__ import annotations

from pathlib import Path

from shipcheck.models import AuditContext, Finding
from .common import finding, is_likely_client_reachable, line_has


def check(ctx: AuditContext) -> list[Finding]:
    out: list[Finding] = []
    uses_supabase = ctx.any_text("@supabase/supabase-js", "createClient(", "supabase")
    sql_files = ctx.by_suffix(".sql")
    has_migrations = any("migrations/" in f.rel_path for f in sql_files)
    all_sql = "\n".join(f.text.lower() for f in sql_files)
    if uses_supabase and not has_migrations:
        out.append(finding("database.no_migrations", "database", "medium", "No Supabase/Postgres migrations directory found", why="Production schema changes need reviewable migration history.", fix="Add migrations under supabase/migrations or an equivalent tracked migration folder."))
    if uses_supabase and "enable row level security" not in all_sql:
        out.append(finding("database.no_rls_evidence", "database", "high", "No row-level security enable statements found", why="Supabase apps rely on RLS to protect browser-accessible data.", fix="Enable RLS on sensitive tables and add scoped policies."))
    if uses_supabase and "create policy" not in all_sql and sql_files:
        out.append(finding("database.no_policies", "database", "high", "No SQL policy definitions found", why="RLS without policies can block access or lead to unsafe workarounds.", fix="Add explicit policies for authenticated access."))
    for f in sql_files:
        for idx, line in enumerate(f.text.splitlines(), 1):
            low = line.lower()
            if "using (true)" in low or "with check (true)" in low:
                out.append(finding("database.wide_open_policy", "database", "high", "Wide-open RLS policy found", f, idx, line, "Policies using true can expose all rows unless tightly limited elsewhere.", "Scope policies to authenticated users, ownership, or admin roles."))
            if "disable row level security" in low:
                out.append(finding("database.rls_disabled", "database", "critical", "Row-level security is disabled", f, idx, line, "Disabling RLS on sensitive data can expose customer records.", "Enable RLS and define scoped policies."))
    for f in ctx.files:
        if "SUPABASE_SERVICE_ROLE_KEY" in f.text and is_likely_client_reachable(f.rel_path, f.text):
            out.append(finding("database.service_role_browser", "database", "critical", "Service role key is used in browser-reachable code", f, 1, "SUPABASE_SERVICE_ROLE_KEY", "Service role bypasses all RLS protections.", "Use anon keys in browser code and service role only on trusted servers."))
    if uses_supabase and any(t in all_sql for t in ("users", "customers", "payments", "subscriptions")) and "enable row level security" not in all_sql:
        out.append(finding("database.sensitive_tables_without_rls", "database", "high", "Sensitive table names found without RLS evidence", why="Customer, payment, and user tables need explicit access boundaries.", fix="Add RLS and policies for sensitive tables."))
    return out
