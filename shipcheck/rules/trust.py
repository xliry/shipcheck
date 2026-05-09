from __future__ import annotations

from shipcheck.models import AuditContext, Finding
from .common import finding, line_has

PLACEHOLDERS = ("lorem ipsum", "coming soon", "todo", "placeholder", "john doe", "acme")
AI_COPY = ("ai-powered", "revolutionary", "10x", "game changer", "magical", "vibe-coded")


def check(ctx: AuditContext) -> list[Finding]:
    out: list[Finding] = []
    text_files = ctx.by_suffix(".md", ".tsx", ".jsx", ".ts", ".js")
    has_privacy = any("privacy" in f.rel_path.lower() for f in ctx.files)
    has_terms = any("terms" in f.rel_path.lower() for f in ctx.files)
    collects_data = ctx.any_text("email", "customer", "subscription", "payment", "supabase", "stripe")
    if collects_data and (not has_privacy or not has_terms):
        out.append(finding("trust.missing_legal", "trust", "medium", "Privacy policy or terms page is missing", evidence="privacy/terms", why="Apps collecting user or payment data need clear trust and legal surfaces.", fix="Add privacy and terms pages linked from the app."))
    if not ctx.any_text("support@", "contact", "mailto:", "help@"):
        out.append(finding("trust.no_contact", "trust", "low", "No contact or support path found", why="Users need a clear support route before trusting a SaaS product.", fix="Add support email or contact page."))
    for f in text_files:
        for idx, line in enumerate(f.text.splitlines(), 1):
            if line_has(line, *PLACEHOLDERS):
                out.append(finding("trust.placeholder_copy", "trust", "low", "Placeholder copy found", f, idx, line, "Placeholder content reduces buyer trust.", "Replace placeholders with specific product copy."))
                break
        if line_has(f.text, *AI_COPY):
            out.append(finding("trust.generic_ai_copy", "trust", "low", "Generic AI launch copy found", f, 1, "generic AI copy marker", "Generic launch copy makes the app feel unfinished.", "Use concrete customer outcomes and specific product language."))
    return out
