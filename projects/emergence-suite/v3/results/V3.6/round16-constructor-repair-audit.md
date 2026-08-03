# Round-16 constructor repair audit

Verdict: **PASS**.

Ruling 16.1 changed exactly one source line in
`ref/v36_round12.py::_external_structure`: the incoherent
`real_danger_adaptive -> cross_sign=-1` special case was removed. The return
now reads:

```python
return structure, (1 if active > 1 else 0)
```

The differential is exactly one added and one deleted line. The file SHA-256
changed from
`78dda8742e39627c3cd6004809207e54e93dfe12a258e117c4a95a766d8d3ab2`
to
`85d4442f128cfe0a92ca53a0be55c9b4b427854f5d463c5e90cbdfd0d3f36146`.

Every scientific-module hash enumerated in
`round15-repair-baseline-hashes.json` matches bitwise: V3.1–V3.5, the V3.6
composition module, and the bridge. Calibration and oracle modules are clean
in git status and their current hashes are pinned in the JSON audit. No
scorer, likelihood, prior, adapter, criterion, or threshold changed.
