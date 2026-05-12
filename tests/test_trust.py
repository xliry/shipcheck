from shipcheck.engine import run_audit


def _report_for_source(tmp_path, rel_path: str, text: str):
    source = tmp_path / rel_path
    source.parent.mkdir(parents=True)
    source.write_text(text, encoding="utf-8")
    return run_audit(str(tmp_path))


def _has_placeholder(report):
    return any(f.id == "trust.placeholder_copy" for f in report.findings)


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


def test_tailwind_placeholder_utility_does_not_count(tmp_path):
    report = _report_for_source(
        tmp_path,
        "app/login.tsx",
        '<input className="placeholder-gray-500 text-gray-900" />',
    )
    assert not _has_placeholder(report)


def test_typescript_placeholder_prop_does_not_count(tmp_path):
    report = _report_for_source(
        tmp_path,
        "components/Input.tsx",
        """
        type InputProps = {
          placeholder?: string
        }
        """,
    )
    assert not _has_placeholder(report)


def test_placeholder_prop_identifier_usage_does_not_count(tmp_path):
    report = _report_for_source(
        tmp_path,
        "components/ui/input.tsx",
        """
        const Input = ({ placeholder }) => {
          return <TextInput placeholderTextColor={colors.icon} placeholder={placeholder} />
        }
        """,
    )
    assert not _has_placeholder(report)


def test_supabase_todo_table_type_does_not_count(tmp_path):
    report = _report_for_source(
        tmp_path,
        "app/table/page.tsx",
        'type Task = Database["public"]["Tables"]["todo_list"]["Row"];',
    )
    assert not _has_placeholder(report)


def test_todo_icon_import_does_not_count(tmp_path):
    report = _report_for_source(
        tmp_path,
        "components/AppLayout.tsx",
        'import { FolderOpen, Home, ListTodo, Settings } from "lucide-react";',
    )
    assert not _has_placeholder(report)


def test_todo_function_identifier_does_not_count(tmp_path):
    report = _report_for_source(
        tmp_path,
        "lib/todos.ts",
        """
        async function getMyTodoList() {
          return []
        }
        """,
    )
    assert not _has_placeholder(report)


def test_code_todo_comment_does_not_count(tmp_path):
    report = _report_for_source(
        tmp_path,
        "app/actions.ts",
        "// TODO: Send invitation email and include inviteId in sign-up URL",
    )
    assert not _has_placeholder(report)


def test_demo_todo_feature_copy_does_not_count(tmp_path):
    report = _report_for_source(
        tmp_path,
        "app/page.tsx",
        'const feature = { description: "Built-in todo system with real-time updates" }',
    )
    assert not _has_placeholder(report)


def test_lorem_ipsum_jsx_still_counts(tmp_path):
    report = _report_for_source(
        tmp_path,
        "app/page.tsx",
        "<p>Lorem ipsum dolor sit amet</p>",
    )
    assert _has_placeholder(report)


def test_acme_brand_copy_still_counts(tmp_path):
    report = _report_for_source(
        tmp_path,
        "app/layout.tsx",
        '<span className="font-semibold">ACME</span>',
    )
    assert _has_placeholder(report)


def test_acme_screen_reader_brand_copy_still_counts(tmp_path):
    report = _report_for_source(
        tmp_path,
        "app/page.tsx",
        '<span className="sr-only">Acme Inc</span>',
    )
    assert _has_placeholder(report)


def test_explicit_pricing_placeholder_still_counts(tmp_path):
    report = _report_for_source(
        tmp_path,
        "components/HomePricing.tsx",
        "<p>IT'S PLACEHOLDER NO PRICING FOR THIS TEMPLATE</p>",
    )
    assert _has_placeholder(report)


def test_fake_testimonial_still_counts(tmp_path):
    report = _report_for_source(
        tmp_path,
        "app/page.tsx",
        "<blockquote>John Doe at Acme says this changed everything.</blockquote>",
    )
    assert _has_placeholder(report)
