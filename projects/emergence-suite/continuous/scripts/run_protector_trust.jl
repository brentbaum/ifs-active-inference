using Pkg
using Dates
using Printf

const PROJECT_DIR = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(PROJECT_DIR)

include(joinpath(PROJECT_DIR, "src", "GlobalPrecisionField.jl"))
include(joinpath(PROJECT_DIR, "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(PROJECT_DIR, "src", "IFSBundleInquiry.jl"))
include(joinpath(PROJECT_DIR, "src", "ProtectorTrust.jl"))

using .GlobalPrecisionField
using .ProtectorTrust

const OUTPUT_DIR = joinpath(PROJECT_DIR, "results", "protector_trust")
const FREEZE_LOG = joinpath(OUTPUT_DIR, "freeze-log.md")
const CONFIRMATION_MARKER = joinpath(OUTPUT_DIR, "confirmation-complete.txt")
const EXPLORATORY_MARKER = joinpath(OUTPUT_DIR,
    "exploratory-d-complete.txt")
const EXPLORATORY_SEEDS = collect(14801:14840)
const EXPLORATORY_COMPETENCE_EPISODES = 4
const FROZEN_SUMMARY_SHA256 =
    "4e9e0f923d4bc411e38a845d1b83519bad9bf07b665ae4b4cb13baf41685c7c2"

number(value) = @sprintf("%.4f", value)
percent(value) = @sprintf("%.1f%%", 100value)
verdict(value) = value ? "PASS" : "FAIL"

function write_magic_numbers(config)
    open(joinpath(OUTPUT_DIR, "magic-numbers.md"), "w") do io
        println(io, "# Experiment 47 magic numbers")
        println(io)
        println(io, "Every authored semantic constant in `ProtectorTrustConfig` is listed. Numeric identities (`0`, `1`), array indices, and machine `eps()` are mathematical or language primitives rather than fitted constants.")
        println(io)
        println(io, "| Constant | Value | Rationale |")
        println(io, "|---|---:|---|")
        for (name, value, rationale) in magic_numbers(config)
            rendered = value isa AbstractVector ?
                "$(first(value)):$(last(value))" : string(value)
            println(io, "| `", name, "` | `", rendered, "` | ",
                rationale, " |")
        end
        println(io)
        println(io, "The hope-shift margin and repair comparator `k` were selected at freeze from the pilot and are justified in `freeze-log.md`. No confirmation result was available at that point.")
    end
end

function write_freeze_log(config, pilot)
    open(FREEZE_LOG, "w") do io
        println(io, "# Experiment 47 freeze log")
        println(io)
        println(io, "- Frozen: $(Dates.format(now(), "yyyy-mm-dd HH:MM:SS")).")
        println(io, "- Pilot opened: `14701:14710` (10 worlds).")
        println(io, "- Confirmation remained unopened: `14751:14770` (20 fresh, disjoint worlds).")
        println(io, "- Measures and register names were frozen before confirmation.")
        println(io, "- The §6.5(d) margin was frozen at `$(config.hope_shift_margin)`. The smallest pilot role-preserving shift was `$(number(minimum(row.hope_role_shift for row in pilot)))`; the margin is a conservative round-number lower bound that remains materially above zero.")
        println(io, "- The §6.5(e) comparator was frozen at `k = $(config.repair_smooth_successes_k)`. In every pilot world, repair log-evidence exceeded `k` smooth successes, while `k + 1` smooth successes exceeded repair; this makes `k` the largest pilot-supported integer comparator.")
        println(io, "- Honest pilot failure: with obsolescence penalty `$(config.obsolescence_penalty)`, mean role-preserving shift was `0.1940` but mean obsolescence shift was `0.1508`; §6.5(d) failed because the control exceeded half the role-preserving shift.")
        println(io, "- Threshold and design changes after pilot: **none**. The failed obsolescence control was retained rather than tuned. The provisional hope margin `$(config.hope_shift_margin)` and repair comparator `$(config.repair_smooth_successes_k)` were retained after the pilot checks above.")
        println(io, "- Confirmation access guard: the runner refuses `--confirm` unless this log exists and refuses any rerun after the confirmation marker exists.")
        println(io, "- Frozen register: *configural* is within-bundle statistical organization; *relational* is interpersonal partner policy; protector encounters are *befriending*; *organization* and *carrier* retain the shared §2 meanings. No carrier construct is introduced in this experiment.")
    end
end

function config_record(config)
    return (; (name => getfield(config, name)
        for name in fieldnames(ProtectorTrustConfig))...)
end

function write_report(config, pilot_summary, pilot_rows;
        confirmation_summary = nothing, confirmation_rows = NamedTuple[])
    confirmed = !isnothing(confirmation_summary)
    open(joinpath(OUTPUT_DIR, "report.md"), "w") do io
        println(io, "# Experiment 47: protector trust")
        println(io)
        println(io, "## Design")
        println(io)
        println(io, "The construction extends the Experiment 43 four-channel protector bundle (`self`, `world`, `policy`, `outcome`) and its joint conditional table with three learned forecasts: tolerated versus flooding/collapse for contact, shared system competence if protection relaxes, and a latent partner policy type (instrumental versus relational). Evidence updates these forecasts by Bayesian likelihood ratios. The public `TrustEvidence` stream is the reuse point for Experiment 49: dyadic scaffolding can shape evidence before it enters the same update function.")
        println(io)
        println(io, "Permission is a soft expected-cost choice among contact-enabling and protective policies. Contact risk is computed from all three posterior forecasts; stakes multiply that risk only inside policy evaluation. Counterfactual futures are additional representable policies. Therefore permission is neither stored in nor identified with any posterior.")
        println(io)
        println(io, "### Register guards")
        println(io)
        println(io, "*Configural* is used only for within-bundle statistical organization. *Relational* names an interpersonal contact-policy type. Protector contact is *befriending*, not witnessing. *Organization* retains the shared §2 definition: the bundle, couplings, precisions, and field profile. *Carrier* would mean independently parameterized substrate; no carrier variable appears here. These labels and readouts were fixed before results.")
        println(io)
        println(io, "### Design decisions")
        println(io)
        println(io, "- One seed is one paired world. All arms within a seed share the same jitter; contrasts change only the named manipulation.")
        println(io, "- §6.4(a)'s “observationally identical until refusal” is literal: pre-refusal observations have no type-dependent likelihood and leave both partner posteriors at `0.5`. Accuracy is posterior mass assigned to the true type. Discrimination and trust growth are separate columns; pressuring increases discrimination while decreasing relational trust.")
        println(io, "- §6.5(b)'s “stakes-attributable permission variance” is the partial variance fraction: reduction in posterior-only regression residual sum of squares after adding the paired stakes indicator. Posterior values are identical within each stakes pair.")
        println(io, "- §6.4(c)'s evidence label is held exactly constant (`tolerated contact`) across framings. Local framing updates only situation 1; shared-cause framing updates system competence. Transfer is permission change in untested situation 2. Because the label has zero variance by construction, its incremental regression contribution is exactly zero.")
        println(io, "- §6.4(d)'s future is an added contact-enabling policy. The role-preserving and obsolescence variants use identical trust posteriors and evidence; only future role value differs.")
        println(io, "- §6.4(e)'s diagnosticity is a failure-attribution log-evidence magnitude. “Asymmetry iff high” means one failure outweighs one smooth success in every high-diagnosticity world and in no low-diagnosticity world. Repair is compared with the frozen integer `k` on the same log-evidence scale.")
        println(io, "- “Remaining” is used rather than withdrawal for the relational refusal response; the instrumental contrast is pressure. This chooses one of the spec's allowed instrumental behaviors and keeps direction of trust change unambiguous.")
        println(io, "- The pilot exposed a weak obsolescence control at penalty `$(config.obsolescence_penalty)`. It was retained unchanged through confirmation under the no-tuning rule.")
        println(io)
        println(io, "### Capacity and matching notes")
        println(io)
        println(io, "All paired contrasts use the same three posterior state variables, priors, likelihood families, evidence budget, decision temperature, and base Experiment 43 bundle. Arm (a) partner types receive identical pre-refusal streams. Arm (b) changes only stakes after inference. Arm (c) reuses the same outcome observations and changes only their graphical attribution. Arm (d) reuses one frozen posterior snapshot and changes only the policy set. Arm (e) uses the same success and repair evidence scales while changing only failure diagnosticity. This is capacity and marginal matching by construction, not an ablation that changes available evidence.")
        println(io)
        check = self_check(config)
        println(io)
        println(io, "Structural audit: Experiment 43 channels match = `$(check.channels_match_experiment_43)`; base conditional rows normalized = `$(check.base_bundle_normalized)`; stakes absent from `TrustEvidence` = `$(check.stakes_absent_from_evidence)`; permission evaluation leaves posteriors unchanged = `$(check.permission_does_not_update)`; seed blocks disjoint = `$(check.seed_blocks_disjoint)`.")
        println(io)
        println(io, "## Pilot")
        println(io)
        println(io, "Ten worlds (`14701:14710`) ran before freeze.")
        println(io)
        println(io, "The pilot passed (a), (b), (c), and (e), but failed (d): role-preserving shift was `0.1940` and obsolescence shift `0.1508`. The failure was frozen unchanged.")
        println(io)
        println(io, "- Refusal: no-refusal accuracy `$(number(pilot_summary.refusal.no_refusal_accuracy))`; after two refusals `$(number(pilot_summary.refusal.after_two_refusals_accuracy))`; remaining trust growth `$(number(pilot_summary.refusal.mean_remaining_trust_growth))`; pressuring trust growth `$(number(pilot_summary.refusal.mean_pressuring_trust_growth))`.")
        println(io, "- Permission/stakes: posterior-only residual variance explained by stakes `$(number(pilot_summary.permission_stakes.posterior_only_residual_variance_explained_by_stakes))`; mean permission gap `$(number(pilot_summary.permission_stakes.mean_permission_gap))`.")
        println(io, "- Transfer: inferred-variable tracking in `$(pilot_summary.transfer.worlds_tracking_inferred_variable)/10`; mean local/shared transfer `$(number(pilot_summary.transfer.mean_local_transfer))` / `$(number(pilot_summary.transfer.mean_shared_transfer))`.")
        println(io, "- Hope: mean role-preserving shift `$(number(pilot_summary.hope.mean_role_shift))`; obsolescence shift `$(number(pilot_summary.hope.mean_obsolescence_shift))`; maximum posterior change `$(pilot_summary.hope.maximum_posterior_change)`.")
        println(io, "- Rupture: high/low diagnosticity asymmetry in `$(pilot_summary.rupture.high_diagnosticity_asymmetry_worlds)/10` and `$(pilot_summary.rupture.low_diagnosticity_asymmetry_worlds)/10`; repair exceeded `k=$(config.repair_smooth_successes_k)` smooth successes in `$(pilot_summary.rupture.repair_exceeds_k_worlds)/10`.")
        println(io)
        println(io, "## Freeze log")
        println(io)
        if isfile(FREEZE_LOG)
            println(io, "The pilot was reviewed and the hope margin (`$(config.hope_shift_margin)`) and repair comparator (`k=$(config.repair_smooth_successes_k)`) were frozen before confirmation. No threshold changed. Full rationale and the access guard are in `freeze-log.md`.")
        else
            println(io, "Not frozen. Confirmation is blocked.")
        end
        println(io)
        println(io, "## Confirmatory results")
        println(io)
        if !confirmed
            println(io, "The confirmatory block has not been opened.")
        else
            cs = confirmation_summary
            println(io, "Twenty fresh worlds (`14751:14770`) ran after freeze; the seed set is disjoint from the pilot.")
            println(io)
            println(io, "- **(a) Refusal discrimination:** no-refusal accuracy `$(number(cs.refusal.no_refusal_accuracy))`; after two refusals `$(number(cs.refusal.after_two_refusals_accuracy))`. Pre-refusal equality held in `$(cs.refusal.pre_refusal_equivalence_worlds)/20`. Mean trust growth was `$(number(cs.refusal.mean_remaining_trust_growth))` after remaining and `$(number(cs.refusal.mean_pressuring_trust_growth))` after pressure.")
            println(io, "- **(b) Permission ≠ trust:** adding stakes explained `$(percent(cs.permission_stakes.posterior_only_residual_variance_explained_by_stakes))` of posterior-only residual permission variance; all `$(cs.permission_stakes.matched_posterior_worlds)/20` stakes pairs had identical posteriors. Mean low-minus-high-stakes permission was `$(number(cs.permission_stakes.mean_permission_gap))`.")
            println(io, "- **(c) Transfer by inferred variable:** `$(cs.transfer.worlds_tracking_inferred_variable)/20` worlds transferred more under shared-cause inference. Mean transfer was local `$(number(cs.transfer.mean_local_transfer))`, shared `$(number(cs.transfer.mean_shared_transfer))`; evidence-label incremental variance was `$(cs.transfer.evidence_label_incremental_variance)`.")
            println(io, "- **(d) Hope merchant:** role-preserving mean permission shift `$(number(cs.hope.mean_role_shift))` against frozen margin `$(config.hope_shift_margin)`; obsolescence shift `$(number(cs.hope.mean_obsolescence_shift))`; maximum posterior change `$(cs.hope.maximum_posterior_change)`.")
            println(io, "- **(e) Conditional rupture asymmetry:** high diagnosticity produced asymmetry in `$(cs.rupture.high_diagnosticity_asymmetry_worlds)/20`, low in `$(cs.rupture.low_diagnosticity_asymmetry_worlds)/20`; repair exceeded `k=$(cs.rupture.k)` smooth successes in `$(cs.rupture.repair_exceeds_k_worlds)/20`.")
            println(io)
            println(io, "### Verdict against §6.5")
            println(io)
            println(io, "1. (a) `$(verdict(cs.criteria.refusal_discrimination))` — chance ±`$(config.chance_tolerance)` without refusal and ≥ `$(config.refusal_accuracy_threshold)` after two refusals.")
            println(io, "2. (b) `$(verdict(cs.criteria.permission_not_trust))` — stakes-attributable variance ≥ `$(config.stakes_variance_threshold)` with matched posteriors.")
            println(io, "3. (c) `$(verdict(cs.criteria.transfer_by_inferred_variable))` — inferred-variable tracking in ≥ `$(config.transfer_world_threshold)/20`, with no evidence-label increment.")
            println(io, "4. (d) `$(verdict(cs.criteria.hope_merchant))` — role shift ≥ `$(config.hope_shift_margin)`, posteriors flat, obsolescence ≤ half the role shift.")
            println(io, "5. (e) `$(verdict(cs.criteria.conditional_rupture))` — asymmetry iff diagnosticity high and repair > `k=$(config.repair_smooth_successes_k)` smooth successes.")
            println(io)
            println(io, "Overall frozen-criterion verdict: **$(cs.all_criteria_pass ? "all five construction criteria passed" : "one or more construction criteria failed")**.")
        end
        println(io)
        println(io, "## Interpretation")
        println(io)
        if !confirmed
            println(io, "Pilot results are calibration only and license no confirmatory claim.")
        else
            cs = confirmation_summary
            if cs.all_criteria_pass
                println(io, "The implemented construction reproduces all five qualitative trust claims under its authored priors, likelihoods, graphical framings, and expected-cost policy. It shows that the claims can coexist computationally: respected refusal can inform a partner model, trust and permission can dissociate, transfer can follow a shared inferred cause, a future can alter policy without rewriting evidence, and rupture asymmetry can depend on attribution. This is an existence result inside the construction, not evidence about clinical effects, biological mechanisms, or the ontology of parts.")
            else
                println(io, "The construction failed at least one frozen criterion. Specifically, the role-preserving future shifted permission with flat posteriors, but the obsolescence control also shifted it too strongly; the full hope-merchant criterion is therefore not reproduced by this implementation.")
            end
            println(io)
            println(io, "The strongest scope limitation is that the likelihoods, causal framing, policy utilities, and diagnosticity regimes are authored. The model infers posterior values and makes permission decisions from them, but it does not learn the model class or utility function. Experiment 49 may feed dyadic scaffolding through `TrustEvidence`; it must not treat the present construction as a derived clinical mechanism.")
        end
    end
end

function summary_payload(config, pilot_summary; confirmation_summary = nothing)
    return (
        experiment = 47,
        name = "protector_trust",
        contract = "experiments-44-49-sufficiency-round-spec.md §6",
        pilot = pilot_summary,
        confirmation = confirmation_summary,
        config = config_record(config),
        structural_audit = self_check(config),
    )
end

function write_status(state; all_criteria_pass = nothing)
    required = ["per_seed.csv", "summary.json", "status.json",
        "magic-numbers.md", "freeze-log.md", "report.md"]
    GlobalPrecisionField.write_json(joinpath(OUTPUT_DIR, "status.json"), (
        experiment = 47,
        state = state,
        confirmation_complete = isfile(CONFIRMATION_MARKER),
        all_criteria_pass = all_criteria_pass,
        required_deliverables = required,
        present_deliverables = [file for file in required
            if isfile(joinpath(OUTPUT_DIR, file))],
        generated_at = string(now()),
    ))
end

function run_pilot(config)
    isfile(CONFIRMATION_MARKER) &&
        error("confirmation is complete; refusing to overwrite frozen results")
    mkpath(OUTPUT_DIR)
    pilot_rows = run_block(config.pilot_seeds; stage = :pilot, config = config)
    pilot_summary = summarize_block(pilot_rows, config)
    GlobalPrecisionField.write_csv(joinpath(OUTPUT_DIR, "per_seed.csv"),
        pilot_rows)
    write_magic_numbers(config)
    GlobalPrecisionField.write_json(joinpath(OUTPUT_DIR, "summary.json"),
        summary_payload(config, pilot_summary))
    write_report(config, pilot_summary, pilot_rows)
    write_status("pilot_complete_awaiting_freeze")
    return pilot_rows, pilot_summary
end

function freeze_pilot(config)
    isfile(CONFIRMATION_MARKER) &&
        error("confirmation is complete; refusing to rewrite freeze")
    mkpath(OUTPUT_DIR)
    pilot_rows = run_block(config.pilot_seeds; stage = :pilot, config = config)
    pilot_summary = summarize_block(pilot_rows, config)
    minimum_role_shift = minimum(row.hope_role_shift for row in pilot_rows)
    config.hope_shift_margin <= minimum_role_shift ||
        error("hope margin is not supported by every pilot world")
    all(row.repair_effect > config.repair_smooth_successes_k *
        row.smooth_success_effect for row in pilot_rows) ||
        error("pilot does not support k smooth successes")
    all(row.repair_effect <= (config.repair_smooth_successes_k + 1) *
        row.smooth_success_effect for row in pilot_rows) ||
        error("k is not the largest pilot-supported integer comparator")
    write_freeze_log(config, pilot_rows)
    write_magic_numbers(config)
    GlobalPrecisionField.write_csv(joinpath(OUTPUT_DIR, "per_seed.csv"),
        pilot_rows)
    GlobalPrecisionField.write_json(joinpath(OUTPUT_DIR, "summary.json"),
        summary_payload(config, pilot_summary))
    write_report(config, pilot_summary, pilot_rows)
    write_status("frozen_confirmation_unopened")
    return pilot_rows, pilot_summary
end

function run_confirmation(config)
    isfile(FREEZE_LOG) ||
        error("confirmation blocked: run --pilot and --freeze first")
    isfile(CONFIRMATION_MARKER) &&
        error("confirmation already complete; refusing to rerun")
    pilot_rows = run_block(config.pilot_seeds; stage = :pilot, config = config)
    pilot_summary = summarize_block(pilot_rows, config)
    confirmation_rows = run_block(config.confirmation_seeds;
        stage = :confirm, config = config)
    confirmation_summary = summarize_block(confirmation_rows, config)
    all_rows = vcat(pilot_rows, confirmation_rows)
    GlobalPrecisionField.write_csv(joinpath(OUTPUT_DIR, "per_seed.csv"),
        all_rows)
    write_magic_numbers(config)
    GlobalPrecisionField.write_json(joinpath(OUTPUT_DIR, "summary.json"),
        summary_payload(config, pilot_summary;
            confirmation_summary = confirmation_summary))
    write_report(config, pilot_summary, pilot_rows;
        confirmation_summary = confirmation_summary,
        confirmation_rows = confirmation_rows)
    open(CONFIRMATION_MARKER, "w") do io
        println(io, "Experiment 47 confirmation completed at $(now())")
        println(io, "Seeds: 14751:14770")
    end
    write_status("confirmation_complete";
        all_criteria_pass = confirmation_summary.all_criteria_pass)
    return confirmation_rows, confirmation_summary
end

function append_exploratory_summary(payload)
    path = joinpath(OUTPUT_DIR, "summary.json")
    raw = read(path, String)
    occursin("\"exploratory\"", raw) &&
        error("summary already contains an exploratory block")
    endswith(raw, "}\n") ||
        error("unexpected frozen summary terminator")
    buffer = IOBuffer()
    GlobalPrecisionField.json_write(buffer, payload; indent = 2)
    rendered = String(take!(buffer))
    # This exact suffix can be removed to reconstruct the frozen bytes.
    updated = chop(raw; tail = 2) *
        ",\n  \"exploratory\": " * rendered * "\n}\n"
    open(path, "w") do io
        write(io, updated)
    end
end

function write_exploratory_log(summary)
    open(joinpath(OUTPUT_DIR, "exploratory-log.md"), "w") do io
        println(io, "# Experiment 47 exploratory (d) log")
        println(io)
        println(io, "- Status: post-freeze, non-confirmatory.")
        println(io, "- Frozen summary SHA-256 before this block: `$(FROZEN_SUMMARY_SHA256)`.")
        println(io, "- Fresh seeds: `14801:14840` (40 worlds), disjoint from pilot `14701:14710` and confirmation `14751:14770`.")
        println(io, "- Co-protection evidence budget: `$(EXPLORATORY_COMPETENCE_EPISODES)` Bernoulli demonstrations per world.")
        println(io, "- True competence generation: one `Uniform(0,1)` draw per seed; demonstrations sampled from that probability.")
        println(io, "- Inference likelihood: existing `competence_success_likelihood`; prior: existing `prior_competence`.")
        println(io, "- Existing stakes, risk weights, refusal cost, decision temperature, and hope value were reused.")
        println(io, "- New obsolescence penalty: **none**. The risk-model path does not read `obsolescence_penalty`.")
        println(io, "- Positive/negative obsolete shifts: `$(summary.positive_obsolete_shift_worlds)` / `$(summary.negative_obsolete_shift_worlds)`.")
        println(io, "- Analytic competence crossover: `$(number(summary.competence_crossover_estimate))`.")
    end
end

function append_exploratory_magic_numbers()
    path = joinpath(OUTPUT_DIR, "magic-numbers.md")
    raw = read(path, String)
    occursin("## Exploratory (d), post-freeze", raw) &&
        error("exploratory magic numbers already recorded")
    open(path, "a") do io
        println(io)
        println(io, "## Exploratory (d), post-freeze")
        println(io)
        println(io, "| Constant | Value | Rationale |")
        println(io, "|---|---:|---|")
        println(io, "| `exploratory_seeds` | `14801:14840` | Forty fresh worlds, disjoint from all opened blocks. |")
        println(io, "| `competence_evidence_episodes` | `4` | Small common evidence budget giving five possible success counts. |")
        println(io, "| `true_competence_support` | `[0,1]` | Normalized probability support for the seed-specific generator. |")
        println(io, "| `incompetent_system_risk_endpoint` | `1` | Existing normalized maximal-risk endpoint; not a fitted penalty. |")
        println(io)
        println(io, "All other exploratory constants reuse the frozen config. No obsolescence-penalty parameter enters the risk-model operationalization.")
    end
end

function append_exploratory_report(config, analytic, exploratory)
    report_path = joinpath(OUTPUT_DIR, "report.md")
    raw = read(report_path, String)
    occursin("## Exploratory addendum (post-freeze; non-confirmatory)", raw) &&
        error("report already contains the exploratory addendum")
    open(report_path, "a") do io
        println(io)
        println(io, "## Exploratory addendum (post-freeze; non-confirmatory)")
        println(io)
        println(io, "This addendum does not alter the frozen 4/5 verdict, thresholds, confirmatory rows, or interpretation of criterion (d) as failed. The pre-addendum `summary.json` SHA-256 was `$(FROZEN_SUMMARY_SHA256)`.")
        println(io)
        println(io, "### Analytic bound for the frozen policy-addition form")
        println(io)
        println(io, "Let `A > 0` be the total softmax weight of existing contact-enabling policies, `B > 0` the total weight of non-enabling policies, and `w = exp(U_new / T) > 0` the weight of an added contact-enabling future at finite decision temperature `T > 0`. Baseline permission is `P = A/(A+B)` and permission after addition is `P' = (A+w)/(A+B+w)`. Therefore:")
        println(io)
        println(io, "```text")
        println(io, "P' - P = wB / ((A+B)(A+B+w)) > 0.")
        println(io, "```")
        println(io)
        println(io, "The obsolescence shift is thus bounded below by zero and is strictly positive whenever refusal retained nonzero mass. It cannot become negative in this model class. For the two added futures, `w_obsolete / w_role = exp(-(obsolescence_penalty + protector_role_value)/T)`. With frozen constants this is `exp(-($(config.obsolescence_penalty) + $(config.protector_role_value))/$(config.decision_temperature)) = $(number(analytic.added_weight_ratio))`. The ≤ half criterion is consequently arithmetic over the authored penalty, role value, and temperature rather than an inference result.")
        println(io)
        println(io, "Re-evaluation of the 20 frozen confirmation posteriors matched the closed form to maximum absolute error `$(analytic.maximum_absolute_error)`. All `$(analytic.strictly_positive_worlds)/20` obsolete shifts were strictly positive; their minimum was `$(number(analytic.minimum_obsolete_shift))`.")
        println(io)
        println(io, "### Risk-model operationalization")
        println(io)
        println(io, "The exploratory form retains the existing allow-versus-refuse policy set. Both counterfactuals represent the same healed exile and receive the same existing hope value; neither adds a third policy. The role-preserving future removes the healed outcome hazard while retaining co-protection and partner risks. In the obsolete future, protector absence makes risk conditional on the inferred competence posterior `c`: `r_obsolete = c*r_role + (1-c)*1`, where `1` is the normalized maximal-risk endpoint. Thus high inferred competence approaches the role-preserving forecast, while low competence forecasts abandonment-level risk. The existing posterior, risk weights, stakes, refusal cost, hope value, and temperature do all the work; `obsolescence_penalty` is not read.")
        println(io)
        println(io, "Forty fresh worlds (`14801:14840`) each generated four co-protection demonstrations from a seed-specific competence probability and inferred `c` through the existing likelihood. The posterior range was `$(number(exploratory.competence_posterior_minimum))`–`$(number(exploratory.competence_posterior_maximum))`. Role-preserving futures increased permission by mean `$(number(exploratory.mean_role_shift))`. Obsolescence shifted permission positively in `$(exploratory.positive_obsolete_shift_worlds)/40` worlds and negatively in `$(exploratory.negative_obsolete_shift_worlds)/40`, with an analytic crossover at competence posterior `$(number(exploratory.competence_crossover_estimate))` (largest observed negative `$(number(exploratory.maximum_competence_with_negative_shift))`; smallest observed positive `$(number(exploratory.minimum_competence_with_positive_shift))`). The analytic utility-sign prediction matched all worlds, all policy evaluations left posteriors flat, and no exploratory path read an obsolescence penalty.")
        println(io)
        println(io, "### Scoped conclusion")
        println(io)
        println(io, "Within these authored model classes, §8's obsolescence clause requires the future to change the protector's forecast of system risk, not merely append another contact-enabling softmax option. Policy addition guarantees a nonnegative shift and makes the control depend on authored utility constants. The risk-model form instead produces the predicted competence-dependent crossover: room for the protector matters when inferred co-protection is weak, while obsolescence can be tolerable when the system is already expected to bear its absence. This is a finding about operationalization and model class, not about people or clinical effectiveness.")
    end
end

function run_exploratory_d(config)
    isfile(CONFIRMATION_MARKER) ||
        error("exploration requires a completed frozen confirmation")
    isfile(EXPLORATORY_MARKER) &&
        error("exploratory (d) block already complete; refusing to rerun")
    opened = union(config.pilot_seeds, config.confirmation_seeds)
    isempty(intersect(opened, EXPLORATORY_SEEDS)) ||
        error("exploratory seeds overlap an opened block")

    analytic_rows = [run_policy_addition_audit(seed; config = config)
        for seed in config.confirmation_seeds]
    maximum_error = maximum(max(row.role_absolute_error,
        row.obsolete_absolute_error) for row in analytic_rows)
    risk_rows = run_exploratory_block(EXPLORATORY_SEEDS;
        competence_evidence_episodes = EXPLORATORY_COMPETENCE_EPISODES,
        config = config)
    risk_summary = summarize_exploratory(risk_rows)
    analytic_summary = (
        formula = "delta = w*B / ((A+B)*(A+B+w))",
        finite_temperature_lower_bound = 0.0,
        strictly_positive_worlds =
            count(row -> row.obsolete_strictly_positive, analytic_rows),
        minimum_obsolete_shift =
            minimum(row.obsolete_direct_shift for row in analytic_rows),
        maximum_absolute_error = maximum_error,
        added_weight_ratio = exp(-(config.obsolescence_penalty +
            config.protector_role_value) / config.decision_temperature),
        authored_constants_controlling_ratio = [
            "obsolescence_penalty", "protector_role_value",
            "decision_temperature"],
    )
    payload = (
        status = "post_freeze_non_confirmatory",
        frozen_verdict_unchanged = "4/5; criterion (d) failed",
        frozen_summary_sha256 = FROZEN_SUMMARY_SHA256,
        reconstruction_rule =
            "remove the final top-level exploratory member and its leading comma",
        analytic_policy_addition = analytic_summary,
        risk_model = merge(risk_summary, (
            seeds_disjoint_from_opened_blocks = true,
            obsolescence_penalty_parameter = nothing,
            risk_equation =
                "r_obsolete = c * r_role + (1 - c) * 1",
        )),
    )
    GlobalPrecisionField.write_csv(joinpath(OUTPUT_DIR,
        "exploratory_policy_addition_audit.csv"), analytic_rows)
    GlobalPrecisionField.write_csv(joinpath(OUTPUT_DIR,
        "exploratory_risk_model_per_seed.csv"), risk_rows)
    GlobalPrecisionField.write_json(joinpath(OUTPUT_DIR,
        "exploratory-summary.json"), payload)
    write_exploratory_log(risk_summary)
    append_exploratory_magic_numbers()
    append_exploratory_summary(payload)
    append_exploratory_report(config, analytic_summary, risk_summary)
    open(EXPLORATORY_MARKER, "w") do io
        println(io, "Experiment 47 exploratory (d) completed at $(now())")
        println(io, "Seeds: 14801:14840")
    end
    return payload
end

function main()
    length(ARGS) == 1 ||
        error("usage: run_protector_trust.jl --pilot|--freeze|--confirm|--explore-d")
    config = ProtectorTrustConfig()
    if ARGS[1] == "--pilot"
        _, summary = run_pilot(config)
        println("Experiment 47 pilot complete: all provisional checks = ",
            summary.all_criteria_pass)
    elseif ARGS[1] == "--freeze"
        freeze_pilot(config)
        println("Experiment 47 frozen; confirmation remains unopened.")
    elseif ARGS[1] == "--confirm"
        _, summary = run_confirmation(config)
        println("Experiment 47 confirmation complete: all criteria = ",
            summary.all_criteria_pass)
    elseif ARGS[1] == "--explore-d"
        payload = run_exploratory_d(config)
        println("Experiment 47 exploratory (d) complete: crossover = ",
            payload.risk_model.competence_crossover_estimate)
    else
        error("unknown mode $(ARGS[1])")
    end
end

main()
