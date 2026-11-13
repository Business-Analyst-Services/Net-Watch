#!/usr/bin/env python3
"""Generates the GPT which GPT? static site into ./docs (GitHub Pages)."""
import os, html, shutil, json
OUT = os.path.join(os.path.dirname(__file__), 'docs')
os.makedirs(os.path.join(OUT, 'types'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'assets'), exist_ok=True)

STATES = [
 ("empty","Empty","0–15%","No action. Log the frame."),
 ("partial","Partially full","15–60%","Schedule in the next round."),
 ("full","Full","60–90%","Empty this week."),
 ("blocked","Blocked","&gt;90% / overtopping","Urgent. Raise today."),
 ("unusable","Unusable","image unreadable","Re-capture; after 3 misses send a person."),
 ("damaged","Damaged","net torn, rack bent","Raise a repair job, not a clean."),
]

TYPES = [
 dict(slug="trash-rack", place="Creek lines and culvert mouths", name="Trash rack / creek screen", short="Open-channel screens across a creek or culvert mouth",
  where="Creek lines through Northmead, Toongabbie, Darling Mills and Hunts Creek; WILLAV 050 is the camera reference frame.",
  how="Vertical bars or mesh across the flow hold back floating litter and large organics. Material builds up on the upstream face until the screen chokes and water backs up or spills around the ends.",
  looks=["Empty: bars visible top to bottom, bed visible between them.","Partial: a band of leaves and bottles along the base, bars still clear above.","Full: debris mat stacked two or three layers, bars hidden in the lower half.","Blocked: mound over the top rail, ponded brown water upstream, starved channel downstream.","Damaged: bars bent, panel sections missing, mat pushed through."],
  cue="Fraction of bar length still visible, texture of the upstream face, waterline difference upstream vs downstream.",
  sensors=[
   ("Trail camera (existing)","Primary","Swift Enduro, 4G, 1920×1440 frames with overlay strip. Already installed at the creek sites on the SCADA wall.","$0 marginal · solar/battery · 4G"),
   ("Upstream/downstream level pair","Strong second signal","Two ultrasonic or pressure level sensors; head loss across the screen rises as it blocks, and it works at night and in fog when the camera is unusable.","~$1.5–3k per site · battery/solar · LoRaWAN or 4G"),
   ("Rain gauge / BoM feed","Context","Tipping-bucket gauge on site or Council's SCADA gauges; first-flush events drive the load.","shared"),
   ("Tilt or strain on panel","Damage only","Detects a bent or displaced panel after a storm.","~$300 · battery · LoRaWAN"),
  ],
  rule="Score from camera; if camera unusable use the level differential; blocked = differential above threshold OR vision ≥ blocked with confidence ≥ 0.8.",
  tickets=["What counts as full?","Can a zero-shot model separate empty / full / blocked on Council frames?","Which rainfall feed do we trust?"]),
 dict(slug="litter-net", place="Pipe outlets into creeks and the river", name="Litter net / sock on a pipe outlet", short="A mesh bag hung on the end of a stormwater pipe",
  where="Pipe outlets into creeks and the river: Lackey St East and West, Bettington Rd, James Ruse Dr, Sturt St on the camera wall.",
  how="Flow carries litter into a net clamped to the outlet; the net swells and sags as it fills. Nets tear on sharp debris and high flows, and a torn net passes everything.",
  looks=["Empty: net hangs slack and translucent, pipe mouth visible through it.","Partial: lower third swollen with leaves and packaging.","Full: net taut and rounded, sagging to the ground, pipe mouth hidden.","Blocked: material backing up inside the pipe, water ponding at the mouth.","Damaged: net torn open, frame off its clamps, bag lying on the rocks (Lackey St West, 13 Nov 2026)."],
  cue="Net silhouette area and sag angle, visibility of the pipe mouth, straight edges where mesh has torn.",
  sensors=[
   ("Trail camera (existing)","Primary","Same cameras as the racks; the net silhouette is a strong visual cue.","$0 marginal"),
   ("Load cell on the net hanger","Strong second signal","Weight of the net rises with contents; a sudden drop to near zero means it has torn or fallen.","~$600–1,200 · battery · LoRaWAN"),
   ("Tilt sensor on frame","Damage","Frame knocked off the outlet by flow or vandalism.","~$300"),
   ("Pipe water-level sensor","Blocked","Level inside the pipe upstream of the net rises when the net chokes.","~$800 · battery · LoRaWAN"),
  ],
  rule="Score from camera; weight trend confirms; weight drop &gt; 80% in one reading with no clean recorded = damaged.",
  tickets=["What counts as full?","Can we read the overlay strip reliably?","Agree pilot terms with Council"]),
 dict(slug="underground-unit", place="Road-side and car-park catchments", name="Underground unit (CDS, vortex, Cleansall)", short="A below-ground chamber that spins litter and sediment out of the flow",
  where="Road-side and car-park catchments: CBD trunk drains, Granville and Rydalmere industrial outlets. No camera today; the only view is the manhole lid.",
  how="Flow enters a cylindrical chamber, spins, and drops gross pollutants and sediment into a sump while screened water leaves. Needs an eductor truck to empty; the sump is invisible from the street.",
  looks=["No trail-cam view. The states are measured, not seen: sump depth against the design capacity.","A chamber camera with IR can show the water surface and floating litter layer only."],
  cue="Sump sediment depth from a level sensor; floating layer from an IR chamber camera if fitted.",
  sensors=[
   ("Ultrasonic sump level","Primary","Mounted under the lid, measures distance to the sediment/litter surface; fullness = 1 − depth/design depth. Standard in the UK and US for these units.","~$1.5–2.5k · battery · LoRaWAN/4G; confined-space install"),
   ("Float or tilt switch","Cheap fallback","Trips at a set level; binary full/not full.","~$200"),
   ("Upstream/downstream level","Bypass detection","When the unit bypasses in high flow, treated and untreated levels converge.","~$2k"),
   ("Chamber IR camera","Optional","Shows oil sheen and floating litter; limited value for sediment depth.","~$1k · needs power"),
   ("Eductor truck weighbridge ticket","After the clean","The mass removed per clean calibrates the level sensor.","$0, from the contractor invoice"),
  ],
  rule="Fullness from level sensor; blocked if level exceeds 90% or bypass detected; the camera classes do not apply; schedule by predicted fill rate × forecast.",
  tickets=["What is the minimum labelled set?","What does a OneCouncil work order need?","Where does it run?"]),
 dict(slug="pit-basket", place="Kerb inlets in town centres", name="Pit basket / insert", short="A lift-out basket under a street grate",
  where="Kerb inlets in town centres and shopping strips: Epping, Harris Park, station shops.",
  how="Catches litter at the kerb before it reaches the pipe. Small, cheap, numerous, emptied by hand or small vacuum unit. Each one is low value; the fleet is not.",
  looks=["Empty: mesh floor visible through the grate.","Partial: leaves and cups across the floor.","Full: basket heaped to the grate, overflow bypass in use.","Blocked: grate itself covered, ponding on the road.","Damaged: basket missing, handle broken, mesh split."],
  cue="Grate-level photo from a phone or a lid camera; the grate pattern gives a fixed reference for fill depth.",
  sensors=[
   ("Phone photo at inspection","Primary","Officer or sweeper crew photographs through the grate; the model scores it. No hardware.","$0"),
   ("Lid-mounted IR camera","Only for hot spots","Fast-food strips and bus stops that fill weekly.","~$400 · battery"),
   ("Tilt/float on basket","Rarely worth it","Fleet-wide hardware is dearer than the cleaning it saves.","~$150"),
  ],
  rule="Batch scoring of crew photos; schedule by land-use class (fast food strip vs residential) and season; no per-basket hardware unless a hot spot.",
  tickets=["What do we demo at Festi, and what do we only describe?","What counts as full?"]),
 dict(slug="boom", place="Weir pool, Lake Parramatta, open water", name="Floating boom / weir pool", short="A floating barrier that corrals litter on open water",
  where="Parramatta River weir pool in the CBD, Lake Parramatta, Charles St and Willmott Ave on the camera wall.",
  how="A skirted boom holds floating litter and oil in a corner of the pool for a skimmer or crew. Wind and tide move the raft; the 2024/25 weir-pool drain removed 430 t of sediment.",
  looks=["Empty: clear water inside the boom line.","Partial: a thin raft along the boom.","Full: raft covers the enclosed area, debris pushing under the skirt.","Blocked: boom submerged or detached, raft escaping.","Damaged: boom sections parted, anchor line slack."],
  cue="Raft area as a share of the enclosed water, boom line continuity, colour and sheen for oil.",
  sensors=[
   ("Wide-angle camera (existing)","Primary","The weir and lake cameras already look across the pool.","$0 marginal"),
   ("Wind and tide feed","Context","Raft position depends on them; use BoM wind and the river gauge.","shared"),
   ("GPS/tilt on boom","Damage","Boom drift or submersion.","~$500 · solar · 4G"),
   ("Oil sheen sensor","Spill","Hydrocarbon detection for industrial catchments.","~$3–5k · power"),
  ],
  rule="Score raft area from camera; damaged if boom line broken; raise a skimmer job rather than an eductor clean.",
  tickets=["How does rainfall change the recommendation?","How is confidence shown, and when does the model abstain?"]),
]

