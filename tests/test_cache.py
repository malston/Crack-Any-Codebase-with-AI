import os
import sys

import crack.core.call_llm  # noqa: F401 (registers the submodule in sys.modules)

# crack.core.__init__ re-exports a function named call_llm, which shadows the
# submodule of the same name as a package attribute, so the module must come
# from sys.modules rather than attribute access.
cache = sys.modules["crack.core.call_llm"]

def test_cache_put_swallows_oserror_on_unwritable_dir(tmp_path, monkeypatch):
    unwritable = tmp_path / "cache"
    unwritable.mkdir()
    os.chmod(unwritable, 0o500)  # read + execute only, no write
    monkeypatch.setattr(cache, "CACHE_DIR", str(unwritable / "sub"))
    monkeypatch.delenv("LLM_CACHE", raising=False)

    try:
        cache._cache_put("anthropic", "claude-x", "prompt", "response")
    finally:
        os.chmod(unwritable, 0o700)

def test_cache_get_swallows_oserror_on_unreadable_file(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", str(tmp_path))
    monkeypatch.delenv("LLM_CACHE", raising=False)
    path = cache._cache_path("anthropic", "claude-x", "prompt")
    with open(path, "w") as fh:
        fh.write("{}")
    os.chmod(path, 0o000)

    try:
        result = cache._cache_get("anthropic", "claude-x", "prompt")
    finally:
        os.chmod(path, 0o600)

    assert result is None
