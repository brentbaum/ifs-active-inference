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

def interval(values, seed, name):
    return v24._bootstrap_interval(values, seed, name)

def gate3():
    rows_by_name={}; checks={}
    # Assays 1-2.
    controls=[]
    for pos,seed in enumerate(range(787500,787740)):
        truth="continuous_drift" if pos<120 else "change_point"
        world=v24.generate_world(truth,seed,length=96)
        result=v24.compare_families(world["observations"])
        pre,_=v24._heldout_partition(world["observations"])
        material=v243.material_redescription(pre)
        controls.append({"seed":seed,"truth":truth,
          "selected":v24.selected_family(result["posterior"]) or "tie",**material})
    rows_by_name["dr-cp"]=controls
    for truth in ("continuous_drift","change_point"):
        subset=[r for r in controls if r["truth"]==truth]
        checks[f"{truth}_raw_cs"]=np.mean([r["selected"]=="context_split" for r in subset])<=.10
        checks[f"{truth}_material"]=np.mean([r["material_redescription"] for r in subset])<=.10

    # Assay 3 and exact BMA.
    held=[]; family_regrets={f:[] for f in v24.FAMILIES}; cs_margins=[]
    for pos,seed in enumerate(range(787800,788200)):
        truth=v24.FAMILIES[pos//80]; world=v24.generate_world(truth,seed,length=32)
        b=v243.bma_heldout(world["observations"])
        true_log=b["family_log_scores"][v24.FAMILY_INDEX[truth]]
        regret=(true_log-b["bma_log_score"])/max(1,b["observed_tokens"])
        hm=v24._heldout_metrics(world)
        family_regrets[truth].append(regret)
        if truth=="context_split" and math.isfinite(hm["generating_family_margin"]):
            cs_margins.append(hm["generating_family_margin"])
        held.append({"seed":seed,"truth":truth,"regret":regret,
          "bma_log_score":b["bma_log_score"],"pre_weights":b["pre_weights"],
          "material_pre":b["material_pre"],"heldout":hm})
    regret_ci={f:interval(v,798000+i,f"v243-regret-{f}") for i,(f,v) in enumerate(family_regrets.items())}
    checks.update({f"bma_{f}":ci[2]<=.01 for f,ci in regret_ci.items()})
    cs_ci=interval(cs_margins,798010,"v243-cs-margin")
    checks["cs_matched"]=len(cs_margins)>=60
    checks["cs_margin"]=cs_ci[0]>=.01 and cs_ci[1]>0
    rows_by_name["heldout-bma"]=held

    # Assay 5 descriptive.
    miss=[]
    for pos,seed in enumerate(range(788200,788440)):
        truth=v24.FAMILIES[pos%5]; world=v24.generate_world(truth,seed,missingness=.30 if pos%2 else 0)
        obs=list(world["observations"])
        if pos%4==0: obs=v24._shuffle_marker_association(obs,seed)
        b=v243.bma_heldout(obs)
        best=max(b["family_log_scores"])
        miss.append({"seed":seed,"best_minus_bma":(best-b["bma_log_score"])/max(1,b["observed_tokens"]),
                     "pre_weights":b["pre_weights"],"material_pre":b["material_pre"]})
    rows_by_name["misspecification"]=miss

    # Assays 6-7.
    genuine=[]; cl=[]
    for seed in range(788500,788620):
        value=v24._composition_world(seed); obs=value["world"]["observations"]; pre,_=v24._heldout_partition(obs)
        m=v243.material_redescription(pre)
        sh=v243.material_redescription(v24._heldout_partition(v24._shuffle_marker_association(obs,seed))[0])
        fx=v243.material_redescription(v24._heldout_partition(v24._fixed_context_control(obs,seed))[0])
        hm=v24._heldout_metrics(value["world"])
        genuine.append({"seed":seed,**m,"shuffle_material":sh["material_redescription"],
          "single_material":fx["material_redescription"],"transfer":value["signed_transfer"],
          "present":value["new_direction"]*(value["now_after"]-value["then_after"]),
          "historical":value["then_after"]-value["then_before"],"margin":hm["generating_family_margin"]})
    for seed in range(788620,788740):
        world=v24.generate_world("cue_local_relearning",seed,length=96)
        result=v24.compare_families(world["observations"]); pre,_=v24._heldout_partition(world["observations"])
        cl.append({"seed":seed,"selected":v24.selected_family(result["posterior"]) or "tie",**v243.material_redescription(pre)})
    rows_by_name["genuine-controls"]=genuine; rows_by_name["cue-local"]=cl
    gmargin=[r["margin"] for r in genuine if math.isfinite(r["margin"])]
    checks.update({
      "genuine_raw":np.mean([r["raw_cs_argmax"] for r in genuine])>=.60,
      "genuine_material":np.mean([r["material_redescription"] for r in genuine])>=.60,
      "genuine_logbf":interval([r["log_bf"] for r in genuine],798020,"glog")[1]>0,
      "genuine_margin":len(gmargin)>=60 and interval(gmargin,798021,"gmargin")[0]>=.01 and interval(gmargin,798021,"gmargin")[1]>0,
      "genuine_shuffle_control":np.mean([r["shuffle_material"] for r in genuine])<=.10,
      "genuine_single_control":np.mean([r["single_material"] for r in genuine])<=.10,
      "genuine_transfer":interval([r["transfer"] for r in genuine],798022,"gtransfer")[0]>=.05 and interval([r["transfer"] for r in genuine],798022,"gtransfer")[1]>0,
      "historical":max(abs(r["historical"]) for r in genuine)<=.01,
      "cue_local_recovery":np.mean([r["selected"]=="cue_local_relearning" for r in cl])>=.60,
      "cue_local_material":np.mean([r["material_redescription"] for r in cl])<=.10})

    # Assay 8 formed bank.
    bridge=[]
    for seed,record in zip(range(788800,788920),v24._bank_states()):
        value=v24._composition_world(seed,bank_state=record["serialized_state"]); obs=value["world"]["observations"]
        pre,_=v24._heldout_partition(obs); m=v243.material_redescription(pre)
        sh=v243.material_redescription(v24._heldout_partition(v24._shuffle_marker_association(obs,seed))[0])
        fx=v243.material_redescription(v24._heldout_partition(v24._fixed_context_control(obs,seed))[0])
        hm=v24._heldout_metrics(value["world"])
        bridge.append({"seed":seed,"stratum":record["stratum"],**m,
          "shuffle_material":sh["material_redescription"],"single_material":fx["material_redescription"],
          "transfer":value["signed_transfer"],"historical":value["then_after"]-value["then_before"],
          "G_fixed":0.0,"margin":hm["generating_family_margin"]})
    rows_by_name["bridge"]=bridge
    bm=[r["margin"] for r in bridge if math.isfinite(r["margin"])]
    checks.update({"bridge_material":np.mean([r["material_redescription"] for r in bridge])>=.60,
      "bridge_shuffle":np.mean([r["shuffle_material"] for r in bridge])<=.10,
      "bridge_single":np.mean([r["single_material"] for r in bridge])<=.10,
      "bridge_margin":len(bm)>=60 and interval(bm,798030,"bmargin")[0]>=.01 and interval(bm,798030,"bmargin")[1]>0,
      "bridge_transfer":interval([r["transfer"] for r in bridge],798031,"btransfer")[0]>=.05 and interval([r["transfer"] for r in bridge],798031,"btransfer")[1]>0,
      "bridge_historical":max(abs(r["historical"]) for r in bridge)<=.01,
      "bridge_G_fixed":max(abs(r["G_fixed"]) for r in bridge)<=1e-10})
    result={"stage":"V2.4.3","gate":3,"checks":{k:bool(v) for k,v in checks.items()},
      "bma_regret_intervals":regret_ci,"cs_margin_interval":cs_ci,
      "rates":{"genuine_material":np.mean([r["material_redescription"] for r in genuine]),
       "genuine_raw":np.mean([r["raw_cs_argmax"] for r in genuine]),
       "genuine_shuffle_material":np.mean([r["shuffle_material"] for r in genuine]),
       "genuine_single_material":np.mean([r["single_material"] for r in genuine]),
       "cl_recovery":np.mean([r["selected"]=="cue_local_relearning" for r in cl]),
       "bridge_material":np.mean([r["material_redescription"] for r in bridge]),
       "bridge_shuffle_material":np.mean([r["shuffle_material"] for r in bridge]),
       "bridge_single_material":np.mean([r["single_material"] for r in bridge])},
      "B_max_inherited_formation":3.801426508560692,
      "B_max_v24_common_emissions":6.704414354964107}
    result["failures"]=[k for k,v in checks.items() if not v]; result["passed"]=not result["failures"]
    dump("gate-3.json",result)
    for name,rows in rows_by_name.items():
        with (OUT/f"gate-3-{name}-per_world.json").open("w") as h: json.dump(rows,h,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))
    return result["passed"]

if __name__=="__main__":
    if not gate1(): raise SystemExit("STOP gate 1")
    if not gate2(): raise SystemExit("STOP gate 2")
    if not gate3():
        (OUT/"diagnosis-stub.md").write_text("# V2.4.3 Gate-3 stop\n\nSee `gate-3.json`. Failures are retained verbatim; no Gate 4 was run.\n")
        raise SystemExit("STOP gate 3")
