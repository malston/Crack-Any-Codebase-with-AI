"""Registry of the six analyses, in port order (converged chapters first)."""
import importlib

ANALYSIS_NAMES = (
    "backend",
    "architecture",
    "interfaces",
    "schema",
    "git-history",
    "product-intent",
)

_MODULES = {name: name.replace("-", "_") for name in ANALYSIS_NAMES}

def load(name):
    """Import and return one analysis module. Raises KeyError if unknown."""
    if name not in _MODULES:
        raise KeyError(f"unknown analysis {name!r}; expected one of {', '.join(ANALYSIS_NAMES)}")
    return importlib.import_module(f"crack.analyses.{_MODULES[name]}")
