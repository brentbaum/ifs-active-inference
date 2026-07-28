"""V2.4.4 exact batched compound-structure and CRT readouts."""
from __future__ import annotations
import math
import numpy as np
from . import v24
from .rng import component_rng

def _norm_step(mass):
    z=mass.sum(axis=1); return mass/z[:,None],np.log(z)

def _emissions(observations_batch, markers_batch, cues, probabilities, descriptor=None):
    y=np.ones((len(observations_batch),len(cues),len(probabilities)))
    for k,p in enumerate(probabilities):
        y[:,:,k]=np.where(observations_batch<0,1,np.where(observations_batch==1,p,1-p))
    if descriptor is None:return y
    rows=np.asarray([v24._marker_row(d) for d in descriptor])
    x=np.ones((len(markers_batch),len(cues),len(descriptor)))
    for k in range(len(descriptor)):
        x[:,:,k]=np.where(markers_batch<0,1,rows[k][np.maximum(markers_batch,0)])
    return y*x

def _factorized(batch_y,batch_m,cues,family):
    B,T=batch_y.shape
    # candidate-common nuisance marker HMM
    n=np.tile(v24._nuisance_initial(),(B,1)); nlog=np.zeros(B)
    nx=_emissions(batch_y,batch_m,cues,[.5,.5,.5],["then","now","none"])
    # discard dummy outcome component
    nx=np.ones_like(nx)*np.where(batch_m[:,:,None]<0,1,
        np.asarray([v24._marker_row(d) for d in ("then","now","none")]).T[np.maximum(batch_m,0),:])
    if family=="global_downweight":
        process=v24.PARAMETERS["family_processes"][family]
        s=np.tile(np.asarray(process["initial_distribution"]),(B,1)); slog=np.zeros(B)
        tr=np.asarray(process["transition_matrix"])
        for t,cue in enumerate(cues):
            probs=np.asarray([v24._gw_probability(int(cue),k) for k in range(5)])
            ly=np.where(batch_y[:,t,None]<0,1,np.where(batch_y[:,t,None]==1,probs,1-probs))
            s,inc=_norm_step(s*ly); slog+=inc
            n,inc=_norm_step(n*nx[:,t]); nlog+=inc
            if t<T-1:s=s@tr;n=n@v24._nuisance_transition()
        return slog+nlog
    process=v24.PARAMETERS["family_processes"][family]; tr=np.asarray(process["per_cue_transition_matrix"])
    states=np.stack([np.tile(np.asarray(process["initial_distribution_by_cue"][f"cue_{c+1}"]),(B,1)) for c in range(3)],axis=1)
    log=np.zeros(B)
    for t,cue in enumerate(cues):
        probs=v24.ELEMENTAL_GRID
        ly=np.where(batch_y[:,t,None]<0,1,np.where(batch_y[:,t,None]==1,probs,1-probs))
        states[:,cue],inc=_norm_step(states[:,cue]*ly);log+=inc
        n,inc=_norm_step(n*nx[:,t]);nlog+=inc
        if t<T-1:
            states=np.einsum("bci,ij->bcj",states,tr);n=n@v24._nuisance_transition()
    return log+nlog

def _drift(batch_y,batch_m,cues):
    B,T=batch_y.shape;p=v24.PARAMETERS["family_processes"]["continuous_drift"]
    names=list(p["transition_templates"]); tr=np.asarray([p["transition_templates"][x] for x in names])
    joint=np.tile(np.outer(p["template_prior"],p["initial_distribution"]),(B,1,1));log=np.zeros(B)
    n=np.tile(v24._nuisance_initial(),(B,1));nlog=np.zeros(B)
    rows=np.asarray([v24._marker_row(d) for d in ("then","now","none")])
    for t in range(T):
        ly=np.where(batch_y[:,t,None]<0,1,np.where(batch_y[:,t,None]==1,v24.ELEMENTAL_GRID,1-v24.ELEMENTAL_GRID))
        joint,inc=_norm_step((joint*ly[:,None,:]).reshape(B,-1));joint=joint.reshape(B,3,5);log+=inc
        mx=np.where(batch_m[:,t,None]<0,1,rows[:,np.maximum(batch_m[:,t],0)].T)
        n,inc=_norm_step(n*mx);nlog+=inc
        if t<T-1:
            joint=np.einsum("bki,kij->bkj",joint,tr);n=n@v24._nuisance_transition()
    return log+nlog

def _graph(initial, transition, T):
    levels=[list(initial)];edges=[]
    dist={k:1. for k in initial}
    for t in range(T-1):
        old=levels[-1]; fake={k:1/len(old) for k in old}; nxt=transition(fake); new=list(nxt)
        index={k:i for i,k in enumerate(new)}; e=[]
        # recover exact probabilities by one-state transition
        for i,k in enumerate(old):
            out=transition({k:1.})
            e.append([(index[j],p) for j,p in out.items()])
        edges.append(e);levels.append(new);dist=nxt
    return levels,edges

