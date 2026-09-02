"""Regression tests for a C-locale encoding failure and an unhelpful KeyError.

The pip-installed CLI is meant to run anywhere, including containers and CI
images that default to a C locale (LANG/LC_ALL unset or "C"). Under that
locale, Python's default `open()` text encoding is ASCII, so reading a prompt
file or writing a report that contains a non-ASCII character (an em dash, a
middle dot, a section sign) raises instead of completing.
"""
import os
import subprocess
import sys

import pytest

from crack.core.runner import repo_name_of


def _c_locale_env():
    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    env["PYTHONUTF8"] = "0"
    return env


def test_read_prompt_survives_c_locale():
    """A prompt file with non-ASCII content must load under a C locale."""
    code = (
        "from crack.core import read_prompt\n"
        "import crack.analyses.backend.nodes as n\n"
        "read_prompt(n.PROMPTS_DIR, 'pipeline.md')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], env=_c_locale_env(), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_every_analysis_loads_its_prompts_under_c_locale():
    """`load_prompt` must open UTF-8 in every analysis, not only the five that
    route through `crack.core.read_prompt`."""
    code = (
        "import importlib, os\n"
        "for name in ('architecture', 'backend', 'git_history', 'interfaces',\n"
        "             'product_intent', 'schema'):\n"
        "    nodes = importlib.import_module(f'crack.analyses.{name}.nodes')\n"
        "    for f in sorted(os.listdir(nodes.PROMPTS_DIR)):\n"
        "        nodes.load_prompt(f)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], env=_c_locale_env(), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_write_index_survives_c_locale(tmp_path):
    """The landing page write must survive a C locale even with non-ASCII input."""
    code = (
        "import sys\n"
        "from crack.core.index import write_index\n"
        f"write_index({str(tmp_path)!r}, 'a \\u2014 b \\u00b7 c \\u00a7', {{}}, [])\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], env=_c_locale_env(), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("modname", [
    "crack.analyses.architecture",
    "crack.analyses.backend",
    "crack.analyses.git_history",
    "crack.analyses.interfaces",
    "crack.analyses.schema",
])
def test_overview_spec_name_matches_repo_name_of(modname):
    """overview_spec's name must agree with the name the rendered page uses."""
    import importlib
    mod = importlib.import_module(modname)
    shared = {"repo_path": ".", "layer_counts": {}, "eras": [],
              "group_names": [], "table_list": [], "migration_names": []}
    assert mod.overview_spec(shared)["name"] == repo_name_of(".")


def test_unrecognised_llm_provider_raises_runtime_error_not_key_error(monkeypatch):
    import importlib
    call_llm = importlib.import_module("crack.core.call_llm")
    monkeypatch.setenv("LLM_PROVIDER", "claude")
    with pytest.raises(RuntimeError, match="claude") as exc_info:
        call_llm._model_for(call_llm._pick())
    assert not isinstance(exc_info.value, KeyError)
