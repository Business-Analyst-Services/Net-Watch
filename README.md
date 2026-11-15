# GPT which GPT?

Entry for the WSTI Festi 2026 "Build with AI" Innovation Challenge (City Challenge track, Challenge 5: AI for Smarter Asset and Environmental Management) by Team 101 (Business Analyst Services).

A computer-vision decision assistant that reads City of Parramatta's gross pollutant trap (GPT) camera frames, scores fullness with a confidence, adds rainfall, and drafts work orders a Council officer approves.

The live site is organised by GPT type, because each type fills differently, shows it differently and wants a different sensor:

- **GPT** (purple): end-of-pipe net or basket, the MVP focus
- **Trash Rack** (blue): steel rack across a waterway
- **pGPT** (green): trap in a road-side pit
- **uGPT** (yellow): underground wet vault
- **Boom** (black): floating boom across deep waterway

Codes and colours are Council's, from the December 2022 GPT Audit.

Plus a sensor matrix, the Wayfinder build plan and the evidence base.

**Landing page:** https://business-analyst-services.github.io/gpt-which-gpt/
**App:** https://business-analyst-services.github.io/gpt-which-gpt/app.html (Net Watch)
**Brief:** https://business-analyst-services.github.io/gpt-which-gpt/brief/

## Build and deploy

`python3 build.py` regenerates `docs/` from the data in `build.py` (the plan page is built from `wayfinder.html`).
`./deploy.sh` rebuilds, pushes `main`, and publishes `docs/` to the `gh-pages` branch, which GitHub Pages serves.

## Model check

`python3 model/baseline.py` reruns the baseline net-state classifier on the labelled frames in `docs/img/frames/` (labels in `model/frames.json`) and writes `docs/data/model-results.js`. Leave-one-camera-out over 8 Council frames; simulated frames are training only. Small demonstration, not production accuracy.
