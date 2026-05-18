from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
import re

from shipcheck.models import AuditContext, Finding, SourceFile

SERVER_HINTS = ("app/api/", "pages/api/", "middleware", "server", "route.ts", "route.js")
CLIENT_HINTS = ("app/", "pages/", "components/", "lib/", "src/")
CODE_SUFFIXES = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py")

PUBLIC_CATALOG_TABLE_WORDS = {
    "product", "products", "price", "prices", "plan", "plans",
    "feature", "features", "tier", "tiers", "catalog", "catalogs",
    "pricing_plan", "pricing_plans",
}
PUBLIC_CONTENT_TABLE_WORDS = {
    "post", "posts", "article", "articles", "page", "pages",
    "doc", "docs", "blog", "blogs", "marketing_page", "marketing_pages",
}
USER_PRIVATE_TABLE_WORDS = {
    "user", "users", "profile", "profiles", "account", "accounts",
    "member", "members", "team", "teams", "organization", "organizations",
    "workspace", "workspaces",
}
BILLING_SENSITIVE_TABLE_WORDS = {
    "customer", "customers", "subscription", "subscriptions",
    "payment", "payments", "invoice", "invoices", "order", "orders",
    "checkout_session", "checkout_sessions",
}
AUTH_SECURITY_TABLE_WORDS = {
    "session", "sessions", "token", "tokens", "api_key", "api_keys",
    "secret", "secrets", "role", "roles", "permission", "permissions",
}


@dataclass(frozen=True)
class SupabasePolicyContext:
    table: str | None
    schema: str | None
    operation: str | None
    expression_kind: str
    table_class: str


@dataclass(frozen=True)
class AppContext:
    stack: str
    has_client_route_guard: bool = False
    has_server_auth_evidence: bool = False


def norm_path(path: str) -> str:
    return path.replace("\\", "/").lower()


def _clean_identifier(value: str | None) -> str | None:
    if not value:
        return None
    return value.strip().strip('"').strip("'").lower()


def classify_supabase_table(table_name: str | None) -> str:
    table = _clean_identifier(table_name)
    if not table:
        return "unknown"
    parts = {p for p in re.split(r"[^a-z0-9]+", table) if p}
    candidates = {table, *parts}
    if candidates & AUTH_SECURITY_TABLE_WORDS:
        return "auth_security"
    if candidates & BILLING_SENSITIVE_TABLE_WORDS:
        return "billing_sensitive"
    if candidates & USER_PRIVATE_TABLE_WORDS:
        return "user_private"
    if candidates & PUBLIC_CATALOG_TABLE_WORDS:
        return "public_catalog"
    if candidates & PUBLIC_CONTENT_TABLE_WORDS:
        return "content_public"
    return "unknown"


def classify_policy_operation(policy_text: str) -> str | None:
    match = re.search(r"\bfor\s+(select|insert|update|delete|all)\b", policy_text, re.IGNORECASE)
    return match.group(1).lower() if match else None


def extract_supabase_policy_context(text: str, line_number: int | None = None) -> SupabasePolicyContext:
    policy_text = text
    if line_number is not None:
        for match in re.finditer(r"\b(?:create|alter)\s+policy\b.*?(?:;|$)", text, re.IGNORECASE | re.DOTALL):
            start_line = text[: match.start()].count("\n") + 1
            end_line = text[: match.end()].count("\n") + 1
            if start_line <= line_number <= end_line:
                policy_text = match.group(0)
                break

    ident = r"(?:\"[^\"]+\"|[A-Za-z_][A-Za-z0-9_]*)"
    table_match = re.search(rf"\bon\s+(?:(?P<schema>{ident})\.)?(?P<table>{ident})\b", policy_text, re.IGNORECASE)
    schema = _clean_identifier(table_match.group("schema")) if table_match else None
    table = _clean_identifier(table_match.group("table")) if table_match else None
    operation = classify_policy_operation(policy_text)
    has_using_true = bool(re.search(r"\busing\s*\(\s*true\s*\)", policy_text, re.IGNORECASE))
    has_check_true = bool(re.search(r"\bwith\s+check\s*\(\s*true\s*\)", policy_text, re.IGNORECASE))
    if has_using_true and has_check_true:
        expression_kind = "using_and_check_true"
    elif has_check_true:
        expression_kind = "with_check_true"
    elif has_using_true:
        expression_kind = "using_true"
    else:
        expression_kind = "unknown"
    return SupabasePolicyContext(
        table=table,
        schema=schema,
        operation=operation,
        expression_kind=expression_kind,
        table_class=classify_supabase_table(table),
    )


