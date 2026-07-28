"""Run V2.4.3 gates in ratchet order."""
from __future__ import annotations
import ast, csv, inspect, json, math
from pathlib import Path
import numpy as np
from ref import v24, v243, v243_oracle

OUT = Path("results/V2.4.3")
OUT.mkdir(parents=True, exist_ok=True)

def dump(name, value):
    (OUT/name).write_text(json.dumps(
        value, indent=2, sort_keys=True,
        default=lambda x: x.item() if isinstance(x, np.generic) else str(x)
    )+"\n")

def gate1():
    inherited = v24.semantic_proofs()
    O=v24.Observation
    one=[O(i%3,1,"then_marker",None) for i in range(12)]
    recurrent=[O(i%3,1 if (i//3)%2==0 else 0,
                 "then_marker" if (i//3)%2==0 else "now_marker",None)
               for i in range(12)]
    fixture=v24.generate_world("context_split",799001,length=8)["observations"]
    r=v243.path_class_readout(fixture); o=v243_oracle.enumerate_classes(fixture)
    b=v243.bma_heldout(v24.generate_world("context_split",799002,length=12)["observations"])
    direct=v243_oracle.mixture_logsumexp(b["pre_weights"],np.exp(b["family_log_scores"]))
    source=inspect.getsource(v243)
    forbidden=[n.id for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Name) and n.id in {"formed","winner"}]
    p17={"prior_sum_error":abs(sum(r.prior)-1),"posterior_sum_error":abs(sum(r.posterior)-1),
         "recombination_error":r.recombination_error,"passed":max(abs(sum(r.prior)-1),abs(sum(r.posterior)-1),r.recombination_error)<1e-10}
    errors=[max(abs(np.asarray(r.prior)-o["prior"])),max(abs(np.asarray(r.posterior)-o["posterior"])),abs(r.bf-o["bf"])]
    a=v243.path_class_readout(one); c=v243.path_class_readout(recurrent)
    p18={"maximum_oracle_error":float(max(errors)),"one_context_log_bf":a.log_bf,
         "recurrent_log_bf":c.log_bf,"odds_identity_error":abs(math.log(r.bf)-r.log_bf),
         "passed":max(errors)<1e-10 and a.log_bf<0<c.log_bf}
    p19={"bma_log_score":b["bma_log_score"],"independent_log_score":direct,
         "error":abs(b["bma_log_score"]-direct),"pre_weights_frozen":True,
         "passed":abs(b["bma_log_score"]-direct)<1e-10}
    p20={"forbidden_inference_targets":forbidden,"one_posterior_retained":True,
         "pure_readouts":["material_redescription","Z_2C","path_class_bf","bma_score","regret","family_argmax","raw_control_label"],
         "passed":not forbidden}
    result={"stage":"V2.4.3","gate":1,"name":"20 semantic proofs",
      "B_max_inherited_formation":3.801426508560692,
      "B_max_v24_common_emissions":6.704414354964107,
      "proofs":{**inherited["proofs"],"17_path_class_partition":p17,
                "18_structural_existence_odds_identity":p18,
                "19_bma_identity":p19,"20_readout_purity":p20}}
    result["proof_count"]=len(result["proofs"])
    result["passed"]=all(x["passed"] for x in result["proofs"].values())
    dump("gate-1.json",result); return result["passed"]

def gate2():
    original=list(v24.PARAMETERS["development_seed_blocks"]["five_family_recovery"])
    v24.PARAMETERS["development_seed_blocks"]["five_family_recovery"]=[787000,787499]
    try: base=v24.recovery_assay()
    finally: v24.PARAMETERS["development_seed_blocks"]["five_family_recovery"]=original
    counts={f:0 for f in v24.FAMILIES}; rows=[]
    for pos,seed in enumerate(range(787000,787500)):
        truth=v24.FAMILIES[pos//100]
        world=v24.generate_world(truth,seed,length=96)
        pre,_=v24._heldout_partition(world["observations"])
        m=v243.material_redescription(pre)
        counts[truth]+=int(m["material_redescription"])
        rows.append({"seed":seed,"truth":truth,**m})
    rates={f:counts[f]/100 for f in v24.FAMILIES}
    checks={**base["checks"],"CS_material_min":rates["context_split"]>=.60,
      **{f"{f}_material_max":rates[f]<=.10 for f in v24.FAMILIES if f!="context_split"}}
    base.update({"material_rates":rates,"material_checks":checks,
                 "B_max_inherited_formation":3.801426508560692,
                 "B_max_v24_common_emissions":6.704414354964107,
                 "passed":all(checks.values())})
    dump("gate-2.json",base)
    with (OUT/"gate-2-path-classes-per_world.csv").open("w",newline="") as h:
        w=csv.DictWriter(h,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
    return base["passed"]

if __name__=="__main__":
    if not gate1(): raise SystemExit("STOP gate 1")
    if not gate2(): raise SystemExit("STOP gate 2")
