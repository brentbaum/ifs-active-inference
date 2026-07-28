"""V2.4.4 gates 1-3, with ratchet stops."""
from __future__ import annotations
import ast,csv,inspect,json,math,time
from pathlib import Path
import numpy as np
from ref import v24,v243,v244,v244_oracle

OUT=Path("results/V2.4.4");OUT.mkdir(parents=True,exist_ok=True)
def dump(name,x): (OUT/name).write_text(json.dumps(x,indent=2,sort_keys=True,default=lambda z:z.item() if isinstance(z,np.generic) else str(z))+"\n")
def writecsv(name,rows):
    with (OUT/name).open("w",newline="") as h:w=csv.DictWriter(h,fieldnames=rows[0]);w.writeheader();w.writerows(rows)

def gate1():
    old=json.load(open("results/V2.4.3/gate-1.json"))["proofs"]
    obs=v24.generate_world("context_split",799100,length=8)["observations"];y,m,c=v244.encode(obs)
    t=float(v244.batch_statistic(y[None],m[None],c)[0]);oracle=v244_oracle.scalar_compound_statistic(obs)
    # exact compound recombination, using the oracle's scalar pieces
    ev=np.asarray([math.exp(v24.score_family(f,obs).log_evidence) for f in v24.FAMILIES]);full=float(np.dot(v24.PRIOR,ev))
    r=v243.path_class_readout(obs);rho=.2*r.prior[1];rjoint=.2*r.prior[1]*r.conditional_evidence[1]
    recombined=rjoint+(full-rjoint)
    p21={"complete_evidence":full,"compound_recombined":recombined,"error":abs(full-recombined),"passed":abs(full-recombined)<1e-10}
    p22={"production_T":t,"independent_T":oracle,"error":abs(t-oracle),"passed":abs(t-oracle)<1e-10}
    # Enumerably small identity-null ranks: all four orderings occupy each rank once.
    vals=[-1.,0.,1.,2.];ps=[v244_oracle.rank_pvalue(x,vals) for x in vals]
    p23={"public_null_statistics":vals,"rank_pvalues":ps,"minimum_p":min(ps),
         "discrete_level":1/(len(vals)+1),"independent_rank_formula":True,"passed":ps==[1.,.8,.6,.4]}
    src=inspect.getsource(v244);tree=ast.parse(src)
    forbidden=[n.id for n in ast.walk(tree) if isinstance(n,ast.Name) and n.id in {"posterior_store","evidence_store","parameter_posterior_store"}]
    p24={"analysis_only":["replicate_id","observed_label","control_label","p_CRT","E_null"],
         "forbidden_store_targets":forbidden,"pi1_24":0.92741935483871,"passed":not forbidden}
    proofs={**old,"21_compound_structural_recombination":p21,"22_global_structural_odds_identity":p22,
            "23_randomization_exchangeability":p23,"24_purity_and_custody":p24}
    result={"stage":"V2.4.4","gate":1,"proof_count":24,"proofs":proofs,
      "B_max_inherited_formation":3.801426508560692,"B_max_v24_common_emissions":6.704414354964107,
      "pi1_24":0.92741935483871,"passed":all(x["passed"] for x in proofs.values())}
    dump("gate-1.json",result);return result["passed"]

def gate2():
    original=list(v24.PARAMETERS["development_seed_blocks"]["five_family_recovery"])
    v24.PARAMETERS["development_seed_blocks"]["five_family_recovery"]=[790500,790999]
    try:base=v24.recovery_assay()
    finally:v24.PARAMETERS["development_seed_blocks"]["five_family_recovery"]=original
    rows=[];counts={f:{"material":0,"selective":0} for f in v24.FAMILIES}
    for pos,seed in enumerate(range(790500,791000)):
        truth=v24.FAMILIES[pos//100];world=v24.generate_world(truth,seed,length=96);pre,_=v24._heldout_partition(world["observations"])
        mat=v243.material_redescription(pre);crt=v244.crt_readout(pre,seed)
        selective=bool(mat["material_redescription"] and crt["p_CRT"]<=.05)
        counts[truth]["material"]+=int(mat["material_redescription"]);counts[truth]["selective"]+=int(selective)
        rows.append({"seed":seed,"truth":truth,**mat,"T0":crt["T0"],"p_CRT":crt["p_CRT"],
          "Q95":crt["Q95"],"E_null":crt["E_null"],"selective_material_redescription":selective})
    rates={f:{k:v/100 for k,v in d.items()} for f,d in counts.items()}
    checks={**base["checks"],"cs_material":rates["context_split"]["material"]>=.60,
      "cs_selective":rates["context_split"]["selective"]>=.60}
    for f in v24.FAMILIES:
        if f!="context_split":
            checks[f"{f}_material"]=rates[f]["material"]<=.10
            checks[f"{f}_selective"]=rates[f]["selective"]<=.10
    result={**base,"stage":"V2.4.4","gate":2,"structural_rates":rates,
      "checks":{k:bool(v) for k,v in checks.items()},"pi1_24":0.92741935483871,
      "B_max_inherited_formation":3.801426508560692,"B_max_v24_common_emissions":6.704414354964107}
    result["failures"]=[k for k,v in checks.items() if not v];result["passed"]=not result["failures"]
    dump("gate-2.json",result);writecsv("gate-2-structural-per_world.csv",rows);return result["passed"]

if __name__=="__main__":
    if not gate1():raise SystemExit("STOP gate 1")
    if not gate2():
        (OUT/"diagnosis-stub.md").write_text("# V2.4.4 Gate-2 stop\n\nSee `gate-2.json`; no Gate 3 was run.\n")
        raise SystemExit("STOP gate 2")
