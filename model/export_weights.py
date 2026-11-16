#!/usr/bin/env python3
"""Train the baseline on all 18 frames and export weights for the in-browser "Check a photo" tool.
Same features and augmentation as baseline.py. Writes docs/data/model-weights.js (window.MODELW).
The honest accuracy figure stays the leave-one-camera-out test in baseline.py, not this model."""
import json, os, runpy, contextlib, io
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(os.path.join(HERE, 'baseline.py'))
feats, augment, meta, imgs = g['feats'], g['augment'], g['meta'], g['imgs']
X, y = [], []
for m in meta:
    for a in augment(imgs[m['id']], m['label']):
        X.append(feats(a)); y.append(m['label'])
clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.5)).fit(np.array(X), np.array(y))
sc, lr = clf.named_steps['standardscaler'], clf.named_steps['logisticregression']
out = dict(classes=[str(c) for c in lr.classes_], mean=sc.mean_.round(6).tolist(), scale=sc.scale_.round(6).tolist(),
           coef=lr.coef_.round(6).tolist(), intercept=lr.intercept_.round(6).tolist(), abstain=0.5,
           trained_on=len(meta), train_images=len(X),
           trained_ids=[m['id'] for m in meta])
open(os.path.join(ROOT, 'docs', 'data', 'model-weights.js'), 'w').write('window.MODELW=' + json.dumps(out) + ';')
ref = {m['id']: dict(feats=[round(float(v), 6) for v in feats(imgs[m['id']])],
       probs=dict(zip(lr.classes_, clf.predict_proba([feats(imgs[m['id']])])[0].round(4).tolist()))) for m in meta}
json.dump(ref, open(os.path.join(HERE, 'weights-ref.json'), 'w'))  # parity check for the JS port
print('classes', out['classes'], 'features', len(out['mean']), 'images', len(X))
