import os
import time
import types
import pytest
from crack import cli
from crack.analyses import ANALYSIS_NAMES

def test_parser_has_all_seven_subcommands():
    parser = cli.build_parser()
    action = next(a for a in parser._actions if a.dest == "command")
    assert set(action.choices) == {
        "backend", "architecture", "interfaces", "schema",
        "git-history", "product-intent", "all",
    }

def test_parser_tolerates_an_unimportable_analysis(monkeypatch):
    """A module that cannot be imported must not break --help."""
    def flaky_load(name):
        if name == "schema":
            raise ImportError("simulated broken analysis module")
        return types.SimpleNamespace(NAME=name)

    monkeypatch.setattr(cli, "load", flaky_load)
    parser = cli.build_parser()
    assert parser.parse_args(["backend", "/tmp/x"]).repo_path == "/tmp/x"

def test_parser_surfaces_a_fault_inside_add_arguments(monkeypatch):
    """A bug in a working analysis must be loud, not silently missing flags."""
    def broken_add_arguments(parser):
        raise TypeError("bug inside add_arguments")

    monkeypatch.setattr(cli, "load", lambda name: types.SimpleNamespace(
        NAME=name, add_arguments=broken_add_arguments))
    with pytest.raises(TypeError, match="bug inside add_arguments"):
        cli.build_parser()

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

def test_all_isolates_an_analysis_that_fails_to_import(tmp_path, monkeypatch, capsys):
    """An import failure must be isolated like any other failure, not fatal."""
    repo = tmp_path / "r"
    repo.mkdir()
    ran = []

    def flaky_load(name):
        if name == "schema":
            raise ImportError("simulated broken analysis module")
        return types.SimpleNamespace(NAME=name)

    monkeypatch.setattr(cli, "load", flaky_load)
    monkeypatch.setattr(
        cli, "run_analysis",
        lambda analysis, repo_path, out_root, args:
            (ran.append(analysis.NAME) or os.path.join(out_root, analysis.NAME), ""))
    monkeypatch.setattr(cli, "write_index", lambda *a, **k: "/out/index.html")

    code = cli.main(["all", str(repo), "--out", str(tmp_path / "o")])

    assert code != 0
    assert len(ran) == 5
    assert "schema" not in ran
    assert "schema" in capsys.readouterr().err

def test_all_reports_every_analysis_failing(tmp_path, monkeypatch, capsys):
    """Six-of-six failures, with nothing about the CLI mocked.

    The isolation tests above patch `cli.load`, `cli.run_analysis` and
    `write_index`, so they cannot see a fault in the real wiring. Here an empty directory and an empty
    environment make every analysis fail on its own terms — a crawler that
    finds nothing, or `call_llm` with no provider key — and the landing page
    still has to be written and the exit code still has to be 1.
    """
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY",
                "LLM_PROVIDER"):
        monkeypatch.delenv(key, raising=False)
    # The asserts that stop most analyses live in post(), which pocketflow does
    # not retry. Two nodes reach an LLM call and back off for two seconds a try.
    monkeypatch.setattr(time, "sleep", lambda *_a, **_kw: None)
    repo = tmp_path / "hollow"
    repo.mkdir()
    out = tmp_path / "o"

    code = cli.main(["all", str(repo), "--out", str(out)])

    assert code == 1
    err = capsys.readouterr().err
    for name in ANALYSIS_NAMES:
        assert f"crack: {name} failed" in err

    index = (out / "hollow" / "index.html").read_text(encoding="utf-8")
    assert "Did not run" in index
    for name in ANALYSIS_NAMES:
        assert name in index
    assert not any((out / "hollow" / name).is_dir() and
                   (out / "hollow" / name / "index.html").exists()
                   for name in ANALYSIS_NAMES)


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
