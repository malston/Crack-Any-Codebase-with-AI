import os
import pytest
from crack.core.env import env_defaults

VAR = "LLM_MAX_OUTPUT_TOKENS"

@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv(VAR, raising=False)

def test_sets_default_when_absent():
    with env_defaults({VAR: "32768"}):
        assert os.environ[VAR] == "32768"

def test_restores_absence_on_exit():
    with env_defaults({VAR: "32768"}):
        pass
    assert VAR not in os.environ

def test_user_value_always_wins(monkeypatch):
    monkeypatch.setenv(VAR, "4096")
    with env_defaults({VAR: "32768"}):
        assert os.environ[VAR] == "4096"
    assert os.environ[VAR] == "4096"

def test_restores_even_when_body_raises():
    with pytest.raises(RuntimeError):
        with env_defaults({VAR: "32768"}):
            raise RuntimeError("boom")
    assert VAR not in os.environ

def test_empty_defaults_is_a_noop():
    with env_defaults({}):
        assert VAR not in os.environ
