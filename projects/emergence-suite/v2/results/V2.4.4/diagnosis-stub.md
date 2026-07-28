# V2.4.4 Gate-2 stop — diagnosis stub

Status: **official honest stop at Gate 2**. Gate 1 passed. Gate 3 was not
run and none of its seed blocks was opened.

Failure retained verbatim:

- `cs_selective`

Fresh 96-slice recovery/calibration results:

- recovery diagonal GW/CL/CS/DR/CP:
  `0.83 / 0.78 / 0.96 / 0.84 / 0.99`;
- macro recovery: `0.88`;
- CS material-redescription rate: `0.92` (passes `>=0.60`);
- CS selective-material-redescription rate: **`0.44`** (fails `>=0.60`);
- nuisance material rates GW/CL/DR/CP:
  `0.01 / 0.01 / 0.00 / 0.01`;
- nuisance selective rates: all exactly `0.00`.

Every retained recovery, calibration, parameter-recovery, DR/CP raw-CS,
and nuisance material/selective criterion passed. The only failure is that
fewer than 60% of exact CS-generating worlds exceed their own 999-replicate
cue-marginal-preserving conditional null at `p_CRT <= .05`.

Per the final-successor stop rule, the numeric failure stands. No threshold,
family, likelihood, transition, prior, randomization definition, or
information length was changed.

Required constants remain:

- `B_max_inherited_formation = 3.801426508560692`
- `B_max_v24_common_emissions = 6.704414354964107`
- `pi1 = 0.92741935483871` at the 24-slice reference prefix
