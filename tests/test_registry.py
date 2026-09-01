import pytest
from crack import analyses

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
