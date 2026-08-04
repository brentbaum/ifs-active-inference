# DT-S1-IDGEN prediction scoring

Code-audit standing: **2**. S1-B/C remain architecture-conditional.

| Registered row | Result | Number |
|---|---|---|
| Step 0 standing 3 | **not_met** | `"standing 2"` |
| S1-A identity-first modal in identity-coupled worlds | **met** | `{"counts": {"identity_first": 2000, "no_crossing": 0, "outcome_first": 0, "simultaneous": 0}, "crossing_worlds": 2000, "no_crossing_rate": 0.0, "rates_among_crossing": {"identity_first": 1.0, "outcome_first": 0.0, "simultaneous": 0.0}}` |
| S1-A outcome-first modal in exposure-rational controls | **met** | `{"counts": {"identity_first": 0, "no_crossing": 0, "outcome_first": 2000, "simultaneous": 0}, "crossing_worlds": 2000, "no_crossing_rate": 0.0, "rates_among_crossing": {"identity_first": 0.0, "outcome_first": 1.0, "simultaneous": 0.0}}` |
| S1-A one-slice simultaneous classification | **met** | `"implemented as abs(t_G-t_Y)<=1"` |
| Falsifier: identity-first modal in exposure controls | **not_triggered** | `{"counts": {"identity_first": 0, "no_crossing": 0, "outcome_first": 2000, "simultaneous": 0}, "crossing_worlds": 2000, "no_crossing_rate": 0.0, "rates_among_crossing": {"identity_first": 0.0, "outcome_first": 1.0, "simultaneous": 0.0}}` |
| Falsifier: no-crossing dominant everywhere | **not_triggered** | `{"s1a_exposure": 0.0, "s1a_identity": 0.0}` |
| S1-B full/lesion/cue-removal pattern | **met** | `{"cue_local_removed": {"treated_movement": 0.0, "untreated_movement": 0.0}, "full": {"treated_movement": 0.4659236089025629, "untreated_movement": 0.5061960889758976}, "preservation_max_errors": {"outcome_count_difference": 0, "q_identity_difference": 0.0, "treated_prediction_difference": 0.0}, "root_sharing_lesion": {"treated_movement": 0.4659236089025629, "untreated_movement": 0.0}}` |
| Falsifier: untreated revision survives root lesion | **not_triggered** | `0.0` |
| S1-C V3.6 transfer primarily identity-sharing | **met** | `{"identity_minus_similarity": 0.4993128165176066, "identity_share_main_effect": 0.4993128165176066, "similarity_main_effect": 0.0}` |
| S1-C comparator transfer primarily perceptual similarity | **met** | `{"identity_minus_similarity": -0.4652676965626999, "identity_share_main_effect": 0.0, "similarity_main_effect": 0.4652676965626999}` |
| S1-C double dissociation | **met** | `{"comparator": {"identity_minus_similarity": -0.4652676965626999, "identity_share_main_effect": 0.0, "similarity_main_effect": 0.4652676965626999}, "v36": {"identity_minus_similarity": 0.4993128165176066, "identity_share_main_effect": 0.4993128165176066, "similarity_main_effect": 0.0}}` |
| Falsifier: V3.6 similarity effect >= identity-share effect | **not_triggered** | `{"identity_minus_similarity": 0.4993128165176066, "identity_share_main_effect": 0.4993128165176066, "similarity_main_effect": 0.0}` |
| S1-D correct structural majority mass in all four families | **met** | `{"acute_transient": {"majority_mass_rate": 0.956, "mean_correct_class_mass": 0.7913481924449347, "mean_part_mass": 0.0014618415567785436}, "mixed": {"majority_mass_rate": 0.72, "mean_correct_class_mass": 0.7030593254067748, "mean_part_mass": 0.9978136595545486}, "persistent_external": {"majority_mass_rate": 0.846, "mean_correct_class_mass": 0.8040255856165749, "mean_part_mass": 0.0013471014683880181}, "recurrent_identity_coupled": {"majority_mass_rate": 1.0, "mean_correct_class_mass": 0.9983368929049352, "mean_part_mass": 0.9983368929049352}}` |
| S1-D no identity pathology in pure external danger | **met** | `{"majority_mass_rate": 0.846, "mean_correct_class_mass": 0.8040255856165749, "mean_part_mass": 0.0013471014683880181}` |

No registered direction, ROPE, or falsifier was changed after the run.
