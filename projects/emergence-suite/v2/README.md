# Simulation Suite v2 — Python exact reference

This directory is the exact, finite-state reference implementation for Suite v2
milestone 1 (V2.0–V2.2). It uses Python 3, NumPy, and the standard library only.

Run all tests and regenerate public results:

```bash
cd projects/emergence-suite/v2
python3 -m unittest discover -s tests -v
python3 run_milestone.py
```

The factor-elimination engine and Cartesian-product oracle are separate code
paths. Protocol state contains only posterior, parameter-posterior, and evidence
stores; readouts are pure functions.

Evaluator-owned sealed challenges are intentionally absent. No file in this
directory depends on Experiment 51.

