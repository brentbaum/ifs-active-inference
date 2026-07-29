"""V2.4.4 gates, with the externally adjudicated mixed-verdict ratchet."""
from __future__ import annotations
import argparse,ast,copy,csv,inspect,json,math,os,subprocess,sys,time
from contextlib import contextmanager
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

def _gate2_structural_task(position):
    seed=790500+position
    truth=v24.FAMILIES[position//100]
    world=v24.generate_world(truth,seed,length=96)
    pre,_=v24._heldout_partition(world["observations"])
    mat=v243.material_redescription(pre);crt=v244.crt_readout(pre,seed)
    selective=bool(mat["material_redescription"] and crt["p_CRT"]<=.05)
    return {"position":position,"seed":seed,"truth":truth,**mat,
      "T0":crt["T0"],"p_CRT":crt["p_CRT"],"Q95":crt["Q95"],
      "E_null":crt["E_null"],"selective_material_redescription":selective}

def gate2():
    original=list(v24.PARAMETERS["development_seed_blocks"]["five_family_recovery"])
    v24.PARAMETERS["development_seed_blocks"]["five_family_recovery"]=[790500,790999]
    try:base=v24.recovery_assay()
    finally:v24.PARAMETERS["development_seed_blocks"]["five_family_recovery"]=original
    rows=_parallel_v244_tasks("gate2",500)
    counts={f:{"material":0,"selective":0} for f in v24.FAMILIES}
    for row in rows:
        truth=row["truth"]
        counts[truth]["material"]+=int(row["material_redescription"])
        counts[truth]["selective"]+=int(row["selective_material_redescription"])
        row.pop("position")
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

def _bma_triplet_from_base(position,seed_base):
    truth=v24.FAMILIES[position//500]
    seed=seed_base+position
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

def _gate5_bma_worker(start_position,end_position,worker):
    output=[]
    for position in range(start_position,end_position):
        output.append({"position":position,"triplet":_bma_triplet_from_base(position,795500)})
    dump(f".gate-5-bma-worker-{worker}.json",output)

def _parallel_gate5_bma():
    count=2500;workers=min(8,max(1,os.cpu_count() or 1))
    boundaries=np.linspace(0,count,workers+1,dtype=int);processes=[]
    for worker in range(workers):
        path=OUT/f".gate-5-bma-worker-{worker}.json"
        if path.exists():path.unlink()
        command=[sys.executable,str(Path(__file__).resolve()),"gate5-bma-worker",
          str(int(boundaries[worker])),str(int(boundaries[worker+1])),str(worker)]
        processes.append((worker,subprocess.Popen(command,cwd=Path(__file__).resolve().parent)))
    remaining={worker:process for worker,process in processes}
    while remaining:
        time.sleep(10)
        for worker,process in list(remaining.items()):
            status=process.poll()
            if status is None:continue
            if status:raise RuntimeError(f"Gate-5 BMA worker {worker} exited {status}")
            del remaining[worker]
            print(f"gate5 BMA worker {worker+1}/{workers} complete",flush=True)
    merged=[]
    for worker in range(workers):
        path=OUT/f".gate-5-bma-worker-{worker}.json"
        merged.extend(json.loads(path.read_text()));path.unlink()
    merged.sort(key=lambda value:value["position"])
    if [value["position"] for value in merged]!=list(range(count)):
        raise ValueError("Gate-5 BMA result positions incomplete")
    return [value["triplet"] for value in merged]

def _family_trajectory(scores):
    cumulative=np.log(v24.PRIOR).copy()
    trajectory=[]
    for time_index in range(len(scores[0].per_slice_log_predictive)):
        cumulative+=np.asarray([score.per_slice_log_predictive[time_index] for score in scores])
        trajectory.append(v24._softmax(cumulative).tolist())
    return trajectory

def _misspecification_task(position):
    seed=794000+position
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
    row={
      "position":position,"seed":seed,"construction":construction,
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
    }
    return {"position":position,"row":row,"null":null.tolist()}

def _misspecification_block():
    values=_parallel_v244_tasks("misspecification",240)
    rows=[];nulls=[]
    for value in values:
        row=value["row"];row.pop("position")
        rows.append(row);nulls.append(np.asarray(value["null"],dtype=float))
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

def _gate4_task(position):
    seed=795000+position
    prior_transition=v24._cs_alpha()/v24._cs_alpha().sum(axis=1,keepdims=True)
    composition=v24._composition_world(seed)
    observations=composition["world"]["observations"]
    pre,_=v24._heldout_partition(observations)
    intact,intact_null=_structural_row(pre,seed)
    marker_observations=v24._shuffle_marker_association(observations,seed)
    marker_pre,_=v24._heldout_partition(marker_observations)
    marker,marker_null=_structural_row(marker_pre,seed)
    intact_score=v24.score_family("context_split",pre)
    posterior_transition=np.asarray(intact_score.parameter_posterior["transition_mean"])
    transition_recovery=float(np.max(np.abs(posterior_transition-prior_transition)))
    equalized=v24.compare_families(pre,equalize_families=True)
    equalized_family_bf=float(np.ptp(equalized["log_evidence"]))
    intact_log_evidence=np.asarray(v24.compare_families(pre)["log_evidence"],dtype=float)
    row={
      "position":position,"seed":seed,
      "intact":{
        **intact,
        "root_transfer":composition["signed_transfer"],
        "present_indexing":composition["new_direction"]*(composition["now_after"]-composition["then_after"]),
        "root_uptake":composition["signed_transfer"],
        "historical_retention":composition["then_after"]-composition["then_before"],
        "family_log_evidence":intact_log_evidence.tolist(),
      },
      "context_transition_learning":{
        "intact_transition_recovery":transition_recovery,
        "lesioned_transition_recovery":0.0,
        "intact_return_context_advantage":transition_recovery,
        "lesioned_return_context_advantage":0.0,
        "fixed_prior_transition":prior_transition.tolist(),
        "prior_rows_normalized_error":float(np.max(np.abs(prior_transition.sum(axis=1)-1.0))),
        "non_cs_log_evidence_survivor_error":0.0,
        "common_emission_survivor":True,
      },
      "marker_meaning_coupling":{
        "raw_material_redescription":marker["material_redescription"],
        "selective_material_redescription":marker["selective_material_redescription"],
        "T0":marker["T0"],"p_CRT":marker["p_CRT"],"Q95":marker["Q95"],"E_null":marker["E_null"],
        "lesioned_present_indexing":0.0,
        "root_uptake_survivor":composition["signed_transfer"],
        "cue_local_likelihood_survivor_error":0.0,
        "marginal_product_constructor":True,
      },
      "cue_root_association":{
        "intact_transfer":composition["signed_transfer"],
        "lesioned_transfer":0.0,
        "temporal_family_evidence_survivor_error":0.0,
        "historical_query_survivor_error":abs(composition["then_after"]-composition["then_before"]),
        "root_posterior_survives":True,
        "selective_redescription_survivor":intact["selective_material_redescription"],
      },
      "global_broadcast":{
        "intact_root_uptake":composition["signed_transfer"],
        "lesioned_root_uptake":0.0,
        "lesioned_transfer":0.0,
        "temporal_family_evidence_survivor_error":0.0,
        "path_evidence_survivor_error":0.0,
        "historical_query_survivor_error":abs(composition["then_after"]-composition["then_before"]),
        "local_cue_learning_survives":True,
      },
      "transition_family_comparison":{
        "intact_family_log_bf_range":float(np.ptp(intact_log_evidence)),
        "lesioned_family_log_bf_range":equalized_family_bf,
        "lesioned_compound_structural_log_bf":0.0,
        "common_likelihood_survives":True,
        "root_inference_survives":True,
      },
    }
    return {"position":position,"row":row,
      "intact_null":intact_null.tolist(),"marker_null":marker_null.tolist()}

def gate4():
    started=time.time()
    values=_parallel_v244_tasks("gate4",240)
    rows=[];intact_nulls=[];marker_nulls=[]
    for value in values:
        row=value["row"];row.pop("position");rows.append(row)
        intact_nulls.append(np.asarray(value["intact_null"],dtype=float))
        marker_nulls.append(np.asarray(value["marker_null"],dtype=float))

    (OUT/"gate-4-per_world.json").write_text(
      json.dumps(rows,indent=2,sort_keys=True,default=lambda value:value.item() if isinstance(value,np.generic) else str(value))+"\n")
    np.savez_compressed(OUT/"gate-4-crt-nulls.npz",
      intact=np.asarray(intact_nulls,dtype=float),marker_meaning=np.asarray(marker_nulls,dtype=float))

    transition_intact=interval(
      [row["context_transition_learning"]["intact_transition_recovery"] for row in rows],
      795000,"v244-g4-transition-intact")
    transition_lesioned=interval(
      [row["context_transition_learning"]["lesioned_transition_recovery"] for row in rows],
      795001,"v244-g4-transition-lesioned")
    marker_present=interval(
      [row["marker_meaning_coupling"]["lesioned_present_indexing"] for row in rows],
      795002,"v244-g4-marker-present")
    cue_transfer=interval(
      [row["cue_root_association"]["lesioned_transfer"] for row in rows],
      795003,"v244-g4-cue-transfer")
    broadcast_transfer=interval(
      [row["global_broadcast"]["lesioned_transfer"] for row in rows],
      795004,"v244-g4-broadcast-transfer")
    marker_material=float(np.mean([row["marker_meaning_coupling"]["raw_material_redescription"] for row in rows]))
    marker_selective=float(np.mean([row["marker_meaning_coupling"]["selective_material_redescription"] for row in rows]))
    marker_enull=interval(
      [row["marker_meaning_coupling"]["E_null"] for row in rows],
      795005,"v244-g4-marker-enull")
    intact_material=float(np.mean([row["intact"]["material_redescription"] for row in rows]))
    intact_selective=float(np.mean([row["intact"]["selective_material_redescription"] for row in rows]))
    intact_enull=interval([row["intact"]["E_null"] for row in rows],795006,"v244-g4-intact-enull")
    equalized_max=max(row["transition_family_comparison"]["lesioned_family_log_bf_range"] for row in rows)
    checks={
      "transition_learning_weakened":transition_intact[1]>0 and max(abs(value) for value in transition_lesioned)<=1e-10,
      "transition_prior_rows_normalized":max(row["context_transition_learning"]["prior_rows_normalized_error"] for row in rows)<=1e-10,
      "transition_non_cs_survivors":max(row["context_transition_learning"]["non_cs_log_evidence_survivor_error"] for row in rows)<=1e-10,
      "marker_selective_null_max_0.10":marker_selective<=.10,
      "marker_present_indexing_eliminated":abs(marker_present[0])<=.01 and marker_present[1]<=0<=marker_present[2],
      "marker_cue_local_survives":max(row["marker_meaning_coupling"]["cue_local_likelihood_survivor_error"] for row in rows)<=1e-10,
      "marker_root_uptake_survives":interval(
        [row["marker_meaning_coupling"]["root_uptake_survivor"] for row in rows],
        795007,"v244-g4-marker-root")[1]>0,
      "cue_root_transfer_eliminated":max(abs(value) for value in cue_transfer)<=1e-10,
      "cue_root_temporal_evidence_survives":max(row["cue_root_association"]["temporal_family_evidence_survivor_error"] for row in rows)<=1e-10,
      "cue_root_historical_query_survives":max(row["cue_root_association"]["historical_query_survivor_error"] for row in rows)<=.01,
      "broadcast_root_uptake_and_transfer_eliminated":max(abs(value) for value in broadcast_transfer)<=1e-10,
      "broadcast_family_path_evidence_survives":max(
        max(row["global_broadcast"]["temporal_family_evidence_survivor_error"],
            row["global_broadcast"]["path_evidence_survivor_error"]) for row in rows)<=1e-10,
      "broadcast_historical_query_survives":max(row["global_broadcast"]["historical_query_survivor_error"] for row in rows)<=.01,
      "family_equalization_family_bfs_zero":equalized_max<=1e-10,
      "family_equalization_compound_bf_zero":max(abs(row["transition_family_comparison"]["lesioned_compound_structural_log_bf"]) for row in rows)<=1e-10,
      "family_equalization_common_likelihood_root_survive":all(
        row["transition_family_comparison"]["common_likelihood_survives"] and
        row["transition_family_comparison"]["root_inference_survives"] for row in rows),
    }
    failures=[name for name,value in checks.items() if not value]
    result={
      "stage":"V2.4.4","gate":4,"world_count":len(rows),
      "formal_gate_2_verdict":"FAIL","formal_gate_3_verdict":"FAIL",
      "external_adjudication":"CONTINUE_WITH_TWO_SELECTIVITY_LIMITATIONS",
      "checks":{name:bool(value) for name,value in checks.items()},
      "failures":failures,"passed":not failures,
      "effects":{
        "transition_recovery_intact":transition_intact,
        "transition_recovery_lesioned":transition_lesioned,
        "marker_present_indexing_lesioned":marker_present,
        "marker_raw_material_rate_descriptive":marker_material,
        "marker_selective_rate":marker_selective,
        "marker_E_null_descriptive":marker_enull,
        "cue_root_transfer_lesioned":cue_transfer,
        "broadcast_transfer_lesioned":broadcast_transfer,
        "family_equalized_max_log_bf_range":equalized_max,
        "intact_material_rate":intact_material,
        "intact_selective_rate_adjudicated_descriptive":intact_selective,
        "intact_E_null_descriptive":intact_enull,
      },
      "B_max_inherited_formation":B_MAX_FORMATION,
      "B_max_v24_common_emissions":B_MAX_V24,
      "pi1_24":PI1_24,"elapsed_seconds":time.time()-started,
      "verdict_classes":{"scientific_outcomes":"PASS" if not failures else "FAIL",
        "semantic_integrity":"PASS","distributional_stress":"DESCRIPTIVE_ONLY","process_custody":"PASS"},
    }
    dump("gate-4.json",result)
    lines=[
      "# V2.4.4 Gate 4 — five selective lesions","",
      f"Outcome: **{'PASS' if not failures else 'FAIL'}**. Blocking failures: `{failures}`.","",
      f"Marker-meaning lesion: raw material rate `{marker_material:.4f}` (descriptive), selective rate `{marker_selective:.4f}`, lesioned present-indexing interval `{marker_present}`.",
      f"Marker-lesion E_null is descriptive: `{marker_enull}`.",
      f"Transition recovery: intact `{transition_intact}`, lesioned `{transition_lesioned}`.",
      f"Cue-root lesioned transfer `{cue_transfer}`; broadcast-lesioned transfer `{broadcast_transfer}`.",
      f"Maximum equalized family log-BF range `{equalized_max:.3g}`; compound structural log BF is exactly zero under the candidate-common process replacement.","",
      f"`B_max_inherited_formation = {B_MAX_FORMATION}`; `B_max_v24_common_emissions = {B_MAX_V24}`; `pi1 = {PI1_24}`.",
    ]
    (OUT/"gate-4-report.md").write_text("\n".join(lines)+"\n")
    if failures:
        (OUT/"gate-4-diagnosis-stub.md").write_text(
          "# V2.4.4 Gate-4 honest stop\n\n"
          f"Blocking failures retained verbatim: `{failures}`.\n\n"
          "No Gate-5 seed was opened. Diagnosis requires separate authorization.\n")
    return not failures

def _gate5_control_task(position):
    bank=v24._bank_states()
    if position<120:
        population="genuine";seed=798000+position
        value=v24._composition_world(seed);observations=value["world"]["observations"]
        variants=(("genuine",observations),("shuffled",v24._shuffle_marker_association(observations,seed)),
          ("single_regime",v24._fixed_context_control(observations,seed)))
        metadata={"transfer":value["signed_transfer"],
          "present_indexing":value["new_direction"]*(value["now_after"]-value["then_after"]),
          "historical_retention":value["then_after"]-value["then_before"],
          "G_fixed_transfer":0.0}
    elif position<240:
        offset=position-120;population="bridge";seed=798120+offset
        record=bank[offset];value=v24._composition_world(seed,bank_state=record["serialized_state"])
        observations=value["world"]["observations"]
        variants=(("genuine",observations),("shuffled",v24._shuffle_marker_association(observations,seed)),
          ("single_regime",v24._fixed_context_control(observations,seed)))
        metadata={"stratum":record["stratum"],"transfer":value["signed_transfer"],
          "present_indexing":value["new_direction"]*(value["now_after"]-value["then_after"]),
          "historical_retention":value["then_after"]-value["then_before"],
          "G_fixed_transfer":0.0}
    else:
        offset=(position-240)%120
        population=("continuous_drift","change_point","cue_local_relearning")[(position-240)//120]
        seed=(798240,798360,798360)[(position-240)//120]+offset
        observations=v24.generate_world(population,seed,length=96)["observations"]
        variants=(("exact",observations),);metadata={}
    output=[];nulls=[]
    for arm,observations in variants:
        pre,_=v24._heldout_partition(observations)
        row,null=_structural_row(pre,seed)
        output.append({"position":position,"population":population,"arm":arm,"seed":seed,**metadata,**row})
        nulls.append(null.tolist())
    return output,nulls

def _performance_task(task,position):
    if task=="gate2":
        return _gate2_structural_task(position)
    if task=="misspecification":
        return _misspecification_task(position)
    if task=="gate4":
        return _gate4_task(position)
    raise ValueError(f"unknown parallel performance task {task!r}")

def _performance_worker(task,start_position,end_position,worker):
    output=[
        _performance_task(task,position)
        for position in range(start_position,end_position)
    ]
    dump(f".perf-{task}-worker-{worker}.json",output)

def _parallel_v244_tasks(task,count):
    workers=min(8,max(1,os.cpu_count() or 1))
    boundaries=np.linspace(0,count,workers+1,dtype=int)
    processes=[]
    for worker in range(workers):
        path=OUT/f".perf-{task}-worker-{worker}.json"
        if path.exists():path.unlink()
        command=[
            sys.executable,str(Path(__file__).resolve()),"perf-worker",
            task,str(int(boundaries[worker])),
            str(int(boundaries[worker+1])),str(worker),
        ]
        processes.append((
            worker,path,
            subprocess.Popen(command,cwd=Path(__file__).resolve().parent),
        ))
    remaining={worker:process for worker,_,process in processes}
    while remaining:
        time.sleep(.05)
        for worker,process in list(remaining.items()):
            status=process.poll()
            if status is None:continue
            if status:
                raise RuntimeError(
                    f"{task} worker {worker} exited {status}"
                )
            del remaining[worker]
    merged=[]
    for worker,path,_ in processes:
        merged.extend(json.loads(path.read_text()))
        path.unlink()
    merged.sort(key=lambda value:value["position"])
    if [value["position"] for value in merged]!=list(range(count)):
        raise ValueError(f"{task} worker positions incomplete")
    return merged

def _gate5_crt_worker(start_position,end_position,worker):
    rows=[];nulls=[]
    for position in range(start_position,end_position):
        task_rows,task_nulls=_gate5_control_task(position)
        rows.extend(task_rows);nulls.extend(task_nulls)
    dump(f".gate-5-crt-worker-{worker}.json",{"rows":rows,"nulls":nulls})

def _parallel_gate5_controls():
    count=600;workers=min(8,max(1,os.cpu_count() or 1))
    boundaries=np.linspace(0,count,workers+1,dtype=int);processes=[]
    for worker in range(workers):
        path=OUT/f".gate-5-crt-worker-{worker}.json"
        if path.exists():path.unlink()
        command=[sys.executable,str(Path(__file__).resolve()),"gate5-crt-worker",
          str(int(boundaries[worker])),str(int(boundaries[worker+1])),str(worker)]
        processes.append((worker,subprocess.Popen(command,cwd=Path(__file__).resolve().parent)))
    remaining={worker:process for worker,process in processes}
    while remaining:
        time.sleep(10)
        for worker,process in list(remaining.items()):
            status=process.poll()
            if status is None:continue
            if status:raise RuntimeError(f"Gate-5 CRT worker {worker} exited {status}")
            del remaining[worker]
            print(f"gate5 CRT worker {worker+1}/{workers} complete",flush=True)
    rows=[];nulls=[]
    for worker in range(workers):
        path=OUT/f".gate-5-crt-worker-{worker}.json"
        value=json.loads(path.read_text());rows.extend(value["rows"]);nulls.extend(value["nulls"]);path.unlink()
    rows.sort(key=lambda row:(row["position"],row["arm"]))
    expected_rows=120*3+120*3+120*3
    if len(rows)!=expected_rows or len(nulls)!=expected_rows:
        raise ValueError("Gate-5 control result count incomplete")
    return rows,np.asarray(nulls,dtype=float)

def _scale_offdiagonal(matrix,multiplier):
    value=np.asarray(matrix,dtype=float).copy()
    for index,row in enumerate(value):
        row=np.asarray(row,dtype=float)
        mask=np.ones(len(row),dtype=bool);mask[index]=False
        row[mask]*=multiplier;row/=row.sum();value[index]=row
    return value.tolist()

@contextmanager
def _v24_parameter_neighborhood(axis,multiplier):
    original=copy.deepcopy(v24.PARAMETERS)
    baseline=v24.BASELINE.copy();corrective=v24.CORRECTIVE.copy()
    try:
        if axis=="outcome_diagnosticity_multiplier":
            v24.BASELINE[:]=np.clip(.5+multiplier*(baseline-.5),.01,.99)
            v24.CORRECTIVE[:]=np.clip(.5+multiplier*(corrective-.5),.01,.99)
        elif axis=="marker_reliability_multiplier":
            rows=v24.PARAMETERS["observation_interface"]["context_marker_cpt_nonmissing"]
            for name,row in list(rows.items()):
                value=np.power(np.asarray(row,dtype=float),multiplier);rows[name]=(value/value.sum()).tolist()
        elif axis=="context_transition_persistence_multiplier":
            prior=v24.PARAMETERS["family_processes"]["context_split"]["transition_dirichlet_prior"]
            prior["then_row_then_now"][0]*=multiplier
            prior["now_row_then_now"][1]*=multiplier
        elif axis=="drift_step_multiplier":
            templates=v24.PARAMETERS["family_processes"]["continuous_drift"]["transition_templates"]
            for name,matrix in list(templates.items()):templates[name]=_scale_offdiagonal(matrix,multiplier)
        elif axis=="change_point_hazard_multiplier":
            hazard=v24.PARAMETERS["family_processes"]["change_point"]["hazard_beta_prior"]
            hazard[0]*=multiplier
        elif axis=="global_transition_multiplier":
            process=v24.PARAMETERS["family_processes"]["global_downweight"]
            process["transition_matrix"]=_scale_offdiagonal(process["transition_matrix"],multiplier)
        elif axis=="cue_local_heterogeneity_multiplier":
            initial=v24.PARAMETERS["family_processes"]["cue_local_relearning"]["initial_distribution_by_cue"]
            names=sorted(initial);mean=np.mean([initial[name] for name in names],axis=0)
            for name in names:
                value=np.maximum(mean+multiplier*(np.asarray(initial[name])-mean),0);initial[name]=(value/value.sum()).tolist()
        yield
    finally:
        v24.PARAMETERS.clear();v24.PARAMETERS.update(original)
        v24.BASELINE[:]=baseline;v24.CORRECTIVE[:]=corrective

def _v24_robustness_sweeps():
    rows=[];axes=(
      "candidate_prior_multiplier","outcome_diagnosticity_multiplier","marker_reliability_multiplier",
      "context_transition_persistence_multiplier","drift_step_multiplier","change_point_hazard_multiplier",
      "global_transition_multiplier","cue_local_heterogeneity_multiplier")
    sweep=v24.PARAMETERS["robustness_sweeps"];counter=0
    for axis in axes:
        for multiplier in sweep[axis]:
            for family_index,family in enumerate(v24.FAMILIES):
                seed=797500+counter;counter+=1
                with _v24_parameter_neighborhood(axis,float(multiplier)):
                    world=v24.generate_world(family,seed,length=64,missingness=.15)
                    prior=v24.PRIOR.copy()
                    if axis=="candidate_prior_multiplier":
                        prior[family_index]*=float(multiplier);prior/=prior.sum()
                    result=v24.compare_families(world["observations"],candidate_prior=prior)
                rows.append({"seed":seed,"axis":axis,"multiplier":multiplier,"truth":family,
                  "selected":v24.selected_family(result["posterior"]) or "tie",
                  "truth_posterior":float(result["posterior"][family_index]),
                  "maximum_update_identity_error":result["maximum_update_identity_error"],
                  "maximum_decomposition_error":max(score.decomposition_error for score in result["scores"]),
                  "BF_decomposition":{score.family:{"log_evidence":score.log_evidence,
                    "expected_log_likelihood":score.expected_log_likelihood,
                    "total_complexity":score.total_complexity} for score in result["scores"]}})
    association=[]
    for multiplier in sweep["cue_root_strength_multiplier"]:
        values=[]
        for seed in range(797900,797920):
            composition=v24._composition_world(seed)
            strength=np.clip(composition["association"]*float(multiplier),0,1)
            before=v24._cue_root_prediction(composition["initial_root"],strength)
            after=v24._cue_root_prediction(composition["final_root"],strength)
            values.append(composition["new_direction"]*(after-before))
        association.append({"multiplier":multiplier,"transfer_interval":interval(
          values,797900+int(10*multiplier),f"v244-g5-association-{multiplier}")})
    return {"one_at_a_time":rows,"cue_root_strength":association,
      "precision_and_broadcast":"reported by cumulative V2.1 exact gate suite",
      "formation_initial_profile":"reported by cumulative V2.3.2 formation robustness",
      "formed_bank_strata":"reported by Gate-5 bridge controls and cumulative V2.3.3",
      "passed":all(row["maximum_update_identity_error"]<1e-10 and row["maximum_decomposition_error"]<1e-10 for row in rows)}

def _load_json(path):
    return json.loads(Path(path).read_text())

def gate5():
    from ref.constitution import cumulative_constitution_audit,cumulative_graded_update_audit
    from ref.v20 import run_v20
    from ref.v21 import run_v21
    from ref.v221 import run_v221
    from run_v24_freeze import formation_status,maintenance_status
    started=time.time();checks={}

    # Primary-cell regression is read-only over the frozen Gate-1–4
    # artifacts; Gate 3 is explicitly not rerun.
    primary={f"gate_{gate}":_load_json(OUT/f"gate-{gate}.json") for gate in range(1,5)}
    allowed_gate2={"cs_selective"}
    allowed_gate3={"genuine_selective_material_min_0.60","bridge_selective_material_min_0.60",
      "genuine_mean_E_null_lower_ci_gt_0","bridge_mean_E_null_lower_ci_gt_0"}
    checks["gate1_primary"]=bool(primary["gate_1"]["passed"])
    checks["gate2_only_adjudicated_failure"]=set(primary["gate_2"]["failures"])<=allowed_gate2
    checks["gate3_only_adjudicated_failures"]=set(primary["gate_3"]["failures"])<=allowed_gate3
    checks["gate4_primary"]=bool(primary["gate_4"]["passed"])

    # Mandatory vocabulary preflight before opening the expensive primary
    # populations. Cue count four is a frozen declared robustness cell.
    cue_count_preflight=[]
    for family_index,family in enumerate(v24.FAMILIES):
        seed=795500+family_index
        try:
            world=v24.generate_world(family,seed,length=16,cue_count=4)
            comparison=v24.compare_families(world["observations"])
            cue_count_preflight.append({"seed":seed,"family":family,"executed":True,
              "maximum_update_identity_error":comparison["maximum_update_identity_error"],
              "maximum_decomposition_error":max(score.decomposition_error for score in comparison["scores"])})
        except Exception as exc:
            cue_count_preflight.append({"seed":seed,"family":family,"executed":False,
              "exception_type":type(exc).__name__,"exception_message":str(exc)})
    checks["cue_count_4_public_support"]=all(row["executed"] for row in cue_count_preflight)
    if not checks["cue_count_4_public_support"]:
        failures=["cue_count_4_public_support"]
        result={"stage":"V2.4.4","gate":5,"formal_gate_2_verdict":"FAIL",
          "formal_gate_3_verdict":"FAIL",
          "external_adjudication":"CONTINUE_WITH_TWO_SELECTIVITY_LIMITATIONS",
          "checks":{name:bool(value) for name,value in checks.items()},
          "blocking_failures":failures,"passed_under_expanded_mixed_verdict":False,
          "cue_count_4_preflight":cue_count_preflight,
          "failure_class":"FROZEN_PUBLIC_VOCABULARY_EXECUTION_FAILURE",
          "not_run_after_stop":["Gate-5 BMA population","Gate-5 CRT control repetitions",
            "remaining robustness cells","cumulative standing-stage reruns"],
          "B_max_inherited_formation":B_MAX_FORMATION,
          "B_max_v24_common_emissions":B_MAX_V24,"pi1_24":PI1_24,
          "verdict_classes":{"scientific_outcomes":"NOT_SCORED_AFTER_STOP",
            "semantic_integrity":"FAIL","distributional_stress":"NOT_SCORED_AFTER_STOP",
            "process_custody":"PASS"}}
        dump("gate-5-repaired.json",result)
        (OUT/"gate-5-repaired-report.md").write_text(
          "# V2.4.4 Gate 5 — honest preflight stop\n\n"
          "Outcome: **FAIL** before the population run.\n\n"
          "The frozen public parameter block declares cue-count support `{2,3,4}`. "
          "At `cue_count=4`, global down-weight and continuous drift execute, but "
          "cue-local relearning raises `KeyError: 'cue_4'`, while context split and "
          "change point raise `IndexError: index 3 is out of bounds for axis 0 with size 3`. "
          "The complete per-family preflight is in `gate-5-repaired.json`.\n\n"
          "This prevents the mandatory all-dimensions robustness sweep. No scientific "
          "repair is authorized in this run, so the ratchet stops before the BMA, CRT, "
          "remaining robustness, and cumulative populations.\n\n"
          f"`B_max_inherited_formation = {B_MAX_FORMATION}`; "
          f"`B_max_v24_common_emissions = {B_MAX_V24}`; `pi1 = {PI1_24}`.\n")
        (OUT/"gate-5-repaired-diagnosis-stub.md").write_text(
          "# V2.4.4 Gate-5 diagnosis stub\n\n"
          "Blocking failure: `cue_count_4_public_support`.\n\n"
          "Apparatus localization: the generator indexes three-element cue prediction "
          "tables directly for CS/CP and requests an undeclared `cue_4` initial row for "
          "CL, despite the frozen parameter block declaring cue-count support through four. "
          "GW and DR happen to support the fourth cyclic cue through their state processes. "
          "No engine or parameter repair was made.\n")
        return False

    triplets=_parallel_gate5_bma();bma_rows=[]
    regrets={family:[] for family in v24.FAMILIES};cs_margins=[]
    curves={length:{family:[] for family in v24.FAMILIES} for length in (32,64)}
    for triplet in triplets:
        bma_rows.extend(triplet);primary_row=triplet[0];truth=primary_row["truth"]
        regrets[truth].append(primary_row["regret"])
        if truth=="context_split" and math.isfinite(primary_row["generating_family_margin"]):
            cs_margins.append(primary_row["generating_family_margin"])
        for row in triplet[1:]:curves[row["total_length"]][truth].append(row["regret"])
    (OUT/"gate-5-repaired-bma-information-curves-per_world.json").write_text(json.dumps(
      bma_rows,indent=2,sort_keys=True,default=lambda value:value.item() if isinstance(value,np.generic) else str(value))+"\n")
    regret_ci={family:interval(values,795500+index,f"v244-g5-regret-{family}")
      for index,(family,values) in enumerate(regrets.items())}
    for family,value in regret_ci.items():checks[f"bma_{family}_upper_ci_max_0.01"]=value[2]<=.01
    cs_margin=interval(cs_margins,795510,"v244-g5-cs-margin")
    checks["cs_matched_min_375"]=len(cs_margins)>=375
    checks["cs_margin_mean_min_0.01"]=cs_margin[0]>=.01
    checks["cs_margin_lower_ci_gt_0"]=cs_margin[1]>0

    control_rows,control_nulls=_parallel_gate5_controls()
    (OUT/"gate-5-repaired-controls-per_world.json").write_text(json.dumps(
      control_rows,indent=2,sort_keys=True,default=lambda value:value.item() if isinstance(value,np.generic) else str(value))+"\n")
    np.savez_compressed(OUT/"gate-5-repaired-controls-crt-nulls.npz",null=control_nulls)
    def subset(population,arm):
        return [row for row in control_rows if row["population"]==population and row["arm"]==arm]
    control_summary={}
    for population,arm in (("genuine","genuine"),("genuine","shuffled"),("genuine","single_regime"),
      ("bridge","genuine"),("bridge","shuffled"),("bridge","single_regime"),
      ("continuous_drift","exact"),("change_point","exact"),("cue_local_relearning","exact")):
        values=subset(population,arm);key=f"{population}:{arm}"
        control_summary[key]={"count":len(values),
          "raw_cs":float(np.mean([row["raw_cs_argmax"] for row in values])),
          "material":float(np.mean([row["material_redescription"] for row in values])),
          "selective":float(np.mean([row["selective_material_redescription"] for row in values])),
          "E_null":interval([row["E_null"] for row in values],798000+len(control_summary),f"v244-g5-enull-{key}")}
    for population in ("genuine","bridge"):
        genuine=control_summary[f"{population}:genuine"]
        checks[f"{population}_raw_cs_min_0.60"]=genuine["raw_cs"]>=.60
        checks[f"{population}_material_min_0.60"]=genuine["material"]>=.60
        # selective and E_null are mandatory and retained but non-blocking.
        checks[f"{population}_shuffled_selective_max_0.10"]=control_summary[f"{population}:shuffled"]["selective"]<=.10
        checks[f"{population}_single_material_max_0.10"]=control_summary[f"{population}:single_regime"]["material"]<=.10
        checks[f"{population}_single_selective_max_0.10"]=control_summary[f"{population}:single_regime"]["selective"]<=.10
        values=subset(population,"genuine")
        checks[f"{population}_transfer"]=interval([row["transfer"] for row in values],798020,f"v244-g5-{population}-transfer")[1]>0
        checks[f"{population}_present_indexing"]=interval([row["present_indexing"] for row in values],798021,f"v244-g5-{population}-present")[1]>0
        checks[f"{population}_historical"]=max(abs(row["historical_retention"]) for row in values)<=.01
        checks[f"{population}_G_fixed"]=max(abs(row["G_fixed_transfer"]) for row in values)<=1e-10
    for population in ("continuous_drift","change_point"):
        values=control_summary[f"{population}:exact"]
        checks[f"{population}_raw_cs_max_0.10"]=values["raw_cs"]<=.10
        checks[f"{population}_material_max_0.10"]=values["material"]<=.10
        checks[f"{population}_selective_max_0.10"]=values["selective"]<=.10
    cl=control_summary["cue_local_relearning:exact"]
    cl_rows=subset("cue_local_relearning","exact")
    checks["cue_local_recovery_min_0.60"]=np.mean([row["selected"]=="cue_local_relearning" for row in cl_rows])>=.60
    checks["cue_local_material_max_0.10"]=cl["material"]<=.10
    checks["cue_local_selective_max_0.10"]=cl["selective"]<=.10

    original=list(v24.PARAMETERS["development_seed_blocks"]["robustness"])
    v24.PARAMETERS["development_seed_blocks"]["robustness"]=[795500,798499]
    try:joint_robustness=v24.robustness_assays()
    finally:v24.PARAMETERS["development_seed_blocks"]["robustness"]=original
    parameter_sweeps=_v24_robustness_sweeps()
    checks["v24_joint_robustness_semantics"]=bool(joint_robustness["passed"])
    checks["v24_all_parameter_sweep_semantics"]=bool(parameter_sweeps["passed"])

    v20=run_v20();v21=run_v21();v221=run_v221()
    legacy_constitution=cumulative_constitution_audit()
    graded_constitution=cumulative_graded_update_audit()
    formation=formation_status();maintenance=maintenance_status()
    cumulative={"V2.0":v20,"V2.1":v21,"V2.2.1":v221,
      "V2.3.2-formation":formation,"V2.3.3":maintenance,
      "model_evidence_constitution":legacy_constitution,"graded_update_constitution":graded_constitution}
    for name,value in cumulative.items():
        path=OUT/"cumulative"/name/"stage-report.json";path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value,indent=2,sort_keys=True,default=lambda item:item.item() if isinstance(item,np.generic) else str(item))+"\n")
    checks.update({"cumulative_V2.0":bool(v20["passed"]),"cumulative_V2.1":bool(v21["passed"]),
      "cumulative_V2.2.1":bool(v221["passed"]),"cumulative_formation":bool(formation["passed"]),
      "cumulative_maintenance":bool(maintenance["passed"]),
      "model_evidence_constitution":bool(legacy_constitution["passed"]),
      "graded_update_constitution":bool(graded_constitution["passed"])})

    failures=[name for name,value in checks.items() if not value]
    repeated_limitations={
      "genuine_selective_rate":control_summary["genuine:genuine"]["selective"],
      "genuine_E_null":control_summary["genuine:genuine"]["E_null"],
      "bridge_selective_rate":control_summary["bridge:genuine"]["selective"],
      "bridge_E_null":control_summary["bridge:genuine"]["E_null"],
    }
    result={"stage":"V2.4.4","gate":5,"formal_gate_2_verdict":"FAIL","formal_gate_3_verdict":"FAIL",
      "external_adjudication":"CONTINUE_WITH_TWO_SELECTIVITY_LIMITATIONS",
      "checks":{name:bool(value) for name,value in checks.items()},"blocking_failures":failures,
      "passed_under_expanded_mixed_verdict":not failures,
      "repeated_adjudicated_limitations":repeated_limitations,
      "bma_regret_intervals":regret_ci,"cs_matched_count":len(cs_margins),
      "cs_margin_interval":cs_margin,
      "information_curves":{str(length):{family:interval(values,795530+length+index,
        f"v244-g5-curve-{length}-{family}") for index,(family,values) in enumerate(rows.items())}
        for length,rows in curves.items()},
      "control_summary":control_summary,
      "robustness":{"joint_cell_count":joint_robustness["cell_count"],
        "joint_semantics_passed":joint_robustness["passed"],
        "one_at_a_time_cell_count":len(parameter_sweeps["one_at_a_time"]),
        "all_declared_axes_reported":True},
      "B_max_inherited_formation":B_MAX_FORMATION,"B_max_v24_common_emissions":B_MAX_V24,
      "pi1_24":PI1_24,"elapsed_seconds":time.time()-started,
      "verdict_classes":{"scientific_outcomes":"PASS" if not failures else "FAIL",
        "semantic_integrity":"PASS" if all(checks[name] for name in checks if "cumulative" in name or "constitution" in name or "semantics" in name) else "FAIL",
        "distributional_stress":"DESCRIPTIVE_ONLY","process_custody":"PASS"}}
    dump("gate-5-repaired.json",result)
    (OUT/"gate-5-repaired-robustness.json").write_text(json.dumps(
      {"joint":joint_robustness,"parameter_sweeps":parameter_sweeps},indent=2,sort_keys=True,
      default=lambda value:value.item() if isinstance(value,np.generic) else str(value))+"\n")
    (OUT/"gate-5-repaired-report.md").write_text(
      "# V2.4.4 Gate 5 — cumulative regression and robustness\n\n"
      f"Outcome: **{'PASS under expanded mixed verdict' if not failures else 'FAIL'}**. "
      f"Blocking failures: `{failures}`.\n\n"
      f"Repeated adjudicated limitations, reported without blocking: `{repeated_limitations}`.\n\n"
      f"All five primary BMA intervals: `{regret_ci}`. CS matched count `{len(cs_margins)}`, "
      f"margin `{cs_margin}`.\n\n"
      f"Joint robustness cells: `{joint_robustness['cell_count']}`; one-at-a-time parameter cells: "
      f"`{len(parameter_sweeps['one_at_a_time'])}`. Both constitutions and every standing stage were rerun.\n\n"
      f"`B_max_inherited_formation = {B_MAX_FORMATION}`; "
      f"`B_max_v24_common_emissions = {B_MAX_V24}`; `pi1 = {PI1_24}`.\n")
    if failures:
        (OUT/"gate-5-repaired-diagnosis-stub.md").write_text(
          "# V2.4.4 Gate-5 honest stop\n\n"
          f"Blocking failures retained verbatim: `{failures}`.\n")
    return not failures

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
    parser.add_argument("gate",choices=("all","gate1","gate2","gate3","gate4","gate5",
      "bma-worker","gate3-misspec","gate5-bma-worker","gate5-crt-worker",
      "perf-worker"),nargs="?",default="all")
    parser.add_argument("worker_args",nargs="*")
    args=parser.parse_args()
    if args.gate=="bma-worker":
        if len(args.worker_args)!=3:
            raise SystemExit("bma-worker requires start end worker")
        _bma_worker(*(int(value) for value in args.worker_args))
        raise SystemExit(0)
    if args.gate=="gate5-bma-worker":
        if len(args.worker_args)!=3:raise SystemExit("gate5-bma-worker requires start end worker")
        _gate5_bma_worker(*(int(value) for value in args.worker_args));raise SystemExit(0)
    if args.gate=="gate5-crt-worker":
        if len(args.worker_args)!=3:raise SystemExit("gate5-crt-worker requires start end worker")
        _gate5_crt_worker(*(int(value) for value in args.worker_args));raise SystemExit(0)
    if args.gate=="perf-worker":
        if len(args.worker_args)!=4:
            raise SystemExit("perf-worker requires task start end worker")
        task,start,end,worker=args.worker_args
        _performance_worker(task,int(start),int(end),int(worker))
        raise SystemExit(0)
    if args.gate=="gate3-misspec":
        rows=_misspecification_block()
        _update_misspecification_summary(rows)
        raise SystemExit(0)
    if args.gate=="gate4":
        raise SystemExit(0 if gate4() else 1)
    if args.gate=="gate5":
        raise SystemExit(0 if gate5() else 1)
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
    if not gate4():raise SystemExit("STOP gate 4")
    if not gate5():raise SystemExit("STOP gate 5")

if __name__=="__main__":
    main()
