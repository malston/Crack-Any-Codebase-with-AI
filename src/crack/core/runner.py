"""Run one analysis end to end and write its report."""
import os

from .env import env_defaults
from .render import render_html, render_markdown

def repo_name_of(repo_path):
    """The directory name of the repo, used as the output folder name."""
    return os.path.basename(os.path.abspath(repo_path).rstrip(os.sep))

def output_dir(root, repo_name, analysis_name):
    return os.path.join(root, repo_name, analysis_name)

def run_analysis(analysis, repo_path, out_root, args):
    """Run one analysis and write index.md + index.html. Returns the output dir.

    The output directory is created before the flow runs, because some
    analyses write extra files into it during the run (ch05 writes pain.png).
    """
    name = repo_name_of(repo_path)
    out_dir = output_dir(out_root, name, analysis.NAME)
    os.makedirs(out_dir, exist_ok=True)

    shared = analysis.init_shared(args, out_dir)
    with env_defaults(getattr(analysis, "ENV_DEFAULTS", {})):
        analysis.build_flow().run(shared)

    with open(os.path.join(out_dir, "index.md"), "w") as fh:
        fh.write(render_markdown(analysis, name, shared))
    with open(os.path.join(out_dir, "index.html"), "w") as fh:
        fh.write(render_html(analysis, name, shared))
    return out_dir
