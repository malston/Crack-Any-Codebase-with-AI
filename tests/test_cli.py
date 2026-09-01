import os
import types
import pytest
from crack import cli

def test_parser_has_all_seven_subcommands():
    parser = cli.build_parser()
    action = next(a for a in parser._actions if a.dest == "command")
    assert set(action.choices) == {
        "backend", "architecture", "interfaces", "schema",
        "git-history", "product-intent", "all",
    }

def test_parser_builds_before_any_analysis_exists():
    """_add_analysis_arguments swallows import errors, so --help always works.

    Per-analysis flag wiring is asserted in Tasks 10, 11 and 12, and end to end
    through the CLI in Task 13; those analyses do not exist when this runs.
    """
    parser = cli.build_parser()
    args = parser.parse_args(["backend", "/tmp/x", "--out", "/tmp/o"])
    assert args.repo_path == "/tmp/x"
    assert args.out == "/tmp/o"

def test_missing_repo_path_exits_before_running(tmp_path, capsys):
    code = cli.main(["backend", str(tmp_path / "nope")])
    assert code != 0
    assert "not a directory" in capsys.readouterr().err

def test_single_analysis_dispatches_to_runner(tmp_path, monkeypatch):
    repo = tmp_path / "r"
    repo.mkdir()
    calls = []
    monkeypatch.setattr(cli, "load", lambda name: types.SimpleNamespace(NAME=name))
    monkeypatch.setattr(
        cli, "run_analysis",
        lambda analysis, repo_path, out_root, args: calls.append(analysis.NAME) or ("/out", ""))
    assert cli.main(["backend", str(repo), "--out", str(tmp_path / "o")]) == 0
    assert calls == ["backend"]

def test_all_isolates_one_failing_analysis(tmp_path, monkeypatch, capsys):
    repo = tmp_path / "r"
    repo.mkdir()
    ran = []

    def fake_run(analysis, repo_path, out_root, args):
        if analysis.NAME == "schema":
            raise RuntimeError("no schema found")
        ran.append(analysis.NAME)
        return os.path.join(out_root, analysis.NAME), ""

    monkeypatch.setattr(cli, "load", lambda name: types.SimpleNamespace(
        NAME=name))
    monkeypatch.setattr(cli, "run_analysis", fake_run)
    monkeypatch.setattr(cli, "write_index", lambda *a, **k: "/out/index.html")

    code = cli.main(["all", str(repo), "--out", str(tmp_path / "o")])

    assert code != 0
    assert len(ran) == 5
    assert "schema" not in ran
    assert "schema" in capsys.readouterr().err

def test_per_analysis_flags_parse_now_that_analyses_exist():
    """Deferred from Task 6: these flags come from analyses built in Tasks 10-12."""
    parser = cli.build_parser()
    args = parser.parse_args(["git-history", "/tmp/x", "--max-graves", "3",
                              "--grave-min-files", "12"])
    assert args.max_graves == 3
    assert args.grave_min_files == 12
    args = parser.parse_args(["schema", "/tmp/x", "--schema", "db/schema.rb"])
    assert args.schema == "db/schema.rb"
    args = parser.parse_args(["product-intent", "/tmp/x",
                              "--include", "src/**", "--exclude", "**/test/**"])
    assert args.include == ["src/**"]
    assert args.exclude == ["**/test/**"]


def test_all_subcommand_accepts_every_analysis_flag():
    """`crack all` merges all six analyses' flags onto one parser."""
    parser = cli.build_parser()
    args = parser.parse_args(["all", "/tmp/x", "--schema", "db/schema.rb",
                              "--max-graves", "2", "--include", "src/**"])
    assert args.schema == "db/schema.rb"
    assert args.max_graves == 2
    assert args.include == ["src/**"]
