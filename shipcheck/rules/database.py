from __future__ import annotations

import re

from shipcheck.models import AuditContext, Finding
from .common import (
    extract_supabase_policy_context,
    finding,
    is_likely_client_reachable,
    severity_for_wide_open_policy,
)


POLICY_BLOCK_RE = re.compile(r"\b(?:create|alter)\s+policy\b.*?(?:;|$)", re.IGNORECASE | re.DOTALL)


def _one_line(text: str) -> str:
    return " ".join(text.strip().split())


def _wide_open_policy_copy(context) -> tuple[str, str, str]:
    table = context.table or "unknown table"
    operation = context.operation or "unknown operation"
    is_write = operation in {"insert", "update", "delete", "all"} or context.expression_kind in {
        "with_check_true",
        "using_and_check_true",
    }
    if is_write:
        return (
            f"Wide-open write policy on {table}",
            f"Public writes can mutate {table} data unless another boundary exists.",
            "Scope write policies to authenticated users, ownership, or admin roles.",
        )
    if context.table_class in {"public_catalog", "content_public"} and operation == "select":
        return (
            f"Public read policy on {table}",
            f"Public read access on {table} may be intentional for catalog or content display.",
            "Verify the table contains only intentionally public data.",
        )
    if context.table_class == "billing_sensitive":
        return (
            f"Wide-open policy on billing-sensitive table {table}",
            f"Public access can expose customer billing state from {table}.",
            "Scope policies to authenticated users, ownership, or trusted service roles.",
        )
    if context.table_class == "auth_security":
        return (
            f"Wide-open policy on auth/security table {table}",
            f"Public access can expose security-sensitive records from {table}.",
            "Restrict access to trusted server-side roles or explicit authorization checks.",
        )
    if context.table_class == "user_private":
        return (
            f"Wide-open policy on user-private table {table}",
            f"Public access can expose private user or account records from {table}.",
            "Scope policies to the current user, team membership, or admin roles.",
        )
    return (
        f"Wide-open policy on table {table}",
        f"ShipCheck could not classify {table} sensitivity; verify this public policy is intentional.",
        "Replace true with an explicit ownership, role, or public-read condition.",
    )


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
        for match in POLICY_BLOCK_RE.finditer(f.text):
            block = match.group(0)
            if not re.search(r"\b(?:using|with\s+check)\s*\(\s*true\s*\)", block, re.IGNORECASE):
                continue
            line = f.text[: match.start()].count("\n") + 1
            context = extract_supabase_policy_context(block)
            severity = severity_for_wide_open_policy(context)
            title, why, fix = _wide_open_policy_copy(context)
            out.append(finding("database.wide_open_policy", "database", severity, title, f, line, _one_line(block), why, fix))
        for idx, line in enumerate(f.text.splitlines(), 1):
            low = line.lower()
            if "disable row level security" in low:
                out.append(finding("database.rls_disabled", "database", "critical", "Row-level security is disabled", f, idx, line, "Disabling RLS on sensitive data can expose customer records.", "Enable RLS and define scoped policies."))
    for f in ctx.files:
        if "SUPABASE_SERVICE_ROLE_KEY" in f.text and is_likely_client_reachable(f.rel_path, f.text):
            out.append(finding("database.service_role_browser", "database", "critical", "Service role key is used in browser-reachable code", f, 1, "SUPABASE_SERVICE_ROLE_KEY", "Service role bypasses all RLS protections.", "Use anon keys in browser code and service role only on trusted servers."))
    if uses_supabase and any(t in all_sql for t in ("users", "customers", "payments", "subscriptions")) and "enable row level security" not in all_sql:
        out.append(finding("database.sensitive_tables_without_rls", "database", "high", "Sensitive table names found without RLS evidence", why="Customer, payment, and user tables need explicit access boundaries.", fix="Add RLS and policies for sensitive tables."))
    return out
