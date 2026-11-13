# GPT which GPT?

Entry for the WSTI Festi 2026 "Build with AI" Innovation Challenge (City Challenge track, Challenge 5: AI for Smarter Asset and Environmental Management) by Business Analyst Services.

A computer-vision decision assistant that reads City of Parramatta's gross pollutant trap (GPT) camera frames, scores fullness with a confidence, adds rainfall, and drafts work orders a Council officer approves.

The live site is organised by GPT type, because each type fills differently, shows it differently and wants a different sensor:

- Trash rack / creek screen
- Litter net / sock on a pipe outlet
- Underground unit (CDS, vortex, Cleansall)
- Pit basket / insert
- Floating boom / weir pool

Plus a sensor matrix, the Wayfinder build plan and the evidence base.

## Build

`python3 build.py` regenerates `docs/` from the data in `build.py`. GitHub Pages serves `docs/` on `main`.
