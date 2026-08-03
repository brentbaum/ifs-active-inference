# V3.7 registered-prediction scoring

Verdict: **PREDICTION_SCORED**.

```json
{
  "falsifiers": {
    "met_means_falsifier_triggered": true,
    "rows": [
      {
        "falsifier": "partner improvement less than half the registered V3.6 deficit",
        "half_deficit": 0.1471423024189065,
        "improvement": 0.3243516283609281,
        "met": false,
        "row": 1
      },
      {
        "change": 0.000543219458346067,
        "falsifier": "context gain drops by more than 0.05",
        "met": false,
        "row": 2
      },
      {
        "falsifier": "identity shows no improvement in real_danger_adaptive",
        "met": false,
        "new": -0.15281562810772586,
        "old": -0.29707870461983726,
        "row": 3
      }
    ]
  },
  "numbered_prediction_rows": [
    {
      "family_verdict": true,
      "met": true,
      "outcome": 0.03006702352311512,
      "prediction": "partner mean in [-0.02, 0.05] and family PASS",
      "row": 1
    },
    {
      "family_verdict": false,
      "met": false,
      "outcome": -0.25731772456592034,
      "prediction": "contact mean in [-0.05, 0.02] and family PASS",
      "row": 2
    },
    {
      "family_verdict": false,
      "met": false,
      "outcome": -0.09774537686168096,
      "prediction": "identity mean in [-0.06, 0.0] and family PASS",
      "row": 3
    },
    {
      "family_verdict": false,
      "met": false,
      "outcome": -0.09107600716770409,
      "prediction": "outcome mean in [-0.01, 0.01] and family PASS",
      "row": 4
    },
    {
      "distance": 0.0008425060392296957,
      "family_verdict": true,
      "met": true,
      "outcome": 0.2698425060392297,
      "prediction": "context within +/-0.03 of +0.269 and PASS",
      "row": 5
    }
  ],
  "per_stratum_commitments": [
    {
      "contact_spread": 0.008683003186217397,
      "met": true,
      "partner_spread": 0.005199884419209162,
      "prediction": "partner and contact stratum spread < 0.05",
      "row": 1
    },
    {
      "chronic_one_new": -0.043530844762187444,
      "chronic_one_old": -0.05382257802669426,
      "met": false,
      "prediction": "identity deficit shrinks >=70% in acute_one and real_danger_adaptive; chronic_one remains near its registered baseline",
      "row": 2,
      "shrinkage_fractions": {
        "acute_one": 0.3966975576979633,
        "real_danger_adaptive": 0.48560557949355726
      }
    },
    {
      "acute_shrinkage_fraction": -0.729057891543766,
      "met": false,
      "other_values": {
        "chronic_multiple": -0.059479208916026115,
        "chronic_one": -0.05791204060413899,
        "real_danger_adaptive": -0.0813154090494153
      },
      "prediction": "acute outcome deficit shrinks >=60%; all other strata within +/-0.02",
      "row": 3
    },
    {
      "met": true,
      "prediction": "context recurrent strata >=0.30 and acute_one within +/-0.05 of +0.03",
      "row": 4,
      "values": {
        "acute_one": 0.034705868611436874,
        "chronic_multiple": 0.3514514024216158,
        "chronic_one": 0.34581530339932065,
        "real_danger_adaptive": 0.3473974497245454
      }
    }
  ],
  "registered_prediction_sha256": "5a26e1e0e67927278d03da186b3e18d6a4d9932f5322112c062f5a7443ad69e9",
  "stage": "V3.7",
  "tournament_verdict_immutable_before_scoring": true,
  "verdict": "PREDICTION_SCORED"
}
```
