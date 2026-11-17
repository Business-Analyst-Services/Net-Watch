"""Shared header menu and footer for every Net Watch page.
nav(prefix, cur) and more(prefix): prefix is the path from the page to the site root ('' , '../', '../../')."""
ITEMS = [('home', '', 'Home'), ('try', '#try', 'Try the demo'), ('pilot', 'pilot.html', 'Pilot plan'), ('team', 'team.html', 'Team')]
MORE = [('app.html', 'App'), ('email.html', 'Email alerts'), ('roles.html', 'Four roles'), ('brief/', 'Brief'),
        ('brief/sensors.html', 'Sensors'), ('brief/plan.html', 'Build plan'), ('brief/evidence.html', 'Evidence')]
def _href(prefix, h, cur):
    if h.startswith('#'):
        return h if cur == 'home' else (prefix or './') + h
    return (prefix + h) or './'
def nav(prefix, cur):
    return ('<nav class="sitenav" aria-label="Main">' + ''.join(
        f'<a href="{_href(prefix, h, cur)}"' + (' class="cur" aria-current="page"' if k == cur else '') + f'>{t}</a>' for k, h, t in ITEMS) + '</nav>')
def more(prefix):
    return ('<div class="more"><div class="in"><b>More</b>' + ''.join(f'<a href="{prefix}{h}">{t}</a>' for h, t in MORE)
            + '<a href="https://github.com/Business-Analyst-Services/Net-Watch">Code</a><a href="https://business-analyst.services/">BAS</a></div></div>')
