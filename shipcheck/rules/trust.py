from __future__ import annotations

import re

from shipcheck.models import AuditContext, Finding
from .common import finding, is_generated_file, is_jsx_placeholder_attribute, is_tailwind_placeholder_class, line_has

PLACEHOLDERS = ("lorem ipsum", "coming soon", "todo", "placeholder", "john doe", "acme")
AI_COPY = ("ai-powered", "revolutionary", "10x", "game changer", "magical", "vibe-coded")
STRONG_VISIBLE_PLACEHOLDERS = (
    "lorem ipsum",
    "john doe",
    "jane doe",
    "acme",
    "acme inc",
)


def is_import_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("import ") or stripped.startswith("export {") or " from " in stripped and stripped.startswith(("import", "}"))


def is_comment_only_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith(("//", "/*", "{/*", "*", "#")) or bool(re.search(r"\{/\*.*\*/\}", stripped))


def is_type_or_interface_line(line: str) -> bool:
    stripped = line.strip()
    low = stripped.lower()
    return (
        stripped.startswith(("type ", "interface "))
        or "placeholder?:" in low
        or bool(re.fullmatch(r"placeholder\s*,?", stripped, re.IGNORECASE))
        or bool(re.search(r"\bplaceholder[A-Z][A-Za-z0-9_]*\b", stripped))
        or ("database[" in low and "tables" in low)
    )


def is_function_or_identifier_line(line: str) -> bool:
    return bool(
        re.search(r"\b(?:async\s+)?(?:function\s+)?get[A-Za-z0-9_]*Todo[A-Za-z0-9_]*\b", line)
        or re.search(r"\b(?:Lucide)?ListTodo\b", line)
        or re.search(r"\btodo_list\b", line, re.IGNORECASE)
    )


def is_tailwind_placeholder_utility(line: str) -> bool:
    return is_tailwind_placeholder_class(line) or bool(re.search(r"\bplaceholder-[a-z0-9_/\-[\]:.]+", line.lower()))


def is_internal_placeholder_identifier_line(line: str) -> bool:
    stripped = line.strip()
    is_rendered_or_prose = bool(
        re.search(r">\s*[^<]*(?:placeholder|coming soon)[^<]*\s*<", stripped, re.IGNORECASE)
        or stripped.startswith(("#", "-", "*", ">"))
    )
    if is_rendered_or_prose:
        return False
    if re.search(r"\b[A-Z0-9_]*PLACEHOLDER[A-Z0-9_]*\b", line):
        return True
    if re.search(r"\b(?:[A-Za-z_$][\w$]*Placeholder[\w$]*|placeholder[A-Z_][\w$]*)\b", line):
        return True
    return False


def is_likely_rendered_copy_line(line: str) -> bool:
    stripped = line.strip()
    if re.search(r">\s*[^<]*(?:lorem ipsum|coming soon|todo|placeholder|john doe|jane doe|acme)[^<]*\s*<", stripped, re.IGNORECASE):
        return True
    if re.search(r">\s*(?:lorem ipsum|coming soon|todo|placeholder|john doe|jane doe|acme)[^<]*$", stripped, re.IGNORECASE):
        return True
    if stripped.startswith(("#", "-", "*", ">")):
        return True
    return not re.search(r"\b(?:const|let|var|type|interface|import|export|function|async)\b", stripped)


def is_code_symbol_placeholder_context(line: str) -> bool:
    if is_comment_only_line(line):
        return True
    if is_import_line(line):
        return True
    if is_type_or_interface_line(line):
        return True
    if is_internal_placeholder_identifier_line(line):
        return True
    if is_function_or_identifier_line(line):
        return True
    if is_jsx_placeholder_attribute(line) or is_tailwind_placeholder_utility(line):
        return True
    low = line.lower()
    if "todo" in low and not re.search(r">\s*[^<]*todo[^<]*<", line, re.IGNORECASE):
        return True
    return False


def should_flag_placeholder_copy(line: str) -> bool:
    if not line_has(line, *PLACEHOLDERS):
        return False
    if is_code_symbol_placeholder_context(line):
        return False
    low = line.lower()
    if any(token in low for token in STRONG_VISIBLE_PLACEHOLDERS):
        return is_likely_rendered_copy_line(line)
    if "placeholder" in low:
        return is_likely_rendered_copy_line(line) or "pricing" in low or "template" in low
    if "coming soon" in low:
        return is_likely_rendered_copy_line(line)
    if "todo" in low:
        return is_likely_rendered_copy_line(line)
    return False


def check(ctx: AuditContext) -> list[Finding]:
    out: list[Finding] = []
    text_files = [f for f in ctx.by_suffix(".md", ".tsx", ".jsx", ".ts", ".js") if not is_generated_file(f.rel_path, f.text)]
    has_privacy = any("privacy" in f.rel_path.lower() for f in ctx.files)
    has_terms = any("terms" in f.rel_path.lower() for f in ctx.files)
    collects_data = ctx.any_text("email", "customer", "subscription", "payment", "supabase", "stripe")
    if collects_data and (not has_privacy or not has_terms):
        out.append(finding("trust.missing_legal", "trust", "medium", "Privacy policy or terms page is missing", evidence="privacy/terms", why="Apps collecting user or payment data need clear trust and legal surfaces.", fix="Add privacy and terms pages linked from the app."))
    if not ctx.any_text("support@", "contact", "mailto:", "help@"):
        out.append(finding("trust.no_contact", "trust", "low", "No contact or support path found", why="Users need a clear support route before trusting a SaaS product.", fix="Add support email or contact page."))
    for f in text_files:
        for idx, line in enumerate(f.text.splitlines(), 1):
            if should_flag_placeholder_copy(line):
                out.append(finding("trust.placeholder_copy", "trust", "low", "Placeholder copy found", f, idx, line, "Placeholder content reduces buyer trust.", "Replace placeholders with specific product copy."))
                break
        if line_has(f.text, *AI_COPY):
            out.append(finding("trust.generic_ai_copy", "trust", "low", "Generic AI launch copy found", f, 1, "generic AI copy marker", "Generic launch copy makes the app feel unfinished.", "Use concrete customer outcomes and specific product language."))
    return out
