#!/usr/bin/env python3
"""Generates the GPT which GPT? static site into ./docs (GitHub Pages).

Content sources: Council SME breakout session (Dr Paul Hackney, 9 Nov 2026), the team's
Proactive GPT Monitoring brief (Zoe), City of Parramatta public records, and the SCADA
GPT Cameras page screenshots (13 Nov 2026).
"""
import re, os, html, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'docs', 'brief')
os.makedirs(os.path.join(OUT, 'types'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'assets'), exist_ok=True)

STATES = [
 ("empty","Empty","0–40%","No action. Log the frame."),
 ("partial","Filling","40–70%","Watch. Re-score after the next rain."),
 ("full","Clean due","70–80%","Email: clean before the next storm."),
 ("blocked","Overdue","&gt;80% or overtopping","Email: urgent. A full net detaches in the next surge."),
 ("unusable","Can't see","leaves, fog, dark, offline","Email after 2 days: restore the view."),
 ("damaged","Damaged / detached","torn mesh, off the pipe","Email: repair job, not a clean."),
]

# Council asset codes and map colours from the Dec 2022 GPT Audit (Council minutes, 25 Mar 2024).
TYPES = [
 dict(slug="net", code="GPT", colour="#7b4fc9", colname="Purple", focus=True,
  name="End-of-pipe net or basket", short="A steel-cable net clamped to the end of a stormwater pipe, just before the creek",
  place="Pipe outlets in creek bushland",
  where="Most of Council's camera sites: Lackey St East and West, Bettington Rd, James Ruse Dr, Sturt St, Norwood Ave and others on the SCADA wall.",
  how="Rain washes litter down the pipe into the net. The net swells and sags as it fills. Nets are designed to detach from the pipe when full and hit by another surge, through a weak link, so the net doesn't tear the outlet apart. That is the whole problem: once a net is full, the next storm sends it and its contents into the creek. Council wants to intervene at 70–80% full.",
  looks=["Empty: net hangs slack, pipe mouth visible through the mesh.","Filling: lower third swollen with leaves and packaging.","Clean due: net taut and rounded, sagging toward the ground.","Overdue: net at full stretch, pipe mouth hidden, material backing into the pipe.","Damaged / detached: mesh torn, or net pulled off the top of the pipe (Lackey St West, 13 Nov 2026; Paul's example in the SME session).","Can't see: leaves or a branch across the lens, fog, IR night frame."],
  cue="Change in the net itself, not the scene. Paul's warning: dense leafy frames, and about 90% of days nothing changes. Score against the trap's own last clean frame, not a generic 'full' image.",
  sensors=[
   ("Existing trail camera","Primary","About 15 installed, about 10 working; one photo a day into SCADA, 1–3 years of history. AI scores fill %, damage, detachment and can't-see.","$0 marginal · solar · 4G"),
   ("Fullness sensor (ToF, ultrasonic or radar) on a bracket over the net","For nets with no camera","CSIRO/Matter 4G dry-sump fullness sensor: 17 units trialled, within 2% of manual checks. Low bandwidth, so it works where 4G is too weak for images.","low-cost · battery · 4G/LTE-M"),
   ("Tilt or strain on the net frame","Detachment","A detached net is the one event that must never be missed; a tilt switch confirms it when the camera can't see.","~$300 · battery"),
   ("BoM 12-hour forecast + FloodSmart gauges","Trigger","Council's 25 SCADA rain and level gauges and the Nelen &amp; Schuurmans forecast already exist. Used to ask: is there room in this net for the next storm?","shared, already in SCADA"),
  ],
  rule="Email when fill ≥ 70% <b>and</b> the 12-hour forecast exceeds the rain this net has historically needed to fill the remainder; email at once for damaged or detached; email after 2 days of can't-see. Expected volume: one email a week or fortnight.",
  tickets=["What counts as full?","Can a zero-shot model separate empty / full / blocked on Council frames?","Which rainfall feed do we trust?","Get a frame export from Council"]),
 dict(slug="trash-rack", code="Trash Rack", colour="#2f6fd6", colname="Blue", focus=False,
  name="Trash rack across a waterway", short="A fixed steel rack across a channel; debris piles against it",
  place="Open channels and culvert mouths",
  where="Fewer sites than nets; one is on the SCADA camera wall (Paul showed it in the SME session, mostly leaves).",
  how="Water comes over the top and debris piles against the bars. Here the risk is hydraulic as much as volume: a choked rack backs water up and floods upstream.",
  looks=["Empty: bars visible top to bottom.","Filling: a band of leaves along the base.","Clean due: debris mat over the lower half.","Overdue: mound over the top rail, ponded water upstream.","Damaged: bars bent or missing.","Can't see: vegetation across the view."],
  cue="Share of bar height still visible; water level difference upstream vs downstream.",
  sensors=[
   ("Existing camera with AI debris coverage","Primary","AquaWatch AW-108 does this at the edge on an ACT trash rack, with an API to work orders.","$0 marginal (existing)"),
   ("Upstream / downstream level pair (radar)","Blockage and flood risk","HiLo LS1-R radar level sends email, SMS, API or SCADA. Head loss across the rack rises as it blocks, day or night.","~$1.5–3k per pair · battery · 4G"),
   ("Rain forecast","Trigger","As for nets.","shared"),
  ],
  rule="Email when debris coverage is high <b>or</b> head loss passes threshold with rain forecast. Blockage and flood risk matter more than volume.",
  tickets=["How does rainfall change the recommendation?","How is confidence shown, and when does the model abstain?"]),
 dict(slug="pit", code="pGPT", colour="#2f9a4a", colname="Green", focus=False,
  name="Trap in a road-side pit", short="A basket or insert inside a kerbside drainage pit",
  place="Kerb inlets in streets and centres",
  where="Road-side pits across the LGA; no cameras today.",
  how="Catches litter at the kerb. Small and numerous. A level sensor sees water rising in the pit, which flags a blockage but not how much litter is in the basket.",
  looks=["No camera view. Fullness is inferred: an abnormal rise in pit level after modest rain points to a blocked basket."],
  cue="Rate of level rise against rainfall, compared with the same pit's history.",
  sensors=[
   ("Radar or ultrasonic pit level","Primary","Exceed M.Scan and HiLo LS1-R offer pit debris, blockage and surge alerts in Australia.","~$800–2k · battery · LoRaWAN/4G"),
   ("Crew phone photo at inspection","Ground truth","Contractor photographs through the grate; the same vision model scores it.","$0"),
   ("Rain forecast","Trigger","As for nets.","shared"),
  ],
  rule="Email an inspect-and-clear when pit level rises faster than this pit's normal response to the rain that fell. Level is not litter fullness, so the email says 'inspect', not 'full'.",
  tickets=["What is the minimum labelled set?","What does a OneCouncil work order need?"]),
 dict(slug="vault", code="uGPT", colour="#e0b020", colname="Yellow", focus=False,
  name="Underground wet vault", short="A below-ground chamber with standing water; litter can be submerged",
  place="Under roads and car parks",
  where="Large units; Paul: 'really, really big', one truck per load or more. No sensors at Council today. The earlier CSIRO trial instrumented one underground GPT at Parramatta, separate from the net cameras.",
  how="Flow enters a vault that always holds water. Floating litter, submerged litter and sediment all collect. Nothing on the surface tells you how full it is, and a level sensor reads the water, not the litter.",
  looks=["No view. Treated as a risk score, not a fullness reading."],
  cue="None from vision. Risk from rainfall since last clean, the tonnes removed at past cleans, and catchment land use.",
  sensors=[
   ("Rainfall + cleaning history model","Primary","Learn each vault's fill rate from mm of rain since the last clean and the mass removed each time. StormHarvester does this for sewers from level, flow and rainfall.","software only"),
   ("Hydraulic level in and out","Secondary","Detects bypass during storms (treated and untreated levels converge).","~$2k · power/4G"),
   ("Periodic inspection or specialist sonar","Ground truth","Submerged litter remains a sensing gap; say so.","per visit"),
  ],
  rule="Email an inspection recommendation when predicted fill passes 70% or the vault bypassed in the last storm. Never claim a measured fullness.",
  tickets=["Where does it run?","Agree pilot terms with Council"]),
 dict(slug="boom", code="Boom", colour="#222222", colname="Black", focus=False,
  name="Floating boom across deep waterway", short="A floating barrier that corrals surface litter",
  place="River, weir pool and lake",
  where="Parramatta River and Lake Parramatta; Charles St and Willmott Ave look across open water on the camera wall.",
  how="A skirted boom holds floating litter in one corner for a skimmer. Wind and tide move the raft. There is no container, so no simple fullness percentage.",
  looks=["Clear: open water inside the boom line.","Raft forming: a thin band along the boom.","Clean due: raft covers most of the enclosed water.","Damaged: boom parted or anchor slack, raft escaping."],
  cue="Raft area as a share of the enclosed water; continuity of the boom line.",
  sensors=[
   ("Existing wide-angle camera","Primary","Raft area from the frame.","$0 marginal"),
   ("Wind and river level","Context","BoM wind and the SCADA river gauge explain where the raft sits.","shared"),
   ("GPS or tilt on the boom","Damage","Boom drift or parting.","~$500 · solar · 4G"),
  ],
  rule="Email a skimmer job when raft area passes threshold; email a repair when the boom line breaks.",
  tickets=["How does rainfall change the recommendation?"]),
]

