from __future__ import annotations

from pathlib import Path
import shutil
import tempfile

from .models import SourceFile

SKIP_DIRS = {
    ".git",
    "node_modules",
    ".next",
    ".vercel",
    "dist",
    "build",
    ".venv",
    "coverage",
    ".pytest_cache",
    "google-cloud-sdk",
}
TEXT_SUFFIXES = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".sql", ".json",
    ".md", ".yml", ".yaml", ".toml", ".env", ".example", ".gitignore",
}
TEXT_NAMES = {".env", ".env.local", ".env.production", ".env.example", ".gitignore", "Dockerfile"}


def resolve_target(target: str) -> tuple[Path, Path | None]:
    if target.startswith(("http://", "https://", "git@")):
        from git import Repo

        tmp = Path(tempfile.mkdtemp(prefix="shipcheck-"))
        Repo.clone_from(target, tmp, depth=1)
        return tmp, tmp
    return Path(target).resolve(), None


def cleanup_tmp(tmp: Path | None) -> None:
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)


def collect_files(root: Path, max_files: int, include_tests: bool = False) -> list[SourceFile]:
    files: list[SourceFile] = []
    if not root.exists():
        raise FileNotFoundError(f"Target does not exist: {root}")
    for path in sorted(root.rglob("*")):
        if len(files) >= max_files:
            break
        if not path.is_file():
            continue
        rel_path = path.relative_to(root)
        parts = set(rel_path.parts)
        if parts & SKIP_DIRS:
            continue
        if not include_tests and any(p in {"test", "tests", "__tests__"} for p in parts):
            continue
        if path.suffix not in TEXT_SUFFIXES and path.name not in TEXT_NAMES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "\x00" in text[:2000]:
            continue
        files.append(SourceFile(path=path, rel_path=rel_path.as_posix(), text=text))
    return files
