from __future__ import annotations

from pathlib import Path
import re

from shipcheck.models import AuditContext, Finding, SourceFile

SERVER_HINTS = ("app/api/", "pages/api/", "middleware", "server", "route.ts", "route.js")
CLIENT_HINTS = ("app/", "pages/", "components/", "lib/", "src/")


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


def is_client_path(path: str) -> bool:
    low = path.lower()
    return any(h in low for h in CLIENT_HINTS) and not any(h in low for h in ("app/api/", "pages/api/", "server/"))


def has_file(ctx: AuditContext, *names: str) -> bool:
    wanted = set(names)
    return any(Path(f.rel_path).name in wanted or f.rel_path in wanted for f in ctx.files)


def code_files(ctx: AuditContext) -> list[SourceFile]:
    return ctx.by_suffix(".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py")
