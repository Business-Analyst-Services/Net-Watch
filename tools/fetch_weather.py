#!/usr/bin/env python3
"""Refresh docs/data/weather.json and weather.js for Net Watch.

Run by a scheduled GitHub Action (the browser can't call these services directly).
- Gauges: City of Parramatta FloodSmart water level and rain gauges, from the public Lizard API.
- Forecast: hourly rain for the next 72 hours from Open-Meteo (CC BY 4.0) at points across the LGA.
Standard library only. Usage: python3 tools/fetch_weather.py <output folder>
"""
import json, os, re, sys, urllib.request, datetime as dt

OUT = sys.argv[1] if len(sys.argv) > 1 else 'docs/data'
LIZ = 'https://parramatta.lizard.net/api/v4/'
NOW = dt.datetime.now(dt.timezone.utc)
UA = {'Accept': 'application/json', 'User-Agent': 'net-watch-demo (WSTI Festi 2026)'}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.load(r)

def all_timeseries():
    url, out = LIZ + 'timeseries/?page_size=100', []
    while url:
        j = get(url); out += j['results']; url = j.get('next')
    return out

def gauges():
    recent = (NOW - dt.timedelta(days=2)).isoformat()
    loc_cache, out = {}, {}
    for t in all_timeseries():
        ot = (t.get('observation_type') or {}).get('code', '')
        if not t.get('end') or t['end'] < recent or not t.get('location'): continue
        if not (ot.startswith('Waterlevel') or ot == 'PRCP'): continue
        if 'Prediction' in (t.get('name') or ''): continue
        lu = t['location']['url']
        if lu not in loc_cache: loc_cache[lu] = get(lu)
        geom = (loc_cache[lu].get('geometry') or {}).get('coordinates')
        if not geom: continue
        raw = t['location']['name']
        name = re.sub(r'\s*\[.*?\]\s*', '', raw).replace(' Warning Area', '').strip()
        m = re.search(r'\[([\d.]+) mAHD\]', raw)
        start = (NOW - dt.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
        ev = get(t['url'] + f'events/?start={start}&page_size=2000')['results']
        vals = [e['value'] for e in ev if e.get('value') is not None]
        kind = 'rain' if ot == 'PRCP' else 'level'
        g = out.setdefault((kind, name), dict(name=name, kind=kind, lat=round(geom[1], 4), lon=round(geom[0], 4)))
        if kind == 'rain':
            g.update(rain_24h=round(sum(vals), 1), unit='mm', time=t['end'])
        else:
            if t.get('last_value') is None: continue
            g.update(level=round(t['last_value'], 2), unit='m AHD', time=t['end'],
                     change_24h=round(vals[-1] - vals[0], 2) if len(vals) > 1 else None)
            if m:
                zero = float(m.group(1)); g['zero'] = zero
                if abs(g['level'] - zero) < 5: g['above_zero'] = round(g['level'] - zero, 2)
                else: g['flag'] = f'Gauge zero in the name ({zero}) does not match the reading; excluded from depth'
    return list(out.values())

POINTS = [(-33.775, 150.95), (-33.775, 151.00), (-33.775, 151.05), (-33.805, 150.95),
          (-33.805, 151.00), (-33.805, 151.05), (-33.835, 150.98), (-33.835, 151.03)]

def forecast():
    lat = ','.join(str(p[0]) for p in POINTS); lon = ','.join(str(p[1]) for p in POINTS)
    j = get('https://api.open-meteo.com/v1/forecast?latitude=' + lat + '&longitude=' + lon +
            '&hourly=precipitation&forecast_hours=72&timezone=Australia%2FSydney')
    j = j if isinstance(j, list) else [j]
    return dict(source='Open-Meteo, CC BY 4.0', time=j[0]['hourly']['time'],
                points=[dict(lat=p['latitude'], lon=p['longitude'], mm=[x or 0 for x in p['hourly']['precipitation']]) for p in j])

data = dict(source='City of Parramatta FloodSmart gauges via the public Lizard API (parramatta.lizard.net)',
            retrieved=NOW.strftime('%Y-%m-%dT%H:%M:%SZ'), mode='live', gauges=[], forecast=None)
try: data['gauges'] = gauges()
except Exception as e: data['gauge_error'] = str(e)[:200]
try: data['forecast'] = forecast()
except Exception as e: data['forecast_error'] = str(e)[:200]
if not data['gauges']:  # keep the previous file's gauges rather than publish an empty map
    try: data['gauges'] = json.load(open(os.path.join(OUT, 'weather.json')))['gauges']; data['mode'] = 'stale gauges'
    except Exception: pass
os.makedirs(OUT, exist_ok=True)
json.dump(data, open(os.path.join(OUT, 'weather.json'), 'w'), indent=1)
open(os.path.join(OUT, 'weather.js'), 'w').write('window.WEATHER=' + json.dumps(data) + ';')
print(len(data['gauges']), 'gauges;', 'forecast' if data['forecast'] else 'no forecast')
