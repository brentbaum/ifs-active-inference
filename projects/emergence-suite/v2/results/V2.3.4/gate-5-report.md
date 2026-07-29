# V2.3.4 gate 5

Verdict: **PASS**.

## Scenario summaries

- `threat_low`: {'threat_error': {'mean': 0.004904480514901737, 'lower_95': 0.003647303181815064, 'upper_95': 0.00616165784798841}, 'eta_error': {'mean': 0.06095410179066299, 'lower_95': 0.058011383211347974, 'upper_95': 0.063896820369978}, 'q_causal': {'mean': 0.9999999999998941, 'lower_95': 0.9999999999996935, 'upper_95': 1.0000000000000948}, 'policy_probability': {'mean': 0.5019489795918367, 'lower_95': 0.4989366579487047, 'upper_95': 0.5049613012349687}, 'masked_action_scientific_error_max': 2.2898349882893854e-16, 'count': 1000}
- `threat_high`: {'threat_error': {'mean': 0.006049257169262971, 'lower_95': 0.004679445351542998, 'upper_95': 0.007419068986982945}, 'eta_error': {'mean': 0.0029461931358253824, 'lower_95': 0.002197370200174658, 'upper_95': 0.003695016071476107}, 'q_causal': {'mean': 1.0, 'lower_95': 1.0, 'upper_95': 1.0}, 'policy_probability': {'mean': 0.5, 'lower_95': 0.4969252228935654, 'upper_95': 0.5030747771064346}, 'masked_action_scientific_error_max': 8.326672684688674e-17, 'count': 1000}
- `efficacy_prior`: {'threat_error': {'mean': 0.021608135564846545, 'lower_95': 0.01894597845069794, 'upper_95': 0.02427029267899515}, 'eta_error': {'mean': 0.0066823494906541716, 'lower_95': 0.005654327708542768, 'upper_95': 0.0077103712727655755}, 'q_causal': {'mean': 1.0, 'lower_95': 1.0, 'upper_95': 1.0}, 'policy_probability': {'mean': 0.49805102040816324, 'lower_95': 0.49495945682878056, 'upper_95': 0.5011425839875459}, 'masked_action_scientific_error_max': 6.852157730108388e-17, 'count': 1000}
- `spike_high`: {'threat_error': {'mean': 0.01640664668551602, 'lower_95': 0.014021755473098436, 'upper_95': 0.018791537897933603}, 'eta_error': {'mean': 0.0007863208363212757, 'lower_95': 0.00016948289393873943, 'upper_95': 0.0014031587787038118}, 'q_causal': {'mean': 0.004014268443426942, 'lower_95': 0.001565040710122514, 'upper_95': 0.006463496176731371}, 'policy_probability': {'mean': 0.5006836734693878, 'lower_95': 0.4975574652905268, 'upper_95': 0.5038098816482488}, 'masked_action_scientific_error_max': 6.245004513516506e-17, 'count': 1000}
- `action_cost`: {'threat_error': {'mean': 0.0, 'lower_95': 0.0, 'upper_95': 0.0}, 'eta_error': {'mean': 0.4154135338345864, 'lower_95': 0.4154135338345864, 'upper_95': 0.4154135338345864}, 'q_causal': {'mean': 0.6500000000000002, 'lower_95': 0.6500000000000002, 'upper_95': 0.6500000000000002}, 'policy_probability': {'mean': 0.9705882352941175, 'lower_95': 0.9705882352941175, 'upper_95': 0.9705882352941175}, 'masked_action_scientific_error_max': 5.204170427930421e-17, 'count': 1000}
- `efficacy_partial`: {'threat_error': {'mean': 0.01519927367973838, 'lower_95': 0.01302779703305318, 'upper_95': 0.017370750326423576}, 'eta_error': {'mean': 0.06731972937483863, 'lower_95': 0.06443611570230993, 'upper_95': 0.07020334304736732}, 'q_causal': {'mean': 0.9999998732594838, 'lower_95': 0.9999996546237261, 'upper_95': 1.0000000918952414}, 'policy_probability': {'mean': 0.5033673469387755, 'lower_95': 0.5002556074055042, 'upper_95': 0.5064790864720468}, 'masked_action_scientific_error_max': 1.196959198423997e-16, 'count': 1000}
- `probe_low`: {'threat_error': {'mean': 0.007474696840106377, 'lower_95': 0.0059095781722459904, 'upper_95': 0.009039815507966764}, 'eta_error': {'mean': 0.0683191283622706, 'lower_95': 0.06522783008924714, 'upper_95': 0.07141042663529405}, 'q_causal': {'mean': 0.9999999999991938, 'lower_95': 0.9999999999985539, 'upper_95': 0.9999999999998336}, 'policy_probability': {'mean': 0.4972448979591837, 'lower_95': 0.4941269881847737, 'upper_95': 0.5003628077335937}, 'masked_action_scientific_error_max': 1.2663481374630692e-16, 'count': 1000}
- `context_change`: {'threat_error': {'mean': 0.06725581525724908, 'lower_95': 0.06378861007867521, 'upper_95': 0.07072302043582294}, 'eta_error': {'mean': 0.09622099022321211, 'lower_95': 0.09307289708881478, 'upper_95': 0.09936908335760944}, 'q_causal': {'mean': 0.9999999480945965, 'lower_95': 0.999999897567049, 'upper_95': 0.999999998622144}, 'policy_probability': {'mean': 0.5057058823529411, 'lower_95': 0.5004556755104922, 'upper_95': 0.51095608919539}, 'masked_action_scientific_error_max': 3.9898639947466563e-17, 'count': 1000}
- `relief_high`: {'threat_error': {'mean': 2.220446049250313e-16, 'lower_95': 2.220446049250313e-16, 'upper_95': 2.220446049250313e-16}, 'eta_error': {'mean': 0.4154135338345863, 'lower_95': 0.4154135338345863, 'upper_95': 0.4154135338345863}, 'q_causal': {'mean': 0.6499999999999998, 'lower_95': 0.6499999999999998, 'upper_95': 0.6499999999999998}, 'policy_probability': {'mean': 0.9401122448979593, 'lower_95': 0.9387471811635502, 'upper_95': 0.9414773086323684}, 'masked_action_scientific_error_max': 1.5959455978986625e-16, 'count': 1000}
- `masking`: {'threat_error': {'mean': 0.16813242073693763, 'lower_95': 0.16466268118122293, 'upper_95': 0.17160216029265232}, 'eta_error': {'mean': 0.15115016232778883, 'lower_95': 0.14561679996127783, 'upper_95': 0.15668352469429983}, 'q_causal': {'mean': 0.8328889013115373, 'lower_95': 0.8260209806256607, 'upper_95': 0.8397568219974139}, 'policy_probability': {'mean': 0.5013469387755103, 'lower_95': 0.4981914058905941, 'upper_95': 0.5045024716604265}, 'masked_action_scientific_error_max': 1.5959455978986625e-16, 'count': 1000}
- `precision_low`: {'threat_error': {'mean': 0.051011802741274107, 'lower_95': 0.04757344862598619, 'upper_95': 0.05445015685656202}, 'eta_error': {'mean': 0.11473559623399456, 'lower_95': 0.11085129418292682, 'upper_95': 0.1186198982850623}, 'q_causal': {'mean': 0.9963863807424812, 'lower_95': 0.9943880724147218, 'upper_95': 0.9983846890702406}, 'policy_probability': {'mean': 0.497969387755102, 'lower_95': 0.49490953116984804, 'upper_95': 0.501029244340356}, 'masked_action_scientific_error_max': 1.196959198423997e-16, 'count': 1000}

## Criteria

- `standing_gates_1_4`: PASS
- `full_cumulative_suite`: PASS
- `permanent_constitution`: PASS
- `manifest_chain`: PASS
- `action_cost_no_scientific_likelihood`: PASS
- `relief_no_scientific_likelihood`: PASS
- `probe_frequency_direction`: PASS
- `context_change_classification`: PASS
- `masking_truth_error_cost`: PASS
- `precision_truth_error_cost`: PASS
- `precision_nonnegative_rate`: PASS
- `partial_efficacy_recovery`: PASS
- `spike_prior_zero_recovery`: PASS
- `threat_prior_low_recovery`: PASS
- `threat_prior_high_recovery`: PASS
