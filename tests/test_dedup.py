import json

from shipcheck.engine import run_audit
from shipcheck.report import render_json


def _write_route(root, rel_path: str):
    route = root / rel_path
    route.parent.mkdir(parents=True)
    route.write_text(
        """
        export async function POST(req: Request) {
          return Response.json({ ok: true });
        }
        """,
        encoding="utf-8",
    )


def _findings(report, finding_id: str):
    return [f for f in report.findings if f.id == finding_id]


def test_repeated_tutorial_findings_group_to_one_representative(tmp_path):
    _write_route(tmp_path, "01-start/app/api/public/route.ts")
    _write_route(tmp_path, "02-final/app/api/public/route.ts")

    report = run_audit(str(tmp_path))
    auth_findings = _findings(report, "auth.api_mutation_no_guard")

    assert len(auth_findings) == 1
    assert auth_findings[0].duplicate_count == 2
    assert auth_findings[0].suppressed_duplicates == 1
    assert len(auth_findings[0].duplicate_examples) == 2
    assert report.categories["auth"]["score"] == 8


def test_duplicate_metadata_is_visible_in_json(tmp_path):
    _write_route(tmp_path, "01-start/app/api/public/route.ts")
    _write_route(tmp_path, "02-final/app/api/public/route.ts")

    data = json.loads(render_json(run_audit(str(tmp_path))))
    auth_finding = next(f for f in data["findings"] if f["id"] == "auth.api_mutation_no_guard")

    assert auth_finding["duplicate_count"] == 2
    assert auth_finding["suppressed_duplicates"] == 1
    assert auth_finding["deduped_by"] == "tutorial_path_fingerprint"
    assert len(auth_finding["duplicate_examples"]) == 2


def test_distinct_routes_do_not_collapse(tmp_path):
    _write_route(tmp_path, "01-start/app/api/admin/route.ts")
    _write_route(tmp_path, "02-final/app/api/users/route.ts")

    report = run_audit(str(tmp_path))
    assert len(_findings(report, "auth.api_mutation_no_guard")) == 2


def test_distinct_app_surfaces_do_not_collapse(tmp_path):
    _write_route(tmp_path, "apps/web/app/api/public/route.ts")
    _write_route(tmp_path, "apps/admin/app/api/public/route.ts")

    report = run_audit(str(tmp_path))
    auth_findings = _findings(report, "auth.api_mutation_no_guard")

    assert len(auth_findings) == 2
    assert all(f.suppressed_duplicates is None for f in auth_findings)


def test_distinct_finding_ids_do_not_collapse(tmp_path):
    _write_route(tmp_path, "01-start/app/api/public/route.ts")
    _write_route(tmp_path, "02-final/app/api/public/route.ts")

    report = run_audit(str(tmp_path))

    assert len(_findings(report, "auth.api_mutation_no_guard")) == 1
    assert len(_findings(report, "reliability.no_rate_limit")) == 1
    assert {f.id for f in report.findings} >= {"auth.api_mutation_no_guard", "reliability.no_rate_limit"}


def test_normal_single_app_routes_are_not_suppressed(tmp_path):
    _write_route(tmp_path, "app/api/public/route.ts")
    _write_route(tmp_path, "app/api/other/route.ts")

    report = run_audit(str(tmp_path))
    auth_findings = _findings(report, "auth.api_mutation_no_guard")

    assert len(auth_findings) == 2
    assert all(f.suppressed_duplicates is None for f in auth_findings)
