# predictor.py

import csv
from collections import Counter, defaultdict

def load_history(path, draw_type):
    hist = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["Type"] == draw_type:
                hist.append((int(r["D1"]), int(r["D2"]), int(r["D3"])))
    return hist

def normalize(counter):
    total = sum(counter.values()) or 1
    return {k: v / total for k, v in counter.items()}

def build_probs(history):
    pos = [Counter() for _ in range(3)]
    trans = [defaultdict(Counter) for _ in range(3)]
    sumc = Counter()
    for i, (d1, d2, d3) in enumerate(history):
        pos[0][d1] += 1
        pos[1][d2] += 1
        pos[2][d3] += 1
        sumc[d1 + d2 + d3] += 1
        if i > 0:
            prev = history[i-1]
            for k in range(3):
                trans[k][prev[k]][history[i][k]] += 1
    pp = [normalize(p) for p in pos]
    tp = [{k: normalize(v) for k,v in t.items()} for t in trans]
    sp = normalize(sumc)
    return pp, tp, sp

def score_candidate(cand, last_draw, pp, tp, sp, alpha, beta, gamma):
    score = 1.0
    for i, d in enumerate(cand):
        f = pp[i].get(d, 1e-6)
        tr = tp[i].get(last_draw[i], {}).get(d, 1e-6)
        score *= (f ** alpha) * (tr ** beta)
    s = sum(cand)
    score *= (sp.get(s, 1e-6) ** gamma)
    return score

def predict_top5(history, alpha, beta, gamma):
    pp, tp, sp = build_probs(history)
    last = history[-1]
    scores = []
    for d1 in range(10):
        for d2 in range(10):
            for d3 in range(10):
                sc = score_candidate((d1, d2, d3), last, pp, tp, sp, alpha, beta, gamma)
                scores.append(((d1, d2, d3), sc))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:5]
