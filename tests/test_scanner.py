from pathlib import Path

from shipcheck.scanner import collect_files


def test_scanner_skips_heavy_dirs(tmp_path: Path):
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "x.ts").write_text("secret", encoding="utf-8")
    (tmp_path / "app.ts").write_text("ok", encoding="utf-8")
    files = collect_files(tmp_path, 10)
    assert [f.rel_path for f in files] == ["app.ts"]


def test_scanner_excludes_tests_by_default():
    files = collect_files(Path("tests/fixtures/next_supabase_clean"), 100)
    assert not any("tests/" in f.rel_path for f in files)
    with_tests = collect_files(Path("tests/fixtures/next_supabase_clean"), 100, include_tests=True)
    assert any("tests/" in f.rel_path for f in with_tests)
