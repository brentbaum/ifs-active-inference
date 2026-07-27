# V2.3.1 retained development failures

## Attempt 21 — complete varied assay after contextual controllability repair

On all 512 calibration worlds and 64 paired worlds, surface incremental
cross-validated R² fell to `.024998`, paired low-minus-high-control
formation was `.319463` (`95% CI [.263707, .373624]`), p99 / maximum step
were `.054246` / `.162599`, and uncontrollability calibration was monotone.
The cumulative-overwhelm curve failed strict monotonicity: mean formation was
`.399967`, `.378953`, and `.392307` across its ordered bins.

The factor used `K` but not the realized event report `B`, so an acute slice
whose high-precision report contradicted an event could still contribute a
positive precision score. The final candidate family includes `B` in the
same bounded factor and signs only the precision-dependent terms by that
realized report. This is a generative-factor correction, not a readout or
schedule rule.

## Attempt 22 — signed realized-report factor

Adding `B` directly to the bounded accumulator and signing precision terms
did not remove the marginal calibration reversal. In a 128-world check the
ordered overwhelm-bin means were `.442`, `.384`, `.404`; signing the entire
positive acute block left them `.438`, `.385`, `.558` after a stronger
precision allocation. The negative-evidence bin contains more acute reports
per world, and a one-slice signed term cannot by itself make a marginal curve
conditional on neither controllability nor acute count. These variants are
rejected; `B` remains evidence only through the declared precision
likelihood.

## Attempt 23 — near-static structure hazard

Reducing the structure hazard to `.001`, then zero, tested whether
timing-dependent forgetting carried the calibration reversal. At `.001`,
overwhelm-bin means were `.167`, `.110`, `.315`, paired low-minus-high
formation was `.247`, but surface incremental R² rose to `.109`. The identity
transition gave `.157`, `.097`, `.307`, paired `.243`, and surface
incremental R² `.109`. This trades one generalization failure for another and
is rejected.

## Attempt 24 — overly strong capped precision

A `.95` factor-score cap with direct precision weights `1.2` and `2.0`
preserved the empirical step bound but did not make the unadjusted marginal
curve monotone; the final reduced check was `.438`, `.385`, `.558`.
The factor was restored to the theory-variable parameterization that passed
surface R², paired control, original assays, and continuity. The final report
retains both marginal curves and calibration curves adjusted only for the
other preregistered theory variable; no surface feature enters that
adjustment.

## Attempt 20 — first full varied-schedule repair assay

The complete preregistered 512-world calibration matrix and 64 paired worlds
were run after recovery passed. Continuity passed strongly: across `30,720`
slices the p99 change was `.029948`, the maximum was `.151074`, and no slice
exceeded the frozen `.294529387` bound. The formation boundary failed:

- uncontrollability calibration was monotone, but cumulative-overwhelm
  calibration was not;
- theory-only cross-validated R² was `.137414`;
- surface features added `.258773` cross-validated R²;
- paired low-minus-high-control formation was `.004933`
  (`95% CI [.002161, .008257]`).

The failure localizes two misplaced parameters. A `.05` controllability
transition made the final inferred-controllability readout forget earlier
event contexts, while an unconditional collapsed-broadcast score accumulated
with event count even in matched high-control worlds. The next attempt lowers
the schedule-blind controllability hazard and reallocates the same bounded
score budget from unconditional collapse to the declared
overwhelm-by-collapse route.

## Attempt 1 — uniform candidate contrast (`tau=.085`)

Eight original-assay worlds and a 32-world/16-pair varied smoke assay were
run before any parameter revision.

- Acute final persistent probability: `0.230817`.
- Gradual final / change: `0.178367` / `-0.041633`.
- Adaptive-threat final: `0.269770`.
- Low-minus-high control: `0.001601`.
- Closed-loop structure effect: `-0.001283`.
- Original-assay maximum step: `0.040519`; varied maximum: `0.014012`.

