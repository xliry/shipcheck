import json

from click.testing import CliRunner

from shipcheck.cli import main


def test_cli_json_valid():
    result = CliRunner().invoke(main, ["tests/fixtures/next_supabase_bad", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.output)["score"] >= 60


def test_cli_threshold_exits_nonzero():
    result = CliRunner().invoke(main, ["tests/fixtures/next_supabase_bad", "--threshold", "50"])
    assert result.exit_code == 1
