from __future__ import annotations

import re

from shipcheck.models import AuditContext, Finding
from .common import finding, is_client_path, line_has

SECRET_PATTERNS = [
    ("secrets.openai_key", "OpenAI API key appears in source", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    ("secrets.stripe_key", "Stripe secret key appears in source", re.compile(r"sk_(?:live|test)_[A-Za-z0-9]{16,}")),
    ("secrets.jwt", "JWT-like secret appears in source", re.compile(r"eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}")),
]
PUBLIC_SECRET = re.compile(r"NEXT_PUBLIC_[A-Z0-9_]*(SECRET|TOKEN|PRIVATE|SERVICE_ROLE|API_KEY)[A-Z0-9_]*")


def check(ctx: AuditContext) -> list[Finding]:
    out: list[Finding] = []
    gitignore = "\n".join(f.text for f in ctx.by_name(".gitignore"))
    has_env_example = any(f.rel_path.endswith(".env.example") for f in ctx.files)
    for f in ctx.files:
        if f.rel_path in {".env", ".env.local", ".env.production"}:
            out.append(finding("secrets.env_committed", "secrets", "critical", "Environment file appears committed", f, evidence=f.rel_path, why="Committed env files often contain production credentials.", fix="Remove committed env files, rotate exposed values, and commit only .env.example."))
        if "SUPABASE_SERVICE_ROLE_KEY" in f.text and is_client_path(f.rel_path):
            line = next((i for i, l in enumerate(f.text.splitlines(), 1) if "SUPABASE_SERVICE_ROLE_KEY" in l), None)
            out.append(finding("secrets.client_service_role", "secrets", "critical", "Supabase service role key appears in client-accessible code", f, line, "SUPABASE_SERVICE_ROLE_KEY", "Service role keys bypass RLS and must never reach browser bundles.", "Move service-role usage to trusted server-only code."))
        for idx, line in enumerate(f.text.splitlines(), 1):
            if PUBLIC_SECRET.search(line):
                out.append(finding("secrets.public_secret_name", "secrets", "high", "Secret-like value is exposed through NEXT_PUBLIC", f, idx, line, "NEXT_PUBLIC variables are bundled for the browser.", "Use server-only env names for secrets."))
            for id_, title, rx in SECRET_PATTERNS:
                if rx.search(line):
                    out.append(finding(id_, "secrets", "critical", title, f, idx, line, "Literal API keys in source can be copied from reports, logs, or git history.", "Move secrets to environment variables and rotate the exposed key."))
    if not has_env_example:
        out.append(finding("secrets.missing_env_example", "secrets", "medium", "No .env.example file found", why="Teams need a safe env contract without secret values.", fix="Add .env.example with placeholder values."))
    if ".env" not in gitignore and ".env*" not in gitignore:
        out.append(finding("secrets.gitignore_env", "secrets", "low", ".gitignore does not ignore env files", evidence=".gitignore", why="Env files are easy to commit accidentally.", fix="Add .env, .env.local, and .env.* to .gitignore."))
    return out
