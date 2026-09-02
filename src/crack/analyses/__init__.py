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

_REQUIRED = ("NAME", "build_flow", "init_shared")

def load(name):
    """Import and return one analysis module. Raises KeyError if unknown."""
    if name not in _MODULES:
        raise KeyError(f"unknown analysis {name!r}; expected one of {', '.join(ANALYSIS_NAMES)}")
    module = importlib.import_module(f"crack.analyses.{_MODULES[name]}")
    is_card = hasattr(module, "THEME") and hasattr(module, "SECTIONS")
    is_bespoke = hasattr(module, "render_html") and hasattr(module, "render_markdown")
    missing = [attr for attr in _REQUIRED if not hasattr(module, attr)]
    if not (is_card or is_bespoke):
        missing.append("THEME/SECTIONS or render_html/render_markdown")
    if missing:
        raise AttributeError(f"analysis {name!r} is missing {', '.join(missing)}")
    return module
