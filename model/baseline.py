#!/usr/bin/env python3
"""Baseline net-state classifier for the Net Watch demo.

Honest small-sample test, not a production model.
- Classes: empty, part_full, full, damaged, cant_see.
- Features: colour histogram (HSV), sharpness (Laplacian variance), contrast, edge density, brightness.
- Model: multinomial logistic regression on standardised features.
- Test scheme: leave-one-camera-out over the 8 Council frames. Each Council frame is predicted by a model
  trained on the simulated frames and the other Council frames, with every image from the same camera
  (including simulated frames built from it) held out. Training images are augmented; test images are not.
- Abstain: a prediction below 0.5 confidence is routed to a person as "review".
Writes model/results.json and docs/data/model-results.json.
"""
import json, os
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FR = os.path.join(ROOT, 'docs', 'img', 'frames')
CLASSES = ['empty', 'part_full', 'full', 'damaged', 'cant_see']
ABSTAIN = 0.5
rng = np.random.default_rng(7)

def feats(im):
    im = im.convert('RGB').resize((160, 120))
    hsv = np.asarray(im.convert('HSV'), dtype=np.float32) / 255.0
    h, _ = np.histogramdd(hsv.reshape(-1, 3), bins=(8, 4, 4), range=((0, 1), (0, 1), (0, 1)))
    h = (h / h.sum()).ravel()
    g = np.asarray(im.convert('L'), dtype=np.float32)
    lap = g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    sharp = np.log1p(lap.var())
    gx, gy = np.abs(np.diff(g, axis=1)).mean(), np.abs(np.diff(g, axis=0)).mean()
    c = g[30:110, 40:120]                                   # centre region where the trap usually sits
    return np.concatenate([h, [sharp, g.std() / 64, (gx + gy) / 32, g.mean() / 255, c.std() / 64, c.mean() / 255]])

def augment(im, label):
    out = [im, ImageOps.mirror(im)]
    for _ in range(6):
        a = im
        w, hh = a.size; dx, dy = int(rng.integers(0, w // 10)), int(rng.integers(0, hh // 10))
        a = a.crop((dx, dy, w - int(rng.integers(0, w // 10)), hh - int(rng.integers(0, hh // 10)))).resize((w, hh))
        a = ImageEnhance.Brightness(a).enhance(float(rng.uniform(.75, 1.25)))
        a = ImageEnhance.Color(a).enhance(float(rng.uniform(.8, 1.2)))
        if rng.random() < .3: a = a.filter(ImageFilter.GaussianBlur(float(rng.uniform(.5, 1.5))))
        if rng.random() < .5: a = ImageOps.mirror(a)
        out.append(a)
    if label == 'cant_see':                                   # extra fogged examples for the can't-see class
        for k in (3, 6):
            out.append(Image.blend(im.filter(ImageFilter.GaussianBlur(k)), Image.new('RGB', im.size, (220, 222, 225)), .45))
    return out

meta = json.load(open(os.path.join(HERE, 'frames.json')))
imgs = {m['id']: Image.open(os.path.join(FR, m['id'] + '.jpg')).convert('RGB') for m in meta}
council = [m for m in meta if m['kind'] == 'council']

results = []
for t in council:
    train = [m for m in meta if m['camera'] != t['camera']]
    X, y = [], []
    for m in train:
        for a in augment(imgs[m['id']], m['label']):
            X.append(feats(a)); y.append(m['label'])
    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.5))
    clf.fit(np.array(X), np.array(y))
    p = clf.predict_proba([feats(imgs[t['id']])])[0]
    probs = {c: 0.0 for c in CLASSES}; probs.update({c: float(v) for c, v in zip(clf.classes_, p)})
    pred = max(probs, key=probs.get); conf = probs[pred]
    results.append(dict(id=t['id'], site=t['site'], camera=t['camera'], date=t['date'], note=t['note'],
                        truth=t['label'], pred=pred, conf=round(conf, 2), probs={k: round(v, 2) for k, v in probs.items()},
                        routed='review' if conf < ABSTAIN else 'auto-flag', correct=pred == t['label'],
                        trained_on=len(train), train_images=len(X), train_classes=sorted(set(y))))

cm = {a: {b: 0 for b in CLASSES} for a in CLASSES}
for r in results: cm[r['truth']][r['pred']] += 1
per = {}
for c in CLASSES:
    tp = cm[c][c]; fn = sum(cm[c].values()) - tp; fp = sum(cm[a][c] for a in CLASSES) - tp
    per[c] = dict(support=sum(cm[c].values()), tp=tp, fp=fp, fn=fn)
acc = sum(r['correct'] for r in results) / len(results)
out = dict(model='Baseline: colour, sharpness and texture features with logistic regression',
           scheme='Leave one camera out over 8 Council frames; train on simulated and other cameras (augmented); test frames never augmented',
           abstain=ABSTAIN, classes=CLASSES, accuracy=round(acc, 2), n_test=len(results),
           n_train_sources=len([m for m in meta]) - 1, confusion=cm, per_class=per, results=results,
           frames=meta)
os.makedirs(os.path.join(ROOT, 'docs', 'data'), exist_ok=True)
for p in (os.path.join(HERE, 'results.json'), os.path.join(ROOT, 'docs', 'data', 'model-results.json')):
    json.dump(out, open(p, 'w'), indent=1)
open(os.path.join(ROOT, 'docs', 'data', 'model-results.js'), 'w').write('window.MODEL=' + json.dumps(out) + ';')
print('accuracy', acc)
for r in results: print(f"{r['site']:15} {r['date']} truth={r['truth']:9} pred={r['pred']:9} conf={r['conf']:.2f} {r['routed']}")
print(json.dumps(per))