CSS = """
:root{--bg:#fff;--paper:#fff;--fg:#1F3A5F;--muted:#5A6B7D;--line:#DDE3EA;--navy:#1F3A5F;--deep:#14284A;--soft:#3E6189;--teal:#1D6E6E;--teal-b:#4DB8B8;--teal-tint:#CDEDED;--orange:#F5A04A;--alt:#F4F6F8;--gold:#A8580A;--gold-soft:#FDEBD6;--green:#2E7D50;--red:#C2352B;--chip:#F4F6F8;--display:Arial,Helvetica,"Liberation Sans",sans-serif;--mono:Arial,Helvetica,"Liberation Sans",sans-serif}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--display);line-height:1.5;padding:0 16px 40px}
a{color:var(--teal)}.wrap{max-width:1120px;margin:0 auto}
nav{display:flex;flex-wrap:wrap;gap:6px 18px;align-items:center;padding:14px 0;border-bottom:1px solid var(--line);font-family:var(--mono);font-size:.8rem}
nav a{text-decoration:none;color:var(--fg)}nav a.brand{font-weight:600;color:var(--gold)}nav a.cur{text-decoration:underline;text-underline-offset:4px}
h1{font-size:2rem;line-height:1.15;margin:28px 0 6px;text-wrap:balance}h2{font-family:var(--mono);font-size:.78rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:30px 0 10px;font-weight:500}
.lede{color:var(--muted);max-width:72ch;margin:0 0 18px;font-size:1.05rem}
.eyebrow{font-family:var(--mono);font-size:.76rem;letter-spacing:.08em;text-transform:uppercase;color:var(--teal)}
.gate{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px}
.gate a{display:grid;gap:6px;align-content:start;background:var(--paper);border:1px solid var(--line);border-top:6px solid var(--c,var(--gold));padding:16px;text-decoration:none;color:var(--fg)}
.gate a:hover{border-color:var(--teal);border-top-color:var(--c,var(--gold))}.gate b{font-size:1.05rem;line-height:1.25}.gate span{color:var(--muted);font-size:.9rem}.gate small{font-family:var(--mono);font-size:.72rem;color:var(--muted)}
.gate a.focus{grid-column:span 2;background:var(--gold-soft)}@media (max-width:640px){.gate a.focus{grid-column:auto}}
.code{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:.74rem;font-weight:500}.code i{width:11px;height:11px;border-radius:50%;background:var(--c)}
.flag{font-family:var(--mono);font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;color:var(--gold);font-weight:600}
.states{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px}
.st{background:var(--paper);border:1px solid var(--line);padding:10px 12px;border-left:5px solid var(--line)}
.st.empty{border-left-color:#6fc48f}.st.partial{border-left-color:#ffb547}.st.full{border-left-color:#f08a5a}.st.blocked{border-left-color:#dc4646}.st.unusable{border-left-color:#8fb3c4}.st.damaged{border-left-color:#c9a3e8}
.st b{display:block}.st i{font-style:normal;font-family:var(--mono);font-size:.74rem;color:var(--muted);display:block}.st span{font-size:.86rem}
.panel{background:var(--paper);border:1px solid var(--line);padding:16px 18px;min-width:0}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
.three{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}
table{border-collapse:collapse;width:100%;font-size:.9rem}th,td{text-align:left;padding:8px 8px;border-top:1px solid var(--line);vertical-align:top}th{font-family:var(--mono);font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:500;border-top:0}
td.role{font-family:var(--mono);font-size:.76rem;color:var(--teal)}td.cost{font-family:var(--mono);font-size:.76rem;color:var(--muted)}td.num{font-family:var(--mono);text-align:right;white-space:nowrap}
.tbl{overflow-x:auto}ul{padding-left:18px;margin:0}li{margin-bottom:4px}
.rule{background:var(--gold-soft);border-left:5px solid var(--gold);padding:10px 14px;font-size:.95rem}
.chips{display:flex;flex-wrap:wrap;gap:6px}.chips span{background:var(--chip);font-family:var(--mono);font-size:.74rem;padding:3px 9px}
img.fig{max-width:100%;border:1px solid var(--line);display:block}
.cap{font-size:.82rem;color:var(--muted);margin-top:6px}
footer{margin-top:40px;font-family:var(--mono);font-size:.74rem;color:var(--muted);line-height:1.6;max-width:100ch}
.matrix td.y{color:var(--green);font-weight:600}.matrix td.n{color:var(--muted)}
.quote{border-left:3px solid var(--teal);padding:4px 0 4px 14px;color:var(--fg);font-size:.98rem;max-width:70ch}
.quote small{display:block;color:var(--muted);font-family:var(--mono);font-size:.72rem;margin-top:4px}
.scn{background:var(--paper);border:1px solid var(--line);padding:14px 16px;display:grid;gap:6px;align-content:start}
.scn .n{font-family:var(--mono);color:var(--gold);font-size:.8rem}.scn b{font-size:1.02rem}.scn span{font-size:.88rem;color:var(--muted)}
.bar{height:10px;background:var(--chip);position:relative}.bar i{position:absolute;inset:0 auto 0 0;background:var(--gold)}
/* email mock */
.mail{background:var(--paper);border:1px solid var(--line);max-width:760px;font-size:.95rem}
.mail .hd{padding:12px 18px;border-bottom:1px solid var(--line);display:grid;gap:2px;font-size:.86rem;color:var(--muted)}
.mail .hd b{color:var(--fg);font-size:1.05rem}
.mail .bd{padding:16px 18px;display:grid;gap:12px}
.mail .pill{display:inline-block;font-family:var(--mono);font-size:.72rem;padding:2px 8px;border-radius:3px;color:#fff;background:var(--red)}
.mail .why{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;font-size:.88rem}.mail .why dt{color:var(--muted);font-family:var(--mono);font-size:.76rem;padding-top:2px}.mail .why dd{margin:0}
.mail .acts{display:flex;flex-wrap:wrap;gap:8px}.mail .acts span{border:1px solid var(--teal);color:var(--teal);padding:7px 12px;font-weight:600;font-size:.86rem}.mail .acts span.pri{background:var(--teal);color:var(--paper)}
.figwrap{position:relative;max-width:640px}.figwrap svg{position:absolute;inset:0;width:100%;height:100%}

/* ---- BAS site frame ---- */
body{padding:0;font-size:16px;line-height:1.6}
a{color:var(--navy)}
.in{max-width:1120px;margin:0 auto;padding-inline:max(20px,env(safe-area-inset-left))}
header.site{padding-block:18px;border-bottom:1px solid var(--line)}
header.site .in{display:flex;align-items:center;justify-content:space-between;gap:12px 20px;flex-wrap:wrap}
.brandl{display:flex;align-items:center;gap:12px;text-decoration:none;color:var(--navy)}
.brandl img{width:44px;height:44px}.brandl b{display:block;font-size:15px}.brandl small{display:block;font-size:9px;letter-spacing:.25em;color:var(--muted);text-transform:uppercase}
nav.sitenav{display:flex;gap:6px 18px;flex-wrap:wrap;padding:0;border:0;font:700 13px var(--display)}
nav.sitenav a{text-decoration:none;color:var(--navy);padding-bottom:3px}nav.sitenav a.cur{border-bottom:2px solid var(--teal-b)}
.hero{background:var(--navy);color:#fff;position:relative;overflow:hidden}
.hero .in{padding-block:52px}
.hero .bars{position:absolute;right:0;bottom:0;display:flex;align-items:flex-end;gap:14px;opacity:.3;pointer-events:none}.hero .bars i{display:block;width:24px;background:var(--soft)}
.hero .eyebrow{color:var(--teal-b)}
.eyebrow{display:flex;align-items:center;gap:12px;font:700 11px var(--display);letter-spacing:.3em;text-transform:uppercase;color:var(--teal)}
.eyebrow::before{content:"";width:28px;height:2px;background:var(--teal-b);flex:none}
.hero h1{font-size:clamp(32px,4.6vw,48px);line-height:1.1;font-weight:400;margin:16px 0 14px;max-width:24ch;position:relative}
.hero h1 b{font-weight:700}
.hero .lede{color:#fff;opacity:.9;font-weight:400;font-size:17px;max-width:64ch;margin:0;position:relative}
.hero .lede a{color:#fff}
.hero .code{color:#fff}
main.in{padding-block:40px 24px}
h2{font:700 24px/1.2 var(--display);letter-spacing:0;text-transform:none;color:var(--navy);margin:44px 0 16px;display:flex;align-items:center;gap:12px}
h2::before{content:"";width:28px;height:3px;background:var(--teal-b);flex:none}
.panel h2{font-size:20px}
.panel,.scn,.st,.gate a{border-color:var(--line)}
.gate a{border-top-width:5px}.gate a.focus{background:var(--alt)}
th{font:700 10.5px var(--display);letter-spacing:.2em;color:var(--muted);background:var(--alt)}
.rule{background:var(--alt);border-left-color:var(--orange)}
.quote{border-left-color:var(--teal-b)}
.tablewrap{overflow-x:auto;border:1px solid var(--line)}
table.cat{width:100%;min-width:720px;border-collapse:collapse;font-size:15px;background:#fff}
table.cat th,table.cat td{text-align:left;padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:top}
table.cat tr:last-child td{border-bottom:0}
table.cat td:first-child{white-space:nowrap;font-weight:700}
.mk{display:inline-block;width:12px;height:12px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);background:var(--c);margin-right:10px;vertical-align:-1px}
.credit{font-size:12px;color:var(--muted);line-height:1.6;max-width:110ch;margin:24px auto 0;padding-bottom:24px}
footer.band{margin:0;background:var(--teal-b);color:#fff;font:700 10px var(--display);letter-spacing:.25em;text-transform:uppercase;max-width:none}
footer.band .in{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;padding-block:16px}
footer.band a{color:#fff;text-decoration:none;margin-left:16px}
"""