def severity_for_wide_open_policy(context: SupabasePolicyContext) -> str:
    is_write = context.operation in {"insert", "update", "delete", "all"} or context.expression_kind in {
        "with_check_true",
        "using_and_check_true",
    }
    if is_write:
        return "critical" if context.table_class == "auth_security" else "high"
    if context.operation == "select":
        if context.table_class in {"public_catalog", "content_public"}:
            return "low"
        if context.table_class == "auth_security":
            return "critical"
        if context.table_class in {"billing_sensitive", "user_private"}:
            return "high"
        return "medium"
    if context.table_class in {"public_catalog", "content_public"}:
        return "medium"
    if context.table_class == "auth_security":
        return "critical"
    if context.table_class in {"billing_sensitive", "user_private"}:
        return "high"
    return "medium"


def redact(value: str | None) -> str | None:
    if not value:
        return value
    text = value.strip().replace("'", "").replace('"', "")
    for token in re.findall(r"(sk_(?:live|test)_[A-Za-z0-9]{8,}|sk-[A-Za-z0-9_-]{12,}|eyJ[A-Za-z0-9_.-]{20,})", text):
        text = text.replace(token, token[:8] + "...REDACTED")
    for token in re.findall(r"=([A-Za-z0-9_./+-]{16,})", text):
        text = text.replace(token, token[:4] + "...REDACTED")
    return text[:160]


def finding(id_: str, category: str, severity: str, title: str, source: SourceFile | None = None, line: int | None = None, evidence: str | None = None, why: str = "", fix: str = "") -> Finding:
    return Finding(id=id_, category=category, severity=severity, title=title, file=source.rel_path if source else None, line=line, evidence=redact(evidence), why_it_matters=why, remediation=fix)


def line_has(text: str, *needles: str) -> bool:
    low = text.lower()
    return any(n.lower() in low for n in needles)


def _package_dependencies(ctx: AuditContext) -> set[str]:
    deps: set[str] = set()
    for source in ctx.by_name("package.json"):
        try:
            data = json.loads(source.text)
        except json.JSONDecodeError:
            continue
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            values = data.get(section)
            if isinstance(values, dict):
                deps.update(str(name).lower() for name in values)
    return deps


def detect_app_context(ctx: AuditContext) -> AppContext:
    deps = _package_dependencies(ctx)
    paths = {norm_path(f.rel_path) for f in ctx.files}
    names = {Path(path).name for path in paths}

    has_next = (
        "next" in deps
        or any(name.startswith("next.config.") for name in names)
        or any(path.startswith(("app/api/", "pages/api/")) for path in paths)
    )
    has_vite = (
        "vite" in deps
        or any(name in {"vite.config.ts", "vite.config.js", "vite.config.mts", "vite.config.mjs"} for name in names)
        or "index.html" in paths
        or any(path in {"src/main.tsx", "src/main.jsx", "index.tsx", "index.jsx"} for path in paths)
    )
    uses_react_router = "react-router-dom" in deps or any("react-router-dom" in f.text for f in ctx.files)

    if has_next:
        stack = "next"
    elif has_vite and uses_react_router and "next" not in deps:
        stack = "vite-react"
    else:
        stack = "unknown"

    has_client_route_guard = any(
        "ProtectedRoute" in f.text
        or (
            line_has(f.text, "useAuth", "Navigate to=", "router.push('/login", 'router.push("/login')
            and not is_server_only_path(f.rel_path, f.text)
        )
        for f in code_files(ctx)
    )
    has_server_auth_evidence = any(
        not is_stripe_webhook_route(f)
        and (
            is_api_route(f.rel_path)
            or norm_path(f.rel_path).startswith(("api/", "server/", "cloudrun/src/routes/"))
            or "/server/" in norm_path(f.rel_path)
        )
        and line_has(
            f.text,
            "supabase.auth.getUser",
            "getUser(",
            "getSession",
            "Authorization",
            "jwt",
            "requireAuth",
            "verifySession",
            "getServerSession",
        )
        for f in code_files(ctx)
    )
    return AppContext(stack=stack, has_client_route_guard=has_client_route_guard, has_server_auth_evidence=has_server_auth_evidence)


