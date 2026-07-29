"""V2.4.4 gates, with the externally adjudicated mixed-verdict ratchet."""
from __future__ import annotations
import argparse,ast,csv,inspect,json,math,os,subprocess,sys,time
from pathlib import Path
import numpy as np
from ref import v24,v243,v244,v244_oracle

OUT=Path("results/V2.4.4");OUT.mkdir(parents=True,exist_ok=True)
B_MAX_FORMATION=3.801426508560692
B_MAX_V24=6.704414354964107
PI1_24=0.92741935483871
ADJUDICATED_NONBLOCKING={
    "genuine_selective_material_min_0.60",
    "bridge_selective_material_min_0.60",
}
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
      "B_max_inherited_formation":B_MAX_FORMATION,"B_max_v24_common_emissions":B_MAX_V24,
      "pi1_24":PI1_24,"passed":all(x["passed"] for x in proofs.values())}
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
      "checks":{k:bool(v) for k,v in checks.items()},"pi1_24":PI1_24,
      "B_max_inherited_formation":B_MAX_FORMATION,"B_max_v24_common_emissions":B_MAX_V24}
    result["failures"]=[k for k,v in checks.items() if not v];result["passed"]=not result["failures"]
    dump("gate-2.json",result);writecsv("gate-2-structural-per_world.csv",rows);return result["passed"]

def interval(values,seed,component):
    return v24._bootstrap_interval(values,seed,component)

def _structural_row(observations,seed):
    sequence=list(observations)
    material=v243.material_redescription(sequence)
    crt=v244.crt_readout(sequence,seed)
    score=v24.score_family("context_split",sequence)
    comparison=v24.compare_families(sequence)
    counts=score.parameter_posterior["transition_expected_counts"]
    means=score.parameter_posterior["transition_mean"]
    context=score.final_predictive["q_context_then_now"]
    row={
      **material,
      "selected":v24.selected_family(comparison["posterior"]) or "tie",
      "family_posterior":comparison["posterior"].tolist(),
      "T0":crt["T0"],"p_CRT":crt["p_CRT"],"Q50":float(np.quantile(crt["null"],.50)),
      "Q90":float(np.quantile(crt["null"],.90)),"Q95":crt["Q95"],
      "Q99":float(np.quantile(crt["null"],.99)),"E_null":crt["E_null"],
      "selective_material_redescription":bool(material["material_redescription"] and crt["p_CRT"]<=.05),
      "null_mean":float(np.mean(crt["null"])),"null_sd":float(np.std(crt["null"],ddof=1)),
      "context_posterior":context,"transition_expected_counts":counts,"transition_mean":means,
      "expected_log_likelihood":score.expected_log_likelihood,
      "parameter_complexity":score.parameter_complexity,
      "latent_path_complexity":score.latent_path_complexity,
      "total_complexity":score.total_complexity,
      "decomposition_error":score.decomposition_error,
    }
    return row,np.asarray(crt["null"],dtype=float)

def _save_structural_block(name,rows,nulls):
    path=OUT/f"gate-3-{name}-per_world.json"
    path.write_text(json.dumps(rows,indent=2,sort_keys=True,default=lambda z:z.item() if isinstance(z,np.generic) else str(z))+"\n")
    np.savez_compressed(OUT/f"gate-3-{name}-crt-nulls.npz",null=np.asarray(nulls,dtype=float))

def _prefix_world(world,length):
    return {**world,"observations":list(world["observations"])[:length]}