ROOTVARS = ':root{--bg:#fff;--paper:#fff;--fg:#1F3A5F;--muted:#5A6B7D;--line:#DDE3EA;--navy:#1F3A5F;--teal:#1D6E6E;--gold:#A8580A;--gold-soft:#FDEBD6;--green:#2E7D50;--green-soft:#E3F1E8;--chip:#F4F6F8;--display:Arial,Helvetica,"Liberation Sans",sans-serif;--mono:Arial,Helvetica,"Liberation Sans",sans-serif}body{background:#fff;padding:0}section.hero{display:block}footer.band{max-width:none;font:700 10px Arial,Helvetica,sans-serif;color:#fff}'

def split_h1(t):
    if '<' in t: return t
    for sep in (', ', '; '):
        if sep in t:
            a,b=t.rsplit(sep,1); return f'{a}{sep.strip()} <b>{b}</b>'
    w=t.split()
    if len(w)<=3: return f'<b>{t}</b>'
    k=max(2,len(w)//2); return ' '.join(w[:-k])+' <b>'+' '.join(w[-k:])+'</b>'

def page(title, body, cur, depth=0):
    root = '../' if depth else ''
    site = root + '../'
    links = [('index.html','Brief'),('mvp.html','MVP'),('alert.html','Sample alert'),('sensors.html','Sensor matrix'),('plan.html','Build plan'),('evidence.html','Evidence')]
    nav = ''.join(f'<a href="{root}{h}"{" class=cur" if cur==h else ""}>{t}</a>' for h,t in links)
    lead_style = ''
    m = re.match(r'\s*(<style>.*?</style>)', body, re.S)
    if m: lead_style, body = m.group(1), body[m.end():]
    m = re.match(r'\s*(<div[^>]*>.*?</div>)\s*<h1[^>]*>(.*?)</h1>\s*(<p class="lede">.*?</p>)?', body, re.S)
    hero = ''
    if m:
        eb = m.group(1)
        if 'class="eyebrow"' not in eb and 'class=eyebrow' not in eb: eb = eb.replace('<div', '<div class="eyebrow-chip"', 1)
        hero = f'{eb}<h1>{split_h1(m.group(2))}</h1>{m.group(3) or ""}'
        body = body[m.end():]
    bars = '<div class="bars" aria-hidden="true"><i style="height:50px"></i><i style="height:110px"></i><i style="height:80px"></i><i style="height:190px"></i><i style="height:260px"></i><i style="height:140px"></i></div>'
    return f"""<!doctype html><html lang="en-AU"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} | Net Watch brief</title>
<style>{CSS}</style>{lead_style}{"<style>"+ROOTVARS+"</style>" if lead_style else ""}</head><body>
<header class="site"><div class="in"><a class="brandl" href="{site}"><img src="https://careers.business-analyst.services/logo.png" alt="BAS"><span><b>Net Watch</b><small>Business Analyst Services · Team 101</small></span></a>
<nav class="sitenav" aria-label="Brief">{nav}<a href="{site}app.html">Open the app</a></nav></div></header>
<section class="hero">{bars}<div class="in">{hero}</div></section>
<main class="in">
{body}
</main>
<div class="in"><p class="credit">GPT which GPT? (Net Watch) is a Team 101 entry for the WSTI Festi 2026 Build with AI challenge, City Challenge track, Parramatta Possibilities Challenge 5 (AI for Smarter Asset and Environmental Management). Operating facts come from the Council SME breakout session with Dr Paul Hackney (9 Nov 2026) and City of Parramatta public records: GPT Audit (Council minutes 25 Mar 2024), Asset Management Plan 2027–2036, Annual Report 2024/25. Sensor costs are indicative, not quotes. Vendor names are examples from public sources, not endorsements. Camera frames are Council SCADA images shared for the challenge.</p></div>
<footer class="band"><div class="in"><span>Human at every gate</span><span><a href="{site}">About</a><a href="{site}app.html">App</a><a href="{site}email.html">Email alerts</a><a href="https://business-analyst.services/">BAS</a></span></div></footer>
</body></html>"""

def code_chip(t):
    return f'<span class="code" style="--c:{t["colour"]}"><i></i>{t["colname"]} · {t["code"]}</span>'

# ---------- index ----------
gates = ''.join(
  f'<a href="types/{t["slug"]}.html" class="{"focus" if t["focus"] else ""}" style="--c:{t["colour"]}">'
  f'{"<span class=flag>MVP focus · Council asked for nets first</span>" if t["focus"] else ""}'
  f'{code_chip(t)}<b>{t["name"]}</b><span>{t["short"]}</span><small>Primary signal: {t["sensors"][0][0]}</small></a>' for t in TYPES)
states = ''.join(f'<div class="st {k}"><b>{n}</b><i>{r}</i><span>{a}</span></div>' for k,n,r,a in STATES)
index = f"""
<div class="eyebrow">City of Parramatta · about 35–40 GPTs · about 15 cameras, 10 working · one photo a day</div>
<h1>Clean the net before the storm, not after it lets go</h1>
<p class="lede">Council's litter nets are built to break away from the pipe when they are full and the next surge hits. Today one officer looks at the camera images for about 15 minutes each weekday; nobody looks on weekends or over Christmas, and that officer is on leave until mid-January. GPT which GPT? reads every image, scores how full each net is, checks the rain forecast, and emails an officer with the marked-up photo when a net needs cleaning or repair. The officer approves; the work order follows.</p>
<h2 id="types">Start with the trap type</h2>
<p style="margin:-4px 0 12px;color:var(--muted);font-size:.92rem">Council's own asset codes and map colours from the 2022 GPT Audit. Each type fills differently and needs a different sensor; the decision and email layer is the same for all of them.</p>
<div class="gate">{gates}</div>
<h2 id="categories">Council's five asset categories</h2>
<p style="margin:-4px 0 14px;color:var(--muted);font-size:.95rem;max-width:80ch">Official public definitions from the December 2022 GPT Audit, published in 2023 and reproduced in the March 2024 Council minutes. Verify against the current 2026 asset register.</p>
<figure class="panel" style="margin:0 0 16px"><img class="fig" src="assets/gpt-types-concept.jpg" alt="Illustrative concept of the five GPT types: yellow underground wet vault, purple end-of-pipe net, green road-side pit trap, black floating boom, blue trash rack"><figcaption class="cap">Illustrative concept, not actual Council assets.</figcaption></figure>
<div class="tablewrap"><table class="cat">
<thead><tr><th>Map marker</th><th>Council code</th><th>Official definition</th><th>What it physically means</th><th>Important limitation</th></tr></thead>
<tbody>
<tr><td><span class="mk" style="--c:#e0b020"></span>Yellow</td><td><b>uGPT</b></td><td>Underground wet vault</td><td>Standing water; captured material may be submerged.</td><td>Not directly comparable with a dry container.</td></tr>
<tr><td><span class="mk" style="--c:#7b4fc9"></span>Purple</td><td><b>GPT</b></td><td>End-of-pipe net or basket</td><td>Outlet net or basket; exposure and geometry vary by site.</td><td>Not a label for every proprietary GPT.</td></tr>
<tr><td><span class="mk" style="--c:#2f9a4a"></span>Green</td><td><b>pGPT</b></td><td>Trap in road-side pit</td><td>Pit insert or basket within a roadside drainage pit.</td><td>The code alone does not prove a dry sump.</td></tr>
<tr><td><span class="mk" style="--c:#222222"></span>Black</td><td><b>Boom</b></td><td>Floating boom across deep waterway</td><td>Floating barrier concentrating surface litter.</td><td>No simple container-style fullness percentage.</td></tr>
<tr><td><span class="mk" style="--c:#2f6fd6"></span>Blue</td><td><b>Trash Rack</b></td><td>Steel rack across waterway</td><td>Fixed rack; debris may restrict upstream flow.</td><td>Blockage and hydraulic risk matter, not only volume.</td></tr>
</tbody></table></div>
<p style="color:var(--muted);font-size:.9rem;margin-top:10px">Map colours encode <b>asset type</b>, not condition or replacement priority. The 2024 minutes say a rectification-category map had not been developed.</p>
<h2>The six states a net is scored into</h2>
<div class="states">{states}</div>
<p style="color:var(--muted);font-size:.9rem;margin-top:10px">Council's target is to intervene at 70–80% full. The thresholds are a starting point for the open question "What counts as full?". <a href="assets/gpt-fullness-states.png">Simulated examples</a> built from two Council frames.</p>
<div class="two" style="margin-top:28px">
<div class="panel"><h2 style="margin-top:0">Today</h2><ul>
<li>Camera nets: one person reviews the day's photos, weekdays only. The judgement lives in that person's head.</li>
<li>Everything else: cleaned about every three months, after a big storm, or from experience ("that one fills after 20 mm, that one after 90 mm").</li>
<li>Some nets are cleaned half empty; some have already overflowed or detached.</li>
</ul><p><a href="assets/gpt-clean-process.png">Process as reconstructed</a> · <a href="assets/gpt-cost-estimate.png">Cost estimate</a></p></div>
<div class="panel"><h2 style="margin-top:0">With GPT which GPT?</h2><ul>
<li>Every image scored the day it arrives, weekends and holidays included.</li>
<li>Rain-aware trigger: clean when the net can't hold the next forecast storm.</li>
<li>One email with the photo, an arrow on the problem, the reason and the confidence. About one a week across the network.</li>
<li>Officer approves, defers or asks for an inspection. The outcome is recorded, so each net's fill behaviour is learned over time.</li>
</ul><p><a href="alert.html">See a sample alert</a> · <a href="mvp.html">What we are demoing</a></p></div>
</div>
"""
open(os.path.join(OUT,'index.html'),'w').write(page('Home', index, 'index.html'))

# ---------- type pages ----------
for t in TYPES:
    looks = ''.join(f'<li>{l}</li>' for l in t['looks'])
    sens = ''.join(f'<tr><td><b>{s[0]}</b><br><span style="font-size:.86rem;color:var(--muted)">{s[2]}</span></td><td class="role">{s[1]}</td><td class="cost">{s[3]}</td></tr>' for s in t['sensors'])
    chips = ''.join(f'<span>{c}</span>' for c in t['tickets'])
    others = ''.join(f'<a href="{o["slug"]}.html" style="--c:{o["colour"]}">{code_chip(o)}<b>{o["name"]}</b></a>' for o in TYPES if o is not t)
    focus = '<p class="flag" style="margin:6px 0 0">MVP focus. Paul Hackney, SME session: "If you wanted to target one type of system, concentrate on the nets."</p>' if t['focus'] else '<p style="margin:6px 0 0;font-size:.9rem;color:var(--muted)">Outside the MVP. Shown so the solution map covers every Council GPT type.</p>'
    body = f"""
<div style="margin-top:24px">{code_chip(t)}</div>
<h1 style="margin-top:8px">{t['name']}</h1>
<p class="lede">{t['short']}. {t['where']}</p>
{focus}
<div class="two" style="margin-top:18px">
<div class="panel"><h2 style="margin-top:0">How it fills</h2><p>{t['how']}</p><h2>What the evidence shows in each state</h2><ul>{looks}</ul><p style="font-size:.9rem;color:var(--muted)"><b>Signal to read:</b> {t['cue']}</p></div>
<div class="panel"><h2 style="margin-top:0">Sensors for this type</h2><div class="tbl"><table><tr><th>Sensor</th><th>Role</th><th>Cost · power · comms</th></tr>{sens}</table></div></div>
</div>
<h2>When to email the officer</h2>
<div class="rule">{t['rule']}</div>
<h2>Open questions that touch this type</h2>
<div class="chips">{chips}</div>
<p style="font-size:.9rem;color:var(--muted)">How these get settled: <a href="../plan.html">build plan</a>.</p>
<h2>Other trap types</h2>
<div class="gate">{others}</div>
"""
    open(os.path.join(OUT,'types',t['slug']+'.html'),'w').write(page(t['name'], body, '', depth=1))

# ---------- MVP ----------
mvp = """
<div class="eyebrow">What we are demoing</div>
<h1>One net, one storm, one email, one decision</h1>
<p class="lede">A small flow that works end to end beats a broad platform that doesn't. Council said synthetic or sample data is fine and no cost-benefit analysis is needed; the judges score a working prototype and a credible path forward.</p>
<h2>Three demo scenarios</h2>
<div class="three">
<div class="scn"><div class="n">01 · CAMERA</div><b>Net 75% full, heavy rain forecast</b><span>Annotated image, confidence and reason; email says clean before the storm. Officer approves; work order drafted.</span></div>
<div class="scn"><div class="n">02 · DAMAGE</div><b>Net torn or off the pipe</b><span>Lackey St West, 13 Nov 2026. Email says repair, not clean, with an arrow on the tear.</span></div>
<div class="scn"><div class="n">03 · DATA QUALITY</div><b>Camera can't see, or a sensor is offline</b><span>Two days of obstructed frames raise a restore-the-view email. Never report a false "empty".</span></div>
</div>
<h2>What is in and what is out</h2>
<div class="two">
<div class="panel"><h2 style="margin-top:0">In</h2><ul><li>Nets, with the other four types shown as a solution map</li><li>Real Council frames plus synthetic ones, with a simulated fullness sensor feed for nets without cameras</li><li>Rain-aware trigger from the BoM forecast</li><li>Email with evidence, and officer approval</li><li>Outcome recorded, so each net's fill behaviour can be learned</li></ul></div>
<div class="panel"><h2 style="margin-top:0">Out</h2><ul><li>Production-grade model training and accuracy claims</li><li>Live integration with SCADA or OneCouncil</li><li>Sending contractors out automatically</li><li>Solving every GPT type</li><li>Cost-benefit analysis (Council said not required)</li></ul></div>
</div>
<h2>How the judges score it, and where this entry answers</h2>
<div class="tbl"><table>
<tr><th>Criterion</th><th style="text-align:right">Weight</th><th>Our answer</th></tr>
<tr><td>Problem understanding and community impact</td><td class="num">25%</td><td>Detach-when-full is the real risk; weekend and holiday gap; one person's knowledge. Less litter reaching creeks, assets protected, staff time saved.</td></tr>
<tr><td>Working prototype and feasibility</td><td class="num">25%</td><td>Three scenarios run end to end on Council frames; uses cameras and SCADA Council already has.</td></tr>
<tr><td>Path forward and implementation potential</td><td class="num">25%</td><td>Pilot on the ~10 working cameras; add low-bandwidth fullness sensors to nets without cameras; then the other types.</td></tr>
<tr><td>Innovation and creativity</td><td class="num">15%</td><td>Rain-aware "is there room for the next storm" trigger; each net learns its own fill rate.</td></tr>
<tr><td>Pitch and presentation</td><td class="num">10%</td><td>Show the torn Lackey St net that nobody saw, then the email that would have caught it.</td></tr>
</table></div>
<p class="cap">Weights from the WSTI Festi judging slide; for City Challenges, community impact includes alignment to Council priorities, community outcomes and implementation potential. Two finalists per city challenge; the jury picks winners at Pitch Night.</p>
<h2>Success measures</h2>
<div class="chips"><span>Damaged or detached nets missed: zero</span><span>Lead time before forecast rain</span><span>False alerts per week</span><span>Weekend and holiday coverage</span><span>Manual review cut to exceptions</span><span>Alert-to-action time</span><span>Cleans avoided on half-empty nets</span></div>
<p class="cap">Scenarios and measures follow the team's alignment brief (<a href="assets/Proactive_GPT_Monitoring_Solution.pdf">PDF</a>).</p>
"""
open(os.path.join(OUT,'mvp.html'),'w').write(page('MVP', mvp, 'mvp.html'))

# ---------- sample alert ----------
alert = """
<div class="eyebrow">Sample alert · the officer's view</div>
<h1>What lands in the inbox</h1>
<p class="lede">Council officers asked for email, not another dashboard to watch, with the image and something pointing at the problem. This is the damage scenario built from the real Lackey St West frame.</p>
<div class="mail">
 <div class="hd"><span>From: GPT Monitor &lt;gpt-monitor@&hellip;&gt; · To: Stormwater officer on duty</span><b>Lackey St West net is torn: repair before Tuesday's rain</b><span>Sat 14 Nov 2026, 07:30 · Camera LACKEST 009 · Asset code GPT (end-of-pipe net)</span></div>
 <div class="bd">
  <div><span class="pill">DAMAGED · confidence 0.86</span></div>
  <div class="figwrap"><img class="fig" src="assets/lackey-st-west-2026-11-13.jpg" alt="Lackey St West camera frame showing the litter net torn and sagging off the pipe outlet">
   <svg viewBox="0 0 100 75" preserveAspectRatio="none" aria-hidden="true"><ellipse cx="57" cy="52" rx="10" ry="13" fill="none" stroke="#ff3b3b" stroke-width=".8"/><line x1="84" y1="22" x2="67.5" y2="40" stroke="#ff3b3b" stroke-width="1"/><polygon points="66.6,41.6 66.4,37.6 69.9,39.6" fill="#ff3b3b"/><text x="85" y="20" fill="#ff3b3b" font-size="4" font-family="IBM Plex Mono,monospace" text-anchor="middle">torn</text></svg></div>
  <dl class="why">
   <dt>What</dt><dd>Net has torn and is hanging off the pipe outlet. Material is spilling onto the rocks.</dd>
   <dt>Since</dt><dd>First seen 13 Nov 11:05. The 12 Nov frame showed an intact net about 40% full.</dd>
   <dt>Rain</dt><dd>BoM forecast 24–38 mm Tue 17 Nov. A torn net passes everything in that storm.</dd>
   <dt>Suggest</dt><dd>Repair (not a clean) this week. Add to the next contractor run.</dd>
   <dt>History</dt><dd>Last cleaned 21 Aug. Lackey St was listed for replacement in the 2022 GPT Audit.</dd>
  </dl>
  <div class="acts"><span class="pri">Approve repair work order</span><span>Defer a week</span><span>Send someone to inspect</span><span>Open live view</span></div>
  <p class="cap" style="margin:0">Your choice is recorded with this frame so the model learns from it. No work order is raised until you approve.</p>
 </div>
</div>
<p class="cap" style="max-width:760px">Illustrative. The frame is real (Council SCADA, 13 Nov 2026); the confidence, forecast, dates of earlier frames and last-clean date are example values for the demo.</p>
"""
open(os.path.join(OUT,'alert.html'),'w').write(page('Sample alert', alert, 'alert.html'))

# ---------- sensor matrix ----------
SENS = ["Existing camera","Fullness sensor (ToF / ultrasonic / radar)","Water level (radar)","Up/down level pair","Tilt / strain","Rain forecast + gauges","Cleaning history model","Crew photo"]
MAT = {
 "net":       ["Primary","No-camera nets","–","–","Detachment","Trigger","Learns fill rate","Ground truth"],
 "trash-rack":["Primary","–","–","Blockage","–","Trigger","Learns fill rate","Ground truth"],
 "pit":       ["–","–","Primary","–","–","Trigger","Normal response","Ground truth"],
 "vault":     ["–","–","Bypass","–","–","Trigger","Primary","Ground truth"],
 "boom":      ["Primary","–","–","–","Damage (GPS)","Context (wind)","–","–"],
}
rows=''.join(f'<tr><td>{code_chip(t)}<br><a href="types/{t["slug"]}.html">{t["name"]}</a></td>'+''.join(f'<td class="{"n" if v=="–" else "y"}">{v}</td>' for v in MAT[t['slug']])+'</tr>' for t in TYPES)
matrix=f"""
<div class="eyebrow">Layered sensing</div>
<h1>Pick the sensor by trap type; keep one decision and email layer</h1>
<p class="lede">One sensing method won't fit every asset. Cameras work where there is a clear line of sight and enough 4G to send an image. Where there isn't, a low-bandwidth fullness or level sensor sends a number instead. Everything feeds the same rule: is there room for the next storm?</p>
<div class="tbl matrix"><table><tr><th>Trap type</th>{''.join(f'<th>{s}</th>' for s in SENS)}</tr>{rows}</table></div>
<h2>Principles</h2>
<div class="two">
<div class="panel"><ul>
<li><b>Use what Council has first.</b> About 15 cameras and 25 FloodSmart rain and level gauges already feed SCADA.</li>
<li><b>Bandwidth decides the sensor.</b> Paul's team flagged weak 4G at some nets. A fullness sensor sends a few bytes; an image sends hundreds of kilobytes.</li>
<li><b>A detached net must never be missed.</b> Back the camera with a tilt switch where the view is unreliable.</li>
</ul></div>
<div class="panel"><ul>
<li><b>"Can't see" is a state, not "empty".</b> Leaves, fog and night frames raise their own email.</li>
<li><b>Level is not litter.</b> Pit and vault sensors trigger "inspect", never "full".</li>
<li><b>Every clean is a data point.</b> Mass removed and date, joined to rainfall, teaches each trap's fill rate (Paul: "60 mm took it from 10% to 50%").</li>
</ul></div>
</div>
<h2>Examples on the market</h2>
<div class="tbl"><table><tr><th>Solution</th><th>Fits</th><th>Watch-out</th></tr>
<tr><td>Matter / CSIRO</td><td>4G dry-sump fullness for nets and baskets; 17 sensors within 2% of manual checks</td><td>Not for submerged litter</td></tr>
<tr><td>AquaWatch AW-108</td><td>Edge AI debris, water level and flood risk on an ACT trash rack; API to work orders</td><td>Needs camera view, power, comms</td></tr>
<tr><td>HiLo LS1-R</td><td>Radar level; email, SMS, API or SCADA</td><td>Level, not litter</td></tr>
<tr><td>Exceed M.Scan</td><td>Pit debris, blockage and surge alerts</td><td>Confirm GPT references</td></tr>
<tr><td>SGS + Rocla</td><td>Commercial multi-sensor GPT monitoring</td><td>Little public validation</td></tr>
<tr><td>StormHarvester</td><td>Sensor-agnostic AI on level, flow, rainfall</td><td>Sewer-focused; no GPT hardware</td></tr>
</table></div>
<p class="cap">From the team's alignment brief, public sources. Not endorsements.</p>
"""
open(os.path.join(OUT,'sensors.html'),'w').write(page('Sensor matrix', matrix, 'sensors.html'))

# ---------- plan (wayfinder) ----------
wf=open(os.path.join(HERE,'wayfinder.html')).read()
style=re.search(r'<style>(.*?)</style>',wf,re.S).group(1)
style=re.sub(r'body\{background:var\(--bg\);color:var\(--fg\);font-family:var\(--display\);line-height:1\.5;\s*padding-left[^}]*\}','',style)
inner=wf.split('</style>',1)[1]
plan=f"""<style>{style}.wrap .wrap{{padding:0;max-width:none}}</style>
<div class="eyebrow" style="margin-top:24px">Build plan</div>
<h1 style="margin-top:4px">How this gets built</h1>
<p class="lede">Planned with the <a href="https://www.aihero.dev/skills-wayfinder">Wayfinder</a> method: the destination is fixed, the route is a map of decisions, each a ticket phrased as a question. The frontier is what can be worked on now. <a href="assets/GPT-which-GPT-wayfinder-map.pdf">One-page PDF</a>.</p>
{inner}
"""
open(os.path.join(OUT,'plan.html'),'w').write(page('Build plan', plan, 'plan.html'))

# ---------- evidence ----------
ev="""
<div class="eyebrow">Evidence</div>
<h1>What we know, and where it came from</h1>
<h2>From Council's SME session (Dr Paul Hackney, 9 Nov 2026)</h2>
<div class="two">
<div class="panel"><ul>
<li>About 35–40 GPTs. About 15 have cameras; about 10 work; a repair run is planned.</li>
<li>One photo a day into SCADA, cameras in place 1–3 years. About 90% of days nothing changes.</li>
<li>One officer reviews the photos for about 15 minutes a day. No weekend or holiday cover. That officer is on leave until mid-January.</li>
<li>GPTs without cameras: cleaned about every three months, after big storms, or from experience of each trap's rainfall threshold.</li>
<li>Contractors clean and repair. Underground units need a truck per load; nets are small.</li>
</ul></div>
<div class="panel"><ul>
<li>Nets detach by design when full and hit by another surge. Intervene at 70–80%.</li>
<li>Email alerts with an image and an arrow on the problem; officers don't want to watch a dashboard. Expect one a week or fortnight.</li>
<li>Trigger must allow for flood risk: a clean can't be arranged the day before a storm.</li>
<li>Alert when the camera can't see, so a person can restore the view.</li>
<li>Non-camera sensors welcome; 4G coverage limits image quality. Synthetic data is fine.</li>
<li>Nice to have: learn each trap's fill behaviour from rain and cleaning records; route the crew.</li>
</ul></div>
</div>
<div class="quote" style="margin-top:14px">"If we could intervene when it's say 70% or 80% full … it's good for the environment because there's less litter going into the environment … and also it saves human time."<small>Dr Paul Hackney, City of Parramatta, SME session transcript</small></div>
<h2>Council's camera wall and the net nobody saw</h2>
<div class="two">
<div class="panel"><img class="fig" src="assets/current_cameras_GPT.png" alt="SCADA GPT Cameras page with 14 camera tiles and 11 named sites without images"><p class="cap">SCADA "GPT Cameras" page: 14 camera tiles (Lackey St West and East, Lake Parra Res, Forest Cl, James Ruse Dr 1 and 2, Shirley St, Bettington Rd, Ridge St, Anthony St, Norwood Ave, Sturt St, Willmott Ave, Charles St), several fogged or obscured, and 11 named sites with no image.</p></div>
<div class="panel"><img class="fig" src="assets/lackey-st-west-2026-11-13.jpg" alt="Lackey St West frame showing a torn litter net"><p class="cap">Lackey St West, 13 Nov 2026, 11:05. Net torn and collapsed onto the rocks.</p></div>
</div>
<h2>Council's GPT categories and the 2022 audit</h2>
<div class="two">
<div class="panel"><img class="fig" src="assets/council-gpt-categories.png" alt="Table of Council GPT asset codes: uGPT, GPT, pGPT, Boom, Trash Rack"><p class="cap">Asset codes and map colours from the December 2022 GPT Audit, reproduced in Council minutes of 25 March 2024. To check against the 2026 asset register.</p></div>
<div class="panel"><img class="fig" src="assets/gpt-audit-2024-locations.png" alt="Map of GPT audit locations with lists of GPTs recommended for replacement or major work"><p class="cap">Recommended for replacement: Anthony St Carlingford, Benaud Pl Telopea, Burrabogee Rd Toongabbie, Clyde St Rydalmere, Lackey St (Lake Parra) North Parramatta, Masons Rd Oatlands, Model Farms Rd Winston Hills. Major work: Blaxland Rd Epping, Cooyong Cres Toongabbie, Lackey St (via car park), Norwood Ave Beecroft. Three of these are camera sites.</p></div>
</div>
<div class="panel" style="margin-top:16px"><img class="fig" src="assets/gpt-types-concept.jpg" alt="Illustrative concept images of the five GPT types"><p class="cap">Illustrative concept of the five types, labelled as not actual Council assets.</p></div>
<h2>Research visuals</h2>
<div class="gate">
<a href="assets/gpt-fullness-states.png"><b>Fullness states, simulated</b><span>Five states on two Council frames</span></a>
<a href="assets/gpt-clean-process.png"><b>How a clean happens today</b><span>Swimlane, documented vs inferred</span></a>
<a href="assets/gpt-cost-estimate.png"><b>What cleaning costs</b><span>Bottom-up estimate, three scenarios</span></a>
<a href="assets/gpt-sources-visual.png"><b>Who fills a trap</b><span>Land use to pollutant to trap</span></a>
</div>
<h2>Public records</h2>
<ul>
<li>Council minutes, 25 March 2024: GPT Audit asset locations and replacement priorities.</li>
<li>Asset Management Plan 2027–2036: 40 GPTs, 13 other pollution control devices; service measure "emptied at optimum frequencies".</li>
<li>Annual Report 2024/25, Appendix 1: traps "cleaned quarterly and following significant rain events".</li>
<li>GIPA Contracts Register, 30 Sep 2026: Urban Asset Solutions holds Part A, Pollution Control Assets, of the stormwater maintenance panel.</li>
<li>Smart City &amp; Innovation Strategy 2024–2033; Council AI Plan motion (Feb 2026).</li>
<li>CSIRO GPT sensors research and the Smarter, Cleaner Sydney Harbour trial: low-cost non-visual fullness sensing. Per Paul, that trial instrumented an underground GPT; the net cameras are Council's own operational installs.</li>
</ul>
"""
open(os.path.join(OUT,'evidence.html'),'w').write(page('Evidence', ev, 'evidence.html'))

# ---------- assets ----------
for f in ['gpt-fullness-states.png','gpt-clean-process.png','gpt-cost-estimate.png','gpt-sources-visual.png','current_cameras_GPT.png','current_cameras_GPT_example_broken_net.png','GPT-which-GPT-wayfinder-map.pdf','gpt-types-concept.jpg']:
    src=os.path.join('/home/claude',f)
    if os.path.exists(src): shutil.copy(src, os.path.join(OUT,'assets',f))
for old in ['gpt-which-gpt-banner-festi.png']:
    p=os.path.join(OUT,'assets',old)
    if os.path.exists(p): os.remove(p)
for old in ['underground-unit.html','pit-basket.html','litter-net.html']:
    p=os.path.join(OUT,'types',old)
    if os.path.exists(p): os.remove(p)
open(os.path.join(OUT,'.nojekyll'),'w').write('')
print('built', sorted(os.listdir(OUT)), sorted(os.listdir(os.path.join(OUT,'types'))))