def _dynamic(batch_y,batch_m,cues,family):
    B,T=batch_y.shape
    if family=="context_split":
        initial=v24._cs_initial(); trans=v24._cs_transition
    else: initial=v24._cp_initial();trans=v24._cp_transition
    levels,edges=_graph(initial,trans,T)
    mass=np.tile(np.asarray([initial[k] for k in levels[0]]),(B,1));log=np.zeros(B)
    for t,keys in enumerate(levels):
        context=np.asarray([k[0] for k in keys])
        probs=np.where(context==0,v24.BASELINE[int(cues[t])],v24.CORRECTIVE[int(cues[t])])
        desc=np.where(context==0,0,1)
        rows=np.asarray([v24._marker_row("then"),v24._marker_row("now")])
        ly=np.where(batch_y[:,t,None]<0,1,np.where(batch_y[:,t,None]==1,probs,1-probs))
        lx=np.where(batch_m[:,t,None]<0,1,rows[desc,np.maximum(batch_m[:,t,None],0)])
        mass,inc=_norm_step(mass*ly*lx);log+=inc
        if t<T-1:
            nxt=np.zeros((B,len(levels[t+1])))
            for i,out in enumerate(edges[t]):
                for j,p in out:nxt[:,j]+=mass[:,i]*p
            mass=nxt
    return log

def batch_statistic(outcomes,markers,cues):
    logs=np.column_stack([
      _factorized(outcomes,markers,cues,"global_downweight"),
      _factorized(outcomes,markers,cues,"cue_local_relearning"),
      _dynamic(outcomes,markers,cues,"context_split"),
      _drift(outcomes,markers,cues),
      _dynamic(outcomes,markers,cues,"change_point")])
    mx=(logs+np.log(v24.PRIOR)).max(axis=1)
    total=mx+np.log(np.exp(logs+np.log(v24.PRIOR)-mx[:,None]).sum(axis=1))
    T=len(cues);alpha=v24._cs_alpha();const=[]
    for c in (0,1):
        lp=math.log(.5)+sum(math.log((alpha[c,c]+i)/(alpha[c].sum()+i)) for i in range(T-1))
        p=np.asarray([v24.BASELINE[int(q)] if c==0 else v24.CORRECTIVE[int(q)] for q in cues])
        lp=lp+np.where(outcomes<0,0,np.where(outcomes==1,np.log(p),np.log(1-p))).sum(axis=1)
        row=v24._marker_row("then" if c==0 else "now")
        lp=lp+np.where(markers<0,0,np.log(row[np.maximum(markers,0)])).sum(axis=1);const.append(lp)
    one=np.logaddexp(const[0],const[1]);full=logs[:,v24.FAMILY_INDEX["context_split"]]
    z1=full+np.log1p(-np.exp(np.minimum(one-full,-1e-15)))
    logr=np.log(v24.PRIOR[v24.FAMILY_INDEX["context_split"]])+z1-total
    q=np.exp(logr);rho=float(v24.PRIOR[v24.FAMILY_INDEX["context_split"]])*(1-sum(.5*math.prod((alpha[c,c]+i)/(alpha[c].sum()+i) for i in range(T-1)) for c in (0,1)))
    return np.log(q/(1-q))-math.log(rho/(1-rho))

def encode(observations):
    y=np.asarray([(-1 if o.outcome is None else o.outcome) for o in observations],int)
    m=np.asarray([(-1 if o.marker is None else v24.MARKER_INDEX[o.marker]) for o in observations],int)
    c=np.asarray([o.cue%3 for o in observations],int);return y,m,c

def randomization_batch(observations,seed,count=999):
    y,m,c=encode(observations);ys=np.tile(y,(count,1));ms=np.tile(m,(count,1))
    for b in range(count):
        for cue in range(3):
            idx=np.flatnonzero(c==cue)
            ys[b,idx]=y[idx][component_rng(seed,f"v244-crt-{b}-outcome-{cue}").permutation(len(idx))]
            ms[b,idx]=m[idx][component_rng(seed,f"v244-crt-{b}-marker-{cue}").permutation(len(idx))]
    return ys,ms,c

def crt_readout(observations,seed,count=999):
    y,m,c=encode(observations);t0=float(batch_statistic(y[None,:],m[None,:],c)[0])
    ys,ms,c=randomization_batch(observations,seed,count);null=batch_statistic(ys,ms,c)
    rank=int(np.sum(null>=t0));q95=float(np.sort(null)[math.ceil(.95*count)-1])
    return {"T0":t0,"p_CRT":(1+rank)/(count+1),"Q95":q95,"E_null":t0-q95,
      "selective":bool((1+rank)/(count+1)<=.05),"null":null}
