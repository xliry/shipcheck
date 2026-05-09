from __future__ import annotations

from .models import AuditContext, AuditReport, Finding
from .scanner import cleanup_tmp, collect_files, resolve_target
from .scoring import score_findings, summary
from .rules import auth, database, payments, reliability, secrets, trust

RULE_MODULES = [secrets, auth, database, payments, reliability, trust]


def run_audit(target: str, profile: str = "next-supabase-stripe", max_files: int = 500, include_tests: bool = False) -> AuditReport:
    root, tmp = resolve_target(target)
    try:
        files = collect_files(root, max_files=max_files, include_tests=include_tests)
        ctx = AuditContext(root=root, files=files, profile=profile)
        findings: list[Finding] = []
        for module in RULE_MODULES:
            findings.extend(module.check(ctx))
        findings.sort(key=lambda f: ({"critical": 0, "high": 1, "medium": 2, "low": 3}[f.severity], f.category, f.file or ""))
        score, verdict, categories = score_findings(findings)
        return AuditReport(target=target, profile=profile, files_scanned=len(files), score=score, verdict=verdict, summary=summary(score), categories=categories, findings=findings)
    finally:
        cleanup_tmp(tmp)