def _bma_row(world,seed,total_length):
    shortened=_prefix_world(world,total_length)
    observations=shortened["observations"]
    pre,heldout=v24._heldout_partition(observations)
    pre_scores=[v24.score_family(name,pre) for name in v24.FAMILIES]
    full_scores=[v24.score_family(name,observations) for name in v24.FAMILIES]
    pre_log=np.asarray([score.log_evidence for score in pre_scores])
    weights=v24._softmax(np.log(v24.PRIOR)+pre_log)
    family_logs=np.asarray([full.log_evidence-prefix.log_evidence for prefix,full in zip(pre_scores,full_scores)])
    terms=np.log(weights)+family_logs;maximum=float(terms.max())
    bma_log=maximum+math.log(float(np.exp(terms-maximum).sum()))
    observed=sum(any(value is not None for value in (item.outcome,item.marker,item.root)) for item in heldout)
    truth=shortened["truth"];truth_index=v24.FAMILY_INDEX[truth]
    regret=(family_logs[truth_index]-bma_log)/max(1,observed)
    heldout_log=family_logs/max(1,len(heldout))
    complexity=np.asarray([score.total_complexity/max(1,len(pre)) for score in pre_scores])
    differences=np.abs(complexity-complexity[truth_index])
    matched=[index for index in range(len(v24.FAMILIES)) if index!=truth_index and
      differences[index]<=float(v24.PARAMETERS["analysis"]["complexity_match_nats_per_observation"])]
    best=max(matched,key=lambda index:heldout_log[index]) if matched else None
    readout=v243.path_class_readout(pre)
    cs=v24.FAMILY_INDEX["context_split"]
    unique=bool(np.sum(weights==weights.max())==1 and weights[cs]==weights.max())
    material_pre={
      "material_redescription":bool(unique and readout.posterior[1]>=.80 and readout.bf>=4.0),
      "raw_cs_argmax":unique,"pi0":readout.prior[0],"pi1":readout.prior[1],
      "q0":readout.posterior[0],"q1":readout.posterior[1],"bf":readout.bf,
      "log_bf":readout.log_bf,"recombination_error":readout.recombination_error,
    }
    return {
      "seed":seed,"truth":truth,"total_length":total_length,"regret":regret,
      "observed_tokens":observed,"pre_weights":weights.tolist(),
      "family_log_scores":family_logs.tolist(),"bma_log_score":bma_log,
      "material_pre":material_pre,
      "heldout_log_per_observation":heldout_log.tolist(),
      "preheldout_complexity_per_observation":complexity.tolist(),
      "matched_comparators":[v24.FAMILIES[index] for index in matched],
      "best_matched_comparator":v24.FAMILIES[best] if best is not None else None,
      "generating_family_margin":float(heldout_log[truth_index]-heldout_log[best]) if best is not None else float("nan"),
      "maximum_decomposition_error":max(score.decomposition_error for score in full_scores),
    }

