#!/usr/bin/env python3
"""Builds prototype/research.html from the research notes in this folder.

Each NN-name.md becomes one tab. Needs pandoc. Run from anywhere:
    python3 prototype/research/build.py
"""
import html
import pathlib
import re
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / 'research.html'

# file stem -> (tab id, tab label)
TABS = {
    '00-overview': ('overview', 'Overview'),
    '01-dashboard-design': ('dashboard', 'Dashboard'),
    '02-key-decision-makers': ('decision-makers', 'Decision makers'),
    '03-progress-and-pacing': ('pacing', 'Progress & pacing'),
    '04-ecosystem': ('ecosystem', 'Ecosystem'),
    '05-news-pipeline': ('news', 'News pipeline'),
}


def render(path, tab):
    body = subprocess.run(
        ['pandoc', '-f', 'gfm', '-t', 'html5', '--id-prefix', f'{tab}-', str(path)],
        check=True, capture_output=True, text=True).stdout
    # Links between the notes open the matching tab.
    for stem, (other, _) in TABS.items():
        body = body.replace(f'href="{stem}.md"', f'href="#{other}"')
        body = body.replace(f'href="./{stem}.md"', f'href="#{other}"')
    # Wide tables scroll on their own instead of the page.
    body = body.replace('<table>', '<div class="scroll"><table>').replace('</table>', '</table></div>')
    # External links open in a new tab.
    body = re.sub(r'<a href="(https?://)', r'<a target="_blank" rel="noopener" href="\1', body)
    return body


notes = sorted(p for p in HERE.glob('[0-9][0-9]-*.md') if p.stem in TABS)
buttons, panels = [], []
for i, path in enumerate(notes):
    tab, label = TABS[path.stem]
    buttons.append(
        f'<a role="tab" id="tab-{tab}" href="#{tab}" aria-controls="{tab}">{html.escape(label)}</a>')
    panels.append(
        f'<section role="tabpanel" id="{tab}" aria-labelledby="tab-{tab}">\n{render(path, tab)}</section>')

page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Earth, seen from outside</title>
<link rel="stylesheet" href="../style.css">
<style>
 main{{display:block;max-width:52rem;margin:0 auto;padding:1rem 1rem 4rem}}
 .intro h1{{font-weight:500;font-size:2rem;margin:.5rem 0 .3rem}}
 .intro p{{color:var(--muted)}}
 .tabs{{position:sticky;top:0;z-index:1;display:flex;gap:1.4rem;overflow-x:auto;scrollbar-width:none;
   margin:1.6rem 0 1.4rem;padding:.7rem 0 0;background:var(--ivory);border-bottom:1px solid #d9d3c4}}
 .tabs::-webkit-scrollbar{{display:none}}
 .tabs a{{flex:none;padding:0 0 .55rem;color:var(--muted);text-decoration:none;white-space:nowrap;
   border-bottom:2px solid transparent;margin-bottom:-1px}}
 .tabs a:hover{{color:var(--ink)}}
 .tabs a[aria-selected="true"]{{color:var(--black);border-bottom-color:var(--black)}}
 .tabs a:focus-visible{{outline:1px solid var(--black);outline-offset:4px}}
 .js [role="tabpanel"]{{display:none}}
 .js [role="tabpanel"].on{{display:block}}
 [role="tabpanel"]+[role="tabpanel"]{{margin-top:3rem}}
 .js [role="tabpanel"]+[role="tabpanel"]{{margin-top:0}}
 section h1{{font-weight:500;font-size:1.65rem;line-height:1.25;margin:0 0 .8rem}}
 section h2{{font-weight:500;font-size:1.3rem;margin:2.2rem 0 .5rem}}
 section h3{{font-weight:500;font-size:1.08rem;font-style:italic;margin:1.5rem 0 .3rem}}
 section h4{{font-weight:500;font-size:1rem;margin:1.2rem 0 .2rem}}
 section p,section ul,section ol,section blockquote{{margin:.55rem 0}}
 section ul,section ol{{padding-left:1.3rem}}
 section li+li{{margin-top:.2rem}}
 section a{{color:var(--ink);text-decoration-color:var(--muted);text-decoration-thickness:1px;text-underline-offset:.2em;
   overflow-wrap:anywhere}}
 section a:hover{{text-decoration-thickness:2px}}
 section{{overflow-wrap:break-word}}
 section code{{font-size:.85em;overflow-wrap:anywhere}}
 section hr{{border:0;border-top:1px solid #d9d3c4;margin:2rem 0}}
 section blockquote{{padding-left:1rem;border-left:2px solid #d9d3c4;color:var(--muted)}}
 .scroll{{overflow-x:auto;margin:1rem 0}}
 table{{border-collapse:collapse;font-size:.8rem;line-height:1.45;min-width:100%}}
 th,td{{text-align:left;vertical-align:top;padding:.4rem .6rem;border-bottom:1px solid #e6e0d2}}
 th{{font-weight:500;border-bottom-color:#cfc8b8}}
 td{{min-width:7rem}}
 @media (max-width:760px){{body{{font-size:17px}}main{{padding:0 1rem 3rem}}.tabs{{gap:1.1rem}}}}
main a{color:var(--ink);text-decoration-color:var(--muted);text-decoration-thickness:1px;text-underline-offset:.22em;transition:text-decoration-color .2s}main a:hover,main a:focus-visible{text-decoration-color:var(--ink);text-decoration-thickness:2px}
</style>
</head>
<body>
<header><a class="brand" href="../"><span class="wordmark">Dragonfly</span><div id="dragonfly" aria-hidden="true"></div></a></header>
<main>
<div class="intro">
<h1>Earth, seen from outside</h1>
<p>Research notes for a civilisational “AI and everything” dashboard: how it is going, as an alien judge would see it. Compiled 6 November 2026. Draft research, not checked for publication.</p>
</div>
<nav class="tabs" role="tablist" aria-label="Research notes">
{chr(10).join(buttons)}
</nav>
{chr(10).join(panels)}
</main>
<script>
(() => {{
  document.documentElement.classList.add('js');
  const tabs = [...document.querySelectorAll('[role="tab"]')];
  const show = (id, scroll) => {{
    const panel = document.getElementById(id);
    const owner = panel && panel.closest('[role="tabpanel"]');
    if (!owner) return false;
    for (const t of tabs) {{
      const on = t.getAttribute('aria-controls') === owner.id;
      t.setAttribute('aria-selected', on);
      t.tabIndex = on ? 0 : -1;
      document.getElementById(t.getAttribute('aria-controls')).classList.toggle('on', on);
      if (on) t.scrollIntoView({{block: 'nearest', inline: 'nearest'}});
    }}
    if (panel !== owner) panel.scrollIntoView();
    else if (scroll) window.scrollTo(0, 0);
    return true;
  }};
  const route = (scroll) => show(decodeURIComponent(location.hash.slice(1)), scroll) || show(tabs[0].getAttribute('aria-controls'));
  addEventListener('hashchange', () => route(true));
  document.querySelector('[role="tablist"]').addEventListener('keydown', (e) => {{
    const i = tabs.indexOf(document.activeElement), step = {{ArrowRight: 1, ArrowLeft: -1}}[e.key];
    if (i < 0 || !step) return;
    const next = tabs[(i + step + tabs.length) % tabs.length];
    next.focus(); next.click();
  }});
  route(false);
}})();
</script>
<script type="module" src="../animations/site.js"></script>
</body></html>
'''
OUT.write_text(page)
print(f'wrote {OUT} ({len(notes)} tabs)')