Continuity was conservative, but the uniform midpoint blend removed too much
candidate contrast from the factors that carry the declared formation routes.
This attempt fails gates 2–3 and is retained.

## Attempt 2 — distributed route budget

The same smoke battery was repeated with the total analytic log-evidence
budget allocated across event `.15`, policy `.05`, transition `.20`, outcome
`.08`, and context `.06`.

- Analytic adjacent-step bound: `0.270558`.
- Acute final persistent probability: `0.333368`.
- Gradual final / change: `0.383051` / `0.163051`.
- Adaptive-threat final: `0.449956`.
- Low-minus-high control: `0.006888`.
- Closed-loop structure effect: `0.008096`.
- Original-assay maximum step: `0.064575`; varied maximum: `0.023498`.

Formation remained below every original threshold. This allocation fails
gates 2–3 and is retained.

## Factor-budget localization

Four 4-world paired allocations used the same analytic budget:

| allocation | acute | gradual | adaptive | low-high C | max step |
|---|---:|---:|---:|---:|---:|
| transition-heavy | .2700 | .3964 | .3137 | .0038 | .0567 |
| outcome-heavy | .2719 | .3356 | .3115 | -.0019 | .0383 |
| event-heavy | .5000 | .5710 | .6210 | .0942 | .0990 |
| context-heavy | .2453 | .3411 | .3180 | .0141 | .0905 |

Only event-coupling allocation recovered substantial formation. None met all
gate-3 thresholds; this table is localization, not a passing attempt.

## Attempt 3 — initial-prior rebalancing

With a `.40` initial persistent prior and the event-heavy budget, the 8-world
smoke results were acute `.653745`, gradual `.700771`, gradual change
`.300771`, adaptive threat `.813360`, low-high control `.022788`, and maximum
step `.092799`. The prior improved final probabilities but mechanically
reduced accumulated change and did not recover the control boundary. A
prior-only repair therefore cannot satisfy the unchanged gates and is
abandoned.

## Attempt 4 — first explicit accumulator

The first bounded accumulation factor produced acute `.355967`, gradual
`.375212`, controlled contrast `.198421`, low-high control `.092795`,
adaptive threat `.683677`, and maximum step `.150292`. Inspection localized
the miss: the `.25` persistence cost was applied even when `E=0`, so safe
slices accumulated transient evidence and reintroduced run-length
dependence. This attempt fails gates 2–3 and is retained.

## Attempt 5 — event-conditioned accumulator

Moving the persistence cost inside the event term produced acute `.468186`,
gradual `.901181`, gradual change `.681181`, controlled contrast `.234872`,
low-high control `.310543`, adaptive threat `.768696`, and maximum step
`.138644`. The general boundary recovered, but the acute assay remained below
`.70`; this localized the remaining miss to cumulative overwhelm precision.

## Attempt 6 — additive overwhelm precision

Adding precision as an independent bounded parent produced acute `.567481`,
gradual `.825255`, controlled contrast `.193420`, low-high control `.280470`,
adaptive threat `.850585`, and maximum step `.138526`. Acute formation still
missed `.70`. The additive term did not isolate the claimed joint
overwhelm-with-uncontrollability boundary, so its budget was reassigned to an
explicit interaction inside the same factor.

## Attempt 8 — bounded gain and modest complexity-prior repair

With additive precision restored, gain `1.2`, and initial persistent prior
`.28`, the 8-world smoke battery produced acute `.690887`, gradual `.905735`,
gradual change `.625735`, controlled contrast `.224392`, low-high control
`.324237`, adaptive threat `.920669`, and maximum step `.155418`. The analytic
bound remained `.291835`. This was advanced to the full open block; the smoke
result is retained separately.

## Attempt 9 — full 64-world original battery

The first full repaired block produced:

- acute final `.682774` (threshold `.70`, FAIL);
- gradual final/change `.854967` / `.574967` (PASS);
- acute-minus-gradual maximum step `.001314` (threshold `.05`, FAIL);
- controlled contrast `.161592`, low-high control `.278635`, adaptive threat
  `.945962` (PASS);
