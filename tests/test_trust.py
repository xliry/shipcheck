from shipcheck.engine import run_audit


def test_bad_fixture_flags_placeholder_copy():
    report = run_audit("tests/fixtures/next_supabase_bad")
    assert any(f.id == "trust.placeholder_copy" for f in report.findings)


def test_clean_fixture_low_score_and_no_critical():
    report = run_audit("tests/fixtures/next_supabase_clean")
    assert report.score <= 30
    assert not any(f.severity == "critical" for f in report.findings)


def test_form_placeholder_attributes_do_not_count_as_placeholder_copy(tmp_path):
    page = tmp_path / "app" / "page.tsx"
    page.parent.mkdir(parents=True)
    page.write_text(
        """
        export default function Page() {
          return <input placeholder="Your email" className="placeholder:text-muted-foreground" />;
        }
        """,
        encoding="utf-8",
    )
    report = run_audit(str(tmp_path))
    assert not any(f.id == "trust.placeholder_copy" for f in report.findings)


def test_visible_placeholder_marketing_copy_still_counts(tmp_path):
    page = tmp_path / "app" / "page.tsx"
    page.parent.mkdir(parents=True)
    page.write_text(
        """
        export default function Page() {
          return <main>Lorem ipsum testimonial from John Doe at Acme.</main>;
        }
        """,
        encoding="utf-8",
    )
    report = run_audit(str(tmp_path))
    assert any(f.id == "trust.placeholder_copy" for f in report.findings)
