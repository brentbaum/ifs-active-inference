# V2.5a Gate-5 honest stop

Blocking failure retained verbatim:
`['V2.4.4_manifest_identity']`.

## Localization

This is a process-custody verifier failure, not a scientific or semantic
failure. The new Gate-5 verifier read only
`results/V2.4.4/freeze-manifest.json`. That base manifest records
`results/V2.4.4/freeze-readiness.md` at:

`d4a2ba54f505759a37242ee02973a299af5d2bb3b1886dd97d72f87f98acea1a`

The current committed file hashes to:

`f350531534e38718f2c31973e1d96416e51de6d080fad441cae8ebe7c97c83f2`

The committed `results/V2.4.4/freeze-manifest-addendum.json` explicitly
overlays that same current hash and states that the updated freeze-readiness
was added after the primary manifest. The V2.5a verifier failed to compose
the base manifest with its committed addendum.

This matches the apparatus class previously repaired in R0's Gate-5
manifest-chain verifier, but no V2.5a repair is made here without explicit
authorization.

## Unaffected completed checks

- all other Gate-5 blocking checks passed;
- Gate-3 eligible bridge contrast: `0.06313714303388203`, 95% interval
  `[0.04462763412351659, 0.08427047327564974]`;
- the 17-world off-lattice class remained descriptive and nonblocking;
- the retired dose-monotone criterion was not evaluated;
- all V2.5a robustness identities and factorized exact-zero checks passed;
- V2.0, V2.1, V2.2.1, formation, maintenance, and both constitutions passed;
- the R0 27-file manifest rehashed cleanly;
- the full suite passed 129/129 in `422.837` unittest seconds
  (`423.014` enclosing seconds).

The complete Gate-5 block `761000:763999` was consumed as preregistered.
No freeze-readiness report or format-core manifest is produced after this
blocking stop.