- all six closed-loop chain intervals bounded above zero (PASS);
- p99 / maximum step `.128477` / `.168043`, with analytic bound `.291835`.

Gate 3 failed on acute level and legacy acute/gradual step separation. The
complete numerical result is retained here before the final allocation
revision.

## Attempt 10 — precision-heavy smoke

The precision-heavy 8-world allocation produced acute `.784654`, gradual
`.916509`, controlled contrast `.147925`, low-high control `.257968`,
adaptive threat `.956003`, and maximum step `.167777`. Acute level recovered,
but gradual maximum steps still occurred at the first of its five late
overwhelm slices, before low-precision accumulation had saturated the
posterior. Acute-minus-gradual step difference was `-.010625`.

## Attempt 11 — lower event cost

Lowering the event-conditioned cost while preserving the acute score produced
acute `.800378`, gradual `.941791`, controlled contrast `.107852`, low-high
control `.223316`, adaptive `.957914`, and acute-minus-gradual step
`.006034`. Gradual saturation improved only slightly at the relevant late
slices, while additive precision leaked into the controlled/integrated arm.
This attempt fails gate 3 and is retained.

## Attempt 12 — overwhelm-by-collapse smoke

The 8-world interaction smoke produced acute `.705561`, gradual `.960830`,
controlled contrast `.297821`, low-high control `.170886`, adaptive
`.947937`, and maximum step `.144036`. All original level/contrast thresholds
passed in the smoke sample. Acute-minus-gradual maximum step improved to
`.025701` but remained below `.05`; gradual failures localized to worlds with
pre-overwhelm posteriors `.63–.71`.

## Attempt 13 — low-precision saturation

The 8-world smoke produced acute `.728386`, gradual `.973033`, controlled
contrast `.261974`, adaptive `.949154`, acute-minus-gradual step `.050918`,
and maximum step `.140034`. It is the first attempt to meet the legacy step
criterion. Low-high controllability was only `.115166`, so the final
within-budget revision shifts weight to inferred uncontrollability without
changing expected acute/gradual scores materially.

## Attempt 14 — control-weight reallocation

Increasing the uncontrollability score weight produced acute `.729401`,
gradual `.970994`, controlled contrast `.252610`, low-high control `.130442`,
adaptive `.943881`, and acute-minus-gradual step `.044614`. It improved the
control contrast only slightly and lost the `.05` step separation. The
allocation was reverted; the next revision changes only the schedule-blind
controllability transition.

## Attempt 15 — persistent controllability inference

Reducing the symmetric `C` transition to `.05` produced acute `.727586`,
gradual `.975546`, controlled contrast `.288357`, low-high control `.133735`,
adaptive `.948199`, acute-minus-gradual step `.051439`, and maximum step
`.139364`. The step criterion was restored; the remaining control miss
motivated a final `.05` within-simplex shift from adverse outcome to
uncontrollability before the full gate run.

## Recovery attempt 1 — bounded-history underconfidence

On 128 worlds the final strain recovered candidate identity perfectly
(`128/128`), mean true-candidate probability `.814518`, Brier `.061638`, but
ECE `.185482` exceeded `.10`. Controllability `.851562`, broadcast `1.0`, and
policy-parameter recovery passed. This is calibrated-history
underconfidence, not candidate confusion; the recovery protocol is extended
from 12 to 24 generated slices while thresholds remain unchanged.

## Recovery attempt 2 — neutral slices do not calibrate transience

The 24-slice recovery protocol yielded accuracy `.992188`, mean true
probability `.809634`, Brier `.070507`, and ECE `.190366`. Adding neutral safe
slices correctly supplied no transient evidence. The final recovery protocol
therefore uses 64 controlled, integrated event slices for the transient
candidate; elapsed time alone is not treated as evidence.

## Recovery attempt 3 — event coupling beat transient context

