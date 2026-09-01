import sys
import types

import pytest
from crack import analyses

def test_all_six_real_analyses_load_cleanly():
    for name in analyses.ANALYSIS_NAMES:
        analyses.load(name)

def test_stub_missing_sections_raises_naming_the_analysis(monkeypatch):
    stub = types.ModuleType("crack.analyses.stub")
    stub.NAME = "stub"
    stub.build_flow = lambda: None
    stub.init_shared = lambda args, out_dir: None
    stub.THEME = object()  # THEME without SECTIONS: not a card, not bespoke either
    monkeypatch.setitem(sys.modules, "crack.analyses.stub", stub)
    monkeypatch.setitem(analyses._MODULES, "stub", "stub")

    with pytest.raises(AttributeError, match="stub"):
        analyses.load("stub")

def test_six_analyses_in_port_order():
    assert analyses.ANALYSIS_NAMES == (
        "backend", "architecture", "interfaces",
        "schema", "git-history", "product-intent",
    )

def test_unknown_name_raises_keyerror():
    with pytest.raises(KeyError):
        analyses.load("nonsense")

def test_load_is_lazy():
    """Importing the registry must not import any analysis module."""
    import subprocess, sys
    code = (
        "import sys; import crack.analyses; "
        "print([m for m in sys.modules if m.startswith('crack.analyses.')])"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.stdout.strip() == "[]", out.stdout
