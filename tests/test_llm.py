"""Unit tests for the plumbing in `crack.core.llm`.

The product-intent analysis keeps private copies of `parse_yaml` and
`yaml_call` (`analyses/product_intent/nodes.py`); nothing here covers those.
"""
import json

import pytest
import yaml

from crack.core import llm


def test_fill_replaces_slots_and_leaves_json_examples_alone():
    template = 'Repo: {name}\nExample: {"table": "users"}'
    assert llm.fill(template, name="notes-app") == (
        'Repo: notes-app\nExample: {"table": "users"}')


def test_fill_stringifies_non_string_values():
    assert llm.fill("count={n}", n=7) == "count=7"


def test_read_prompt_reads_utf8_content(tmp_path):
    """The locale side of this is asserted in tests/test_encoding_and_env.py,
    which forces a C locale in a subprocess. Setting LC_ALL in this process
    cannot change an encoding CPython fixed at interpreter startup."""
    (tmp_path / "p.md").write_text("café — naïve", encoding="utf-8")
    assert llm.read_prompt(str(tmp_path), "p.md") == "café — naïve"


def test_read_prompt_raises_on_a_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        llm.read_prompt(str(tmp_path), "absent.md")


def test_extract_mermaid_takes_the_first_block():
    md = "intro\n```mermaid\nflowchart LR\n  a --> b\n```\ntail\n```mermaid\nerDiagram\n```\n"
    assert llm.extract_mermaid(md) == "flowchart LR\n  a --> b"


def test_extract_mermaid_can_require_a_diagram_kind():
    md = "```mermaid\nflowchart LR\n```\n```mermaid\nerDiagram\n  A ||--o{ B : has\n```"
    assert llm.extract_mermaid(md, "erDiagram") == "erDiagram\n  A ||--o{ B : has"


def test_extract_mermaid_returns_empty_when_absent():
    assert llm.extract_mermaid("no diagram here") == ""
    assert llm.extract_mermaid(None) == ""


def test_parse_json_reads_a_fenced_object():
    assert llm.parse_json('sure:\n```json\n{"a": 1}\n```\n') == {"a": 1}


def test_parse_json_reads_an_unfenced_value():
    assert llm.parse_json('here you go [1, 2]') == [1, 2]


def test_parse_json_survives_a_nested_fence_inside_a_string_value():
    """raw_decode, not a closing-fence regex — so an embedded ``` can't truncate."""
    payload = {"diagram": "```mermaid\nflowchart LR\n```", "name": "x"}
    text = "```json\n" + json.dumps(payload) + "\n```\ntrailing prose"
    assert llm.parse_json(text) == payload


def test_parse_json_raises_when_there_is_no_json():
    with pytest.raises(AssertionError, match="No JSON found"):
        llm.parse_json("the model apologised instead")


def test_parse_yaml_reads_a_fenced_block():
    assert llm.parse_yaml('```yaml\ncompetitors:\n  - name: A\n```') == {
        "competitors": [{"name": "A"}]}


def test_parse_yaml_raises_without_a_fence():
    with pytest.raises(AssertionError, match="missing ```yaml fence"):
        llm.parse_yaml("competitors: []")


def _replies(*texts):
    """A call_llm stand-in returning each text in turn, recording the prompts."""
    seen = []
    remaining = list(texts)

    def fake(prompt):
        seen.append(prompt)
        return remaining.pop(0) if remaining else texts[-1]
    return fake, seen


def test_json_call_returns_the_normalized_value(monkeypatch):
    fake, seen = _replies('```json\n{"eras": [{"name": "start"}]}\n```')
    monkeypatch.setattr(llm, "call_llm", fake)
    assert llm.json_call("PROMPT", lambda r: r["eras"]) == [{"name": "start"}]
    assert seen == ["PROMPT"]


def test_json_call_retries_with_a_changed_tail_so_the_retry_misses_the_cache(monkeypatch):
    fake, seen = _replies("no json at all", '```json\n{"ok": true}\n```')
    monkeypatch.setattr(llm, "call_llm", fake)
    assert llm.json_call("PROMPT", lambda r: r) == {"ok": True}
    assert seen[0] == "PROMPT"
    assert seen[1].startswith("PROMPT") and seen[1] != "PROMPT"


def test_json_call_retries_when_normalize_rejects_a_missing_field(monkeypatch):
    def normalize(result):
        assert "start" in result, "era missing 'start'"
        return result
    fake, seen = _replies('```json\n{"name": "x"}\n```', '```json\n{"name": "x", "start": "2020-01"}\n```')
    monkeypatch.setattr(llm, "call_llm", fake)
    assert llm.json_call("PROMPT", normalize)["start"] == "2020-01"
    assert len(seen) == 2


def test_json_call_gives_up_after_the_retry_budget(monkeypatch):
    fake, seen = _replies("never valid")
    monkeypatch.setattr(llm, "call_llm", fake)
    with pytest.raises(AssertionError, match="gave up after 3 tries"):
        llm.json_call("PROMPT", lambda r: r, retries=3)
    assert len(seen) == 3


def test_json_call_lets_network_errors_bubble_to_the_node(monkeypatch):
    """Only parse/validation errors retry here; transport errors are the node's job."""
    def boom(prompt):
        raise ConnectionError("socket closed")
    monkeypatch.setattr(llm, "call_llm", boom)
    with pytest.raises(ConnectionError):
        llm.json_call("PROMPT", lambda r: r)


def test_yaml_call_returns_the_normalized_value(monkeypatch):
    fake, _ = _replies("```yaml\npresent: []\nabsent: []\n```")
    monkeypatch.setattr(llm, "call_llm", fake)
    assert llm.yaml_call("PROMPT", lambda r: r) == {"present": [], "absent": []}


def test_yaml_call_retries_on_broken_quoting(monkeypatch):
    fake, seen = _replies('```yaml\nname: "un"escaped"\n```', '```yaml\nname: "fine"\n```')
    monkeypatch.setattr(llm, "call_llm", fake)
    assert llm.yaml_call("PROMPT", lambda r: r) == {"name": "fine"}
    assert "escape any double quote" in seen[1]


def test_yaml_call_gives_up_after_the_retry_budget(monkeypatch):
    fake, seen = _replies("no fence")
    monkeypatch.setattr(llm, "call_llm", fake)
    with pytest.raises(AssertionError, match="gave up after 2 tries"):
        llm.yaml_call("PROMPT", lambda r: r, retries=2)
    assert len(seen) == 2


def test_yaml_call_lets_network_errors_bubble_to_the_node(monkeypatch):
    def boom(prompt):
        raise ConnectionError("socket closed")
    monkeypatch.setattr(llm, "call_llm", boom)
    with pytest.raises(ConnectionError):
        llm.yaml_call("PROMPT", lambda r: r)


def test_yaml_is_the_dependency_the_module_actually_imports():
    """The YAML helpers resolve the real package, not a shadowed name."""
    assert llm.yaml is yaml