CSS = """
:root{--bg:#f5f3ee;--paper:#fff;--fg:#14232e;--muted:#5c6b74;--line:#d8d3c8;--navy:#0f2f52;--teal:#126a6a;--gold:#c98a1c;--gold-soft:#fff1d6;--green:#2f8a58;--chip:#ece8df;--display:"IBM Plex Sans",system-ui,sans-serif;--mono:"IBM Plex Mono",ui-monospace,monospace}
@media (prefers-color-scheme:dark){:root{--bg:#0f2f52;--paper:#143a5f;--fg:#f3f1ea;--muted:#bfd6e2;--line:#2a4f73;--navy:#0b2440;--teal:#9fd8d0;--gold:#ffb547;--gold-soft:#3a3214;--green:#6fc48f;--chip:#1d4670;color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--display);line-height:1.5;padding:0 16px 40px}
a{color:var(--teal)}.wrap{max-width:1120px;margin:0 auto}
nav{display:flex;flex-wrap:wrap;gap:6px 18px;align-items:center;padding:14px 0;border-bottom:1px solid var(--line);font-family:var(--mono);font-size:.8rem}
nav a{text-decoration:none;color:var(--fg)}nav a.brand{font-weight:600;color:var(--gold)}nav a.cur{text-decoration:underline;text-underline-offset:4px}
h1{font-size:2rem;line-height:1.15;margin:28px 0 6px;text-wrap:balance}h2{font-family:var(--mono);font-size:.78rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:30px 0 10px;font-weight:500}
.lede{color:var(--muted);max-width:70ch;margin:0 0 18px;font-size:1.05rem}
.eyebrow{font-family:var(--mono);font-size:.76rem;letter-spacing:.08em;text-transform:uppercase;color:var(--teal)}
.gate{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}
.gate a{display:grid;gap:6px;background:var(--paper);border:1px solid var(--line);border-top:4px solid var(--gold);padding:16px;text-decoration:none;color:var(--fg)}
.gate a:hover{border-color:var(--teal)}.gate b{font-size:1.05rem}.gate span{color:var(--muted);font-size:.9rem}.gate small{font-family:var(--mono);font-size:.72rem;color:var(--teal)}
.states{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px}
.st{background:var(--paper);border:1px solid var(--line);padding:10px 12px;border-left:5px solid var(--line)}
.st.empty{border-left-color:#6fc48f}.st.partial{border-left-color:#ffb547}.st.full{border-left-color:#f08a5a}.st.blocked{border-left-color:#dc4646}.st.unusable{border-left-color:#8fb3c4}.st.damaged{border-left-color:#c9a3e8}
.st b{display:block}.st i{font-style:normal;font-family:var(--mono);font-size:.74rem;color:var(--muted);display:block}.st span{font-size:.86rem}
.panel{background:var(--paper);border:1px solid var(--line);padding:16px 18px}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
table{border-collapse:collapse;width:100%;font-size:.9rem}th,td{text-align:left;padding:8px 8px;border-top:1px solid var(--line);vertical-align:top}th{font-family:var(--mono);font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:500;border-top:0}
td.role{font-family:var(--mono);font-size:.76rem;color:var(--teal);white-space:nowrap}td.cost{font-family:var(--mono);font-size:.76rem;color:var(--muted)}
.tbl{overflow-x:auto}ul{padding-left:18px;margin:0}li{margin-bottom:4px}
.rule{background:var(--gold-soft);border-left:5px solid var(--gold);padding:10px 14px;font-size:.95rem}
.chips{display:flex;flex-wrap:wrap;gap:6px}.chips span{background:var(--chip);font-family:var(--mono);font-size:.74rem;padding:3px 9px}
img.fig{max-width:100%;border:1px solid var(--line);display:block}
footer{margin-top:40px;font-family:var(--mono);font-size:.74rem;color:var(--muted);line-height:1.6;max-width:100ch}
.matrix td.y{color:var(--green);font-weight:600}.matrix td.n{color:var(--muted)}
"""