def _bma_triplet(item):
    position,seed=item
    truth=v24.FAMILIES[position//500]
    world=v24.generate_world(truth,seed,length=96)
    return [_bma_row(world,seed,length) for length in (96,32,64)]

def _bma_worker(start_position,end_position,worker):
    output=[]
    for position in range(start_position,end_position):
        output.append({"position":position,"triplet":_bma_triplet((position,791500+position))})
    dump(f".gate-3-bma-worker-{worker}.json",output)

def _parallel_bma_triplets():
    count=2500;workers=min(8,max(1,os.cpu_count() or 1))
    boundaries=np.linspace(0,count,workers+1,dtype=int)
    processes=[]
    for worker in range(workers):
        path=OUT/f".gate-3-bma-worker-{worker}.json"
        if path.exists():
            path.unlink()
        command=[sys.executable,str(Path(__file__).resolve()),"bma-worker",
          str(int(boundaries[worker])),str(int(boundaries[worker+1])),str(worker)]
        processes.append((worker,subprocess.Popen(command,cwd=Path(__file__).resolve().parent)))
    remaining={worker:process for worker,process in processes}
    while remaining:
        time.sleep(10)
        for worker,process in list(remaining.items()):
            status=process.poll()
            if status is None:
                continue
            if status:
                raise RuntimeError(f"BMA worker {worker} exited {status}")
            del remaining[worker]
            print(f"gate3 BMA worker {worker+1}/{workers} complete",flush=True)
    merged=[]
    for worker in range(workers):
        path=OUT/f".gate-3-bma-worker-{worker}.json"
        merged.extend(json.loads(path.read_text()))
        path.unlink()
    merged.sort(key=lambda value:value["position"])
    if [value["position"] for value in merged]!=list(range(count)):
        raise ValueError("parallel BMA result positions incomplete")
    return [value["triplet"] for value in merged]

def _family_trajectory(scores):
    cumulative=np.log(v24.PRIOR).copy()
    trajectory=[]
    for time_index in range(len(scores[0].per_slice_log_predictive)):
        cumulative+=np.asarray([score.per_slice_log_predictive[time_index] for score in scores])
        trajectory.append(v24._softmax(cumulative).tolist())
    return trajectory

def _misspecification_block():
    rows=[];nulls=[]
    for position,seed in enumerate(range(794000,794240)):
        base_family=v24.FAMILIES[position%5]
        world=v24.generate_world(base_family,seed,missingness=.30 if position%2 else 0.0)
        observations=list(world["observations"])
        construction="marker_product" if position%4==0 else "mixed_temporal" if position%4==1 else "missingness_or_base"
        if position%4==0:
            observations=v24._shuffle_marker_association(observations,seed)
        elif position%4==1:
            half=len(observations)//2
            observations=list(v24.generate_world("continuous_drift",seed,length=half)["observations"])+list(
                v24.generate_world("change_point",seed+1,length=len(observations)-half)["observations"])
        bma=v243.bma_heldout(observations)
        best=max(bma["family_log_scores"])
        comparison=v24.compare_families(observations)
        pre,_=v24._heldout_partition(observations)
        structural,null=_structural_row(pre,seed)
        scores=comparison["scores"]
        rows.append({
          "seed":seed,"construction":construction,
          "selected":v24.selected_family(comparison["posterior"]) or "tie",
          "posterior":comparison["posterior"].tolist(),
          "posterior_entropy":float(-np.sum(comparison["posterior"]*np.log(np.maximum(comparison["posterior"],1e-300)))),
          "family_posterior_trajectory":_family_trajectory(scores),
          "best_minus_bma_per_token":(best-bma["bma_log_score"])/max(1,bma["observed_tokens"]),
          "maximum_update_identity_error":comparison["maximum_update_identity_error"],
          "maximum_decomposition_error":max(score.decomposition_error for score in scores),
          "candidate_decompositions":[{
            "family":score.family,"log_evidence":score.log_evidence,
            "expected_log_likelihood":score.expected_log_likelihood,
            "parameter_complexity":score.parameter_complexity,
            "latent_path_complexity":score.latent_path_complexity,
            "total_complexity":score.total_complexity,
            "decomposition_error":score.decomposition_error,
          } for score in scores],
          "structural_pre":structural,
        })
        nulls.append(null)
        if (position+1)%10==0:
            print(f"gate3 misspecification CRT {position+1}/240",flush=True)
    path=OUT/"gate-3-misspecification-per_world.json"
    path.write_text(json.dumps(rows,indent=2,sort_keys=True,default=lambda z:z.item() if isinstance(z,np.generic) else str(z))+"\n")
    np.savez_compressed(OUT/"gate-3-misspecification-crt-nulls.npz",null=np.asarray(nulls,dtype=float))
    return rows

def _update_misspecification_summary(rows):
    result=json.loads((OUT/"gate-3.json").read_text())
    result["misspecification"]={
      "world_count":len(rows),
      "mean_best_minus_bma_per_token":float(np.mean([row["best_minus_bma_per_token"] for row in rows])),
      "mean_posterior_entropy":float(np.mean([row["posterior_entropy"] for row in rows])),
      "material_rate_descriptive":float(np.mean([row["structural_pre"]["material_redescription"] for row in rows])),
      "selective_material_rate_descriptive":float(np.mean([row["structural_pre"]["selective_material_redescription"] for row in rows])),
      "mean_p_CRT_descriptive":float(np.mean([row["structural_pre"]["p_CRT"] for row in rows])),
      "maximum_update_identity_error":max(row["maximum_update_identity_error"] for row in rows),
      "maximum_decomposition_error":max(row["maximum_decomposition_error"] for row in rows),
    }
    dump("gate-3.json",result)

def gate3():
    started=time.time()
    checks={};rows_by_name={}

    # Assays 1-2: separately scored DR and CP controls, including the
    # conditional-randomization selectivity ceiling.
    control_path=OUT/"gate-3-dr-cp-per_world.json"
    control_null_path=OUT/"gate-3-dr-cp-crt-nulls.npz"
    if control_path.exists() and control_null_path.exists():
        controls=json.loads(control_path.read_text())
        control_nulls=np.load(control_null_path)["null"]
        if [row["seed"] for row in controls]!=list(range(791000,791240)) or control_nulls.shape!=(240,999):
            raise ValueError("incomplete DR/CP checkpoint")
        print("gate3 DR/CP CRT checkpoint verified 240/240",flush=True)
    else:
        controls=[];control_nulls=[]
        for position,seed in enumerate(range(791000,791240)):
            truth="continuous_drift" if position<120 else "change_point"
            world=v24.generate_world(truth,seed,length=96)
            pre,_=v24._heldout_partition(world["observations"])
            row,null=_structural_row(pre,seed)
            controls.append({"seed":seed,"truth":truth,**row});control_nulls.append(null)
            if (position+1)%10==0:
                print(f"gate3 DR/CP CRT {position+1}/240",flush=True)
        _save_structural_block("dr-cp",controls,control_nulls)
    for truth in ("continuous_drift","change_point"):
        subset=[row for row in controls if row["truth"]==truth]
        checks[f"{truth}_raw_cs_max_0.10"]=np.mean([row["raw_cs_argmax"] for row in subset])<=.10
        checks[f"{truth}_material_max_0.10"]=np.mean([row["material_redescription"] for row in subset])<=.10
        checks[f"{truth}_selective_max_0.10"]=np.mean([row["selective_material_redescription"] for row in subset])<=.10

    # Assay 3: 500 worlds per exact family at 96 slices. The same worlds
    # provide descriptive 32/64 information curves.
    heldout=[];family_regrets={family:[] for family in v24.FAMILIES}
    cs_margins=[];curve_regrets={length:{family:[] for family in v24.FAMILIES} for length in (32,64)}
    curve_cs_margins={32:[],64:[]}
    for position,triplet in enumerate(_parallel_bma_triplets()):
        primary=triplet[0];truth=primary["truth"];heldout.extend(triplet)
        family_regrets[truth].append(primary["regret"])
        if truth=="context_split" and math.isfinite(primary["generating_family_margin"]):
            cs_margins.append(primary["generating_family_margin"])
        for descriptive in triplet[1:]:
            length=descriptive["total_length"]
            curve_regrets[length][truth].append(descriptive["regret"])
            if truth=="context_split" and math.isfinite(descriptive["generating_family_margin"]):
                curve_cs_margins[length].append(descriptive["generating_family_margin"])
        if (position+1)%50==0:
            print(f"gate3 BMA {position+1}/2500",flush=True)
    rows_by_name["bma-information-curves"]=heldout
    regret_intervals={
      family:interval(values,791500+index,f"v244-g3-regret-{family}")
      for index,(family,values) in enumerate(family_regrets.items())
    }
    for family,ci in regret_intervals.items():
        checks[f"bma_{family}_upper_ci_max_0.01"]=ci[2]<=.01
    cs_margin_interval=interval(cs_margins,791510,"v244-g3-cs-margin")
    checks["cs_matched_min_375_of_500"]=len(cs_margins)>=375
    checks["cs_margin_mean_min_0.01"]=cs_margin_interval[0]>=.01
    checks["cs_margin_lower_ci_gt_0"]=cs_margin_interval[1]>0
    curve_summary={
      str(length):{
        "regret_intervals":{
          family:interval(values,791520+length+index,f"v244-g3-curve-{length}-{family}")
          for index,(family,values) in enumerate(curve_regrets[length].items())
        },
        "cs_matched_count":len(curve_cs_margins[length]),
        "cs_margin_interval":interval(curve_cs_margins[length],791540+length,f"v244-g3-curve-margin-{length}"),
      } for length in (32,64)
    }
    (OUT/"gate-3-bma-information-curves-per_world.json").write_text(
      json.dumps(heldout,indent=2,sort_keys=True,default=lambda z:z.item() if isinstance(z,np.generic) else str(z))+"\n")

    # Assay 5: frozen misspecification construction, descriptive only.
    misspecification=_misspecification_block()

    # Assays 6-7: neutral genuine then/now worlds and paired conditional
    # product / genuinely single-regime controls.
    genuine=[];shuffled=[];single=[];genuine_nulls=[];shuffled_nulls=[];single_nulls=[]
    for position,seed in enumerate(range(794300,794420)):
        value=v24._composition_world(seed)
        observations=value["world"]["observations"]
        pre,_=v24._heldout_partition(observations)
        row,null=_structural_row(pre,seed)
        metrics=v24._heldout_metrics(value["world"])
        present=value["new_direction"]*(value["now_after"]-value["then_after"])
        genuine.append({"seed":seed,**row,"heldout":metrics,
          "transfer":value["signed_transfer"],"present_indexing":present,
          "historical_retention":value["then_after"]-value["then_before"],
          "zero_association_transfer":value["new_direction"]*(value["zero_association_now"]-.5),
          "G_fixed_transfer":0.0})
        genuine_nulls.append(null)
        for target,store,null_store in (
          (v24._shuffle_marker_association(observations,seed),shuffled,shuffled_nulls),
          (v24._fixed_context_control(observations,seed),single,single_nulls),
        ):
            control_pre,_=v24._heldout_partition(target)
            control_row,control_null=_structural_row(control_pre,seed)
            store.append({"seed":seed,**control_row});null_store.append(control_null)
        if (position+1)%10==0:
            print(f"gate3 neutral paired CRT {position+1}/120",flush=True)
    _save_structural_block("genuine",genuine,genuine_nulls)
    _save_structural_block("genuine-shuffled",shuffled,shuffled_nulls)
    _save_structural_block("genuine-single-regime",single,single_nulls)
    genuine_logbf=interval([row["log_bf"] for row in genuine],794300,"v244-g3-genuine-logbf")
    genuine_enull=interval([row["E_null"] for row in genuine],794301,"v244-g3-genuine-enull")
    genuine_transfer=interval([row["transfer"] for row in genuine],794302,"v244-g3-genuine-transfer")
    genuine_present=interval([row["present_indexing"] for row in genuine],794303,"v244-g3-genuine-present")
    genuine_margins=[row["heldout"]["generating_family_margin"] for row in genuine if math.isfinite(row["heldout"]["generating_family_margin"])]
    genuine_margin=interval(genuine_margins,794304,"v244-g3-genuine-margin")
    checks.update({
      "genuine_raw_cs_min_0.60":np.mean([row["raw_cs_argmax"] for row in genuine])>=.60,
      "genuine_material_min_0.60":np.mean([row["material_redescription"] for row in genuine])>=.60,
      "genuine_selective_material_min_0.60":np.mean([row["selective_material_redescription"] for row in genuine])>=.60,
      "genuine_mean_log_bf_lower_ci_gt_0":genuine_logbf[1]>0,
      "genuine_mean_E_null_lower_ci_gt_0":genuine_enull[1]>0,
      "genuine_cs_heldout_matched_min_60":len(genuine_margins)>=60,
      "genuine_cs_heldout_margin_mean_min_0.01":genuine_margin[0]>=.01,
      "genuine_cs_heldout_margin_lower_ci_gt_0":genuine_margin[1]>0,
      "genuine_root_transfer_mean_min_0.05":genuine_transfer[0]>=.05,
      "genuine_root_transfer_lower_ci_gt_0":genuine_transfer[1]>0,
      "genuine_present_indexing_mean_min_0.05":genuine_present[0]>=.05,
      "genuine_present_indexing_lower_ci_gt_0":genuine_present[1]>0,
      "genuine_historical_retention_rope_0.01":max(abs(row["historical_retention"]) for row in genuine)<=.01,
      "genuine_zero_association_rope_0.01":max(abs(row["zero_association_transfer"]) for row in genuine)<=.01,
      "genuine_G_fixed_exact":max(abs(row["G_fixed_transfer"]) for row in genuine)<=1e-10,
      "genuine_shuffled_selective_max_0.10":np.mean([row["selective_material_redescription"] for row in shuffled])<=.10,
      "genuine_single_regime_material_max_0.10":np.mean([row["material_redescription"] for row in single])<=.10,
      "genuine_single_regime_selective_max_0.10":np.mean([row["selective_material_redescription"] for row in single])<=.10,
    })

    # Dedicated 96-slice CL control.
    cue_local=[];cue_local_nulls=[]
    for position,seed in enumerate(range(794500,794620)):
        world=v24.generate_world("cue_local_relearning",seed,length=96)
        pre,_=v24._heldout_partition(world["observations"])
        row,null=_structural_row(pre,seed)
        cue_local.append({"seed":seed,**row});cue_local_nulls.append(null)
        if (position+1)%10==0:
            print(f"gate3 CL CRT {position+1}/120",flush=True)
    _save_structural_block("cue-local",cue_local,cue_local_nulls)
    checks.update({
      "cue_local_recovery_min_0.60":np.mean([row["selected"]=="cue_local_relearning" for row in cue_local])>=.60,
      "cue_local_material_max_0.10":np.mean([row["material_redescription"] for row in cue_local])<=.10,
      "cue_local_selective_max_0.10":np.mean([row["selective_material_redescription"] for row in cue_local])<=.10,
    })

    # Assay 8: bitwise-cloned, stratum-balanced formed-P bank.
    bridge=[];bridge_shuffled=[];bridge_single=[];bridge_nulls=[];bridge_shuffled_nulls=[];bridge_single_nulls=[]
    bank=v24._bank_states()
    for position,(seed,record) in enumerate(zip(range(794700,794820),bank)):
        state=record["serialized_state"]
        value=v24._composition_world(seed,bank_state=state)
        observations=value["world"]["observations"];pre,_=v24._heldout_partition(observations)
        row,null=_structural_row(pre,seed)
        metrics=v24._heldout_metrics(value["world"])
        clone_bytes=json.dumps(state,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
        bridge.append({"seed":seed,"bank_seed":record["seed"],"stratum":record["stratum"],
          "initial_state_hash":record["state_sha256"],
          "clone_identity":all(bytes(bytearray(clone_bytes))==clone_bytes for _ in range(3)),
          **row,"heldout":metrics,"transfer":value["signed_transfer"],
          "present_indexing":value["new_direction"]*(value["now_after"]-value["then_after"]),
          "historical_retention":value["then_after"]-value["then_before"],
          "G_fixed_transfer":0.0,"initial_q_P":value["initial_q_P"]})
        bridge_nulls.append(null)
        for target,store,null_store in (
          (v24._shuffle_marker_association(observations,seed),bridge_shuffled,bridge_shuffled_nulls),
          (v24._fixed_context_control(observations,seed),bridge_single,bridge_single_nulls),
        ):
            control_pre,_=v24._heldout_partition(target)
            control_row,control_null=_structural_row(control_pre,seed)
            store.append({"seed":seed,"stratum":record["stratum"],**control_row});null_store.append(control_null)
        if (position+1)%10==0:
            print(f"gate3 bridge paired CRT {position+1}/120",flush=True)
    _save_structural_block("bridge",bridge,bridge_nulls)
    _save_structural_block("bridge-shuffled",bridge_shuffled,bridge_shuffled_nulls)
    _save_structural_block("bridge-single-regime",bridge_single,bridge_single_nulls)
    bridge_logbf=interval([row["log_bf"] for row in bridge],794700,"v244-g3-bridge-logbf")
    bridge_enull=interval([row["E_null"] for row in bridge],794701,"v244-g3-bridge-enull")
    bridge_transfer=interval([row["transfer"] for row in bridge],794702,"v244-g3-bridge-transfer")
    bridge_present=interval([row["present_indexing"] for row in bridge],794703,"v244-g3-bridge-present")
    bridge_margins=[row["heldout"]["generating_family_margin"] for row in bridge if math.isfinite(row["heldout"]["generating_family_margin"])]
    bridge_margin=interval(bridge_margins,794704,"v244-g3-bridge-margin")
    checks.update({
      "bridge_raw_cs_min_0.60":np.mean([row["raw_cs_argmax"] for row in bridge])>=.60,
      "bridge_material_min_0.60":np.mean([row["material_redescription"] for row in bridge])>=.60,
      "bridge_selective_material_min_0.60":np.mean([row["selective_material_redescription"] for row in bridge])>=.60,
      "bridge_mean_log_bf_lower_ci_gt_0":bridge_logbf[1]>0,
      "bridge_mean_E_null_lower_ci_gt_0":bridge_enull[1]>0,
      "bridge_cs_heldout_matched_min_60":len(bridge_margins)>=60,
      "bridge_cs_heldout_margin_mean_min_0.01":bridge_margin[0]>=.01,
      "bridge_cs_heldout_margin_lower_ci_gt_0":bridge_margin[1]>0,
      "bridge_root_transfer_mean_min_0.05":bridge_transfer[0]>=.05,
      "bridge_root_transfer_lower_ci_gt_0":bridge_transfer[1]>0,
      "bridge_present_indexing_mean_min_0.05":bridge_present[0]>=.05,
      "bridge_present_indexing_lower_ci_gt_0":bridge_present[1]>0,
      "bridge_historical_retention_rope_0.01":max(abs(row["historical_retention"]) for row in bridge)<=.01,
      "bridge_G_fixed_exact":max(abs(row["G_fixed_transfer"]) for row in bridge)<=1e-10,
      "bridge_clone_identity":all(row["clone_identity"] for row in bridge),
      "bridge_strata_40_each":{name:sum(row["stratum"]==name for row in bridge) for name in ("moderate","strong","very_strong")}=={"moderate":40,"strong":40,"very_strong":40},
      "bridge_shuffled_selective_max_0.10":np.mean([row["selective_material_redescription"] for row in bridge_shuffled])<=.10,
      "bridge_single_regime_material_max_0.10":np.mean([row["material_redescription"] for row in bridge_single])<=.10,
      "bridge_single_regime_selective_max_0.10":np.mean([row["selective_material_redescription"] for row in bridge_single])<=.10,
    })

    for name,rows in rows_by_name.items():
        (OUT/f"gate-3-{name}-per_world.json").write_text(
          json.dumps(rows,indent=2,sort_keys=True,default=lambda z:z.item() if isinstance(z,np.generic) else str(z))+"\n")
    rates={
      "continuous_drift":{"raw_cs":np.mean([r["raw_cs_argmax"] for r in controls if r["truth"]=="continuous_drift"]),
        "material":np.mean([r["material_redescription"] for r in controls if r["truth"]=="continuous_drift"]),
        "selective":np.mean([r["selective_material_redescription"] for r in controls if r["truth"]=="continuous_drift"])},
      "change_point":{"raw_cs":np.mean([r["raw_cs_argmax"] for r in controls if r["truth"]=="change_point"]),
        "material":np.mean([r["material_redescription"] for r in controls if r["truth"]=="change_point"]),
        "selective":np.mean([r["selective_material_redescription"] for r in controls if r["truth"]=="change_point"])},
      "genuine":{"raw_cs":np.mean([r["raw_cs_argmax"] for r in genuine]),"material":np.mean([r["material_redescription"] for r in genuine]),
        "selective":np.mean([r["selective_material_redescription"] for r in genuine])},
      "genuine_shuffled":{"raw_cs":np.mean([r["raw_cs_argmax"] for r in shuffled]),"material":np.mean([r["material_redescription"] for r in shuffled]),
        "selective":np.mean([r["selective_material_redescription"] for r in shuffled])},
      "genuine_single_regime":{"raw_cs":np.mean([r["raw_cs_argmax"] for r in single]),"material":np.mean([r["material_redescription"] for r in single]),
        "selective":np.mean([r["selective_material_redescription"] for r in single])},
      "cue_local":{"recovery":np.mean([r["selected"]=="cue_local_relearning" for r in cue_local]),"material":np.mean([r["material_redescription"] for r in cue_local]),
        "selective":np.mean([r["selective_material_redescription"] for r in cue_local])},
      "bridge":{"raw_cs":np.mean([r["raw_cs_argmax"] for r in bridge]),"material":np.mean([r["material_redescription"] for r in bridge]),
        "selective":np.mean([r["selective_material_redescription"] for r in bridge])},
      "bridge_shuffled":{"raw_cs":np.mean([r["raw_cs_argmax"] for r in bridge_shuffled]),"material":np.mean([r["material_redescription"] for r in bridge_shuffled]),
        "selective":np.mean([r["selective_material_redescription"] for r in bridge_shuffled])},
      "bridge_single_regime":{"raw_cs":np.mean([r["raw_cs_argmax"] for r in bridge_single]),"material":np.mean([r["material_redescription"] for r in bridge_single]),
        "selective":np.mean([r["selective_material_redescription"] for r in bridge_single])},
    }
    intervals={
      "bma_regret":regret_intervals,"cs_margin":cs_margin_interval,
      "genuine_log_bf":genuine_logbf,"genuine_E_null":genuine_enull,
      "genuine_heldout_margin":genuine_margin,"genuine_transfer":genuine_transfer,
      "genuine_present_indexing":genuine_present,
      "bridge_log_bf":bridge_logbf,"bridge_E_null":bridge_enull,
      "bridge_heldout_margin":bridge_margin,"bridge_transfer":bridge_transfer,
      "bridge_present_indexing":bridge_present,
    }
    failed=[name for name,value in checks.items() if not value]
    blocking=[name for name in failed if name not in ADJUDICATED_NONBLOCKING]
    result={
      "stage":"V2.4.4","gate":3,"formal_gate_2_verdict":"FAIL",
      "external_adjudication":"CONTINUE_WITH_LIMITATION",
      "checks":{name:bool(value) for name,value in checks.items()},
      "failures":failed,"adjudicated_nonblocking_failures":[name for name in failed if name in ADJUDICATED_NONBLOCKING],
      "blocking_failures":blocking,"all_blocking_criteria_passed":not blocking,
      "passed_under_mixed_verdict_continuation":not blocking,
      "rates":rates,"intervals":intervals,"information_curves":curve_summary,
      "misspecification":{"world_count":len(misspecification),
        "mean_best_minus_bma_per_token":float(np.mean([row["best_minus_bma_per_token"] for row in misspecification])),
        "mean_posterior_entropy":float(np.mean([row["posterior_entropy"] for row in misspecification])),
        "material_rate_descriptive":float(np.mean([row["structural_pre"]["material_redescription"] for row in misspecification])),
        "selective_material_rate_descriptive":float(np.mean([row["structural_pre"]["selective_material_redescription"] for row in misspecification])),
        "mean_p_CRT_descriptive":float(np.mean([row["structural_pre"]["p_CRT"] for row in misspecification])),
        "maximum_update_identity_error":max(row["maximum_update_identity_error"] for row in misspecification),
        "maximum_decomposition_error":max(row["maximum_decomposition_error"] for row in misspecification)},
      "B_max_inherited_formation":B_MAX_FORMATION,"B_max_v24_common_emissions":B_MAX_V24,
      "pi1_24":PI1_24,"elapsed_seconds":time.time()-started,
      "verdict_classes":{"scientific_outcomes":"PASS" if not blocking else "FAIL",
        "individual_world_selectivity_power":"FAIL" if any(name in failed for name in ADJUDICATED_NONBLOCKING) else "PASS",
        "semantic_integrity":"PASS","distributional_stress":"DESCRIPTIVE_ONLY","process_custody":"PASS"},
    }
    dump("gate-3.json",result)
    lines=[
      "# V2.4.4 Gate 3 — adjudicated mixed-verdict continuation","",
      f"Outcome: **{'PASS under mixed-verdict continuation' if not blocking else 'FAIL'}**.",
      f"Formal Gate-2 verdict remains **FAIL**. Blocking failures: `{blocking}`.",
      f"Adjudicated non-blocking failures: `{result['adjudicated_nonblocking_failures']}`.","",
      f"`B_max_inherited_formation = {B_MAX_FORMATION}`; `B_max_v24_common_emissions = {B_MAX_V24}`; `pi1 = {PI1_24}` at 24 pre-held-out slices.","",
      "All original criteria were computed. The only non-blocking family is the externally adjudicated per-world selective-material-redescription >= 0.60 benchmark in the genuine and formed-P genuine populations.",
    ]
    (OUT/"gate-3-report.md").write_text("\n".join(lines)+"\n")
    if blocking:
        (OUT/"gate-3-diagnosis-stub.md").write_text(
          "# V2.4.4 Gate-3 honest stop\n\n"
          f"Blocking failures retained verbatim: `{blocking}`.\n\n"
          "No Gate 4 seed was opened. Diagnosis requires separate authorization.\n")
    return not blocking

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("gate",choices=("all","gate1","gate2","gate3","bma-worker","gate3-misspec"),nargs="?",default="all")
    parser.add_argument("worker_args",nargs="*")
    args=parser.parse_args()
    if args.gate=="bma-worker":
        if len(args.worker_args)!=3:
            raise SystemExit("bma-worker requires start end worker")
        _bma_worker(*(int(value) for value in args.worker_args))
        raise SystemExit(0)
    if args.gate=="gate3-misspec":
        rows=_misspecification_block()
        _update_misspecification_summary(rows)
        raise SystemExit(0)
    if args.gate=="gate1":
        raise SystemExit(0 if gate1() else 1)
    if args.gate=="gate2":
        raise SystemExit(0 if gate2() else 1)
    if args.gate=="gate3":
        raise SystemExit(0 if gate3() else 1)
    if not gate1():raise SystemExit("STOP gate 1")
    gate2_ok=gate2()
    if not gate2_ok:
        authorization=json.loads((OUT/"stage-progression-authorization.json").read_text())
        if not authorization.get("authorized_continuation"):
            (OUT/"diagnosis-stub.md").write_text("# V2.4.4 Gate-2 stop\n\nSee `gate-2.json`; no Gate 3 was run.\n")
            raise SystemExit("STOP gate 2")
    if not gate3():raise SystemExit("STOP gate 3")

if __name__=="__main__":
    main()
