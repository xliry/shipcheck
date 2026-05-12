from shipcheck.engine import run_audit


def _report_for_sql(tmp_path, sql: str):
    migration = tmp_path / "supabase" / "migrations" / "001.sql"
    migration.parent.mkdir(parents=True)
    migration.write_text(sql, encoding="utf-8")
    return run_audit(str(tmp_path))


def _wide_open_findings(report):
    return [f for f in report.findings if f.id == "database.wide_open_policy"]


def test_bad_fixture_flags_database_risks():
    report = run_audit("tests/fixtures/next_supabase_bad")
    ids = {f.id for f in report.findings}
    assert "database.wide_open_policy" in ids


def test_clean_fixture_has_no_database_findings():
    report = run_audit("tests/fixtures/next_supabase_clean")
    assert not [f for f in report.findings if f.category == "database"]


def test_server_only_service_role_helper_is_not_browser_exposure(tmp_path):
    helper = tmp_path / "src" / "libs" / "supabase" / "supabase-admin.ts"
    helper.parent.mkdir(parents=True)
    helper.write_text(
        """
        import "server-only";
        export const serviceRole = process.env.SUPABASE_SERVICE_ROLE_KEY!;
        """,
        encoding="utf-8",
    )
    report = run_audit(str(tmp_path))
    assert not any(f.id == "database.service_role_browser" for f in report.findings)


def test_client_service_role_usage_remains_browser_exposure(tmp_path):
    component = tmp_path / "components" / "Account.tsx"
    component.parent.mkdir(parents=True)
    component.write_text(
        """
        "use client";
        export const serviceRole = process.env.SUPABASE_SERVICE_ROLE_KEY!;
        """,
        encoding="utf-8",
    )
    report = run_audit(str(tmp_path))
    assert any(f.id == "database.service_role_browser" for f in report.findings)


def test_catalog_read_policy_is_low_severity(tmp_path):
    report = _report_for_sql(
        tmp_path,
        """
        create policy "Public can read products"
        on public.products
        for select
        using (true);

        create policy "Public can read prices"
        on public.prices
        for select
        using (true);
        """,
    )
    findings = _wide_open_findings(report)
    assert {f.severity for f in findings} == {"low"}
    assert all("Public read policy" in f.title for f in findings)


def test_sensitive_billing_read_policy_remains_high(tmp_path):
    report = _report_for_sql(
        tmp_path,
        """
        create policy "Anyone can read subscriptions"
        on public.subscriptions
        for select
        using (true);

        create policy "Anyone can read payments"
        on public.payments
        for select
        using (true);
        """,
    )
    assert [f.severity for f in _wide_open_findings(report)] == ["high", "high"]


def test_public_catalog_write_policy_remains_high(tmp_path):
    report = _report_for_sql(
        tmp_path,
        """
        create policy "Anyone can insert products"
        on public.products
        for insert
        with check (true);
        """,
    )
    finding = _wide_open_findings(report)[0]
    assert finding.severity == "high"
    assert "write policy" in finding.title


def test_unknown_table_policy_is_cautious_medium(tmp_path):
    report = _report_for_sql(
        tmp_path,
        """
        create policy "Anyone can read widgets"
        on public.widgets
        for select
        using (true);
        """,
    )
    finding = _wide_open_findings(report)[0]
    assert finding.severity == "medium"
    assert "could not classify" in finding.why_it_matters


def test_multiline_policy_block_is_parsed(tmp_path):
    report = _report_for_sql(
        tmp_path,
        """
        create policy "Anyone can read customers"
          on public.customers
          for select
          using (
            true
          );
        """,
    )
    finding = _wide_open_findings(report)[0]
    assert finding.severity == "high"
    assert "customers" in finding.title


def test_scoped_policy_is_not_wide_open(tmp_path):
    report = _report_for_sql(
        tmp_path,
        """
        create policy "Users can read own profile"
        on public.profiles
        for select
        using (auth.uid() = user_id);
        """,
    )
    assert not _wide_open_findings(report)
