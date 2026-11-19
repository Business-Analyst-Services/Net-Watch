#!/usr/bin/env python3
"""Writes the Net Watch marketing pages (Home, Pilot plan, Team, Four roles) from tools/pages/*.body.html.
Shared header menu and footer come from sitenav.py; styles from docs/css/site.css."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from sitenav import nav, more
DOCS = os.path.join(os.path.dirname(HERE), 'docs')
PAGES = [('index', 'home', 'Net Watch | Empty every litter net before the storm',
          'Check this morning’s camera photos. Net Watch flags full, torn or blocked litter nets, checks the rain and emails the officer, who approves every job.'),
         ('pilot', 'pilot', 'Pilot plan | Net Watch', 'An 8-week Net Watch pilot on the cameras City of Parramatta already has: targets, timeline, what it needs, owners and data rules.'),
         ('team', 'team', 'Team | Net Watch', 'Team 101, Business Analyst Services: the people behind Net Watch.'),
         ('roles', '', 'Four roles | Net Watch', 'The officer, contractor, customer service and manager views in Net Watch.')]
REDIRECT = "<script>(function(){var q=location.search;if(/[?&](net|lane|role|do|view|photo)=/.test(q))location.replace('app.html'+q+location.hash)})();</script>\n"
for name, cur, title, desc in PAGES:
    body = open(os.path.join(HERE, 'pages', name + '.body.html')).read()
    sp = os.path.join(HERE, 'pages', name + '.script.html')
    script = open(sp).read() if os.path.exists(sp) else ''
    html = f'''<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="https://business-analyst-services.github.io/Net-Watch/img/lackey-st-west-alert.jpg">
{REDIRECT if name == 'index' else ''}<link rel="stylesheet" href="css/site.css">
</head>
<body>
<header><div class="in">
 <a class="brand" href="./"><img src="https://careers.business-analyst.services/logo.png" alt="BAS"><span><b>Net Watch</b><small>Business Analyst Services · Team 101</small></span></a>
 {nav('', cur)}
</div></header>
<main>
{body}
</main>
{more('')}
<footer><div class="in"><span>The AI ranks. People decide.</span><span>Team 101 · WSTI Festi 2026</span></div></footer>
{script}</body>
</html>
'''
    open(os.path.join(DOCS, name + '.html'), 'w').write(html)
print('wrote', [p[0] for p in PAGES])