def is_client_path(path: str) -> bool:
    low = norm_path(path)
    return any(h in low for h in CLIENT_HINTS) and not any(h in low for h in ("app/api/", "pages/api/", "server/"))


def is_route_file(path: str) -> bool:
    low = norm_path(path)
    name = Path(low).name
    return (low.startswith("app/api/") or "/app/api/" in low) and name in {"route.ts", "route.tsx", "route.js", "route.jsx", "route.mjs", "route.cjs"}


def is_api_route(path: str) -> bool:
    low = norm_path(path)
    return (
        is_route_file(low)
        or ((low.startswith("pages/api/") or "/pages/api/" in low) and low.endswith(CODE_SUFFIXES))
    )


def is_generated_file(path: str, text: str = "") -> bool:
    low_path = norm_path(path)
    low_text = text.lower()
    name = Path(low_path).name
    generated_names = {
        "types_db.ts",
        "database.types.ts",
        "supabase.types.ts",
        "schema.types.ts",
    }
    return (
        name in generated_names
        or ".generated." in low_path
        or "database.types" in low_path
        or "supabase.types" in low_path
        or "types_db" in low_path
        or ("supabase" in low_path and name in {"types.ts", "types_db.ts"})
        or "this file was generated" in low_text
        or "generated by" in low_text
        or ("export type json" in low_text and "database" in low_text)
    )


def is_server_only_path(path: str, text: str = "") -> bool:
    low = norm_path(path)
    low_text = text.lower()
    return (
        low.startswith("app/api/")
        or "/app/api/" in low
        or low.startswith("pages/api/")
        or "/pages/api/" in low
        or "/server/" in low
        or low.startswith("server/")
        or "/lib/server/" in low
        or "/libs/server/" in low
        or "server-only" in low_text
        or "supabase-admin" in low
        or "admin-client" in low
    )


def is_likely_client_reachable(path: str, text: str = "") -> bool:
    low = norm_path(path)
    low_text = text.lower()
    if is_server_only_path(low, text):
        return False
    if '"use client"' in low_text or "'use client'" in low_text:
        return True
    if low.startswith("components/") or "/components/" in low:
        return True
    if low.startswith("pages/") and not low.startswith("pages/api/"):
        return True
    return False


def verifies_stripe_signature(text: str) -> bool:
    return line_has(text, "constructEvent", "stripe-signature", "STRIPE_WEBHOOK_SECRET", "stripe_webhook_secret")


def is_stripe_webhook_route(source: SourceFile) -> bool:
    low_path = norm_path(source.rel_path)
    if not is_api_route(source.rel_path) and not (low_path.startswith("api/") and low_path.endswith(CODE_SUFFIXES)):
        return False
    low_text = source.text.lower()
    has_stripe_context = "stripe" in low_path or "stripe" in low_text
    has_webhook_context = "webhook" in Path(low_path).parts or "webhook" in Path(low_path).name or "webhook" in low_text
    has_event_context = line_has(
        source.text,
        "constructEvent",
        "stripe-signature",
        "checkout.session.completed",
        "customer.subscription",
        "invoice.paid",
        "invoice.payment",
        "payment_intent",
    )
    return has_stripe_context and (has_webhook_context or has_event_context) and has_event_context


def is_jsx_placeholder_attribute(line: str) -> bool:
    low = line.lower()
    return bool(re.search(r"\bplaceholder\s*=", low))


def is_tailwind_placeholder_class(line: str) -> bool:
    return bool(re.search(r"\bplaceholder:[a-z0-9_/\-[\]:.]+", line.lower()))


def has_file(ctx: AuditContext, *names: str) -> bool:
    wanted = set(names)
    return any(Path(f.rel_path).name in wanted or f.rel_path in wanted for f in ctx.files)


def code_files(ctx: AuditContext) -> list[SourceFile]:
    return ctx.by_suffix(*CODE_SUFFIXES)
