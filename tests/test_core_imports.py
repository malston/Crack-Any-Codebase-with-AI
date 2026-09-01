"""crack.core must re-export the same surface utils/ does."""
import inspect

def test_core_reexports_public_surface():
    import crack.core as core

    expected = {
        "call_llm", "call_image", "write_overview", "OverviewNode",
        "read_prompt", "fill", "extract_mermaid", "parse_json", "parse_yaml",
        "json_call", "yaml_call", "crawl", "list_files", "safe_read",
        "DEFAULT_KEEP_EXT", "DEFAULT_SKIP_DIR", "DEFAULT_KEEP_NAMES",
        "DEFAULT_MAX_FILE_BYTES",
    }
    missing = expected - set(dir(core))
    assert not missing, f"crack.core is missing: {sorted(missing)}"

def test_core_does_not_touch_sys_path():
    """The chapters manipulate sys.path; the package must not."""
    import pathlib
    core_dir = pathlib.Path(inspect.getfile(__import__("crack.core", fromlist=["x"]))).parent
    for path in core_dir.glob("*.py"):
        assert "sys.path.insert" not in path.read_text(), f"{path.name} manipulates sys.path"

def test_call_llm_signature_matches_utils():
    from crack.core import call_llm
    assert list(inspect.signature(call_llm).parameters) == ["prompt"]