def page(title, body, cur, depth=0):
    root = '../' if depth else ''
    links = [('index.html','Home'),('index.html#types','GPT types'),('sensors.html','Sensor matrix'),('plan.html','Build plan'),('evidence.html','Evidence')]
    nav = ''.join(f'<a href="{root}{h}"{" class=cur" if cur==h.split("#")[0] else ""}>{t}</a>' for h,t in links)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · GPT which GPT?</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CSS}</style></head><body><div class="wrap">
<nav><a class="brand" href="{root}index.html">GPT which GPT?</a>{nav}</nav>
{body}
<footer>GPT which GPT? is a Business Analyst Services entry for the WSTI Festi 2026 Build with AI challenge (City Challenge track, Challenge 5: AI for Smarter Asset and Environmental Management). Council facts cite City of Parramatta public records: Asset Management Plan 2027–2036, Annual Report 2024/25 Appendix 1, GIPA Contracts Register 30 Sep 2026, Smart City &amp; Innovation Strategy 2024–2033. Sensor costs are indicative 2026 ranges, not quotes. Camera frames are City of Parramatta SCADA trail-camera images used with the Festi brief.</footer>
</div></body></html>"""

# ---------- index ----------
gates = ''.join(f'<a href="types/{t["slug"]}.html"><small>{t["place"]}</small><b>{t["name"]}</b><span>{t["short"]}</span><span style="font-family:var(--mono);font-size:.74rem;color:var(--teal)">Primary sensor: {t["sensors"][0][0]}</span></a>' for t in TYPES)
states = ''.join(f'<div class="st {k}"><b>{n}</b><i>{r}</i><span>{a}</span></div>' for k,n,r,a in STATES)
index = f"""
<div class="eyebrow">City of Parramatta · 40 GPTs · 13 other pollution control devices · 23 camera sites</div>
<h1>Which trap needs the truck this week?</h1>
<p class="lede">Council cleans its gross pollutant traps quarterly and after big rain, whether they need it or not. The cameras already exist. GPT which GPT? reads every frame, scores each trap's fullness with a confidence, adds the rain forecast, and drafts a work order an officer approves in one click. Start with the type of trap: each one fills differently, shows it differently, and wants a different sensor.</p>
<h2 id="types">Choose a trap type</h2>
<div class="gate">{gates}</div>
<h2>The six states every type is scored into</h2>
<div class="states">{states}</div>
<p style="color:var(--muted);font-size:.9rem;margin-top:10px">Thresholds are the starting schema; the open ticket "What counts as full?" sets them per type with Council's stormwater team. <a href="assets/gpt-fullness-states.png">See simulated examples of the first five states</a> built from two Council frames.</p>
<div class="two" style="margin-top:28px">
<div class="panel"><h2 style="margin-top:0">Today</h2><p>Quarterly rounds plus storm callouts, run by Urban Asset Solutions under Part A of ITT 22/2023 on a schedule of rates. Fullness is judged with the lid off. No per-trap record exists between cleans. Estimated cost ≈ $420k a year, of which $60–120k is visits to traps that were nearly empty.</p><p><a href="assets/gpt-clean-process.png">The end-to-end process, as reconstructed</a> · <a href="assets/gpt-cost-estimate.png">The cost estimate</a></p></div>
<div class="panel"><h2 style="margin-top:0">With GPT which GPT?</h2><p>Every camera frame scored daily. A ranked morning list instead of a grid of thumbnails. Officer approves, defers or sends someone to look. Work order lands in OneCouncil with the frame attached; fullness at clean is recorded, so the Asset Management Plan's "emptied at optimum frequencies" finally has data behind it.</p><p><a href="plan.html">The build plan (Wayfinder map)</a></p></div>
</div>
"""
open(os.path.join(OUT,'index.html'),'w').write(page('Home', index, 'index.html'))

# ---------- type pages ----------
for t in TYPES:
    looks = ''.join(f'<li>{l}</li>' for l in t['looks'])
    sens = ''.join(f'<tr><td><b>{s[0]}</b><br><span style="font-size:.86rem;color:var(--muted)">{s[2]}</span></td><td class="role">{s[1]}</td><td class="cost">{s[3]}</td></tr>' for s in t['sensors'])
    chips = ''.join(f'<span>{c}</span>' for c in t['tickets'])
    others = ''.join(f'<a href="{o["slug"]}.html"><b>{o["name"]}</b><span>{o["short"]}</span></a>' for o in TYPES if o is not t)
    body = f"""
