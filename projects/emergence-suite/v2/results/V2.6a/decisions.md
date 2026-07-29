# V2.6a decisions

1. The single latent `L_t` is a four-state HMM shared by all four relational
   channels. No channel-specific partner latent was introduced.
2. Root evidence is a separate observation whose likelihood is sharpened by
   broadcast global precision. Relational observations therefore affect
   evidence uptake but have root BF exactly one when the root channel is
   absent.
3. Stable and switching recovery histories are balanced within every family.
   A switching world's registered family is its initial and majority-occupancy
   state; its final third occupies the declared adjacent state.
4. `co_regulated` is a pure thresholded readout over posterior reliable mass
   and global precision. It is never stored as scientific state or fed back.
5. The original Gate-2 ECE stop remains historical. The authorized apparatus
   repair aligned generation and per-slice calibration with the exact HMM.
6. The repaired onset-floor miss remains verbatim and is non-blocking only
   under `gate2-adjudication.md`; no threshold changed.
7. Gate 4 implements only the five master-spec lesions. Each lesion has a
   target-disappearance check and an unrelated-path preservation check.
8. Gate 5 uses thirteen disjoint 1,000-world cells spanning all eight named
   robustness dimensions and two partner controls. Directional results are
   reported per cell without pooling.
