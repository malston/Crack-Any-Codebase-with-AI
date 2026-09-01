import os
import types
import pytest
from crack.core import runner

def _fake_analysis(**overrides):
    """A minimal analysis module standing in for a real one."""
    mod = types.SimpleNamespace()
    mod.NAME = "fake"
    mod.ENV_DEFAULTS = {}
    mod.SECTIONS = []
    mod.init_shared = lambda args, out_dir: {"repo_path": args.repo_path}
    mod.overview_spec = lambda shared: {"name": "x", "what": "y", "sections": []}
    ran = {"count": 0}

    def build_flow():
        flow = types.SimpleNamespace()
        def run(shared):
            ran["count"] += 1
            shared["ran"] = True
        flow.run = run
        return flow

    mod.build_flow = build_flow
    mod._ran = ran
    for key, value in overrides.items():
        setattr(mod, key, value)
    return mod

def test_repo_name_strips_trailing_slash():
    assert runner.repo_name_of("/tmp/zulip/") == "zulip"
    assert runner.repo_name_of("/tmp/zulip") == "zulip"

def test_output_dir_layout():
    assert runner.output_dir("/out", "zulip", "backend") == os.path.join(
        "/out", "zulip", "backend")

def test_run_analysis_writes_both_files(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "render_html", lambda a, n, s: "<html>ok</html>")
    monkeypatch.setattr(runner, "render_markdown", lambda a, n, s: "# ok")
    repo = tmp_path / "myrepo"
    repo.mkdir()
    analysis = _fake_analysis()
    args = types.SimpleNamespace(repo_path=str(repo))

    out = runner.run_analysis(analysis, str(repo), str(tmp_path / "out"), args)

    assert analysis._ran["count"] == 1
    assert open(os.path.join(out, "index.html")).read() == "<html>ok</html>"
    assert open(os.path.join(out, "index.md")).read() == "# ok"
    assert out.endswith(os.path.join("myrepo", "fake"))

def test_run_analysis_applies_env_defaults(tmp_path, monkeypatch):
    monkeypatch.delenv("LLM_MAX_OUTPUT_TOKENS", raising=False)
    monkeypatch.setattr(runner, "render_html", lambda a, n, s: "")
    monkeypatch.setattr(runner, "render_markdown", lambda a, n, s: "")
    seen = {}

    def build_flow():
        flow = types.SimpleNamespace()
        flow.run = lambda shared: seen.update(
            value=os.environ.get("LLM_MAX_OUTPUT_TOKENS"))
        return flow

    repo = tmp_path / "r"
    repo.mkdir()
    analysis = _fake_analysis(ENV_DEFAULTS={"LLM_MAX_OUTPUT_TOKENS": "32768"},
                              build_flow=build_flow)
    runner.run_analysis(analysis, str(repo), str(tmp_path / "out"),
                        types.SimpleNamespace(repo_path=str(repo)))

    assert seen["value"] == "32768"
    assert "LLM_MAX_OUTPUT_TOKENS" not in os.environ

def test_run_analysis_passes_out_dir_to_init_shared(tmp_path, monkeypatch):
    """ch05 needs out_dir in shared before the flow runs (pain.png)."""
    monkeypatch.setattr(runner, "render_html", lambda a, n, s: "")
    monkeypatch.setattr(runner, "render_markdown", lambda a, n, s: "")
    captured = {}
    repo = tmp_path / "r"
    repo.mkdir()
    analysis = _fake_analysis(
        init_shared=lambda args, out_dir: captured.update({"out_dir": out_dir}) or
        {"repo_path": args.repo_path})
    out = runner.run_analysis(analysis, str(repo), str(tmp_path / "out"),
                              types.SimpleNamespace(repo_path=str(repo)))
    assert captured["out_dir"] == out