<div class="eyebrow">GPT type</div>
<h1>{t['name']}</h1>
<p class="lede">{t['short']}. {t['where']}</p>
<div class="two">
<div class="panel"><h2 style="margin-top:0">How it fills</h2><p>{t['how']}</p><h2>What the camera sees</h2><ul>{looks}</ul><p style="font-size:.9rem;color:var(--muted)"><b>Vision cue:</b> {t['cue']}</p></div>
<div class="panel"><h2 style="margin-top:0">Sensors for this type</h2><div class="tbl"><table><tr><th>Sensor</th><th>Role</th><th>Indicative cost · power · comms</th></tr>{sens}</table></div></div>
</div>
<h2>Decision rule</h2>
<div class="rule">{t['rule']}</div>
<h2>Open Wayfinder tickets that touch this type</h2>
<div class="chips">{chips}</div>
<p style="font-size:.9rem;color:var(--muted)">See the <a href="../plan.html">build plan</a> for how these are settled.</p>
<h2>Other trap types</h2>
<div class="gate">{others}</div>
"""
    open(os.path.join(OUT,'types',t['slug']+'.html'),'w').write(page(t['name'], body, '', depth=1))

# ---------- sensor matrix ----------
SENS = ["Trail camera (existing)","Level sensor (ultrasonic/pressure)","Up/down level pair","Load cell","Tilt / float switch","Rain / wind / tide feed","Phone photo at inspection","Weighbridge ticket"]
MAT = {
 "trash-rack":      ["Primary","–","Strong second","–","Damage","Context","Backup","Calibrates"],
 "litter-net":      ["Primary","Blocked (in pipe)","–","Strong second","Damage","Context","Backup","Calibrates"],
 "underground-unit":["– (no view)","Primary","Bypass","–","Cheap fallback","Context","–","Calibrates"],
 "pit-basket":      ["Hot spots only","–","–","–","Rarely","Context","Primary","–"],
 "boom":            ["Primary","–","–","–","Damage (GPS/tilt)","Context (wind, tide)","Backup","–"],
}
rows=''.join('<tr><td><a href="types/%s.html">%s</a></td>'%(t['slug'],t['name'])+''.join(f'<td class="{"y" if v not in ("–","– (no view)") else "n"}">{v}</td>' for v in MAT[t['slug']])+'</tr>' for t in TYPES)
matrix=f"""
<div class="eyebrow">Sensing strategy</div>
<h1>One model, five trap types, the cheapest sensor that answers the question</h1>
<p class="lede">The camera is the primary sensor wherever there is a line of sight, because Council already owns 23 of them. Underground units have no view, so they get a level sensor instead. Everything else is a second signal for the hours the camera can't see (night, fog, lens water) or for damage the camera can't judge.</p>
<div class="tbl matrix"><table><tr><th>Trap type</th>{''.join(f'<th>{s}</th>' for s in SENS)}</tr>{rows}</table></div>
<h2>Principles behind the matrix</h2>
<div class="two">
<div class="panel"><ul>
<li><b>Vision first, hardware second.</b> The CSIRO trial already proved 4G trail cameras work and LoRaWAN did not at these sites. Add hardware only where the camera is blind.</li>
<li><b>Two independent signals before "urgent".</b> A blocked call that triggers a same-day truck should come from the camera and a physical sensor, or from the camera at high confidence twice.</li>
<li><b>The weighbridge ticket is a sensor.</b> Mass removed per clean, already on the contractor invoice, calibrates every other reading against reality.</li>
</ul></div>
<div class="panel"><ul>
<li><b>Night is "unusable", not "empty".</b> IR frames are scored by a separate head or routed to the level sensor; a dark frame never counts as a clean trap.</li>
<li><b>Damage is its own state.</b> A torn net scores as empty to a naive model. Load drop, tilt and torn-edge detection catch it and raise a repair job under Part G, not a clean under Part A.</li>
<li><b>Fleet economics.</b> 13 pit baskets at $150 of hardware each is cheaper than one eductor visit, but not cheaper than a crew photo. Spend per trap in proportion to its cleaning cost.</li>
</ul></div>
</div>
"""
open(os.path.join(OUT,'sensors.html'),'w').write(page('Sensor matrix', matrix, 'sensors.html'))

# ---------- plan (wayfinder) ----------
wf=open('/tmp/claude-0/-home-claude/981d7120-64b3-57a1-b6b3-7424906ca6b8/scratchpad/wayfinder.html').read()
# strip title/meta/font link, keep style + body
import re
style=re.search(r'<style>(.*?)</style>',wf,re.S).group(1)
inner=wf.split('</style>',1)[1]
style=style.replace('body{background:var(--bg);color:var(--fg);font-family:var(--display);line-height:1.5;\n  padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:28px}','')
plan=f"""<style>{style}.wrap .wrap{{padding:0;max-width:none}}</style>
<div class="eyebrow" style="margin-top:24px">Build plan</div>
<h1 style="margin-top:4px">How this gets built</h1>
<p class="lede">Planned with the <a href="https://www.aihero.dev/skills-wayfinder">Wayfinder</a> method: the destination is fixed, the route is a map of decisions, each a ticket with a question for a title. The frontier is what can be worked on now. <a href="assets/GPT-which-GPT-wayfinder-map.pdf">One-page PDF</a>.</p>
{inner}
"""
open(os.path.join(OUT,'plan.html'),'w').write(page('Build plan', plan, 'plan.html'))

# ---------- evidence ----------
ev="""
<div class="eyebrow">Evidence</div>
<h1>What we know about Parramatta's traps, and where it came from</h1>
<div class="two">
<div class="panel"><h2 style="margin-top:0">Council's camera wall</h2><p>The SCADA "GPT Cameras" page shows 14 live trail-camera feeds (Lackey St West and East, Lake Parra Res, Forest Cl, James Ruse Dr 1 and 2, Shirley St, Bettington Rd, Ridge St, Anthony St, Norwood Ave, Sturt St, Willmott Ave, Charles St) and nine named sites awaiting cameras (21 Short St, 11 and 12 Parra Park West/East, 26 Beecroft Ave, 27 Stanley Rd North, 17 Pemberton St, 24 McDonald St, 19 Harris St, 52 Cowells Lane, 23 Mason Rd, 30 Stanley Rd South).</p><img class="fig" src="assets/current_cameras_GPT.png" alt="SCADA GPT Cameras page"></div>
<div class="panel"><h2 style="margin-top:0">A damaged net, seen but not acted on</h2><p>Lackey St West, 13 Nov 2026 11:05, 24 °C. The litter net has torn and collapsed onto the rocks. A human sees it at a glance; nobody is looking at 23 feeds four times a day. This frame is why "damaged" is a sixth state.</p><img class="fig" src="assets/current_cameras_GPT_example_broken_net.png" alt="Lackey St West frame showing a torn litter net"></div>
</div>
<h2>Visuals from the research</h2>
<div class="gate">
<a href="assets/gpt-fullness-states.png"><b>Fullness states, simulated</b><span>Five states on two Council frames</span></a>
<a href="assets/gpt-clean-process.png"><b>How a clean happens today</b><span>Swimlane, documented vs inferred</span></a>
<a href="assets/gpt-cost-estimate.png"><b>What cleaning costs</b><span>$230–740k/yr, three scenarios</span></a>
<a href="assets/gpt-sources-visual.png"><b>Who fills a trap</b><span>Land use to pollutant to trap</span></a>
</div>
<h2>Public records used</h2>
<ul>
<li>City of Parramatta, Asset Management Plan 2027–2036: 40 GPTs, 13 pollution control devices, 2 swales; service measure "emptied at optimum frequencies".</li>
<li>Annual Report 2024/25, Appendix 1: traps "cleaned quarterly and following significant rain events"; contracts list shows ITT 22/2023 parts as schedule of rates.</li>
<li>GIPA Contracts Register, 30 Sep 2026: Urban Asset Solutions holds Part A Pollution Control Assets, 1 Jul 2024 – 30 Jun 2027.</li>
<li>Smart City &amp; Innovation Strategy 2024–2033 and the Council AI Plan motion (NOM26-2, Feb 2026).</li>
<li>Smarter, Cleaner Sydney Harbour trial (CSIRO, 2022–24): 4G trail cameras worked, LoRaWAN did not; ~1% of frames contained litter.</li>
<li>Council GPT page: about 104 tonnes removed from the traps each year.</li>
</ul>
"""
open(os.path.join(OUT,'evidence.html'),'w').write(page('Evidence', ev, 'evidence.html'))

# ---------- assets ----------
for f in ['gpt-fullness-states.png','gpt-clean-process.png','gpt-cost-estimate.png','gpt-sources-visual.png','current_cameras_GPT.png','current_cameras_GPT_example_broken_net.png','GPT-which-GPT-wayfinder-map.pdf','gpt-which-gpt-banner-festi.png']:
    shutil.copy(os.path.join('/home/claude',f), os.path.join(OUT,'assets',f))
open(os.path.join(OUT,'.nojekyll'),'w').write('')
print('built', os.listdir(OUT))