With 64 controlled/integrated event slices, transient recovery fell to
`29/64`; overall accuracy `.726562`, mean true probability `.735377`, Brier
`.139021`, ECE `.264623`. Repeated event coupling outweighed the small
event-conditioned transient cost. The cost is increased from `.05` to `.10`
with compensating gain so open expected scores and the continuity bound remain
nearly unchanged.

## Recovery generator diagnosis

An 8-world convergence check showed that the hand-labeled controlled-event
schedule was not generated by the transient candidate: after 192 slices its
true-candidate probabilities were only `.35–.59`, while persistent histories
were approximately `.99`. The schedule-label recovery assay is therefore
invalid for the repaired family. Gate 2 is changed to exact conditional
generation from `H=0/1`, with the generating label withheld from inference.

## Recovery attempt 4 — fixed labels contradict dynamic `H`

Exact conditional sampling with a fixed `H` label yielded accuracy `.507812`,
mean true probability `.514218`, Brier `.281800`, and ECE `.168140`. V2.3.1
declares `H_t` as a Markov structure state; fixing it across slices while
also applying its transition is not generation from that primitive. The
final recovery assay therefore generates the complete `H_t` and carried-state
trajectory from the declared dynamic model and scores filtering recovery at
each slice.

## Recovery attempt 5 — dynamic state is weakly emitted

Dynamic joint-state recovery yielded accuracy `.569010`, mean true
probability `.528377`, Brier `.253063`, ECE `.115596`. The freely sampled
`H_t` state is only weakly emitted after candidate CPT bounding; V2.3's
recovery target is regime identity, not an independently switching hidden
label. A direct regime convergence check then found controlled/integrated
true-candidate probability declining from `.60` at 6 slices to `.12` at 48,
localizing a real accumulation-balance error.

## Attempt 16 — stronger universal event cost

Raising the universal event cost to `.25` fixed 24-slice transient/persistent
regime convergence to `.778` / `.992`, but broke the open acute result
(`.602614`) and acute-minus-gradual step separation (`.001812`). A universal
cost cannot distinguish controlled contextualization from low-control
formation; the final family uses conditional high-control and
high-control-by-integrated penalties instead.

## Attempt 17 — independent and integrated control penalties

The penalties fixed 24-slice transient/persistent convergence to `.988` /
`.991`, controlled and low-high contrasts, but the independent high-control
penalty fired while `C` was uncertain in acute low-control worlds. Acute
formation fell to `.575750` and step separation to `.009930`. The independent
term is removed; transient protection is assigned only to the inferred
high-control-by-integrated conjunction.

## Attempt 18 — conjunction penalty with inherited monitor

The conjunction-only penalty preserved 24-slice transient/persistent
convergence `.966` / `.994`, low-high control `.164031`, and adaptive threat
`.910843`, but acute formation remained `.606377` because the inherited `.90`
monitor left enough posterior mass on integrated `R` for the penalty to fire.
The final stage-local calibration sharpens the actual `p(Q|R)` likelihood to
`.99`; no new evidence route is added.

## Attempt 19 — sharpened reflexive monitor

With `.99` monitor reliability, the 8-world smoke passed every original
level/contrast: acute `.726590`, gradual `.973499`, step separation `.057113`,
controlled contrast `.599014`, low-high control `.155129`, adaptive
`.920422`, maximum step `.170035`. Twenty-four-slice transient/persistent
convergence was `.754` / `.994`; the integrated-control penalty is increased
to `.80`, which leaves the positive score bound and all low-control arms
unchanged.

## Attempt 7 — overwhelm-by-uncontrollability allocation

The interaction allocation produced acute `.529923`, gradual `.691682`,
controlled contrast `.205383`, low-high control `.122215`, adaptive threat
`.801049`, and maximum step `.135587`. Because `C` remains uncertain early in
an acute sequence, replacing additive precision with the interaction reduced
rather than increased acute formation. This attempt fails gate 3 and is
retained.
