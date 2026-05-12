from __future__ import annotations

from dataclasses import replace
import re

from .models import Finding
from .rules.common import norm_path


TUTORIAL_CONTAINER_PARTS = {"tutorial", "tutorials", "lesson", "lessons", "step", "steps", "chapter", "chapters"}
MULTI_APP_CONTAINER_PARTS = {"examples", "apps", "packages"}
TUTORIAL_PART_RE = re.compile(
    r"^(?:\d{1,2}[-_].+|lesson[-_]?.+|step[-_]?.+|chapter[-_]?.+|starter|start|final|solution)$",
    re.IGNORECASE,
)


def looks_like_tutorial_or_multi_app_path(path: str | None) -> bool:
    if not path:
        return False
    parts = [p for p in norm_path(path).split("/") if p]
    return any(
        part in TUTORIAL_CONTAINER_PARTS
        or part in MULTI_APP_CONTAINER_PARTS
        or bool(TUTORIAL_PART_RE.match(part))
        for part in parts
    )


def _normalized_path_shape(path: str) -> str:
    parts = [p for p in norm_path(path).split("/") if p]
    normalized: list[str] = []
    for part in parts:
        if part in TUTORIAL_CONTAINER_PARTS or TUTORIAL_PART_RE.match(part):
            continue
        normalized.append(part)
    return "/".join(normalized)


def _normalized_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.strip().lower())


def normalized_finding_fingerprint(finding: Finding) -> tuple[str, str, str, str, str]:
    return (
        finding.id,
        finding.severity,
        _normalized_text(finding.title),
        _normalized_text(finding.evidence),
        _normalized_path_shape(finding.file or ""),
    )


def deduplicate_findings(findings: list[Finding]) -> list[Finding]:
    passthrough: list[Finding] = []
    groups: dict[tuple[str, str, str, str, str], list[Finding]] = {}

    for item in findings:
        if not looks_like_tutorial_or_multi_app_path(item.file):
            passthrough.append(item)
            continue
        groups.setdefault(normalized_finding_fingerprint(item), []).append(item)

    deduped: list[Finding] = list(passthrough)
    for group in groups.values():
        ordered = sorted(group, key=lambda f: (f.file or "", f.line or 0))
        if len(ordered) == 1:
            deduped.append(ordered[0])
            continue
        representative = ordered[0]
        example_paths = tuple(
            f"{finding.file}:{finding.line}" if finding.file and finding.line else (finding.file or "repo")
            for finding in ordered[:3]
        )
        deduped.append(
            replace(
                representative,
                duplicate_count=len(ordered),
                duplicate_examples=example_paths,
                deduped_by="tutorial_path_fingerprint",
                suppressed_duplicates=len(ordered) - 1,
            )
        )
    return deduped
