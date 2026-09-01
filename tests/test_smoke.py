"""End-to-end run against a real provider. Skipped without an API key."""
import os
import pytest
from crack import cli

HAS_KEY = any(os.environ.get(k) for k in
              ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"))

pytestmark = pytest.mark.skipif(not HAS_KEY, reason="no LLM provider key set")

def test_backend_analysis_end_to_end(fixture_repo, tmp_path):
    code = cli.main(["backend", fixture_repo, "--out", str(tmp_path)])
    assert code == 0

    out = tmp_path / os.path.basename(fixture_repo) / "backend"
    html = (out / "index.html").read_text()
    markdown = (out / "index.md").read_text()

    assert "<!doctype html>" in html.lower()
    assert len(markdown) > 200
    assert "## The pipeline" in markdown
