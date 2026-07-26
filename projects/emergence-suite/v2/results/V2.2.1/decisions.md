# V2.2.1 decision log

- Diagnosis verdict is (b): the Beta(1,1) update was calibrated, but exact
  factorization was a measure-zero parameter value rather than a candidate
  structure.
- The repair adds a cue-level existence variable. It does not change the
  whole-model shared/factorized/reversed family, root factors, precision
  admission, observation likelihood, or transfer readout.
- The zero component is fixed at `P(M=G)=.5`. The associated slab uses
  Beta(match=9,mismatch=1), centered on the inherited `.9` associated world.
- Prior existence probability is `.6` zero / `.4` associated: mildly sparse,
  but finite evidence can dominate it in either direction.
- Association delivered to inference is posterior model averaging. No
  posterior-probability cutoff, strength clamp, transfer coefficient, or
  target update is permitted.
- V2.0 and V2.1 parameter files remain byte-identical. All inherited gates are
  rerun rather than assumed.

