"""Independently authored scalar V2.4.4 semantic oracles."""
from __future__ import annotations
import math
import numpy as np
from . import v24

def scalar_compound_statistic(observations):
    obs=list(observations); evid=np.asarray([math.exp(v24.score_family(f,obs).log_evidence) for f in v24.FAMILIES])
    total=float(np.dot(v24.PRIOR,evid)); T=len(obs); alpha=((8.,2.),(2.,8.))
    one=0.
    for c in (0,1):
        mass=.5
        for i in range(T-1):mass*= (alpha[c][c]+i)/(sum(alpha[c])+i)
        for o in obs:
            cue=o.cue%3;p=(.8,.75,.7)[cue] if c==0 else (.2,.25,.3)[cue]
            mass*=1 if o.outcome is None else (p if o.outcome else 1-p)
            if o.marker is not None:
                row=((.8,.05,.15),(.05,.8,.15))[c]
                mass*=row[{"then_marker":0,"now_marker":1,"ambiguous":2}[o.marker]]
            if o.root is not None:mass*=.5
        one+=mass
    z1=evid[2]-one;q=.2*z1/total
    pi_one=sum(.5*math.prod((alpha[c][c]+i)/(sum(alpha[c])+i) for i in range(T-1)) for c in (0,1))
    rho=.2*(1-pi_one)
    return math.log(q/(1-q))-math.log(rho/(1-rho))

def rank_pvalue(observed, randomized):
    return (1+sum(float(x)>=float(observed) for x in randomized))/(len(randomized)+1)

def nearest_rank_95(values):
    ordered=sorted(float(x) for x in values)
    return ordered[math.ceil(.95*len(ordered))-1]
