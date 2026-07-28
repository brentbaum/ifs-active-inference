"""Independently authored V2.4.3 CS path-class summation oracle."""
from __future__ import annotations
import math
import numpy as np
from . import v24

def enumerate_classes(observations):
    obs = list(observations)
    a = ((8.0, 2.0), (2.0, 8.0))
    def run(with_data):
        frontier = {(0, (0,0,0,0), 1): .5, (1, (0,0,0,0), 2): .5}
        for t, item in enumerate(obs):
            seen = {}
            for (c, counts, mask), mass in frontier.items():
                cue = item.cue % 3
                p = (0.8, .75, .7)[cue] if c == 0 else (.2, .25, .3)[cue]
                y = 1.0 if item.outcome is None else (p if item.outcome else 1-p)
                marker_rows = ((.8,.05,.15),(.05,.8,.15))
                mi = {"then_marker":0,"now_marker":1,"ambiguous":2}
                x = 1.0 if item.marker is None else marker_rows[c][mi[item.marker]]
                r = 1.0 if item.root is None else .5
                seen[(c,counts,mask)] = mass * (y*x*r if with_data else 1.0)
            if t == len(obs)-1:
                frontier = seen; break
            nxt = {}
            for (c, counts, mask), mass in seen.items():
                for j in (0,1):
                    denom = sum(a[c]) + counts[2*c] + counts[2*c+1]
                    chance = (a[c][j] + counts[2*c+j]) / denom
                    updated = list(counts); updated[2*c+j] += 1
                    key = (j,tuple(updated),mask | (1<<j))
                    nxt[key] = nxt.get(key,0.0) + mass*chance
            frontier = nxt
        return np.array([
            sum(m for (_,_,mask),m in frontier.items() if mask != 3),
            sum(m for (_,_,mask),m in frontier.items() if mask == 3),
        ])
    prior_joint, data_joint = run(False), run(True)
    pi = prior_joint/prior_joint.sum(); q = data_joint/data_joint.sum()
    bf = (q[1]/q[0])/(pi[1]/pi[0])
    return {"prior":pi, "posterior":q, "bf":float(bf), "log_bf":math.log(float(bf))}

def mixture_logsumexp(weights, sequence_probabilities):
    values = [float(w)*float(p) for w,p in zip(weights,sequence_probabilities)]
    return math.log(sum(values))
