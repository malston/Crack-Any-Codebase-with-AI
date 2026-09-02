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

def test_a_cached_response_round_trips(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", str(tmp_path))
    monkeypatch.delenv("LLM_CACHE", raising=False)
    assert cache._cache_get("anthropic", "claude-x", "prompt") is None

    cache._cache_put("anthropic", "claude-x", "prompt", "the answer")
    assert cache._cache_get("anthropic", "claude-x", "prompt") == "the answer"

def test_the_key_separates_provider_model_and_prompt(tmp_path, monkeypatch):
    """A cache hit across providers or models would serve one model's answer
    as another's, and a hit across prompts would defeat the retry tails."""
    monkeypatch.setattr(cache, "CACHE_DIR", str(tmp_path))
    monkeypatch.delenv("LLM_CACHE", raising=False)
    cache._cache_put("anthropic", "claude-x", "prompt", "claude answer")

    assert cache._cache_get("openai", "claude-x", "prompt") is None
    assert cache._cache_get("anthropic", "gpt-x", "prompt") is None
    assert cache._cache_get("anthropic", "claude-x", "prompt (retry 1)") is None
    assert cache._cache_get("anthropic", "claude-x", "prompt") == "claude answer"

def test_the_cache_path_is_stable_across_calls(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", str(tmp_path))
    first = cache._cache_path("anthropic", "claude-x", "prompt")
    assert first == cache._cache_path("anthropic", "claude-x", "prompt")
    assert first != cache._cache_path("anthropic", "claude-x", "other")

def test_llm_cache_off_neither_reads_nor_writes(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", str(tmp_path))
    monkeypatch.delenv("LLM_CACHE", raising=False)
    cache._cache_put("anthropic", "claude-x", "prompt", "the answer")

    monkeypatch.setenv("LLM_CACHE", "0")
    assert cache._cache_get("anthropic", "claude-x", "prompt") is None
    cache._cache_put("anthropic", "claude-x", "fresh", "not written")

    monkeypatch.delenv("LLM_CACHE")
    assert cache._cache_get("anthropic", "claude-x", "fresh") is None
    assert cache._cache_get("anthropic", "claude-x", "prompt") == "the answer"

def test_a_truncated_cache_file_is_a_miss_not_a_crash(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", str(tmp_path))
    monkeypatch.delenv("LLM_CACHE", raising=False)
    path = cache._cache_path("anthropic", "claude-x", "prompt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write('{"provider": "anthropic", "resp')

    assert cache._cache_get("anthropic", "claude-x", "prompt") is None

def test_a_cache_file_missing_its_response_field_is_a_miss(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", str(tmp_path))
    monkeypatch.delenv("LLM_CACHE", raising=False)
    path = cache._cache_path("anthropic", "claude-x", "prompt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write('{"provider": "anthropic", "model": "claude-x"}')

    assert cache._cache_get("anthropic", "claude-x", "prompt") is None

def test_an_empty_response_is_cached_and_returned(tmp_path, monkeypatch):
    """A miss is None, so an empty string must not read as one."""
    monkeypatch.setattr(cache, "CACHE_DIR", str(tmp_path))
    monkeypatch.delenv("LLM_CACHE", raising=False)
    cache._cache_put("anthropic", "claude-x", "prompt", "")
    assert cache._cache_get("anthropic", "claude-x", "prompt") == ""
