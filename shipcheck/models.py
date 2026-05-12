from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass(frozen=True)
class SourceFile:
    path: Path
    rel_path: str
    text: str


@dataclass(frozen=True)
class Finding:
    id: str
    category: str
    severity: str
    title: str
    file: str | None = None
    line: int | None = None
    evidence: str | None = None
    why_it_matters: str = ""
    remediation: str = ""
    duplicate_count: int | None = None
    duplicate_examples: tuple[str, ...] = ()
    deduped_by: str | None = None
    suppressed_duplicates: int | None = None


@dataclass
class AuditContext:
    root: Path
    files: list[SourceFile]
    profile: str

    def by_suffix(self, *suffixes: str) -> list[SourceFile]:
        return [f for f in self.files if f.rel_path.endswith(suffixes)]

    def by_name(self, *names: str) -> list[SourceFile]:
        wanted = set(names)
        return [f for f in self.files if Path(f.rel_path).name in wanted]

    def paths_containing(self, *parts: str) -> list[SourceFile]:
        return [f for f in self.files if any(p in f.rel_path for p in parts)]

    def find_regex(self, pattern: str, flags: int = 0) -> list[tuple[SourceFile, int, str]]:
        rx = re.compile(pattern, flags)
        out = []
        for source in self.files:
            for idx, line in enumerate(source.text.splitlines(), 1):
                if rx.search(line):
                    out.append((source, idx, line.strip()))
        return out

    def any_text(self, *needles: str) -> bool:
        haystack = "\n".join(f.text.lower() for f in self.files)
        return any(n.lower() in haystack for n in needles)


@dataclass
class AuditReport:
    target: str
    profile: str
    files_scanned: int
    score: int
    verdict: str
    summary: str
    categories: dict[str, dict[str, int]]
    findings: list[Finding] = field(default_factory=list)
