"""The landing page `crack all` writes above the six reports."""
import os

from .render import esc

TITLES = {
    "product-intent": "Product intent",
    "git-history": "Git history",
    "schema": "Schema",
    "interfaces": "Interfaces",
    "architecture": "Architecture",
    "backend": "Backend",
}

NOTES = {
    "product-intent": "the product story, reverse engineered from the source",
    "git-history": "the roadmap already written in the git log",
    "schema": "the data model and how it migrated",
    "interfaces": "the API surface and one action traced through it",
    "architecture": "the services and how a request crosses them",
    "backend": "the six layers every request flows through",
}

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #f7f8fa; --surface: #fff; --text: #101828; --muted: #667085;
    --faint: #98a2b3; --rule: #e4e7ec; --accent: #4f46e5;
    --bad: #b42318; --bad-bg: #fef3f2;
    --shadow: 0 1px 2px rgba(16,24,40,.05); --radius: 12px;
  }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    font-size: 13.5px; line-height: 1.5; background: var(--bg); color: var(--text); margin: 0;
    -webkit-font-smoothing: antialiased; }}
  main {{ max-width: 900px; margin: 0 auto; padding: 0 24px 56px; }}
  .hero {{ background: radial-gradient(120% 140% at 50% 0%, #1e1b4b 0%, #0f0d2b 70%);
    color: #fff; padding: 46px 20px 42px; text-align: center; }}
  .eyebrow {{ display: inline-flex; align-items: center; gap: 7px; color: #a5b4fc;
    font-size: .68rem; font-weight: 700; letter-spacing: .18em; text-transform: uppercase; }}
  .eyebrow::before {{ content: ''; width: 16px; height: 2px; background: #818cf8; border-radius: 2px; }}
  .hero h1 {{ font-size: 1.9rem; font-weight: 800; letter-spacing: -.025em; margin: 12px 0 10px; }}
  .hero .sub {{ font-size: .94rem; color: #d6d8f5; margin: 0; }}
  ul.reports {{ list-style: none; padding: 0; margin: 32px 0 0; display: grid; gap: 14px; }}
  a.report {{ display: block; background: var(--surface); border: 1px solid var(--rule);
    border-left: 4px solid var(--accent); border-radius: var(--radius); box-shadow: var(--shadow);
    padding: 18px 22px; text-decoration: none; color: inherit; }}
  a.report:hover {{ border-color: var(--accent); }}
  .report h2 {{ margin: 0 0 5px; font-size: 1rem; font-weight: 700; }}
  .report p {{ margin: 0; font-size: .86rem; color: var(--muted); }}
  .failed {{ background: var(--bad-bg); border: 1px solid #fecdca; border-radius: var(--radius);
    padding: 16px 20px; margin-top: 26px; }}
  .failed h2 {{ margin: 0 0 8px; font-size: .78rem; font-weight: 700; letter-spacing: .1em;
    text-transform: uppercase; color: var(--bad); }}
  .failed li {{ font-size: .84rem; color: #7a271a; margin: .3em 0; }}
  .failed code {{ font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: .82em; }}
  footer {{ color: var(--faint); font-size: .74rem; text-align: center; margin-top: 44px;
    padding-top: 18px; border-top: 1px solid var(--rule); }}
</style>
</head>
<body>
  <header class="hero">
    <span class="eyebrow">Codebase</span>
    <h1>{name}</h1>
    <p class="sub">{sub}</p>
  </header>
  <main>
    <ul class="reports">
{cards}
    </ul>
{failures}
    <footer>Written by crack.</footer>
  </main>
</body>
</html>
"""

def _card(name, rel, welcome):
    note = welcome if welcome else NOTES.get(name, "")
    return (f'      <li><a class="report" href="{esc(rel)}">\n'
            f'        <h2>{esc(TITLES.get(name, name))}</h2>\n'
            f'        <p>{esc(note)}</p>\n'
            f'      </a></li>')

def _failures(failed):
    if not failed:
        return ""
    items = "\n".join(
        f"        <li><code>{esc(name)}</code> -- {esc(exc)}</li>" for name, exc in failed)
    return ('    <section class="failed">\n'
            '      <h2>Did not run</h2>\n'
            f'      <ul>\n{items}\n      </ul>\n'
            '    </section>\n')

def write_index(root, repo_name, written, failed):
    """Write the landing page linking each report. Returns its path."""
    os.makedirs(root, exist_ok=True)
    cards = "\n".join(
        _card(name, os.path.join(os.path.basename(path), "index.html"), welcome)
        for name, (path, welcome) in written.items())
    n = len(written)
    sub = f"{n} of 6 reads complete." if failed else "Six reads of one codebase."
    page = PAGE.format(name=esc(repo_name), sub=esc(sub), cards=cards,
                       failures=_failures(failed))
    path = os.path.join(root, "index.html")
    with open(path, "w") as fh:
        fh.write(page)
    return path
