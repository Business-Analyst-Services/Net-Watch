"""One top navigation for every Net Watch page. nav(prefix, cur): prefix is the path from the page to the site root."""
ITEMS = [('home', '', 'Home'), ('app', 'app.html', 'App'), ('email', 'email.html', 'Email alerts'),
         ('brief', 'brief/', 'Brief'), ('mvp', 'brief/mvp.html', 'MVP and pilot'), ('sensors', 'brief/sensors.html', 'Sensors'),
         ('plan', 'brief/plan.html', 'Build plan'), ('evidence', 'brief/evidence.html', 'Evidence')]
def nav(prefix, cur):
    return ('<nav class="sitenav" aria-label="Main">' + ''.join(
        f'<a href="{prefix}{h}"' + (' class="cur" aria-current="page"' if k == cur else '') + f'>{t}</a>' for k, h, t in ITEMS) + '</nav>')
