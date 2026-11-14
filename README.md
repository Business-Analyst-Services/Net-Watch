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

**Live site:** https://business-analyst-services.github.io/gpt-which-gpt/

## Build and deploy

`python3 build.py` regenerates `docs/` from the data in `build.py` (the plan page is built from `wayfinder.html`).
`./deploy.sh` rebuilds, pushes `main`, and publishes `docs/` to the `gh-pages` branch, which GitHub Pages serves.
